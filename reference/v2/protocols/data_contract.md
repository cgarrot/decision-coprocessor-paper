# CONTRAT DE DONNÉES V2 — Famille B simplifiée (E0-DONNÉES)

**Source :** audit externe §7.2/§7.3/§7.4/§13 + amendements DECISION-V2.md §3.5/§3.4.
**Module :** `src/v2data/bfamily.py` (générateur+oracle+traces), `src/v2data/pools.py` (E1-E4).
**Budget commun :** 16 transitions, terminal absorbant (jamais de budget choisi depuis la profondeur privée).

---

## 1. Structure d'un problème (génération)

- Plusieurs **chaînes orientées disjointes** ; **successeur UNIQUE** par nœud
  (validé) ; **aucune boucle** (marche oraculaire bornée, validée).
- **Plusieurs terminaux** (≥ 3, obligatoire — anti-raccourci : avec un
  terminal unique la réponse serait trouvable sans suivre le départ).
  Nœuds orphelins éventuels pointent vers des terminaux.
- **Candidats** = tous les terminaux (réponse + terminaux distracteurs)
  + au plus **un** nœud interne éliminable (minoritaire, ≤ 1, < 50 %).
  Aucun candidat non-réponse n'est atteignable depuis le départ (validé).
- **Entités opaques renommées par problème** (codes aléatoires, ou lettres
  A-Z pour le domaine simple E2) — l'ordre des identifiants est SANS
  corrélation avec la position dans la chaîne (testé statistiquement).
- **Ordre des faits mélangé** (arêtes en ordre aléatoire).
- **Nombre de nœuds comparable entre profondeurs** : E3 impose 14 nœuds
  pour les profondeurs 2/3/4 (profondeur plus grande ⇒ moins de
  distracteurs, budget total constant).

## 2. Format des entrées (vue PUBLIQUE `input`) — pour l'exécuteur S

```json
{
  "id": "b2-E3_train-000042-1a2b3c4d",
  "nodes": ["k7m", "q3x", ...],
  "edges": [["q3x", "k7m"], ...],
  "query": {"start": "q3x"},
  "options": [{"id": "a4t7k", "node": "k7m"}, ...]
}
```

- `nodes` : étiquettes opaques (l'indice dans cette liste = indice
  d'entité pour l'exécuteur).
- `edges` : arêtes orientées, ordre mélangé.
- `query` : nœud de départ UNIQUE. Pas de nombre de sauts demandé (le
  terminal est absorbant) ; un nombre de sauts explicite serait une
  entrée légitime pour une variante ultérieure « sauts fixés ».
- `options` : candidats, ids opaques aléatoires, ordre mélangé.

**INTERDIT dans `input`** (invariants testés) : réponse, trajectoire,
profondeur, drapeaux de terminal, group_id, métadonnées de paire, toute
marque du terminal réponse.

### Vue texte PUBLIQUE `text` (étage T ultérieur)

Rendu français déterministe (« Le point X mène au point Y. », « Le point
Z est un terminal. », « Départ : le point S. »), lignes mélangées. Le
terminal réponse n'y est pas distingué (comptage des mentions contrôlé).

## 3. Sorties attendues du système

Distribution sur les `options` (ids) ; pendant l'entraînement uniquement :
prédiction d'état par créneau t = 0..16 (voir §4). À l'inférence, aucune
trace n'est fournie ni requise.

## 4. Vue PRIVÉE `private` — supervision, JAMAIS en entrée d'inférence

```json
{
  "answer_node": "k7m",
  "answer_id": "a4t7k",
  "depth": 4,
  "trace_nodes":   ["q3x", "b2w", "r9d", "m1z", "k7m"],
  "trace_indices": [3, 0, 5, 2, 1],
  "trace_padded_indices_budget16": [3, 0, 5, 2, 1, 1, 1, ..., 1],
  "trace_loss_weights_budget16":   [w, w, w, w, w, w/12, ..., w/12],
  "is_terminal_flags": [0, 0, 0, 0, 0, 1, 0, 1, ...],
  "terminals": ["k7m", "x4c", "p8n"],
  "group_id": "gb2-000042-7kd93m",
  "pair": {"role": "base"}
}
```

- `trace_indices` : indices dans `nodes` — c'est la **séquence exacte
  d'états du pointeur** (départ → … → terminal), longueur `depth+1`.
- `trace_padded_indices_budget16` : trace + **terminal absorbant répété**
  jusqu'au budget 16 (17 états : t = 0..16) — cibles communes à tous les
  exemples d'un protocole.
- `is_terminal_flags` : par nœud (lecture finale : l'état doit désigner
  un nœud terminal ; le candidat réponse = terminal atteint).

### Normalisation de perte (audit §7.4 — anti-surpondération)

`Problem.trace_loss_weights(depth, budget=16)` fournit les poids par
créneau (somme = 1) :

- chaque état UNIQUE (t = 0..depth) reçoit `w = 1/(depth+2)` ;
- la masse absorbante (un seul « état » conceptuel) vaut `w`, RÉPARTIE
  uniformément sur les créneaux de répétition (t = depth+1..16) : les
  problèmes courts ne sont pas surpondérés par leurs nombreuses
  répétitions, les longues traces ne pèsent pas plus.

L (recommandé) = CE(réponse finale) + alpha × Σ_t poids_t · CE(état_t,
trace_padded_t), alpha fixé sur pilote puis consigné au registre.

### Interface traces ↔ exécuteur (@ag-3)

- entités : `nodes[i]` → vecteur d'entité i ; arêtes → relations locales ;
- état initial `s_0` : contraint par la tâche = pointeur sur
  `query.start` (jamais un résumé contextualisé libre) ;
- cible d'état au créneau t : one-hot de `trace_padded_indices_budget16[t]`
  (dimension |nodes|) ;
- lecture finale : score partagé entre l'état calculé et CHAQUE candidat
  (`options[*].node`) — la tête ne reçoit ni `q` ni `c_i` directement
  (amendement §3.3) ; la réponse correcte = l'option dont le nœud est le
  terminal atteint (`private.answer_id`, côté évaluation uniquement) ;
- un problème de profondeur 16 remplit exactement le budget (trace 17) ;
- amorçage possible sur états exacts pendant l'entraînement, puis
  déroulements autonomes à rapporter séparément (audit §7.4).

## 5. Paires contrôlées (interventions causales, audit §2.6)

| Variante | Transformation | Oracle exige |
|---|---|---|
| `decisive_edge` | retarget d'une arête DU chemin réponse vers un autre terminal | réponse CHANGE |
| `distractor_edge` | retarget d'une arête HORS chemin vers un terminal | réponse STABLE |

- mêmes nœuds, mêmes candidats, même nombre d'arêtes ;
- `group_id` attribué AVANT les variantes ; toutes les variantes d'un
  groupe dans le MÊME pool/split ;
- `pair.expected` ∈ {`answer_changed`, `answer_same`} — vérifié par
  l'oracle à la génération ET par les tests.

## 6. Pools

| Pool | Taille | Profondeurs | Nœuds | Terminaux | Paires | Domaine |
|---|---:|---|---:|---:|---:|---|
| E1 (surapprentissage) | 128 | 1-3 | 9 | 3 | 0 | codes |
| E2 (held-out) | 256 | 2-4 | 12-15 | 4 | ~30 % groupes | **lettres A-Z** (simple) |
| E3_train | 768 bases (+ variantes) | 2/3/4 | **13-16 (bande étroite)** | 4-5 | ~10 % | codes |
| E3_eval | 192 bases (+ variantes) | 2/3/4 | 13-16 | 4-5 | ~30 % | codes |
| E4 (RÉSERVÉ) | — | 6/8/10/16 | ~22 | 5 | — | capability `build_E4`, NON générée |

Invariants de pools (testés) : variété structurelle intra-pool — au plus
`SIG_CAP = 16` exemplaires par classe d'isomorphie (l'espace des petites
structures est borné, principe du pigeonnier ; la variété réelle vient
des étiquettes, de l'ordre des arêtes et des options) ; **disjonction
STRICTE des classes réservée à E4 contre E1-E3** (formes différentes par
construction : profondeurs 6-16, ~26 nœuds, 5 terminaux) ; E4 exigera en
plus des seeds de génération indépendantes (déjà implémenté dans
`build_E4` via `seen_sig` strict). Le manifeste compte les signatures.

## 7. Invariants généraux (tous testés — `tests/test_v2data.py`)

1. solution unique : marche oraculaire = réponse ; réponse présente
   exactement une fois dans les candidats ;
2. successeur unique, aucune boucle, terminaux = nœuds sans successeur ;
3. **≥ 3 terminaux** ; candidats non-réponses inatteignables depuis le
   départ ; internes minoritaires (≤ 1) ;
4. zéro fuite trace → entrée : aucune clé/marque privée dans `input`
   ni dans `text` ; le terminal réponse n'est pas le plus mentionné ;
   ordre des ids non corrélé à la position dans la trace ;
5. paires contrôlées : `answer_changed` ⇒ réponse différente ;
   `answer_same` ⇒ identique ; même groupe ⇒ même pool ;
6. traces : longueur depth+1 ≤ budget+1 ; padding absorbant exact ;
   poids de perte sommant à 1 ;
7. fichiers : une ligne JSONL par problème, manifeste avec compteurs,
   signatures et sha256.

---

## §E5 — Pools TEXTE (audit §8 version T)

**Module :** `src/v2data/textfamily.py` (rendu varié + oracle de
re-analyse) + `pools.build_E5_pool / build_and_write_E5`.

### Vue publique (texte seul)

```json
{"state": "…formulations variées des arêtes et terminaux, ordre mélangé…",
 "question": "…départ cité, formulation tirée…",
 "options": [{"id": "x4k2m", "text": "le relais q3x"}, …]}
```

- 8 formulations d'arêtes, 6 de terminaux, 5 de question, 7 wrappers
  d'options — tirées PAR INSTANCE via des decks sans-remise (chaque
  formulation utilisée avant répétition) ; wrapper CONSTANT par instance ;
- entités opaques citées telles quelles (codes du domaine « gen ») ;
- la réponse n'est pas dérivable lexicalement : question sans le label
  réponse, recouvrement question↔option au niveau du hasard (testé),
  chaque terminal mentionné exactement 2 fois dans l'état (bases).

### Vue privée

`private.graph` = le graphe structuré EXACT (cible d'extraction :
nodes/edges/query/options/terminals/answer) + les traces d'états au
format exécuteur INCHANGÉ (trace_indices, padding absorbant budget 16,
poids de perte) — le bridge v2model consomme les mêmes clés qu'en E1-E4.
+ `group_id`, `pair`.

### Invariants E5 (testés — tests/test_v2text.py)

1. oracle texte↔structure : `parse_state(state)` redonne exactement les
   arêtes/terminaux privés ; la marche depuis le départ = answer (sur
   100 % des lignes des deux pools) ;
2. zéro fuite : aucun marqueur privé dans la vue texte ; mentions
   uniformes des terminaux (bases) ;
3. anti-lexical : l'argmax du recouvrement question↔option prédit la
   réponse au niveau du hasard ;
4. reformulations (paraphrase) : même group_id, même pool, même graphe,
   texte différent ; paires decisive_edge : réponse change, texte
   différent, mêmes nœuds ;
5. E5_eval RÉSERVÉ : capability `build_E5_pool` avec seed indépendante
   (1007), empreintes de graphes EXACTS disjointes de train+dev — non
   généré avant sa porte.

### Pools (sur disque)

| Pool | Total | Bases | Paires decisive | Paraphrases | Depths | Seed |
|---|---:|---:|---:|---:|---|---:|
| E5_train | 1999 | 1400 (467/467/466) | 328 | 271 | 2/3/4 | 1005 |
| E5_dev | 400 | 280 (94/93/93) | 63 | 57 | 2/3/4 | 1006 |
| E5_eval | RÉSERVÉ | ~280 cibles | ~25 % | ~20 % | 2/3/4 | 1007 |

Limite documentée : les classes d'isomorphie de E5 sont VOLONTAIREMENT
celles de la distribution E3 (l'étage S a appris sur cette distribution ;
E5 isole la connexion TEXTE — la nouveauté n'est pas structurelle) ;
l'anti-doublon E5 porte sur les graphes EXACTS (étiquettes comprises),
pas sur les classes. Cap de variété E5 = 32 (même justification qu'E4).

---

## §E5v2 — Pool TEXTE corrigé (remédiation A6, branche B)

**Motif :** le bench T v1 (E5) était invalide — un probe lexical trivial
résolvait la tâche. Deux bugs générateur + un raccourci structurel,
tous trois corrigés et **détectés par le probe lui-même** :

| # | Indice | Correctif | Preuve |
|---|---|---|---|
| I1 | template de déclaration lié à la réponse (« est un point d'arrivée », +8.56 en log-odds) | deck mélangé À LA CRÉATION (le 1er tirage ne prend plus template[0]) + émission des terminaux en ordre aléatoire | test fréquences par formulation réponse vs distracteurs (±0.08) |
| I4 | ordre de tirage des templates = ordre de construction des chaînes (réponse en tête) | arêtes ET terminaux émis en ordre mélangé indépendant | test position 1re mention (±0.05) |
| I5 | « terminal de la chaîne la plus longue » résout la tâche (distracteurs quasi tous de longueur 2) | mode `distractor_length_mode="varied"` + post-passe : ≥ 1 distracteur AUSSI LONG que la chaîne réponse (faisabilité : depth 4 → nœuds 14-16, t=4) | P(réponse = unique plus longue) = 0.036 (vs 0.31 avant), test ≤ 0.06 |
| I2 | comptages de mentions | rappels d'arêtes (p=0.30, AUTRE formulation) + secondes déclarations (p=0.25) → comptages aléatoires uniformes | test moyenne mentions réponse vs distracteurs (±0.25) |
| I6 | wrappers prédictifs | wrapper tiré PAR option (deck de 10) | test distribution réponse vs distracteurs (±0.10) |
| I3 | longueur | bande de nœuds étroite ; lignes aléatoires (rappels) | — |

**Discriminant A6 (publié : `reports/lexical_probe_e5v2.json`)** — probe
lexical trivial (bag-of-words des lignes du candidat, bigrammes de
voisinage, comptages/positions de mentions, wrapper, index, K — Bernoulli
NB add-1, stdlib pur, ~14 s) entraîné sur E5v2_train :

```text
train=100   dev_acc=0.2286  hasard=0.2205  excès=+0.0080
train=250   dev_acc=0.2179  hasard=0.2205  excès=-0.0027
train=500   dev_acc=0.2250  hasard=0.2205  excès=+0.0045
train=1000  dev_acc=0.2179  hasard=0.2205  excès=-0.0027
train=1400  dev_acc=0.2429  hasard=0.2205  excès=+0.0223   → NEAR_CHANCE
```

**Pools** : E5v2_train = 2 049 (1 400 bases 467/467/466 + 360 decisive +
272 paraphrases, seed 1105) ; E5v2_dev = 411 (280 bases + 80 + 55,
seed 1106) ; E5v2_eval RÉSERVÉ (seed 1107, graphes exacts disjoints,
non générée). E5 v1 : train/dev SUPERSEDED au manifeste, **eval v1
scellée À JAMAIS (seed 1007 retirée)**. Contrat inchangé par ailleurs :
traces au format exécuteur, paires decisive (texte : arête décisive
reformulée ⇒ réponse change), paraphrases même group_id. Cap E5v2 = 48
(espace structurel rétréci par la post-passe I5 ; la diversité est
portée par la surface : 14 templates d'arêtes, 10 de terminaux, 9 de
question, 10 wrappers, rappels et secondes déclarations).

---

## §V2.1 — Bancs de validation (protocole préenregistré V21_PROTOCOL.md §2)

8 cellules n=400 (B1-court, B2-prof6, B3-prof8, B4-prof10, B5-surface,
B6-distract, B7-options, B8-depart) — seeds 2205-2212, K∈{4,5,6}, ≤20
nœuds, FR, surface E5v2. Fichiers `data/v21/*.jsonl` + manifeste dédié
`data/manifest_v21data.json` (sha256, by_K, token_len, classes
d'isomorphie, appariements). Spécificités du contrat V2.1 :
`example_uid` unique, `base_group_id` (appariement B5-B8 → B1 par
`pair.anchor`), `public_hash` par exemple, `path_candidate_option_id`
(liste) = candidats INTERMÉDIAIRES DU CHEMIN par construction (~25 %,
relaxation Q3 préenregistrée : non terminaux, jamais la réponse),
`token_len` mesuré au tokenizer Qwen3-0.6B figé (≤512 par construction).
B7 partage le graphe exact de son ancre PAR CONCEPTION (seules les
options changent — exemption d'unicité documentée, uid/hash distincts).
Pigeonhole documenté : n=400/cellule sur espaces d'isomorphie bornés →
répétition de classes intra-cellule mesurée (`class_counts`) ; les
garanties strictes sont la disjonction B1-B4 ↔ E5v2 figé et l'unicité
globale des graphes exacts (hors appariement B7). E5v2_eval (1107) et
E5_eval (1007) : scellés, intacts.
