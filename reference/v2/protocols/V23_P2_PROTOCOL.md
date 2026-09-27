# PROTOCOLE P2 — diagnostic de la décroissance inversions×profondeur (PRÉENREGISTREMENT, à valider par QA avant figage/exécution)

*GO utilisateur 21:52 (audit 096bc009 §P2). Aucun entraînement — poids figés
(A2-E2 s22 + s24), bancs E3-p6/p8/p10 (inversions), zéro compute nouveau
hors évals diagnostiques (~40 min GPU). Interdits + anti-écrasement actifs.*

## Question

Pourquoi la robustesse aux inversions d'A2-E2 décroît-elle avec la profondeur
(0.93 court → 0.68–0.80 prof10) alors que canonique/L1 restent à 0.99–1.00 ?

## Trois hypothèses préenregistrées (mutuellement non exclusives, à départager)

- **H-A (composition d'erreurs locales)** : la précision PAR ARÊTE sur les
  lignes inversées baisse peu avec la profondeur (p ≈ cste < 1) mais les
  erreurs se composent le long de la chaîne : acc ≈ p^profondeur.
  *Prédiction falsifiable : p(inv, arête) ≈ 0.93–0.96 constant par profondeur
  ET acc(canonique) ≈ 1.0 (donc pas d'effet contexte).*
- **H-B (contexte long/chargé)** : la lecture des inversions se dégrade avec
  la LONGUEUR du texte (pas la profondeur) — à nombre d'inversions égal,
  un texte plus long lit plus mal.
  *Prédiction : p(inv, arête) décroît avec la longueur du texte à profondeur
  fixée ; V4 (chemin court dans texte long paddé) dégrade aussi le court.*
- **H-C (masse perdue)** : les arêtes top-1 sont correctes (p > 0.99) mais la
  MASSE se disperse (chemins parasites, INCONNU) : la propagation dilue.
  *Prédiction : p(inv, arête top-1) > 0.99 à toutes profondeurs ET masse
  p_T sur le terminal correct décroît / masse INCONNU+hors-candidats croît.*

## Mesures (chaque item deep inv : E3-p6/p8/p10-variante, 300/cellule, ×2 ckpts)

1. **p(arête, inv)** : précision top-1 des relations sur les lignes inversées
   du chemin utile (oracle par alignement ligne↔arête via la table fermée) —
   par profondeur, par position de ligne (tiers début/milieu/fin).
2. **Masses** : p_T[terminal correct], masse INCONNU, masse hors-candidats,
   masse sur terminaux parasites — par profondeur.
3. **Trajectoires** : p0..p20 archivées (matrice alignée rendu↔probas↔états).

## Variations contrôlées (générées depuis les MÊMES graphes E3, rendus neufs)

- **V1** : exactement UNE ligne inversée (position: début/milieu/fin du texte) ;
- **V2** : inversions sur les lignes DISTRACTRICES uniquement (chemin canonique) ;
- **V4** : chemin court (prof 1–2) dans un texte LONG paddé de distracteurs
  canoniques (longueur ≈ p10) — isole la longueur de la profondeur ;
- (V5 départs variés : DIFFÉRÉ — déjà couvert par B8 en canonique.)

## Interventions oraculaires (SURGERIE de matrice A prédite — diagnostic seul)

Pour chaque item deep-inv, re-propager avec :
- **O1** : lignes du CHEMIN utile remplacées par leurs distributions canoniques
  (ré-encodage du rendu canonique même graphe) ;
- **O2** : terminaux seuls corrigés ;
- **O3** : hors-chemin seul corrigé.
*Interprétation : O1 ≫ O3 → le déficit est la lecture du chemin en inversé ;
O3 ≫ O1 → les distracteurs inversés polluent la propagation.*

## Baseline P1 (en parallèle, CPU)

- **Parser étendu** : P_eval + les 8 formes inversées dans SA grammaire
  (assistance DÉCLARÉE — le P_eval officiel des rapports reste inchangé) +
  solveur exact sur E3-inv : le langage inversé est-il déterministement
  résoluble une fois la grammaire étendue ? (attendu : oui par construction
  — publié comme borne, pas comme concurrent neuronal).
- **Schéma de dépendances** : table des valeurs consommées par l'INFÉRENCE
  (texte public, spans lignes, candidats) vs CIBLES seules (arêtes oracle
  pour p(arête)) — formalise l'amendement 5.

## Critères de décision (figés avant exécution)

| constat | hypothèse retenue | modification recommandée (UNE) |
|---|---|---|
| p(inv,arête) cste < 1 ET O1 grand gain | H-A (composition) | E2-bis : inversions aux profondeurs VARIÉES dans la mixture (couverture) |
| p(inv,arête) ↓ avec longueur ET V4 dégrade | H-B (contexte) | exposition contexte long à l'entraînement (rendus paddés) |
| p(inv,arête) > 0.99 ET masse dispersée | H-C (masse) | contrainte de cohérence inter-formulations (perte de masse) |
| mixte | documenter les parts | la modification visant la part dominante |

La recommandation est SOUMISE À ARBITRAGE UTILISATEUR avant tout entraînement.

---

# AJOUTS QA (5 conditions, REG @ag-4 21:54 — figés AVANT exécution)

- **R1 — Seuils préfixés** : **H-A** retenu si p(inv,arête) constant à ±2 pts
  entre profondeurs ET |acc − p^prof| ≤ 3 pts (fit géométrique publié par
  profondeur) ET acc canonique ≥ 0.99. **H-B** si p(tercile long) −
  p(tercile court) ≥ 3 pts à profondeur fixée ET V4 perd ≥ 3 pts vs chemin
  court normal. **H-C** si top-1 p(arête) > 0.99 toutes profondeurs ET
  ratio masse(terminal correct)/top-1 < 0.90 OU masse INCONNU+hors > 5 %.
- **R2 — Dominance (cas mixte)** : part de l'écart d'accuracy attribuée à
  chaque hypothèse via les fits O1/O3 et p(arête) ; la modification vise la
  part > 50 %.
- **R3 — Position** : n par tercile publié ; les lignes non alignées par la
  table fermée sont COMPTÉES COMME ERREURS, jamais ignorées.
- **R4 — Assistance oracle explicite** : O1/O2/O3 sélectionnent les lignes
  par le chemin GOLD (assistance déclarée) ; **O1 = ré-encodage du rendu
  canonique** (correction : pas « zéro ré-encodage ») ; tables séparées,
  jamais comptées comme benchmark.
- **R5 — Statut** : P2 = diagnostic POST-HOC (bancs E3 déjà observés) ;
  aucune revendication confirmatoire ; recommandations → arbitrage
  utilisateur (acté).
