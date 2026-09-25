"""Pont données → exécuteur S : problèmes B-V2 (@ag-2) → tenseurs.

Le contrat public est celui de `data_contract.md` (§2) : `nodes`, `edges`,
`query.start`, `options`. **Aucun champ privé** (réponse, trace, profondeur,
drapeaux de terminal) n'entre dans les tenseurs lus par le forward ; les
cibles d'état et l'index de réponse sont optionnels et séparés.

Deux constructeurs :

- :func:`batch_from_problems` — objets ``v2data.bfamily.Problem`` (ou dict
  ``{"input": ..., "private": ...}``) pour l'entraînement/l'évaluation ;
- :func:`batch_from_public_inputs` — dicts publics seuls, pour l'inférence
  (aucune cible, aucun accès aux champs privés).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import torch

__all__ = ["BUDGET", "RelationBatch", "batch_from_problems", "batch_from_public_inputs"]

BUDGET = 16  # plafond commun de transitions (audit §7.5)


@dataclass
class RelationBatch:
    """Lot S : entrées publiques + cibles séparées (jamais lues par forward)."""

    entity_features: torch.Tensor     # [B, N, F] — one-hot index (F = N)
    edge_mask: torch.Tensor           # [B, N, N] bool, [b, j, i] = arête j -> i
    relation: torch.Tensor            # [B, N, N, R] float (R=1 : « pointe vers »)
    node_mask: torch.Tensor           # [B, N] bool
    question: torch.Tensor            # [B, N] one-hot(départ)
    start_index: torch.Tensor         # [B] long
    candidates: torch.Tensor          # [B, K] long (indices d'entités)
    candidate_ids: list[list[str]]    # ids opaques, ordre des candidats
    candidate_mask: torch.Tensor      # [B, K] bool
    answer_index: torch.Tensor        # [B] long (-1 si inconnu)
    state_targets: torch.Tensor | None      # [B, T] long (terminal absorbant)
    state_weights: torch.Tensor | None      # [B, T] float (somme 1 par ligne)
    hops: torch.Tensor                # [B] long — privé, métriques uniquement
    ids: list[str] = field(default_factory=list)

    def to(self, device: torch.device | str) -> "RelationBatch":
        def move(value):
            return None if value is None else value.to(device)

        return RelationBatch(
            entity_features=move(self.entity_features),
            edge_mask=move(self.edge_mask),
            relation=move(self.relation),
            node_mask=move(self.node_mask),
            question=move(self.question),
            start_index=move(self.start_index),
            candidates=move(self.candidates),
            candidate_ids=[list(row) for row in self.candidate_ids],
            candidate_mask=move(self.candidate_mask),
            answer_index=move(self.answer_index),
            state_targets=move(self.state_targets),
            state_weights=move(self.state_weights),
            hops=move(self.hops),
            ids=list(self.ids),
        )


@dataclass
class _Record:
    id: str
    nodes: list[str]
    edges: list[tuple[int, int]]
    start: int
    candidates: list[int]
    candidate_ids: list[str]
    answer_index: int = -1
    targets: list[int] | None = None
    weights: list[float] | None = None
    hops: int = 0
    positions: list[int] | None = None   # indices réels si remap aléatoire


def _remap_record(record: _Record, positions: list[int]) -> _Record:
    """Applique une bijection d'indices aux entités (augmentation du pont).

    Les étiquettes d'indices sont arbitraires (data_contract.md §2) : une
    ré-indexation aléatoire préserve le graphe, les cibles et les ids de
    candidats, tout en couvrant des colonnes d'identité supplémentaires.
    """

    def map_index(index: int) -> int:
        return positions[int(index)]

    return _Record(
        id=record.id,
        nodes=record.nodes,
        edges=[(map_index(source), map_index(target)) for source, target in record.edges],
        start=map_index(record.start),
        candidates=[map_index(candidate) for candidate in record.candidates],
        candidate_ids=record.candidate_ids,
        answer_index=record.answer_index,
        targets=(
            [map_index(target) for target in record.targets]
            if record.targets is not None
            else None
        ),
        weights=record.weights,
        hops=record.hops,
        positions=list(positions),
    )


def _record_from_mapping(item: Mapping[str, Any]) -> _Record:
    public = item.get("input", item)
    private = item.get("private", {}) or {}
    nodes = list(public["nodes"])
    index = {node: position for position, node in enumerate(nodes)}
    edges = [(index[edge[0]], index[edge[1]]) for edge in public["edges"]]
    options = list(public["options"])
    answer_node = private.get("answer_node")
    answer_index = (
        next(
            (position for position, option in enumerate(options) if option["node"] == answer_node),
            -1,
        )
        if answer_node is not None
        else -1
    )
    return _Record(
        id=str(public.get("id", item.get("id", ""))),
        nodes=nodes,
        edges=edges,
        start=index[public["query"]["start"]],
        candidates=[index[option["node"]] for option in options],
        candidate_ids=[str(option["id"]) for option in options],
        answer_index=answer_index,
        targets=(
            list(private["trace_padded_indices_budget16"])
            if "trace_padded_indices_budget16" in private
            else None
        ),
        weights=(
            list(private["trace_loss_weights_budget16"])
            if "trace_loss_weights_budget16" in private
            else None
        ),
        hops=int(private.get("depth", 0) or 0),
    )


def _record_from_problem(problem: Any, budget: int) -> _Record:
    """Objet ``v2data.bfamily.Problem`` (API duck-typée, privé non requis)."""
    if isinstance(problem, Mapping):
        return _record_from_mapping(problem)
    nodes = list(problem.nodes)
    index = {node: position for position, node in enumerate(nodes)}
    answer_index = -1
    answer_node = getattr(problem, "answer_node", None)
    if answer_node is not None:
        answer_index = next(
            (
                position
                for position, option in enumerate(problem.options)
                if option["node"] == answer_node
            ),
            -1,
        )
    targets = None
    weights = None
    if hasattr(problem, "trace_padded_indices"):
        targets = list(problem.trace_padded_indices(budget))
    if hasattr(problem, "trace_loss_weights"):
        weights = list(problem.trace_loss_weights(budget))
    return _Record(
        id=str(problem.id),
        nodes=nodes,
        edges=[(index[edge[0]], index[edge[1]]) for edge in problem.edges],
        start=index[problem.start],
        candidates=[index[option["node"]] for option in problem.options],
        candidate_ids=[str(option["id"]) for option in problem.options],
        answer_index=answer_index,
        targets=targets,
        weights=weights,
        hops=int(getattr(problem, "depth", 0) or 0),
    )


def _collate(records: Sequence[_Record], *, budget: int, pad_nodes: int | None,
             pad_candidates: int | None, device: torch.device | str | None,
             feature_dim: int | None = None):
    if not records:
        raise ValueError("lot vide")
    batch = len(records)
    max_nodes = max(len(record.nodes) for record in records)
    max_candidates = max(len(record.candidates) for record in records)
    if pad_nodes is not None:
        max_nodes = max(max_nodes, int(pad_nodes))
    if pad_candidates is not None:
        max_candidates = max(max_candidates, int(pad_candidates))
    if feature_dim is not None:
        max_nodes = max(max_nodes, int(feature_dim))
    max_states = max(
        (len(record.targets) for record in records if record.targets), default=0
    )

    features = torch.zeros(batch, max_nodes, max_nodes, dtype=torch.float32)
    edge_mask = torch.zeros(batch, max_nodes, max_nodes, dtype=torch.bool)
    relation = torch.zeros(batch, max_nodes, max_nodes, 1, dtype=torch.float32)
    node_mask = torch.zeros(batch, max_nodes, dtype=torch.bool)
    question = torch.zeros(batch, max_nodes, dtype=torch.float32)
    start_index = torch.zeros(batch, dtype=torch.long)
    candidates = torch.zeros(batch, max_candidates, dtype=torch.long)
    candidate_mask = torch.zeros(batch, max_candidates, dtype=torch.bool)
    answer_index = torch.full((batch,), -1, dtype=torch.long)
    hops = torch.zeros(batch, dtype=torch.long)

    has_targets = all(record.targets is not None for record in records)
    has_weights = all(record.weights is not None for record in records)
    state_targets = (
        torch.zeros(batch, max_states, dtype=torch.long) if has_targets else None
    )
    state_weights = (
        torch.zeros(batch, max_states, dtype=torch.float32) if has_weights else None
    )

    for b, record in enumerate(records):
        positions = (
            record.positions
            if record.positions is not None
            else list(range(len(record.nodes)))
        )
        node_mask[b, positions] = True
        for position in positions:
            features[b, position, position] = 1.0
        for source, destination in record.edges:
            edge_mask[b, source, destination] = True
            relation[b, source, destination, 0] = 1.0
        start_index[b] = record.start
        question[b, record.start] = 1.0
        k = len(record.candidates)
        candidates[b, :k] = torch.tensor(record.candidates, dtype=torch.long)
        candidate_mask[b, :k] = True
        answer_index[b] = record.answer_index
        hops[b] = record.hops
        if state_targets is not None:
            state_targets[b, : len(record.targets)] = torch.tensor(
                record.targets, dtype=torch.long
            )
        if state_weights is not None:
            state_weights[b, : len(record.weights)] = torch.tensor(
                record.weights, dtype=torch.float32
            )

    output = RelationBatch(
        entity_features=features,
        edge_mask=edge_mask,
        relation=relation,
        node_mask=node_mask,
        question=question,
        start_index=start_index,
        candidates=candidates,
        candidate_ids=[list(record.candidate_ids) for record in records],
        candidate_mask=candidate_mask,
        answer_index=answer_index,
        state_targets=state_targets,
        state_weights=state_weights,
        hops=hops,
        ids=[record.id for record in records],
    )
    if device is not None:
        output = output.to(device)
    return output


def batch_from_problems(
    problems: Sequence[Any],
    *,
    budget: int = BUDGET,
    pad_nodes: int | None = None,
    pad_candidates: int | None = None,
    device: torch.device | str | None = None,
    index_space: int | None = None,
    index_seed: int | None = None,
) -> RelationBatch:
    """Convertit des problèmes B-V2 (objets ou dicts) en lot S torch.

    Les cibles d'état (``trace_padded_indices_budget16``) et leurs poids
    (``trace_loss_weights_budget16``) ne sont présentes que pour
    l'entraînement/l'évaluation ; elles ne sont jamais lues par le forward.

    ``index_space`` (optionnel, **entraînement**) : ré-indexe aléatoirement
    les entités dans ``0..index_space-1`` (même graphe/cibles/ids), pour
    couvrir des colonnes d'identité que le pool ne fournit pas — les indices
    sont des positions arbitraires par contrat.
    """
    records = [_record_from_problem(problem, budget) for problem in problems]
    if index_space is not None:
        import random as _random

        generator = _random.Random(0 if index_seed is None else int(index_seed))
        records = [
            _remap_record(
                record,
                generator.sample(range(int(index_space)), len(record.nodes)),
            )
            for record in records
        ]
    return _collate(
        records,
        budget=budget,
        pad_nodes=pad_nodes,
        pad_candidates=pad_candidates,
        device=device,
        feature_dim=index_space,
    )


def batch_from_public_inputs(
    inputs: Sequence[Mapping[str, Any]],
    *,
    pad_nodes: int | None = None,
    pad_candidates: int | None = None,
    device: torch.device | str | None = None,
) -> RelationBatch:
    """Lot d'**inférence** : entrées publiques seules, aucune cible privée."""
    records = [_record_from_mapping(item) for item in inputs]
    return _collate(
        records,
        budget=BUDGET,
        pad_nodes=pad_nodes,
        pad_candidates=pad_candidates,
        device=device,
    )
