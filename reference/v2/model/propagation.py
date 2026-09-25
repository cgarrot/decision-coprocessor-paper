"""V2.2-A2 — propagation différentiable p_{t+1} = p_t @ A (audit §6.2).

Sémantique FIGÉE (V22_A2_ADDENDUM.md, contre-signé) :

- Espace d'état : N nœuds + 1 sink INCONNU (index ``N``).
- Classes de transition d'une mention : successeurs (0..N-1), TERMINAL
  (dans ``object_logits`` fact-level : index N), INCONNU (index N+1 de la
  distribution de transition, matérialisé par la **masse de sujet manquante**
  ``1 − Σ_f P(sujet_f = u)``).
- TERMINAL = **self-loop sur i** (l'identité du terminal atteint est
  conservée) ; INCONNU = **sink absorbant global**.
- Pas de renormalisation : la réponse est l'argmax sur les nœuds CANDIDATS de
  p_T (règle A1, tie-break ``eps`` par clé stable) ; le CE de réponse porte sur
  l'état complet (les masses hors candidats pénalisent).
- T = 20 pas (absorbant).

Deux sources de A :
- ``transition_matrix_from_facts`` : **source A2** — agrégation des têtes
  fact-level (les seules supervisées en mode fact ; le head bilinéaire
  ``successor_logits`` n'est pas entraîné dans ce mode, top-1 ≈ hasard mesuré).
- ``transition_matrix_bilinear`` : parité A1 historique (``successor_logits``),
  conservée pour rejouer A1-bis/contrôles.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F

__all__ = [
    "EPS_TIE",
    "PropagationResult",
    "transition_matrix_from_facts",
    "transition_matrix_bilinear",
    "start_distribution",
    "propagate",
    "propagate_from_facts",
    "answer_index",
    "answer_nll",
    "state_nll",
    "gold_state_targets",
]

EPS_TIE = 1e-3   # tie-break des argmax (mandat n°4, échelle logit/probabilité)
T_STEPS = 20


@dataclass
class PropagationResult:
    """Sortie de propagation : états [B, T, N+1], final [B, N+1], réponse [B]."""

    states: torch.Tensor
    final: torch.Tensor
    answer: torch.Tensor


def transition_matrix_from_facts(
    subject_logits: torch.Tensor,
    object_logits: torch.Tensor,
    fact_mask: torch.Tensor,
) -> torch.Tensor:
    """A [B, N+1, N+1] depuis les têtes fact-level (source A2).

    ``mass[u, v] = Σ_f P(sujet_f = u) · P(objet_f = v)`` pour v < N ;
    ``mass[u, TERMINAL] = Σ_f P(sujet_f = u) · P(objet_f = TERMINAL)``.
    Règle de stochasticité figée : ``A[u, ·] = mass[u, ·] / max(1, Σ_f P(sujet_f = u))``
    et ``A[u, sink] = max(0, 1 − Σ_f P(sujet_f = u))`` (masse INCONNU =
    « aucun fait ne désigne u comme sujet » ; division seulement si les votes
    de sujet dépassent 1). Ligne sink = one-hot (absorbant).
    """
    boolean = fact_mask.bool()
    zero = torch.zeros_like(subject_logits)
    subject_logits = torch.where(boolean[..., None], subject_logits,
                                 torch.full_like(subject_logits, -1e9))
    object_logits = torch.where(boolean[..., None], object_logits,
                                torch.full_like(object_logits, -1e9))
    subj = torch.softmax(subject_logits.float(), dim=-1)          # [B, F, N]
    obj = torch.softmax(object_logits.float(), dim=-1)            # [B, F, N+1]
    subj = subj * boolean[..., None]        # faits masqués = contribution NULLE
    obj = obj * boolean[..., None]
    batch, _, n_entities = subj.shape
    mass = torch.einsum("bfu,bfc->buc", subj, obj)                # [B, N, N+1]
    row_mass = mass.sum(dim=-1)                                   # [B, N] = Σ_f subj
    scale = row_mass.clamp(min=1.0)                               # /max(1, Σ subj)
    device = subj.device
    matrix = torch.zeros(batch, n_entities + 1, n_entities + 1,
                         dtype=mass.dtype, device=device)
    matrix[:, :n_entities, :n_entities] = mass[:, :, :n_entities] / scale[..., None]
    diagonal = mass[:, :, n_entities] / scale                     # masse TERMINAL
    matrix[:, torch.arange(n_entities, device=device),
           torch.arange(n_entities, device=device)] += diagonal
    matrix[:, :n_entities, n_entities] = (1.0 - row_mass).clamp(min=0.0)
    matrix[:, n_entities, n_entities] = 1.0
    return matrix


def transition_matrix_bilinear(
    successor_logits: torch.Tensor,
    *,
    with_sink: bool = True,
) -> torch.Tensor:
    """A [B, N+1, N+1] depuis ``successor_logits`` (parité A1 historique).

    Classes attendues : N successeurs + TERMINAL (index N) [+ INCONNU (N+1)
    si présent]. Terminal = self-loop sur i ; sink optionnel (absorbant).
    """
    probs = torch.softmax(successor_logits.float(), dim=-1)
    batch, n_entities, classes = probs.shape
    device = probs.device
    matrix = torch.zeros(batch, n_entities + 1, n_entities + 1,
                         dtype=probs.dtype, device=device)
    matrix[:, :n_entities, :n_entities] = probs[:, :, :n_entities]
    matrix[:, torch.arange(n_entities, device=device),
           torch.arange(n_entities, device=device)] += probs[:, :, n_entities]
    if classes > n_entities + 1:
        if not with_sink:
            raise ValueError(
                "masse INCONNU présente (classes N+2) : with_sink=False laisserait "
                "des lignes non stochastiques"
            )
        matrix[:, :n_entities, n_entities] = probs[:, :, n_entities + 1]
    matrix[:, n_entities, n_entities] = 1.0
    return matrix


def start_distribution(
    start: torch.Tensor, n_entities: int, *, dtype: torch.dtype | None = None
) -> torch.Tensor:
    """p_0 = one-hot(start) [B, N+1] (le sink n'est jamais le départ)."""
    batch = start.shape[0]
    p0 = torch.zeros(batch, n_entities + 1, dtype=dtype or torch.float32,
                     device=start.device)
    valid = (start >= 0) & (start < n_entities)
    rows = torch.arange(batch, device=start.device)
    p0[rows[valid], start[valid]] = 1.0
    invalid = ~valid
    if bool(invalid.any()):   # départ indéterminé : uniforme sur les nœuds
        p0[invalid, :n_entities] = 1.0 / n_entities
    return p0


def propagate(p0: torch.Tensor, matrix: torch.Tensor, steps: int = T_STEPS) -> torch.Tensor:
    """États [B, T, S] : p_{t+1} = p_t @ A (différentiable, sans in-place)."""
    states = []
    p = p0
    for _ in range(int(steps)):
        p = torch.bmm(p.unsqueeze(1), matrix).squeeze(1)
        states.append(p)
    return torch.stack(states, dim=1)


def propagate_from_facts(
    subject_logits: torch.Tensor,
    object_logits: torch.Tensor,
    fact_mask: torch.Tensor,
    start: torch.Tensor,
    *,
    steps: int = T_STEPS,
    candidate_mask: torch.Tensor | None = None,
) -> PropagationResult:
    """Propagation complète A2 (fact-level) + réponse argmax candidats."""
    matrix = transition_matrix_from_facts(subject_logits, object_logits, fact_mask)
    n_entities = matrix.shape[-1] - 1
    p0 = start_distribution(start, n_entities, dtype=matrix.dtype)
    states = propagate(p0, matrix, steps)
    final = states[:, -1]
    if candidate_mask is None:
        candidate_mask = torch.ones(final.shape[0], n_entities, dtype=torch.bool,
                                    device=final.device)
    answer = answer_index(final, candidate_mask)
    return PropagationResult(states=states, final=final, answer=answer)


def answer_index(
    final: torch.Tensor,
    candidate_mask: torch.Tensor,
    labels: list[list[str]] | None = None,
    *,
    eps: float = EPS_TIE,
) -> torch.Tensor:
    """Argmax sur les nœuds CANDIDATS de ``final`` [B, S] — tie-break stable.

    ``candidate_mask`` : [B, N] (les candidats sont des nœuds, jamais le sink).
    À écart ≤ eps, la clé stable est l'ordre alphabétique des labels (mandat
    n°4) ; sans labels, l'ordre d'index. Retourne -1 si aucun candidat.
    """
    values = final.float()
    batch, n_entities = candidate_mask.shape
    result = torch.full((batch,), -1, dtype=torch.long, device=final.device)
    for row in range(batch):
        candidates = [index for index in range(n_entities)
                      if bool(candidate_mask[row, index])]
        if not candidates:
            continue
        if labels is not None:
            candidates = sorted(candidates, key=lambda index: labels[row][index])
        best = max(float(values[row, index]) for index in candidates)
        for index in candidates:
            if float(values[row, index]) >= best - eps:
                result[row] = index
                break
    return result


def answer_nll(final: torch.Tensor, target: torch.Tensor,
               eps: float = 1e-12) -> torch.Tensor:
    """NLL de la réponse = −log p_T[terminal gold] sur l'état COMPLET (pas de renormalisation)."""
    picked = final.gather(1, target.clamp(min=0).unsqueeze(1)).squeeze(1)
    valid = target >= 0
    loss = -picked.clamp(min=eps).log()
    return torch.where(valid, loss, torch.zeros_like(loss))


def state_nll(
    states: torch.Tensor,
    targets: torch.Tensor,
    mask: torch.Tensor | None = None,
    eps: float = 1e-12,
) -> torch.Tensor:
    """NLL moyen des états prédits vs cibles par pas (β·CE états)."""
    picked = states.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
    loss = -picked.clamp(min=eps).log()
    if mask is not None:
        weights = mask.float()
        return (loss * weights).sum() / weights.sum().clamp(min=1.0)
    return loss.mean()


def gold_state_targets(path: list[int], terminal: int, steps: int = T_STEPS) -> list[int]:
    """Cibles d'état : nœud gold au pas t, terminal absorbant ensuite."""
    trajectory = list(path) if path else []
    if terminal >= 0 and (not trajectory or trajectory[-1] != terminal):
        trajectory.append(terminal)
    if not trajectory:
        return []
    return [trajectory[min(step, len(trajectory) - 1)] for step in range(1, steps + 1)]
