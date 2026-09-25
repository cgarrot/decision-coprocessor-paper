"""Contrôles non récurrents B3/B4 — SPEC §6.1, §8.3, ``configs/controls.yaml``.

Deux témoins face au sidecar récurrent (R), mêmes données / même tête / même
backbone gelé :

- **B3 ``NonRecurrentMemory``** : lit la **même mémoire H** (mêmes
  ``memory_keys``/``memory_values``) mais en **une seule passe** (aucune boucle
  temporelle). Pour un budget de paramètres comparable au sidecar, le bloc
  unique est élargi (slots 8→16, FFN 1024→1152, d=256 inchangé).
- **B4 ``UnsharedStack``** : ``blocks`` blocs **non partagés** appliqués
  séquentiellement (``blocks=4`` ≈ profondeur de R4), d=256 identique. Le
  surcoût de paramètres est assumé et documenté (SPEC §6.1 : « l'indiquer
  plutôt que dissimuler »).

Les deux respectent les invariants du sidecar : budget 0 = tête directe
exacte, un seul encodage backbone par forward, correction résiduelle
identique, mémoire jamais mélangée entre exemples.

Compatibilité ``training.py::run_phase_c`` : ``forward(base, q, c, hidden,
attention_mask, candidate_mask)`` est appelable **sans budget** (B3 = 1 passe,
B4 = tous ses blocs). Le budget reste accepté pour l'évaluation contrôlée.
"""
from __future__ import annotations

from typing import Any, Mapping

import torch
import torch.nn as nn

from .sidecar import LatentSidecar, MemoryCorrectionBase, RecurrentBlock

__all__ = [
    "NonRecurrentMemory",
    "UnsharedStack",
    "REFINER_KINDS",
    "B3_DEFAULTS",
    "B4_DEFAULTS",
    "build_refiner",
    "refiner_dims_from_config",
    "control_module_factory",
]

# Dimensions par défaut calibrées sur le budget du sidecar (2 110 465).
B3_DEFAULTS: dict[str, Any] = {
    "width": 256,        # d identique au sidecar
    "slots": 16,         # élargi (sidecar : 8)
    "heads": 4,
    "ffn_width": 1152,   # élargi (sidecar : 1024)
    "residual_scale": 0.1,
}
B4_DEFAULTS: dict[str, Any] = {
    "width": 256,        # d identique au sidecar
    "slots": 8,
    "heads": 4,
    "ffn_width": 1024,
    "blocks": 4,         # 4 blocs NON partagés
    "residual_scale": 0.1,
}

REFINER_KINDS: tuple[str, ...] = (
    "recurrent",
    "non_recurrent_memory",
    "unshared_stack",
)

_KIND_ALIASES = {
    "r": "recurrent",
    "sidecar": "recurrent",
    "b3": "non_recurrent_memory",
    "b-3": "non_recurrent_memory",
    "b4": "unshared_stack",
    "b-4": "unshared_stack",
}

_CONSTRUCTOR_KEYS = (
    "width",
    "slots",
    "heads",
    "ffn_width",
    "blocks",
    "residual_scale",
    "correction_hidden",
    "correction_init_std",
    "max_trainable_parameters",
)


def _canonical_kind(kind: str) -> str:
    key = str(kind).strip().lower()
    key = _KIND_ALIASES.get(key, key)
    if key not in REFINER_KINDS:
        raise ValueError(
            f"kind de raffineur inconnu: {kind!r} (attendu: {', '.join(REFINER_KINDS)})"
        )
    return key


class NonRecurrentMemory(MemoryCorrectionBase):
    """B3 — cross-attention unique sur H, aucune boucle temporelle (§6.1)."""

    kind = "non_recurrent_memory"

    def __init__(
        self,
        hidden_size: int,
        width: int = 256,
        slots: int = 16,
        heads: int = 4,
        ffn_width: int = 1152,
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

        self.learned_slots = nn.Parameter(torch.empty(self.slots, self.width))
        nn.init.normal_(self.learned_slots, std=0.02)
        self.proj_init = nn.Linear(self.width, self.width)

        # UN bloc élargi, appliqué une seule fois (pas de ModuleList, pas de boucle).
        self.block = RecurrentBlock(
            self.width, self.heads, self.ffn_width, self.residual_scale
        )

        self.assert_within_parameter_budget()

    def initialize(self, query: torch.Tensor) -> torch.Tensor:
        query = query.to(dtype=self.proj_init.weight.dtype)
        batch = query.shape[0]
        slots = self.learned_slots.unsqueeze(0).expand(batch, -1, -1)
        return slots + self.proj_init(query).unsqueeze(1)

    def effective_steps(self, budget: int | None = None) -> int:
        """0 si budget explicite 0, sinon exactement 1 (jamais plus)."""
        if budget is None:
            return 1
        count = int(budget)
        if count < 0:
            raise ValueError(f"budget négatif: {count}")
        return 0 if count == 0 else 1

    def forward(
        self,
        base_logits: torch.Tensor,
        query: torch.Tensor,
        candidates: torch.Tensor,
        hidden: torch.Tensor,
        attention_mask: torch.Tensor,
        candidate_mask: torch.Tensor,
        budget: int | None = None,
        *,
        memory_mode: str = "normal",
        memory_permutation: torch.Tensor | None = None,
    ) -> torch.Tensor:
        self.forward_calls += 1
        if self.effective_steps(budget) == 0:
            return base_logits  # budget 0 = tête directe exacte

        keys, values = self.project_memory(
            hidden, mode=memory_mode, permutation=memory_permutation
        )
        z = self.initialize(query)
        self.step_calls += 1
        key_padding_mask = ~attention_mask.to(device=z.device, dtype=torch.bool)
        z = self.block(z, keys, values, key_padding_mask=key_padding_mask)
        delta = self.correct(query, candidates, z, candidate_mask)
        return base_logits + delta

    @torch.no_grad()
    def latent_states(
        self,
        hidden: torch.Tensor,
        query: torch.Tensor,
        attention_mask: torch.Tensor,
        budget: int | None = None,
        *,
        memory_mode: str = "normal",
        memory_permutation: torch.Tensor | None = None,
        collect_steps: bool = False,
    ) -> torch.Tensor | list[torch.Tensor]:
        """Z après la passe unique (ou liste d'un état) — diagnostic §13.3."""
        if self.effective_steps(budget) == 0:
            raise ValueError("latent_states: budget 0 ne produit aucun état")
        keys, values = self.project_memory(
            hidden, mode=memory_mode, permutation=memory_permutation
        )
        z = self.initialize(query)
        key_padding_mask = ~attention_mask.to(device=z.device, dtype=torch.bool)
        z = self.block(z, keys, values, key_padding_mask=key_padding_mask)
        return [z] if collect_steps else z


class UnsharedStack(MemoryCorrectionBase):
    """B4 — ``blocks`` blocs non partagés appliqués séquentiellement (§6.1)."""

    kind = "unshared_stack"

    def __init__(
        self,
        hidden_size: int,
        width: int = 256,
        slots: int = 8,
        heads: int = 4,
        ffn_width: int = 1024,
        blocks: int = 4,
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
        self.blocks_count = int(blocks)
        if self.blocks_count < 1:
            raise ValueError("unshared_stack: au moins 1 bloc requis")
        self.residual_scale = float(residual_scale)
        self.max_trainable_parameters = int(max_trainable_parameters)

        self.learned_slots = nn.Parameter(torch.empty(self.slots, self.width))
        nn.init.normal_(self.learned_slots, std=0.02)
        self.proj_init = nn.Linear(self.width, self.width)

        # Blocs NON partagés : un module distinct par profondeur.
        self.blocks = nn.ModuleList(
            [
                RecurrentBlock(self.width, self.heads, self.ffn_width, self.residual_scale)
                for _ in range(self.blocks_count)
            ]
        )

        self.assert_within_parameter_budget()

    def initialize(self, query: torch.Tensor) -> torch.Tensor:
        query = query.to(dtype=self.proj_init.weight.dtype)
        batch = query.shape[0]
        slots = self.learned_slots.unsqueeze(0).expand(batch, -1, -1)
        return slots + self.proj_init(query).unsqueeze(1)

    def effective_steps(self, budget: int | None = None) -> int:
        """``budget=None`` → tous les blocs ; sinon 0..blocks (erreur au-delà)."""
        total = len(self.blocks)
        if budget is None:
            return total
        count = int(budget)
        if count < 0:
            raise ValueError(f"budget négatif: {count}")
        if count > total:
            raise ValueError(
                f"unshared_stack: budget {count} > {total} blocs non partagés "
                "(pas d'extrapolation possible sans partage)"
            )
        return count

    def forward(
        self,
        base_logits: torch.Tensor,
        query: torch.Tensor,
        candidates: torch.Tensor,
        hidden: torch.Tensor,
        attention_mask: torch.Tensor,
        candidate_mask: torch.Tensor,
        budget: int | None = None,
        *,
        memory_mode: str = "normal",
        memory_permutation: torch.Tensor | None = None,
    ) -> torch.Tensor:
        self.forward_calls += 1
        steps = self.effective_steps(budget)
        if steps == 0:
            return base_logits  # budget 0 = tête directe exacte

        keys, values = self.project_memory(
            hidden, mode=memory_mode, permutation=memory_permutation
        )
        z = self.initialize(query)
        key_padding_mask = ~attention_mask.to(device=z.device, dtype=torch.bool)
        for index in range(steps):
            self.step_calls += 1
            z = self.blocks[index](z, keys, values, key_padding_mask=key_padding_mask)
        delta = self.correct(query, candidates, z, candidate_mask)
        return base_logits + delta

    @torch.no_grad()
    def latent_states(
        self,
        hidden: torch.Tensor,
        query: torch.Tensor,
        attention_mask: torch.Tensor,
        budget: int | None = None,
        *,
        memory_mode: str = "normal",
        memory_permutation: torch.Tensor | None = None,
        collect_steps: bool = False,
    ) -> torch.Tensor | list[torch.Tensor]:
        """Z après ``effective_steps(budget)`` blocs — diagnostic §13.3."""
        steps = self.effective_steps(budget)
        if steps == 0:
            raise ValueError("latent_states: budget 0 ne produit aucun état")
        keys, values = self.project_memory(
            hidden, mode=memory_mode, permutation=memory_permutation
        )
        z = self.initialize(query)
        key_padding_mask = ~attention_mask.to(device=z.device, dtype=torch.bool)
        states: list[torch.Tensor] = []
        for index in range(steps):
            z = self.blocks[index](z, keys, values, key_padding_mask=key_padding_mask)
            if collect_steps:
                states.append(z)
        return states if collect_steps else z


def build_refiner(kind: str, hidden_size: int, **kwargs: Any) -> MemoryCorrectionBase:
    """Fabrique de raffineur par ``kind`` (SPEC §6.1).

    ``kind`` : ``recurrent`` (R1/R2/R4, d=256) · ``non_recurrent_memory`` (B3)
    · ``unshared_stack`` (B4). Les alias ``R``/``B3``/``B4`` sont acceptés.
    """
    resolved_kind = _canonical_kind(kind)
    if resolved_kind == "recurrent":
        return LatentSidecar(hidden_size, **kwargs)
    if resolved_kind == "non_recurrent_memory":
        dims = dict(B3_DEFAULTS)
        dims.update(kwargs)
        return NonRecurrentMemory(hidden_size, **dims)
    dims = dict(B4_DEFAULTS)
    dims.update(kwargs)
    return UnsharedStack(hidden_size, **dims)


def refiner_dims_from_config(kind: str, resolved: Mapping[str, Any] | None) -> dict[str, Any]:
    """Dimensions d'un contrôle depuis une config résolue (``controls:`` du YAML).

    Section attendue (optionnelle) ::

        controls:
          non_recurrent_memory: {slots: 16, ffn_width: 1152}
          unshared_stack: {blocks: 4}

    À défaut, les défauts calibrés de ce module s'appliquent.
    """
    resolved_kind = _canonical_kind(kind)
    defaults: dict[str, Any] = {}
    if resolved_kind == "non_recurrent_memory":
        defaults = dict(B3_DEFAULTS)
    elif resolved_kind == "unshared_stack":
        defaults = dict(B4_DEFAULTS)
    if not resolved:
        return defaults
    section = resolved.get("controls", {}) if isinstance(resolved, Mapping) else {}
    raw = section.get(resolved_kind, {}) if isinstance(section, Mapping) else {}
    if not isinstance(raw, Mapping):
        return defaults
    for key in _CONSTRUCTOR_KEYS:
        if key in raw:
            defaults[key] = raw[key]
    return defaults


def control_module_factory(
    kind: str, resolved: Mapping[str, Any] | None = None
):
    """Fabrique compatible ``training.py::run_phase_c(module_factory=...)``.

    ``module_factory(context)`` reçoit ``{"hidden_size", "device", "resolved"}``
    et renvoie le module de contrôle prêt à ``.to(device)``.
    """
    resolved_kind = _canonical_kind(kind)

    def factory(context: Mapping[str, Any]) -> MemoryCorrectionBase:
        config = resolved if resolved is not None else context.get("resolved", {})
        dims = refiner_dims_from_config(resolved_kind, config)
        return build_refiner(resolved_kind, int(context["hidden_size"]), **dims)

    return factory
