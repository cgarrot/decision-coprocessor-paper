# QA C2 — verdicts recalculés, incident >512, checkpoints, marges

- **Date :** 2026-09-26, @ag-4. **Commit audité :** `e7e7165b`.
  **Artefacts :** `reports/c2_final.md`, `V22_C2_PROTOCOL.md` (sha `6dd53719`,
  registre 22:20:49), `runs/c2_eval/` (8 évals), `reports/qa_c2_metrics.json`.
- **Méthode :** recalcul depuis les preds archivées (CPU), checks d'exclusion,
  sha/loader des checkpoints.

## 1. Verdicts — VALIDÉS

| verdict | recalcul QA | fichier officiel | accord |
|---|---|---|---|
| C2-a s17 Δ profond poolé | **+65.304 pts** IC [+62.55,+67.97] | +65.30 [+62.6,+68.1] | ✓ |
| C2-a s18 | **+64.053** [+61.38,+66.89] | +64.05 [+61.3,+66.8] | ✓ |
| C2-a s19 | **+68.140** [+65.55,+70.64] | +68.14 [+65.6,+70.9] | ✓ |
| C2-b A2-blind poolé | **0.98666** (item-poolé) | 0.98665 | ✓ (≥0.90) |
| C2-b A3-blind | **0.27106** | 0.27102 | ✓ |
| dispersion A2 deep (3 seeds) | 0.994996 / 0.998332 / 0.998332 → **0.334 pt** | 0.33 pt | ✓ |
| non-rég court A2 (moyenne) | **0.99917** | 0.9992 | ✓ |

IC bas > 0 sur les 3 seeds ; verdicts **PASS C2-a** et **LARGEMENT RÉUSSIE
C2-b** confirmés. Convention à nommer (R-C2-2) : le « poolé » du fichier est la
**moyenne des 3 accuracies de cellule** ; le pool par item (QA) diffère de
~2e-6 (prof10 n=399) — sans effet.

## 2. Incident >512 — exclusion VALIDÉE, cause à CORRIGER (R-C2-0)

- Vérifié sur l'item `v21-C2a-prof10-00045-bb0513ff` : **lecteur 484 tokens ;
  prompt direct `collate_direct_text` = 518 > 512** → exclusion justifiée
  (consommateur max), appliquée **identiquement** : prof10 n=399 dans les
  **8 évals**, un seul item, aucun autre écart de population.
- ⚠️ **La cause rapportée est inexacte** : le générateur n'assertait PAS « le
  texte lecteur » — `tok_len` lit bien `state+question+options`, mais avec un
  **rendu différent** du consommateur (`Options :\n- …`) :
  **tok_len = 511 (passe)** vs **collate direct = 518 (+7)**. Le vrai écart est
  **rendu générateur ≠ rendu consommateur**, pas lecteur vs direct.
  → À corriger dans `c2_final.md`/erratum ; pour C3, faire vérifier la limite
  par le **collate réel du consommateur max** (ou répliquer son rendu).
- Claim « rejouées population commune (écarts ≤ 0.2 pt) » : les origines
  pré-exclusion ne sont pas archivées → non vérifiable ; la population commune
  l'est (n identiques).

## 3. Checkpoints — VALIDÉS

- **sha256 8/8** conformes aux `metrics.json` (dont s17 = paire V2.2 réutilisée).
- Assertions de chargement **100 % (clés + valeurs)** dans `run_c2_eval.py`
  (l.46-47) ; **échantillon structurel QA** A2-s18 (224/224 + extracteur OK)
  et A3-s18 (224/224 + tête stricte OK), format `pm.state_dict` `.default`.
- Toolchain des évals : **torch 2.5.1+cu121** stampé (= environnement de mes
  vérifications C1/C2) ; entraînements sous 2.14 (venv) — séparation notée.

## 4. Marges top-2 — ABSENTES (réserve R-C2-1)

Le protocole (C2-a secondaires + C2-b) promet la « distribution des marges
top-2 publiée (reco QA REG-84) » : **aucun artefact** (`*prob*`/`*marge*` = 0),
preds limitées à `answer+ok` → non recalculable. Action : archiver les probas
par item (comme C1/R-A) et publier les marges, ou amender le protocole.

## 5. Verdict QA global

**C2-a PASS et C2-b LARGEMENT RÉUSSIE : VALIDÉS sur les chiffres** (recalcul
identique, exclusions uniformes, loaders 8/8). Corrections documentaires :
R-C2-0 (cause de l'incident), R-C2-1 (marges top-2), R-C2-2 (nommer la
convention « poolé »), R-C2-3 mineur (preuve avant/après exclusion non
archivée). Aucune n'affecte les conclusions.

---

*QA @ag-4 — preuves : `scripts/qa_c2_review.py`, `reports/qa_c2_metrics.json`.*
