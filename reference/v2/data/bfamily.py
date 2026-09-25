"""Famille B simplifiée V2 — générateur, oracle, traces d'états exactes.

Audit §7.2 / amendement §3.5 (DECISION-V2.md) :

- plusieurs chaînes orientées ; successeur UNIQUE par nœud ; AUCUNE boucle ;
- PLUSIEURS terminaux (anti-raccourci : sans cela la réponse est trouvable
  sans suivre le départ) ; candidats = terminaux (vrai + distracteurs) et
  au plus un nœud interne éliminable (minoritaire) ;
- entités opaques RENOMMÉES par problème (aucune corrélation entre l'ordre
  des identifiants et la position dans la chaîne — testé) ;
- ordre des faits mélangé ; nombre de nœuds comparable entre profondeurs ;
- traces exactes du pointeur (départ → … → terminal), terminal ABSORBANT,
  cibles répétées jusqu'au budget 16 ; normalisation de perte fournie pour
  ne pas surpondérer les répétitions du terminal ;
- paires contrôlées : arête décisive modifiée ⇒ réponse change ; arête
  distractrice modifiée ⇒ réponse stable ; group_id AVANT variantes.

Vues :
- ``input`` (PUBLIQUE) : nœuds, arêtes, requête, candidats — SANS réponse
  ni trajectoire ni profondeur ;
- ``text`` (PUBLIQUE, optionnel, étage T ultérieur) : rendu français ;
- ``private`` : réponse, trace, indices, drapeaux terminaux, métadonnées
  de paire. JAMAIS en entrée d'inférence (test anti-fuite dédié).

Python stdlib uniquement. CPU uniquement.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

BUDGET = 16  # plafond commun de transitions (audit §7.5, amendement §3.4)

# domaines d'étiquettes (renouvelées par problème)
_ALPHABET = "abcdefghjkmnpqrstuvwxyz"


def _codes(rng: random.Random, n: int, domain: str) -> list[str]:
    """Étiquettes opaques, tirées SANS remise, ordre aléatoire (aucune
    corrélation ordre d'id ↔ position dans la chaîne)."""
    if domain == "letters":
        pool = [chr(65 + i) for i in range(26)]
        rng.shuffle(pool)
        out, pool = pool[:n], pool[n:]
        while len(out) < n:
            out.append(out[rng.randrange(len(out))] + "'")
        return out
    out, used = [], set()
    while len(out) < n:
        c = (rng.choice(_ALPHABET) + str(rng.randint(0, 99))
             + rng.choice(_ALPHABET.upper()))
        if c not in used:
            used.add(c)
            out.append(c)
    return out


@dataclass
class Problem:
    """Un problème B-V2 + ses vues publiques/privées."""
    id: str
    nodes: list[str]                       # étiquettes opaques (ordre aléatoire)
    edges: list[list[str]]                 # ordre mélangé
    start: str
    options: list[dict]                    # [{"id": oid, "node": label}]
    # ---- privé ----
    answer_node: str
    depth: int
    trace_nodes: list[str]                 # départ → … → terminal (exact)
    terminals: list[str]
    group_id: str = ""
    pair: dict = field(default_factory=lambda: {"role": "base"})
    pool: str = ""

    # ---------- oracle ----------
    def successor_map(self) -> dict[str, str]:
        succ: dict[str, str] = {}
        for u, v in self.edges:
            if u in succ:
                raise ValueError(f"{self.id}: successeur multiple pour {u}")
            succ[u] = v
        return succ

    def walk(self, start: Optional[str] = None) -> tuple[str, list[str]]:
        """Oracle : suit les arêtes jusqu'à un terminal. Vérifie l'absence
        de boucle (cut ≤ n_nœuds)."""
        succ = self.successor_map()
        node = start if start is not None else self.start
        path = [node]
        seen = {node}
        while node in succ:
            node = succ[node]
            if node in seen:
                raise ValueError(f"{self.id}: boucle détectée")
            seen.add(node)
            path.append(node)
            if len(path) > len(self.nodes) + 1:
                raise ValueError(f"{self.id}: marche divergente")
        return node, path

    def validate(self) -> None:
        succ = self.successor_map()
        assert len(self.edges) == len(succ), f"{self.id}: arêtes en double"
        # terminaux = nœuds sans successeur
        terms = [n for n in self.nodes if n not in succ]
        assert set(terms) == set(self.terminals), f"{self.id}: terminaux incohérents"
        # plusieurs terminaux OBLIGATOIRES (anti-raccourci audit §7.2)
        assert len(self.terminals) >= 3, f"{self.id}: < 3 terminaux"
        answer, path = self.walk()
        assert answer == self.answer_node, f"{self.id}: réponse ≠ marche"
        assert path == self.trace_nodes, f"{self.id}: trace ≠ marche"
        assert self.depth == len(path) - 1, f"{self.id}: profondeur ≠ trace"
        assert len(self.trace_nodes) <= BUDGET + 1, f"{self.id}: trace > budget"
        # candidats : uniques, réponse présente exactement une fois,
        # terminaux distracteurs non atteignables depuis le départ
        opt_nodes = [o["node"] for o in self.options]
        assert len(set(opt_nodes)) == len(opt_nodes), f"{self.id}: candidats dupliqués"
        assert opt_nodes.count(self.answer_node) == 1
        reach = set(self.trace_nodes)
        for o in self.options:
            if o["node"] != self.answer_node:
                assert o["node"] not in reach, \
                    f"{self.id}: candidat {o['node']} atteignable depuis le départ"
        # minorité de nœuds internes éliminables
        n_internal = sum(1 for o in opt_nodes if o not in self.terminals)
        assert n_internal <= 1 and n_internal < len(opt_nodes) / 2, \
            f"{self.id}: internes non minoritaires"
        assert 3 <= len(self.options) <= 8

    # ---------- traces ----------
    def trace_indices(self) -> list[int]:
        idx = {n: i for i, n in enumerate(self.nodes)}
        return [idx[n] for n in self.trace_nodes]

    def trace_padded_indices(self, budget: int = BUDGET) -> list[int]:
        """États cibles sur le budget complet : trace exacte puis terminal
        ABSORBANT répété (audit §7.3)."""
        idx = {n: i for i, n in enumerate(self.nodes)}
        tr = [idx[n] for n in self.trace_nodes]
        return tr + [tr[-1]] * (budget + 1 - len(tr))

    def is_terminal_flags(self) -> list[int]:
        terms = set(self.terminals)
        return [1 if n in terms else 0 for n in self.nodes]

    def trace_loss_weights(self, budget: int = BUDGET) -> list[float]:
        """Poids de la perte d'état par créneau (somme = 1).

        Normalisation anti-surpondération (audit §7.4) : chaque état UNIQUE
        (t = 0..depth) reçoit le même poids w = 1/(depth+2) ; la masse du
        terminal absorbant (w) est RÉPARTIE uniformément sur les créneaux
        de répétition (t > depth) — les longues suites de répétitions ne
        pèsent pas plus qu'un seul état supplémentaire, et les problèmes
        courts ne sont pas surpondérés par leurs répétitions nombreuses.
        """
        w = 1.0 / (self.depth + 2)
        n_rep = budget - self.depth          # créneaux t = depth+1 .. budget
        weights = [w] * (self.depth + 1)
        weights += [w / n_rep if n_rep > 0 else 0.0] * n_rep
        return weights[: budget + 1]

    # ---------- vues ----------
    def public_input(self) -> dict:
        """Entrée S (PUBLIQUE) : nœuds/arêtes/requête — sans réponse ni
        trajectoire (data_contract.md)."""
        return {
            "id": self.id,
            "nodes": list(self.nodes),
            "edges": [list(e) for e in self.edges],
            "query": {"start": self.start},
            "options": [{"id": o["id"], "node": o["node"]} for o in self.options],
        }

    def public_text(self) -> str:
        """Rendu texte français (étage T ultérieur). Aucune marque de la
        réponse : les mentions d'un terminal (arêtes entrantes + déclaration)
        ne le distinguent pas des autres (contrôlé par test : le terminal
        réponse n'est jamais le plus mentionné avec écart)."""
        lines = [f"Le point {u} mène au point {v}." for u, v in self.edges]
        lines += [f"Le point {t} est un terminal." for t in self.terminals]
        random.Random(self.id).shuffle(lines)  # déterministe, mélangé
        lines.append(f"Départ : le point {self.start}.")
        return "\n".join(lines)

    def private_view(self) -> dict:
        return {
            "answer_node": self.answer_node,
            "answer_id": next(o["id"] for o in self.options
                              if o["node"] == self.answer_node),
            "depth": self.depth,
            "trace_nodes": list(self.trace_nodes),
            "trace_indices": self.trace_indices(),
            "trace_padded_indices_budget16": self.trace_padded_indices(),
            "trace_loss_weights_budget16": self.trace_loss_weights(),
            "is_terminal_flags": self.is_terminal_flags(),
            "terminals": list(self.terminals),
            "group_id": self.group_id,
            "pair": dict(self.pair),
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pool": self.pool,
            "input": self.public_input(),
            "text": self.public_text(),
            "private": self.private_view(),
        }


# --------------------------------------------------------------------------
# Génération
# --------------------------------------------------------------------------

def build_problem(rng: random.Random, depth: int, n_nodes: int,
                  n_terminals: int, domain: str = "gen",
                  internal_candidate: bool = False,
                  pid: str = "", group_id: str = "",
                  isolated_terminals: int = 0,
                  distractor_length_mode: str = "flat") -> Problem:
    """Construit un problème : chaîne principale (profondeur ``depth``) +
    chaînes distractrices pour atteindre ``n_nodes`` et ``n_terminals``.

    Le nombre TOTAL de nœuds est contrôlé (comparable entre profondeurs) :
    profondeur plus grande ⇒ moins de nœuds distracteurs.
    ``isolated_terminals`` : terminaux sans aucune arête (puits isolés) —
    utilisés uniquement pour le stress profondeur 16, où la contrainte
    « ≥ 3 terminaux » est irréalisable avec des chaînes seules dans le
    budget de nœuds autorisé (17 nœuds de chaîne + 2×2 distracteurs = 21).
    """
    assert depth >= 1 and n_terminals >= 3
    n_distr = n_terminals - 1 - isolated_terminals
    assert n_distr >= 1, "au moins une chaîne distractrice"
    assert n_nodes >= depth + 1 + 2 * n_distr + isolated_terminals, \
        "budget de nœuds insuffisant"
    labels = _codes(rng, n_nodes, domain)
    # chaîne principale : start + (depth-1) internes + terminal réponse
    chain_nodes = [labels.pop() for _ in range(depth + 1)]
    answer_term = chain_nodes[-1]
    # chaînes distractrices : distribution EXACTE du budget restant,
    # chacune ≥ 2 nœuds (aucun nœud orphelin : budget total contrôlé).
    # mode "flat" (historique E1-E4) : +1 aléatoire → distracteurs courts.
    # mode "varied" (E5v2) : longueurs étalées jusqu'à depth+2 → des
    # distracteurs AUSSI LONGS (ou plus) que la chaîne réponse : la
    # longueur de chaîne ne prédit plus la réponse (anti-raccourci A6).
    lengths = [2] * n_distr
    extra = n_nodes - (depth + 1) - isolated_terminals - 2 * n_distr
    if distractor_length_mode == "varied":
        cap = depth + 2
        guard = 0
        while extra > 0 and guard < 10 * n_nodes:
            guard += 1
            i = rng.randrange(n_distr)
            if lengths[i] < cap:
                lengths[i] += 1
                extra -= 1
        # reste éventuel (cap atteint partout) : réparti quand même
        while extra > 0:
            lengths[rng.randrange(n_distr)] += 1
            extra -= 1
        # post-passe A6 : garantir ≥ 1 distracteur AUSSI LONG que la chaîne
        # réponse (depth+1) en transférant depuis les autres (chacun ≥ 2) —
        # la chaîne réponse n'est JAMAIS strictement la plus longue.
        # Faisabilité : n_nodes ≥ 2*(depth+1) + 2*(n_distr-1) (assurée par
        # les configurations des pools E5v2).
        target = depth + 1
        feasible = n_nodes >= 2 * (depth + 1) + 2 * (n_distr - 1)
        if n_distr >= 2 and max(lengths) < target and feasible:
            i_max = lengths.index(max(lengths))
            need = target - lengths[i_max]
            guard = 0
            while need > 0 and guard < 10 * n_nodes:
                guard += 1
                donors = [j for j in range(n_distr)
                          if j != i_max and lengths[j] > 2]
                if not donors:
                    break
                j = max(donors, key=lambda k: lengths[k])
                lengths[j] -= 1
                lengths[i_max] += 1
                need -= 1
    else:
        for _ in range(extra):
            lengths[rng.randrange(n_distr)] += 1
    chains = [chain_nodes] + [[labels.pop() for _ in range(ln)] for ln in lengths]
    isolated = [labels.pop() for _ in range(isolated_terminals)]
    terminals = [c[-1] for c in chains] + isolated
    # ANTI-RACCOURCI CRITIQUE : l'ordre des nœuds est mélangé — sinon les
    # indices suivent l'ordre de construction des chaînes et la trace
    # devient 0,1,2,…,depth sans lire les arêtes (test de corrélation).
    nodes = [n for c in chains for n in c] + isolated
    rng.shuffle(nodes)
    edges = [[c[i], c[i + 1]] for c in chains for i in range(len(c) - 1)]
    rng.shuffle(edges)

    options = []
    term_opts = list(terminals)
    rng.shuffle(term_opts)
    for t in term_opts:
        options.append({"id": _oid(rng), "node": t})
    if internal_candidate:
        # nœud interne éliminable : jamais sur le chemin de la réponse
        # (sinon il serait atteignable depuis le départ)
        path_set = set(chain_nodes)
        internal = [n for n in nodes if n not in terminals and n not in path_set]
        if internal:
            options.append({"id": _oid(rng), "node": rng.choice(internal)})
    rng.shuffle(options)

    p = Problem(
        id=pid or _pid(rng), nodes=nodes, edges=edges, start=chain_nodes[0],
        options=options, answer_node=answer_term, depth=depth,
        trace_nodes=chain_nodes, terminals=terminals,
        group_id=group_id, pool="")
    p.validate()
    return p


def _pid(rng: random.Random) -> str:
    return "b2-" + "".join(rng.choice("0123456789abcdef") for _ in range(10))


def _oid(rng: random.Random) -> str:
    return "".join(rng.choice(_ALPHABET + "23456789") for _ in range(5))


# --------------------------------------------------------------------------
# Paires contrôlées (audit §2.6 / mission)
# --------------------------------------------------------------------------

def variant_decisive_edge(p: Problem, rng: random.Random,
                          pid: str = "") -> Optional[Problem]:
    """Arête DÉCISIVE modifiée : retarget une arête du chemin de la réponse
    vers un autre terminal ⇒ la réponse DOIT changer (vérifié par oracle)."""
    succ = p.successor_map()
    on_path = [(p.trace_nodes[i], p.trace_nodes[i + 1])
               for i in range(p.depth)]
    rng.shuffle(on_path)
    others = [t for t in p.terminals if t != p.answer_node]
    for u, _v in on_path:
        for t in rng.sample(others, len(others)):
            edges2 = [list(e) for e in p.edges]
            edges2 = [[u, t] if e[0] == u else e for e in edges2]
            q = Problem(
                id=pid or _pid(rng), nodes=list(p.nodes), edges=edges2,
                start=p.start, options=[dict(o) for o in p.options],
                answer_node="", depth=0, trace_nodes=[], terminals=list(p.terminals),
                group_id=p.group_id, pool=p.pool)
            try:
                ans, path = q.walk()
                if ans == p.answer_node or ans not in [o["node"] for o in q.options]:
                    continue
                q.answer_node, q.trace_nodes = ans, path
                q.depth = len(path) - 1
                q.pair = {"role": "decisive_edge", "base": p.id,
                          "expected": "answer_changed"}
                q.validate()
                return q
            except (ValueError, AssertionError):
                continue
    return None


def variant_distractor_edge(p: Problem, rng: random.Random,
                            pid: str = "") -> Optional[Problem]:
    """Arête DISTRACTRICE modifiée : retarget une arête HORS chemin vers un
    terminal ⇒ la réponse DOIT rester stable (vérifié par oracle)."""
    path_set = set(p.trace_nodes)
    candidates = [e for e in p.edges if e[0] not in path_set]
    rng.shuffle(candidates)
    for u, _v in candidates:
        for t in rng.sample(p.terminals, len(p.terminals)):
            if t == _v:
                continue  # pas de variante no-op
            edges2 = [list(e) for e in p.edges]
            edges2 = [[u, t] if e[0] == u else e for e in edges2]
            q = Problem(
                id=pid or _pid(rng), nodes=list(p.nodes), edges=edges2,
                start=p.start, options=[dict(o) for o in p.options],
                answer_node=p.answer_node, depth=p.depth,
                trace_nodes=list(p.trace_nodes), terminals=list(p.terminals),
                group_id=p.group_id, pool=p.pool)
            try:
                q.pair = {"role": "distractor_edge", "base": p.id,
                          "expected": "answer_same"}
                q.validate()          # marche inchangée ⇒ stable par oracle
                return q
            except (ValueError, AssertionError):
                continue
    return None


# --------------------------------------------------------------------------
# Signature structurelle (contrôle des doublons, E4 / pools distincts)
# --------------------------------------------------------------------------

def structural_signature(p: Problem) -> tuple:
    """Empreinte indépendante des étiquettes : multi-ensemble des longueurs
    de chaînes (marches depuis les sources, degré entrant nul), longueur de
    la chaîne réponse, terminaux, candidats, profondeur. Deux problèmes de
    même signature = même structure renommée."""
    indeg = {n: 0 for n in p.nodes}
    succ = p.successor_map()
    for _u, v in p.edges:
        indeg[v] += 1
    chains = []
    ans_len = 0
    start = p.trace_nodes[0]
    for s in (n for n in p.nodes if indeg[n] == 0):
        ln, node = 1, s
        is_ans = s == start
        while node in succ:
            node = succ[node]
            ln += 1
            if node == start:
                is_ans = True
        chains.append(ln)
        if is_ans:
            ans_len = ln
    chains.sort()
    return (tuple(chains), ans_len, len(p.terminals), len(p.options),
            p.depth, sum(1 for o in p.options if o["node"] not in p.terminals))
