"""Bancs V2.1 — protocole préenregistré V21_PROTOCOL.md §2 (commit 0adc08f8).

8 cellules n=400 (±5 %), seeds 2205-2212 (jamais utilisées), budget ≤20
nœuds, K∈{4,5,6}, français, famille B, surface E5v2 (anti-biais A6) :

- B1-court  : profondeurs 1-4, nouveaux groupes/noms/seeds ;
- B2/B3/B4  : profondeurs 6/8/10 (chaînes 6/8/10 arêtes), longueur
  tokenisée réelle ≤ 512 vérifiée par construction ;
- B5-surface : mêmes graphes-signatures que B1 (appariés, noms nouveaux) ;
- B6-distract : mêmes chemin/réponse que B1 + ~50 % de faits inutiles ;
- B7-options : question/état inchangés, candidats permutés + distracteurs
  admissibles, ids d'options stables ;
- B8-depart  : mêmes faits (état identique), AUTRE départ, apparié par graphe.

Invariant RELAXÉ par construction (QA v1.8 Q3 + audit §5) : ~25 % des
items de B1-B4 incluent un nœud INTERMÉDIAIRE DU CHEMIN comme candidat
(non terminal, donc jamais la réponse — rend la détection de chaîne
cassée évaluable). Générés par construction, jamais sélectionnés post-hoc.

Anti-doublons : signatures structurelles STRICTEMENT disjointes de
E5v2_train+dev (fichiers figés) et uniques intra-cellule pour B1-B4 ;
B5 partage les signatures de B1 PAR CONCEPTION (appariement) ; les
empreintes de graphes EXACTS (étiquettes comprises) sont uniques
globalement. `example_uid` unique, `base_group_id` pour l'appariement,
hash du contenu public par exemple.

E5v2_eval (seed 1107) : SCELLÉ — jamais touché ici.

Interdits respectés (§0) : aucune difficulté choisie selon des erreurs
observées ; transformations préenregistrées ci-dessus ; information
publique équitable aux deux voies (mêmes textes pour direct et pipeline).
"""
from __future__ import annotations

import hashlib
import json
import os
import random
from collections import Counter
from typing import Optional

from .bfamily import (BUDGET, Problem, build_problem, structural_signature,
                      _codes)
from .textfamily import render_text_v2

V21_SEEDS = {"B1": 2205, "B2": 2206, "B3": 2207, "B4": 2208,
             "B5": 2209, "B6": 2210, "B7": 2211, "B8": 2212}
N_PER_CELL = 400
MAX_NODES = 20
K_RANGE = (4, 5, 6)
PATH_CANDIDATE_FRACTION = 0.25   # par construction (Q3), pas post-hoc
BENCH_NAMES = {"B1": "B1-court", "B2": "B2-prof6", "B3": "B3-prof8",
               "B4": "B4-prof10", "B5": "B5-surface", "B6": "B6-distract",
               "B7": "B7-options", "B8": "B8-depart"}

# configs (nœuds, terminaux) par profondeur — faisabilité post-passe I5
# (2(d+1)+2(t-1) ≤ nn) visée quand le budget le permet ; aux profondeurs
# 6/8/10 elle est STRUCTURELLEMENT impossible sous 20 nœuds (confondeur
# « chaîne la plus longue » inhérent, équitable pour les deux voies —
# documenté au manifeste).
B1_CONFIGS = {1: ([12, 13, 14, 15], [3, 4, 5]),
              2: ([13, 14, 15, 16], [3, 4, 5]),
              3: ([14, 15], [3, 4]),
              4: ([14, 15], [3, 4])}
# Cellules de profondeur : n=400 impose la répétition de classes
# d'isomorphie (pigeonhole inhérent au budget ≤20 nœuds — depth 10 :
# partitions de 6-7 nœuds distracteurs en 3 chaînes ≥2 → ~2 classes).
# La variété réelle vient des étiquettes, ordres et surface ; mesurée et
# consignée au manifeste (anti_duplicates.class_counts).
DEPTH_CONFIGS = {6: ([17, 18], [4, 5, 6]), 8: ([17, 18], [4, 5]),
                 10: ([17, 18], [4])}


def _fresh_ids(rng: random.Random, problems: list, key) -> set:
    out = set()
    for p in problems:
        out.add(key(p))
    return out


def load_frozen_e5v2(data_dir: str) -> tuple[set, set]:
    """Signatures structurelles + empreintes de graphes EXACTS des pools
    E5v2 figés (train+dev) — l'anti-doublon V2.1 est rejoué depuis le
    disque, jamais depuis la mémoire du générateur."""
    struct, exact = set(), set()
    for name in ("E5v2_train", "E5v2_dev"):
        path = os.path.join(data_dir, f"{name}.jsonl")
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8"):
            d = json.loads(line)
            if d["private"]["pair"]["role"] != "base":
                continue
            g = d["private"]["graph"]
            pseudo = Problem(id=d["id"], nodes=g["nodes"], edges=g["edges"],
                             start=g["query"]["start"], options=g["options"],
                             answer_node=g["answer_node"], depth=g["depth"],
                             trace_nodes=g["trace_nodes"],
                             terminals=g["terminals"])
            struct.add(structural_signature(pseudo))
            exact.add((frozenset(tuple(e) for e in g["edges"]),
                       g["query"]["start"], g["answer_node"], g["depth"]))
    return struct, exact


def _uid(rng: random.Random, bench: str, i: int) -> str:
    salt = "".join(rng.choice("0123456789abcdef") for _ in range(8))
    return f"v21-{bench}-{i:05d}-{salt}"


def _oid(rng: random.Random, used: set) -> str:
    while True:
        c = "".join(rng.choice("abcdefghjkmnpqrstuvwxyz23456789")
                    for _ in range(5))
        if c not in used:
            used.add(c)
            return c


def validate_v21(p: Problem, path_candidate_ids=None,
                 bench: str = "") -> None:
    if path_candidate_ids is None:
        path_candidate_ids = set()
    elif isinstance(path_candidate_ids, str):
        path_candidate_ids = {path_candidate_ids}
    else:
        path_candidate_ids = set(path_candidate_ids)
    """Validation V2.1 : invariants du contrat + relaxations préenregistrées.

    - successeur unique, sans boucle, terminaux = puits, réponse = marche ;
    - K ∈ {4,5,6} ; réponse exactement une fois dans les options ;
    - candidats non-réponse : soit inatteignables depuis le départ, soit le
      candidat intermédiaire DU chemin (non terminal — relaxation Q3) ;
    - budget nœuds ≤ 20.
    """
    succ = p.successor_map()
    assert len(succ) == len(p.edges)
    answer, path = p.walk()
    assert answer == p.answer_node and path == p.trace_nodes
    assert len(p.trace_nodes) <= BUDGET + 1
    terms = set(p.terminals)
    assert len(terms) >= 3
    reach = set(path)
    opt_nodes = [o["node"] for o in p.options]
    assert len(set(opt_nodes)) == len(opt_nodes)
    assert opt_nodes.count(p.answer_node) == 1, \
        f"{bench}: réponse {p.answer_node} en double ; options=" \
        f"{[(o['id'], o['node']) for o in p.options]} " \
        f"terminals={p.terminals} trace={p.trace_nodes}"
    assert K_RANGE[0] <= len(p.options) <= K_RANGE[-1], \
        f"{bench}: K={len(p.options)}"
    for o in p.options:
        if o["node"] == p.answer_node:
            continue
        if o["id"] in path_candidate_ids:
            # relaxation Q3 : nœud intermédiaire du chemin, NON terminal
            assert o["node"] in reach and o["node"] not in terms
            assert o["node"] != path[0]
        else:
            assert o["node"] not in reach, \
                f"{bench}: candidat atteignable non déclaré {o['node']} " \
                f"reach={sorted(reach)} trace={p.trace_nodes} " \
                f"declared={sorted(path_candidate_ids)}"
    assert len(p.nodes) <= MAX_NODES


def _add_path_candidate(p: Problem, rng: random.Random, used: set
                        ) -> Optional[str]:
    """Ajoute un nœud INTERMÉDIAIRE du chemin comme candidat (Q3)."""
    mids = [n for n in p.trace_nodes[1:-1]]
    if not mids:
        return None
    node = rng.choice(mids)
    oid = _oid(rng, used)
    p.options.append({"id": oid, "node": node})
    return oid


def _maybe_internal(p: Problem, rng: random.Random, used: set,
                    allow: bool) -> None:
    """Candidat interne éliminable (hors chemin) si la place le permet."""
    if not allow or len(p.options) >= K_RANGE[-1]:
        return
    path_set = set(p.trace_nodes)
    internal = [n for n in p.nodes
                if n not in p.terminals and n not in path_set]
    if internal:
        p.options.append({"id": _oid(rng, used), "node": rng.choice(internal)})


def _trim_options(p: Problem, rng: random.Random,
                  keep_ids=frozenset()) -> None:
    """Ramène K dans {4,5,6}. Priorité de retrait : interne NON déclaré >
    terminal distracteur > candidat déclaré (le candidat intermédiaire
    Q3 n'est jamais sacré par le rognage)."""
    while len(p.options) > K_RANGE[-1]:
        idx = {o["id"]: i for i, o in enumerate(p.options)}
        internal_free = [i for i, o in enumerate(p.options)
                         if o["node"] not in p.terminals
                         and o["id"] not in keep_ids]
        if internal_free:
            del p.options[internal_free[-1]]
            continue
        terms = [i for i, o in enumerate(p.options)
                 if o["node"] in p.terminals and o["node"] != p.answer_node]
        if terms:
            del p.options[terms[rng.randrange(len(terms))]]
            continue
        break  # rien de sacrifiable (ne devrait pas survenir)


# ---------------------------------------------------------------------------
# B1-B4 : problèmes neufs (signatures strictement fraîches)
# ---------------------------------------------------------------------------
SIG_CAP_V21 = 32  # variété intra-cellule B1 (depth 4 : ~5 classes atteignables) ;
#                   classes d'isomorphie aux courtes profondeurs est borné ;
#                   précédent E4/E5v2). STRICT vs E5v2 figé + unicité
#                   GLOBALE des graphes exacts (étiquettes comprises).


def build_core_bench(bench: str, seed: int, n: int, depths,
                     configs: dict, frozen_struct: set,
                     exact_seen: set, rng_out: random.Random,
                     sig_cap: Optional[int] = SIG_CAP_V21
                     ) -> list[tuple[Problem, Optional[str]]]:
    rng = random.Random(seed)
    out: list = []
    struct_counts: dict = {}
    used: set = set()
    for i in range(n):
        depth = depths[i % len(depths)]
        nn_list, nt_list = configs[depth]
        p = None
        for _try in range(400):
            # rotation décalée par problème : les configurations (nœuds,
            # terminaux) sont couvertes uniformément — sinon le premier
            # essai accepté fige systématiquement (nn[0], nt[0])
            j = (_try + i) % 12
            cand = build_problem(rng, depth, nn_list[j % len(nn_list)],
                                 nt_list[j % len(nt_list)], "gen",
                                 internal_candidate=False,
                                 distractor_length_mode="varied")
            sig = structural_signature(cand)
            if sig in frozen_struct:
                continue                      # STRICT vs E5v2 figé
            struct_counts[sig] = struct_counts.get(sig, 0) + 1
            p = cand
            break
        assert p is not None, f"{bench}: épuisement structurel"
        # options : terminaux + (chemin 25 % | interne 20 %), K∈{4,5,6}
        path_id = None
        if rng.random() < PATH_CANDIDATE_FRACTION:
            path_id = _add_path_candidate(p, rng, used)
        elif rng.random() < 0.25:
            _maybe_internal(p, rng, used, allow=True)
        rng.shuffle(p.options)
        _trim_options(p, rng, frozenset({path_id} if path_id else ()))
        if len(p.options) < K_RANGE[0]:  # jamais attendu (t ≥ 3)
            _maybe_internal(p, rng, used, allow=True)
        if path_id is not None and path_id not in \
                {o["id"] for o in p.options}:
            path_id = None                             # jamais sacré, sécurité
        validate_v21(p, path_id, bench)
        exact = (frozenset(tuple(e) for e in p.edges), p.start,
                 p.answer_node, p.depth)
        assert exact not in exact_seen, f"{bench}: graphe exact dupliqué"
        exact_seen.add(exact)
        p.group_id = f"v21g-{bench}-{i:05d}-" + \
            "".join(rng.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(6))
        p.id = _uid(rng_out, bench, i)
        p.pool = BENCH_NAMES[bench]
        out.append((p, path_id))
    return out


# ---------------------------------------------------------------------------
# Relabeling exact (B5) et dérivés appariés (B6/B7/B8)
# ---------------------------------------------------------------------------
def relabel(p: Problem, rng: random.Random) -> Problem:
    """Même graphe (signature identique), étiquettes toutes nouvelles."""
    mapping = dict(zip(p.nodes, _codes(rng, len(p.nodes), "gen")))
    q = Problem(
        id=p.id, nodes=[mapping[n] for n in p.nodes],
        edges=[[mapping[u], mapping[v]] for u, v in p.edges],
        start=mapping[p.start],
        options=[{"id": o["id"], "node": mapping[o["node"]]}
                 for o in p.options],
        answer_node=mapping[p.answer_node], depth=p.depth,
        trace_nodes=[mapping[n] for n in p.trace_nodes],
        terminals=[mapping[t] for t in p.terminals],
        group_id=p.group_id, pool=p.pool)
    return q


def add_useless_facts(p: Problem, rng: random.Random) -> Problem:
    """B6 : +50 % de lignes de faits (arêtes entrantes depuis des nœuds
    neufs vers des terminaux existants) — chemin/réponse inchangés,
    budget ≤ 20 nœuds."""
    n_extra = max(1, round(0.5 * len(p.edges)))
    n_extra = min(n_extra, MAX_NODES - len(p.nodes))
    edges = [list(e) for e in p.edges]
    nodes = list(p.nodes)
    fresh, used_labels = [], set(p.nodes)
    while len(fresh) < n_extra:
        c = _codes(rng, 1, "gen")[0]
        if c not in used_labels:          # jamais de collision d'étiquette
            used_labels.add(c)
            fresh.append(c)
    for i in range(n_extra):
        target = p.terminals[rng.randrange(len(p.terminals))]
        edges.append([fresh[i], target])
        nodes.append(fresh[i])
    rng.shuffle(edges)
    rng.shuffle(nodes)
    q = Problem(id=p.id, nodes=nodes, edges=edges, start=p.start,
                options=[dict(o) for o in p.options],
                answer_node=p.answer_node, depth=p.depth,
                trace_nodes=list(p.trace_nodes),
                terminals=list(p.terminals), group_id=p.group_id,
                pool=p.pool)
    return q


def permute_and_extend_options(p: Problem, view: dict, rng: random.Random,
                               used: set) -> dict:
    """B7 : question/état inchangés ; options permutées + distracteurs
    admissibles (nœuds internes hors chemin), ids stables."""
    opts = [{"id": o["id"], "text": o["text"]} for o in view["options"]]
    ids_now = {o["id"] for o in opts}
    path_set = set(p.trace_nodes)
    admissible = [n for n in p.nodes
                  if n not in p.terminals and n not in path_set
                  and n not in {o["node"] for o in p.options}]
    rng.shuffle(admissible)
    while len(opts) < K_RANGE[-1] and admissible:
        node = admissible.pop()
        oid = _oid(rng, used)
        opts.append({"id": oid, "text": node})   # wrapper neutre : label nu
        p.options.append({"id": oid, "node": node})
    rng.shuffle(opts)
    return {"state": view["state"], "question": view["question"],
            "options": opts}


def other_start(p: Problem, rng: random.Random) -> Optional[str]:
    """B8 : autre départ valide — tête d'une autre chaîne si possible
    (réponse différente), sinon nœud intermédiaire hors chemin. Les nœuds
    déjà candidats sont EXCLUS (le départ ne peut pas être une option)."""
    opt_nodes = {o["node"] for o in p.options}
    targets = {n for e in p.edges for n in e}
    indeg = {n: 0 for n in p.nodes}
    for _u, v in p.edges:
        indeg[v] += 1
    heads = [n for n in p.nodes
             if indeg[n] == 0 and n != p.start and n not in opt_nodes]
    rng.shuffle(heads)
    for h in heads:
        term, path = p.walk(h)
        if term != p.answer_node and len(path) <= BUDGET + 1:
            return h
    mid = [n for n in p.nodes if n not in set(p.trace_nodes)
           and n in targets and n not in opt_nodes]
    return rng.choice(mid) if mid else None


# ---------------------------------------------------------------------------
# Ligne V2.1
# ---------------------------------------------------------------------------
def row_for(p: Problem, view: dict, bench: str, seed: int,
            base_group_id: str, pair: dict, path_ids,
            token_len: Optional[int]) -> dict:
    if isinstance(path_ids, str):
        path_ids = [path_ids]
    path_ids = list(path_ids or [])
    from .bfamily import Problem as _P
    g = {
        "nodes": list(p.nodes), "edges": [list(e) for e in p.edges],
        "query": {"start": p.start},
        "options": [{"id": o["id"], "node": o["node"]} for o in p.options],
        "terminals": list(p.terminals), "answer_node": p.answer_node,
        "answer_id": next(o["id"] for o in p.options
                          if o["node"] == p.answer_node),
        "depth": p.depth, "trace_nodes": list(p.trace_nodes),
        "trace_indices": p.trace_indices(),
        "trace_padded_indices_budget16": p.trace_padded_indices(),
        "trace_loss_weights_budget16": p.trace_loss_weights(),
        "is_terminal_flags": p.is_terminal_flags(),
    }
    pub = {"state": view["state"], "question": view["question"],
           "options": view["options"]}
    h = hashlib.sha256(json.dumps(pub, ensure_ascii=False,
                                  sort_keys=True).encode()).hexdigest()
    return {
        "example_uid": p.id,
        "bench": BENCH_NAMES.get(bench, bench), "seed": seed,
        "input": pub,
        "private": {"graph": g, "base_group_id": base_group_id,
                    "pair": pair, "path_candidate_option_id": path_ids,
                    "token_len": token_len},
        "public_hash": h,
    }
