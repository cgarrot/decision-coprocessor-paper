# 00 — Overview

*Snapshot: 2026-09-25. This document is the shortest complete tour of the project.*

## 1. One paragraph

The *Decision Coprocessor* project studies whether a **small, explicitly computational module** attached to a small language model can improve **multi-step decisions** on a single 8 GB laptop GPU. The project ran in two major acts. **V1** trained a latent recurrent *sidecar* on top of a frozen Qwen3-0.6B and lost to a plain direct head — a documented negative result. An external audit then showed that the targeted mechanism (sequencing dependent operations in latent space) had never actually been demonstrated in the V1 assembly. **V2** rebuilt the idea from first principles: a **transition executor** on an explicit graph state, supervised with exact state traces. Stage **S** (structured input) demonstrated a learned, composed, causally useful transition to depths never seen in training. Stage **T** (text input) closed the loop with a LoRA-adapted reader — and produced the project's central scientific negative: *under a fair comparison, the decomposed text→graph→executor pipeline (0.762) is dominated by the adapted direct path (1.000)*. Post-closure diagnostics (**V2.1**) then found a **depth reversal**: the direct path collapses beyond depth 6 while the decomposed pipeline holds, and (**V2.2**, ongoing) traced the bottleneck to **discretisation at the interface**, recovering c_prop ≈ 0.85 invariant in depth by propagating successor distributions without any retraining.

## 2. The five acts

| Act | Period (2026) | Content | Verdict |
|---|---|---|---|
| I. V1 execution | 09-24 10:08 → 22:11 | 53,500 oracle-generated examples; frozen Qwen3-0.6B; direct head B2; recurrent sidecar R1/R2/R4; controls B3/B4; gate G4; pre-registration; reserved test opened **once** | N1 reached; H1–H4 not supported — clean negative |
| II. V1 post-closure | 09-24 22:16 → 23:43 | Export fixes R1–R11; QA addendum; "mixed" ablation annex | R1–R3/R6/R7/R10 resolved |
| III. External audit | 09-24 evening | 546-line critique: 6 interpretation corrections, 3 benchmark defects, proposed V2 architecture, gates E0–E8 | GO with 9 amendments |
| IV. V2 mechanism (stage S) | 09-24 22:49 → 09-25 00:36 | Supervised transition executor on structured relations (92,802 params, pure CPU); anti-shortcut readout; E0→E4b | All pass: learned, composed (depth 10 zero-shot), causal (k-sweep 0.188→1.000), robust (399/399) |
| V. V2 text (stage T) + closure | 09-25 01:15 → 10:34 | Text→graph→executor connection: E5 (benchmark found defective), E5v2 iterations (frozen reader), E5v3-A (LoRA, representation fairness) | Stage S **demonstrated**; stage T **cleanly refuted**; direct path (1.000) dominates decomposition (0.762) |
| VI. V2.1 validation | 09-25 ≈11:40 → 14:00 | Frozen checkpoints on 8 new sealed benches (n=400): depth 1–10, surface, distractors, options, start; error attribution; deterministic parser control | **Depth reversal**: pipeline wins at depth 6–10 (+14/+32/+25 pts); deficit localised to path edges; ceiling 0.95 |
| VII. V2.2 interface ablations | 09-25 14:03 → ongoing | A1 (frozen-reader distribution propagation) **failed** (unsupervised head → noise); A1-bis (fact-level transition matrix, zero training) **passed**: c_prop 0.83–0.86 invariant in depth; A2 (distributional retraining + UNKNOWN sink) **running** | Interface confirmed as the bottleneck; A2 status at snapshot: step 300, selection c_prop 0.99 |

## 3. What was actually demonstrated

1. **A transition operator can be learned, composed, and causally verified** on a controlled relational task with a tiny CPU model (92,802 parameters) — including zero-shot depths 6/8/10/16, with no state divergence, and with paired causal interventions.
2. **A depth-generalising interface exists without retraining**: propagating successor distributions instead of taking per-edge argmax removes the depth decay of a frozen reader (c_prop ≈ 0.85 for depths 1→10 vs 0.80→0.56 for discretisation).
3. **Fair-comparison discipline changes conclusions**: the frozen-backbone comparison showed the decomposition marginally ahead (+5.1 pts, inconclusive); once *both* paths received the same LoRA adaptation, the direct path jumped to 1.000 and the pipeline to 0.762. The apparent benefit was an artefact of crippling the baseline.
4. **What was not demonstrated**: that explicit decomposition is *useful* on this text domain under equal representation budgets; that the frozen direct path survives depth; that the 1.000 direct number generalises (1 run, dev-only, adaptive campaign); and any product-level claim.

## 4. Methodological core (the durable part)

- **Pre-registration with hashed configs** before every run; no threshold moved afterwards.
- **Independent QA agent** recalculating metrics from archived per-item predictions, not from executor logs.
- **Sealed test sets** never opened: V1's reserved test opened exactly once after pre-registration; V2's `E5v2_eval` (seed 1107) was sealed forever; V2.1 benches are pure evaluation; V2.2 uses seed 2213 for selection only.
- **Anti-shortcut contracts**: unique successor, multiple terminals, renamed entities, shuffled facts, no private field in public inputs — all tested.
- **Causal interventions over probes**: modify the decisive fact / add distractors / permute options / change the start node, with oracle-verified expected answer changes.
- **Honest incidents**: 2 E0 bugs, a failed E3 learning-rate collapse, a defective E5 benchmark, duplicate-id matching bug, an OOM caused by `train()` after forward, an eval-window bug, and a QA archive contamination — all documented with root causes and invariant-based detection.

## 5. Reading paths

- **Just the results:** [`paper/PAPER.md`](../paper/PAPER.md) §Results, then [`docs/10-results-reference.md`](10-results-reference.md).
- **The model:** [`docs/04-v2-transition-executor.md`](04-v2-transition-executor.md) and [`docs/02-v1-frozen-backbone-sidecar.md`](02-v1-frozen-backbone-sidecar.md).
- **The data:** [`docs/08-data-generation.md`](08-data-generation.md).
- **The method:** [`docs/09-methodology.md`](09-methodology.md) and [`docs/12-timeline.md`](12-timeline.md).
- **The story:** this file, then [`docs/13-lessons.md`](13-lessons.md).
