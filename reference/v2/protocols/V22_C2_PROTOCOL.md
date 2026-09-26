# PROTOCOLE C2 — confirmation (a) + extrapolation aveugle (b) — FIGÉ avant génération

*GO utilisateur « ab » 22:20 via @ag-ask, autonomie totale pour la nuit.
Audit V22-confirmation §9 (C2) ; interdits et discipline inchangés
(préenregistrement, registre append-only, équité, incidents documentés,
aucun test fabriqué). Génération INTERDITE avant ce figage — désormais figé.*

## Fait structurant (vérifié avant figage)

**E5v2_train ne contient QUE les profondeurs 1–4** (128/715/619/587). La
performance profondeur d'A2 est donc DÉJÀ aveugle au niveau des gradients —
le seul élément non-aveugle est le banc de SÉLECTION 2213 (50 % prof 6/8,
audit §3.2). Conséquence : C2-b = mêmes données d'entraînement, sélection
sur banc court-seulement neuf.

## Bancs neufs (génération @ag-1 avec le générateur @ag-2, anti-doublons TOTAL)

| banc | seed | contenu | usage |
|---|---|---|---|
| C2a-court | 2214 | prof 1–4, n=400 | évaluation a+b |
| C2a-prof6/8/10 | 2215 | 3 cellules × n=400 | évaluation a+b |
| C2b-select | 2216 | prof 1–4 SEUL, n=400 | sélection b (court-seulement) |

Anti-doublons : signatures strictes excluant E5v2_train+dev + data/v21/* +
data/v22/* (aucune signature partagée avec toute décision antérieure) ;
unicité globale des graphes exacts ; étiquettes usage (eval_only /
selection_only) par ligne ; manifeste data/manifest_c2data.json.

## C2-a — confirmer le système actuel (3 seeds/voie)

- Entraînements : A2-s18, A3-s18, A2-s19, A3-s19 — recettes AMENDEMENTS
  inchangées, MÊME init bundle, MÊME sélection 2213 (le système confirmé
  EST le système actuel, sélection mixte comprise), seule la seed varie
  (ordre données + dropout). Configs hashées avant start.
- Éval : 3 paires (s17 existante + s18 + s19) sur C2a-court + C2a-prof.
- **Hypothèse primaire PRÉFIXÉE** : cellules profondes POOLÉES (6+8+10,
  n=1200/paire), Δ(A2−A3) = moyenne par groupe des deltas moyens par seed
  (appariement même problèmes × seeds, groupé par base_group_id, bootstrap
  groupé 2000) **> 0 avec IC bas > 0**.
- Secondaires : tableau par cellule × par seed + dispersion inter-seeds ;
  non-régression court PRÉFIXÉE : A2 court moyen ≥ 0.93 ; distribution des
  marges top-2 publiée (reco QA REG-84) ; A2 vs direct-V2.1 descriptif.
- Verdict : PASS / PARTIEL (IC contient 0) / FAIL, selon règles figées ;
  publication dans tous les cas.

## C2-b — extrapolation aveugle (sélection court-seulement)

- Entraînements : A2-s20-blind, A3-s21-blind — recettes inchangées, MÊME
  data (déjà court-seulement), sélection sur **C2b-select (2216)** —
  aucune profondeur >4 n'entre dans le choix de checkpoint.
- Éval : sur C2a-prof6/8/10 (+ C2a-court pour non-régression).
- **Critères PRÉFIXÉS** : primaire = c_prop profond poolé d'A2-blind :
  ≥ 0.90 = extrapolation LARGEMENT RÉUSSIE ; 0.70–0.90 = PARTIELLE ;
  < 0.70 = LIMITÉE. Secondaires : Δ vs A2-full (descriptif, init non-aveugle
  déclaré), non-régression court ≥ 0.90, dispersion, marges.
- Les deux verdicts sont publiés même en échec (« système confirmé,
  extrapolation limitée » = résultat valide — mandat).

## Chaîne d'exécution (nuit, ~8 h, un job GPU à la fois)

génération (CPU ~15 min) → A2-s18 → A3-s18 → A2-s19 → A3-s19 →
[A2-s20-blind → A3-s21-blind] → évals C2-a puis C2-b → rapport consolidé.
Chaque étape : registre start/finish + logs persistants. Si une étape
échoue : documenter, continuer la chaîne (les FAIL font partie de la
science — mandat). Anomalie bloquante majeure seule interrompt tout.
