"""Extracteur texte → mémoire structurée (étage T) — backbone gelé.

Entrée : ``H`` du backbone **gelé** (no_grad, jamais de logits vocabulaire) sur
le texte seul. Sorties :

1. **détection d'entités** : tagger BIO token-level (O/B/I) → mentions ;
2. **successeur** : classification par entité sur ``N+1`` classes (N entités +
   TERMINAL) — un softmax par entité, contrainte « successeur unique »
   satisfaite par construction (pas de post-traitement), décodage O(N²) via
   produit bilinéaire ``m_i^T W m_j`` (un matmul, pas N² MLP) ;
3. **départ** : classifieur sur les mentions, **conditionné au contexte de la
   question** (le départ y est toujours désigné ; la question est une entrée
   publique, jamais la réponse ni les candidats privés) ;
4. terminaux = entités de successeur TERMINAL (dérivable).

Aucun raccourci : l'extracteur ne voit jamais la question, la réponse, ni une
mémoire oracle — uniquement ``H`` (texte) et, à l'entraînement, les cibles.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

import re

import torch
import torch.nn as nn
import torch.nn.functional as F

from .extraction_data import ExtractionBatch, TAG_IN, TAG_O

__all__ = [
    "ExtractorConfig",
    "PredictedMemory",
    "MemoryExtractor",
    "normalize_mentions",
    "entity_metrics",
    "successors_from_facts",
    "normalize_for_match",
    "deterministic_start",
    "hybrid_start",
    "train_extractor",
]


@dataclass
class ExtractorConfig:
    hidden_size: int
    d_model: int = 64
    hidden: int = 128
    tagger_hidden: int = 128
    tagger_context: bool = True     # 1 couche d'auto-attention trainable sur H
    tagger_balance: bool = True     # pondération de classe IN/OUT
    context_window: int = 0         # 0 = identité stricte ; >0 = fenêtre autour des mentions
    relation_attention: bool = True # cross-attention mention → texte (relations)
    relation_heads: int = 4
    tagger_heads: int = 4
    tag_weight: float = 1.0
    successor_weight: float = 1.0
    fact_weight: float = 1.0
    relation_mode: str = "fact"       # fact (par ligne) | bilinear (v2)
    unknown_class: bool = False       # A2 : « sans fait ⇒ -2 » (INCONNU) ; OFF = legacy
    deterministic_start: bool = True  # containment question→mentions (it2)
    start_weight: float = 1.0
    max_length: int = 512


@dataclass
class PredictedMemory:
    """Mémoire prédite — consommable par l'exécuteur (contrat S)."""

    id: str
    text: str
    labels: list[str]                     # identités canoniques (e0..eN-1)
    char_spans: list[tuple[int, int]]     # mention principale par entité
    token_spans: list[tuple[int, int]]
    successor: list[int]                  # index successeur, -1 = terminal
    start: int
    confidences: list[float] = field(default_factory=list)
    start_source: str = "learned"         # deterministic | learned (diagnostic)
    successor_probs: torch.Tensor | None = None   # [N, N+1] (diagnostic)
    start_probs: torch.Tensor | None = None       # [N]
    tagger_probs: torch.Tensor | None = None      # [L, 3] (diagnostic)

    @property
    def terminals(self) -> list[int]:
        return [index for index, value in enumerate(self.successor) if value == -1]

    @property
    def n_entities(self) -> int:
        return len(self.labels)


def normalize_mentions(
    text: str, entries: list[tuple[tuple[int, int], int, int, float]]
) -> list[tuple[tuple[int, int], int, int, float]]:
    """Normalise les mentions (correctif de CONSTRUCTION, pas de critère).

    - strip des blancs aux deux bords ;
    - fusion des runs adjacents/chevauchements après strip ;
    - déduplication par texte exact, en gardant la confiance maximale.

    ``entries`` : ``[(token_span, char_start, char_end, confidence)]``.
    """
    cleaned: list[list] = []
    for token_span, char_start, char_end, confidence in entries:
        while char_start < char_end and text[char_start].isspace():
            char_start += 1
        while char_end > char_start and text[char_end - 1].isspace():
            char_end -= 1
        if char_start < char_end:
            cleaned.append([tuple(token_span), char_start, char_end, float(confidence)])
    cleaned.sort(key=lambda entry: entry[1])
    merged: list[list] = []
    for entry in cleaned:
        if merged and entry[1] <= merged[-1][2]:
            last = merged[-1]
            last[0] = (min(last[0][0], entry[0][0]), max(last[0][1], entry[0][1]))
            last[2] = max(last[2], entry[2])
            last[3] = max(last[3], entry[3])
        else:
            merged.append(entry)
    best: dict[str, list] = {}
    order: list[str] = []
    for entry in merged:
        key = text[entry[1]:entry[2]]
        if key not in best:
            best[key] = entry
            order.append(key)
        elif entry[3] > best[key][3]:
            best[key] = entry
    return [best[key] for key in order]


def entity_metrics(
    predicted: list[list[tuple[int, int, str]]],
    target: list[list[tuple[int, int, str]]],
    *,
    strict: bool = True,
) -> dict:
    """P/R/F1 de mentions — strict (spans exacts) ou stripped (textes normalisés)."""
    true_positive = false_positive = false_negative = 0
    predicted_counts: list[int] = []
    target_counts: list[int] = []
    for pred_spans, target_spans in zip(predicted, target):
        predicted_counts.append(len(pred_spans))
        target_counts.append(len(target_spans))
        if strict:
            pred_keys = [(start, end) for start, end, _ in pred_spans]
            target_keys = [(start, end) for start, end, _ in target_spans]
        else:
            pred_keys = [text.strip() for _, _, text in pred_spans]
            target_keys = [text.strip() for _, _, text in target_spans]
        pred_counter = Counter(pred_keys)
        target_counter = Counter(target_keys)
        true_positive += sum((pred_counter & target_counter).values())
        false_positive += sum((pred_counter - target_counter).values())
        false_negative += sum((target_counter - pred_counter).values())
    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "predicted_mean": sum(predicted_counts) / max(1, len(predicted_counts)),
        "target_mean": sum(target_counts) / max(1, len(target_counts)),
    }


def successors_from_facts(
    subject_logits: torch.Tensor,
    object_logits: torch.Tensor,
    fact_mask: torch.Tensor,
    *,
    unknown: bool = False,
) -> list[list[int]]:
    """Relations lues PAR FAIT : ``(sujet, objet|terminal)`` → successeurs.

    ``subject_logits [B,F,N]``, ``object_logits [B,F,N+1]`` (dernier = terminal),
    ``fact_mask [B,F]``. En cas de faits conflictuels sur un même sujet, la
    confiance ``P(sujet)·P(objet)`` la plus haute gagne.

    ``unknown=True`` (A2, addendum) : une entité sans fait sujet ET sans fait
    terminal ⇒ ``-2`` (INCONNU) — corrige « entité sans fait ⇒ terminale »
    (audit §5 : « absence d'information ≠ terminal »). Défaut ``False`` =
    comportement legacy (``-1``), byte-identique aux runs V2/V2.1.
    """
    boolean = fact_mask.bool()
    subj_probs = torch.softmax(
        subject_logits.float().masked_fill(~boolean[..., None], -1e9), dim=-1
    )
    obj_probs = torch.softmax(
        object_logits.float().masked_fill(~boolean[..., None], -1e9), dim=-1
    )
    batch, n_facts = boolean.shape
    n_entities = int(subject_logits.shape[-1])
    results: list[list[int]] = []
    for row in range(batch):
        best: dict[int, tuple[float, int]] = {}
        for fact in range(n_facts):
            if not bool(boolean[row, fact]):
                continue
            subject = int(subj_probs[row, fact].argmax())
            obj_class = int(obj_probs[row, fact].argmax())
            confidence = float(subj_probs[row, fact, subject]) * float(
                obj_probs[row, fact, obj_class]
            )
            if confidence > best.get(subject, (-1.0, -1))[0]:
                best[subject] = (
                    confidence,
                    -1 if obj_class == n_entities else obj_class,
                )
        results.append([
            best.get(entity, (0.0, -2 if unknown else -1))[1]
            for entity in range(n_entities)
        ])
    return results


def normalize_for_match(text: str) -> str:
    """Normalisation pour l'appariement déterministe (case + espaces)."""
    return re.sub(r"\s+", " ", str(text).strip().casefold())


def deterministic_start(
    text: str,
    char_spans: Sequence[tuple[int, int]],
    question_text: str,
) -> int | None:
    """Départ par CONTAINMENT : la question cite toujours le label de départ.

    Retourne l'index de la seule mention dont le texte apparaît dans la question
    (frontières de mot, case/espaces normalisés) ; ``None`` si aucune ou
    plusieurs mentions matchent (→ repli sur la tête apprise).
    """
    if not question_text or not char_spans:
        return None
    question = normalize_for_match(question_text)
    matched: list[int] = []
    for index, (char_start, char_end) in enumerate(char_spans):
        mention = normalize_for_match(text[char_start:char_end])
        if not mention:
            continue
        pattern = re.compile(
            r"(?<![0-9a-z_])" + re.escape(mention) + r"(?![0-9a-z_])"
        )
        if pattern.search(question):
            matched.append(index)
    return matched[0] if len(matched) == 1 else None


def hybrid_start(learned_index: int, deterministic_index: int | None) -> int:
    """Start = containment déterministe PRINCIPAL ; tête apprise en REPLI."""
    return int(deterministic_index) if deterministic_index is not None else int(learned_index)


def masked_span_mean(
    hidden: torch.Tensor, spans: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Moyenne des tokens ``[start, end)`` par mention — O(B·L·D) via cumsum."""
    batch, length, dim = hidden.shape
    compute = hidden.float() if hidden.dtype in (torch.float16, torch.bfloat16) else hidden
    prefix = compute.cumsum(dim=1)
    starts = spans[..., 0].clamp(min=0)
    ends = spans[..., 1].clamp(min=1, max=length)
    end_sum = prefix.gather(
        1, (ends - 1).unsqueeze(-1).expand(-1, -1, dim)
    )
    before_sum = prefix.gather(
        1, (starts - 1).clamp(min=0).unsqueeze(-1).expand(-1, -1, dim)
    )
    before_sum = torch.where(
        (starts > 0).unsqueeze(-1), before_sum, torch.zeros_like(before_sum)
    )
    counts = (ends - starts).clamp(min=1).unsqueeze(-1).to(end_sum.dtype)
    pooled = (end_sum - before_sum) / counts
    return torch.where(mask.unsqueeze(-1), pooled, torch.zeros_like(pooled))


class MemoryExtractor(nn.Module):
    """Tagger BIO + têtes successeur/départ sur représentations de mentions."""

    def __init__(self, config: ExtractorConfig) -> None:
        super().__init__()
        self.config = config
        context_layers = 1 if config.tagger_context else 0
        self.tagger_context = (
            nn.TransformerEncoderLayer(
                d_model=config.hidden_size,
                nhead=config.tagger_heads,
                dim_feedforward=2 * config.tagger_hidden,
                dropout=0.0,
                activation="gelu",
                batch_first=True,
                norm_first=True,
            )
            if context_layers
            else None
        )
        self.tagger = nn.Sequential(
            nn.Linear(config.hidden_size, config.tagger_hidden),
            nn.GELU(),
            nn.Linear(config.tagger_hidden, 2),
        )
        self.mention_proj = nn.Sequential(
            nn.Linear(config.hidden_size, config.d_model),
            nn.LayerNorm(config.d_model),
            nn.GELU(),
        )
        self.token_proj = nn.Linear(config.hidden_size, config.d_model)
        self.relation_attention = (
            nn.MultiheadAttention(
                config.d_model, config.relation_heads, batch_first=True, dropout=0.0
            )
            if config.relation_attention
            else None
        )
        self.relation_norm = nn.LayerNorm(config.d_model)
        self.successor_bilinear = nn.Parameter(
            torch.empty(config.d_model, config.d_model).normal_(std=0.02)
        )
        self.terminal_score = nn.Linear(config.d_model, 1)
        self.start_proj = nn.Linear(config.d_model, 1)
        self.start_query = nn.Linear(config.d_model, config.d_model)
        self.start_key = nn.Linear(config.d_model, config.d_model)
        self.start_question = nn.Sequential(
            nn.Linear(3 * config.d_model + 1, config.hidden),
            nn.GELU(),
            nn.Linear(config.hidden, 1),
        )
        # --- Lecteur v3 : relation PAR FAIT (une ligne = un fait visible) ---
        self.fact_mean_proj = nn.Linear(config.hidden_size, config.d_model)
        self.fact_attn_proj = nn.Linear(config.hidden_size, config.d_model)
        self.fact_attn_score = nn.Linear(config.hidden_size, 1)
        self.fact_norm = nn.LayerNorm(config.d_model)
        self.subject_proj = nn.Linear(config.d_model, config.d_model)
        self.object_proj = nn.Linear(config.d_model, config.d_model)
        self.terminal_fact = nn.Linear(config.d_model, 1)

    # ---- têtes ----------------------------------------------------------
    def tagger_logits(
        self, hidden: torch.Tensor, attention_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        context = hidden
        if self.tagger_context is not None:
            padding = (~attention_mask.bool()) if attention_mask is not None else None
            context = self.tagger_context(hidden, src_key_padding_mask=padding)
        return self.tagger(context)

    def mention_reps(
        self,
        hidden: torch.Tensor,
        spans: torch.Tensor,
        mention_mask: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        window = int(self.config.context_window)
        pooled_spans = spans
        if window:
            pooled_spans = torch.stack(
                [
                    (spans[..., 0] - window).clamp(min=0),
                    (spans[..., 1] + window).clamp(max=hidden.shape[1]),
                ],
                dim=-1,
            )
        pooled = masked_span_mean(hidden, pooled_spans, mention_mask)
        reps = self.mention_proj(pooled)
        if self.relation_attention is not None:
            tokens = self.token_proj(hidden)
            padding = (
                ~attention_mask.bool() if attention_mask is not None
                else (~mention_mask.new_ones(hidden.shape[:2]))
            )
            attended, _ = self.relation_attention(
                reps, tokens, tokens, key_padding_mask=padding, need_weights=False
            )
            reps = self.relation_norm(reps + attended)
        return reps

    def successor_logits(
        self, reps: torch.Tensor, mention_mask: torch.Tensor
    ) -> torch.Tensor:
        """``[B, N, N+1]`` : scores bilinéaires + classe TERMINAL."""
        scores = torch.einsum("bnd,de,bme->bnm", reps, self.successor_bilinear, reps)
        terminal = self.terminal_score(reps)                     # [B, N, 1]
        logits = torch.cat([scores, terminal], dim=-1)           # [B, N, N+1]
        return logits

    def fact_reps(
        self,
        hidden: torch.Tensor,
        fact_spans: torch.Tensor,
        fact_mask: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Représentation d'un fait : moyenne masquée + attention intra-fait.

        L'attention est restreinte aux tokens DU FAIT (masque de span), donc
        aucune information ne fuit d'une ligne à l'autre.
        """
        mean = masked_span_mean(hidden, fact_spans, fact_mask)
        scores = self.fact_attn_score(hidden).squeeze(-1)            # [B, L]
        length = hidden.shape[1]
        positions = torch.arange(length, device=hidden.device)
        span_mask = (
            (positions[None, None, :] >= fact_spans[..., 0:1])
            & (positions[None, None, :] < fact_spans[..., 1:2])
        ) & fact_mask[:, :, None]
        scores = scores[:, None, :].masked_fill(
            ~span_mask, torch.finfo(scores.dtype).min
        )
        weights = torch.softmax(scores.float(), dim=-1).to(hidden.dtype)
        attended = torch.einsum("bfl,bld->bfd", weights, hidden)
        return self.fact_norm(
            self.fact_mean_proj(mean) + self.fact_attn_proj(attended)
        )

    def fact_logits(
        self, reps: torch.Tensor, fact_reps: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """``(subject [B,F,N], object [B,F,N+1])`` — objet N = terminal."""
        subject = torch.einsum(
            "bfd,bnd->bfn", self.subject_proj(fact_reps), reps
        )
        object_entities = torch.einsum(
            "bfd,bnd->bfn", self.object_proj(fact_reps), reps
        )
        terminal = self.terminal_fact(fact_reps)                     # [B, F, 1]
        return subject, torch.cat([object_entities, terminal], dim=-1)

    def start_logits(
        self,
        reps: torch.Tensor,
        mention_mask: torch.Tensor,
        hidden: torch.Tensor,
        attention_mask: torch.Tensor,
        question_spans: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Score de départ conditionné à la QUESTION (câblage explicite).

        Le départ est toujours désigné dans la question : on lit un contexte de
        question (moyenne masquée de ses tokens, projetée en d) et on l'oppose à
        chaque mention — score local + MLP [m_i, q_ctx, m_i*q_ctx].
        """
        base = self.start_proj(reps).squeeze(-1)                 # [B, N]
        question_mask: torch.Tensor | None = None
        if question_spans is not None and question_spans.numel() > 0:
            lengths = question_spans[:, 1] - question_spans[:, 0]
            has_question = lengths > 0
            pooled = masked_span_mean(
                hidden, question_spans.unsqueeze(1), has_question.unsqueeze(1)
            )                                                        # [B, 1, D]
            context = self.token_proj(pooled[:, 0])                  # [B, d]
            context = torch.where(
                has_question.unsqueeze(-1), context, torch.zeros_like(context)
            )
            positions = torch.arange(hidden.shape[1], device=hidden.device)
            question_mask = (
                (positions[None, :] >= question_spans[:, 0:1])
                & (positions[None, :] < question_spans[:, 1:2])
            )
        else:
            weights = attention_mask.to(hidden.dtype).unsqueeze(-1)
            global_pool = (hidden * weights).sum(dim=1) / weights.sum(dim=1).clamp(min=1.0)
            context = self.token_proj(global_pool)
        context = context.unsqueeze(1).expand_as(reps)
        # Appariement TOKEN-À-TOKEN mention ↔ tokens de la question (le départ y
        # est toujours désigné) : query = mention, key = tokens question, max lissé.
        match = torch.zeros_like(base)
        if question_mask is not None and bool(question_mask.any()):
            tokens = self.token_proj(hidden)                         # [B, L, d]
            queries = self.start_query(reps)                         # [B, N, d]
            keys = self.start_key(tokens)                            # [B, L, d]
            scores = torch.einsum("bnd,bld->bnl", queries, keys)
            scores = scores / (self.config.d_model ** 0.5)
            scores = scores.masked_fill(
                ~question_mask[:, None, :], torch.finfo(scores.dtype).min
            )
            match = torch.logsumexp(scores, dim=-1)                  # [B, N]
        features = torch.cat(
            [reps, context, reps * context, match.unsqueeze(-1)], dim=-1
        )
        return base + self.start_question(features).squeeze(-1)

    # ---- perte ----------------------------------------------------------
    def loss(
        self, batch: ExtractionBatch, hidden: torch.Tensor
    ) -> tuple[torch.Tensor, dict[str, float]]:
        hidden = hidden.to(dtype=self.tagger[0].weight.dtype)   # H bf16 → FP32
        token_mask = batch.attention_mask.bool()
        tagger_logits = self.tagger_logits(hidden, batch.attention_mask)   # [B, L, 3]
        if self.config.tagger_balance:
            counts = torch.bincount(
                batch.tagger_targets[token_mask], minlength=2
            ).float()
            weights = counts.sum() / (2.0 * counts.clamp(min=1))
            ce_tag = F.cross_entropy(
                tagger_logits[token_mask], batch.tagger_targets[token_mask],
                weight=weights,
            )
        else:
            ce_tag = F.cross_entropy(
                tagger_logits[token_mask], batch.tagger_targets[token_mask]
            )
        reps = self.mention_reps(
            hidden, batch.mention_spans, batch.mention_mask, batch.attention_mask
        )
        n_entities = reps.shape[1]
        if self.config.relation_mode == "fact" and bool(batch.fact_mask.any()):
            fact_reps = self.fact_reps(
                hidden, batch.fact_spans, batch.fact_mask, batch.attention_mask
            )
            subject_logits, object_logits = self.fact_logits(reps, fact_reps)
            subject_target = batch.fact_subject
            object_target = torch.where(
                batch.fact_object < 0,
                torch.full_like(batch.fact_object, n_entities),
                batch.fact_object,
            )
            ce_successor = 0.5 * (
                F.cross_entropy(
                    subject_logits[batch.fact_mask], subject_target[batch.fact_mask]
                )
                + F.cross_entropy(
                    object_logits[batch.fact_mask], object_target[batch.fact_mask]
                )
            )
        else:
            successor_logits = self.successor_logits(reps, batch.mention_mask)
            targets = torch.where(
                batch.successor < 0,
                torch.full_like(batch.successor, n_entities),
                batch.successor,
            )
            ce_successor = F.cross_entropy(
                successor_logits[batch.mention_mask],
                targets[batch.mention_mask],
            ) if batch.mention_mask.any() else torch.zeros((), device=hidden.device)
        start_logits = self.start_logits(
            reps, batch.mention_mask, hidden, batch.attention_mask,
            batch.question_spans,
        )
        masked_start = start_logits.masked_fill(
            ~batch.mention_mask, torch.finfo(start_logits.dtype).min
        )
        ce_start = F.cross_entropy(masked_start, batch.start)
        total = (
            self.config.tag_weight * ce_tag
            + self.config.successor_weight * ce_successor
            + self.config.start_weight * ce_start
        )
        return total, {
            "ce_tag": float(ce_tag.detach()),
            "ce_successor": float(ce_successor.detach()),
            "ce_start": float(ce_start.detach()),
        }

    # ---- inférence ------------------------------------------------------
    @staticmethod
    def decode_mentions(
        tagger_logits: torch.Tensor,
        offsets: torch.Tensor,
        token_mask: torch.Tensor,
    ) -> list[list[tuple[int, int]]]:
        """Décode IN/OUT → runs maximaux de tokens par exemple."""
        tags = tagger_logits.argmax(dim=-1)                       # [B, L]
        decoded: list[list[tuple[int, int]]] = []
        for row in range(tags.shape[0]):
            spans: list[tuple[int, int]] = []
            length = int(token_mask[row].sum())
            start: int | None = None
            for token in range(length):
                if int(tags[row, token]) == TAG_IN:
                    if start is None:
                        start = token
                elif start is not None:
                    spans.append((start, token))
                    start = None
            if start is not None:
                spans.append((start, length))
            decoded.append(spans)
        return decoded

    @torch.no_grad()
    def extract(self, batch: ExtractionBatch, hidden: torch.Tensor) -> list[PredictedMemory]:
        """Mémoires prédites (mentions normalisées puis têtes successeur/départ)."""
        hidden = hidden.to(dtype=self.tagger[0].weight.dtype)   # H bf16 → FP32
        token_mask = batch.attention_mask.bool()
        tagger_logits = self.tagger_logits(hidden, batch.attention_mask)
        decoded = self.decode_mentions(tagger_logits, batch.offsets, token_mask)
        memories: list[PredictedMemory] = []
        for row, spans in enumerate(decoded):
            tag_probs = torch.softmax(tagger_logits[row], dim=-1)
            offsets = batch.offsets[row]
            entries: list[tuple[tuple[int, int], int, int, float]] = []
            for start_token, end_token in spans:
                confidence = (
                    float(tag_probs[start_token:end_token, TAG_IN].mean())
                    if end_token > start_token else 0.0
                )
                entries.append((
                    (int(start_token), int(end_token)),
                    int(offsets[start_token, 0]),
                    int(offsets[end_token - 1, 1]),
                    confidence,
                ))
            normalized = normalize_mentions(batch.texts[row], entries)
            if not normalized:
                memories.append(
                    PredictedMemory(
                        id=batch.ids[row], text=batch.texts[row], labels=[],
                        char_spans=[], token_spans=[], successor=[], start=0,
                    )
                )
                continue
            token_spans = [entry[0] for entry in normalized]
            char_spans = [(entry[1], entry[2]) for entry in normalized]
            confidences = [entry[3] for entry in normalized]
            max_mentions = len(normalized)
            mention_spans = torch.tensor(token_spans, dtype=torch.long, device=hidden.device)
            mention_mask = torch.ones(max_mentions, dtype=torch.bool, device=hidden.device)
            reps = self.mention_reps(
                hidden[row: row + 1], mention_spans.unsqueeze(0),
                mention_mask.unsqueeze(0), batch.attention_mask[row: row + 1],
            )
            successor_logits = self.successor_logits(
                reps, mention_mask.unsqueeze(0)
            )[0]
            start_logits = self.start_logits(
                reps, mention_mask.unsqueeze(0),
                hidden[row: row + 1], batch.attention_mask[row: row + 1],
                batch.question_spans[row: row + 1],
            )[0]
            successor_probs = torch.softmax(successor_logits, dim=-1)
            start_probs = torch.softmax(start_logits, dim=-1)
            use_facts = (
                self.config.relation_mode == "fact"
                and bool(batch.fact_mask[row].any())
            )
            if use_facts:
                fact_reps = self.fact_reps(
                    hidden[row: row + 1], batch.fact_spans[row: row + 1],
                    batch.fact_mask[row: row + 1], batch.attention_mask[row: row + 1],
                )
                subject_logits, object_logits = self.fact_logits(reps, fact_reps)
                successor_values = successors_from_facts(
                    subject_logits, object_logits, batch.fact_mask[row: row + 1],
                    unknown=self.config.unknown_class,
                )[0]
            else:
                if self.config.unknown_class:
                    raise NotImplementedError(
                        "INCONNU (-2) non supporté en mode bilinéaire "
                        "(A2 = mode fact, sémantique par masse de sujet manquante)"
                    )
                next_scores = successor_probs[:, :max_mentions]
                terminal_scores = successor_probs[:, max_mentions]
                successor_values = []
                for index in range(max_mentions):
                    best_next = int(next_scores[index].argmax())
                    if float(next_scores[index, best_next]) >= float(terminal_scores[index]):
                        successor_values.append(best_next)
                    else:
                        successor_values.append(-1)
            start = int(start_probs.argmax())
            start_source = "learned"
            if self.config.deterministic_start:
                deterministic = deterministic_start(
                    batch.texts[row], char_spans,
                    batch.question_texts[row] if batch.question_texts else "",
                )
                if deterministic is not None:
                    start = hybrid_start(start, deterministic)
                    start_source = "deterministic"
            labels = [f"e{index}" for index in range(max_mentions)]
            memories.append(
                PredictedMemory(
                    id=batch.ids[row],
                    text=batch.texts[row],
                    labels=labels,
                    char_spans=char_spans,
                    token_spans=token_spans,
                    successor=successor_values,
                    start=start,
                    confidences=confidences,
                    start_source=start_source,
                    successor_probs=successor_probs.cpu(),
                    start_probs=start_probs.cpu(),
                    tagger_probs=torch.softmax(tagger_logits[row], dim=-1).cpu(),
                )
            )
        return memories


def train_extractor(
    extractor: MemoryExtractor,
    backbone: Any,
    targets: Sequence[Any],
    *,
    tokenizer: Any,
    optimizer_steps: int = 1200,
    lr: float = 3e-4,
    weight_decay: float = 0.01,
    warmup_ratio: float = 0.05,
    batch_size: int = 8,
    accum: int = 1,
    seed: int = 17,
    max_length: int = 512,
    device: torch.device | str = "cpu",
) -> dict:
    """Boucle d'entraînement CPU/GPU du head seul (backbone gelé).

    Défauts alignés sur ``configs/e5_extract.yaml`` (mêmes plafonds que la
    baseline directe) : lr 3e-4, AdamW wd 0.01, warmup linéaire 5 %,
    clip 1.0. Pour un mini-backbone CPU, lr 3e-3 reste utilisable via l'API.
    """
    from .extraction_data import collate_extraction

    torch.manual_seed(seed)
    extractor = extractor.to(device)
    optimizer = torch.optim.AdamW(
        extractor.parameters(), lr=lr, weight_decay=weight_decay
    )
    warmup_steps = int(int(optimizer_steps) * float(warmup_ratio))
    base_lr = float(lr)
    accum = max(1, int(accum))
    generator = torch.Generator().manual_seed(seed)
    history: list[float] = []
    extractor.train()
    for step in range(int(optimizer_steps)):
        if warmup_steps:
            scale = min(1.0, (step + 1) / warmup_steps)
            for group in optimizer.param_groups:
                group["lr"] = base_lr * scale
        optimizer.zero_grad()
        step_loss = 0.0
        for _ in range(accum):
            size = min(int(batch_size), len(targets))
            chunk = torch.randint(len(targets), (size,), generator=generator).tolist()
            batch = collate_extraction(
                [targets[index] for index in chunk],
                tokenizer,
                max_length=max_length,
                device=device,
            )
            hidden = backbone.encode(batch.input_ids, batch.attention_mask)
            loss, _ = extractor.loss(batch, hidden)
            (loss / accum).backward()
            step_loss += float(loss.detach()) / accum
        torch.nn.utils.clip_grad_norm_(extractor.parameters(), 1.0)
        optimizer.step()
        history.append(step_loss)
    extractor.eval()
    return {
        "optimizer_steps": int(optimizer_steps),
        "loss_first": history[0] if history else None,
        "loss_last": history[-1] if history else None,
    }
