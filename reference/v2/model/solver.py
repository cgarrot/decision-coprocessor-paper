"""Exécuteur exact sur mémoire prédite + validateur (audit §9).

L'audit exige un **validateur avant solveur** : si le graphe prédit est
invalide (cycle, successeur hors bornes, départ absent, aucun terminal…), le
système s'**abstient** — l'abstention est comptée, jamais transformée en
réponse silencieuse.

Le solveur est la marche déterministe sur les successeurs, sémantique
identique à ``v2data.bfamily.Problem.walk`` (@ag-2) ; l'équivalence est testée
différentiellement (`tests/test_extractor_contracts.py`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import torch

from .extractor import PredictedMemory
from .relation_data import RelationBatch, batch_from_problems

__all__ = [
    "SolveResult",
    "validate_memory",
    "solve_memory",
    "memory_to_public_input",
    "memory_to_batch",
]


@dataclass
class SolveResult:
    status: str                      # "solved" | "abstain"
    terminal: int | None = None
    path: list[int] = field(default_factory=list)
    reason: str | None = None


def validate_memory(memory: PredictedMemory) -> tuple[bool, str | None]:
    """Invariants essentiels d'une mémoire prédite (avant tout solveur)."""
    n = len(memory.labels)
    if n == 0:
        return False, "aucune entité détectée"
    if len(memory.successor) != n:
        return False, "successor et entités désynchronisés"
    for index, value in enumerate(memory.successor):
        if value != -1 and not (0 <= value < n):
            return False, f"successeur hors bornes en {index}: {value}"
        if value == index:
            return False, f"auto-successeur en {index}"
    if not (0 <= memory.start < n):
        return False, f"départ hors bornes: {memory.start}"
    if not any(value == -1 for value in memory.successor):
        return False, "aucun terminal (graphe entièrement cyclique ?)"
    for index, (start, end) in enumerate(memory.char_spans):
        if not (0 <= start < end <= len(memory.text)):
            return False, f"mention {index} hors bornes du texte"
    # marche de validation : détecte les cycles accessibles depuis le départ
    visited: set[int] = set()
    cursor = memory.start
    while cursor != -1:
        if cursor in visited:
            return False, f"cycle détecté en {cursor}"
        visited.add(cursor)
        cursor = memory.successor[cursor]
    return True, None


def solve_memory(memory: PredictedMemory) -> SolveResult:
    """Marche exacte départ → terminal ; ABSTENTION si la mémoire est invalide."""
    valid, reason = validate_memory(memory)
    if not valid:
        return SolveResult(status="abstain", reason=reason)
    path: list[int] = []
    cursor = memory.start
    while cursor != -1:
        path.append(cursor)
        cursor = memory.successor[cursor]
    return SolveResult(status="solved", terminal=path[-1], path=path)


def memory_to_public_input(
    memory: PredictedMemory,
    options: Sequence[int | str] | None = None,
    *,
    example_id: str | None = None,
) -> dict:
    """Vue publique S consommable par ``batch_from_problems`` (sans privé).

    ``options`` : entités candidates (indices ou labels). Par défaut, tous les
    terminaux — l'énoncé de la tâche fournit normalement ses candidats.
    """
    n = len(memory.labels)
    if options is None:
        option_indices = [index for index, value in enumerate(memory.successor) if value == -1]
    else:
        option_indices = [
            int(value) if isinstance(value, int) else memory.labels.index(str(value))
            for value in options
        ]
    for index in option_indices:
        if not (0 <= index < n):
            raise ValueError(f"candidat hors bornes: {index}")
    for index, target in enumerate(memory.successor):
        if target == -2:
            raise ValueError(
                "successeur INCONNU (-2) non supporté par l'exécuteur "
                "(A2 = propagation ; INCONNU ⇒ abstention, pas une arête)"
            )
    edges = [
        [memory.labels[index], memory.labels[target]]
        for index, target in enumerate(memory.successor)
        if target != -1
    ]
    return {
        "id": example_id or memory.id,
        "nodes": list(memory.labels),
        "edges": edges,
        "query": {"start": memory.labels[memory.start]},
        "options": [
            {"id": f"c{position}", "node": memory.labels[index]}
            for position, index in enumerate(option_indices)
        ],
    }


def memory_to_batch(
    memory: PredictedMemory,
    options: Sequence[int | str] | None = None,
    *,
    pad_nodes: int | None = None,
    pad_candidates: int | None = None,
    device: torch.device | str | None = None,
) -> RelationBatch:
    """Mémoire prédite → ``RelationBatch`` (entrée de l'exécuteur E3/E4b)."""
    public = memory_to_public_input(memory, options)
    return batch_from_problems(
        [public],
        pad_nodes=pad_nodes,
        pad_candidates=pad_candidates,
        device=device,
    )
