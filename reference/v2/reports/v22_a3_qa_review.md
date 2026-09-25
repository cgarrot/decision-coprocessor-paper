# QA V2.2-A3 (direct à supervision auxiliaire ÉGALE) — recalcul + verdict

- **Date :** 2026-09-25, @ag-4. **Commit :** `18bc1ff5`. **Artefacts :**
  `runs/v22_a3/` (best.pt, metrics.json, train_log.txt), `runs/v22_a3_eval/`
  (8×`pred_a3` + `a3_eval_verdict.json`), `configs/v22_a3.yaml` (sha `4e8e7fe6`
  = `config_sha256` du run).
- **Méthode :** recalcul depuis prédictions archivées + check structurel CPU
  du checkpoint. Spec : `V22_A3_SPEC.md` (sha `2f58f02b`, prereg validée
  REG-77).

## 1. Recalcul 8/8 — Δ(A2−A3) positif IC bas > 0 partout

| Banc | A3 acc | Δ(A2−A3) pts [IC QA] | Δ(A3−direct) pts [IC QA] |
|---|---:|---|---|
| B1-court | 0.9625 | **+3.25** [+1.50,+5.25] | +2.50 [+0.25,+4.75] |
| B2-prof6 | 0.4925 | **+50.50** [+45.50,+55.50] | −3.25 [−8.50,+2.25] |
| B3-prof8 | 0.2475 | **+75.00** [+70.50,+79.01] | −3.25 [−8.50,+1.75] |
| B4-prof10 | 0.2825 | **+71.50** [+66.75,+75.76] | −2.50 [−7.75,+2.75] |
| B5-surface | 0.9575 | **+4.25** [+2.25,+6.25] | +1.75 [−0.25,+3.75] |
| B6-distract | 0.9450 | **+5.50** [+3.49,+7.75] | +0.75 [−1.25,+2.75] |
| B7-options | 0.9600 | **+3.50** [+1.50,+5.50] | +2.00 [0.00,+4.00] |
| B8-depart | 0.8550 | **+14.25** [+10.75,+18.00] | +1.50 [−1.50,+4.75] |

- **Identique au verdict** (écarts IC ≤ 0,5 pt, graines bootstrap) ; 0 désaccord
  QA/flag `ok`.
- **Règle figée appliquée PAR BANC** : 8/8 « A2 supérieur architectural
  (IC>0) » — conforme à ma nuance REG-77 (aucune globalisation).
- **Pas de saturation** : A2 0.9975 vs A3 0.2475–0.2825 aux profondeurs
  6/8/10 → la comparaison sépare bien les voies.
- **A3 ≈ direct V2.1** (court : +2.5 B1 IC>0 ; profondeur : −2.5/−3.25 pts,
  IC contient 0) : **la supervision auxiliaire seule ne répare pas la
  profondeur ; c'est la propagation qui porte le gain.**

## 2. Checkpoint / loader — vérifié

- `best.pt` : `lora` (224), `answer` (12), `relations`, `config`, `step=800`,
  `selection={acc 0.6775, nll 2.168}`.
- **LoRA 224/224 clés exactes**, 0 unexpected ; **`head.load_state_dict` strict
  OK** (dims `d_model 64 / hidden 128`, conformes à `configs/v22_a3.yaml`) ;
  loader avec assertions `.default` (leçon A2) présent dans le harnais.

## 3. Sélection / scellés / incidents

- Sélection **2213** : `S-selection.jsonl` sha `7089876d…` = `selection_sha256` ;
  trace pas-à-pas dans `train_log.txt` (100→1200) ; **best@800, accuracy
  0.6775** (primaire accuracy, tie-break NLL non exercé) ; plateau 0.61–0.68,
  switch β@600 sans déclic — cohérent avec le récit.
- **Bancs V2.1 scellés** : éval pure (git clean), aucun usage en sélection.
- Incidents annotés : kill outil au lancement (aucun step), fix
  `encode→self.adapter.encode` (commit `024fd338`).

## 4. Conclusion

**Supériorité architecturale de la propagation VALIDÉE, par banc, 8/8**
(Δ(A2−A3) > 0, IC bas > 0 partout), sans saturation. À publier : table 8/8
complète, revendication **par banc** ; noter que l'écart est massif en
profondeur (50–75 pts) et plus modeste à court (+3.25 à +5.5 pts) — mais
IC>0 à chaque fois. Réserves mineures (héritées) : seuil d'assertion de
chargement 90 % (recommandé 100 % pour la suite) ; tête `relations` du
checkpoint inutilisée en inférence (documenté).

---

*QA @ag-4 — preuves : transcript de recalcul, check structurel checkpoint,
`runs/v22_a3*/*` ; entrée REG-78.*
