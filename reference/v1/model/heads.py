"""Tête de décision directe — SPEC §5.4.

Readout partagé, sans neurone associé durablement à une classe :

    q = Pq(LayerNorm(q_raw))                      [B, d]
    c = Pc(LayerNorm(c_raw))                      [B, K, d]
    features_i = concat(q, c_i, q*c_i, |q-c_i|)   [B, K, 4d]
    logit0_i = MLP_partagé(features_i)            [B, K]
    p0 = softmax masqué(logit0)

``q_raw`` est le dernier token **valide** (padding à droite, SPEC §5.3) ;
``c_raw`` est la **moyenne masquée** des tokens de description de chaque
candidat (SPEC §5.4). La même fonction score tous les candidats.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from .backbone import last_valid_index

__all__ = [
    "HeadOutput",
    "DecisionHead",
    "masked_softmax",
    "masked_segment_mean",
    "decision_cross_entropy",
]


def masked_softmax(
    logits: torch.Tensor,
    mask: torch.Tensor,
    dim: int = -1,
    *,
    dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    """Softmax masqué, sans NaN, en FP32 (SPEC §10.4).

    Les positions invalides ont une probabilité exactement nulle. Une ligne
    entièrement invalide donne un vecteur de zéros (jamais de NaN).
    """
    bool_mask = mask.to(device=logits.device, dtype=torch.bool)
    if bool_mask.shape != logits.shape:
        raise ValueError("mask et logits de formes différentes")
    work = logits.to(dtype=dtype)
    neg = torch.finfo(work.dtype).min
    masked = work.masked_fill(~bool_mask, neg)
    probs = torch.softmax(masked, dim=dim)
    probs = torch.where(bool_mask, probs, torch.zeros_like(probs))
    probs = torch.nan_to_num(probs, nan=0.0, posinf=0.0, neginf=0.0)
    denom = probs.sum(dim=dim, keepdim=True)
    return probs / denom.clamp(min=torch.finfo(probs.dtype).tiny)


def masked_segment_mean(
    hidden: torch.Tensor,
    starts: torch.Tensor,
    lens: torch.Tensor,
    candidate_mask: torch.Tensor,
    attention_mask: torch.Tensor | None = None,
) -> torch.Tensor:
    """Moyenne masquée des tokens ``[start, start+len)`` par candidat.

    Utilise des sommes préfixes (O(B·L·D)) plutôt qu'un masque dense [B,K,L].
    """
    if hidden.dim() != 3:
        raise ValueError("hidden doit être [B, L, D]")
    batch, length, dim = hidden.shape
    device = hidden.device

    starts = starts.to(device=device, dtype=torch.long)
    lens = lens.to(device=device, dtype=torch.long)
    mask = candidate_mask.to(device=device, dtype=torch.bool)
    if starts.shape != lens.shape or starts.shape != mask.shape:
        raise ValueError("starts/lens/candidate_mask doivent avoir la même forme [B, K]")
    if starts.shape[0] != batch:
        raise ValueError("starts et hidden n'ont pas le même batch")

    # Mean = opération sensible : calcul en FP32 si le hidden est réduit.
    compute = hidden.float() if hidden.dtype in (torch.float16, torch.bfloat16) else hidden

    valid = mask & (lens > 0)
    if attention_mask is not None:
        valid_lengths = attention_mask.to(device=device).sum(dim=1)
        valid = valid & (starts >= 0) & ((starts + lens) <= valid_lengths.unsqueeze(1))

    prefix = compute.cumsum(dim=1)
    end_index = (starts + lens - 1).clamp_(min=0, max=length - 1)
    before_index = (starts - 1).clamp_(min=0, max=length - 1)
    end_sum = prefix.gather(1, end_index.unsqueeze(-1).expand(-1, -1, dim))
    before_sum = prefix.gather(1, before_index.unsqueeze(-1).expand(-1, -1, dim))
    before_sum = torch.where(
        (starts > 0).unsqueeze(-1), before_sum, torch.zeros_like(before_sum)
    )
    segment_sum = end_sum - before_sum
    counts = lens.clamp(min=1).unsqueeze(-1).to(segment_sum.dtype)
    pooled = segment_sum / counts
    return torch.where(valid.unsqueeze(-1), pooled, torch.zeros_like(pooled))


@dataclass
class HeadOutput:
    """Sorties de la tête directe (le sidecar consomme q/c, la loss logits0)."""

    base_logits: torch.Tensor          # [B, K]
    probabilities: torch.Tensor        # [B, K] FP32
    query: torch.Tensor                # [B, d]
    candidates: torch.Tensor           # [B, K, d]
    features: torch.Tensor | None = None


class DecisionHead(nn.Module):
    """Tête dynamique partagée (SPEC §5.4)."""

    def __init__(
        self,
        hidden_size: int,
        width: int = 256,
        mlp_width: int | None = None,
        layernorm_eps: float = 1e-5,
    ) -> None:
        super().__init__()
        if width <= 0:
            raise ValueError("width doit être > 0")
        self.hidden_size = int(hidden_size)
        self.width = int(width)
        self.mlp_width = int(mlp_width) if mlp_width is not None else 2 * self.width

        self.ln_query = nn.LayerNorm(self.hidden_size, eps=layernorm_eps)
        self.ln_candidates = nn.LayerNorm(self.hidden_size, eps=layernorm_eps)
        self.proj_query = nn.Linear(self.hidden_size, self.width)
        self.proj_candidates = nn.Linear(self.hidden_size, self.width)
        self.mlp = nn.Sequential(
            nn.Linear(4 * self.width, self.mlp_width),
            nn.GELU(),
            nn.Linear(self.mlp_width, 1),
        )

    def parameter_count(self) -> tuple[int, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return total, trainable

    def forward(
        self,
        hidden: torch.Tensor,
        *,
        candidate_starts: torch.Tensor,
        candidate_lens: torch.Tensor,
        candidate_mask: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> HeadOutput:
        if hidden.dim() != 3:
            raise ValueError("hidden doit être [B, L, D]")
        # Frontière de précision (SPEC §10.4) : le backbone peut produire H en
        # bf16 ; les modules entraînables restent FP32. Conversion explicite du
        # flux ici ⇒ aucun autocast externe requis (correctif @ag-5).
        hidden = hidden.to(dtype=self.proj_query.weight.dtype)
        batch = hidden.shape[0]
        if attention_mask is None:
            attention_mask = torch.ones(
                (batch, hidden.shape[1]), dtype=torch.long, device=hidden.device
            )
        last_index = last_valid_index(attention_mask)
        query_raw = hidden.gather(
            1, last_index.view(batch, 1, 1).expand(-1, -1, hidden.shape[-1])
        ).squeeze(1)  # [B, D]

        candidates_raw = masked_segment_mean(
            hidden,
            candidate_starts,
            candidate_lens,
            candidate_mask,
            attention_mask=attention_mask,
        )  # [B, K, D]

        query = self.proj_query(self.ln_query(query_raw))              # [B, d]
        candidates = self.proj_candidates(self.ln_candidates(candidates_raw))  # [B, K, d]

        query_expanded = query.unsqueeze(1).expand_as(candidates)
        features = torch.cat(
            [query_expanded, candidates, query_expanded * candidates, (query_expanded - candidates).abs()],
            dim=-1,
        )
        base_logits = self.mlp(features).squeeze(-1)                   # [B, K]
        probabilities = masked_softmax(base_logits, candidate_mask)
        return HeadOutput(
            base_logits=base_logits,
            probabilities=probabilities,
            query=query,
            candidates=candidates,
            features=features,
        )


def decision_cross_entropy(
    logits: torch.Tensor, candidate_mask: torch.Tensor, labels: torch.Tensor
) -> torch.Tensor:
    """Cross-entropy masquée en FP32 (SPEC §10.4). ``labels`` = index candidat."""
    bool_mask = candidate_mask.to(device=logits.device, dtype=torch.bool)
    safe = logits.to(dtype=torch.float32).masked_fill(
        ~bool_mask, torch.finfo(torch.float32).min
    )
    return F.cross_entropy(safe, labels.to(device=logits.device, dtype=torch.long))
