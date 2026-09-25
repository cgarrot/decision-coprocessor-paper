# QA V2.2-A2 (évaluation scellée B1–B8) — recalcul indépendant + arbitrage A3

- **Date :** 2026-09-25, @ag-4. **Commit :** `d299eb9a`. **Artefacts :**
  `runs/v22_a2/` (best.pt, metrics.json, train_log.txt), `runs/v22_a2_eval/`
  (8×`pred_prop` + `a2_eval_metrics.json` + `a2_eval_verdict.json` + log).
- **Méthode :** recalcul depuis prédictions archivées (aucun GPU/modèle pour les
  métriques) ; **check de chargement structurel CPU** du checkpoint.

## 1. Recalcul 8/8 — identique aux métriques

| Banc | c_prop | Δ vs discret [IC QA] | Δ vs direct [IC QA] |
|---|---:|---|---|
| B1 | 0.9950 | +19.50 [+15.25,+23.50] | **+5.75** [+3.25,+8.25] |
| B2 | 0.9975 | +33.00 [+28.25,+38.00] | **+47.25** [+42.50,+52.25] |
| B3 | 0.9975 | **+40.00** [+34.75,+45.00] | **+71.75** [+67.00,+76.25] |
| B4 | 0.9975 | +43.75 [+39.00,+48.75] | **+69.00** [+64.50,+73.25] |
| B5 | 1.0000 | +19.00 [+15.25,+23.00] | **+6.00** [+4.00,+8.50] |
| B6 | 1.0000 | +22.75 [+19.00,+27.00] | **+6.25** [+4.00,+8.75] |
| B7 | 0.9950 | +19.50 [+15.25,+23.50] | **+5.50** [+3.25,+8.00] |
| B8 | 0.9975 | +23.25 [+19.25,+27.50] | **+15.75** [+12.25,+19.75] |

- **Grille §8 (amendement) : PASS** — B3 Δ = +40.0 pts (≥ +5), IC bas
  +34.75 pts > 0 ✓ ; non-régression B1 +19.5 pts ✓. Contrôle baseline
  supplémentaire : c_prop B3 0.9975 ≥ A1-bis 0.8525 ✓.
- **Δ vs direct positif 8/8, IC > 0 partout** (le plus serré : B1 +5.75
  [+3.25,+8.25]). c_prop > plafond parser 0.95 ; B5/B6 = 1.000 (saturation).
- Écarts QA/harnais ≤ 0,8 pt sur les IC (graines bootstrap) ; 0 désaccord
  conceptuel.

## 2. Checkpoint et loader (incident `.default`) — VÉRIFIÉ

- `best.pt` : 224 clés LoRA + 55 clés extracteur. **Loader corrigé**
  (`pm.load_state_dict`, clés `pm.state_dict()` `.default`) :
  **224/224 clés exactes**, 0 unexpected (310 « missing » = poids de base hors
  adaptateur, normal). Extracteur : strict OK.
- **Incident reproduit** (preuve du bien-fondé du correctif) :
  `set_peft_model_state_dict` (ancien chemin) = **28/224** clés exactes →
  chargeait quasi à vide. Les assertions de chargement de `run_v22_a2_eval.py`
  couvrent le cas (seuil ≥ 90 % ; QA recommande 100 % pour les runs futurs).

## 3. Sélection (seed 2213) et scellés

- `selection = data/v22/S-selection.jsonl`, sha `7089876d…` = `selection_sha256`
  du run ✓ ; **aucun banc V2.1 dans la sélection** (train = E5v2_train +
  augmentation).
- Trace par step dans `train_log.txt` (100→1200) ; `selection_best` =
  **step 1200, c_prop 1.0, b_discret 0.7975** (critère c_prop puis b).
  ⚠️ La note de finish dit « best@600-700 » (= meilleur intermédiaire) : les
  artefacts font foi (step 1200) — correction de communication.
- **Bancs scellés intacts** : `data/v21` sans diff git ; évaluation pure.
- Incidents du run 1 (OOM GC + éval de sélection ancrée gold/predit) annulés et
  annotés ; run 2 = chiffres publiés.

## 4. Réserve mineure

`runs/v22_a2_eval/a2_eval_verdict.json` porte la clé **`verdict_A1bis`**
(copie de harnais) — la renommer `verdict_A2` ; le message annonçait
`runs/v22_a2/history.json` qui n'existe pas (la trace de sélection est dans
`train_log.txt` + `selection_best`).

## 5. Arbitrage A3 — **OUI** (avec conditions)

- §10 de l'amendement : toute **revendication de bénéfice** exige A3 (direct à
  tête auxiliaire **ÉGALE**). Les chiffres publiés revendiquent une supériorité
  (« domine le direct partout ») : sans A3, le gain **mélange architecture de
  propagation et supervision auxiliaire supplémentaire** (le lecteur A2 a été
  entraîné avec relations/états/INCONNU augmenté ; le direct de référence est
  le LoRA V2.1 sans ces cibles). C'est l'attaque d'audit la plus évidente.
- **Conditions** : spec A3 préenregistrée et hashée AVANT le run ; mêmes
  annotations/cibles auxiliaires, même augmentation, même recette LoRA,
  **même sélection (2213, critère primaire de la voie)** ; bancs V2.1 scellés en
  évaluation pure ; comparaison **A2 vs A3 appariée** (Δ, IC groupés) comme
  métrique primaire ; règle de conclusion figée : si A2 > A3 (IC>0) →
  supériorité architecturale ; sinon publication **descriptive** (l'avantage
  vient de la supervision/lecteur, pas de la propagation seule).
- **Saturation** : si A3 atteint aussi ~0.995+, la comparaison sera
  inconcluante sur ces bancs → à déclarer tel quel (pas de sur-interprétation).
- Coût ~1 h GPU sous verrou : acceptable ; le contraire laisse une faille
  d'équité dans la publication finale.

---

*QA @ag-4 — preuves : transcript de recalcul, check structurel checkpoint,
`runs/v22_a2_eval/*`, `runs/v22_a2/{metrics.json,train_log.txt}`.*
