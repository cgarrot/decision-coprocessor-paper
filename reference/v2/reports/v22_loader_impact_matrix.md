# V2.2 — MATRICE D'IMPACT DES LOADERS (C0, audit §8.1)

*Produit par @ag-4 (QA), 2026-09-25. Preuve : `scripts/qa_loader_manifests.py`,
sortie `reports/qa_loader_manifests.json` (valeurs comparées après chargement
sur modèle neuf, CPU).*

## 1. Manifestes (attendus / chargés / manquants / valeurs)

| checkpoint | format des clés | loader correct | exactitude valeurs | manquants/inattendus | loader erroné (preuve) |
|---|---|---|---|---|---|
| `bundle/reader_lora_best.pt` | peft-natif | `set_peft_model_state_dict` | **224/224 exactes, maxdiff 0** | 0 | `load_state_dict` : 0/224 (noms incompatibles) |
| `runs/v22_a2/best.pt` (lora) | `pm.state_dict` `.default` | `pm.load_state_dict(strict=False)` + **assert 100 %** | **224/224 exactes, maxdiff 0** | 310 (poids de base hors adaptateur, normal) | **`set_peft_model_state_dict` : chargement quasi-vide** (0–28/224 selon comptage) ← incident historique |
| `bundle/direct_lora_best.pt` | peft-natif | `set_peft_model_state_dict` | **224/224 exactes, maxdiff 0** | 0 | — |
| `runs/v22_a3/best.pt` (lora) | `pm.state_dict` `.default` | `pm.load_state_dict(strict=False)` + assert | **224/224 exactes, maxdiff 0** | 310 (base) | `set_peft` : quasi-vide |
| `bundle/executor_s_e4b_pad20.pt` | state_dict nu | `load_state_dict` strict | **28/28** | 0 | — |

Têtes : `direct_lora_best` (V2.1) state_dict **strict OK** ; A3 `answer`
12 tenseurs **strict OK** ; extracteur (lecteur) state_dict strict OK
(le `relations` d'A3 n'est pas utilisé en inférence, documenté).

## 2. Matrice `run → loader → correctif → replay / non affecté`

| run / résultat publié | checkpoint | loader utilisé | correctif nécessaire | statut replay / impact |
|---|---|---|---|---|
| E1–E4b (exécuteur S) | executor bundle | strict | non | non affecté (28/28 ; ancre (a)) |
| V2.1-Q1 (direct + pipeline E5v3-A) | bundle reader/direct | `set_peft` (format natif) | non | non affecté ; recalcul QA V2.1 indépendant déjà fait |
| A1 (publ. FAIL) | bundle reader | `set_peft` (correct) | non (bug = **tête** bilinéaire non supervisée, rétracté) | chiffres = artefact valide ; interprétation retirée |
| A1-bis (PASS) | bundle reader | `set_peft` (correct) | non | **replay item-level QA : R0-soft == A1-bis 400/400 ×8** (`qa_c1_metrics.json`) |
| A2 (PASS) — run 2 | `v22_a2/best.pt` | `load_state_dict` + assert 100 % | **OUI** (eval du run 1 chargeait à vide ; non publiée) | **replay item-level QA : R1-soft == A2 400/400 ×8** ; passe probs : assert 100 % + identité 400/400 ×8 |
| A3 (PASS) | `v22_a3/best.pt` | `load_state_dict` + assert | OUI (même correctif) | structurel 224/224 + head strict ; prédictions publiées après correctif |
| C1 (2×2) | les deux lecteurs | `load_state_dict` + assert 100 % (script l.67) | OUI (hérité) | **assertions internes R0-soft==A1-bis / R1-soft==A2 vérifiées item-level par QA** |
| A2-probs / borne routeur | `v22_a2/best.pt` | assert 100 % (probs), archives A2/A3 | OUI (hérité) | identité answer==publiée 400/400 ×8 ; oracle recalculé QA |

## 3. Portée et limites

- **Replay de processus neuf** : la QA vérifie les **valeurs chargées** (CPU) et
  l'**identité item-level** des prédictions entre runs (C1 ↔ publiés), mais ne
  peut pas rejouer un processus **GPU neuf** (CPU ≠ GPU, R7) : le replay GPU
  relève de l'exécuteur ; les assertions in-run 100 % + identités ci-dessus en
  tiennent lieu à ce stade.
- **Aucun résultat publié n'est invalidé** : tous les chiffres publiés
  proviennent de runs postérieurs au correctif (assertions 100 %), sauf A1
  dont le défaut était la tête (rétracté), pas le loader.
- Reste à produire côté C0 : `v22_release_manifest.json` (non encore déposé).
