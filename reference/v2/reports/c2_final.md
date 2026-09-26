# RAPPORT C2 — confirmation + extrapolation aveugle (nuit du 25/26-09)

*Protocole V22_C2_PROTOCOL.md figé AVANT génération (7b7e7d19). GO « ab »
utilisateur 22:20. Règles préfixées, autonomy complète, incidents publiés.*

## Verdicts officiels (règles figées)

### C2-a — CONFIRMATION DU SYSTÈME : **PASS**

Hypothèse primaire préfixée : Δ(A2−A3) profond poolé (prof 6+8+10) > 0,
IC bas > 0, apparié par base_group_id, bootstrap groupé 2000 :

| seed | Δ profond poolé | IC95 |
|---|---|---|
| s17 (paire existante) | **+65.30 pts** | [+62.6, +68.1] |
| s18 | **+64.05 pts** | [+61.3, +66.8] |
| s19 | **+68.14 pts** | [+65.6, +70.9] |

**Δ moyen 3 seeds : +65.83 pts, IC bas > 0 sur les trois.** Non-régression
court : A2 court moyen 3 seeds = (0.9975+1.000+1.000)/3 = **0.9992** ≥ 0.93 ✓.
**Dispersion inter-seeds A2 (profond poolé) : 0.9950 / 0.9983 / 0.9983**
(écart max 0.33 pt — réplication quasi parfaite). A3 (direct+aux) reste
effondré en profondeur sur les trois seeds (0.342/0.358/0.317 poolé).

### C2-b — EXTRAPOLATION AVEUGLE : **LARGEMENT RÉUSSIE**

Critère préfixé ≥ 0.90 = largement réussie :

| | court | prof6 | prof8 | prof10 | **profond poolé** |
|---|---|---|---|---|---|
| **A2-s20-blind** (sélection court-seulement, 2216) | 0.9950 | 0.9825 | 0.9950 | 0.9825 | **0.9867** |
| A3-s21-blind | 0.9475 | 0.3225 | 0.2625 | 0.2281 | 0.2710 |

**La revendication tient : l'invariance en profondeur s'acquiert SANS JAMAIS
sélectionner sur la profondeur** (rappel : E5v2_train ne contient que les
profondeurs 1–4 — les gradients non plus ne l'ont jamais vue). Le direct,
même à sélection aveugle, reste effondré.

## Table complète (population commune, exclusions appliquées)

| voie | seed | court | prof6 | prof8 | prof10 | poolé |
|---|---|---|---|---|---|---|
| A2 | 17 | 0.9975 | 0.9975 | 0.9950 | 1.0000 | 0.9950 |
| A2 | 18 | 1.0000 | 0.9975 | 0.9975 | 1.0000 | 0.9983 |
| A2 | 19 | 1.0000 | 0.9975 | 0.9975 | 1.0000 | 0.9983 |
| A3 | 17 | 0.9350 | 0.3400 | 0.2825 | 0.3183 | 0.3419 |
| A3 | 18 | 0.9375 | 0.4725 | 0.2825 | 0.3183 | 0.3578 |
| A3 | 19 | 0.9600 | 0.3925 | 0.2850 | 0.2732 | 0.3169 |
| A2-blind | 20 | 0.9950 | 0.9825 | 0.9950 | 0.9825 | 0.9867 |
| A3-blind | 21 | 0.9475 | 0.3225 | 0.2625 | 0.2281 | 0.2710 |

## Incident de la nuit (documenté, corrigé, à valider QA)

**Écart de génération** : 1 item de C2a-prof10 (…00045-bb0513ff) mesurait
484 tokens au lecteur et **518 au prompt direct** > 512 → collate_direct_text
a échoué bruyamment (design) sur les 3 évals A3 de la nuit. **Cause exacte
(corrigée sur identification QA REG-86)** : le générateur mesurait bien
state+question+options (511 ≤ 512 ✓) mais avec un **rendu différent** de
celui du consommateur (format `Options :\n- …` du collate direct, +7
tokens) — l'écart est un **rendu générateur ≠ rendu consommateur**, pas une
mesure lecteur-seule. Pour tout banc futur : vérifier la limite via le
collate RÉEL du consommateur max.
**Correctif** : exclusions id-par-id identiques pour toutes les voies
(data/c2/exclusions_direct_gt512.json, 1/2000 items), les 8 évals rejouées
sur population commune (A2 inclus). Convention « profond poolé » : moyenne
des exactitudes des 3 cellules profondes, chacune sur ses items communs
(≠ pool par item ; écart ~2e-6, QA REG-86).
Registre : écart consigné, déviation mineure selon règle préexistante,
validation QA @ag-4 demandée.

## Coûts de la nuit

6 entraînements ~70 min chacun (sous verrou, séquentiels) + 8 évals
~40 s/chacune ≈ 7 h GPU au total. Logs : runs/c2*/train_log.txt,
/tmp/c2_night.log (chaîne), registre par étape.

## Conclusion consolidée (a + b)

1. **Le système A2 est confirmé sur seeds neuves et bancs neufs** :
   Δ moyen +65.8 pts vs contrôle équitable, IC > 0 partout, dispersion
   inter-seeds ≤ 0.33 pt.
2. **Son invariance en profondeur est une EXTRAPOLATION AVEUGLE authentique**
   (0.9867 sans jamais sélectionner — ni entraîner — sur la profondeur).
3. Le contrôle A3 (direct + supervision égale) reste effondré dans toutes
   les configurations (0.27–0.36 poolé) : la conclusion architecturale
   de V2.2 est répliquée sur données et seeds neuves.


## Marges top-2 (R-C2-1, convention : AGRÉGÉE court+deep, n=1599/voie)

| voie | médiane | p05 | part ≤1e-2 |
|---|---|---|---|
| A2 s17 | 0.9963 | 0.9413 | 0.31 % |
| A2 s18 | 0.9955 | 0.8723 | 0.13 % |
| A2 s19 | 0.9914 | 0.9031 | 0.06 % |
| A2 s20-blind | 0.9882 | 0.0639 | 1.25 % |
| A3 s17 (TOUTES cellules) | 0.9631 | 0.1121 | 0.50 % |
| A3 s21-blind (toutes) | 0.8334 | 0.0601 | 0.88 % |

**Deep SEUL** (la vraie fragilité, non diluée par le court — QA REG-86) :
A2 s19 deep médiane 0.9889, ≤1e-2 0.08 % ; A2 s20-blind deep ≤1e-2 1.50 %.
NB : « A3 s17 médiane 0.963, p05 0.11 » = TOUTES cellules — le court A3
seul est médiane 1.0 / p05 0.59 (micro-libellé corrigé).
