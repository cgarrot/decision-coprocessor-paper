# 12 — Timeline: 2026-09-24 10:08 → 2026-09-25 (ongoing)

*Reconstructed from git histories, registries, run logs and reports. All times are local (CEST).*

## Act I — V1 execution (09-24, 10:08 → 22:11)

| Time | Commit | Event |
|---|---|---|
| 10:08 | — | Agent mesh created; initial missions @ag-1 → @ag-2/3/4/5 |
| 12:07 | `55d0390` | Bootstrap: skeleton, schemas, configs, GPU lock |
| 12:37 | `ffa6df2` | **P0 passed** (first judged non-passable by QA, then fixed); architecture decision: raw format, no chat template |
| 12:41 | `7cdd007` | **P1 data**: 53,500 examples, independent audit 0 violations, 123 green tests; reserves M1–M3 |
| 13:03 | `31a71f4`/`0a49a19` | **Pilot B2 = 0.455 dev**; **dataset freeze** (sha256 manifest); invalid run #1 documented |
| 15:05 | `070cc57` | **Phase A**: B2 ×3 seeds, dev macro ≈ .55, reload ×3 PASS |
| 15:09 | `060b8de` | QA: "document and proceed" (selection-metric deviation); pre-reg v1.1 |
| 15:40 | `38ebdea` | P4 diagnostics (memory, saturation, probes, permutations) |
| 15:46 | `696c7cc` | Gate G4 code |
| 20:19 | `88f959f` | **P3b**: R/B3/B4 ×3 seeds (~4 h 50 GPU) — H1 modest, H2 not demonstrated, k = 1 saturation |
| 20:50 | `2a7a69f` | **Permutation erratum** (harness metric bug) + position-uniformity audit |
| 21:05 | `5444a7d` | Calibration fix |
| 21:33 | `9072258` | **P5 gate** (20 % retention, H4 not demonstrated) + **P6 matrix executed** (66 JSONL, conforming) |
| 22:04 | `0381f31` | **V1 final report**: N1 reached, H1–H4 not supported |
| 22:09 | `2b6bc23` | **P7**: bundle, reload 0.0, CLI end-to-end |
| 22:11 | `c2586ae` | **Closure review**: "CLOSED WITH RESERVES" (R1–R12) |

## Act II — V1 post-closure (09-24, 22:16 → 23:43)

| Time | Commit | Event |
|---|---|---|
| 22:16 | `2636f1f` | Export fixes R1–R11: versioned weights, committed scripts, prediction archive, complete manifests |
| 22:20 | `160b230` | **QA addendum**: R1–R3/R6/R7/R10 resolved; R5 partial; R8/R9 accepted |
| 22:30 | — | Compaction dossier produced; 15/15 key numbers re-verified |
| 22:49–22:56 | — | **External audit read**; V2 repository created; `DECISION-V2.md` GO + 9 amendments |
| 23:43 | `c0f4fad` | Technical annex on the V1 "mixed" ablation (real batch-axis destruction; 0 flips reinforce "memory branch barely read") |

## Act III — External audit (09-24 evening)

**Key recommendation:** *"Do not immediately rebuild the whole system. Start with a verifiable transition executor on a single family, then reconnect language."* → **GO** with 9 amendments (isolation, CPU-first, explicit anti-shortcut, absorbing terminal + fixed budget, simplified family B, fixed α, registry from E0, V1 test ≠ V2 test, documentation corrections).

## Act IV — V2 stage S (09-24 22:49 → 09-25 00:36, pure CPU)

| Time | Commit | Event |
|---|---|---|
| 23:43 | `abb0ede5` | **E0 complete**: simplified family-B data contract + traces, anti-shortcut executor vS, gates E0–E2 frozen, registry infra, 42 green tests |
| 23:54 | `f31315a1` | **E1 PASS** (1.000 autonomous trajectory) + **E2 PASS** (919/919 zero-shot, depth 4 unseen); readout index>9 anomaly traced |
| 00:20 | `31d9589e` | **E3 PASS after diagnostic**: lr 3e-3 failure (diffuse pointer, 0.000) → lr 1e-3: 1.000; causal k-sweep 0.188@k0 → 1.000@k4; executor 1.000 vs direct 0.204 |
| 00:26 | `7ec0386d`/`58b7d36f` | QA E3/E4 + **E4 PASS zero-shot 6/8/10 (1.000)** + **E4b pad20: stress 399/399** |

Along the way, **two E0 bugs found and fixed** (pointer not reinjected: ~2-hop ceiling; terminals frozen at init), with registered prudence note REG-36: *"a ~2-hop ceiling can come from the assembly, not the task"* — retrospective on V1 saturation, without touching V1 conclusions.

## Act V — V2 stage T + closure (09-25, 01:15 → 10:34)

| Time | Commit | Event |
|---|---|---|
| 01:15 | `d21ef166` | **E5-prep**: text pools 1999/400/400, extractor (tagger + mentions + bilinear), validator + exact solver, frozen criteria, H cache infra; 71 green tests |
| 02:24 | `7b61f7f3` | **E5-it1 honest MISS** (edges 0.766 PASS, start 0.37 MISS) + **direct interventions: dominant surface bias** → reader v3 |
| 02:35 | `24f45e44` | E5-it2 closed — interventions verdict **AMBIGUOUS** → **branch B** (QA v1.2: data remediation first) |
| 03:00 | `db4a1f88` | **Branch B**: E5v2 pool generated (2049/411) + lexical harness: old pool 0.220 (chance) — direct's 0.78 was a distributional shortcut, not trivial lexical |
| 03:32 | `688d1d8e` | Parse v2 wiring + QA v1.4: **T conclusion conditions** = beat direct AND follow causally |
| 04:12 | `92cf48f5` | E5v2-it2-prep: deterministic containment start (one variable) |
| 04:22 | `8e4904eb` | **E5v2-it2**: start 1.000, 3/4 gates — pipeline (c) 0.333 ≈ direct 0.326; controlled-noise D1 |
| 04:52 | `87a0f7f9` | Multi-layer pre-check L14+L21 readable → LoRA postponed for it3; QA v1.7bis (train-only layer choice) |
| 05:05 | `55afefca` | v1.7ter: layers frozen train-only, GO it3 |
| 06:25 | `9c4cd33a` | **E5v2-it3 closed**: 3/4 (solve 0.248 MISS); Δ(cn−d) +5.1 [−1.4, +11.7] **grey zone**; weak (c) interventions (decisive 0.388) → **(iii) local failure**; `E5v2_eval` sealed |
| 06:30 | `dc8d7383` | **QA it3 verdict**: documented local failure + inconclusive benefit published separately; **E5v3-A conditional**; no it4 |
| 07:23 | `4b8582e9` | **User GO E5v3-A (LoRA)**: configs hashed before start, fairness F1, pre-registered abstention F4; erratum params 92,802 |
| 07:40 | `766c31a6` | **OOM1 fix**: `train()` before forward; run cancelled and relaunched, config sha unchanged |
| 08:58 | `aa7caf19` | **LoRA reader 4/4** (edge 0.928, solve 0.762) — exact n = 411 re-eval after window fix |
| 10:30 | `54bd7b73` | **E5v3-A closed**: adapted direct **1.000** dominates pipeline 0.762 (**Δ −23.8 [−28.3, −19.6]**); direct causal profile 0.996/0.996/0.988; **issue (iii) definitive**; branch 2 automatic |
| 10:33 | `f0e57f85`/`a79631a1` | **V2 closure**: final report, DECISION-V2 addendum, bundle reload PASS (8/8 + 8/8); costs registered |
| 10:34 | `b76d6f94` | **Final QA validation (addendum v1.9)**: independent recalculation — issue (iii) + closure (T) confirmed; registry `qa_validated` ×3; 3 reserves published |

## Act VI — V2.1 frozen validation (09-25, ≈11:00 → 14:00)

| Time | Event |
|---|---|
| ≈11:26 | QA pre-registration review: GO conditional, 5 audit requirements transcribed |
| ≈11:40 | V2.1 protocol pre-registered; benches generation (seeds 2205–2212) |
| 12:06 / 12:40 | Harness self-test Q0 PASS (device + non-regression values in log; rerun) |
| 12:57 | Batch invariance artefact (GPU batch 1 vs 8) |
| 13:44–13:53 | QA pre-reg review DONE → Q1 metrics recalculated → `v21_results.md` published; **depth reversal confirmed** |
| 13:50 | Deterministic parser (p) delivered: coverage 1.0, agreement 1.0 (3200/3200) |
| 13:49 | `det_parser_v21.json`; complementarity (123/172/163) published; Q4 line 2: work on the interface |

## Act VII — V2.2 interface ablations (09-25, 14:03 → ongoing)

| Time | Event |
|---|---|
| 14:03 | **V2.2 protocol pre-registered** (commit `c40a168a`): A1 frozen-reader propagation, A2 distributional retraining, criteria Δ ≥ +5 pts B3 IC > 0; stable eps tie-break |
| 14:11–14:14 | A1 run |
| 14:15 | A1 documented FAIL (Δ B3 = −38.25 pts) |
| 14:22 | Root cause found and registered: `successor_bilinear` head never supervised in fact mode (top-1 0.054); A1-bis spec pre-registered |
| 14:35–14:40 | **A1-bis executed** (fact-level transition matrix, zero training) |
| 14:52 | QA addendum D: **A1-bis PASS validated**, c_prop 0.83–0.86 invariant in depth, Δ vs direct +57.25 pts at depth 8 |
| 14:55 | A1 archive regenerated on GPU bit-identical; `__main__` guards added to all runners (QA incident resolution) |
| 15:04–15:28 | **A2 run 1** — cancelled (gradient checkpointing inactive → OOM; selection eval gold/predicted mismatch) |
| 15:25–15:31 | Fixes committed; **A2 relaunched with frozen config unchanged** |
| 15:42 | Snapshot: A2 at step 300/1200 — selection c_prop **0.99**, b_discret 0.9125–0.9675 |

**At snapshot:** 20 commits in V1, 51 in V2 (71 total), ≈29 h of continuous work, V2 compute ≈ 4.96 h (stage S included), V2.2/A2 running.
