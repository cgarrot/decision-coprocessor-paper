# v2model — notes exécuteur S (@ag-3)

Étage S (entrée structurée exacte), CPU pur. Contrat de données : celui de
@ag-2 (`data_contract.md`) ; métriques de référence : `v2eval` (@ag-4).

## API (3 lignes d'architecture)

1. **État** : un vecteur par entité `h ∈ R^{B×N×d}` + distribution de pointeur
   `p_t = softmax(pointer_head(h_t))` ; `s_0` = `one-hot(départ)` (contrainte de
   tâche) ; le terminal (nœud sans successeur — information publique) est
   **absorbant structurel** une fois atteint.
2. **Transition partagée** : messages `m_i = Σ_j p_j·φ(h_j, h_i, rel_ji)/Σ_j p_j`
   (front d'onde émis par l'état actif), cellule locale `GRUCell([m_i, question,
   p_i])` ; le `h` du terminal pointé ne change plus.
3. **Lecture finale** : score **partagé** `MLP([summary(p_T,h_T), features
   brutes du candidat])` — ni `q` ni `c_i` contextualisés ; `DirectScorer` est
   un module séparé (aucun paramètre partagé).

## Diagnostic E0 (deux corrections nécessaires)

1. **Pointeur non réinjecté** : sans `p_i` dans la transition ni messages émis
   par le pointeur, le modèle plafonnait à ~2 sauts (52-55 % de trajectoire).
   L'état est désormais `(h, p)` et le front d'onde est porté par `p`.
2. **Terminal gelé trop tôt** (bug décisif) : `has_successor` figeait le `h`
   des terminaux **dès l'initialisation**, donc le front d'onde ne pouvait
   jamais les atteindre ; le modèle n'apprenait que les nœuds internes.
   Le gel ne s'applique plus qu'à un terminal **déjà pointé** ; le pointeur
   reste absorbant par règle structurelle.
   Après correction : **100 % de trajectoire complète sur E1 en 500 étapes**
   (α=0.5, lr 3e-3), profondeurs 1/2/3 confondues.

## Perte pilote

`L = CE(finale) + α · Σ_t w_t · CE(état_t, cible_t)` avec les poids par créneau
du contrat @ag-2 (`trace_loss_weights_budget16`, somme 1, masse absorbante
répartie). **α = 0.5** au pilote (à consigner au registre E0-6 ; toute
modification = nouvelle entrée). Amorçage (`teacher_forcing=True`) et
déroulement autonome sont mesurés séparément (E1/E2).

## Implémentation

- `src/v2model/relation_data.py` : `batch_from_problems` (objets `v2data.bfamily.Problem`
  ou dicts `input`/`private`), `batch_from_public_inputs` (inférence, **aucune**
  cible privée) ; features = one-hot d'entité uniquement (pas de drapeau
  terminal, qui est privé) ; cibles et poids séparés du forward.
- `src/v2model/executor.py` : `ExecutorConfig`, `RelationExecutor`,
  `SharedTransition`, `PointerHead`, `CandidateReadout`, `DirectScorer`.
- `src/v2model/train.py` : `TrainConfig`, `train_executor`, `trajectory_metrics`,
  `metrics_from_outputs` (E0-3, valeurs recalculées à la main dans les tests).
- `tests/test_v2model_{contracts,executor,gradients,mechanism}.py` : 21 tests.

## Préparation E3 (pré-enregistrée, NON lancée)

- Deux branches figées avant run : `configs/e3.yaml` (lecture `concat`, réf.) et
  `configs/e3_tied.yaml` (lecture `tied` : candidats projetés par le **même**
  `memory_encoder` que les états — correction de l'anomalie d'identité E2 pour
  les index non vus). `ExecutorConfig.readout_kind ∈ {concat, tied}` ;
  `TiedCandidateReadout` garde l'anti-raccourci (summary + features brutes).
- Entrées registre : `E3-official-concat-s0` et `E3-official-tied-s0`
  (`register` sans `start` ; le CLI n'a pas de `--dry-run`). Une seule branche
  sera lancée après recommandation QA ; l'autre reste "registered".
- Script `scripts/run_e3.py` versionné avant run : autonome + teacher séparés,
  conditionnelle à état correct (denominateurs), trajectoire complète, réponse
  finale, par profondeur, corrections/dégradations vs `DirectScorer` séparé,
  coût. Seuils proposés : autonome ≥0.90, conditionnelle ≥0.98.

## Portes E1/E2 officielles (2026-09-24)

- **E1-official-s0 : PASS.** Autonome trajectoire complète **1.000 (128/128)**, finale
  1.000 ; teacher-forced finale 1.000 ; loss 2.2696 → 7.84e-05 ; d1/d2/d3 = 1.000 ;
  452 s, 700 mises à jour, 22 400 exemples, 92 802 params *[erratum v2, cf. REG-42 — initialement publié 88 322]*. Artefacts `runs/e1/`
  (`metrics.json`, `model.pt`) + `predictions/e1/{autonomous,teacher_forced}.jsonl`.
- **E2-official-s0 : PASS (critère principal).** Zéro-shot poids E1 sur `data/E2.jsonl`
  (335 problèmes inédits, 13-15 nœuds, profondeurs 1-4) : exactitude de l'état suivant
  avec états d'entrée **exacts = 1.000 (919/919)**, par profondeur 1.000 (d4 jamais vue
  incluse), rôles base 767/767 + decisive_edge 152/152 ; 1,32 s. Artefacts `runs/e2/` +
  `predictions/e2/{transitions,autonomous}.jsonl`.
- **Anomalie E2 (secondaire, hors critère)** : pointeurs autonomes 100 %, mais lecture
  finale 0.725 ; split par index : réponse > 9 → 25,3 % (n=87) car E1 n'a que ≤10 nœuds
  (index 0-9, jamais d'identité entraînée au-delà), ≤ 9 → 88,7 % (léger écart de
  généralisation de lecture). La transition est intacte. E3 (13-16 nœuds, E3_train 855)
  est requis avant toute revendication au niveau réponse autonome — non lancé.
- Rapports : `reports/e1.md`, `reports/e2.md`.

## Vérification sur artefacts disque (2026-09-24)

`batch_from_problems` validé directement sur `data/{E1,E2,E3_train,E3_eval}.jsonl`
(@ag-2) : `state_targets` == `trace_padded_indices_budget16`, poids par créneau
de somme 1, `candidate_ids` == ids d'options, `answer_index` == `answer_id`,
forward fini, et `batch_from_public_inputs` n'expose **aucune** cible privée.
N = 10 (E1) / 13 (E2, E3), Kmax = 5. Les pools E3 (855/255, paires contrôlées)
sont prêts pour les interventions causales §2.6 au moment venu.

## Commandes

```bash
cd decision-coprocessor-v2
uv run pytest -q          # suite V2 complète : 42 passed (~1 min 20)
```

## Points ouverts / honnêteté

- E1/E2 officiels restent à exécuter et enregistrer (@ag-5/@ag-4) ; le test
  mécanisme atteint déjà le critère E1 (≥ 99 % trajectoire complète) sur
  `build_E1()`, mais un run de porte dédié avec prédictions sauvegardées est requis.
- Les métriques `trajectory_metrics`/`metrics_from_outputs` sont des
  diagnostics d'entraînement ; la QA doit confirmer que `v2eval` les reproduit
  (E0-3 : une seule implémentation pour sélection ET évaluation).
- `alpha=0.5` n'est pas encore inscrit dans `registry/experiment_registry.jsonl`
  (infra @ag-5).
