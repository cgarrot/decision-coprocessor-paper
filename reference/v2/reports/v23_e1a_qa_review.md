# QA V2.3-E1-L1-a — recalcul Q1/Q2/Q3, appariement, parser

- **Date :** 2026-09-26, @ag-4. **Commit/registre :** `3aa37b3b` (finish
  12:06:39), figage `V2.3-E1a` 11:41:47 (avant génération 11:44).
  **Artefacts :** `runs/c2_eval/c23_*` (12 évals), `data/c23/*`,
  `reports/p_cell_l1a.json`, `reports/qa_e1a_metrics.json`.

## 1. Recalcul indépendant — verdicts validés

| mesure | QA (recalcul) | rapport | accord |
|---|---|---|---|
| Q1 A2 variante (3 seeds) | **1.0000 / 1.0000 / 1.0000** | 1.0000 ×3 | ✓ |
| A2 canonique (moyenne) | 0.9975 / 0.9975 / 1.0000 → 0.9983 | 0.9983 | ✓ |
| A3 variante | 0.9375 / 0.9475 / 0.9675 (moy. 0.9508) | 0.9508 | ✓ |
| Q2 A2 appariée (variante−canonique) | **+0.25 / +0.25 / 0.00 pt**, IC [0.00,+0.75] | −0.25 pt IC [−0.75,0.00] | ⚠️ signe (R-E1a-1) |
| Q3 Δ(A2−A3) variante | **+6.25 / +5.25 / +3.25 pts** | idem | ✓ |
| Parser (2 rendus) | **1.000/1.000** (recouvrement/accord, recalcul direct) | idem | ✓ |

**Seuils figés (addendum @ag-1 59862077)** : Q1 plancher L1 = 0.9483 →
**PASS** (plafond) ; Q2 seuil L1 « drop > 10 pts = plomberie » → **PASS**
(aucune dégradation, +0.25 pt) ; Q3 descriptif au L1 (primaire = Q2 au L2)
→ positif. **A2 tient L1-a sans dégradation — verdict validé.**

## 2. Appariement et contrat de génération — OK

- 400 groupes, **graphes/réponses/traces identiques 400/400**, textes
  différents 400/400, profondeurs 100×(1,2,3,4).
- Scan programmatique des interdits : **pas de pronoms d'entité** (les 105
  occurrences de « il » = inversion « aboutit-il ? ») ; **polarité négative
  héritée des templates** (« rien ne suit », « Aucun ») présente dans les
  **deux** rendus → la formulation « sans négation » doit se lire « aucune
  négation AJOUTÉE par la transformation » (R-E1a-3).
- Revue humaine 30/30 au start (registre) ; marges `marge_top2` archivées par
  item ✓ ; loader assert 100 % (l.47/73) + `ckpt_sha` par éval ✓.

## 3. Corrections à demander

- **R-E1a-1 (A2, signe/convention)** : le delta apparié réel est
  **+0.25 pt (variante − canonique)** — la variante corrige 1 item de plus sur
  s17/s18 (s19 : 0). Le rapport écrit −0.25 pt avec IC miroir : nommer la
  convention (canonique − variante) ou corriger le signe.
- **R-E1a-2 (A3, non reproductible)** : comptes QA = canonique 374/373/370 vs
  variante **375/379/387** → Δ(variante−canonique) = **+0.25 / +1.50 /
  +4.25 pts** (poolé **+2.0 pts**) ; le rapport donne −0.25 pt
  IC [−3.25,+2.75] → recalculer Q2 A3 (le signe seul n'explique pas l'écart)
  et publier les comptes par seed. **A3 s'améliore aussi sur L1-a.**
- **R-E1a-3** : scoper « sans négation » (polarité héritée des templates).
- **R-E1a-4 (process)** : mon gate « validation du préenregistrement AVANT
  génération » n'a pas été demandé (figage bien enregistré 11:41:47 avant
  génération, mes seuils intégrés 11:37) → **validation rétroactive faite
  ici, sans impact** ; pour E1-L2, merci de passer la porte QA **avant** la
  génération.

## 4. Verdict

**E1-L1-a VALIDÉ** (A2 tient, plafond ; parser intact — résultat informatif
publié tel quel) avec 4 correctifs documentaires, dont 1 chiffre à recalculer
(A3 Q2). Le vrai test reste L2 (où le parser doit casser par construction).

---

*QA @ag-4 — preuves : `scripts/qa_e1a_review.py`, `reports/qa_e1a_metrics.json`.*
