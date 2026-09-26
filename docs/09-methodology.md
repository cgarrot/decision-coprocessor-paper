# 09 — Methodology: pre-registration, independent QA, fairness, evidence rules

## 1. Organisation

The project was executed by a mesh of five specialised agents over roughly 36 hours of wall-clock time, with an explicit separation of powers:

| Agent | Role |
|---|---|
| **@ag-1** | orchestrator: decisions, budgets, gate closures, arbitration |
| **@ag-2** | data: generators, oracles, pools, manifests, anti-duplicate control |
| **@ag-3** | models: architecture, wiring, training recipes, technical annexes |
| **@ag-4** | **independent QA**: re-implementation of oracles, recalculation from archived predictions, gate validation, reserve publication |
| **@ag-5** | infrastructure: experiment registry, config hashing, costs, GPU lock, environment inventory |

The user interacted through an `@ag-ask` channel; user GO was required for any new budget (for example E5v3-A LoRA, V2.2). Independence of QA was structural: the QA never wrote the artefacts it validated, and its findings could block gates (they did: v1.1, v1.3, v1.7bis, v1.8, R7/R11, REG-74).

The `role="assistant"` ledger, the append-only research register (`research_register.md`, 86 entries REG-01…REG-86) and the experiment registry (`experiment_registry.jsonl`, 160+ entries) record observations, hypotheses and tests with dates and statuses.

## 2. Pre-registration

Every experiment followed the same cycle:

1. **Protocol document written first**, containing: hypothesis, variables, frozen thresholds, stop conditions, prohibited analyses.
2. **Config files hashed (sha256) and registered** in an append-only registry **before** the run starts (`status = registered` → `running` → `pass/fail/blocked`).
3. **Scripts committed before use** (absolute rule since V2 v1.8, item 4) so that no analysis code can be tuned to the results.
4. **Results published in the report**, then QA either validates, annotates or contests.

Examples of the rule binding in practice:

- V1 pre-registration went through v1.0 → v1.1 → v2.0 → v2.1 before the reserved test was opened; open order (21:05 vs predictions 21:10) is verifiable from mtimes and commits.
- V2's E5 reader layer choice was **rejected by QA** because the pre-check had been computed on dev; a train-only split was produced and the choice frozen on train only.
- V2.2/A1-bis has a dedicated pre-registration document (`V22_A1BIS_SPEC.md`) with a registry hash, after QA noted that the original hash pointed to a document that did not mention A1-bis.

## 3. Independent QA and recomputation

The QA's method is constant: **recompute from archived per-item predictions**, never trust executor logs.

- V1: 66 prediction files, counts 3997/3080/3993, hash gate 33/33, bootstrap recomputation, paired counters re-derived.
- V2 executor gates: QA recomputed E2 (919/919), E3, E4b (399/399) from `predictions/`.
- V2.1: 8/8 benches recomputed identically (blessing of the "gevé" mode); the parser (p) reproduced with coverage/agreement 1.0.
- V2.2 A1/A1-bis: item/flag-level comparison, 0 disagreement; incident and provenance documented.
- Edge-F1 definition discrepancy (0.7043 QA vs 0.7252 harness) traced to terminal edges (`mention → FIN`): with FIN, QA reproduces 0.7252 exactly; published definition; no verdict affected.

## 4. Statistics

- **Paired comparisons** on the same problems: `group_id` unit, coupled grouped bootstrap 2000 replicates, 95 % CI.
- Seeds: V1 used 3 seeds (17/29/43) for a confirmatory test; V2.1/V2.2 used 1 existing seed and are labelled **descriptive** with CIs **conditional on the measured checkpoints** (bootstrap over examples/groups, not over training runs).
- **Multiplicity awareness**: one primary comparison is fixed per study; everything else is labelled exploratory.
- Exactness guards: `n` and denominators printed everywhere ("always assert your denominators" — a lesson paid for by the n = 814 eval bug).

## 5. Gates, stop rules, and evidence levels

- V1: N1/N2/N3 levels; pre-registered branches (S-negatif, S-B3/B4, S-saturation) decided the verdict without improvisation.
- V2: conditional gates E0–E8; E0–E2 are prerequisites (learning the mechanism), not generalisation evidence; E8 (gate/export) is conditional on demonstrated utility and was never built.
- Stop rules applied as written: no mastered transition → stop depth claims; structured OK/text failed → attack extraction; no gain at higher cost → no gate to hide it.
- Three publication levels, used consistently: **experiment stop** vs **local scientific conclusion** vs **product validation** (the last never claimed).

## 6. Fairness rules (the project's most transferable contribution)

**F1 — Representation fairness before comparison.** Any advantage (extra layers, adaptation, context) must be offered to *both* the decomposed path and the direct control, with identical configs. This rule **inverted a conclusion** (see below).

**F2 — Cache invalidation.** If backbone weights change (LoRA), any cached hidden state is invalid by construction; caches are keyed by adapter state.

**F3 — No selection on evaluation data.** Layer choices, thresholds and checkpoints are chosen on train/dev (and in V2.2 on a fresh selection bench), never on evaluation benches. A distinct, explicit label is attached to development campaigns: V2.1 benches were held out from training and checkpoint selection but observed during the adaptive V2.1→V2.2 campaign, so they are *development* evaluation; independent confirmation requires fresh benches and seeds (C2: 2214–2216, blind selection protocol).

**F4 — Pre-registered abstention, symmetric.** Any abstention rule must be frozen before the run and given to both paths; primary metric all-in (abstention = error), coverage/risk published separately.

**The demonstration that F1 matters:** on the frozen backbone, the decomposed pipeline was marginally ahead of the direct path (Δ +5.1 pts, inconclusive). Once **both** received the same LoRA adaptation: direct 1.000, pipeline 0.762 → Δ −23.8 pts. The apparent benefit of decomposition was an artefact of crippling the baseline. Any comparison between a pipeline and a direct control that does not equalise representation budgets is measuring the crippling, not the decomposition.

## 7. Mechanism before benefit

From V2 v1.8 onward, a registered precedence rule:

> **Mechanism takes precedence over benefit.** A Δ without a causal profile cannot validate a decomposition; a strong causal profile without Δ does not justify it either.

Operationally, a claim of usefulness requires *both*: a paired benefit with CI low > 0 **and** a causal profile (decisive-fact following, distractor stability, option-permutation stability, broken-chain handling) at pre-registered thresholds with n ≥ 200–250. This is why it3's +5.1 pts was published as a **grey zone** leading to issue (iii), not as a win.

## 8. Evidence rules for mechanism

Four minimal mechanistic measures, all required (`QA_MECHANISTIC_CHECKLIST.md`):

1. **full-trajectory accuracy** (autonomous roll-out, not teacher-forced);
2. **transition accuracy conditional on a correct input state** (denominator explicit);
3. **autonomous roll-out** at depths never trained;
4. **paired causal interventions** (decisive fact changed → answer must change; distractor changed → answer stable; options permuted → answer stable by id; state replaced → compatible continuation; memory of another problem → answer must follow the source).

Probes, attention maps, state norms and error taxonomies are diagnostics; they never substitute for these four.

## 9. Incident handling: invariants as detectors

The project treats incidents as data and publishes them with root causes. Notable ones and the invariants that caught them:

| Incident | Detector | Resolution |
|---|---|---|
| E0 pointer not reinjected (~2-hop ceiling) | diagnostic overfit plateau at 52–55 % | state `(h,p)`, wavefront by pointer |
| E0 terminals frozen at init | terminals never reached (histogram) | freeze only already-pointed terminals |
| E3 lr 3e-3 collapse (trajectory 0.000) | gate metrics + single-problem/curriculum diagnostics | lr 1e-3, new registry id |
| E5 v1 defective bench | lexical probe + causal interventions | bench archived; E5v2 rebuilt |
| Duplicate ids → 2–14/250 pair mismatches | errata counted; positional matching | construction-level fix; `opt_map` archived |
| OOM1 (`train()` after forward, GC off, dropout off) | VRAM 7.6 vs 2.1 GiB invariant | run cancelled; config hash unchanged on relaunch |
| Eval windows overlapping (n = 814 not 411) | denominator assert | exact re-eval; obsolete history flagged |
| A1 archive overwritten by QA import (CPU) | mtime + value change | runner guards; GPU regeneration bit-identical |
| A2 run 1 corrupted selection (gold/predicted mismatch) | c_prop implausible | run cancelled; eval re-anchored; relaunch unchanged config |

The recurring lesson: **assert your denominators, and distrust any number that moved without a committed reason.**

## 10. Threats to validity (as published)

1. V1: 3 seeds, depth coverage amputated by 512 tokens, gate non-selective, latency batch-1.
2. V2-T: dev-only negative (n = 411), 1 seed per path, adaptive campaign (checkpoint selection on dev), direct 1.000 from a single run, no confirmatory test opened.
3. V2.1/V2.2: descriptive, CIs conditional on measured checkpoints; inter-environment (CPU/GPU) variance ≈ 6 pts on dev, hence environment-bound labels; benches are synthetic French, family B, chain tasks.
4. Broken-chain "det" not evaluable on these pools (0/411; structural) — semantics fixed for future work, requirement propagated to all future pools.
