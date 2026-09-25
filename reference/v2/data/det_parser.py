"""(p) Parser déterministe BORNÉ aux templates — contrôle d'ingénierie.

Protocole V2.1 §3 voie (p) + audit §4.3 : lit EXCLUSIVEMENT le texte
public (état, question, options), aucun champ privé, aucun entraînement,
aucun apprentissage — expressions rationnelles sur la grammaire de rendus
français E5v2/V2.1 (templates, rappels, secondes déclarations, wrappers).

Sortie par exemple :
  {"uid", "parsed": bool, "coverage_reason": None|…,
   "start", "edges", "terminals",            # extraction (si parsé)
   "predicted_option_id": str|None,          # prédiction ou INCONNU
   "walk_terminal"}

Règles d'INCONNU (couverture publiée, jamais de défaillance silencieuse) :
- une ligne de l'état ne matche aucun template ;
- départ introuvable dans la question ;
- ambiguïté (plusieurs labels candidats au départ, option sans label) ;
- le nœud final de la marche n'est pas un terminal déclaré ;
- le terminal atteint n'apparaît dans aucune option.

Ce parser est un CONTRÔLE, pas un lecteur général : borné aux templates
synthétiques par conception. Les métriques produites sont des contrôles
d'ingénierie étiquetés « diagnostic », jamais comptées dans un benchmark
(V21_PROTOCOL.md §0.3).
"""
from __future__ import annotations

import re

from .textfamily import (EDGE_TEMPLATES_V2, TERMINAL_TEMPLATES_V2,
                         parse_state_v2)

_LABEL_RE = re.compile(r"[a-z]{1,3}\d{1,3}[A-Z]{1,3}")


class _Grammar:
    def __init__(self):
        self.edge_rx = [re.compile("^" + t.replace("{A}", f"({_LABEL_RE.pattern})")
                                   .replace("{B}", f"({_LABEL_RE.pattern})") + "$")
                        for t in EDGE_TEMPLATES_V2]
        self.term_rx = [re.compile("^" + t.replace("{T}", f"({_LABEL_RE.pattern})") + "$")
                        for t in TERMINAL_TEMPLATES_V2]

    def parse_line(self, line: str):
        """('edge', u, v) | ('term', t) | None."""
        for rx in self.edge_rx:
            m = rx.match(line)
            if m:
                return ("edge", m.group(1), m.group(2))
        for rx in self.term_rx:
            m = rx.match(line)
            if m:
                return ("term", m.group(1))
        return None


_G = _Grammar()


def parse_public(pub: dict) -> dict:
    """Extraction déterministe depuis la vue publique seule."""
    out = {"parsed": False, "coverage_reason": None, "start": None,
           "edges": [], "terminals": [], "walk_terminal": None,
           "predicted_option_id": None}
    # ---- état : arêtes + terminaux (rappels inclus, dédupliqués) ----
    edges, terminals, seen_e, seen_t = [], [], set(), set()
    for raw in pub["state"].split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Rappel : "):
            line = line[len("Rappel : "):]
        hit = _G.parse_line(line)
        if hit is None:
            out["coverage_reason"] = f"ligne hors grammaire : {raw!r}"
            return out
        if hit[0] == "edge":
            e = (hit[1], hit[2])
            if e not in seen_e:
                seen_e.add(e)
                edges.append(e)
        else:
            if hit[1] not in seen_t:
                seen_t.add(hit[1])
                terminals.append(hit[1])
    # ---- départ : label unique dans la question ----
    q_labels = _LABEL_RE.findall(pub["question"])
    if len(q_labels) != 1:
        out["coverage_reason"] = f"départ ambigu dans la question : {q_labels}"
        return out
    start = q_labels[0]
    # ---- options : exactement un label chacune ----
    opt_label = {}
    for o in pub["options"]:
        labs = _LABEL_RE.findall(o["text"])
        if len(labs) != 1:
            out["coverage_reason"] = f"option sans label unique : {o['text']!r}"
            return out
        opt_label[o["id"]] = labs[0]
    # ---- marche déterministe ----
    succ = {}
    for u, v in edges:
        if u in succ and succ[u] != v:
            out["coverage_reason"] = f"successeur multiple parsé pour {u}"
            return out
        succ[u] = v
    node, seen = start, {start}
    while node in succ:
        node = succ[node]
        if node in seen:
            out["coverage_reason"] = "cycle parsé"
            return out
        seen.add(node)
    if node not in set(terminals):
        out["coverage_reason"] = "final hors terminaux déclarés"
        return out
    matches = [oid for oid, lab in opt_label.items() if lab == node]
    if len(matches) != 1:
        out["coverage_reason"] = f"terminal {node} : {len(matches)} options"
        return out
    out.update({"parsed": True, "start": start, "edges": edges,
                "terminals": terminals, "walk_terminal": node,
                "predicted_option_id": matches[0]})
    return out


def coverage_and_control(rows: list[dict]) -> dict:
    """Couverture + accord avec la réponse privée (CONTRÔLE d'ingénierie,
    jamais un benchmark — étiquette « diagnostic » obligatoire)."""
    n = len(rows)
    parsed = 0
    agree = 0
    reasons: dict = {}
    for r in rows:
        res = parse_public(r["input"])
        if res["parsed"]:
            parsed += 1
            if res["predicted_option_id"] == r["private"]["graph"]["answer_id"]:
                agree += 1
        else:
            reasons[res["coverage_reason"].split(" :")[0]] = \
                reasons.get(res["coverage_reason"].split(" :")[0], 0) + 1
    return {"n": n, "parsed": parsed, "coverage": round(parsed / n, 4),
            "agree_with_private": agree,
            "accuracy_if_parsed": round(agree / parsed, 4) if parsed else None,
            "inconnu_reasons": dict(sorted(reasons.items(),
                                           key=lambda kv: -kv[1])),
            "label": "diagnostic — contrôle d'ingénierie (p), "
                     "hors benchmark (V21_PROTOCOL.md §0.3)"}
