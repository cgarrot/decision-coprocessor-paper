"""Boucle d'entraînement CPU de l'étage S + métriques de diagnostic.

La QA (@ag-4, ``v2eval``) reste l'implémentation de référence pour
l'évaluation des portes ; les métriques d'ici servent aux courbes
d'entraînement et aux tests E0 (valeurs recalculées à la main). Le budget
est un paramètre de protocole : ``batch.hops`` n'est utilisé que pour les
dénominateurs publiés, jamais pour choisir ``steps``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import torch

from .executor import RelationExecutor
from .relation_data import RelationBatch, batch_from_problems

__all__ = ["TrainConfig", "TrainStats", "metrics_from_outputs", "trajectory_metrics", "train_executor"]


@dataclass
class TrainConfig:
    optimizer_steps: int = 400
    lr: float = 3e-3
    weight_decay: float = 0.0
    alpha: float = 0.5
    steps: int = 16
    batch_size: int = 64
    seed: int = 0
    grad_clip: float = 1.0


@dataclass
class TrainStats:
    optimizer_steps: int
    loss_history: list[float]
    final_metrics: dict
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "optimizer_steps": self.optimizer_steps,
            "loss_first": self.loss_history[0] if self.loss_history else None,
            "loss_last": self.loss_history[-1] if self.loss_history else None,
            "final_metrics": self.final_metrics,
            "config": self.config,
        }


def _chunks(items: Sequence[Any], size: int):
    for index in range(0, len(items), size):
        yield list(items[index : index + size])


def metrics_from_outputs(
    predicted_states: torch.Tensor,
    targets: torch.Tensor,
    final_logits: torch.Tensor,
    answer_index: torch.Tensor,
    candidate_mask: torch.Tensor | None = None,
) -> dict:
    """Métriques de diagnostic à partir de tenseurs bruts (testables à la main).

    ``predicted_states`` / ``targets`` : [B, T] ; ``final_logits`` : [B, K].
    ``candidate_mask`` (optionnel) garantit que l'argmax final **n'est jamais**
    un candidat de padding (E0-2).
    """
    correct_steps = predicted_states == targets
    score = final_logits
    if candidate_mask is not None:
        score = score.masked_fill(
            ~candidate_mask.bool(), torch.finfo(score.dtype).min
        )
    final_correct = score.argmax(dim=-1) == answer_index
    full = correct_steps.all(dim=1) & final_correct
    conditional = [None]
    for step in range(1, predicted_states.shape[1]):
        gate = correct_steps[:, step - 1]
        denominator = int(gate.sum())
        conditional.append(
            float((correct_steps[:, step] & gate).sum()) / denominator
            if denominator
            else None
        )
    return {
        "per_step": [
            float(correct_steps[:, step].float().mean())
            for step in range(predicted_states.shape[1])
        ],
        "conditional_transition": conditional,
        "final_accuracy": float(final_correct.float().mean()),
        "full_trajectory": float(full.float().mean()),
        "full_flags": full,
        "steps": int(predicted_states.shape[1]),
    }


@torch.no_grad()
def trajectory_metrics(
    executor: RelationExecutor,
    batch: RelationBatch,
    steps: int | None = None,
) -> dict:
    """Métriques de diagnostic : trajet complet, transitions, absorbant.

    - ``full_trajectory`` : état correct à **chaque** créneau (t=0..steps) ET
      réponse finale correcte (définition E0/E1) ;
    - ``per_step`` : exactitude du pointeur par créneau ;
    - ``conditional_transition`` : exactitude de ``s_{t+1}`` restreinte aux
      cas où ``s_t`` est correct (dénominateur exposé).
    """
    output = executor(batch, steps=steps)
    predicted = output.pointers.argmax(dim=-1)              # [B, T+1]
    total_steps = predicted.shape[1]
    if batch.state_targets is None:
        raise ValueError("métriques d'état exige state_targets (privé, évaluation)")
    targets = batch.state_targets
    if targets.shape[1] < total_steps:
        tail = targets[:, -1:].expand(-1, total_steps - targets.shape[1])
        targets = torch.cat([targets, tail], dim=1)
    targets = targets[:, :total_steps]

    return metrics_from_outputs(
        predicted, targets, output.logits, batch.answer_index,
        candidate_mask=batch.candidate_mask,
    )

def train_executor(
    problems: Sequence[Any],
    config: TrainConfig | None = None,
    *,
    executor: RelationExecutor,
    eval_problems: Sequence[Any] | None = None,
    pad_nodes: int | None = None,
    device: torch.device | str = "cpu",
    index_space: int | None = None,
) -> tuple[RelationExecutor, TrainStats]:
    """Entraîne l'exécuteur sur des problèmes B-V2 (cibles privées en loss)."""
    config = config or TrainConfig()
    torch.manual_seed(config.seed)
    generator = torch.Generator().manual_seed(config.seed)
    executor = executor.to(device)
    executor.train()
    optimizer = torch.optim.Adam(
        executor.parameters(),
        lr=config.lr,
        weight_decay=config.weight_decay,
    )
    batches = list(_chunks(list(problems), config.batch_size))
    if not batches:
        raise ValueError("aucun problème d'entraînement")

    history: list[float] = []
    for step in range(int(config.optimizer_steps)):
        items = batches[int(torch.randint(len(batches), (1,), generator=generator))]
        batch = batch_from_problems(
            items,
            pad_nodes=pad_nodes,
            device=device,
            index_space=index_space,
            index_seed=step,
        )
        output = executor(batch, steps=config.steps)
        loss, _ = executor.loss(output, batch, alpha=config.alpha)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(executor.parameters(), config.grad_clip)
        optimizer.step()
        history.append(float(loss.detach()))

    executor.eval()
    metrics: dict = {}
    if eval_problems is not None:
        eval_batch = batch_from_problems(
            list(eval_problems), pad_nodes=pad_nodes, device=device
        )
        metrics = trajectory_metrics(executor, eval_batch, steps=config.steps)
        metrics.pop("full_flags", None)
    stats = TrainStats(
        optimizer_steps=int(config.optimizer_steps),
        loss_history=history,
        final_metrics=metrics,
        config={
            "lr": config.lr,
            "alpha": config.alpha,
            "steps": config.steps,
            "batch_size": config.batch_size,
            "seed": config.seed,
        },
    )
    return executor, stats
