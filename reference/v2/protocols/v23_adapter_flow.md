# V2.3 — B5 : flux adaptateur public, texte → réponse (document de contrat)

*Objet : formaliser **ce que le parser étendu fournit à l'INFÉRENCE** (spans de
faits, entités par ligne) vs **ce qui ne sert qu'aux CIBLES** (arêtes oracle,
terminaux, trajectoires), et le **schéma de dépendances complet** avec les 5
rôles de l'amendement 2 (`V2.3_PROPOSAL.md`). Document de consolidation, aucune
expérience ; s'appuie sur le code, les correctifs QA `0ef0904a` + `058de55a`,
`data_contract.md §V2.3` et l'audit anti-fuite C1 (`reports/c1_complements_ag3.md`).*

## 1. Schéma de dépendances (texte → réponse)

```
                 ┌──────────────────────── Renderer (graphe) ────────────────────────┐
                 │ texte public : state (lignes-faits) + question + options[].text   │
                 └───────────────────────────────┬───────────────────────────────────┘
                                                 ▼
   ┌────────────────────────── PublicAdapter (PUBLIC SEUL) ───────────────────────────┐
   │ tokenizer épinglé (offsets) ─ tokens ; parse_state_v2 (8 formes inversées)        │
   │   → unités-fait = LIGNES reconnues (span char→token) + entités présentes/ligne   │
   │ question → containment du départ ; options[].text → labels CANDIDATS publics     │
   │ sortie = batch public (aucun champ privé)        [collate_public / C1]           │
   └───────────────────────────────┬───────────────────────────────────────────────────┘
                                   ▼
   ┌──────────────── Lecteur A2 (LoRA + têtes, gelé en E1) ───────────────────────────┐
   │ tagger → mentions (runs de tokens, normalisées) ; têtes fact-level sur les SPANS │
   │ DE FAIT → distributions (sujet, objet) ; départ = containment sinon tête apprise │
   └───────────────────────────────┬───────────────────────────────────────────────────┘
                                   ▼
   ┌──────────── Propagation (soft) ────────────┐   ┌── Voie discrète (diagnostic) ──┐
   │ A = masses sujet×objet (transition_matrix_ │   │ successors_from_facts → marche  │
   │ from_facts) ; INCONNU = masse sujet        │   │ exacte / solveur               │
   │ manquante ; p_{t+1}=p_t@A (T=20, terminaux │   └───────────────┬────────────────┘
   │ self-loop) ; argmax CANDIDATS (clé stable) │                   │
   └───────────────┬────────────────────────────┘                   │
                   ▼                                                ▼
              RÉPONSE ─────────────────────────────► Evaluator (prédiction + terminal oracle)
                                                        │
                        P_eval (parser+solveur figé) ───┘  (baseline concurrente, même texte)
                        V_sem (texte + graphe attendu + traces) — OUTIL SÉPARÉ, hors score
                                   ┌──────────────────────────────────────────────┐
        CIBLES (jamais à l'inférence) : graph.edges → successor (-1/-2), terminal
        oracle, trajectoire gold (β·CE états) ; graph.query.start (gold) ;
        graph.nodes (harnais d'entraînement seulement) ; mapping option→nœud.
                                   └──────────────────────────────────────────────┘
```

## 2. Ce que le parser étendu fournit à l'INFÉRENCE

`parse_state_v2` (v2 strict **+ les 8 formes inversées**, `src/v2data/textfamily.py`
l.302-322 ; rappels l.329) est consommé **ligne par ligne** par
`_parse_fact_line` (`extraction_data.py` l.127). À l'inférence, via
`collate_public` (`scripts/run_c1_complement.py` l.263) :

1. **Segmentation en unités-fait** : chaque ligne reconnue devient un **span
   (char → token)** ; c'est l'entrée des têtes fact-level (`fact_reps`).
   Comportement **différent selon le consommateur** — à connaître pour lire
   un échec :
   - **harnais d'évaluation historique** (`targets_from_problem`, via
     `_parse_fact_line`) : une ligne non reconnue **LÈVE**
     (« ligne d'état non analysable (v2 strict) », `extraction_data.py`
     l.211-213) ⇒ l'éval s'arrête bruyamment (c'est exactement ce qui s'est
     produit sur L2-inv avant le correctif `0ef0904a`) ;
   - **chemin public seul** (`collate_public`) : la ligne est **ignorée**
     (pas de span) ⇒ **perte silencieuse** d'un fait : la masse de sujet
     manquante augmente, l'INCONNU absorbe — effet de **plomberie**, pas de
     compréhension.
   Dans les deux cas, c'est LE point de mesure **F0** des freeze-checks V2.3 :
   compter les faits perdus par niveau (le silence du chemin public ne doit pas
   être confondu avec une réussite).
2. **Entités présentes par ligne** (noms cités) : utilisées pour ancrer les
   **cibles d'entraînement** (`fact_subject`/`fact_object`) ; à l'inférence, les
   têtes prédisent sujet/objet sur les **mentions du tagger** — le parser ne
   choisit jamais la réponse.
3. **Normalisation d'orientation** : les 8 formes inversées
   (« p34M est pointé par d45U. » → `(d45U → p34M)`) fixent le sens
   prédécesseur→successeur. À l'inférence cela ne sert qu'à **reconnaître la
   ligne comme fait** (le span) ; l'orientation elle-même est **apprise** par
   les têtes (cibles en entraînement, cf. §3).
4. **Garde de reproductibilité** : `parse_state_v2` a été étendu **sans
   toucher P_eval** (`0ef0904a`, restauré proprement en `058de55a`) ; la
   couverture de P_eval reste un **résultat publié**, pas un outil de tri des
   items.

Le parser **n'est pas** la source de : mentions (tagger), départ
(`deterministic_start`, containment question↔mention, l.227 de `extractor.py`),
successeurs (têtes fact-level → `transition_matrix_from_facts`, l.59 de
`propagation.py`), candidats (labels des options publiques), réponse.

## 3. Ce qui ne sert qu'aux CIBLES (jamais à l'inférence)

| élément cible | source | usage unique |
|---|---|---|
| `graph.edges` → `successor` (-1 terminal / -2 INCONNU) | privé | CE transitions (α) en entraînement ; marche discrète/oracle |
| terminal oracle (fin de marche) | privé | **scoring** (Evaluator) ; jamais montré au modèle |
| trajectoire gold (nœuds par pas) | privé | β·CE états (entraînement A2/A3) |
| `graph.query.start` | privé | cible du départ (CE start) ; p0 teacher-forcé en entraînement |
| `graph.nodes` | privé | **harnais d'entraînement** uniquement (construction des mentions/faits gold) ; inutile au chemin public |
| `graph.options` / mapping option→nœud | privé | mapping des candidats **dans l'Evaluator** (par texte de label) |
| terminaux déclarés, flags | privé | contrôle/QA (V_sem, tests) |

Preuve de cloisonnement : audit C1 (`reports/c1_complements_ag3.md`) —
couche structurelle **3200/3200 tenseurs d'entrée identiques** après
randomisation des champs privés (edges/terminals/traces), couche publique
« batch sans aucun champ privé ≡ harnais » (64/64 ×2 lecteurs), couche
comportementale prédictions inchangées 64/64 ×2. Le `successor` gold change
(3200/3200) sans que rien de l'entrée ne change : la cible n'alimente pas
l'inférence.

## 4. Récapitulatif : élément → source → usage

| élément | fourni par | inférence | cibles | rôle (am. 2) |
|---|---|---|---|---|
| texte public (state/question/options) | Renderer | oui | — | Renderer |
| tokens/offsets, spans de fait, unités-lignes | parser public (`parse_state_v2` + 8 formes) via PublicAdapter | **oui** (entrée des têtes fact) | oui (spans identiques) | PublicAdapter |
| mentions/spans d'entités | tagger appris | oui | (oracle à l'entraînement) | PublicAdapter + modèle |
| sujet/objet d'un fait | têtes fact-level (modèle) | oui (prédit) | oui (CE fact, orientation parser) | modèle |
| arêtes/terminal/trajectoire | graphe privé | **non** | oui | Evaluator/training |
| départ | containment question (public) sinon tête | oui | `query.start` (CE) | PublicAdapter/modèle |
| candidats | labels des options publiques | oui | mapping nœud (Evaluator) | PublicAdapter/Evaluator |
| réponse | propagation / voie discrète | oui | terminal oracle (score) | modèle → Evaluator |
| couverture parser (baseline) | P_eval figé | baseline concurrente | — | P_eval |
| validité sémantique des textes | V_sem (texte + graphe attendu + traces) | — | — | V_sem (hors score) |

## 5. Contrat d'interface (amendement 4) — réponses verrouillées

- **Entités** : extraites du **texte** au runtime (tagger) ; l'inventaire
  public disponible est celui des **options** (candidats). Aucun inventaire
  privé n'entre dans le flux.
- **Départ** : question **brute** + containment (espaces/casse normalisés) ;
  fallback = tête apprise. Le pointeur gold n'est jamais lu.
- **Unité fact-level = la LIGNE** du state (contrat verrouillé) ; **une ligne
  = 0 ou 1 relation** au runtime. Les empaquetages multi-relations par
  phrase/ligne (L2-b) **ne sont pas supportés par ce flux** : s'ils sont
  testés, l'échec est une **limite de segmentation** à publier comme telle,
  jamais une preuve d'incompréhension — et la réparation par les relations
  privées est interdite (cellule privilégiée de diagnostic uniquement).
- **Deux scores séparés** : texte brut / assistance structurée déclarée
  (jamais mélangés).
- **Assistance limitée au public** : la seule « structure » fournie par
  l'adaptateur est la segmentation en lignes/faits (déclarée) et les labels
  d'options ; jamais les arêtes.

## 6. Règles de cloisonnement des rôles (amendement 2)

| composant | informations autorisées | interdits |
|---|---|---|
| **P_eval** (parser+solveur figé) | texte + interface publique déclarée | graphe privé ; toute influence sur la sélection des items |
| **V_sem** (validateur sémantique) | texte, graphe attendu, traces de génération | alimenter le score ou le modèle ; fusion avec P_eval |
| **Renderer** | graphe de génération | connaître les systèmes évalués ; produire d'après leurs erreurs |
| **Evaluator** | prédictions + réponses exactes | exposer les réponses au modèle |
| **PublicAdapter** | informations publiques prévues **uniquement** | tout champ `private.*` |

Interdits structurants : (i) **round-trip « parser == graphe ⇒ rejet »** avec
P_eval (circulaire) — la vérification sémantique passe par V_sem/humain ;
(ii) **aucune exclusion basée sur une erreur d'A2/A3/P_eval** — seulement des
règles sémantiques/techniques préfixées ; (iii) aucune renormalisation
silencieuse de la masse hors-candidats/INCONNU (elle est archivée et publiée).

## 7. Limites et pièges documentés (avec preuves)

1. **Couverture du parser = plomberie, pas compréhension** : le correctif L2-inv
   (`0ef0904a` : extension aux 8 formes inversées, P_eval inchangé ; `058de55a` :
   restauration propre, tests 9/9) a été nécessaire pour que l'éval A2 variante
   soit seulement **exécutable** (avant : `targets_from_problem` **levait** sur
   les templates inversés). Attention à l'asymétrie harnais/public : une forme
   inconnue **arrête** le harnais mais **disparaît silencieusement** dans le
   chemin public seul — un score public sans mesure des faits perdus est
   ininterprétable. Contrôles QA positifs : 2719/2719 inversions = arêtes
   réelles, 0 violation d'unicité, 400/400 paires de graphes identiques,
   canonique direct max 387 tokens.
2. **Matching label↔mention par TEXTE** (jamais par index) : les ids E5v2 ne
   sont pas uniques (358 doublons à contenu différent) ; les harnais assertent
   `set(labels) == set(nodes)` à l'entrée.
3. **≤512 binding = prompt DIRECT** (state+question+options) : max 503/512,
   marge 9 tokens (`data_contract.md §V2.3`) ; tous les collates **lèvent**
   (jamais de troncature) ; règle préenregistrée : régénérer plus court à seed
   fixe, jamais dropper.
4. **Le harnais d'évaluation historique consomme du privé** (`targets_from_problem`
   exige `graph.nodes` pour construire les lots) : le chemin **public seul**
   existe (`collate_public`) et a été prouvé égal (C1) — à utiliser pour tout
   audit de cloisonnement.
5. **Drift bf16 inter-toolchain** : comparaisons freeze même-session/même
   toolchain ou tolérance (≤1,5 pt) ; publication toolchain torch 2.6.0+cu124
   = 0 flip/3200, torch 2.14 = 18/3200 (divergence H backbone).
6. **L2-c (référence) et négation** : hors de ce flux — un fait sans mention
   explicite n'a pas d'ancrage (nouveau module/contrat), et « négation ≠
   absence ≠ terminal » doit être défini avant toute mesure.

## 8. Références code (chemins et lignes)

- `src/v2data/textfamily.py` : `parse_state_v2` l.302, `_INV` (8 formes) l.311-320,
  rappels l.329 ; `RAPPEL_PREFIX` l.259 ; templates `EDGE_TEMPLATES_V2`.
- `src/v2model/extraction_data.py` : `_parse_fact_line` l.127 ; ligne non
  analysable = `ValueError` l.211-213 (harnais) ; `collate_extraction`
  (lève >512) l.326.
- `src/v2model/extractor.py` : `successors_from_facts` l.172 ; `deterministic_start` l.227.
- `src/v2model/propagation.py` : `transition_matrix_from_facts` l.59 (INCONNU =
  masse de sujet manquante ; terminaux self-loop).
- `src/v2model/direct_text.py` : `build_direct_prompt` ; `collate_direct_text`
  (lève >512) l.165.
- `scripts/run_c1_complement.py` : `collate_public` l.263 ; `structural_antileak`.
- Commits : `0ef0904a`, `058de55a` (parser) ; `e79eb387`/`a10976e9` (audits
  publics/anti-fuite) ; `data_contract.md §V2.3` ; `reports/c1_complements_ag3.md`.
