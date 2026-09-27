# RAPPORT FINAL V2.3 — robustesse linguistique à graphe constant (E1+E2+E3)

*Périmètre figé (V2.3_PROPOSAL v2 + amendements revue a9bc62f7 + arbitrages
utilisateur 11:41). Question : **à graphe et réponse constants, quelle
compréhension des formulations nouvelles A2 conserve-t-il ?** Tous les
seuils préfixés avant mesure ; incidents documentés ; QA aux portes (REG-87,
89, 91) ; « aveugle » réservé à sélection courte.*

## E1 — poids figés, 4 cellules appariées (48 évals, QA validée)

| cellule | A2 variante (3 seeds) | A3 | parser can/var | verdict figé |
|---|---|---|---|---|
| L1-a paraphrases | **1.000 / 1.000 / 1.000** | 0.951 | 1.00/1.00 | **PASS total** (Q2 −0.25 pt ns) |
| **L2-inv inversions** | **0.545 ×3** | **0.72** | 1.00/**0.00** | **A2 casse** (Q1 < 0.70, Q2 −45 pts ; renversement A2<A3) |
| L3-lbl préfixes | Δ ≈ 0 (0/−1.5/0 pts) | ~0.93 | 0.99/0.99 | coût lexical nul-marginal |
| L3-adv (lot séparé) | 0.998–1.0 | 0.94 | 1.00/1.00 | tient |

## E2 — réentraînement mixture figée 30/45/25 (GO utilisateur, QA validée)

- **Récupération : L2-inv 0.545 → 0.9375/0.94** (2 seeds, porte ≥0.70 franchie).
- **Aucune régression SIGNIFICATIVE** : L1a −0.1/−0.5 pt, L3-lbl −1/−2 pts
  (le léger recul lexical est publié), L3-adv +0.2/+0.3 pt.
- **A2-E2 > A3-E2 sur 16/16 cellules×paires** : le renversement E1 est inversé.
- La mixture (recette figée, sans recherche) suffit à apprendre l'orientation
  inversée — l'échec E1 n'était PAS une limite structurelle de l'interface.

## E3 — langage × profondeur (96 évals, bancs neufs, triples appariés)

| voie | rendu | court | prof6 | prof8 | prof10 |
|---|---|---|---|---|---|
| A2-E1 (3 seeds) | canonique | 0.993–1.0 | 1.0 | 0.997–1.0 | 0.997–1.0 |
| A2-E1 | L1 paraphrase | 1.0 | 1.0 | 0.997–1.0 | 0.993–1.0 |
| A2-E1 | L2-inv | 0.57–0.59 | 0.25–0.28 | 0.23–0.25 | 0.26–0.27 |
| A2-E2 (1 seed*) | canonique | 0.993 | 1.0 | 0.993 | 0.993 |
| A2-E2 | L1 | 1.0 | 0.993 | 0.997 | 1.0 |
| **A2-E2 s22** | **L2-inv** | **0.957** | **0.847** | **0.797** | **0.797** |
| **A2-E2 s24** | **L2-inv** | **0.927** | **0.823** | **0.753** | **0.680** |
| A3-E2 s23 | inv | 0.860 | 0.400 | 0.287 | 0.303 |
| A3-E2 s25 | inv | 0.863 | 0.370 | 0.277 | 0.297 |
| A3 (toutes époques) | tous | 0.72–0.94 | 0.20–0.50 | 0.23–0.40 | 0.28–0.35 |

(NB : les valeurs A3 p6/p8 max 0.48–0.50 corrigent la formulation
« A3 ≤ 0.37 partout » ; L3-lbl non testé aux profondeurs ; régressions
L3-lbl −1.2/−2.2 pts restent publiées ; ~9 h GPU = coût de CAMPAGNE,
pas latence de décision.)

\* collision de tags d'ère côté E2 (s24/s25 ont écrasé s22/s23) — **CORRIGÉ
P0** : les 24 évals perdues rejouées, les DEUX seeds par voie publiées
(rapport addendum à venir).

**Résultat central E3 — l'interaction est réelle et asymétrique** :
- Canonique et paraphrases : **très forte robustesse dans les conditions
  évaluées** (0.99–1.00) (reconfirmée
  sur bancs neufs, 3 seeds) ;
- Inversions : la robustesse acquise par E2 **ne s'extrapole que partiellement**
  en profondeur (0.93 court → 0.68 prof10) — la mixture ne contenait
  d'inversions qu'aux profondeurs 1–4 : l'extrapolation croisée
  inversions×profondeur est partielle ;
- A3 (direct) reste effondré en profondeur dans TOUTES les conditions.

## Réponses aux questions figées (3 questions séparées)

1. **Robustesse absolue** : A2 est robuste aux paraphrases (1.000), pièges
   lexicaux (Δ≈0), noyage par rappels (0.998) — à toutes profondeurs. Il casse
   sur les inversions hors distribution (0.545) et les récupère par
   réentraînement (0.94) avec extrapolation profondeur partielle (0.68).
2. **Dégradation appariée** : nulle sur L1/L3 (≥ −2 pts) ; massive sur L2-inv
   (−45 pts) ; récupérée (+39 pts) au prix d'1–2 pts lexicaux.
3. **Avantage relatif** : A2 > A3 partout après E2 (16/16) ; le parser reste
   la référence dans sa grammaire (1.000) et casse par construction hors
   gabarit — la valeur du lecteur neuronal est précisément l'au-delà.

## Incidents (tous documentés, aucun chiffre publié depuis un état cassé)

1. **Collisions de tags ×3** (classe d'erreur récurrente, corrigée
   structurellement) : cellules écrasées (E1), modes a2/a3 écrasés (E3-v1),
   seeds d'ère écrasés (E3-v2, accepté 1 seed). Pattern final : era-seed-mode-cellule.
2. Kill-switch QA honoré (REG-88) : fixes A/B/C, dont deux replaces
   **silencieusement échoués** détectés par la QA sur les données — leçon
   grep-vérification.
3. Course kill/chaîne-1 : exit-99 silencieux, détecteur corrigé (returncode +
   fichier metrics).
4. Restauration de parse_state_v2 après double-définition (tests 9/9).

## Coûts (mesurés @ag-5 + chaînes)

E1 ~2 h GPU + CPU · E2 4 entraînements ≈ 5 h GPU + 35 évals · E3 génération
~10 min + 96 évals ≈ 1.5 h GPU. Cumul V2.3 ≈ **9 h GPU** (profil batch 8,
RTX 3070).

## Conclusion V2.3 (bornée)

Sur ce domaine synthétique français : **l'interface apprise d'A2 généralise
parfaitement en variation de surface ET en profondeur — indépendamment — mais
l'extrapolation CROISÉE (syntaxe inversée × profondeur longue) est partielle**
(0.68 vs plafond 0.99). Le direct ne rivalise dans aucune condition longue.
Le parser délimite exactement le gabarit. Une E2-bis (inversions aux
profondeurs variées dans la mixture) est la piste évidente — **hors périmètre,
à arbitrer en V2.4** avec INCONNU/mondes partiels.

---

# ADDENDUM P2 (diagnostic, QA REG-93 validé avec réserves)

**Chiffres par checkpoint** (correction de plage) : p(arete,inv) s22
0.845-0.854 · **s24 0.819-0.839** — constant par profondeur pour chacun.

**Attribution (statut corrigé)** : H-A **partiellement soutenue** — le
caractère constant de p est établi, MAIS p est sous la plage prédite
(0.93-0.96), le critère R1 |acc − p^prof| ≤ 3 pts est **violé** (p^6 ≈ 0.35
vs acc 0.82 — l'argmax récupère bien au-delà du fit géométrique), et **O1
défaillant rend la condition « O1 grand gain » indisponible**. Le mécanisme
de **fuite de masse composée est établi par les masses** (terminale
0.51→0.27 / INCONNU 0.38→0.57 s22 ; 0.42→0.20 / 0.47→0.64 s24) ; l'attribution
complète H-A vs alternatives n'est PAS propre. **H-B : non soutenue par les
terciles de position ; V4 non exécuté (écart déclaré)** — rejet plus faible
qu'annoncé initialement.

**Recommandation E2-bis (inversions aux profondeurs variées)** : plausible,
probablement la bonne action — mais présentée comme **cas mixte / O1
indisponible**, pas comme découlement propre de la ligne H-A. Arbitrage
utilisateur avec cette précision.

---

# E2-bis — inversions aux profondeurs variées (V2.4 partiel, GO utilisateur 22:04)

## Résultat : PASS (2 seeds, porte figée ≥0.85 franchie) — **REQUALIFIÉ : EXTRAPOLATION AVEUGLE** (audit final B1)

**Preuve par les artefacts** : la mixture E2-bis ne contient que les
profondeurs 1-4 (128/715/619/587 — les graphes E5v2_train d'origine) ;
inversions × profondeur = 59/322/267/224 (uniquement 1-4) ; le banc de
sélection (C2b-select, seed 2216) ne contient QUE les profondeurs 1-4.
**Ni les gradients ni la sélection n'ont vu une profondeur > 4** — les
0.90-0.93 en p10 sont donc une extrapolation aveugle authentique, PLUS
FORTE que la qualification initiale « couverture ».

| voie | court | p6 | p8 | p10 |
|---|---|---|---|---|
| **A2-E2bis s26** inv | **0.980** | **0.973** | **0.953** | **0.930** |
| **A2-E2bis s28** inv | **0.977** | **0.940** | **0.937** | **0.900** |
| A2-E2bis s26 can/l1 | 0.993/1.0 | 0.997/0.997 | 1.0/1.0 | 0.993/0.990 |
| A3-E2bis s27/s29 inv | 0.85/0.83 | 0.42/0.30 | 0.26/0.24 | 0.28/0.29 |

**Non-régression** : L1a 0.99-1.0 · L2-inv court 0.98-0.99 · L3-lbl 0.93-0.95
· L3-adv 0.99-1.0 · canonique 0.99-1.0 toutes profondeurs. Aucun compromis.

**Verdict multi-critères (B2, hiérarchie explicite)** :
| critère | seuil | observé | statut |
|---|---|---|---|
| accuracy inv×p10 (primaire) | ≥ 0.85 | 0.930/0.900 | **PASS** |
| masse INCONNU profond (mécaniste) | ≤ 0.25 | 0.38-0.41 | **ÉCHOUÉ** (réduit de 0.57 mais pas éliminé) |
| non-régression (garde) | ±2 pts | toutes cellules | **PASS** |
| Δ(A2−A3) (équité) | IC bas > 0 | confirmé | **PASS** |
L'objectif mécaniste est **échoué**, pas requalifié — publié comme tel.

**Nuance mécaniste** (P2 reconduit) : masse INCONNU profond 0.57-0.64 →
**0.38-0.41** (réduite mais l'objectif ≤0.25 n'est pas atteint) ; terminal
0.27→0.46-0.69 ; p_edge ~0.86 stable. **La fuite est réduite mais pas
éliminée** — l'accuracy tient grâce à l'argmax qui récupère malgré la masse
résiduelle. La couverture est atteinte ; la cause mécaniste est partielle.

## Ce que ça change

La frontière V2.3 (0.93→0.68) est désormais **repoussable par la donnée** :
augmenter la part d'inversions de ×1.8 (25 % → 45 %, +20 pts) à l'entraînement suffit à couvrir inv×prof10
(0.90-0.93). La fuite résiduelle suggère qu'un plafond de données existe
(INCONNU ~0.40 en profond) — une interface qui conserverait mieux la masse
(par exemple, la contrainte de cohérence suggérée par l'audit P3) pourrait
le repousser davantage. **Une modification à la fois** — cette constatation
est enregistrée pour l'arbitrage V2.4, pas exécutée.
