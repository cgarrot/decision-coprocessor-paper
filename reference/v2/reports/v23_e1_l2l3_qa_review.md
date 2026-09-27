# QA V2.3-E1 L2/L3 (36 évals) — recalcul + réserves

- 2026-09-26, @ag-4. Commit `a6d72bf5`. Preuves : `scripts/qa_e1_l2l3_review.py`,
  `reports/qa_e1_l2l3_metrics.json`.

## Chiffres validés (recalcul identique)

| cellule | A2 canon | A2 variante | A3 variante | Q2 A2 apparié | Q3 Δ(A2−A3) |
|---|---|---|---|---|---|
| L2-inv | 0.995/1.0/1.0 | **0.5450 ×3** | 0.7350/0.7000/0.7225 | **−45.0/−45.5/−45.5 pts** IC<0 | **−19.0/−15.5/−17.75** |
| L3-lbl | 0.9725/0.9600/0.9825 | 0.9775/0.9325/0.9750 | 0.9125/0.8850/0.9275 | +0.5/−2.75/−0.75 pts | +6.5/+4.75/+4.75 |
| L3-adv | 0.995/1.0/1.0 | **1.0/0.9975/0.995** | 0.9475/0.9325/0.9475 | +0.5/−0.25/−0.5 pt | +5.25/+6.5/+4.75 |

- **Parser** : L2-inv variante couverture **0.00** (P_eval INCHANGÉ ✓) ; L3-lbl
  0.9825/0.975 (labels parsables) ; L3-adv 1.0/1.0 — conforme à `p_cell_*`.
- **Limites réelles** : aucun item >512 (max direct 443 L3-lbl-can, reader 403).
- **Appariement** : L2-inv et L3-adv 400/400 graphes identiques ; usage
  `adversarial_separate` ✓ pour L3-adv.
- **Seuils figés** : Q1 L2 = 0.545 < 0.70 → **E2 ARMÉ** (GO utilisateur) ;
  Q2 L2 drop 45.5 pts ≫ 15 → échec ; L3 descriptif (plancher 0.50) → tenable ;
  Q3 L2 négatif = renversement A2<A3.

## Réserves

1. **R-L3lbl-1 (spec, à corriger)** : le **mapping L3-lbl n'est PAS partagé** —
   code committé (l.196-198) appelle `relabel_shared_prefix` deux fois avec le
   même `rng` → deux bijections différentes ; les données le confirment
   (canon `g759AX…` vs var `k719AX…`, **0/400 paires identiques**). Le « fix B
   (bijection unique) » annoncé **n'est pas implémenté**. → Implémenter le
   mapping unique (1 appel, appliqué aux deux) **ou** amender la spec en
   déclarant la conception réelle (deux tirages de renommage) — la conclusion
   « coût lexical ~2-4 pts » restera à réévaluer sous la conception figée.
2. **R-C-1** : le fix C (marge 505 / collate réel) **n'est pas dans le script**
   (l.190 : `tok_len` + `assert tl <= 512`). Sans conséquence ici (0 dépassement
   réel mesuré sur les 6 banques) mais à corriger pour l'avenir (R-C2-0).
3. **R-count** : **36 évals complets** (3 cellules × 12), pas 34 — préciser.
4. Incidents : exit-99/chaînes concurrentes → détecteur corrigé ; rejeu complet
   cohérent (marges présentes partout) ; crash A2 L2-inv levé (fix A vérifié
   par l'existence des preds + marges et la couverture P_eval 0.00).
