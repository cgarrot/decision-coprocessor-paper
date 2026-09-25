"""Exécuteur de transitions vS — audit §7.3, amendements DECISION-V2 §3.3.

```text
h_0, p_0 = init(features, question, départ)          # p_0 = one-hot(départ)
m_i(t)   = aggregate_j phi(h_j(t), h_i(t), rel_ji)   # messages locaux aux arêtes
h_i(t+1) = update(h_i(t), m_i(t), question)          # transition PARTAGÉE
p_t      = softmax(pointer_head(h(t)))               # pointeur actif
score_c  = readout_shared(summary(p_T, h_T), features_brutes_c)
```

**Anti-raccourci (point racine de l'audit §3)** :

- la lecture finale ne reçoit **ni** `question` **ni** candidats contextualisés :
  uniquement le résumé d'état calculé et les features *brutes* du candidat,
  via un score partagé entre candidats ;
- `p_0` est le pointeur de départ contraint par la tâche, jamais un résumé
  contextualisé libre ;
- le terminal est absorbant (`h` figé sur les nœuds sans successeur) ;
- le chemin direct vit dans un module **séparé** (:class:`DirectScorer`).

La perte pilote utilise les poids par créneau fournis par le contrat de
données (``trace_loss_weights``) : la masse du terminal absorbant n'est pas
surcomptée (audit §7.4).
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from .relation_data import RelationBatch

__all__ = [
    "ExecutorConfig",
    "ExecutorOutput",
    "SharedTransition",
    "PointerHead",
    "CandidateReadout",
    "TiedCandidateReadout",
    "RelationExecutor",
    "DirectScorer",
]


@dataclass
class ExecutorConfig:
    """Configuration de l'exécuteur S. ``alpha`` du pilote — à consigner (E0-6).

    ``readout_kind`` : ``concat`` (lecture directe features concaténées) ou
    ``tied`` (identités candidates projetées par le MÊME codeur que les états —
    correction préparée pour l'anomalie E2 des index non vus).
    """

    feature_dim: int
    question_dim: int
    relation_dim: int = 1
    d_model: int = 64
    hidden: int = 128
    max_steps: int = 16          # budget fixe pendant la phase mécanisme (§7.5)
    alpha: float = 0.5           # poids de la CE d'état (fixé au pilote puis consigné)
    readout_kind: str = "concat"  # concat | tied

    def __post_init__(self) -> None:
        if self.readout_kind not in ("concat", "tied"):
            raise ValueError(f"readout_kind inconnu: {self.readout_kind!r}")


@dataclass
class ExecutorOutput:
    """Sortie : logits candidats + trajectoire de pointeurs (t = 0..steps)."""

    logits: torch.Tensor           # [B, K]
    probabilities: torch.Tensor    # [B, K]
    pointer_logits: torch.Tensor   # [B, T+1, N]
    pointers: torch.Tensor         # [B, T+1, N] — pointeurs utilisés (forçage inclus)
    hidden: torch.Tensor           # [B, N, d]
    steps: int
    hidden_steps: torch.Tensor | None = None   # [B, T+1, N, d] si collecté

    def pointer_at(self, step: int) -> torch.Tensor:
        return self.pointers[:, int(step)]

    def predicted_state(self, step: int) -> torch.Tensor:
        return self.pointers[:, int(step)].argmax(dim=-1)


class SharedTransition(nn.Module):
    """Transition PARTAGÉE, locale aux arêtes : ``m_i = Σ_j φ(h_j, h_i, rel_ji)``.

    L'état est ``s_t = (h_t, p_t)`` : seuls les nœuds avec ``p_j > 0`` émettent
    des messages (front d'onde), et le pointeur précédent est réinjecté dans
    la cellule locale (``p_i``). Sans cela, l'état n'a aucun marqueur du nœud
    actif et les sauts multiples ne sont pas apprenables (diagnostic E0).
    """

    def __init__(
        self,
        d_model: int,
        hidden: int,
        question_dim: int,
        relation_dim: int,
        pointer_dim: int = 1,
    ) -> None:
        super().__init__()
        self.phi = nn.Sequential(
            nn.Linear(2 * d_model + relation_dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, d_model),
        )
        self.cell = nn.GRUCell(d_model + question_dim + pointer_dim, d_model)
        self.norm = nn.LayerNorm(d_model)

    def forward(
        self,
        h: torch.Tensor,
        edge_mask: torch.Tensor,
        relation: torch.Tensor,
        question: torch.Tensor,
        pointer: torch.Tensor,
        node_mask: torch.Tensor,
        frozen_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        batch, nodes, d_model = h.shape
        source = h.unsqueeze(2).expand(batch, nodes, nodes, d_model)
        target = h.unsqueeze(1).expand(batch, nodes, nodes, d_model)
        messages = self.phi(torch.cat([source, target, relation], dim=-1))
        # Le pointeur fait partie de l'état : seuls les nœuds actifs émettent
        # (front d'onde local) ; l'agrégat est normalisé par la masse active.
        emitter = pointer.unsqueeze(2).expand(batch, nodes, nodes)
        weighted = messages * emitter.unsqueeze(-1)
        active_mass = (edge_mask.to(messages.dtype) * emitter).sum(dim=1)
        aggregated = weighted.sum(dim=1) / active_mass.unsqueeze(-1).clamp(min=1e-6)

        question_expanded = question.unsqueeze(1).expand(
            batch, nodes, question.shape[1]
        )
        pointer_expanded = pointer.unsqueeze(-1)
        updates = self.cell(
            torch.cat(
                [aggregated, question_expanded, pointer_expanded], dim=-1
            ).reshape(batch * nodes, -1),
            h.reshape(batch * nodes, -1),
        ).reshape(batch, nodes, d_model)

        updated = self.norm(updates)
        if frozen_mask is not None:
            # Terminal ABSORBANT : un nœud déjà désigné terminal ne change
            # plus ; les autres (y compris un terminal pas encore atteint)
            # reçoivent leurs messages.
            updated = torch.where(frozen_mask.unsqueeze(-1), h, updated)
        return updated * node_mask.unsqueeze(-1)


class PointerHead(nn.Module):
    """``p_t = softmax(pointer_head(h(t)))`` sur les nœuds valides."""

    def __init__(self, d_model: int) -> None:
        super().__init__()
        self.proj = nn.Linear(d_model, 1)

    def forward(self, h: torch.Tensor, node_mask: torch.Tensor) -> torch.Tensor:
        logits = self.proj(h).squeeze(-1)
        logits = logits.masked_fill(
            ~node_mask.bool(), torch.finfo(logits.dtype).min
        )
        return logits

    @staticmethod
    def probabilities(logits: torch.Tensor, node_mask: torch.Tensor) -> torch.Tensor:
        probabilities = torch.softmax(logits, dim=-1)
        probabilities = torch.nan_to_num(probabilities, nan=0.0)
        return probabilities * node_mask.to(probabilities.dtype)


class CandidateReadout(nn.Module):
    """Score PARTAGÉ état × candidat (aucun accès à la question ni à un contexte)."""

    def __init__(self, d_model: int, feature_dim: int, hidden: int) -> None:
        super().__init__()
        self.candidate_proj = nn.Linear(feature_dim, d_model)
        self.score = nn.Sequential(
            nn.Linear(2 * d_model, hidden),
            nn.GELU(),
            nn.Linear(hidden, 1),
        )

    def forward(
        self,
        state_summary: torch.Tensor,         # [B, d]
        candidate_features: torch.Tensor,    # [B, K, F] — brut, non contextualisé
    ) -> torch.Tensor:
        candidates = self.candidate_proj(candidate_features)
        summary = state_summary.unsqueeze(1).expand_as(candidates)
        return self.score(torch.cat([summary, candidates], dim=-1)).squeeze(-1)


class TiedCandidateReadout(nn.Module):
    """Lecture à identités PARTAGÉES avec le codeur d'entités (branche E3 « tied »).

    Les features brutes du candidat passent par le **même** ``memory_encoder``
    que les états : la correspondance « état final = ce nœud » devient une
    similarité directe (produit summary×candidat) au lieu d'une projection
    d'identité séparée — préparation de la correction de l'anomalie E2
    (index d'entité non vus). Aucun accès à la question ni au contexte.
    """

    def __init__(self, memory_encoder: nn.Module, d_model: int, hidden: int) -> None:
        super().__init__()
        self.memory_encoder = memory_encoder
        self.score = nn.Sequential(
            nn.Linear(3 * d_model, hidden),
            nn.GELU(),
            nn.Linear(hidden, 1),
        )

    def forward(
        self,
        state_summary: torch.Tensor,         # [B, d]
        candidate_features: torch.Tensor,    # [B, K, F] — brut
    ) -> torch.Tensor:
        candidates = self.memory_encoder(candidate_features)
        summary = state_summary.unsqueeze(1).expand_as(candidates)
        features = torch.cat([summary, candidates, summary * candidates], dim=-1)
        return self.score(features).squeeze(-1)


class RelationExecutor(nn.Module):
    """Exécuteur vS : mémoire, état, transition partagée, pointeur, lecture."""

    def __init__(self, config: ExecutorConfig) -> None:
        super().__init__()
        self.config = config
        self.memory_encoder = nn.Sequential(
            nn.Linear(config.feature_dim, config.d_model),
            nn.LayerNorm(config.d_model),
            nn.GELU(),
        )
        self.state_init = nn.Sequential(
            nn.Linear(config.d_model + config.question_dim, config.hidden),
            nn.GELU(),
            nn.Linear(config.hidden, config.d_model),
            nn.LayerNorm(config.d_model),
        )
        self.transition = SharedTransition(
            config.d_model,
            config.hidden,
            config.question_dim,
            config.relation_dim,
        )
        self.pointer_head = PointerHead(config.d_model)
        if config.readout_kind == "tied":
            self.readout = TiedCandidateReadout(
                self.memory_encoder, config.d_model, config.hidden
            )
        else:
            self.readout = CandidateReadout(
                config.d_model, config.feature_dim, config.hidden
            )

    # ---- modules (séparation exigée par l'audit §3.2 / E0-4) ------------
    def initialize(self, batch: RelationBatch) -> tuple[torch.Tensor, torch.Tensor]:
        """Lecture mémoire + initialisation contrainte : ``p_0 = one-hot(départ)``."""
        encoded = self.memory_encoder(batch.entity_features)
        question = batch.question.unsqueeze(1).expand(-1, encoded.shape[1], -1)
        hidden = self.state_init(torch.cat([encoded, question], dim=-1))
        hidden = hidden * batch.node_mask.unsqueeze(-1)
        pointer = F.one_hot(
            batch.start_index, hidden.shape[1]
        ).to(hidden.dtype) * batch.node_mask.to(hidden.dtype)
        return hidden, pointer

    def state_summary(
        self, hidden: torch.Tensor, pointer: torch.Tensor
    ) -> torch.Tensor:
        """Résumé d'état lu : moyenne des états pondérée par le pointeur."""
        return (pointer.unsqueeze(-1) * hidden).sum(dim=1)

    def candidate_features(self, batch: RelationBatch) -> torch.Tensor:
        """Features BRUTES des candidats (jamais l'état contextualisé)."""
        return batch.entity_features.gather(
            1,
            batch.candidates.unsqueeze(-1).expand(
                -1, -1, batch.entity_features.shape[-1]
            ),
        )

    def forward(
        self,
        batch: RelationBatch,
        *,
        steps: int | None = None,
        teacher_states: torch.Tensor | None = None,
        teacher_forcing: bool = False,
        collect_hidden: bool = False,
    ) -> ExecutorOutput:
        """Déroule ``steps`` transitions (budget fixe si ``None``).

        ``teacher_states`` = amorçage d'entraînement, jamais une entrée
        d'inférence ; ``batch.hops`` n'est **jamais** lu ici.
        """
        steps = self.config.max_steps if steps is None else int(steps)
        if steps < 0:
            raise ValueError(f"steps négatif: {steps}")
        if teacher_forcing and teacher_states is None:
            raise ValueError("teacher_forcing exige teacher_states")

        hidden, pointer = self.initialize(batch)
        terminal_mask = batch.node_mask & ~batch.edge_mask.any(dim=2)  # public
        pointer_logits = [self.pointer_head(hidden, batch.node_mask)]
        pointers = [pointer]
        hidden_steps = [hidden] if collect_hidden else None

        for step in range(steps):
            previous_terminal = terminal_mask.gather(
                1, pointer.argmax(dim=-1, keepdim=True)
            ).squeeze(-1)
            frozen_mask = terminal_mask & previous_terminal.unsqueeze(-1)
            hidden = self.transition(
                hidden,
                batch.edge_mask,
                batch.relation,
                batch.question,
                pointer,
                batch.node_mask,
                frozen_mask,
            )
            logits = self.pointer_head(hidden, batch.node_mask)
            used = PointerHead.probabilities(logits, batch.node_mask)
            if teacher_forcing and teacher_states is not None:
                index = min(step + 1, teacher_states.shape[1] - 1)
                used = F.one_hot(
                    teacher_states[:, index], hidden.shape[1]
                ).to(hidden.dtype) * batch.node_mask.to(hidden.dtype)
            else:
                # Terminal absorbant STRUCTUREL (audit §7.3) : si le pointeur
                # précédent est déjà sur un terminal (nœud sans successeur,
                # information publique), il ne bouge plus.
                used = torch.where(previous_terminal[:, None], pointer, used)
            pointer = used
            pointer_logits.append(logits)
            pointers.append(used)
            if collect_hidden:
                hidden_steps.append(hidden)

        summary = self.state_summary(hidden, pointers[-1])
        logits = self.readout(summary, self.candidate_features(batch))
        masked = logits.masked_fill(
            ~batch.candidate_mask.bool(), torch.finfo(logits.dtype).min
        )
        probabilities = torch.softmax(masked, dim=-1)
        probabilities = probabilities * batch.candidate_mask.to(probabilities.dtype)

        return ExecutorOutput(
            logits=logits,
            probabilities=probabilities,
            pointer_logits=torch.stack(pointer_logits, dim=1),
            pointers=torch.stack(pointers, dim=1),
            hidden=hidden,
            steps=steps,
            hidden_steps=(
                torch.stack(hidden_steps, dim=1) if collect_hidden else None
            ),
        )

    # ---- perte pilote ---------------------------------------------------
    def loss(
        self,
        output: ExecutorOutput,
        batch: RelationBatch,
        *,
        alpha: float | None = None,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        """``L = CE(finale) + alpha × Σ_t w_t · CE(état_t, cible_t)``.

        ``w_t`` vient du contrat de données (somme 1 par exemple, masse du
        terminal absorbant répartie) ; à défaut, moyenne uniforme des créneaux.
        """
        alpha = self.config.alpha if alpha is None else float(alpha)
        final_ce = F.cross_entropy(
            output.logits.masked_fill(
                ~batch.candidate_mask.bool(), torch.finfo(output.logits.dtype).min
            ),
            batch.answer_index,
        )

        if batch.state_targets is None:
            zero = torch.zeros((), device=output.logits.device)
            return final_ce, {"ce_final": float(final_ce.detach()), "ce_state": 0.0, "alpha": alpha}

        targets = batch.state_targets
        total_steps = output.pointer_logits.shape[1]
        if targets.shape[1] < total_steps:
            tail = targets[:, -1:].expand(-1, total_steps - targets.shape[1])
            targets = torch.cat([targets, tail], dim=1)
        targets = targets[:, :total_steps]

        batch_size, steps, nodes = output.pointer_logits.shape
        per_step = F.cross_entropy(
            output.pointer_logits.reshape(batch_size * steps, nodes),
            targets.reshape(-1),
            reduction="none",
        ).reshape(batch_size, steps)
        if batch.state_weights is not None:
            weights = batch.state_weights[:, :total_steps]
            state_ce = (per_step * weights).sum(dim=1).mean()
        else:
            state_ce = per_step.mean()
        total = final_ce + alpha * state_ce
        return total, {
            "ce_final": float(final_ce.detach()),
            "ce_state": float(state_ce.detach()),
            "alpha": alpha,
        }


class DirectScorer(nn.Module):
    """Chemin direct SÉPARÉ (contrôle E6), sans exécution ni état calculé."""

    def __init__(self, feature_dim: int, d_model: int = 64, hidden: int = 128) -> None:
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(feature_dim, d_model), nn.GELU())
        self.readout = CandidateReadout(d_model, feature_dim, hidden)

    def forward(self, batch: RelationBatch) -> torch.Tensor:
        encoded = self.encoder(batch.entity_features)
        mask = batch.node_mask.unsqueeze(-1).to(encoded.dtype)
        summary = (encoded * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        candidates = batch.entity_features.gather(
            1,
            batch.candidates.unsqueeze(-1).expand(
                -1, -1, batch.entity_features.shape[-1]
            ),
        )
        return self.readout(summary, candidates)
