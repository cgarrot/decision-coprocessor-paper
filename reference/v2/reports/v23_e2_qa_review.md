# QA V2.3-E2 (32 évals + 4 portes) — recalcul

- 2026-09-26, @ag-4. Commit `f7598fcf`. Preuves : `scripts/qa_e2_review.py`,
  `reports/qa_e2_metrics.json`.

## Chiffres validés
- **A2-E2 L2-inv variante : 0.9375 / 0.94** (s22/s24) vs E1 0.545 → récupération
  confirmée ; porte s22 = **0.9375 ≥ 0.70** ✓ (400 items, marges).
- **Δ(A2−A3) POSITIF partout** : 16/16 cellules×paires de seeds (0.030→0.090) —
  renversement E1 inversé ✓ (A3 L2-inv var 0.87/0.8675).
- **Mixture** : sha `ff8f3504…` = manifeste, 2049 items, recette figée ✓.

## Nuance sur « sans aucune régression »
Comparaison A2-E2 (s22) vs A2-E1 : L1a −0.1/−0.5 pt ; L2-inv canon −0.3 pt ;
L2-inv var **+39.3 pts** ; L3-adv +0.2/+0.3 pt ; **L3-lbl −2.2/−1.2 pts**
(E2 ~0.95 vs E1 ~0.965–0.97). Donc : **aucune régression significative ; léger
recul L3-lbl (~1–2 pts)** à publier comme tel (le mot « aucune » est trop fort).

## Comptes
- **32 évals officielles** (4 seeds × 4 cellules × 2 rendus) + **4 de porte**
  (`e2_s22_a2_L1a_var`, `e2_s22_a2_L2inv_can`, `e2_s22_a2_L2inv_var`,
  `e2_s23_a3_L2inv_var`), pas 3.

## Verdict
**E2 PASS VALIDÉ** : porte franchie, récupération des inversions, A2 > A3 sur
toutes les cellules, non-régression à ~1–2 pts près (L3-lbl). E3 peut suivre.
