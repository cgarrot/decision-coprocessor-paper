"""Sidecar latent récurrent + base commune des raffiners + assemblage — SPEC §5.5-5.6, §5.8, §6.1.

Ordre exact du forward pour le sidecar récurrent (pseudocode §5.8) :

1. ``H`` encodé UNE fois par le backbone gelé ;
2. tête directe → ``logit0``, ``q``, ``c`` ;
3. si ``budget == 0`` : retour immédiat des **mêmes** logits que la tête
   directe (le raffineur n'est ni projeté ni déroulé) ;
4. sinon ``memory_keys``/``memory_values`` calculés une seule fois, puis
   ``budget`` applications du **même** bloc récurrent partagé ;
5. correction résiduelle ``delta_i = CorrectionHead(concat(q, c_i, r_i))``,
   ``logit_t_i = logit0_i + delta_i``.

``MemoryCorrectionBase`` factorise la mémoire projetée et la correction
résiduelle pour les trois raffiners contrôlés (§6.1) :

- ``LatentSidecar`` (R1/R2/R4) : bloc partagé, budget = nombre d'étapes ;
- ``NonRecurrentMemory`` (B3) : **une seule passe** d'un bloc élargi, params
  comparables au sidecar ;
- ``UnsharedStack`` (B4) : ``n`` blocs **non partagés** appliqués
  séquentiellement, profondeur ≈ n étapes récurrentes.

Propriétés garanties (SPEC §5.7) : aucune génération textuelle, mémoire
jamais mélangée entre exemples d'un lot, un seul encodage backbone par
exemple et par forward quel que soit le budget, K variable avec masque.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from .heads import DecisionHead, decision_cross_entropy, masked_softmax
from .serialization import BatchEncoded

__all__ = [
    "AttentionBlock",
    "RecurrentBlock",
    "MemoryCorrectionBase",
    "LatentSidecar",
    "CoprocessorOutput",
    "BudgetEvaluation",
    "DecisionCoprocessor",
    "evaluate_refiner_budgets",
]


class AttentionBlock(nn.Module):
    """Multi-head attention SDPA, masque additif sur les clés invalides."""

    def __init__(self, width: int, heads: int, dropout: float = 0.0) -> None:
        super().__init__()
        if width % heads != 0:
            raise ValueError(f"width={width} non divisible par heads={heads}")
        self.width = int(width)
        self.heads = int(heads)
        self.head_dim = self.width // self.heads
        self.dropout = float(dropout)
        self.q_proj = nn.Linear(self.width, self.width)
        self.k_proj = nn.Linear(self.width, self.width)
        self.v_proj = nn.Linear(self.width, self.width)
        self.out_proj = nn.Linear(self.width, self.width)

    def _split(self, x: torch.Tensor) -> torch.Tensor:
        batch, length, _ = x.shape
        return x.view(batch, length, self.heads, self.head_dim).transpose(1, 2)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        batch, query_len, _ = query.shape
        key_len = key.shape[1]
        q = self._split(self.q_proj(query))
        k = self._split(self.k_proj(key))
        v = self._split(self.v_proj(value))

        attn_bias: torch.Tensor | None = None
        if key_padding_mask is not None:
            mask = key_padding_mask.to(device=query.device, dtype=torch.bool)
            if mask.shape != (batch, key_len):
                raise ValueError(
                    f"key_padding_mask {tuple(mask.shape)} != {(batch, key_len)}"
                )
            if mask.all(dim=1).any():
                raise ValueError(
                    "attention entièrement masquée : au moins un token valide est requis"
                )
            attn_bias = torch.zeros(
                (batch, 1, 1, key_len), dtype=q.dtype, device=query.device
            ).masked_fill(mask[:, None, None, :], float("-inf"))

        context = F.scaled_dot_product_attention(
            q, k, v, attn_mask=attn_bias, dropout_p=self.dropout, is_causal=False
        )
        context = context.transpose(1, 2).reshape(batch, query_len, self.width)
        return self.out_proj(context)


class RecurrentBlock(nn.Module):
    """Bloc récurrent PARTAGÉ (SPEC §5.5) — un seul exemplaire, réutilisé.

    ``Z = Z + a·CrossAttn(LN(Z), keys, values, mask)``
    ``Z = Z + a·SelfAttn(LN(Z))``
    ``Z = Z + a·FFN(LN(Z))``
    """

    def __init__(
        self,
        width: int,
        heads: int,
        ffn_width: int,
        residual_scale: float = 0.1,
    ) -> None:
        super().__init__()
        self.residual_scale = float(residual_scale)
        self.ln_cross = nn.LayerNorm(width)
        self.cross_attn = AttentionBlock(width, heads)
        self.ln_self = nn.LayerNorm(width)
        self.self_attn = AttentionBlock(width, heads)
        self.ln_ffn = nn.LayerNorm(width)
        self.ffn = nn.Sequential(
            nn.Linear(width, ffn_width), nn.GELU(), nn.Linear(ffn_width, width)
        )

    def forward(
        self,
        z: torch.Tensor,
        keys: torch.Tensor,
        values: torch.Tensor,
        key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        a = self.residual_scale
        z = z + a * self.cross_attn(
            self.ln_cross(z), keys, values, key_padding_mask=key_padding_mask
        )
        z_norm = self.ln_self(z)
        z = z + a * self.self_attn(z_norm, z_norm, z_norm)
        z = z + a * self.ffn(self.ln_ffn(z))
        return z


class MemoryCorrectionBase(nn.Module):
    """Mémoire H projetée + correction résiduelle — socle commun B3/B4/R.

    Les noms d'attributs sont stables : ils font partie des clés de
    ``state_dict`` déjà utilisées par ``training.py``/``checkpointing.py``.
    ``H`` (bf16 possible) est converti explicitement au dtype des modules
    entraînables (FP32) — aucun autocast externe requis (SPEC §10.4).
    """

    def __init__(
        self,
        hidden_size: int,
        width: int,
        heads: int,
        correction_hidden: int | None = None,
        correction_init_std: float = 0.01,
    ) -> None:
        super().__init__()
        self.hidden_size = int(hidden_size)
        self.width = int(width)
        self.heads = int(heads)

        # Mémoire de tokens : projections calculées UNE fois par forward.
        self.ln_memory_keys = nn.LayerNorm(self.hidden_size)
        self.ln_memory_values = nn.LayerNorm(self.hidden_size)
        self.proj_keys = nn.Linear(self.hidden_size, self.width)
        self.proj_values = nn.Linear(self.hidden_size, self.width)

        # Correction résiduelle.
        self.candidate_attn = AttentionBlock(self.width, self.heads)
        correction_hidden = int(correction_hidden) if correction_hidden else self.width
        self.correction = nn.Sequential(
            nn.Linear(3 * self.width, correction_hidden),
            nn.GELU(),
            nn.Linear(correction_hidden, 1),
        )
        nn.init.normal_(self.correction[-1].weight, std=correction_init_std)
        nn.init.zeros_(self.correction[-1].bias)

        # Diagnostics de coût (SPEC §11.3), pas des tenseurs de graphe.
        self.step_calls = 0
        self.forward_calls = 0

    # ---- mémoire --------------------------------------------------------
    def project_memory(
        self,
        hidden: torch.Tensor,
        *,
        mode: str = "normal",
        permutation: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """``memory_keys = Wk(LN(H))``, ``memory_values = Wv(LN(H))`` — une fois.

        ``mode`` est un mode **diagnostic** (SPEC §13.1), jamais un entraînement :
        ``normal`` · ``masked`` (clés/valeurs nulles) · ``mixed`` (mémoire d'un
        autre exemple du lot via ``permutation [B]``).
        """
        # H (bf16) → dtype des projections entraînables (FP32) : SPEC §10.4.
        hidden = hidden.to(dtype=self.proj_keys.weight.dtype)
        keys = self.proj_keys(self.ln_memory_keys(hidden))
        values = self.proj_values(self.ln_memory_values(hidden))
        if mode == "normal":
            return keys, values
        if mode == "masked":
            return torch.zeros_like(keys), torch.zeros_like(values)
        if mode == "mixed":
            if permutation is None:
                raise ValueError("memory mode 'mixed' exige une permutation [B]")
            index = permutation.to(device=keys.device, dtype=torch.long)
            if index.shape != (keys.shape[0],):
                raise ValueError(
                    f"permutation {tuple(index.shape)} != batch {(keys.shape[0],)}"
                )
            return keys[index], values[index]
        raise ValueError(f"memory mode inconnu: {mode!r} (normal | masked | mixed)")

    # ---- correction -----------------------------------------------------
    def correct(
        self,
        query: torch.Tensor,
        candidates: torch.Tensor,
        z: torch.Tensor,
        candidate_mask: torch.Tensor,
    ) -> torch.Tensor:
        """``delta_i = CorrectionHead(concat(q, c_i, r_i))`` → [B, K]."""
        dtype = self.correction[0].weight.dtype
        query = query.to(dtype=dtype)
        candidates = candidates.to(dtype=dtype)
        z = z.to(dtype=dtype)
        r = self.candidate_attn(candidates, z, z)  # query = c_i, keys/valeurs = Z_t
        query_expanded = query.unsqueeze(1).expand_as(candidates)
        features = torch.cat([query_expanded, candidates, r], dim=-1)
        delta = self.correction(features).squeeze(-1)
        return delta.masked_fill(~candidate_mask.to(device=delta.device, dtype=torch.bool), 0.0)

    # ---- interface commune ----------------------------------------------
    def effective_steps(self, budget: int | None = None) -> int:
        """Nombre d'applications effectives du raffineur pour un budget donné."""
        raise NotImplementedError

    # ---- coût -----------------------------------------------------------
    def parameter_breakdown(self, depth: int = 1) -> OrderedDict[str, int]:
        """Décompte par module (profondeur ``depth`` pour les groupes)."""
        counts: OrderedDict[str, int] = OrderedDict()

        def count(module: nn.Module) -> int:
            return sum(p.numel() for p in module.parameters())

        for name, module in self.named_children():
            children = list(module.named_children())
            if children and depth > 0:
                own = sum(p.numel() for p in module.parameters(recurse=False))
                if own:
                    counts[name] = own
                for child_name, child in children:
                    counts[f"{name}.{child_name}"] = count(child)
            else:
                counts[name] = count(module)
        # Paramètres portés directement par le module (ex. learned_slots).
        direct = list(self.named_parameters(recurse=False))
        if direct:
            direct_name = (
                direct[0][0] if len(direct) == 1 else "direct:" + "+".join(n for n, _ in direct)
            )
            counts[direct_name] = sum(p.numel() for _, p in direct)
        counts["TOTAL"] = sum(v for k, v in counts.items() if k != "TOTAL")
        counts["TOTAL_TRAINABLE"] = sum(
            p.numel() for p in self.parameters() if p.requires_grad
        )
        return counts

    def parameter_count(self) -> tuple[int, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return total, trainable

    def assert_within_parameter_budget(self, limit: int | None = None) -> int:
        limit = (
            int(getattr(self, "max_trainable_parameters", 15_000_000))
            if limit is None
            else int(limit)
        )
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        if trainable > limit:
            breakdown = self.parameter_breakdown()
            detail = ", ".join(f"{k}={v}" for k, v in breakdown.items())
            raise ValueError(
                f"{type(self).__name__}: {trainable} paramètres entraînables > "
                f"plafond {limit} (SPEC §14.3) — décompte: {detail}"
            )
        return trainable


class LatentSidecar(MemoryCorrectionBase):
    """Coprocesseur latent récurrent (SPEC §5.5-5.6).

    Configuration initiale : d=256, 8 slots, 4 têtes, FFN 1024, a=0.1,
    aucun embedding d'étape, aucun dropout.
    """

    kind = "recurrent"

    def __init__(
        self,
        hidden_size: int,
        width: int = 256,
        slots: int = 8,
        heads: int = 4,
        ffn_width: int = 1024,
        residual_scale: float = 0.1,
        correction_hidden: int | None = None,
        correction_init_std: float = 0.01,
        max_trainable_parameters: int = 15_000_000,
    ) -> None:
        super().__init__(
            hidden_size,
            width,
            heads,
            correction_hidden=correction_hidden,
            correction_init_std=correction_init_std,
        )
        self.slots = int(slots)
        self.ffn_width = int(ffn_width)
        self.residual_scale = float(residual_scale)
        self.max_trainable_parameters = int(max_trainable_parameters)

        # Z0 = learned_slots + broadcast(Winit(q))
        self.learned_slots = nn.Parameter(torch.empty(self.slots, self.width))
        nn.init.normal_(self.learned_slots, std=0.02)
        self.proj_init = nn.Linear(self.width, self.width)

        # Bloc récurrent partagé (un seul).
        self.block = RecurrentBlock(self.width, self.heads, self.ffn_width, self.residual_scale)

        self.assert_within_parameter_budget()

    def initialize(self, query: torch.Tensor) -> torch.Tensor:
        """``Z0 = learned_slots + broadcast(Winit(q))`` → [B, M, d]."""
        query = query.to(dtype=self.proj_init.weight.dtype)
        batch = query.shape[0]
        slots = self.learned_slots.unsqueeze(0).expand(batch, -1, -1)
        return slots + self.proj_init(query).unsqueeze(1)

    def step(
        self,
        z: torch.Tensor,
        keys: torch.Tensor,
        values: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Une application du bloc partagé (pas d'embedding d'étape)."""
        self.step_calls += 1
        z = z.to(dtype=keys.dtype)
        key_padding_mask = ~attention_mask.to(device=z.device, dtype=torch.bool)
        return self.block(z, keys, values, key_padding_mask=key_padding_mask)

    def effective_steps(self, budget: int | None = None) -> int:
        count = 0 if budget is None else int(budget)
        if count < 0:
            raise ValueError(f"budget négatif: {count}")
        return count

    def forward(
        self,
        base_logits: torch.Tensor,
        query: torch.Tensor,
        candidates: torch.Tensor,
        hidden: torch.Tensor,
        attention_mask: torch.Tensor,
        candidate_mask: torch.Tensor,
        budget: int = 0,
        *,
        memory_mode: str = "normal",
        memory_permutation: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if budget < 0:
            raise ValueError(f"budget négatif: {budget}")
        self.forward_calls += 1
        if budget == 0:
            # Aucune projection, aucun déroulé : les logits directs passent tels quels.
            return base_logits

        keys, values = self.project_memory(
            hidden, mode=memory_mode, permutation=memory_permutation
        )
        z = self.initialize(query)
        for _ in range(int(budget)):
            z = self.step(z, keys, values, attention_mask)
        delta = self.correct(query, candidates, z, candidate_mask)
        return base_logits + delta

    @torch.no_grad()
    def latent_states(
        self,
        hidden: torch.Tensor,
        query: torch.Tensor,
        attention_mask: torch.Tensor,
        budget: int,
        *,
        memory_mode: str = "normal",
        memory_permutation: torch.Tensor | None = None,
        collect_steps: bool = False,
    ) -> torch.Tensor | list[torch.Tensor]:
        """Slots Z_t après ``budget`` étapes — diagnostic/probes (SPEC §13.3)."""
        keys, values = self.project_memory(
            hidden, mode=memory_mode, permutation=memory_permutation
        )
        z = self.initialize(query)
        states: list[torch.Tensor] = []
        for _ in range(int(budget)):
            z = self.step(z, keys, values, attention_mask)
            if collect_steps:
                states.append(z)
        return states if collect_steps else z


@dataclass
class BudgetEvaluation:
    """Résultat d'évaluation multi-budgets SANS réentraînement (SPEC §8.2)."""

    budget: int
    logits: list[torch.Tensor]
    probabilities: list[torch.Tensor]
    predictions: list[torch.Tensor]
    losses: list[torch.Tensor] | None = None
    mean_loss: float | None = None
    accuracy: float | None = None
    stats: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CoprocessorOutput:
    """Sortie complète : logits du budget demandé + logits directs + coût."""

    logits: torch.Tensor               # [B, K] logits finaux
    probabilities: torch.Tensor        # [B, K] FP32
    base_logits: torch.Tensor          # [B, K] chemin direct (toujours conservés)
    query: torch.Tensor                # [B, d]
    candidates: torch.Tensor           # [B, K, d]
    hidden: torch.Tensor               # [B, L, D]
    loss: torch.Tensor | None
    stats: dict[str, Any]


class DecisionCoprocessor(nn.Module):
    """Assemblage backbone gelé + tête directe + raffineur (SPEC §5.8).

    Le raffineur (``sidecar``) peut être ``LatentSidecar`` (R), ou un contrôle
    B3/B4 de :mod:`decision_coprocessor.controls` — sélectionnable via
    ``kind`` dans ``from_kind``. Le backbone n'est pas un sous-module
    ``nn.Module`` (paramètres gelés hors de ``.parameters()``) ; il est appelé
    une seule fois par forward, quel que soit le budget.
    """

    def __init__(
        self,
        backbone: Any,
        head: DecisionHead,
        sidecar: MemoryCorrectionBase,
        *,
        freeze_fast_head: bool = True,
    ) -> None:
        super().__init__()
        self.backbone = backbone
        self.head = head
        self.sidecar = sidecar
        self.refiner_kind = getattr(sidecar, "kind", type(sidecar).__name__)
        self.freeze_fast_head = bool(freeze_fast_head)
        if self.freeze_fast_head:
            for p in self.head.parameters():
                p.requires_grad_(False)

    @classmethod
    def from_kind(
        cls,
        backbone: Any,
        head: DecisionHead,
        kind: str,
        *,
        freeze_fast_head: bool = True,
        **refiner_kwargs: Any,
    ) -> "DecisionCoprocessor":
        """Assemble un coprocesseur dont le raffineur est choisi par ``kind``.

        ``kind`` ∈ ``recurrent`` | ``non_recurrent_memory`` (B3) |
        ``unshared_stack`` (B4). Voir ``controls.build_refiner``.
        """
        from .controls import build_refiner  # import paresseux (évite le cycle)

        refiner = build_refiner(kind, backbone.hidden_size, **refiner_kwargs)
        return cls(backbone, head, refiner, freeze_fast_head=freeze_fast_head)

    def freeze_fast_head_(self) -> None:
        self.freeze_fast_head = True
        for p in self.head.parameters():
            p.requires_grad_(False)

    def unfreeze_fast_head_(self) -> None:
        self.freeze_fast_head = False
        for p in self.head.parameters():
            p.requires_grad_(True)

    def forward(
        self,
        batch: BatchEncoded,
        budget: int = 0,
        labels: torch.Tensor | None = None,
        *,
        memory_mode: str = "normal",
        memory_permutation: torch.Tensor | None = None,
    ) -> CoprocessorOutput:
        if budget < 0:
            raise ValueError(f"budget négatif: {budget}")

        # 1) UN seul encodage backbone par exemple et par forward.
        hidden = self.backbone.encode(batch.input_ids, batch.attention_mask)

        # Frontière de précision (SPEC §10.4) : H peut être en bf16 (backbone),
        # les modules entraînables sont FP32. Un seul cast explicite alimente la
        # tête et le sidecar ⇒ fonctionne SANS autocast externe (correctif @ag-5).
        module_dtype = self.head.proj_query.weight.dtype
        hidden_modules = hidden.to(dtype=module_dtype)

        # 2) Tête directe : opérations différentiables hors no_grad.
        head_out = self.head(
            hidden_modules,
            candidate_starts=batch.candidate_starts,
            candidate_lens=batch.candidate_lens,
            candidate_mask=batch.candidate_mask,
            attention_mask=batch.attention_mask,
        )
        base_logits = head_out.base_logits
        query = head_out.query
        candidates = head_out.candidates
        if self.freeze_fast_head:
            # Détachables sans mettre la suite en no_grad : le sidecar garde ses grads.
            base_logits = base_logits.detach()
            query = query.detach()
            candidates = candidates.detach()

        # 3) budget 0 : retour exact du chemin direct (même tenseur).
        if budget == 0:
            logits = base_logits
        else:
            logits = self.sidecar(
                base_logits,
                query,
                candidates,
                hidden_modules,
                batch.attention_mask,
                batch.candidate_mask,
                budget,
                memory_mode=memory_mode,
                memory_permutation=memory_permutation,
            )
        latent_steps = self.sidecar.effective_steps(budget)

        probabilities = masked_softmax(logits, batch.candidate_mask)
        loss = None
        if labels is not None:
            loss = decision_cross_entropy(logits, batch.candidate_mask, labels)

        stats: dict[str, Any] = {
            "backbone_passes": 1,
            "latent_steps": latent_steps,
            "generated_tokens": 0,
            "budget": int(budget),
            "refiner_kind": self.refiner_kind,
        }
        return CoprocessorOutput(
            logits=logits,
            probabilities=probabilities,
            base_logits=base_logits,
            query=query,
            candidates=candidates,
            hidden=hidden,
            loss=loss,
            stats=stats,
        )

    # ---- évaluation multi-budgets SANS réentraînement -------------------
    @torch.no_grad()
    def evaluate_budgets(
        self,
        batches: list[BatchEncoded],
        labels: list[torch.Tensor] | None = None,
        budgets: tuple[int, ...] = (0, 1, 2, 4),
    ) -> dict[int, BudgetEvaluation]:
        """Évalue R1/R2/R4 (mêmes poids, budgets 1/2/4) sans réentraîner.

        Aucun gradient n'est calculé (``torch.no_grad``), aucun paramètre n'est
        modifié ; l'état ``train/eval`` du module est restauré. ``labels`` est
        une liste alignée sur ``batches`` (optionnelle). Pour chaque budget,
        les logits/probabilités bruts sont conservés (diagnostic §14.5) et la
        loss moyenne (CE masquée FP32) est calculée si les labels sont fournis.
        """
        batches = list(batches)
        if labels is not None and len(labels) != len(batches):
            raise ValueError("labels et batches n'ont pas la même longueur")

        was_training = self.training
        self.eval()
        results: dict[int, BudgetEvaluation] = {}
        try:
            for budget in budgets:
                record = BudgetEvaluation(
                    budget=int(budget),
                    logits=[],
                    probabilities=[],
                    predictions=[],
                    losses=[] if labels is not None else None,
                )
                total_loss, total_examples, total_correct = 0.0, 0, 0
                for index, batch in enumerate(batches):
                    batch_labels = None if labels is None else labels[index]
                    out = self.forward(batch, budget=budget, labels=batch_labels)
                    record.logits.append(out.logits.detach().cpu())
                    record.probabilities.append(out.probabilities.detach().cpu())
                    record.predictions.append(
                        out.probabilities.argmax(dim=-1).detach().cpu()
                    )
                    record.stats.append(dict(out.stats))
                    if batch_labels is not None:
                        loss_value = float(out.loss.detach())
                        size = int(batch_labels.shape[0])
                        record.losses.append(out.loss.detach().cpu())
                        total_loss += loss_value * size
                        total_correct += int(
                            (record.predictions[-1] == batch_labels.detach().cpu()).sum()
                        )
                        total_examples += size
                if labels is not None and total_examples:
                    record.mean_loss = total_loss / total_examples
                    record.accuracy = total_correct / total_examples
                results[int(budget)] = record
        finally:
            self.train(was_training)
        return results


# Alias de typage documentaire.
MemoryRefiner = MemoryCorrectionBase


def evaluate_refiner_budgets(
    backbone: Any,
    head: DecisionHead,
    refiner: MemoryCorrectionBase,
    batches: list[BatchEncoded],
    labels: list[torch.Tensor] | None = None,
    budgets: tuple[int, ...] = (1, 2, 4),
) -> dict[int, BudgetEvaluation]:
    """Évalue un raffineur déjà entraîné à plusieurs budgets, SANS réentraîner.

    Enveloppe ``DecisionCoprocessor`` + ``evaluate_budgets`` : pratique depuis
    ``training.py`` (Phase B/C) qui détient déjà le backbone gelé, la tête et le
    module entraîné. Aucun gradient, aucun pas d'optimiseur : les mêmes poids
    servent à tous les budgets (règle préenregistrée SPEC §8.2).
    """
    coprocessor = DecisionCoprocessor(backbone, head, refiner, freeze_fast_head=True)
    return coprocessor.evaluate_budgets(batches, labels=labels, budgets=budgets)
