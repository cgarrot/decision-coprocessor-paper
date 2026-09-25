"""Données d'extraction (étage T) — interface texte ↔ mémoire prédite.

Interface figée (indépendante des futurs pools E5 d'@ag-2) :

- :class:`ExtractionTargets` : texte + entités + mentions (spans caractères) +
  successeur par entité (-1 = terminal) + pointeur de départ ;
- :func:`targets_from_problem` : adaptateur **temporaire** depuis un
  ``v2data.bfamily.Problem`` (texte public + vue privée) — remplaçable par le
  format E5 sans changer le reste ;
- :func:`collate_extraction` : tenseurs torch (tokens, spans de mentions,
  cibles de tagger BIO, successeur, départ).

Aucun champ privé n'entre dans les entrées du modèle : seul ``text`` est
visible ; les cibles ne servent qu'aux pertes/métriques.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import torch

__all__ = [
    "ExtractionTargets",
    "ExtractionBatch",
    "targets_from_problem",
    "collate_extraction",
    "char_span_to_token_span",
    "tagger_targets_from_spans",
]

TAG_O, TAG_IN = 0, 1
# Compatibilité : ancien schéma BIO (B=IN sur le premier token, I=IN interne).
TAG_B, TAG_I = TAG_IN, TAG_IN


@dataclass(frozen=True)
class ExtractionTargets:
    """Cibles exactes d'extraction pour un texte (vue d'entraînement)."""

    id: str
    text: str
    labels: tuple[str, ...]                         # entités canoniques (index)
    mentions: tuple[tuple[tuple[int, int], ...], ...]  # char spans par entité
    successor: tuple[int, ...]                      # index successeur, -1 = terminal
    start: int
    question_char_span: tuple[int, int] | None = None   # span du texte de la question
    fact_char_spans: tuple[tuple[int, int], ...] = ()    # une ligne = un fait relationnel
    fact_subject: tuple[int, ...] = ()                  # entité sujet de chaque fait
    fact_object: tuple[int, ...] = ()                   # entité objet, -1 = terminal
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = len(self.labels)
        if n < 2:
            raise ValueError("au moins 2 entités requises")
        if len(self.mentions) != n or len(self.successor) != n:
            raise ValueError("mentions/successor doivent avoir une entrée par entité")
        if len(set(self.labels)) != n:
            raise ValueError("labels dupliqués")
        for index, spans in enumerate(self.mentions):
            if not spans:
                raise ValueError(f"entité {index}: aucune mention")
            for start, end in spans:
                if not (0 <= start < end <= len(self.text)):
                    raise ValueError(f"mention hors bornes: {(start, end)}")
        for index, successor in enumerate(self.successor):
            # -1 = TERMINAL ; -2 = INCONNU (A2, addendum) ; sinon index de mention
            if successor not in (-1, -2) and not (0 <= successor < n):
                raise ValueError(f"successeur hors bornes pour {index}")
            if successor == index:
                raise ValueError(f"auto-successeur interdit pour {index}")
        if not (0 <= self.start < n):
            raise ValueError("départ hors bornes")

    @property
    def terminals(self) -> tuple[int, ...]:
        return tuple(index for index, successor in enumerate(self.successor) if successor == -1)


@dataclass
class ExtractionBatch:
    input_ids: torch.Tensor          # [B, L]
    attention_mask: torch.Tensor     # [B, L]
    offsets: torch.Tensor            # [B, L, 2]
    mention_spans: torch.Tensor      # [B, N, 2] — spans de TOKENS
    mention_mask: torch.Tensor       # [B, N]
    question_spans: torch.Tensor     # [B, 2] — tokens de la question (0,0 si absente)
    fact_spans: torch.Tensor         # [B, F, 2] — tokens par fait (ligne)
    fact_mask: torch.Tensor          # [B, F]
    fact_subject: torch.Tensor       # [B, F] — index entité
    fact_object: torch.Tensor        # [B, F] — index entité, -1 = terminal
    successor: torch.Tensor          # [B, N] (-1 terminal ; padding masqué)
    start: torch.Tensor              # [B]
    tagger_targets: torch.Tensor     # [B, L] (O/B/I)
    texts: list[str]
    question_texts: list[str]
    ids: list[str]
    labels: list[list[str]]

    def to(self, device: torch.device | str) -> "ExtractionBatch":
        return ExtractionBatch(
            input_ids=self.input_ids.to(device),
            attention_mask=self.attention_mask.to(device),
            offsets=self.offsets.to(device),
            mention_spans=self.mention_spans.to(device),
            mention_mask=self.mention_mask.to(device),
            question_spans=self.question_spans.to(device),
            fact_spans=self.fact_spans.to(device),
            fact_mask=self.fact_mask.to(device),
            fact_subject=self.fact_subject.to(device),
            fact_object=self.fact_object.to(device),
            successor=self.successor.to(device),
            start=self.start.to(device),
            tagger_targets=self.tagger_targets.to(device),
            texts=list(self.texts),
            question_texts=list(self.question_texts),
            ids=list(self.ids),
            labels=[list(row) for row in self.labels],
        )


LABEL_BOUNDARY = r"(?<![0-9A-Za-z_]){}(?![0-9A-Za-z_])"


def _parse_fact_line(line: str) -> tuple[list[tuple[str, str]], list[str], str]:
    """Parse une ligne-fait : **v2 strict d'abord**, repli v1 EXPLICITE.

    Le repli n'a lieu que si v2 échoue ET que v1 reconnaît la ligne (textes
    historiques de tests) ; sinon l'erreur v2 est propagée (strict).
    """
    from v2data.textfamily import parse_state, parse_state_v2

    try:
        edges, terminals = parse_state_v2(line)
        return edges, terminals, "v2"
    except ValueError as v2_error:
        try:
            edges, terminals = parse_state(line)
            return edges, terminals, "v1"
        except ValueError:
            raise v2_error


def _label_occurrences(text: str, label: str) -> list[tuple[int, int]]:
    pattern = re.compile(_label_boundary_pattern(label))
    return [(match.start(), match.end()) for match in pattern.finditer(text)]


def _label_boundary_pattern(label: str) -> str:
    return LABEL_BOUNDARY.format(re.escape(label))


def targets_from_problem(problem: Any, *, text: str | None = None) -> ExtractionTargets:
    """Adaptateur ``v2data`` → cibles d'extraction (E5 texte + legacy S).

    Formats acceptés :
    - ``v2data.textfamily`` / JSONL E5 : ``input.{state,question,options}`` +
      ``private.graph`` (nœuds, arêtes, départ, options) — le texte visible est
      ``state + question`` ;
    - ``v2data.bfamily.Problem`` (objet) ou dict ``{"input", "private"}``
      avec texte public (legacy).

    Les mentions sont localisées par occurrences du label avec frontières de
    mot (aucune supposition sur la tokenisation).
    """
    if isinstance(problem, Mapping):
        public = problem.get("input", problem)
        private = problem.get("private", {}) or {}
        if "graph" in private:
            graph = private["graph"]
            nodes = list(graph["nodes"])
            state = str(public.get("state", ""))
            question = str(public.get("question", ""))
            default_text = state + ("\n" + question if question else "")
            text = text if text is not None else default_text
            successor_map = {source: target for source, target in graph["edges"]}
            start_label = graph["query"]["start"]
            index = {label: position for position, label in enumerate(nodes)}
            option_nodes = [option.get("node") for option in graph.get("options", [])]
            option_indices = [
                index[node] if node in index else -1 for node in option_nodes
            ]
            successor = [
                -1 if label not in successor_map else index[successor_map[label]]
                for label in nodes
            ]
            mentions = tuple(
                tuple(_label_occurrences(text, label)) for label in nodes
            )
            # Fait = ligne du state (structure visible) ; le sujet/objet vient de
            # l'oracle par ligne via les templates connus (parse_state).
            fact_char_spans: list[tuple[int, int]] = []
            fact_subject: list[int] = []
            fact_object: list[int] = []
            cursor = 0
            for line in state.split("\n"):
                line_end = cursor + len(line)
                if line.strip():
                    edges_line, terms_line, _fmt = _parse_fact_line(line)
                    if edges_line:
                        source, target = edges_line[0]
                        fact_char_spans.append((cursor, line_end))
                        fact_subject.append(index[source])
                        fact_object.append(index[target])
                    elif terms_line:
                        fact_char_spans.append((cursor, line_end))
                        fact_subject.append(index[terms_line[0]])
                        fact_object.append(-1)
                    else:
                        raise ValueError(
                            f"ligne d'état non analysable (v2 strict): {line!r}"
                        )
                cursor = line_end + 1
            return ExtractionTargets(
                id=str(problem.get("id", "")),
                text=text,
                labels=tuple(nodes),
                mentions=mentions,
                successor=tuple(successor),
                start=index[start_label],
                question_char_span=(
                    (len(state) + 1, len(state) + 1 + len(question))
                    if question
                    else None
                ),
                fact_char_spans=tuple(fact_char_spans),
                fact_subject=tuple(fact_subject),
                fact_object=tuple(fact_object),
                meta={
                    "option_nodes": option_nodes,
                    "option_indices": option_indices,
                    "pool": problem.get("pool", ""),
                    "pair": private.get("pair", {}),
                },
            )
        nodes = list(public["nodes"])
        edges = public["edges"]
        start_label = public["query"]["start"]
        text = text if text is not None else problem.get("text", "")
        successor_map = {source: target for source, target in edges}
    else:
        nodes = list(problem.nodes)
        successor_map = problem.successor_map()
        start_label = problem.start
        text = text if text is not None else problem.public_text()
    index = {label: position for position, label in enumerate(nodes)}
    successor: list[int] = []
    for label in nodes:
        target = successor_map.get(label)
        successor.append(-1 if target is None else index[target])
    mentions = tuple(
        tuple(_label_occurrences(text, label)) for label in nodes
    )
    return ExtractionTargets(
        id=str(problem.id if not isinstance(problem, Mapping) else problem.get("id", "")),
        text=text,
        labels=tuple(nodes),
        mentions=mentions,
        successor=tuple(successor),
        start=index[start_label],
    )


def char_span_to_token_span(
    offsets: Sequence[tuple[int, int]], char_start: int, char_end: int
) -> tuple[int, int]:
    """Span de tokens couvrant ``[char_start, char_end)`` (tokenisation effective)."""
    selected = [
        index for index, (start, end) in enumerate(offsets)
        if start < char_end and end > char_start
    ]
    if not selected:
        raise ValueError(f"aucun token ne couvre [{char_start}, {char_end})")
    if selected != list(range(selected[0], selected[-1] + 1)):
        raise ValueError("tokens non contigus pour la mention")
    first_start = offsets[selected[0]][0]
    last_end = offsets[selected[-1]][1]
    if first_start > char_start or last_end < char_end:
        raise ValueError("span de tokens incomplet pour la mention")
    return selected[0], selected[-1] + 1


def tagger_targets_from_spans(
    token_spans: Sequence[tuple[int, int]], length: int
) -> list[int]:
    """Cibles IN/OUT : 1 pour tout token à l'intérieur d'une mention.

    Décodage en **runs maximaux** de 1 (pas de distinction B/I : les mentions
    sont séparées par des tokens OUT, ce qui évite toute ambiguïté de
    transition pour une tête position-wise).
    """
    targets = [TAG_O] * int(length)
    for start, end in sorted(token_spans):
        if not (0 <= start < end <= length):
            raise ValueError(f"span de tokens hors bornes: {(start, end)}")
        for position in range(start, end):
            targets[position] = TAG_IN
    return targets


def collate_extraction(
    targets: Sequence[ExtractionTargets],
    tokenizer: Any,
    *,
    max_length: int | None = None,
    pad_token_id: int | None = None,
    device: torch.device | str | None = None,
) -> ExtractionBatch:
    """Tokenisation effective du texte complet + spans de mentions par entité."""
    if not targets:
        raise ValueError("lot vide")
    pad = pad_token_id if pad_token_id is not None else (
        getattr(tokenizer, "pad_token_id", 0) or 0
    )
    encoded = []
    max_tokens = 0
    for item in targets:
        enc = tokenizer(
            item.text, add_special_tokens=False, return_offsets_mapping=True
        )
        ids = [int(value) for value in enc["input_ids"]]
        offsets = [(int(s), int(e)) for s, e in enc["offset_mapping"]]
        if max_length is not None and len(ids) > max_length:
            raise ValueError(f"{item.id}: {len(ids)} tokens > max_length={max_length}")
        max_tokens = max(max_tokens, len(ids))
        encoded.append((ids, offsets))

    batch = len(targets)
    max_mentions = max(len(item.labels) for item in targets)
    input_ids = torch.full((batch, max_tokens), int(pad), dtype=torch.long)
    attention_mask = torch.zeros((batch, max_tokens), dtype=torch.long)
    offsets_out = torch.zeros((batch, max_tokens, 2), dtype=torch.long)
    mention_spans = torch.zeros((batch, max_mentions, 2), dtype=torch.long)
    mention_mask = torch.zeros((batch, max_mentions), dtype=torch.bool)
    question_spans = torch.zeros((batch, 2), dtype=torch.long)
    max_facts = max((len(item.fact_char_spans) for item in targets), default=0)
    fact_spans = torch.zeros((batch, max_facts, 2), dtype=torch.long)
    fact_mask = torch.zeros((batch, max_facts), dtype=torch.bool)
    fact_subject = torch.zeros((batch, max_facts), dtype=torch.long)
    fact_object = torch.zeros((batch, max_facts), dtype=torch.long)
    successor = torch.zeros((batch, max_mentions), dtype=torch.long)
    start = torch.zeros((batch,), dtype=torch.long)
    tagger_targets = torch.zeros((batch, max_tokens), dtype=torch.long)
    labels_out: list[list[str]] = []

    for row, item in enumerate(targets):
        ids, offsets = encoded[row]
        length = len(ids)
        input_ids[row, :length] = torch.tensor(ids, dtype=torch.long)
        attention_mask[row, :length] = 1
        offsets_out[row, :length] = torch.tensor(offsets, dtype=torch.long)
        spans: list[tuple[int, int]] = []
        all_spans: list[tuple[int, int]] = []
        for entity, char_spans in enumerate(item.mentions):
            token_span = char_span_to_token_span(offsets, *char_spans[0])
            mention_spans[row, entity] = torch.tensor(token_span, dtype=torch.long)
            spans.append(token_span)
            for char_start, char_end in char_spans:
                all_spans.append(char_span_to_token_span(offsets, char_start, char_end))
        mention_mask[row, : len(item.labels)] = True
        if item.question_char_span is not None:
            question_spans[row] = torch.tensor(
                char_span_to_token_span(offsets, *item.question_char_span),
                dtype=torch.long,
            )
        for fact_index, fact_char_span in enumerate(item.fact_char_spans):
            fact_spans[row, fact_index] = torch.tensor(
                char_span_to_token_span(offsets, *fact_char_span), dtype=torch.long
            )
            fact_subject[row, fact_index] = item.fact_subject[fact_index]
            fact_object[row, fact_index] = item.fact_object[fact_index]
        if item.fact_char_spans:
            fact_mask[row, : len(item.fact_char_spans)] = True
        successor[row, : len(item.labels)] = torch.tensor(item.successor, dtype=torch.long)
        start[row] = item.start
        tagger_targets[row, :length] = torch.tensor(
            tagger_targets_from_spans(all_spans, length), dtype=torch.long
        )
        labels_out.append(list(item.labels))

    output = ExtractionBatch(
        input_ids=input_ids,
        attention_mask=attention_mask,
        offsets=offsets_out,
        mention_spans=mention_spans,
        mention_mask=mention_mask,
        question_spans=question_spans,
        fact_spans=fact_spans,
        fact_mask=fact_mask,
        fact_subject=fact_subject,
        fact_object=fact_object,
        successor=successor,
        start=start,
        tagger_targets=tagger_targets,
        texts=[item.text for item in targets],
        question_texts=[
            item.text[item.question_char_span[0]:item.question_char_span[1]]
            if item.question_char_span is not None else ""
            for item in targets
        ],
        ids=[item.id for item in targets],
        labels=labels_out,
    )
    if device is not None:
        output = output.to(device)
    return output
