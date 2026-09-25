"""Encodage partagé gelé — SPEC §5.3.

Contrat :

- chargement d'une révision **épinglée** (``RESOLVE_AND_PIN_BEFORE_RUNNING``
  est rejeté, cf. §14.3) ;
- backbone en ``eval()``, paramètres gelés, ``use_cache=False`` ;
- ``H = Backbone(tokens, attention_mask).last_hidden_state`` calculé sous
  ``torch.no_grad()`` — **pas** ``inference_mode()`` (SPEC §5.3 / [S18]) ;
- jamais de matérialisation des logits vocabulaire complets pour les chemins à
  tête de décision (on charge ``AutoModel``, pas la tête LM) ;
- dtype paramétrable (bf16 par défaut), attention SDPA ;
- « dernier vecteur de requête » = dernier token **valide** (padding à droite).
"""
from __future__ import annotations

from typing import Any, Mapping

import torch
import torch.nn as nn

__all__ = [
    "REVISION_SENTINEL",
    "ContextLengthError",
    "RevisionNotPinned",
    "resolve_dtype",
    "default_device",
    "validate_revision",
    "last_valid_index",
    "FrozenBackbone",
    "code_token_logits",
    "load_tokenizer",
    "load_backbone",
]

REVISION_SENTINEL = "RESOLVE_AND_PIN_BEFORE_RUNNING"

_DTYPE_ALIASES = {
    "bf16": torch.bfloat16,
    "bfloat16": torch.bfloat16,
    "fp16": torch.float16,
    "float16": torch.float16,
    "half": torch.float16,
    "fp32": torch.float32,
    "float32": torch.float32,
    "float": torch.float32,
}


class RevisionNotPinned(ValueError):
    """La révision du backbone doit être immuable (hash de commit)."""


class ContextLengthError(ValueError):
    """Entrée au-delà de la longueur maximale admise (SPEC §10.6)."""


class FastTokenizerRequired(ValueError):
    """Les spans exigent un tokenizer rapide avec offset_mapping (SPEC §5.2)."""


def validate_revision(revision: str | None) -> str:
    if revision is None:
        raise RevisionNotPinned("révision absente : épingler un commit avant tout run")
    revision = revision.strip()
    if not revision or revision == REVISION_SENTINEL:
        raise RevisionNotPinned(
            f"révision non épinglée ({revision!r}) : remplacer {REVISION_SENTINEL} "
            "par un hash de commit immuable (SPEC §14.3)"
        )
    return revision


def resolve_dtype(dtype: Any) -> torch.dtype:
    if isinstance(dtype, torch.dtype):
        return dtype
    if isinstance(dtype, str):
        key = dtype.lower()
        if key in _DTYPE_ALIASES:
            return _DTYPE_ALIASES[key]
    raise ValueError(f"dtype non pris en charge: {dtype!r}")


def default_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def last_valid_index(attention_mask: torch.Tensor) -> torch.Tensor:
    """Index du dernier token valide par ligne (padding à droite, SPEC §5.3)."""
    if attention_mask.dim() != 2:
        raise ValueError(f"attention_mask doit être [B, L], reçu {tuple(attention_mask.shape)}")
    counts = attention_mask.sum(dim=1)
    if (counts <= 0).any():
        raise ValueError("ligne d'attention_mask sans aucun token valide")
    return counts.to(dtype=torch.long) - 1


def _extract_hidden(out: Any) -> torch.Tensor:
    if hasattr(out, "last_hidden_state"):
        return out.last_hidden_state
    if isinstance(out, Mapping) and "last_hidden_state" in out:
        return out["last_hidden_state"]
    if isinstance(out, (tuple, list)) and out:
        return out[0]
    raise TypeError(f"sortie backbone sans last_hidden_state: {type(out).__name__}")


class FrozenBackbone:
    """Enveloppe d'un backbone gelé : une seule méthode d'encodage, ``H`` brut.

    ``model`` peut être un modèle Hugging Face (``AutoModel``) ou tout module
    de même interface (utilisé par les tests CPU mini-backbone).
    """

    def __init__(
        self,
        model: nn.Module,
        tokenizer: Any | None = None,
        *,
        device: torch.device | str | None = None,
        dtype: Any | None = None,
        max_length: int | None = None,
        name: str = "backbone",
    ) -> None:
        if dtype is not None:
            model = model.to(dtype=resolve_dtype(dtype))
        if device is not None:
            model = model.to(device=device)
        model.eval()
        model.requires_grad_(False)

        self.model = model
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.name = name
        # Diagnostics de comptage (SPEC §5.7 / §11.3), pas des tenseurs de graphe.
        self.encode_calls = 0
        self.last_encode_kwargs: dict[str, Any] | None = None

    # ---- introspection --------------------------------------------------
    @property
    def hidden_size(self) -> int:
        config = getattr(self.model, "config", None)
        size = getattr(config, "hidden_size", None)
        if size is not None:
            return int(size)
        for module in self.model.modules():
            if isinstance(module, nn.Linear):
                return int(module.out_features)
        raise ValueError("hidden_size introuvable sur le backbone")

    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.model.parameters())

    # ---- encodage -------------------------------------------------------
    def encode(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        **kwargs: Any,
    ) -> torch.Tensor:
        """Retourne ``H`` : ``[B, L, D]``, calculé sous ``torch.no_grad()``."""
        if input_ids.dim() != 2:
            raise ValueError(f"input_ids doit être [B, L], reçu {tuple(input_ids.shape)}")
        if self.max_length is not None and input_ids.shape[1] > self.max_length:
            raise ContextLengthError(
                f"{self.name}: {input_ids.shape[1]} tokens > max_length={self.max_length} "
                "(rejeter ou régénérer l'entrée, ne pas tronquer silencieusement)"
            )
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)
        if attention_mask.shape != input_ids.shape:
            raise ValueError("attention_mask et input_ids de formes différentes")
        if (attention_mask.sum(dim=1) <= 0).any():
            raise ValueError("ligne sans aucun token valide (padding à droite requis)")

        call_kwargs: dict[str, Any] = {"use_cache": False, "return_dict": True}
        call_kwargs.update(kwargs)
        self.last_encode_kwargs = dict(call_kwargs)
        self.encode_calls += 1

        # no_grad volontairement, PAS inference_mode (SPEC §5.3 / [S18]).
        with torch.no_grad():
            out = self.model(
                input_ids=input_ids, attention_mask=attention_mask, **call_kwargs
            )
        hidden = _extract_hidden(out)
        if hidden.dim() != 3:
            raise ValueError(f"hidden state attendu [B, L, D], reçu {tuple(hidden.shape)}")
        return hidden


def code_token_logits(
    hidden: torch.Tensor,
    code_token_indices: torch.Tensor,
    code_token_ids: torch.Tensor,
    *,
    lm_head_weight: torch.Tensor,
    lm_head_bias: torch.Tensor | None = None,
) -> torch.Tensor:
    """Baseline B1 (SPEC §6.2) : logits des codes à leur position réelle.

    Pour chaque candidat i, le logit sélectionné est celui du token-code de la
    lettre à sa position ``p_i`` dans le prompt, conditionné par le préfixe
    ``[0, p_i)``. Ne matérialise pas les logits vocabulaire complets : seules
    les lignes du ``lm_head`` des codes autorisés sont utilisées.
    """
    if hidden.dim() != 3:
        raise ValueError("hidden doit être [B, L, D]")
    if (code_token_indices <= 0).any():
        raise ValueError("un code ne peut pas être en position 0 (préfixe vide)")
    batch, length, dim = hidden.shape
    if code_token_indices.shape != code_token_ids.shape:
        raise ValueError("code_token_indices et code_token_ids doivent avoir la même forme")

    positions = code_token_indices.to(hidden.device, dtype=torch.long) - 1
    if positions.max() >= length:
        raise ValueError("position de code au-delà des tokens fournis")
    rows = hidden.gather(1, positions.unsqueeze(-1).expand(-1, -1, dim))

    ids = code_token_ids.to(hidden.device, dtype=torch.long)
    weight = lm_head_weight.to(hidden.device)[ids]           # [B, K, D]
    logits = torch.einsum("bkd,bkd->bk", rows.to(weight.dtype), weight)
    if lm_head_bias is not None:
        logits = logits + lm_head_bias.to(hidden.device)[ids]
    return logits


def load_tokenizer(model_id: str, revision: str, **kwargs: Any):
    """Charge le tokenizer à la révision épinglée (tokenizer rapide requis)."""
    revision = validate_revision(revision)
    from transformers import AutoTokenizer  # import paresseux (tests CPU sans réseau)

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, **kwargs)
    if not getattr(tokenizer, "is_fast", False):
        raise FastTokenizerRequired(
            "tokenizer non rapide : les spans exigent offset_mapping (SPEC §5.2)"
        )
    return tokenizer


def load_backbone(
    model_id: str,
    revision: str,
    *,
    dtype: Any = "bf16",
    device: torch.device | str | None = None,
    tokenizer: Any | None = None,
    max_length: int | None = None,
    attn_implementation: str = "sdpa",
    local_files_only: bool = False,
    **kwargs: Any,
) -> FrozenBackbone:
    """Charge ``AutoModel`` (sans tête LM) à la révision épinglée."""
    revision = validate_revision(revision)
    from transformers import AutoModel  # import paresseux

    dt = resolve_dtype(dtype)
    common: dict[str, Any] = {
        "revision": revision,
        "attn_implementation": attn_implementation,
        "local_files_only": local_files_only,
        **kwargs,
    }
    try:
        model = AutoModel.from_pretrained(model_id, dtype=dt, **common)
    except TypeError:
        # Compatibilité transformers < 4.56 (ancien nom torch_dtype).
        model = AutoModel.from_pretrained(model_id, torch_dtype=dt, **common)
    if hasattr(model, "config"):
        model.config.use_cache = False

    target_device = device if device is not None else default_device()
    return FrozenBackbone(
        model,
        tokenizer=tokenizer,
        device=target_device,
        dtype=None,  # déjà chargé dans le bon dtype
        max_length=max_length,
        name=model_id,
    )
