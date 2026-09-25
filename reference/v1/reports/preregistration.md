# Préenregistrement — Decision Coprocessor (SPEC §11.7)

# **VERSION 2.1 — FIGÉE (amendement du 2026-09-24 21:00)**

- **Date de figement :** 2026-09-24, 20:35 ; **amendement v2.1 :** 2026-09-24,
  21:00 (Europe/Paris). **Rédaction et signature :** @ag-4 (évaluation
  indépendante), sur instruction de @ag-1.
- **Portée :** tout ce document est **gelé avant l'ouverture du test final**.
  Toute modification après le figement produit une **v2.x** avec justification
  au `CHANGELOG.md` ; aucune règle de sélection, de métrique, de seuil ou
  d'exclusion ne peut être modifiée après l'ouverture (§1.4.7, §11.7).
- **Historique :** v1.0-draft (2026-09-24) · v1.1 (écart de sélection Phase A,
  `reports/p3a_review.md`) · **v2.0 figée** (matrice finale, agrégation
  multi-seeds, cadre de décision, latence) · **v2.1** (§9bis : erratum
  permutation, protocole de précision d'évaluation, convention de seed du
  gate).

---

## 1. Question et hypothèses

**Question :** un petit module récurrent (sidecar), ajouté après l'encodage
d'un backbone gelé, améliore-t-il les décisions nécessitant plusieurs
opérations dépendantes, à coût réel acceptable sur RTX 3070 Laptop 8 Go ?

- **H1 utilité** — le sidecar améliore l'exactitude sur les tâches de
  composition par rapport au chemin direct (même backbone).
- **H2 récurrence** — une partie du gain persiste face à un module non
  récurrent à budget de paramètres comparable (B3) et à un contrôle de coût
  comparable (B4).
- **H3 généralisation** — le gain ne se limite pas aux profondeurs/structures
  vues à l'entraînement.
- **H4 efficacité** — une politique 0/4 (G4) conserve une fraction mesurable
  du gain sans activer systématiquement le sidecar.
- **H5 fiabilité** — erreurs, calibration et dégradations mesurées.

**Contexte dev honnête (avant test réservé, ne préjuge pas du test) :**
R4−B2 = +0.57/+0.90/+0.90 pt (3/3 seeds, net corrections +17/+27/+27) ;
**B3 égale ou dépasse R** sur les 3 seeds ; **R1 ≈ R4** (saturation dès 1
étape). H2 est donc **non démontrée sur dev** et H4 n'est conditionnelle qu'à
un gain fixe. Le cadre §7 préenregistre les conclusions pour chacun de ces
scénarios sans ajustement post-hoc. Un résultat négatif documenté reste un
résultat valide (§1.4.1).

## 2. Données (figées)

- **Manifeste :** `artifacts/datasets_manifest.json`,
  `frozen_at = 2026-09-24T13:20:00+02:00`, 11 fichiers, hashes sha256
  (16 premiers caractères consignés). @ag-4 a vérifié 11/11 le 2026-09-24.
  Au moment de l'ouverture du test, re-vérification obligatoire ; tout écart
  invalide l'ouverture.
- **Splits :** Train 30 000 · Dev 3 000 · Router-train 3 000 · Router-dev
  1 500 · Calibration 2 000 · Test IID 4 000 · Test profondeur 4 000 · Test
  composition 4 000.
- **Unité d'échantillonnage = `group_id`** (paraphrases/permutations/contre-
  factuels dans le même split) ; le bootstrap ré-échantillonne des groupes.
- Le pilote (`pilot_*`) n'entre dans aucun résultat.

### 2bis. Règle d'exclusion > 512 tokens (décidée maintenant, identique partout)

**Règle gelée :** sérialisation identique pour toutes les variantes, tokenizer
à la révision `c1899de289a04d12100db370d81485cdf75e47ca`, `max_length = 512` ;
tout exemple dépassant 512 tokens est **exclu, compté et identifié**, **sans
troncature** (§10.6). La même règle s'applique à Train, Dev et aux **3 splits
test**. Les exclusions sont **décidées avant l'ouverture** (table ci-dessous,
calculée par @ag-4) et le rapport final publie les compteurs + les courbes par
profondeur sur le sous-ensemble conservé.

| Split | Total | Rejetés >512 | Conservés | Tokens max |
|---|---:|---:|---:|---:|
| train | 30 000 | 41 | 29 959 | 596 |
| dev | 3 000 | 3 | 2 997 | 567 |
| test_iid | 4 000 | 3 (B d4) | 3 997 | 565 |
| **test_depth** | 4 000 | **920** | **3 080** | 1 083 |
| test_composition | 4 000 | 7 (B d3/d4) | 3 993 | 541 |

**Couverture `test_depth` par famille × profondeur (conservés / rejetés) :**
A_rules d6 444/0 · d8 433/5 · d10 **300/142** · indéterminés 69/7 ;
B_relations d6 353/114 · d8 **191/276** · d10 **90/376** ;
C_programs d6/d8/d10 400/0 chacun.

**Limitation préenregistrée :** à 512 tokens, le test de profondeur
**sous-couvre fortement B_relations à d8/d10** (59 % et 81 % des exemples
exclus) et partiellement A_rules d10 (32 %). Les conclusions de H3 pour ces
cellules sont **conditionnelles à la sous-population conservée** ; elles
seront publiées comme telles. Aucune régénération, troncature ou extension de
longueur ne sera effectuée après l'ouverture ; une couverture complète
éventuelle relèverait d'une **nouvelle expérience préenregistrée** (hors P6).

**Liste complète des exclusions figée :** `artifacts/test_exclusions.json`
(sha256 `cbde987a9c999401604ea2f18bfe2ca6c1e8dd4fea015dac797f4252ba091283`) :
ids exclus par split/famille/profondeur, compteurs conservés/rejetés,
révision tokenizer et règle. À re-vérifier à l'ouverture du test.

## 3. Variantes préenregistrées (matrice finale)

| ID | Définition | Init | Params entraînés | Budget d'inférence | Sélection |
|---|---|---|---:|---|---|
| B0-u | Tirage uniforme seedé | — | 0 | — | — |
| B0-m | Classe majoritaire par famille (règle documentée) | — | 0 | — | — |
| B1 | Backbone gelé, logits des codes à leur position réelle, renormalisés sur les codes autorisés (§6.2) | backbone épinglé | 0 (596 049 920 gelés) | 0 | — |
| B2 | Backbone gelé + tête dynamique | Train, seeds 17/29/43 | **1 054 209** | 0 | dev macro-acc (v1.1) |
| B3 | B2 + module non récurrent lisant H, budget de paramètres comparable | B2 même seed gelé | **2 178 177** | 0 | dev macro-acc |
| B4 | B2 + blocs non partagés, coût ≈ 4 étapes | B2 même seed gelé | **5 270 785** | 0 | dev macro-acc |
| R | B2 + sidecar récurrent (bloc partagé) | B2 même seed gelé | **2 110 465** | 1/2/4 | dev macro-acc @ budget 4 |
| R1/R2/R4 | Mêmes poids R évalués à 1/2/4 étapes | — | — | 1, 2, 4 | — |
| G4 | Politique 0/4 sur sorties gelées | modèles gelés | gate ≤ plafond | 0 ou 4 | seuils Router-dev (gate seed 17, pairé B2_s17↔R4_s17 — §9bis.A3) |

**G4 est conditionnelle :** ajoutée à la matrice **uniquement si P5 est
exécutée** (potentiel de correction démontré en P4, §9.1). Si P5 est exécutée,
le checkpoint du gate et les valeurs de λ sont enregistrés par une **annexe
datée de la v2.1 autorisée à l'avance par la présente section** (aucune autre
règle modifiée ; convention de seed précisée en §9bis.A3).
Si P5 est omise, G4 est absente de la matrice et aucune revendication de
compromis de latence (H4) n'est formulée.
**EXT (Eos 0.8B) : informatif uniquement**, hors matrice de décision.

## 4. Entraînement, plafonds et checkpoints (figés)

- **Seeds :** 17, 29, 43 pour B2/B3/B4/R. Gate (si P5) : seed 17.
- **Plafonds effectifs (identiques aux phases exécutées) :** AdamW lr 3e-4,
  weight_decay 0.01, warmup_ratio 0.05, clip 1.0, microbatch 2,
  effective_batch_size 32 (accumulation explicite), `max_epochs 3`,
  `max_optimizer_steps 1200`, `eval_every_steps 100`, `eval_microbatch 8`,
  `backbone_feature_cache false`, `max_length 512`.
- **Sélection :** B2/B3/B4 → `dev_macro_accuracy` (macro **globale** sur dev
  filtré, familles présentes, argmax masqué — définition v1.1) ; R →
  `dev_macro_accuracy_budget4`. Steps retenus : B2 1000/1200/1200 ;
  R 200/700/800 ; B3 200/800/800 ; B4 300/700/800.
  **Rappel v1.1 :** le checkpoint B2 est le « checkpoint du plateau retenu par
  la Phase A, métrique de sélection corrigée ensuite » (écart documenté).
- **Rechargement :** chaque bundle rechargé en processus propre, **dans le mode
  d'évaluation figé (§9bis.A2 : autocast bf16)**, comparaison des logits dev,
  tolérance `max_abs_diff ≤ 1e-2` **et argmax identique sur ≥ 99,9 %** des
  exemples rechargés (une divergence supérieure bloque la porte) ; le mode est
  consigné dans le manifeste (`eval_precision: autocast-bf16`).
- **Checkpoints évalués (best) et sha256 — figés :**

| Checkpoint | Fichier | sha256 |
|---|---|---|
| `runs/p3_main/b2_s17/best/` | `head.safetensors` | `96112465abc61e02c3c7c1830f9d459d37a2f6e9248f126d398e5cc7bb19cb25` |
| `runs/p3_main/b2_s17/best/` | `manifest.json` | `b59b576abf1722b7afa7b6601feec17e5562fa14ec15c046461b6b22c393f3b0` |
| `runs/p3_main/b2_s29/best/` | `head.safetensors` | `1ab852da66ccae3cf97061c8913b0bf6de1b868bf236ffd380477bdba9a448c5` |
| `runs/p3_main/b2_s29/best/` | `manifest.json` | `7ff6fea6743b3d6b19fd9fdfce608b2158da611bf647f117be8e1baec03ccef1` |
| `runs/p3_main/b2_s43/best/` | `head.safetensors` | `0ac515468760423442f1e11d227aa5ad73bb8667e9c47b25c2df46408a1b449e` |
| `runs/p3_main/b2_s43/best/` | `manifest.json` | `078bcee8c83d9d1fb201f9a4cba46a8eeb9d0286e976c69e3e45828eecaffe78` |
| `runs/p3_main/b3_s17/best/` | `control.safetensors` | `6d743e4d0b9207b31f5665beafa0983719c93543b90961a7c0db883d664e2459` |
| `runs/p3_main/b3_s17/best/` | `head.safetensors` | `96112465abc61e02c3c7c1830f9d459d37a2f6e9248f126d398e5cc7bb19cb25` |
| `runs/p3_main/b3_s17/best/` | `manifest.json` | `f75c99a9e11aa1f097613e9094cf37ce7a3aa8901198f2e26b3bcd3f8746806d` |
| `runs/p3_main/b3_s29/best/` | `control.safetensors` | `c5a331b9805bd9fbb3ef0502cf3729f2a610fde65bc0b69a272670928cfd5e08` |
| `runs/p3_main/b3_s29/best/` | `head.safetensors` | `1ab852da66ccae3cf97061c8913b0bf6de1b868bf236ffd380477bdba9a448c5` |
| `runs/p3_main/b3_s29/best/` | `manifest.json` | `9da1b49d43b4fe18ce43fd4daee92a31b5c15280ea9fda1dcac9cfa2e9113964` |
| `runs/p3_main/b3_s43/best/` | `control.safetensors` | `572d60273dfd82b69b92dbc4bdbf37d8e8bec06720d6365251280fc1d7db49c2` |
| `runs/p3_main/b3_s43/best/` | `head.safetensors` | `0ac515468760423442f1e11d227aa5ad73bb8667e9c47b25c2df46408a1b449e` |
| `runs/p3_main/b3_s43/best/` | `manifest.json` | `3970d943c26061e9ac9629b8165b4f1c517dd244cd1d766eb60a474c97caa29f` |
| `runs/p3_main/b4_s17/best/` | `control.safetensors` | `a9c6a557ed7c6b845e072c6215e10036037112a5c0438b1daddcb48187632f71` |
| `runs/p3_main/b4_s17/best/` | `head.safetensors` | `96112465abc61e02c3c7c1830f9d459d37a2f6e9248f126d398e5cc7bb19cb25` |
| `runs/p3_main/b4_s17/best/` | `manifest.json` | `6a31099defbad8a88b6d5a366fc84e282bfc9a95869e6f17bb6d672f2d7d8a24` |
| `runs/p3_main/b4_s29/best/` | `control.safetensors` | `3802491e4dfaa278198c14723edb6a7f6e91bf649c513210a463a9d30bfcb12e` |
| `runs/p3_main/b4_s29/best/` | `head.safetensors` | `1ab852da66ccae3cf97061c8913b0bf6de1b868bf236ffd380477bdba9a448c5` |
| `runs/p3_main/b4_s29/best/` | `manifest.json` | `20188f3eca47c9bd9714b13bebfe9442de314e0927d64ecc7c32dffcc034d513` |
| `runs/p3_main/b4_s43/best/` | `control.safetensors` | `5ab3a17d7f806d0d1d10cc69e156a333ce2157994ebcfc0a0faf3c38d7ecdfe7` |
| `runs/p3_main/b4_s43/best/` | `head.safetensors` | `0ac515468760423442f1e11d227aa5ad73bb8667e9c47b25c2df46408a1b449e` |
| `runs/p3_main/b4_s43/best/` | `manifest.json` | `b83eee2acbbc297a6a4950b3ee24e7152a2321da004f5a2da1ea195347993736` |
| `runs/p3_main/r_s17/best/` | `head.safetensors` | `96112465abc61e02c3c7c1830f9d459d37a2f6e9248f126d398e5cc7bb19cb25` |
| `runs/p3_main/r_s17/best/` | `manifest.json` | `d04938f823c1ed9fd7c4c4c99a812394ccd41640a1f6ef1551b42d2ec3bd2656` |
| `runs/p3_main/r_s17/best/` | `sidecar.safetensors` | `9dfe1375872fdb863b1f823986ebd747979fb7f5bc884d8b19a6a0f40770d88f` |
| `runs/p3_main/r_s29/best/` | `head.safetensors` | `1ab852da66ccae3cf97061c8913b0bf6de1b868bf236ffd380477bdba9a448c5` |
| `runs/p3_main/r_s29/best/` | `manifest.json` | `a174e2eab7b1905d814c80e04fe5bb954a649bd2daaa6b0f6676c6de0b2d84dd` |
| `runs/p3_main/r_s29/best/` | `sidecar.safetensors` | `1b5ef4f6ebbc4b91f2402d5f4f772953f86065becae746a76bcbc2a7c31fb3ab` |
| `runs/p3_main/r_s43/best/` | `head.safetensors` | `0ac515468760423442f1e11d227aa5ad73bb8667e9c47b25c2df46408a1b449e` |
| `runs/p3_main/r_s43/best/` | `manifest.json` | `29590c0a1b7d3f6cb548e98e35e887f9109056817d7550cef403b7aa51c3c182` |
| `runs/p3_main/r_s43/best/` | `sidecar.safetensors` | `f0df3805c866457b11ee53a18224c191bdc294b98a842d53a35b849afc49c9da` |

## 5. Matrice d'évaluation finale

**Variantes × splits :**

| | test_iid (3 997) | test_depth (3 080) | test_composition (3 993) |
|---|---|---|---|
| B0-u, B0-m, B1, B2, B3, B4 | ✅ | ✅ | ✅ |
| R1, R2, R4 | ✅ | ✅ | ✅ |
| G4 (si P5) | ✅ | ✅ | ✅ |

- **Critère principal (inchangé) :** exactitude **macro des familles cœur
  A_rules / B_relations / C_programs sur `test_depth`**, sur le sous-ensemble
  conservé, agrégée sur les 3 seeds (§6).
- **Secondaires :** même macro sur `test_iid` et `test_composition` ;
  garde-fou D_control (dégradation ≤ 1 pt) ; NLL, Brier, ECE (equal_width 15
  bins, construction publiée) ; courbes par profondeur (None exclu) et par K ;
  corrections/dégradations appariées ; taux de rejet par cellule ;
  **stabilité sous permutation** (§9bis.A1 : exactitude permutée **par
  identifiant de candidat** + flips par id, rapportée mais **jamais** critère
  de décision) ; paraphrases.
- **G4 (si exécutée) :** mêmes splits, plus le couple qualité/latence du §8.

## 6. Agrégation multi-seeds et construction exacte des intervalles

- Pour une variante V et une seed s, on dispose des prédictions par exemple
  (`correct ∈ {0,1}`) sur chaque split conservé.
- **Métrique de seed** `M_{V,s}` = macro A/B/C sur le split considéré.
- **Métrique agrégée** `M_V = (1/3)·Σ_{s∈{17,29,43}} M_{V,s}`.
- **Delta apparié** `Δ_{V,W} = (1/3)·Σ_s (M_{V,s} − M_{W,s})`, en **points**.
- **Bootstrap groupé (B = 2000, unité `group_id`)** : pour chaque réplique b,
  tirer les groupes du split avec remise (même tirage pour **toutes** les
  variantes et **toutes** les seeds — bootstrap couplé) ; recalculer `M_{V,s}`
  sur les exemples tirés ; agréger sur les seeds (`M_V^{(b)}`, `Δ_{V,W}^{(b)}`).
  IC 95 % = percentiles 2.5/97.5 de la distribution des répliques.
  **Le nombre d'exemples n'est jamais multiplié par 3** : `n_examples` = nombre
  d'exemples conservés, `n_groups` = nombre de groupes indépendants.
- **Lecture :** supériorité = borne basse de l'IC du delta > 0 ; infériorité =
  borne haute < 0 ; **équivalence/non-conclusion** = IC contient 0. Les trois
  deltas par seed sont publiés (dispersion), ainsi que la moyenne/écart-type.
- Les prédictions de chaque (variante, seed) sont sauvegardées au format
  §14.5 (listes **ou** dicts indexés par `candidate_id`, validés par le module
  d'évaluation) ; chaque score est recalculé depuis ces fichiers.

## 7. Cadre de décision (préenregistré, sans ajustement post-hoc)

**Niveaux §12.1 :**
- **N1 (faisabilité)** : runs complets, rechargements PASS, scores recalculables
  depuis les prédictions, aucune violation de protocole → déclaré.
- **N2 (gain)** : `Δ_{R4,B2}` sur `test_depth`, borne basse IC > 0. L'objectif
  §12.2 « ≥ 3 points » est déclaré **atteint** si de plus l'estimation
  ponctuelle ≥ 3 pts, sinon « atteint au sens de la signification, objectif
  chiffré non atteint » — sans requalification.
- **N3 (intérêt spécifique)** : N2 **et** `Δ_{R4,B3}` borne basse > 0 **et**
  `Δ_{R4,B4}` borne basse > 0 **et**, si G4 exécutée, rétention ≥ 70 % du gain
  R4 et cibles de latence §8 respectées. Si G4 n'est pas exécutée, N3 n'est pas
  déclaré ; le rapport conclut « avantage sur les contrôles, volet adaptation
  non testé ».

**Scénarios préenregistrés (le test tranche, le rapport constate) :**
- **S-B3** `Δ_{R4,B3}` → non significatif ou négatif : **H2 non démontrée** ;
  si B3 égale R à coût ≤, B3 est recommandé comme variante efficace ; le gain
  est attribué à la capacité/mémoire non récurrente (§2.2). N3 non déclaré.
- **S-depth-only** : gain significatif sur `test_depth` mais IC contenant 0 sur
  `test_iid` et `test_composition` → N2 sur le critère principal, **H3 non
  démontrée** (généralisation limitée à la profondeur) ; publié explicitement.
- **S-saturation** `Δ_{R4,R1}` IC contient 0 (attendu d'après dev) →
  récurrence multi-étapes non démontrée ; R1 retenu comme variante efficace ;
  H2 non démontrée. Résultat scientifique valide (§12.2).
- **S-négatif** `Δ_{R4,B2}` IC contient 0 → N2 non atteint ; résultat négatif
  documenté ; P5 omise ; conclusion au niveau N1.
- **S-B4** B4 ≥ R4 sur le critère principal → gain expliqué par le contrôle de
  coût/paramètres ; H2 non démontrée ; N3 non déclaré.
- **Garde-fou D** : dégradation D_control = (acc_D(B2) − acc_D(V)) en points ;
  violation déclarée si > 1 pt (estimation ponctuelle agrégée) ; IC publié.
- **Mémoire** : cible GPU ≤ 6,5 Gio + 1,0 Gio de marge et arbre hôte ≤ 22 Gio,
  sinon critère mémoire déclaré non tenu.
- **Reproductibilité** : tout échec de rechargement ou d'incohérence de hash
  invalide la conclusion correspondante.

## 8. Protocole de latence et de coûts (préenregistré)

- **Harnais :** CUDA events + synchronisation ; **scope `unit`** par requête ;
  **batch 1** comme mesure principale ; batches supportés sans OOM (1/4/8)
  rapportés séparément, jamais comparés comme la même latence.
- **Longueurs fixées :** 128, 256, 512 tokens. **≥ 30 répliques de warm-up**
  exclues, **200 requêtes chronométrées** par cellule.
- **Scopes mesurés séparément :** encodage backbone ; readout direct ; sidecar
  (par budget) ; gate ; **temps complet depuis entrée préparée** ; **temps
  complet depuis texte brut** (tokenisation + transferts inclus).
- **Publication :** p50/p95/p99, moyenne et distribution (pas seulement le
  minimum) ; `p99` signalé comme peu stable si n < 500 ; aucun temps agrégé par
  batch présenté comme unitaire (§14.5) ; extraction de cache mesurée à part
  (jamais incluse silencieusement dans l'end-to-end).
- **Cibles G4 (si P5) :** latence moyenne ≤ 1,25 × B2 et p95 ≤ 2 × B2 sur un
  workload fixé ; rétention ≥ 70 % du gain de R4 sur B2 quand ce gain > 0.
- **Mémoire :** VRAM pic allouée et réservée (nvidia-smi/pyTorch), arbre de
  processus hôte ; machine sur secteur, état thermique consigné, un seul job
  GPU à la fois.

## 9. Ouverture du test et engagements anti-dérive

1. Test ouvert **une seule fois**, après figement (v2.0) et re-vérification des
   hashes de données et de checkpoints (§2, §4).
2. **Aucun ajustement post-hoc** : checkpoints, seuils, températures, features
   de gate et hyperparamètres sont gelés. Toute nouvelle hypothèse issue du
   test part dans une **nouvelle expérience** avec jeu réservé neuf.
3. Toutes les cellules préenregistrées sont publiées, y compris défavorables ;
   aucune sélection de résultats.
4. Chaque score est recalculé depuis les prédictions JSONL par
   `decision_coprocessor.evaluation` (bootstrap groupé §6).
5. Les scripts de calcul (dont B0/B1) sont committés et exécutables avant P6.
6. @ag-4 ne modifie ni modèle, ni donnée, ni seuil pour améliorer un score
   (§16.1).

## 9bis. Amendement v2.1 — trois points figés avant ouverture

### A1. Erratum P4 — permutation : métrique secondaire corrigée, jamais un critère

Le §4 de `reports/p4_diagnostics.md` (« biais d'ordre massif », .512→.240)
était un **artefact de métrique** : le harnais comparait l'index argmax du
chemin **permuté** à l'index gold du chemin **original** (`reports/p4b_permutation_audit.md`).
Valeurs corrigées **par identifiant de candidat** : B2 **+0,4 pt**, R4 **+0,2 pt**,
B3 **−1,0 pt**, B1 **+1,4 pt** — l'exactitude est **stable** sous permutation.
L'instabilité par instance (~39 % de flips pour B2/R4/B3, 70 % pour B1) est
réelle mais **déjà présente sans sidecar** (propriété du pipeline causal +
lettres), et ne doit pas être présentée comme un défaut du sidecar.

**Règle figée :** la stabilité sous permutation est une **métrique secondaire à
rapporter** (exactitude permutée par id de candidat + flips par id, protocole
`reports/p4b_permutation_audit.md`), **explicitement non décisionnelle**. L'argument
« le gain ne survit pas aux permutations » est **retiré** ; le caveat publié est
l'instabilité par instance, et le diagnostic fort contre le sidecar reste
§13.1 (mémoire H quasi non lue).

### A2. Protocole de précision d'évaluation (test final) — AUTOCAST BF16

Constat P4b §5 : 0,4–2,4 % de désaccords d'argmax par exemple entre les évals
P3 (autocast bf16) et un rejeu FP32, concentrés sur des **égalités quasi
parfaites** (marges top-2 ≈ 0,001–0,10 logit) ; exactitudes globales
identiques (.512 / .518).

**Choix figé : toutes les évaluations finales (B0→G4, 3 seeds, 3 splits) sont
faites en `autocast` bf16, identique au mode de sélection des checkpoints et
aux artefacts P3.** Justification : (1) cohérence de mode — aucune
comparaison ne réintroduit l'écart métrique découvert en P4b ; (2) les
désaccords sont des départages sur quasi-égalités, sans biais en faveur d'une
variante ; (3) c'est le mode de déploiement (§10.4) et ~2× plus rapide, ce qui
permet la campagne test + latence complète.

**Précisions d'exécution :** le forward backbone/modules tourne sous autocast
bf16 ; les logits sont **castés en FP32 pour le softmax, l'argmax et toutes
les métriques** (§10.4) ; le mode est consigné dans chaque run
(`eval_precision: autocast-bf16`). Aucun basculement de mode après ouverture ;
un écart bf16↔fp32 n'est **pas** une violation de reproductibilité (il est
attendu et borné à ~2,4 % de flips sur quasi-égalités), alors qu'un écart
de rechargement **dans le même mode** l'est (tolérance §4 :
`max_abs_diff ≤ 1e-2` et argmax identique ≥ 99,9 %).

### A3. Convention de seed du gate G4 — confirmée et figée

**G4 est pairée par seed : les features proviennent de B2_s et R4_s de la
MÊME seed** ; le gate est entraîné sur Router-train (optimiseur/RNG de seed
17, identique pour toutes les paires), les seuils et λ sont choisis sur
Router-dev, puis G4_s est évaluée sur les 3 splits test de la seed s ;
l'agrégation §6 (moyenne des seeds, bootstrap groupé couplé) s'applique.
Donc, pour l'exécution minimale en cours : **G4 ≡ B2 s17 vs R4 s17**, conforme
à `configs/gate.yaml` (`seeds: [17]`) et au §4 du présent document.

**Extension multi-seeds :** si P5 n'a produit que la paire s17, G4_s29 et
G4_s43 sont marquées **[NON EXÉCUTÉ]** (aucune substitution ni mélange de
seeds) ; la revendication H4/N3 est limitée à « volet adaptation testé sur
s17, non répété », avec dispersion non estimable publiée et application de la
formule §6 restreinte aux seeds disponibles (1/3). Le checkpoint du gate et
les λ seront ajoutés en **annexe d'enregistrement datée (même version 2.1)**
dès la fin de P5, sans modifier aucune règle ci-dessus.

## 10. Modification de version

Toute modification de ce document après ouverture du test exige une **v2.x**
motivée au `CHANGELOG.md` et, si elle touche une comparaison déjà ouverte, un
**nouveau jeu de test réservé**. Les seules adjonctions pré-autorisées sont
l'enregistrement du checkpoint G4 et des λ si P5 est exécutée (§3, annexe
datée de la v2.1).

---

**Signé : @ag-4 (évaluation indépendante) — v2.0 figée le 2026-09-24 20:35,
v2.1 amendée le 2026-09-24 21:00. Contreseing attendu : @ag-1 (orchestrateur).**
