# QA — Validation finale du rapport V2.2 (`reports/v22_final.md`, commit 40e24a0f)

- **Date :** 2026-09-25, @ag-4. **Porte :** dernière porte V2.2 (hors §7 coûts
  @ag-5). **Méthode :** lecture intégrale + confrontation aux recalculs QA
  (REG-74→79) et aux artefacts (`runs/v22_*`).

## Verdict : **VALIDÉ** — 4 micro-corrections de formulation (aucun écart de chiffre)

Les 9 exigences sont satisfaites sur pièce :
1. Table 8/8 toutes voies + claims par banc ✓ (valeurs identiques à mes
   recalculs : A1-bis 0.855/0.838/0.853/0.855/0.853/0.833/0.855/0.858 ;
   A2 ; A3 ; direct ; discret) ; (p) en table diagnostic séparée ✓.
2. Chronologie des 4 préenregistrements ✓ (voir micro-correction M1).
3. 5 incidents cause/correction/impact ✓ — dont la contamination B1-A1 côté
   QA, nommée telle quelle (voir M2 sur « au bit près »).
4. Environnement R7 ✓ (variance ~6 pts, tie-break eps non rétroactif,
   sélection 2213 seule).
5. Limites ✓ (« sur CES bancs », 1 seed, INCONNU non évalué, tête relations
   unused, assertions 90→100 %).
6. **A2 probs vérifiées** : passe dédiée `runs/v22_a2_probs/` — loader
   **assert 100 %** (l.44), **identité prédiction==publiée 400/400 × 8** (l.138),
   **NLL recalculée = fichier** (0.0044–0.0294) ; Brier (voir M3).
7. Coûts : section **EN ATTENTE @ag-5**, aucune conclusion produit ✓.
8. Négatifs publiés ✓ (A1 FAIL, A3 court < A2 par banc IC>0, asymétrie
   chiffrée).
9. Renvois QA ✓ (reviews + REG-76/77/78 + R7).

## Micro-corrections de formulation (erratum daté recommandé)

- **M1 (chronologie A1-bis)** : le rapport écrit « spec f6460e29 (14:25, doc
  d9337317) avant run 14:35 ». Précis : **préenregistrement registre
  14:22:44** (commit `f6460e29`) → **run 14:37:44** ; le **doc**
  `V22_A1BIS_SPEC.md` (`d9337317`) a été déposé **14:56** (post-run, extrait
  verbatim de l'entrée de registre, résout la réserve de traçabilité).
- **M2 (« identique au bit près »)** : la régénération GPU A1 est identique
  **aux agrégats 8/8** au bit près (vérifié sur ma référence pré-contamination,
  y compris B1 = 0.3225) ; l'original per-item n'ayant pas été conservé,
  l'identité per-item n'est pas vérifiable → écrire « agrégats 8/8 identiques
  au bit près ».
- **M3 (Brier)** : le « Brier » archivé est `(1 − p_oracle)²` (classe gold
  seule), pas le Brier multiclasse Σ(p−y)² ; le renommer « Brier gold-class »
  ou préciser la définition (le Brier multiclasse direct reste 0.119→1.234,
  QA V2.1-Q1). Aucun impact NLL/calibration.
- **M4 (« +2.5 pts en court — significatif »)** : seul **B1** est significatif
  (+2.5, IC [0.25 ; 4.75]) ; B5 +1.75, B6 +0.75, B8 +1.5 (IC contiennent 0),
  B7 +2.0 (IC [0.00 ; 4.00], limite). Écrire « B1 significatif ; autres courts
  +0.75→+2.0 IC∋0 ». La conclusion architecturale (profondeur) n'est pas
  affectée.

## Ce qui reste ouvert (inchangé)

- **§7 coûts end-to-end (@ag-5)** : sans eux, pas de conclusion produit —
  conforme à mon exigence n°7.
- Jalons hors V2.2 : INCONNU/mondes partiels, bancs plus durs (saturation
  B5/B6), multi-seed.

---

*QA @ag-4 — preuves : transcript de recalcul (table 8/8, probs A2, routeur),
`reports/v22_a{1,2,3}_qa_review.md`, REG-74→79.*

---

# Addendum — Section 7 (coûts end-to-end) : **VALIDÉE — dernière porte V2.2 fermée**

- **Date :** 2026-09-25, @ag-4. **Artefacts :** `runs/v22_couts/`
  (`couts_metrics.json`, `COUT_TABLE.md`, `nohup.log`), harnais
  `scripts/run_v22_couts.py` sha `0c708b42…` = **config_sha256 du registre
  V2.2-couts** (register/start 18:50:43, finish 18:54:22). M1–M4 appliquées
  (commit `f916e808`) ✓.

## Vérifications (arithmétique + méthodologie + équité ; QA n'a pas rejoué le GPU)

- **Ratios/débits recalculés** : B1 batch8 ×1.235, B3 batch8 ×1.273 (rapport
  ×1.23/×1.27 ✓) ; débit ×0.782/×0.792 (rapport ×0.78–0.79 ✓) ; p95 cohérents.
- **Propagation** : 0.585–0.665 ms/item (p95 0.715–0.797), soit **1.29–1.45 %
  du p50 A2** — le rapport écrit « ~1.3 % » : à préciser **« ≈1.3–1.5 % »**
  (M5, cosmétique). Microbench CPU 0.187 ms cohérent en ordre de grandeur.
- **Équité** : mêmes batchs (8 et 1), mêmes lots/ordre, warmup 2, sync CUDA,
  48/398 batchs comptés **identiques pour les deux voies** ; alloc VRAM pic
  parité (1472/1478 et 1493/1512 MiB) ; RSS non revendiqué (pic dépend de
  l'ordre/allocation — le rapport ne le compare pas, correct).
- **Interdits §8** : aucune latence V1 réutilisée (vérifié) ; chemins
  end-to-end documentés (A2 : tok+forward+extract+facts+transition+propagate
  T=20+réponse ; A3 : collate+forward+tête) ; assert LoRA **100 % ×2**
  (224/224, steps 1200/800) ; multi-questions = mesure future notée.
- **Lecture opérationnelle validée** : +23–27 % de latence pour +3.25 pts (B1)
  et +50–75 pts (profondeur) ; surcoût porté par l'extraction, propagation
  ≈ gratuite.

## Clôture

**Toutes les portes V2.2 sont fermées** : protocole, A1 (FAIL publié), A1-bis,
A2, A3, borne routeur, rapport final (M1–M4 appliquées), **coûts §7 validés**.
Seuls restent les jalons déclarés hors V2.2 (INCONNU/mondes partiels, bancs
plus durs que la saturation B5/B6, multi-seed, OOD) — documentés au rapport.
