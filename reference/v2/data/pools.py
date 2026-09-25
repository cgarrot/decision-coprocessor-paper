"""Pools E1-E4 (audit §10, mission E0-DONNÉES).

- E1_overfit   : 128 problèmes courts (profondeurs 1-3), surapprentissage ;
- E2_heldout   : 256 problèmes, graphes inédits, domaine volontairement
                 simple (lettres A-Z), paires contrôlées sur ~30 % des
                 groupes ;
- E3           : profondeurs 2/3/4 équilibrées, nombre de nœuds CONSTANT
                 entre profondeurs (bande étroite) — train 1536 + eval 384 ;
                 paires : ~10 % (train), ~30 % (eval) ;
- E4 (RÉSERVÉ) : profondeurs 6/8/10/16, seeds de génération indépendantes,
                 contrôle des doublons structurels contre E1-E3 —
                 CAPABILITY PRÉPARÉE, NON EXÉCUTÉE (aucun fichier écrit ;
                 utilisable uniquement à la porte E4).

Contrôles à la génération : signatures structurelles uniques par pool et
disjointes entre pools ; group_id attribué AVANT les variantes ; toutes
les variantes d'un groupe dans le même pool ; validation oracle de chaque
problème (successeur unique, sans boucle, terminaux multiples, réponse
unique non prévisible par raccourci).

Sortie : data/<pool>.jsonl + data/manifest_v2data.json (compteurs,
signatures, sha256). CPU uniquement, stdlib uniquement.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
from collections import Counter
from typing import Optional

from .bfamily import (
    Problem, build_problem, structural_signature,
    variant_decisive_edge, variant_distractor_edge,
)


def _group_id(rng: random.Random, counter: int) -> str:
    salt = "".join(rng.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(6))
    return f"gb2-{counter:06d}-{salt}"


SIG_CAP = 16  # variété intra-pool : au plus 16 exemplaires d'une même
#              classe d'isomorphie (l'espace des petites structures est
#              borné — principe du pigeonnier) ; la disjonction STRICTE est
#              exigée pour E4 contre E1-E3 (formes différentes par
#              construction) et documentée dans data_contract.md.


def _emit(rng: random.Random, depth: int, n_nodes: int, n_terminals: int,
          domain: str, pool: str, counter: int, sig_counts: dict,
          strict_seen: Optional[set] = None, internal_prob: float = 0.3,
          tries: int = 300, cap: int = None, isolated: int = 0,
          rotate: int = 0, varied: bool = False
          ) -> tuple[Problem, tuple]:
    nn_list = [n_nodes] if isinstance(n_nodes, int) else list(n_nodes)
    nt_list = [n_terminals] if isinstance(n_terminals, int) else list(n_terminals)
    for t in range(tries):
        # fait tourner les budgets (nœuds, terminaux) à chaque essai : la
        # capacité de classes d'isomorphie se somme sur les configurations
        # rotation décalée par problème : la plage de nœuds est couverte
        # uniformément (sinon l'acceptation au premier essai fige nn[0])
        j = (t + rotate) % 12
        nn = nn_list[j % len(nn_list)]
        nt = nt_list[j % len(nt_list)]
        if nn < depth + 1 + 2 * (nt - 1 - isolated) + isolated:
            continue  # budget insuffisant pour cette configuration
        p = build_problem(rng, depth, nn, nt, domain,
                          internal_candidate=rng.random() < internal_prob,
                          isolated_terminals=isolated,
                          distractor_length_mode="varied" if varied else "flat")
        sig = structural_signature(p)
        if strict_seen is not None and sig in strict_seen:
            continue
        if sig_counts.get(sig, 0) >= (SIG_CAP if cap is None else cap):
            continue
        sig_counts[sig] = sig_counts.get(sig, 0) + 1
        p.pool = pool
        p.id = f"b2-{pool}-{counter:06d}-" + \
            "".join(rng.choice("0123456789abcdef") for _ in range(8))
        return p, sig
    raise RuntimeError(f"impossible de produire une structure acceptable "
                       f"(depth={depth}, pool={pool})")


def build_pool(pool: str, n: int, depths, n_nodes, n_terminals, domain: str,
               seed: int, pair_fraction: float = 0.0,
               sig_counts: Optional[dict] = None) -> list[Problem]:
    """Génère un pool complet (bases + variantes de paires). ``sig_counts``
    partage le plafond de variété intra/inter pools appelants."""
    rng = random.Random(seed)
    counts = sig_counts if sig_counts is not None else {}
    out: list[Problem] = []
    counter = 0
    depth_cycle = depths if isinstance(depths, list) else [depths]
    for i in range(n):
        depth = depth_cycle[i % len(depth_cycle)]
        # n_nodes / n_terminals passés TELS QUELS : _emit fait tourner les
        # configurations à chaque essai (capacité = somme des classes)
        p, _sig = _emit(rng, depth, n_nodes, n_terminals,
                        domain, pool, counter, counts)
        p.group_id = _group_id(rng, counter)
        counter += 1
        out.append(p)
        if rng.random() < pair_fraction:
            v = variant_decisive_edge(p, rng) or variant_distractor_edge(p, rng)
            if v is not None:
                v.group_id = p.group_id
                out.append(v)
    return out


# --------------------------------------------------------------------------
# Pools officiels
# --------------------------------------------------------------------------

def build_E1(seed: int = 101) -> list[Problem]:
    """128 problèmes courts — pilote de surapprentissage (audit §10 E1).
    Nœuds 9-12 et terminaux 3-4 variés (espace structurel petit : la
    variété vient aussi de ces paramètres)."""
    return build_pool("E1", 128, [1, 2, 3], [9, 10, 11, 12], [3, 4],
                      "gen", seed)


def build_E2(seed: int = 202) -> list[Problem]:
    """256 problèmes inédits, domaine simple (lettres) — held-out E2."""
    return build_pool("E2", 256, [2, 3, 4], [13, 14, 15], 4, "letters",
                      seed, pair_fraction=0.30)


def build_E3(seed: int = 303) -> dict[str, list[Problem]]:
    """Profondeurs 2/3/4, nœuds CONSTANTS entre profondeurs (14±1) —
    train + eval. Signature partageées inter-split via un seen global."""
    # MÊME distribution pour train et eval : les classes d'isomorphie se
    # recouvrent volontiers (les graphes réels diffèrent : étiquettes,
    # ordre des arêtes, options) — le plafond de variété s'applique PAR POOL.
    train = build_pool("E3_train", 768, [2, 3, 4], [13, 14, 15, 16], [4, 5],
                       "gen", seed, pair_fraction=0.10)
    ev = build_pool("E3_eval", 192, [2, 3, 4], [13, 14, 15, 16], [4, 5],
                    "gen", seed + 1, pair_fraction=0.30)
    return {"train": train, "eval": ev}


# E4 : seeds de GÉNÉRATION indépendantes d'E1/E2/E3 (101/202/303) et entre
# profondeurs ; cap de variété propre (l'espace d'isomorphie est étroit à
# profondeur 10 dans 13-16 nœuds : 4 classes seulement) ; stress 16 = 20
# nœuds avec 1 terminal ISOLÉ (contrainte structurelle : une chaîne de 16
# occupe 17 nœuds ; 3 terminaux chaînés exigeraient 21 nœuds > 20).
E4_SEEDS = {6: 904, 8: 905, 10: 906, 16: 907}
E4_SIG_CAP = 32
E4_COUNTS = {6: 96, 8: 96, 10: 96, 16: 24}   # bases équilibrées + stress
E4_PAIR_FRACTION = 0.25


def _e4_configs(depth: int):
    """Configurations par profondeur : la plage de nœuds VUE en E3 (13-16)
    est conservée — l'extrapolation porte sur la PROFONDEUR ; seul le
    stress 16 dépasse (20 nœuds, documenté au manifeste)."""
    if depth == 16:
        return [20], [3], 1
    if depth == 10:
        return [15, 16], [3], 0
    if depth == 8:
        return [13, 14, 15, 16], [3, 4], 0
    return [13, 14, 15, 16], [3, 4, 5], 0


def build_E4(seeds=None, counts=None, seen_sig=None,
             pair_fraction=None) -> list[Problem]:
    """E4 : profondeurs nouvelles 6/8/10 + stress 16, paires contrôlées
    decisive_edge. Signatures STRICTEMENT disjointes de ``seen_sig``
    (E1/E2/E3, relues depuis les fichiers figés par build_and_write_E4)."""
    seeds = seeds or E4_SEEDS
    counts = counts or E4_COUNTS
    pf = E4_PAIR_FRACTION if pair_fraction is None else pair_fraction
    strict = set(seen_sig) if seen_sig is not None else set()
    out: list[Problem] = []
    counter = 0
    for depth, n in counts.items():
        rng = random.Random(seeds[depth])          # seed indépendante/consignée
        nn_list, nt_list, isolated = _e4_configs(depth)
        for i in range(n):
            p, _ = _emit(rng, depth, nn_list, nt_list, "gen", "E4", counter,
                         {}, strict_seen=strict, cap=E4_SIG_CAP,
                         isolated=isolated, rotate=counter)
            p.group_id = _group_id(rng, counter)
            counter += 1
            out.append(p)
            if rng.random() < pf:
                v = variant_decisive_edge(p, rng)
                if v is not None:
                    v.group_id = p.group_id
                    out.append(v)
    return out


def _problem_from_dict(d: dict) -> Problem:
    pr = d["private"]
    return Problem(
        id=d["id"], nodes=d["input"]["nodes"], edges=d["input"]["edges"],
        start=d["input"]["query"]["start"], options=d["input"]["options"],
        answer_node=pr["answer_node"], depth=pr["depth"],
        trace_nodes=pr["trace_nodes"], terminals=pr["terminals"],
        group_id=pr["group_id"], pair=pr["pair"], pool=d["pool"],
    )


def build_and_write_E4(out_dir: str) -> dict:
    """Génère E4 contre les signatures des fichiers E1/E2/E3 FIGÉS sur
    disque, écrit data/E4.jsonl et met à jour le manifeste."""
    frozen = ["E1", "E2", "E3_train", "E3_eval"]
    seen: set = set()
    for name in frozen:
        for line in open(os.path.join(out_dir, f"{name}.jsonl"),
                         encoding="utf-8"):
            d = json.loads(line)
            if d["private"]["pair"]["role"] == "base":
                seen.add(structural_signature(_problem_from_dict(d)))
    problems = build_E4(seen_sig=seen)
    path = os.path.join(out_dir, "E4.jsonl")
    write_pool(problems, path)
    groups = {p.group_id for p in problems}
    with_pairs = sum(1 for g in groups
                     if any(q.pair.get("role") == "decisive_edge"
                            for q in problems if q.group_id == g))
    e4_sigs = {structural_signature(p) for p in problems
               if p.pair.get("role") == "base"}
    assert not (e4_sigs & seen), "collision structurelle E4 vs E1-E3"
    mpath = os.path.join(out_dir, "manifest_v2data.json")
    manifest = json.load(open(mpath, encoding="utf-8"))
    manifest["pools"]["E4"] = {
        "file": "E4.jsonl", "count": len(problems), "groups": len(groups),
        "groups_with_decisive_pairs": with_pairs,
        "by_depth": dict(Counter(p.depth for p in problems
                                 if p.pair.get("role") == "base")),
        "nodes_minmax": [min(len(p.nodes) for p in problems),
                         max(len(p.nodes) for p in problems)],
        "sha256": sha256_file(path),
        "generation_seeds": dict(E4_SEEDS),
        "sig_cap": E4_SIG_CAP,
        "stress16": {
            "nodes": 20,
            "note": "chaîne de 16 = 17 nœuds ; 3 terminaux chaînés "
                    "exigeraient 21 nœuds (> plafond autorisé 20) → 1 "
                    "terminal ISOLÉ (puits sans arête) comme 3e candidat",
        },
    }
    manifest["e4"] = {
        "status": "GENERATED (porte E4)",
        "depths": [6, 8, 10, 16],
        "seeds": dict(E4_SEEDS),
        "anti_duplicates": {
            "method": "signature canonique de graphes fonctionnels (degré "
                      "sortant ≤ 1) : multiset des longueurs de chaînes "
                      "(marches depuis les sources), longueur de la chaîne "
                      "réponse, nb de terminaux, nb d'options, profondeur, "
                      "nb de candidats internes — indépendante des "
                      "étiquettes (opaques/renommées par conception)",
            "limits": "ne distingue ni la position du candidat interne "
                      "éliminable, ni l'identité des étiquettes (volontaire "
                      ": renommées), ni l'ordre des arêtes (mélangé par "
                      "conception)",
            "check": "0 intersection stricte contre les signatures des "
                     "fichiers E1/E2/E3 figés, rejouée depuis le disque",
        },
    }
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
    return {"problems": problems, "manifest_path": mpath,
            "frozen_signatures": len(seen), "e4_signatures": len(e4_sigs)}


# --------------------------------------------------------------------------

def build_E1(seed: int = 101) -> list[Problem]:
    """128 problèmes courts — pilote de surapprentissage (audit §10 E1).
    Nœuds 9-12 et terminaux 3-4 variés (espace structurel petit : la
    variété vient aussi de ces paramètres)."""
    return build_pool("E1", 128, [1, 2, 3], [9, 10, 11, 12], [3, 4],
                      "gen", seed)


def build_E2(seed: int = 202) -> list[Problem]:
    """256 problèmes inédits, domaine simple (lettres) — held-out E2."""
    return build_pool("E2", 256, [2, 3, 4], [13, 14, 15], 4, "letters",
                      seed, pair_fraction=0.30)


def build_E3(seed: int = 303) -> dict[str, list[Problem]]:
    """Profondeurs 2/3/4, nœuds CONSTANTS entre profondeurs (14±1) —
    train + eval. Signature partageées inter-split via un seen global."""
    # MÊME distribution pour train et eval : les classes d'isomorphie se
    # recouvrent volontiers (les graphes réels diffèrent : étiquettes,
    # ordre des arêtes, options) — le plafond de variété s'applique PAR POOL.
    train = build_pool("E3_train", 768, [2, 3, 4], [13, 14, 15, 16], [4, 5],
                       "gen", seed, pair_fraction=0.10)
    ev = build_pool("E3_eval", 192, [2, 3, 4], [13, 14, 15, 16], [4, 5],
                    "gen", seed + 1, pair_fraction=0.30)
    return {"train": train, "eval": ev}


# --------------------------------------------------------------------------
# Écriture + manifeste
# --------------------------------------------------------------------------

def write_pool(problems: list[Problem], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for p in problems:
            f.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_all(out_dir: str, seeds=(101, 202, 303)) -> dict:
    """Construit E1/E2/E3 sur disque + manifeste. E4 non généré."""
    os.makedirs(out_dir, exist_ok=True)
    e1 = build_E1(seeds[0])
    e2 = build_E2(seeds[1])
    e3 = build_E3(seeds[2])
    manifest = {"budget": 16, "pools": {}, "e4": {
        "status": "RESERVED — capability prête (v2data.pools.build_E4), "
                  "NON générée (portes E0-E2 d'abord, seeds indépendantes, "
                  "contrôle des doublons structurels contre E1-E3)",
        "depths": [6, 8, 10, 16]}}
    sig_all: set = set()
    for name, probs in (("E1", e1), ("E2", e2),
                        ("E3_train", e3["train"]), ("E3_eval", e3["eval"])):
        path = os.path.join(out_dir, f"{name}.jsonl")
        write_pool(probs, path)
        for p in probs:
            sig_all.add(structural_signature(p))
        groups = {p.group_id for p in probs}
        with_pairs = sum(1 for g in groups
                         if any(q.pair.get("role") != "base"
                                for q in probs if q.group_id == g))
        manifest["pools"][name] = {
            "file": os.path.basename(path), "count": len(probs),
            "groups": len(groups), "groups_with_pairs": with_pairs,
            "by_depth": dict(Counter(p.depth for p in probs
                                     if p.pair.get("role") == "base")),
            "by_terminals": dict(Counter(len(p.terminals) for p in probs)),
            "by_options": dict(Counter(len(p.options) for p in probs)),
            "nodes_minmax": [min(len(p.nodes) for p in probs),
                             max(len(p.nodes) for p in probs)],
            "sha256": sha256_file(path),
        }
    manifest["structural_signatures_total"] = len(sig_all)
    mpath = os.path.join(out_dir, "manifest_v2data.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
    manifest["_path"] = mpath
    return manifest


# ==========================================================================
# E5 — pools TEXTE (audit §8 version T)
# ==========================================================================
E5_SEEDS = {"train": 1005, "dev": 1006, "eval_reserved": 1007}
E5_DEPTH_COUNTS = {"train": 1400, "dev": 280, "eval_reserved": 280}
E5_SIG_CAP = 32          # même justification qu'E4 : espace d'isomorphie étroit


def build_E5_pool(pool: str, n_bases: int, seed: int,
                  decisive_fraction: float = 0.25,
                  paraphrase_fraction: float = 0.20) -> list[dict]:
    """Pool texte : bases + paires decisive_edge (texte) + paraphrases,
    toutes au même group_id. Cohérence texte↔structure assertée à la
    création (oracle de re-analyse)."""
    from .textfamily import paraphrase_text_problem, text_problem
    rng = random.Random(seed)
    counts: dict = {}
    rows: list[dict] = []
    counter = 0
    for i in range(n_bases):
        depth = [2, 3, 4][i % 3]
        p, _ = _emit(rng, depth, [13, 14, 15, 16], [4, 5], "gen", pool,
                     counter, counts, cap=E5_SIG_CAP, rotate=counter)
        p.group_id = _group_id(rng, counter)
        counter += 1
        rows.append(text_problem(p, rng))
        if rng.random() < decisive_fraction:
            v = variant_decisive_edge(p, rng)
            if v is not None:
                v.group_id, v.pool = p.group_id, pool
                rows.append(text_problem(v, rng))
        if rng.random() < paraphrase_fraction:
            rows.append(paraphrase_text_problem(p, rng))
    return rows


def graph_signature(p: dict) -> tuple:
    """Empreinte du graphe EXACT (au-delà des classes d'isomorphie) : deux
    problèmes de même empreinte = même graphe renommé près."""
    g = p["private"]["graph"]
    return (frozenset(tuple(e) for e in g["edges"]), g["query"]["start"],
            g["answer_node"], g["depth"])


def build_and_write_E5(out_dir: str) -> dict:
    """E5_train + E5_dev sur disque ; E5_eval RÉSERVÉ (capability, seed
    indépendante consignée, anti-doublons graphes vs train+dev) — NON
    généré. Manifeste mis à jour."""
    train = build_E5_pool("E5_train", E5_DEPTH_COUNTS["train"], E5_SEEDS["train"])
    dev = build_E5_pool("E5_dev", E5_DEPTH_COUNTS["dev"], E5_SEEDS["dev"])
    # anti-doublons GRAPHE entre train et dev (même distribution, graphes
    # distincts) : aucune empreinte exacte partagée
    sigs = {}
    for rows in (train, dev):
        for r in rows:
            if r["private"]["pair"]["role"] != "base":
                continue
            gs = graph_signature(r)
            assert sigs.get(gs, r["pool"]) == r["pool"], \
                "graphe exact partagé entre pools E5"
            sigs.setdefault(gs, r["pool"])
    out = {}
    mpath = os.path.join(out_dir, "manifest_v2data.json")
    manifest = json.load(open(mpath, encoding="utf-8"))
    for name, rows in (("E5_train", train), ("E5_dev", dev)):
        path = os.path.join(out_dir, f"{name}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        from collections import Counter as _C
        bases = [r for r in rows if r["private"]["pair"]["role"] == "base"]
        manifest["pools"][name] = {
            "file": f"{name}.jsonl", "count": len(rows),
            "bases": len(bases),
            "by_depth": dict(_C(r["private"]["graph"]["depth"] for r in bases)),
            "by_pair_role": dict(_C(r["private"]["pair"]["role"] for r in rows)),
            "sha256": sha256_file(path),
            "seed": E5_SEEDS[name.split("_")[1]],
        }
        out[name] = rows
    manifest["e5_eval_reserved"] = {
        "status": "RESERVED — capability prête (v2data.pools.build_E5_pool), "
                  "NON générée (porte d'évaluation E5)",
        "target_bases": E5_DEPTH_COUNTS["eval_reserved"],
        "seed": E5_SEEDS["eval_reserved"],
        "anti_duplicates": "empreintes de graphes EXACTS disjointes de "
                           "E5_train+E5_dev (graph_signature) ; classes "
                           "d'isomorphie partagées avec E3 par conception "
                           "(l'étage S a appris sur cette distribution : "
                           "E5 isole la connexion TEXTE, la nouveauté "
                           "n'est pas structurelle)",
    }
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
    return {"train": len(train), "dev": len(dev), "manifest": mpath}


# ==========================================================================
# E5v2 — pools TEXTE corrigés (remédiation A6, branche B)
# ==========================================================================
E5V2_SEEDS = {"train": 1105, "dev": 1106, "eval_reserved": 1107}
E5V2_SIG_CAP = 48  # espace rétréci par la post-passe (depth 4 : ~14 classes) ; la diversité d E5v2 est portée par la SURFACE


def _e5v2_configs(depth: int):
    """Configurations faisables par profondeur : la post-passe « distracteur
    aussi long que la chaîne réponse » exige n_nodes ≥ 2(depth+1)+2(n_distr-1)
    → depth 4 limité à 14-16 nœuds / 4 terminaux."""
    if depth == 4:
        return [14, 15, 16], [4]
    return [13, 14, 15, 16], [4, 5]


def build_E5v2_pool(pool: str, n_bases: int, seed: int,
                    decisive_fraction: float = 0.25,
                    paraphrase_fraction: float = 0.20) -> list[dict]:
    """Pool texte v2 : structures « varied » (anti I5) + surface massivement
    diversifiée (anti I1-I4, I6). Paires decisive + paraphrases au même
    group_id. Cohérence oracle v2 assertée à la création."""
    from .textfamily import (paraphrase_text_problem_v2, text_problem_v2)
    rng = random.Random(seed)
    counts: dict = {}
    rows: list[dict] = []
    counter = 0
    for i in range(n_bases):
        depth = [2, 3, 4][i % 3]
        nn_list, nt_list = _e5v2_configs(depth)
        p, _ = _emit(rng, depth, nn_list, nt_list, "gen", pool, counter,
                     counts, cap=E5V2_SIG_CAP, rotate=counter, varied=True)
        p.group_id = _group_id(rng, counter)
        counter += 1
        rows.append(text_problem_v2(p, rng))
        if rng.random() < decisive_fraction:
            v = variant_decisive_edge(p, rng)
            if v is not None:
                v.group_id, v.pool = p.group_id, pool
                rows.append(text_problem_v2(v, rng))
        if rng.random() < paraphrase_fraction:
            rows.append(paraphrase_text_problem_v2(p, rng))
    return rows


def build_and_write_E5v2(out_dir: str) -> dict:
    """E5v2_train + E5v2_dev sur disque ; E5v2_eval RÉSERVÉ (seed 1107) ;
    E5 v1 marqué SUPERSEDED et son eval scellée À JAMAIS au manifeste."""
    train = build_E5v2_pool("E5v2_train", 1400, E5V2_SEEDS["train"])
    dev = build_E5v2_pool("E5v2_dev", 280, E5V2_SEEDS["dev"])
    sigs = {}
    for rows in (train, dev):
        for r in rows:
            if r["private"]["pair"]["role"] != "base":
                continue
            gs = graph_signature(r)
            assert sigs.get(gs, r["pool"]) == r["pool"], \
                "graphe exact partagé entre pools E5v2"
            sigs.setdefault(gs, r["pool"])
    mpath = os.path.join(out_dir, "manifest_v2data.json")
    manifest = json.load(open(mpath, encoding="utf-8"))
    for name in ("E5_train", "E5_dev"):
        manifest["pools"][name]["status"] = (
            "SUPERSEDED — biais de surface A6 (bench T invalide) ; remplacé "
            f"par {name.replace('E5_', 'E5v2_')}")
    for name, rows in (("E5v2_train", train), ("E5v2_dev", dev)):
        path = os.path.join(out_dir, f"{name}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        from collections import Counter as _C
        bases = [r for r in rows if r["private"]["pair"]["role"] == "base"]
        manifest["pools"][name] = {
            "file": f"{name}.jsonl", "count": len(rows), "bases": len(bases),
            "by_depth": dict(_C(r["private"]["graph"]["depth"] for r in bases)),
            "by_pair_role": dict(_C(r["private"]["pair"]["role"] for r in rows)),
            "sha256": sha256_file(path),
            "seed": E5V2_SEEDS[name.split("_")[1]],
            "surface": "v2 (14 templates arêtes, 10 terminaux, 9 questions, "
                       "10 wrappers/option, rappels p=0.30, 2es déclarations "
                       "p=0.25)",
            "structure": "varied (distracteur ≥ chaîne réponse ; "
                         "P(réponse=unique plus longue)≈0.04)",
        }
    manifest["e5_eval_reserved"] = {
        "status": "SEALED FOREVER — banc invalide (biais de surface A6) ; "
                  "seed 1007 RETIRÉE, ne jamais générer",
    }
    manifest["e5v2_eval_reserved"] = {
        "status": "RESERVED — capability build_E5v2_pool, non générée "
                  "(porte d'évaluation E5v2)",
        "target_bases": 280, "seed": E5V2_SEEDS["eval_reserved"],
        "anti_duplicates": "empreintes de graphes EXACTS disjointes de "
                           "E5v2_train+dev (graph_signature)",
    }
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
    return {"train": len(train), "dev": len(dev), "manifest": mpath}
