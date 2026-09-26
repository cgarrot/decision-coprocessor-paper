# QA — Audit V22-confirmation (C0, C1, loaders, tie-break, localisation)

- **Date :** 2026-09-25, @ag-4. **Audit :** `DECISION-COPROCESSOR-AUDIT-V22-CONFIRMATION.md`
  (sha `d47186ec`). **Artefacts :** `v22_scope_erratum.md`,
  `v22_public_inference_audit.md`, `runs/c1_ablation/` (commit `e9c669ac`),
  `reports/qa_c1_metrics.json`, `reports/qa_loader_manifests.json`,
  `v22_loader_impact_matrix.md`, `reports/qa_tiebreak_stability.json`.

## 1. C0 — corrections : VALIDÉES (1 sortie manquante)

- **Erratum de portée** (`v22_scope_erratum.md`) : les 7 corrections sont
  conformes aux faits (NLL retirée ; `gold_class_squared_error` renommé +
  Brier multiclasse à calculer ; parser 1.000/1.000 réconcilié — le 0.95 était
  un framing erroné ; bancs requalifiés « campagne adaptative » ; coûts
  reformulés (1.3–1.5 %, unités) ; IC canoniques = `a3_eval_verdict.json`
  (écarts QA ≤ 0.5 pt = graine bootstrap, vérifié) ; « direct dominant en
  court » restreint à V2.1).
- **Chemin d'inférence public A2** (`v22_public_inference_audit.md`) :
  **l'exécuteur S n'intervient pas** — vérifié par code (seuls LoRA + têtes
  fact + propagation). Consommation déclarée : `input.{state,question,options}`
  + `private.graph.options` (mapping des candidats publics).
- ⚠️ **Le test anti-fuite n'avait PAS été exécuté par C1** (docstring
  seulement). **QA l'a exécuté (structurel)** : randomisation des champs privés
  (edges, trace, answer, terminals) → **entrées de modèle identiques
  3200/3200** (les cibles gold, elles, changent) ⇒ les entrées d'inférence ne
  dépendent pas de ces champs. Preuve : `qa_c1_metrics.json` §anti_leak.
- ⚠️ **Sorties C0 manquantes** : `v22_loader_impact_matrix.md` **produite par
  la QA** (ci-dessous/§3) ; **`v22_release_manifest.json` toujours absent**.

## 2. C1 — ablation 2×2 : VALIDÉE

- **Replay exact** (preds vs `c1_ablation.json`) sur 4 cellules × 8 bancs.
- **Identité item-level** (au-delà des asserts d'accuracy du script) :
  **R0-soft == A1-bis 400/400 ×8** et **R1-soft == A2 400/400 ×8**.
- Résultat (lecture) : **soft > hard à lecteur fixé** (R1 : 0.995–1.0 vs
  0.78–0.875 ; R0 : 0.83–0.86 vs 0.56–0.83) **et** lecteur R1 > R0 en hard
  (0.78–0.875 vs 0.56–0.83) → **les deux facteurs contribuent** (audit §2.3,
  interprétation 1) ; le parser+solveur borné est dans la même table.
- ⚠️ **« Brier multiclasse » publié = candidats seuls, résidu hors-candidats +
  INCONNU exclu** (résidu rapporté à part 0.0005–0.0103) — ce n'est pas le
  Brier multiclasse complet demandé (audit §5.3). Non recalculable depuis les
  archives (seuls `answer_label+ok` sont sauvegardés) : **action R-A** —
  archiver par item les distributions candidats + résidu et calculer le Brier
  complet, ou renommer explicitement `brier_candidats_residu_exclu`.

## 3. Loaders — manifestes + matrice d'impact (`v22_loader_impact_matrix.md`)

- Valeurs vérifiées **après chargement sur modèle neuf** : bundle reader
  224/224 (peft-natif), A2 224/224 (`pm.state_dict` + assert 100 %),
  bundle direct 224/224, A3 224/224 + tête stricte, exécuteur 28/28 — maxdiff 0.
- **Incident `.default` reproduit** : `set_peft_model_state_dict` sur les
  checkpoints `pm.state_dict` charge quasi à vide (0–28/224) ; aucun chiffre
  publié ne vient d'un état cassé (assertions 100 %).
- Matrice run→loader→correctif→replay : A1 (défaut = tête, pas loader),
  A1-bis/A2/A3/C1/probs = replay item-level vérifié ; portée : replay GPU neuf
  non réalisable par la QA (R7), couvert par assertions in-run + identités.

## 4. Tie-break — stabilité : VALIDÉE (8/8)

`qa_tiebreak_stability.json` : ordre des faits invariant ; **renommage =
équivariance** (la réponse se transporte, elle n'est pas « invariante ») ;
réindexation à mapping inversé invariante ; ordre des candidats sans effet ;
**égalité réelle → clé alphabétique** ; **quasi-égalité ≤ eps (1e-3) → clé
alphabétique même si la masse est légèrement inférieure** (politique déclarée,
mandat n°4 — à documenter) ; écart > eps → argmax ; sink jamais candidat.

## 5. Localisation CPU/GPU (§8.3) — partielle + artefact requis

- **Structurel** : tokenisation identique (même révision de tokenizer) ;
  l'unique point d'entrée possible des divergences est le backbone bf16, puis
  l'argmax de l'extracteur (successeurs) ; A→pT→réponse sont déterministes
  à entrées fixées (même chemin de code).
- **Empirique disponible** : divergences CPU/GPU observées **au premier étage
  archivé = successeurs de mentions** (26/64 mémoires différents sur E5v3-A ;
  CPU B1 c_prop 0.3450 vs GPU 0.3225 pour A1) ; pas de divergence aval
  observée à entrées identiques.
- **Pour la localisation étage-par-étage exigée** (backbone→logits→A→états→
  réponse à entrées tokenisées identiques), il faut un dump GPU (1 run court,
  8–16 items B1+B3) : token ids, h14/h21, mention spans, logits fact (subj/obj),
  A, p0, pT, réponse. **Action R-D** : @ag-1/@ag-3 exécutent le dump ; la QA
  fournit le script de diff et publie le premier étage divergent.

## 6. Verdict et actions

**C0/C1 validés ; loaders et tie-break validés ; localisation CPU/GPU
partielle.** Actions ouvertes :
- **R-A** Brier multiclasse complet (archiver probs/résidu par item) ;
- **R-B** anti-fuite : exécuté par la QA (structurel) — committer le test dans C1
  ou mettre à jour le docstring (le doc annonçait « à exécuter ») ;
- **R-C** produire `v22_release_manifest.json` (sortie C0 manquante) ;
- **R-D** dump GPU des étages pour §8.3 (script QA prêt) ;
- **R-E** documenter la préférence alphabétique dans les quasi-égalités (eps).

---

*QA @ag-4 — preuves : `reports/qa_c1_metrics.json`,
`reports/qa_loader_manifests.json`, `reports/qa_tiebreak_stability.json`,
`v22_loader_impact_matrix.md`.*

---

# Addendum — Localisation CPU/GPU (§8.3) : dump étage par étage exécuté

- **Date :** 2026-09-25, @ag-4. **Artefacts :** `scripts/qa_diff_stages.py`,
  `runs/v22_stages_cpu.pt` (16 items : 8 B1 + 8 B3), `runs/v22_stages_gpu.pt`
  (dumb @ag-1 sous verrou, même code/loader assert 100 %),
  `reports/qa_stage_diff.json`.

## Résultats

- **Premier étage divergent : `h14` (backbone), 16/16 items** — max|Δ| médian
  2.0 (h21 : 3.0) sur une échelle max|h| médiane ≈ 428, soit **erreur relative
  ~0.49 %** (max 2.29 %) = dérive bf16 inter-plateformes au fil des couches,
  pas un bug de code (token_ids/mask/spans **exacts** ; p0 **exact**).
- Aval : logits fact max|Δ| 0.3–1.2 ; A ≤ 0.01 ; pT médian 1.2e-4 (1/16 >1e-3).
- **Décisions stables sur cet échantillon : successeurs de mentions 0/16 flips,
  réponses 0/16 flips.** Un seul argmax de logits objet flippe — sur un
  quasi-égalité (marge GPU 0.044 vs CPU 0.005) — sans effet sur la décision.
- Cohérent avec R7 : les ~6 pts CPU↔GPU de V2.1 concernaient le **lecteur
  E5v3-A** (marges plus faibles) ; le lecteur A2 a des marges plus larges.

## Interprétation et suite

- La divergence **entre au backbone** (flottants), pas dans une étape logique ;
  tout l'aval est déterministe à entrées fixées. Les flips de décision
  n'apparaissent qu'aux quasi-égalités.
- Pour capturer des flips de décision et chiffrer le taux : étendre le dump
  (32–64 items, inclure des items connus divergents d'E5v2_dev) et/ou rejouer
  le **lecteur E5v3-A** ; publier la distribution des marges top-2 comme
  prédicteur du taux de flip. À défaut, la conclusion opérationnelle tient :
  **aucun étage logique n'est en cause ; le bruit numérique remonte du
  backbone et n'affecte que les quasi-égalités.**

---

# Addendum 2 — Marges top-2 (plancher de bruit pour C2), depuis les archives

- **A3 (direct, probs complètes archivées, n=3200)** : marge top-2 médiane
  0.9999 ; **quasi-égalités : 0.00 % ≤ 1e-3 · 0.19 % ≤ 1e-2 · 1.25 % ≤ 5e-2**.
  Par banc : B2–B4 (profondeur) concentrent le risque (p05 0.085–0.097 ;
  0.3–0.7 % ≤ 1e-2), les bancs courts ≈ 0 %.
- **A2 (p_oracle archivée)** : médiane 0.998 ; 16.3 % < 0.99 · 2.8 % < 0.95 ·
  min 0.03 (marges top-2 non archivées — cf. R-A).
- **Lecture C2** : la dérive bf16 (~0.5 % relatif, mesurée au backbone) ne peut
  flipper que les items quasi-égalitaires → au pire ~0.2–1.3 % des items
  (≈ 6–40/3200), soit **≲1 pt d'accuracy** pour la voie directe ; cohérent avec
  0/16 flips du dump et avec les ~6 pts historiques du vieux lecteur E5v3-A
  (marges plus faibles). **Recommandation C2** : archiver les probs par item
  (R-A) et publier la distribution des marges top-2 comme métrique de risque
  de flip, à côté de la dispersion inter-seeds.
