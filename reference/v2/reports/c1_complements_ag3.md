# C1 — compléments @ag-3 : anti-fuite publique, sweep budget, relecture des décodeurs

*Audit V22-confirmation (§2.3 même lecteur discret/continu, §8.2 inférence
strictement publique, §8.3 stabilité et première divergence ; Lot C1). Sorties
**versionnées séparées** : les scores publiés de `runs/c1_ablation/c1_ablation.json`
et les prédictions `*_pred_*.jsonl` ne sont JAMAIS réécrits. Garde `__main__`
ajouté à `run_c1_ablation.py` (incident « archive écrasée lors d'un import »).
Merge QA/REG-82 : la couche anti-fuite d'@ag-4 (structurelle, 3 200 items) est
portée dans le même artefact rejouable.*

## 1. Anti-fuite — **PASS** (trois couches, un seul artefact)

| couche | épreuve | résultat |
|---|---|---|
| **structurelle (@ag-4, 3 200)** | privé randomisé (edges/terminals/traces ; `nodes`/`options`/`query.start` CONSERVÉS) → identité de TOUS les tenseurs d'entrée | **3200/3200** identiques ; cibles gold changées 3200/3200 ; vérité changée 2292/3200 — source QA `scripts/qa_c1_replay.py`, exécution `reports/qa_c1_metrics.json`, commit `a10976e9` ; merge re-vérifié par la QA |
| **publique seule** | batch sans aucun champ privé ≡ chemin du harnais (mémoires) | R0 64/64 · R1 64/64 |
| **comportementale** | privé randomisé → prédictions du lecteur inchangées | R0 64/64 · R1 64/64 (vérité 48–49/64 changée) |

- Convention FIGÉE (nuance @ag-4) : `private.graph.options` est consommé par le
  mapping candidat→nœud ; il reste donc FIXE dans l'anti-fuite, ainsi que
  `nodes` et `query.start` (les champs dont la dérive fausserait le test). La
  permutation cohérente (renommage/réindexation ⇒ équivariance) est couverte
  séparément par les tests QA T2/T3 (`qa_tiebreak_stability.py`).
- Verdict : **PASS** ; `collate_public()` (texte/offsets/parse public)
  et la randomisation sont rejouables (`--mode anti-leak`), stamp toolchain.

## 2. Sweep budget 0/1/2/4/8/16/20 (mêmes poids, mêmes problèmes) — diagnostic

Toolchain de publication (torch 2.6.0+cu124, CUDA 12.4) : re-run
**exactement identique aux publiés** sur ce passage (0 flip / 3 200
prédictions soft ; deux passages indépendants concordants). La profondeur privée
n'est jamais utilisée pour choisir un budget (bancs seulement).

### R0 (E5v3-A figé)

| banc | 0 | 1 | 2 | 4 | 8 | 16 | 20 |
|---|---|---|---|---|---|---|---|
| B1-court | 0.233 | 0.422 | 0.603 | 0.895 | 0.863 | 0.855 | 0.855 |
| B2-prof6 | 0.200 | 0.198 | 0.195 | 0.233 | 0.853 | 0.843 | 0.838 |
| B3-prof8 | 0.205 | 0.210 | 0.212 | 0.300 | 0.860 | 0.855 | 0.853 |
| B4-prof10 | 0.250 | 0.260 | 0.268 | 0.328 | 0.420 | 0.863 | 0.855 |
| B5-surface | 0.223 | 0.400 | 0.590 | 0.910 | 0.865 | 0.853 | 0.853 |
| B6-distract | 0.233 | 0.407 | 0.593 | 0.892 | 0.853 | 0.835 | 0.833 |
| B7-options | 0.170 | 0.365 | 0.573 | 0.887 | 0.863 | 0.855 | 0.855 |
| B8-depart | 0.225 | 0.265 | 0.450 | 0.833 | 0.885 | 0.858 | 0.858 |

### R1 (A2)

| banc | 0 | 1 | 2 | 4 | 8 | 16 | 20 |
|---|---|---|---|---|---|---|---|
| B1-court | 0.233 | 0.435 | 0.672 | 0.998 | 0.998 | 0.998 | 0.995 |
| B2-prof6 | 0.200 | 0.188 | 0.180 | 0.165 | 0.998 | 0.998 | 0.998 |
| B3-prof8 | 0.205 | 0.200 | 0.182 | 0.185 | 0.990 | 0.998 | 0.998 |
| B4-prof10 | 0.250 | 0.237 | 0.223 | 0.250 | 0.287 | 0.998 | 0.998 |
| B5-surface | 0.223 | 0.435 | 0.642 | 1.000 | 1.000 | 1.000 | 1.000 |
| B6-distract | 0.233 | 0.440 | 0.685 | 1.000 | 1.000 | 1.000 | 1.000 |
| B7-options | 0.170 | 0.380 | 0.640 | 0.998 | 0.998 | 0.998 | 0.995 |
| B8-depart | 0.225 | 0.263 | 0.435 | 0.875 | 1.000 | 0.998 | 0.998 |

Lecture : budget 0 ≈ hasard ; R0 converge à ≈ profondeur+1 (prof 6/8 → 8 ;
prof 10 → 16, 0,42 à 8) puis **pic précoce + décroissance** (B1 0,895@4 →
0,855@20 ; B5 0,910@4 → 0,853@20) = fuite du lecteur figé qui s'accumule
au-delà de l'horizon utile ; R1 converge plus tôt (4 courts, 8 prof 6/8, 16
prof 10) et **plateau stable** (0,998–1,0). Avant l'arrivée du terminal,
l'argmax candidat porte sur des masses ~0 : le tie-break stable décide
(creux 0,16–0,19 à budget 4 en profondeur), à lire « pas encore de masse ».

## 3. Relecture `decode_hard`/`decode_soft` (§2.3) — findings et v2 alignés

Findings v1 : (1) confusion TERMINAL / auto-successeur (diagonale de A) ;
(2) tie-break index vs stable ; (3) horizon non borné ; (4) asymétrie départ
indéterminé + crash `A=None` ; (5) résidu « hors-candidats + INCONNU » non
scindé. Décodeurs **v2 alignés** : projection 3-canaux de la MÊME masse
pré-diagonale, tie-break stable identique (nœuds par label, puis TERMINAL, puis
INCONNU), horizon 20, symétrie mémoire vide, résidu scindé ; tests CPU.

Soft v2 ≡ soft v1 (**0 divergence**, 8 bancs × 2 lecteurs) ⇒ les publiés
restent valides. Hard aligné :

| banc-lecteur | hard v1 (publié) | hard v2 aligné | Δ pts |
|---|---:|---:|---:|
| B1-court-R0 | 0.8175 | 0.8100 | -0.75 |
| B1-court-R1 | 0.8575 | 0.8750 | +1.75 |
| B2-prof6-R0 | 0.6675 | 0.6650 | -0.25 |
| B2-prof6-R1 | 0.7775 | 0.7850 | +0.75 |
| B3-prof8-R0 | 0.5750 | 0.5775 | +0.25 |
| B3-prof8-R1 | 0.8200 | 0.8450 | +2.50 |
| B4-prof10-R0 | 0.5575 | 0.5500 | -0.75 |
| B4-prof10-R1 | 0.8275 | 0.8425 | +1.50 |
| B5-surface-R0 | 0.8250 | 0.8175 | -0.75 |
| B5-surface-R1 | 0.8750 | 0.8875 | +1.25 |
| B6-distract-R0 | 0.8150 | 0.8100 | -0.50 |
| B6-distract-R1 | 0.8475 | 0.8550 | +0.75 |
| B7-options-R0 | 0.8175 | 0.8100 | -0.75 |
| B7-options-R1 | 0.8575 | 0.8750 | +1.75 |
| B8-depart-R0 | 0.7850 | 0.7850 | +0.00 |
| B8-depart-R1 | 0.8175 | 0.8300 | +1.25 |

Deltas petits pour R0 (−0,75…+0,5 : rares auto-successeurs prédits),
**systématiquement positifs pour R1 (+0,75…+2,25)** : plus les distributions
sont fines, plus la projection alignée compte.

## 3bis. R-A (REG-82) — probs + résidu PAR ITEM et Brier COMPLET

Archives par item (16 fichiers `runs/c1_ablation/c1_probs_lb_<banc>_<lecteur>.jsonl`,
budget 20) : `truth`, `cand`, `p_cand`, `p_inconnu`, `p_hors_candidats`,
`residu_total`, `answer`, `ok`. Convention déclarée : classes = candidats
∪ {AUTRE}, P(AUTRE) = p_inconnu + p_hors ; gold hors candidats → classe AUTRE
(0 cas sur ces bancs). Brier recalculable depuis les seules archives
(`brier_scores()`, testé) :

| banc-lecteur | Brier candidats-seuls | Brier complet (+AUTRE) | p_INCONNU moy. | p_hors moy. |
|---|---:|---:|---:|---:|
| B1-court-R0 | 0.22333 | 0.29983 | 0.09888 | 0.01055 |
| B1-court-R1 | 0.00354 | 0.00525 | 0.00347 | 0.00019 |
| B2-prof6-R0 | 0.29481 | 0.44372 | 0.19089 | 0.00945 |
| B2-prof6-R1 | 0.00186 | 0.00206 | 0.00279 | 0.00079 |
| B3-prof8-R0 | 0.30732 | 0.46321 | 0.20166 | 0.02281 |
| B3-prof8-R1 | 0.00788 | 0.01182 | 0.00748 | 0.00198 |
| B4-prof10-R0 | 0.34313 | 0.58264 | 0.27729 | 0.04223 |
| B4-prof10-R1 | 0.00757 | 0.01189 | 0.00631 | 0.00395 |
| B5-surface-R0 | 0.22906 | 0.30851 | 0.10637 | 0.00471 |
| B5-surface-R1 | 0.00082 | 0.00159 | 0.00178 | 0.00040 |
| B6-distract-R0 | 0.25133 | 0.33720 | 0.10414 | 0.01445 |
| B6-distract-R1 | 0.00226 | 0.00376 | 0.00379 | 0.00093 |
| B7-options-R0 | 0.22339 | 0.29946 | 0.09888 | 0.01007 |
| B7-options-R1 | 0.00354 | 0.00525 | 0.00347 | 0.00018 |
| B8-depart-R0 | 0.24467 | 0.34730 | 0.13507 | 0.00562 |
| B8-depart-R1 | 0.00131 | 0.00131 | 0.00037 | 0.00017 |

Le Brier publié (candidats-seuls) ne voyait ni la masse INCONNU ni la masse
hors-candidats ; le complet les intègre. Signature déjà connue : R1 ≈ 0,003–0,012
vs R0 0,17–0,46 ; la part INCONNU de R0 en profondeur (≈0,20 sur B3) est la
fuite mesurée au §2. Pour R1, p_hors ≤ p_inconnu ≤ 0,008 : masse résiduelle
négligeable.

## 4. Reproductibilité et première divergence (§8.3)

- **Intra-session** : deux instances du même checkpoint, forwards répétés →
  H, A et réponses **bit-identiques**.
- **Inter-toolchain** : torch 2.6.0+cu124 reproduit les publiés
  **exactement** (0 flip sur 3 200, deux passages) ; torch 2.14.0+cu130 diverge
  sur **37 items** / 3 200 (2–7 par banc, ≤0,75 pt).
- **Première divergence localisée** : pour les items divergents, le tenseur
  **H du backbone** diffère entre toolchains (bitwise=False, écart max 1,12–1,70
  en bf16), alors que A et la réponse sont des fonctions déterministes de H
  intra-toolchain ⇒ la divergence naît au **forward backbone** (noyaux
  bf16/SDPA), en amont des têtes et du décodeur.
- Conséquence : toute assertion « exactement == publié » doit être rejouée dans
  le toolchain de publication ; sinon tolérance (1,5 pt) + diff item-par-item.
  Les JSON sont stampés `toolchain`/`cuda`.

## 5. Artefacts

- `runs/c1_ablation/c1_antileak.json` (3 couches, PASS) ;
- `c1_sweep_lb.json` + `c1_review_hard_lb.json` (toolchain publication,
  autoritatifs : sweep, Brier, repro, hard v1/v2) ; `c1_sweep.json` +
  `c1_review_hard.json` (torch 2.14, table de drift) ;
- `c1_probs_lb_<banc>_<lecteur>.jsonl` ×16 (probs par item, R-A) ;
- `scripts/run_c1_complement.py` (`--mode anti-leak|sweep|review`, `--tag`,
  `--archive-probs`, `brier_scores`, `randomize_private`, `structural_antileak`) ;
- `tests/test_c1_complement.py` (7 tests CPU) ; garde `__main__` sur
  `scripts/run_c1_ablation.py` (aucune sémantique changée).
- Renvois croisés QA (commit `a10976e9`) : `scripts/qa_c1_replay.py`
  (couche structurelle d'origine), `reports/qa_c1_metrics.json` (3200/3200),
  `qa_tiebreak_stability.py` (T2/T3 permutation cohérente),
  `v22_loader_impact_matrix.md`.
