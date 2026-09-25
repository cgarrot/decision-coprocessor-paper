# Rapport final — Decision Coprocessor

- **Version :** finale, 2026-09-24. **Préenregistrement :** `reports/preregistration.md` v2.1 (figée avant ouverture du test).
- **Auteur :** @ag-4, évaluation indépendante. **Recalcul intégral** des scores par mes soins depuis `runs/p6/*.jsonl` (66 fichiers), jamais depuis les chiffres de l'exécutant.
- **Mode d'évaluation :** `autocast` bf16 (prereg §9bis.A2), logits castés FP32 pour softmax/argmax/métriques ; exclusions >512 appliquées id par id (`artifacts/test_exclusions.json`, sha256 vérifié) ; hash gate 33/33 checkpoints PASS ; test ouvert **une seule fois**.
- **Statistiques :** moyenne des 3 seeds par variante, comparaisons appariées (mêmes problèmes), bootstrap groupé **couplé** 2000 répliques, unité `group_id` (prereg §6). `n_examples` jamais multiplié par 3.
- **G4 :** seule la paire s17 est exécutée (prereg §9bis.A3) ; s29/s43 marquées [NON EXÉCUTÉ].

## Résumé des verdicts (§12.1)

| Niveau | Déclaration |
|---|---|
| **N1 faisabilité** | **ATTEINT** — 66 fichiers conformes (comptes 3997/3080/3993), scores recalculables, hash gate 33/33 checkpoints PASS, exclusions id par id. *Réserve* : aucun `reload_check` P6 dédié n'est fourni ; l'intégrité des checkpoints est couverte par le hash gate 33/33 et les rechargements P3 des mêmes best étaient PASS. |
| N2 gain de prédiction | **NON ATTEINT** — Δ(R4−B2) sur test_depth = **−0.59 pt, IC 95 % [−1.25 ; +0.07]** (non significatif). |
| N3 intérêt spécifique | **NON ATTEINT** — R4 ne bat ni B3 (−0.16 pt en faveur de B3, ns) ni B4 (ns) ; G4 sans gain à conserver. |

**Conclusion honnête (confirmée par les tests) :** la **tête directe apprise est réelle** (B2 ≫ B1/B0 sur dev et IID), mais **la récurrence n'est pas démontrée** (saturation dès 1 étape, B3/B4 égaux ou meilleurs) et **la mémoire latente n'est pas exploitée** (P4 : Δlogits ≤ 0.004 sur s43). Le sidecar **dégrade légèrement** les décisions de profondeur sur le test réservé.

---

## Réponses aux 8 questions du §17

**Q1. Le sidecar améliore-t-il les décisions multiétapes ?**
**Non.** Sur le critère principal (macro A/B/C, `test_depth`) : R4 − B2 = **−0.59 pt** [−1.25 ; +0.07] (agrégé 3 seeds) ; par seed : −0.65/−0.06/−1.06 pt. Sur `test_iid` : +0.24 pt [−0.33 ; +0.74] (ns) ; sur `test_composition` : −0.08 pt [−0.64 ; +0.44] (ns). H1 non soutenue.

**Q2. L'amélioration dépasse-t-elle celle d'une tête plus grande ?**
**Non** : R4 vs B3 = **+0.16 pt** [−0.17 ; +0.48] ; R4 vs B4 = **−0.23 pt** [−0.63 ; +0.16]. Les deux contrôles (2,18 M non récurrent / 5,27 M coût comparable) sont au niveau de R4 ou au-dessus. H2 non soutenue.

**Q3. Davantage d'itérations aident-elles avec les mêmes poids ?**
**Non.** R4 − R1 = **−0.02 pt** [−0.20 ; +0.15] (depth), +0.07 [−0.08 ; +0.23] (compo), −0.02 [−0.16 ; +0.12] (IID). Saturation dès **k = 1** : sur dev aussi (b1 .5402 → b4 .5409). Scénario **S-saturation** déclaré.

**Q4. Le gain survit-il à des profondeurs et compositions nouvelles ?**
**Sans objet** (aucun gain à faire survivre). La tête elle-même chute sous distribution shift : B2 macro-cœur dev .476 → **.342** (depth) et **.408** (composition). La couverture `test_depth` est réduite (23 % d'exclusions >512, dont 81 % des B_relations d10) — les conclusions de profondeur sont conditionnelles (limites L8).

**Q5. Quelles décisions correctes sont dégradées ?**
Sur `test_depth` (somme 3 seeds, n=3×3080) : **181 corrections / 238 dégradations (net −57)**. Par famille : A_rules 6/39 (net −33), B_relations 139/148 (net −9), C_programs 36/51 (net −15). Le sidecar corrige surtout B_relations mais en dégrade presque autant ; sur A/C il dégrade plus qu'il ne corrige.

**Q6. Quelle est la latence complète sur la RTX 3070 Laptop ?**
Batch 1, autocast bf16, 30 warm-up + 200 mesures, événements CUDA (L512 « full prepared ») : **B2 46.18 ms (p95 46.86)** · **R4 50.04 ms (p95 50.71)** — ratio moyen ×1.083. Composants : encodage 45.34 ms, readout B2 0.66 ms, sidecar 0.99/1.55/2.68 ms (R1/R2/R4). Depuis texte brut : B2 46.67 ms (L512). VRAM pic mesurée (B2/R4) : 1.175 GiB alloués / **1.199 GiB réservés** — très en dessous des cibles (6,5 + 1 GiB). Débit R4 (mesures séparées) : 28,9/47,8/51,6 req/s en B1/B4/B8. p99 mesuré mais non concluant (n=200 < 500).

**Q7. Quelle part du gain l'allocation adaptative conserve-t-elle ?**
Gain R4 ≤ 0 → **rétention non mesurable**. G4 (s17) : macro-cœur depth **.3420** vs B2 .3418 (Δ ponctuel +0.02 pt ; apparié −0.62 pt [−1.47 ; +0.18], ns), activations R4 **47.9 % (iid) / 53.1 % (depth) / 56.7 % (compo)**. Le gate n'apporte pas de gain ; H4 non soutenue/non mesurable.

**Q8. Quelles limites empêchent une conclusion plus forte ?**
Voir la liste exhaustive en fin de rapport (§Limites). Les principales : saturation k=1, mémoire H non lue, gate non sélectif, couverture de profondeur amputée par la limite 512 tokens, 3 seeds, latence mesurée en batch 1 seulement.

---

## Tableau central (§17) — mesures uniquement, moyennes des seeds

| Variante | Paramètres entraînés | IID | Profondeur | Composition | Simple (D) | NLL | Latence moyenne (L512) | p95 | VRAM réservée |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B2 direct | 1 054 209 | 0.4884 | **0.3418** | 0.4081 | 0.7473 | 1.3511 | 46.18 ms | 46.86 ms | 1228 MiB |
| B3 non récurrent | 2 178 177 | 0.4918 | 0.3343 | 0.4070 | 0.7477 | 1.3541 | — (1.05 ms module) | — | — |
| B4 coût comparable | 5 270 785 | 0.4930 | 0.3382 | 0.4062 | 0.7468 | 1.3521 | — (2.58 ms module) | — | — |
| R1 | 2 110 465 | 0.4910 | 0.3361 | 0.4066 | 0.7460 | 1.3543 | ≈47.2 ms* | — | — |
| R2 | 2 110 465 | 0.4915 | 0.3366 | 0.4058 | 0.7464 | 1.3543 | ≈47.7 ms* | — | — |
| R4 | 2 110 465 | 0.4908 | 0.3359 | 0.4073 | 0.7473 | 1.3540 | 50.04 ms | 50.71 ms | 1228 MiB |
| G4 (s17) | 35 116 | 0.4934 | 0.3420 | 0.4070 | 0.7494 | 1.3322 | — (gate 0.70 ms) | — | — |
| B0 uniforme | 0 | 0.2682 | 0.2752 | 0.2666 | 0.2608 | 1.3122 | — | — | — |
| B0 majoritaire | 0 | 0.2785 | 0.3334 | 0.2830 | 0.2595 | 1.3122 | — | — | — |
| B1 codes gelés | 0 | 0.2741 | 0.2827 | 0.2715 | 0.3101 | 3.0578 | — | — | — |

\* R1/R2 : estimées additivement (B2 full + sidecar mesuré), **non mesurées end-to-end** ; R1/R2/R4 partagent le même checkpoint. « Simple (D) » = D_control sur `test_iid`. Colonnes vides : non mesurées, jamais inventées.

**Apparié vs B2 (Δ macro A/B/C en points, IC 95 % groupé couplé 2000, corrections/dégradations) :**

| Variante | test_iid | test_depth | test_composition | corr./dégr. depth |
|---|---:|---:|---:|---:|
| B3 | +0.33 [−0.23 ; +0.84] | −0.75 [−1.40 ; −0.08] | −0.11 [−0.66 ; +0.42] | 177 / 241 |
| B4 | +0.46 [−0.10 ; +0.99] | −0.36 [−1.02 ; +0.32] | −0.19 [−0.74 ; +0.34] | 206 / 242 |
| R1 | +0.26 [−0.30 ; +0.77] | −0.57 [−1.23 ; +0.09] | −0.15 [−0.70 ; +0.40] | 182 / 235 |
| R2 | +0.30 [−0.25 ; +0.80] | −0.52 [−1.19 ; +0.16] | −0.23 [−0.77 ; +0.30] | 188 / 239 |
| **R4** | +0.24 [−0.33 ; +0.74] | **−0.59 [−1.25 ; +0.07]** | −0.08 [−0.64 ; +0.44] | **181 / 238** |
| G4 (s17) | +0.22 [−0.44 ; +0.85] | −0.62 [−1.47 ; +0.18] | +0.18 [−0.59 ; +0.93] | 31 / 49 |
| R4−B3 | −0.09 [−0.35 ; +0.16] | +0.16 [−0.17 ; +0.48] | +0.03 [−0.23 ; +0.27] | — |
| R4−B4 | −0.22 [−0.52 ; +0.09] | −0.23 [−0.63 ; +0.16] | +0.11 [−0.19 ; +0.41] | — |
| R4−R1 | −0.02 [−0.16 ; +0.12] | −0.02 [−0.20 ; +0.15] | +0.07 [−0.08 ; +0.23] | — |

---

## Exactitude selon la profondeur (test_depth, moyenne des seeds)

| Variante | d=6 | d=8 | d=10 |
|---|---:|---:|---:|
| B2 | 0.3411 | 0.3945 | 0.3072 |
| R4 | 0.3358 | 0.3857 | 0.3025 |
| B3 | 0.3342 | 0.3841 | 0.3038 |
| B4 | 0.3375 | 0.3896 | 0.3030 |
| G4 | 0.3467 | 0.4014 | 0.3013 |
| B0-m | 0.3400 | 0.3516 | 0.3582 |
| B1 | 0.1963 | 0.4453 | 0.1949 |

**Couverture (préenregistrée) :** `test_depth` perd 920/4000 exemples >512 (A d10 142, B d6 114 / d8 276 / d10 376), conservés 3080. Les cellules B_relations d8/d10 ne portent que sur 191/90 exemples : les conclusions de profondeur pour B sont **conditionnelles**. `test_iid` 3 rejets, `test_composition` 7. Détail complet : `artifacts/test_exclusions.json`.

## Qualité / coût et calibration (NLL, Brier, ECE 15 bins equal_width)

| Variante | Split | NLL | Brier | ECE |
|---|---|---:|---:|---:|
| B2 | test_iid | 0.9728 | 0.5370 | 0.0246 |
| B2 | test_depth | 1.3511 | 0.7463 | 0.1254 |
| B2 | test_composition | 1.1893 | 0.6393 | 0.0546 |
| R4 | test_iid | 0.9711 | 0.5361 | 0.0253 |
| R4 | test_depth | 1.3540 | 0.7477 | 0.1295 |
| R4 | test_composition | 1.1869 | 0.6380 | 0.0524 |
| G4 (s17) | test_depth | 1.3322 | 0.7370 | 0.1224 |
| B0-u | test_depth | 1.3122 | 0.7220 | 0.0197 |
| B1 | test_depth | 3.0578 | 1.0505 | 0.4098 |

Lecture : R4 est légèrement **moins** bien calibré que B2 sur depth (NLL +0.003, ECE +0.004) ; le sidecar n'améliore pas la qualité probabiliste. L'ECE du B0 uniforme est bas par construction (confiance ≈ exactitude) malgré une NLL médiocre : l'ECE seul ne suffit pas — d'où la publication conjointe NLL/Brier. La garde D_control est respectée (aucune dégradation > 1 pt : B2 .7473 vs R4 .7473, B3 .7477).

## Mémoire et stabilité

- **VRAM pic mesurée** (B2/R4, L512) : 1.175 GiB alloués / 1.199 GiB réservés — marge très large sur la cible 6,5+1 GiB ; aucun OOM.
- **Stabilité sous permutation** (métrique secondaire corrigée, prereg §9bis.A1) : exactitude stable sous permutation (B2 +0.4 pt, R4 +0.2 pt, B3 −1.0 pt, B1 +1.4 pt, comparaison par id de candidat) ; l'instabilité **par instance** (~39 % pour B2/R4/B3, 70 % pour B1) est une propriété partagée avec B2, non un défaut du sidecar.
- **Première passe de latence invalidée** (horloges laptop à 210 MHz sans rampe) et relancée avec 120 forwards de chauffe : les chiffres publiés sont la seconde passe (monotones). Méthode dans `runs/p6/latency/latency.json`.

---

## Résultats observés vs hypothèses explicatives vs prochaines expériences

**Résultats observés (mesurés, recalculés)**
1. B2 apprend : dev macro 4 familles ≈ .55 ; IID test .488 ; largement au-dessus de B1 (.274) et B0 (≤ .279).
2. Sur le test réservé, **aucune variante sidecar/contrôle ne bat B2** : Δ(R4−B2) depth −0.59 pt [−1.25 ; +0.07] ; IID/compo ns.
3. Saturation k=1 (R4≈R1) ; B3 ≈ R4 ; B4 ≈ R4 ; G4 sans gain (rétention non mesurable).
4. Le sidecar corrige et dégrade quasi autant (181/238 sur depth), net négatif sur les 3 familles.

**Hypothèses explicatives (non prouvées par ces données)**
1. Le sidecar lit très peu la mémoire H (P4 §13.1 : Δlogits ≤ 0.004 s43) → l'information pertinente resterait dans les représentations de candidats, pas dans Z.
2. La tâche et/ou la supervision ne fournissent pas de signal d'utilité locale : la correction ne cible pas les erreurs de chaînage (net négatif sur A, le plus « compositionnel »).
3. La sélection Dev (plateau, 1200 steps) et le sous-ajustement relatif des modules contrôles expliquent une partie des écarts faibles, mais pas le signe négatif sur depth.
4. Le test de profondeur, amputé à 512 tokens (B d10 : 81 % exclus), mesure surtout une extrapolation « texte court » et pourrait sous-estimer un effet réel sur les longues chaînes — hypothèse non testable dans ce protocole.

**Prochaines expériences (nouveaux jeux réservés obligatoires, §11.7)**
1. Sidecar qui lit les **représentations de candidats** (et non seulement H) à budget constant.
2. **Supervision d'utilité par exemple** (labels de transition B2→R4) et gate avec features enrichies ; sinon abandonner P5 (§9.1).
3. `max_length` 1024 (ou génération de textes plus compacts) pour couvrir réellement d10.
4. Étude de cas B_relations : pourquoi 139 corrections / 148 dégradations (probe par type d'erreur §13.4).
5. 5 seeds et tailles d'échantillon augmentées pour détecter des effets ≤1 pt.

---

## Limites (exhaustif)

1. **Saturation k=1** : aucune conclusion sur l'intérêt de la récurrence multi-étapes.
2. **Mémoire H non exploitée** (Δlogits ≤ 0.004 sur s43) : le mécanisme latent n'est pas démontré.
3. **Gate non sélectif** (λ=0.0 ; ~50 % d'activations ; net Dev +4) : H4 non soutenue ; latence adaptative non testée en déploiement réel (§11.5, pas de compactage).
4. **Instabilité par instance sous permutation** (~39 %, partagée avec B2) : les prédictions individuelles changent, l'agrégat non ; toute utilisation per-instance est fragile.
5. **p99 instable** (n=200 < 500) ; première passe de latence invalidée (horloges) — seul le batch 1 est mesuré end-to-end ; R1/R2 estimés additivement.
6. **3 seeds seulement** : dispersion faible observée (≤0.005) mais variabilité d'optimisation imparfaitement estimée ; IC de ±0.6 pt environ.
7. **Probes directionnels seulement** (§13.3) : lisibilité de l'info ≠ usage causal.
8. **Couverture de test réduite** : 920/4000 exclusions sur depth (81 % des B d10) ; conclusions de profondeur conditionnelles ; H3 non concluable pour les longues chaînes B.
9. **Composition réservée** : test_composition évalue des structures réservées, mais les patrons simples partagés avec IID ne sont pas une généralisation structurelle.
10. **Précision bf16 figée** : écarts d'argmax bf16↔fp32 attendus jusqu'à ~2,4 % sur quasi-égalités (aucun cross-check fp32 permis par le prereg).
11. **ECE sensible à la construction** (equal_width 15 bins, publiée) ; B0-u montre qu'un ECE bas ne vaut pas bonne qualité probabiliste.
12. **VRAM complète mesurée seulement pour B2/R4** ; B3/B4/G4 ont des temps de module, pas de full end-to-end.
13. **Comparateur externe EXT (Eos)** non exécuté : aucune mesure.
14. **Machine unique / thermique laptop** (72–80 °C, secteur) : chiffres non transposables à un autre matériel.
15. **B0-u seedé à 17** (choix documenté, sans impact décisionnel) ; `selected_budget: null` pour B3/B4 (format).
16. **Test ouvert une seule fois**, sans possibilité de corriger a posteriori une métrique : toute nouvelle hypothèse exige un nouveau jeu réservé.
17. **Reload P6 non consigné séparément** (contrairement à P3/P2) : intégrité couverte par le hash gate 33/33, mais un test de rechargement en processus propre reste à faire pour clore P7.

## Ce qui aurait été fait autrement (sans mea culpa)

1. **Traiter la couverture du test de profondeur comme un critère de conception** : 23 % d'exclusions (81 % des B d10) affaiblissent la question H3 ; fixer `max_length` (ou la compacité des textes) dès le plan de données, pas après le figement.
2. **Figer tôt le protocole d'évaluation** (métrique de sélection, mode de précision, tolérance de rechargement) : les écarts P3a/P4b sur la sélection et bf16/fp32 ont coûté du temps et des artefacts « legacy ».
3. **Mesurer directement les comparaisons prévues** : R4 vs B3/B4 (et non seulement vs B2) dès le pipeline d'analyse ; un préenregistrement qui cite les deux côtés évite les ambiguïtés d'interprétation.
4. **Budgéter le sidecar sur k=1** vu la saturation observée dès le pilote ; k=4 a consommé du calcul GPU sans gain.
5. **Diagnostiquer la mémoire avant de figer l'architecture** : un sidecar lisant les candidats (et non H seul) aurait peut-être un signal ; les probes P4 le suggéraient déjà.
6. **Éviter le gate tel quel** : les features (marge/entropie) ne séparent pas corrections et dégradations ; soit features enrichies, soit gate par transitions supervisées.
7. **Baselines documentées dès P2** : la règle du « majoritaire » a dû être auditée après coup ; un script unique et testé pour B0/B1 aurait suffi.
8. **Plus de seeds (5) et un budget de latence pour R1/R2 full end-to-end** : les effets observés sont de l'ordre de la barre d'erreur.

---

## Addendum — Interprétations nuancées après audit externe (2026-09-24, post-clôture)

**Référence :** audit externe `DECISION-COPROCESSOR-AUDIT-RELANCE-V2.md`
(sha256 `fab4b37b…`), section §4. **Règle : aucun chiffre, aucune métrique, aucun
artefact modifié** — cet addendum ne change que des **interprétations**. Les verdicts
V1 (N1 ; H1–H4 non soutenues ; H5 mesures complètes) sont **inchangés** et l'audit ne
les conteste pas. Points nuancés :

1. **« La branche H est peu lue » ≠ « les faits ne sont pas utilisés ».** `q` (dernier
   état valide de Qwen) et les candidats encodés après l'état du problème peuvent déjà
   contenir les faits ; la conclusion correcte est **locale** : la branche mémoire
   supplémentaire apporte peu de sensibilité dans les conditions diagnostiquées, et les
   voies `q,c` contextualisées restent. De plus, l'ablation « mémoire mélangée » par
   permutation **conjointe** clés/valeurs/masque peut être **non concluante** :
   `Attention(Q, PK, PV) = Attention(Q, K, V)` — seule la mise à zéro est nettement
   informative. → les interventions causales (fait décisif modifié, état remplacé,
   mémoire d'un autre problème) sont plus probantes et fondent la V2 ; annexe technique
   de @ag-3 sur l'ablation « mixed » V1 en préparation.
2. **Les probes ne justifient pas l'exclusion de LoRA.** 25 exemples/famille, cibles
   partielles : un échec de probe ne démontre pas l'absence d'information, une réussite
   ne démontre pas son usage causal. LoRA n'est **ni démontrée nécessaire, ni exclue** ;
   tester l'extraction de plusieurs faits/états à différentes profondeurs (splits
   groupés) avant de conclure.
3. **L'instabilité sous permutation (~39 % par instance) est un défaut fonctionnel
   sérieux**, pas une simple curiosité d'agrégat : elle doit être traitée
   **architecturalement en V2** (encodage des candidats sans liste ordonnée + score
   partagé ou bloc de set équivariant), en mesurant le coût sur l'encodage. Les
   permutations de faits/instructions ont leur propre sémantique et ne sont pas couvertes
   automatiquement.
4. **Budget réel = ~1,28 époque** (38 399 présentations / 29 959 exemples retenus) :
   le plafond de 3 époques n'a pas été atteint et deux best B2 sont au dernier point
   évalué. La convergence n'est **pas tranchée** par les artefacts disponibles, donc les
   courbes V1 ne sont **pas concluantes** sur ce point ; vérifier la convergence
   (surapprentissage d'un petit ensemble, tâche à 1 étape, courbes loss/accuracy) avant
   d'augmenter les budgets.
5. **« B3 égale ou dépasse R sur les 3 seeds » est nuancé** : sur dev, R est légèrement
   supérieur sur **2 seeds** (s17 .5409 vs .5405 ; s43 .5485 vs .5472), B3 sur s29
   (.5469 vs .5452). La conclusion finale — **aucun avantage établi** en faveur du
   sidecar — est **inchangée**.
6. En complément : « le gate n'est pas en cause puisqu'il apprend sur train » n'est pas
   une conclusion valide (overfit, rareté des transitions utiles, qualité des features
   restent possibles) ; et les libellés de taxonomie (`chain_interrupted`) ne prouvent pas
   qu'une chaîne interne a été exécutée puis interrompue.

Ces nuances ont motivé la relance V2 (exécuteur de transitions supervisé, portes E0–E8) :
**la V1 n'a pas établi un mécanisme puis montré son inutilité ; le mécanisme visé n'a pas
été démontré** — notamment parce que la tête de correction V1 recevait `q, c_i`
directement (SPEC §5.6) et qu'une CE finale seule n'impose aucune progression d'état.

---

*Rapport produit par @ag-4, agent QA indépendant. Tous les scores ont été
recalculés depuis les prédictions sauvegardées ; aucune donnée, aucun modèle
et aucun seuil n'ont été modifiés (SPEC §16.1). Préenregistrement v2.1 figé ;
toute réinterprétation future exige une nouvelle expérience et un nouveau jeu
de test réservé (§11.7).*
