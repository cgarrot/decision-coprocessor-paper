# QA V2.2 — Protocole, A1 (FAIL supersédé), A1-bis (en cours) et incident d'archive

- **Date :** 2026-09-25, par @ag-4. **Commits :** `c40a168a` (protocole 14:03),
  `dcdcf7f9e` (A1 FAIL 14:15), `f6460e29` (correction A1/A1-bis 14:22).
- **Méthode :** recalcul depuis archives (`runs/v22_a1/*_pred_prop.jsonl`,
  `runs/v21_eval/*_pred_c.jsonl`, `data/v21/*.jsonl`) ; inspection de source ;
  aucun GPU.

## 1. Protocole `V22_PROTOCOL.md` (sha 6fc9d7d4) — VALIDÉ (rétroactivement)

- Préenregistrement daté 14:03 (registre 14:03:35) **avant** le run A1 (14:11) :
  hypothèse centrale, ablations ordonnées, critères figés (Δ≥+5.0 pts B3 IC>0 +
  non-régression B1), tie-break `eps=1e-3` clé stable (mandat n°4), interdits
  V2.1 reconduits, bancs scellés en évaluation pure, sélection 2213+ seulement,
  routeur mesuré avant toute construction. **Conforme.** Le QA est intervenu
  après le run A1 (aucun entraînement/sélection en A1) : seule irrégularité de
  forme, sans impact, registre daté à l'appui.

## 2. A1 (FAIL) — factuellement VALIDÉ, interprétation SUPERSÉDÉE

- **Recalcul QA (avant contamination, cf. §3)** : c_prop = 0.3225/0.2125/0.2150/
  0.1850/0.2775/0.2375/0.2650/0.2575 ; c_discret = 0.80/0.6675/0.5975/0.56/0.81/
  0.7725/0.80/0.765 ; **Δ B3 = −38.25 pts IC [−44.75 ; −31.75]** (critère
  +5 pts IC>0 → FAIL), B1 0.3225 < 0.80 − 2 pts → FAIL. **0 désaccord**
  item-par-item avec les flags `ok` archivés.
- **Mécanisme 0.75^k RETIRÉ** (registre 14:22, mesure @ag-3) : en mode `fact`,
  `extract()` utilise `fact_logits` (sujet/objet) et **ne passe jamais par
  `successor_logits`** (bilinéaire) ; le script d'entraînement ne supervise pas
  `successor_bilinear` → head non entraîné (top-1 0.054 ≈ hasard) : A1
  propageait du **bruit**. Vérifié structurellement (`src/v2model/extractor.py`
  branche fact ; absence de `successor_bilinear` dans la loss).
- **A1 reste un échec documenté** (fait), mais son explication par « fuite de
  masse » est retirée ; l'ablation opérante est **A1-bis** (A construite depuis
  les têtes fact-level supervisées, mêmes critères, préenregistrée 14:22).

## 3. Incident d'archive — CONTAMINATION PAR LA QA (transparence)

- `runs/v22_a1/B1-court_pred_prop.jsonl` a une mtime **14:37:31** : mon import
  de `scripts/run_v22_a1_prop.py` (le script **s'exécute à l'import**, aucune
  garde `__main__`) a lancé une ré-exécution complète en CPU
  (`CUDA_VISIBLE_DEVICES=""`) ; B1 réécrit avec les valeurs CPU (0.3450) puis
  processus tué par timeout (30 min) → **B2–B8, `a1_metrics.json`,
  `a1_verdict.json`, `a1_log.txt` intacts** (mtimes 14:12–14:14).
- Conséquence : l'archive per-item A1 de B1 est perdue (runs/ non tracké) ;
  l'agrégat publié (c_prop B1 = 0.3225) et ma vérification pré-contamination
  (0 désaccord avec les flags originaux) restent les références.
- **Demandes** : (a) garde `if __name__ == "__main__":` sur tous les runners
  (aucune écriture `runs/` à l'import) ; (b) marquer/regénérer B1 A1 (renommage
  avec provenance ou re-run GPU) pour qu'un auditeur ne recalcule pas 0.3450 ;
  (c) côté QA : ne plus importer un runner sans vérifier la garde. Le FAIL
  agrégé n'est pas affecté.

## 4. A1-bis (en cours au 14:50) — préliminaire QA

Recalcul partiel (B1–B3) **identique aux métriques** : B1 c_prop 0.8550
(+5.5 pts, IC [1.75 ; 9.25]) ; B2 0.8375 (+17.0, IC [12.5 ; 21.25]) ;
B3 0.8525 (**+25.5 pts**, IC [21.0 ; 30.0]) ; flags conformes. → **PASS
probable** sur la grille A1 (à confirmer sur les 8 bancs). Réserve de
traçabilité : le hash de préenregistrement d'A1-bis (`2334c67b`) pointe
`V22_A2_ADDENDUM.md`, qui **ne mentionne pas** A1-bis (grep) → ajouter une
section datée (ou pointer un doc contenant la spec A1-bis).

## 5. A2 — amendement vu (co-signé, module 14:33, INCONNU 14:42, training
14:43, banc 2213 14:19) : QA complète quand le run atterrit (α/β, INCONNU,
propagation dans la boucle, sélection 2213 uniquement).

---

*QA @ag-4 — preuves : transcript de recalcul + `reports/v22_a1_qa_review.md`,
`reports/qa_v21_q1_metrics.json` (référence).*

---

# Addendum D — QA complète A1-bis (8 bancs) : **PASS VALIDÉ**

- **Date :** 2026-09-25, @ag-4. Sortie : `runs/v22_a1bis/` (finish registre
  14:52:58, `pass`). Recalcul intégral depuis les prédictions archivées.

## D.1 Résultats (recalcul QA vs métriques : identiques, 0 désaccord item/flag)

| Banc | c_prop | c_disc | Δ (pts) [IC95] | Δ vs direct (pts) |
|---|---:|---:|---|---:|
| B1-court | 0.8550 | 0.8000 | **+5.50** [+1.50,+9.25] | −8.25 |
| B2-prof6 | 0.8375 | 0.6675 | **+17.00** [+12.50,+21.50] | +31.25 |
| B3-prof8 | 0.8525 | 0.5975 | **+25.50** [+20.75,+30.00] | **+57.25** |
| B4-prof10 | 0.8550 | 0.5600 | **+29.50** [+24.50,+34.75] | +54.75 |
| B5-surface | 0.8525 | 0.8100 | **+4.25** [+0.25,+8.25] | −8.75 |
| B6-distract | 0.8325 | 0.7725 | **+6.00** [+2.25,+9.75] | −10.50 |
| B7-options | 0.8550 | 0.8000 | **+5.50** [+1.50,+9.25] | −8.50 |
| B8-depart | 0.8575 | 0.7650 | **+9.25** [+5.25,+13.50] | +1.75 |

- **c_prop ≈ 0.83–0.86 INVARIANT en profondeur** (plus de décroissance 1→10) ;
  plafond 0.95 : écart restant ≈ 9–12 pts.
- **Critère PASS** : B3 Δ = +25.5 pts (≥ +5) IC bas +20.75 > 0 ✓ ;
  non-régression B1 0.855 ≥ 0.80 − 2 pts ✓ → **PASS confirmé**.
- IC > 0 sur les **8** bancs (le plus serré : B5, +4.25 pts, IC bas +0.25 —
  à publier tel quel).

## D.2 Conformité spec / harnais

- **A depuis les têtes fact-level supervisées** : `ext.fact_logits` +
  `transition_matrix_from_facts` (vérifié source) : `A[u,v]=Σ_f P(subj=u)P(obj=v)`,
  terminal → self-loop, **INCONNU = sink absorbant** `max(0,1−Σ P(subj))`,
  pas de renormalisation silencieuse, ligne sink one-hot ; tie-break `eps=1e-3`
  dans le module (mandat n°4). Zéro entraînement (no_grad, aucun optimiseur),
  checkpoints figés, bancs scellés en évaluation pure.
- `V22_A1BIS_SPEC.md` (sha `d9337317…`) enregistrée : spec préenregistrée +
  provenance — **réserve n°4 résolue**.

## D.3 Incident — résolution vérifiée

- Gardes `if __name__ == "__main__":` : **aucun runner V2.2 sans garde**
  (`grep -L` vide).
- **A1 régénéré GPU** : les 8 agrégats sont **identiques** à la référence
  pré-contamination (B1 0.3225, B2 0.2125, B3 0.2150, B4 0.1850, B5 0.2775,
  B6 0.2375, B7 0.2650, B8 0.2575) ✓.

## D.4 Conclusion

**A1-bis PASS validé** : la propagation des distributions fact-level (zéro
entraînement) élimine la chute en profondeur et bat le discret partout
(IC>0), +57 pts vs direct à prof 8. **Le goulot était bien l'interface**
(audit §6.2), démontré par la preuve la moins coûteuse. Reste ≈ 9–12 pts vers
le plafond (p) et la sémantique INCONNU — objet d'A2 (grille figée).
