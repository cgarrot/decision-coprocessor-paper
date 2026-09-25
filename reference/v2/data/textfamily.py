"""Famille B-V2 — étage TEXTE (E5, audit §8 version T).

Rendu narratif français varié d'un problème structuré (``bfamily.Problem``) :

- formulations MULTIPLES des arêtes, déclarations de terminaux et question
  (tirées par instance, sans corrélation avec la réponse) ;
- ordre des faits mélangé ; pas de format mécanique unique ;
- entités opaques (codes) citées telles quelles dans l'état ; options
  habillées d'un wrapper constant par instance (pas de signal de position) ;
- la réponse n'est PAS dérivable d'un appariement lexical question↔option :
  les formulations « terminal/arrivée » varient indépendamment du contenu.

Vue publique = texte seul ; vue PRIVÉE = le graphe structuré EXACT
(cible d'extraction) + traces d'états (interface exécuteur inchangée).

``parse_state`` = oracle de re-analyse : reconstruit arêtes + terminaux
depuis le texte (templates connus) — test de cohérence texte↔structure.
"""
from __future__ import annotations

import random
import re
from typing import Optional

from .bfamily import Problem

# ---------------------------------------------------------------------------
# Templates (chaque {A}/{B} = étiquette opaque ; {S} = départ ; {T} = terminal)
# ---------------------------------------------------------------------------
EDGE_TEMPLATES = [
    "{A} pointe vers {B}.",
    "Depuis {A}, on passe à {B}.",
    "{A} est relié à {B}.",
    "En partant de {A}, on arrive à {B}.",
    "Le lien va de {A} à {B}.",
    "{A} précède directement {B}.",
    "{A} envoie vers {B}.",
    "Après {A}, vient {B}.",
]
TERMINAL_TEMPLATES = [
    "{T} est un point d'arrivée.",
    "{T} marque la fin d'un chemin.",
    "On s'arrête en {T}.",
    "{T} est une extrémité.",
    "Le trajet peut s'achever en {T}.",
    "{T} termine une chaîne.",
]
QUESTION_TEMPLATES = [
    "En suivant les indications depuis {S}, où le trajet aboutit-il ?",
    "Si l'on part de {S} et qu'on suit les liens, quelle est l'arrivée ?",
    "Quel point final atteint-on en partant de {S} ?",
    "Depuis {S}, en suivant les relations une par une, où finit-on ?",
    "En partant de {S} et en avançant de lien en lien, où s'arrête-t-on ?",
]
OPTION_WRAPPERS = ["le point {}", "la balise {}", "le poste {}", "{}",
                   "le relais {}", "la borne {}", "le repère {}"]

_LABEL_RE = r"[a-z]{1,3}\d{1,3}[A-Z]{1,3}"   # codes opaques du domaine « gen »


def _compile_templates():
    edge_rx = [re.compile("^" + t.replace("{A}", f"({_LABEL_RE})")
                          .replace("{B}", f"({_LABEL_RE})") + "$")
               for t in EDGE_TEMPLATES]
    term_rx = [re.compile("^" + t.replace("{T}", f"({_LABEL_RE})") + "$")
               for t in TERMINAL_TEMPLATES]
    return edge_rx, term_rx


class _Deck:
    """Tirages SANS remise reconstitués : chaque formulation est utilisée
    avant qu'une ne se répète (variété maximale par instance)."""

    def __init__(self, items, rng):
        # MÉLANGE IMMÉDIAT (correctif A6) : sans lui, la première déclaration
        # émise prenait toujours le template[0] de la liste — et les terminaux
        # étant émis dans l'ordre des chaînes (réponse en tête), la réponse
        # portait déterministiquement « est un point d'arrivée ».
        self.items, self.rng, self.i = list(items), rng, len(items)
        self._refill()

    def _refill(self):
        self.rng.shuffle(self.items)
        self.i = 0

    def draw(self):
        if self.i >= len(self.items):
            self._refill()
        x = self.items[self.i]
        self.i += 1
        return x


def render_text(p: Problem, rng: random.Random) -> dict:
    """Rendu public : état (arêtes + terminaux, ordre mélangé, formulations
    tirées), question, options (wrapper constant par instance)."""
    edge_deck = _Deck(EDGE_TEMPLATES, rng)
    term_deck = _Deck(TERMINAL_TEMPLATES, rng)
    lines = []
    for u, v in p.edges:
        lines.append(edge_deck.draw().format(A=u, B=v))
    for t in p.terminals:
        lines.append(term_deck.draw().format(T=t))
    rng.shuffle(lines)
    wrapper = rng.choice(OPTION_WRAPPERS)
    question = rng.choice(QUESTION_TEMPLATES).format(S=p.start)
    options = [{"id": o["id"], "text": wrapper.format(o["node"])}
               for o in p.options]
    rng.shuffle(options)
    return {
        "state": "\n".join(lines),
        "question": question,
        "options": options,
    }


# ---------------------------------------------------------------------------
# Oracle de re-analyse (cohérence texte ↔ structure)
# ---------------------------------------------------------------------------
def parse_state(state_text: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Reconstruit (arêtes, terminaux) depuis l'état textuel. Chaque ligne
    doit matcher un template connu — sinon ValueError (donnée incohérente)."""
    edge_rx, term_rx = _compiled
    edges, terminals = [], []
    for line in state_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for rx in edge_rx:
            m = rx.match(line)
            if m:
                edges.append((m.group(1), m.group(2)))
                break
        else:
            for rx in term_rx:
                m = rx.match(line)
                if m:
                    terminals.append(m.group(1))
                    break
            else:
                raise ValueError(f"ligne non analysable : {line!r}")
    return edges, terminals


_compiled = _compile_templates()


def check_text_structure_coherence(view: dict, private_graph: dict) -> bool:
    """L'oracle : le texte re-analysé redonne EXACTEMENT le graphe privé,
    et la marche depuis le départ aboutit à la réponse."""
    edges, terminals = parse_state(view["state"])
    g_edges = {(u, v) for u, v in private_graph["edges"]}
    if set(edges) != g_edges or len(edges) != len(g_edges):
        return False
    if set(terminals) != set(private_graph["terminals"]):
        return False
    succ = {u: v for u, v in edges}
    start = private_graph.get("start") or private_graph["query"]["start"]
    node, seen = start, set()
    while node in succ:
        node = succ[node]
        if node in seen:
            return False
        seen.add(node)
    if node != private_graph["answer_node"]:
        return False
    # la question cite le départ ; les options portent les candidats
    if start not in view["question"]:
        return False
    labels = {o["text"].format() if False else o["text"] for o in view["options"]}
    ok = any(private_graph["answer_node"] in lab for lab in labels)
    return ok


# ---------------------------------------------------------------------------
# Problème textuel complet (vues publique/privée)
# ---------------------------------------------------------------------------
def text_problem(p: Problem, rng: random.Random) -> dict:
    view = render_text(p, rng)
    graph = {
        "nodes": list(p.nodes),
        "edges": [list(e) for e in p.edges],
        "query": {"start": p.start},
        "options": [{"id": o["id"], "node": o["node"]} for o in p.options],
        "terminals": list(p.terminals),
        "answer_node": p.answer_node,
        "answer_id": next(o["id"] for o in p.options
                          if o["node"] == p.answer_node),
        "depth": p.depth,
        "trace_nodes": list(p.trace_nodes),
        "trace_indices": p.trace_indices(),
        "trace_padded_indices_budget16": p.trace_padded_indices(),
        "trace_loss_weights_budget16": p.trace_loss_weights(),
        "is_terminal_flags": p.is_terminal_flags(),
    }
    assert check_text_structure_coherence(view, graph), p.id
    return {
        "id": p.id,
        "pool": p.pool,
        "input": view,                     # PUBLIC : texte seul
        "private": {"graph": graph,        # PRIVÉ : cible d'extraction + traces
                    "group_id": p.group_id,
                    "pair": dict(p.pair)},
    }


def paraphrase_text_problem(p: Problem, rng: random.Random) -> dict:
    """Reformulation : MÊME graphe, texte différent (même group_id)."""
    d = text_problem(p, rng)
    d["private"]["pair"] = {"role": "paraphrase", "base": p.id,
                            "expected": "answer_same"}
    return d


# ==========================================================================
# E5v2 — surface massivement diversifiée (remédiation A6)
# ==========================================================================
# Indices de surface identifiés et neutralisés :
#  I1 recouvrement question↔option  → wrappers/tokens sans lien, label
#     réponse JAMAIS dans la question, tirages indépendants de la réponse ;
#  I2 comptages de mentions         → mentions OPTIONNELLES : « Rappel : »
#     d'une arête (p≈0,30, AUTRE formulation) et 2e déclaration de terminal
#     (p≈0,25, autre formulation) — les comptages varient uniformément ;
#  I3 longueur                      → budget de nœuds en bande étroite,
#     nombre de lignes décorrélé de la réponse (rappels aléatoires) ;
#  I4 ordre/positions               → shuffle uniforme de TOUTES les
#     lignes ; position de l'arête décisive et de la déclaration réponse
#     uniformes (test chi2) ;
#  I5 « chaîne la plus longue »     → CORRECTIF STRUCTUREL : mode
#     distractor_length_mode="varied" + post-passe (≥ 1 distracteur aussi
#     long que la chaîne réponse) — P(réponse = unique plus longue)
#     mesurée ≈ 0,04 (vs 0,31 avant) ;
#  I6 wrappers prédictifs           → wrapper tiré PAR OPTION (deck), le
#     texte du terminal-réponse est indistinguable de ceux des distracteurs.

EDGE_TEMPLATES_V2 = EDGE_TEMPLATES + [
    "De {A}, le prochain point est {B}.",
    "{A} a pour suivant {B}.",
    "Si on est en {A}, la prochaine étape est {B}.",
    "Le successeur de {A} est {B}.",
    "{A} aboutit à {B}.",
    "De {A} on glisse vers {B}.",
]
TERMINAL_TEMPLATES_V2 = TERMINAL_TEMPLATES + [
    "Aucun lien ne part de {T}.",
    "{T} boucle la course, rien ne suit.",
    "En {T}, le parcours est terminé.",
    "Une fois en {T}, on ne bouge plus.",
]
QUESTION_TEMPLATES_V2 = QUESTION_TEMPLATES + [
    "Partant de {S} et en enchaînant les étapes, sur quel point finit-on ?",
    "On démarre en {S} : quel est le point d'arrivée final ?",
    "En suivant pas à pas depuis {S}, quelle issue atteint-on ?",
    "Quel est le terminus si l'on commence en {S} ?",
]
OPTION_WRAPPERS_V2 = OPTION_WRAPPERS + [
    "le marqueur {}", "la station {}", "le point {}", "le jalonnement {}",
]
RAPPEL_PREFIX = "Rappel : "


def render_text_v2(p: Problem, rng: random.Random) -> dict:
    """Rendu E5v2 : 14 formulations d'arêtes / 10 de terminaux / 9 de
    question / 10 wrappers (PAR option), rappels optionnels d'arêtes et
    secondes déclarations — chaque tirage indépendant de la réponse."""
    edge_deck = _Deck(EDGE_TEMPLATES_V2, rng)
    term_deck = _Deck(TERMINAL_TEMPLATES_V2, rng)
    lines = []
    # émission en ordre ALÉATOIRE (I4) : l'ordre de tirage des templates ne
    # suit ni l'ordre des chaînes ni la position réponse/distracteur
    emit_edges = list(p.edges)
    rng.shuffle(emit_edges)
    for u, v in emit_edges:
        t1 = edge_deck.draw()
        lines.append(t1.format(A=u, B=v))
        if rng.random() < 0.30:  # I2 : mention multiple, AUTRE formulation
            t2 = edge_deck.draw()
            while t2 == t1:
                t2 = edge_deck.draw()
            lines.append(RAPPEL_PREFIX + t2.format(A=u, B=v))
    emit_terms = list(p.terminals)
    rng.shuffle(emit_terms)
    for term in emit_terms:
        t1 = term_deck.draw()
        lines.append(t1.format(T=term))
        if rng.random() < 0.25:  # I2 : seconde déclaration
            t2 = term_deck.draw()
            while t2 == t1:
                t2 = term_deck.draw()
            lines.append(t2.format(T=term))
    rng.shuffle(lines)
    question = rng.choice(QUESTION_TEMPLATES_V2).format(S=p.start)
    wrap_deck = _Deck(OPTION_WRAPPERS_V2, rng)
    options = [{"id": o["id"], "text": wrap_deck.draw().format(o["node"])}
               for o in p.options]
    rng.shuffle(options)
    return {"state": "\n".join(lines), "question": question,
            "options": options}


def parse_state_v2(state_text: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Oracle de re-analyse E5v2 : gère les rappels (préfixe dédié) et les
    secondes déclarations — chaque arête/terminal doit apparaître 1 à 2
    fois, formulations distinctes."""
    edge_rx = [re.compile("^" + t.replace("{A}", f"({_LABEL_RE})")
                          .replace("{B}", f"({_LABEL_RE})") + "$")
               for t in EDGE_TEMPLATES_V2]
    term_rx = [re.compile("^" + t.replace("{T}", f"({_LABEL_RE})") + "$")
               for t in TERMINAL_TEMPLATES_V2]
    edges: list[tuple[str, str]] = []
    terminals: list[str] = []
    for line in state_text.split("\n"):
        raw = line.strip()
        if not raw:
            continue
        line = raw[len(RAPPEL_PREFIX):] if raw.startswith(RAPPEL_PREFIX) else raw
        for rx in edge_rx:
            m = rx.match(line)
            if m:
                edges.append((m.group(1), m.group(2)))
                break
        else:
            for rx in term_rx:
                m = rx.match(line)
                if m:
                    terminals.append(m.group(1))
                    break
            else:
                raise ValueError(f"ligne non analysable (v2) : {raw!r}")
    return edges, terminals


def text_problem_v2(p: Problem, rng: random.Random) -> dict:
    """Problème E5v2 : vue texte publique + graphe privé (cible
    d'extraction) + traces, format exécuteur inchangé."""
    view = render_text_v2(p, rng)
    d = text_problem(p, rng)          # construit private.graph (oracle v1)
    d["input"] = view                 # remplace la vue par le rendu v2
    g = d["private"]["graph"]
    edges, terms = parse_state_v2(view["state"])
    assert {tuple(e) for e in edges} == {tuple(e) for e in g["edges"]}
    # chaque arête 1..2 fois, chaque terminal 1..2 fois
    from collections import Counter as _C
    ce, ct = _C(edges), _C(terms)
    assert all(1 <= v <= 2 for v in ce.values()) and set(ce) == \
        {tuple(e) for e in g["edges"]}
    assert all(1 <= v <= 2 for v in ct.values()) and set(ct) == set(g["terminals"])
    succ = dict(edges)
    node = g["query"]["start"]
    while node in succ:
        node = succ[node]
    assert node == g["answer_node"]
    return d


def paraphrase_text_problem_v2(p: Problem, rng: random.Random) -> dict:
    d = text_problem_v2(p, rng)
    d["private"]["pair"] = {"role": "paraphrase", "base": p.id,
                            "expected": "answer_same"}
    return d
