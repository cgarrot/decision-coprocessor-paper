# PROTOCOLE V2.2 — ablations interface (préenregistré AVANT toute implémentation)

*GO utilisateur 14:04 via @ag-ask. Suite directe de V2.1-Q1 (ligne 2 matrice
Q4 : travailler l'interface). Audit §6 ; une hypothèse par ablation ;
interdits V21_PROTOCOL §0 reconduits intégralement (scellés, équité
d'information, pas de test fabriqué contre le direct).*

## Hypothèse centrale (préenregistrée)

Le déficit du pipeline en profondeur vient de la **discrétisation à
l'interface** (argmax par arête → une arête manquante tue la chaîne),
PAS d'une incapacité du lecteur (F1 arêtes 0.93, parser (p) : plafond ~0.95
atteignable depuis le texte public). En propageant les DISTRIBUTIONS de
successeurs (p_{t+1} = p_t @ A, terminaux auto-boucle, audit §6.2), le
pipeline doit récupérer une part mesurable de l'écart vers le plafond.

## Découverte fondatrice (étape 0, FAITE avant ce préenregistrement)

`MemoryExtractor.successor_logits` produit **[B, N, N+1]** (bilineaire +
classe TERMINAL, src/v2model/extractor.py:376) — les distributions par arête
EXISTENT dans le checkpoint figé ; `extract()` les jette à l'argmax.
→ **A1 réalisable SANS réentraînement** (le lecteur du bundle reste figé).

## Ablations (UNE À LA FOIS, ordre figé)

| id | contenu | entraînement |
|---|---|---|
| **A1** | propagation p_{t+1}=p_t@A sur les distributions du LECTEUR FIGÉ : p_0 = one-hot(départ déterministe reconduit), A[i,:] = softmax(successor_logits[i, :N+1]), colonne TERMINAL = auto-boucle sur i ; T=20 pas (absorbant) ; réponse = argmax sur les nœuds CANDIDATS de p_T. Pas de INCONNU en A1 (le lecteur figé n'a pas cette classe — réservé à A2). | **AUCUN** |
| A2 | lecteur réentraîné à supervision distributionnelle (relations + états + réponse, audit §6.4, poids α/β progressifs) + INCONNU à sémantique définie | si A1 insuffisant OU demandé |
| A3 | direct avec tête auxiliaire ÉGALE (mêmes annotations, équité §3 du mandat) | après A2, si comparaison revendiquée |
| A4 | lecture paresseuse (relation utile à l'étape courante) | conditionnel |

## Critères figés (AVANT tout run)

- Évaluation sur les bancs V2.1 **scellés** (B1–B8, jamais utilisés pour
  une sélection — aucune sélection en A1 par construction).
- **Succès A1** : Δ(c_prop − c_discret) ≥ **+5.0 pts** sur B3 (prof 8),
  apparié par base_group_id, bootstrap groupé 2000, **IC bas > 0** ;
  non-régression court : c_prop ≥ c_discret − 2.0 pts sur B1.
- Publication systématique : Δ vs direct (descriptif), écart au plafond
  (p)=0.95, couverture (A1 n'abstient pas ; naked par construction).
- ÉCHEC A1 documenté tel quel → A2 selon la même grille de critères
  (cible : franchir le seuil que A1 a manqué + plafond ~0.95 comme
  milestone publié, jamais comme critère de succès).

## Tie-break CPU/GPU (mandat n°4, correctif dès le harnais)

Toute comparaison d'argmax à moins de **eps = 1e-3** (échelle logit) se
résout par **clé stable** (ordre alphabétique des labels). Appliqué au
harnais V2.2 (pas rétroactif sur V2.1 — mode gévé publié avec son caveat).

## Équité et interdits

- A1 n'ajoute RIEN au direct (aucune donnée nouvelle, aucun entraînement) :
  la comparaison vs direct reste celle de V2.1-Q1 (chiffres publiés).
- A2/A3 : mêmes annotations auxiliaires des deux côtés (sinon on confond
  architecture et données — mandat n°3).
- Sélection de checkpoints (A2+) : NOUVEAU banc de sélection à seed neuve
  (2213+, @ag-2) — les bancs V2.1 restent évaluation pure.
- Diagnostics oraculaires : tables séparées, jamais comptés.

## Chaîne après ablations (mandat n°5)

1. Borne oracle routeur (complémentarité V2.1 : 123/172/163 items) — le NLL
   direct (8.85 nats à prof 10 quand il se trompe) est le signal de routage
   à exploiter ; borne mesurée AVANT toute construction.
2. Coûts end-to-end Q3 (latence p50/p95/débit/mémoire/probas, mêmes lots,
   batch équitable deux voies — @ag-5).

## Rôles

@ag-1 : protocole, harnais A1, coordination, décisions. @ag-3 : câblage
(réutilisation en lecture seule ; A2/A4 si déclenchés). @ag-4 : validation
de CE préenregistrement puis QA de chaque ablation. @ag-2 : banc de
sélection seed 2213 (si A2), revue grammaire. @ag-5 : registre, coûts,
vérif tie-break.
