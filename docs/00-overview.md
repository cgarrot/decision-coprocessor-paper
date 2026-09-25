# 00 — Overview

*Snapshot: 2026-09-25 evening. All programs (V1, V2, V2.1, V2.2) are closed; the paper and this compendium reflect the final state.*

## 1. One paragraph

The *Decision Coprocessor* project studies whether a **small, explicitly computational module** attached to a small language model can improve **multi-step decisions** on a single 8 GB laptop GPU. The project ran in two major acts. **V1** trained a latent recurrent *sidecar* on top of a frozen Qwen3-0.6B and lost to a plain direct head — a documented negative result. An external audit then showed that the targeted mechanism had never actually been demonstrated in the V1 assembly. **V2** rebuilt the idea from first principles: a **transition executor** on an explicit graph state, supervised with exact state traces. Stage **S** (structured input) demonstrated a learned, composed, causally useful transition to depths never seen in training. Stage **T** (text input) closed the loop with a LoRA-adapted reader and produced the central initial negative: *under a fair comparison, the decomposed text→graph→executor pipeline (0.762) was dominated by the adapted direct path (1.000)*. Post-closure diagnostics then rebuilt the picture: **V2.1** found a **depth reversal** (the direct path collapses beyond depth 6 while the decomposed pipeline holds), and **V2.2** traced the bottleneck to **discretisation at the interface** — then fixed it. Propagating successor distributions (zero training first; then supervised distributional training) makes the pipeline accurate **0.995–1.000, invariant in depth**, beating the direct path on **8/8 sealed benches** (up to **+71.75 pts** at depth 8), beating the deterministic parser ceiling, and dominating **even when the direct path receives identical auxiliary supervision** (+50 to +75 pts in depth) — while the architectural core costs ≈1.3–1.5 % of end-to-end latency.

## 2. The five acts (all closed)

| Act | Period (2026) | Content | Verdict |
|---|---|---|---|
| I. V1 execution | 09-24 10:08 → 22:11 | 53,500 oracle-generated examples; frozen Qwen3-0.6B; direct head B2; recurrent sidecar R1/R2/R4; controls B3/B4; gate G4; pre-registration; reserved test opened **once** | N1 reached; H1–H4 not supported — clean negative |
| II. V1 post-closure | 09-24 22:16 → 23:43 | Export fixes R1–R11; QA addendum; "mixed" ablation annex | R1–R3/R6/R7/R10 resolved |
| III. External audit | 09-24 evening | 546-line critique: 6 interpretation corrections, 3 benchmark defects, proposed V2 architecture, gates E0–E8 | GO with 9 amendments |
| IV. V2 mechanism (stage S) | 09-24 22:49 → 09-25 00:36 | Supervised transition executor on structured relations (92,802 params, pure CPU); anti-shortcut readout; E0→E4b | All pass: learned, composed (depth 10 zero-shot), causal (k-sweep 0.188→1.000), robust (399/399) |
| V. V2 text (stage T) + closure | 09-25 01:15 → 10:34 | Text→graph→executor connection: E5 (benchmark found defective), E5v2 iterations (frozen reader), E5v3-A (LoRA, representation fairness) | Stage S **demonstrated**; stage T **refuted under fairness**; direct path (1.000) dominates (0.762) on short chains |
| VI. V2.1 validation | 09-25 ≈11:40 → 14:00 | Frozen checkpoints on 8 new sealed benches (n=400): depth 1–10, surface, distractors, options, start; error attribution; deterministic parser control | **Depth reversal**: pipeline wins at depth 6–10 (+14/+32/+25 pts); deficit localised to path edges; ceiling 0.95 |
| VII. V2.2 interface ablations | 09-25 14:03 → 19:06 | A1 FAIL (unsupervised head), A1-bis PASS (zero training, 0.85 invariant), A2 PASS (distributional training, 0.995–1.000), A3 (equal-supervision direct control), router bound, costs | **The interface was the whole deficit**: architectural superiority of propagation validated 8/8; router useless; propagation ≈1.3–1.5 % of latency |

## 3. What was actually demonstrated (final state)

1. **A transition operator can be learned, composed, and causally verified** on a controlled relational task with a tiny CPU model (92,802 parameters) — zero-shot depths 6/8/10/16, no state divergence, paired causal interventions.
2. **The interface, not the executor nor the information, was the pipeline's bottleneck.** The deterministic parser reaches 1.0 coverage/agreement; the executor is 1.000 at depth 10; the discretised reader decays with depth.
3. **Propagating successor distributions fixes the depth decay twice over.** Zero training: 0.83–0.86 invariant, CIs > 0 on 8/8. Supervised distributional training (A2): 0.995–1.000, above the parser ceiling, Δ vs direct positive 8/8 on sealed benches.
4. **The gain is architectural, not a supervision artefact.** A3 — the direct path with the *same* auxiliary heads, targets, augmentation and recipe — stays collapsed in depth (0.2475–0.2825 at depths 8/10 vs A2 0.9975); Δ(A2−A3) goes from +3.25 pts (short) to **+75.0 pts** (depth 8), CIs excluding zero on 8/8.
5. **A router is unnecessary.** The oracle router bound is +0.00 to +0.50 pts over A2 alone: the propagation pipeline absorbed the V2.1 complementarity entirely.
6. **Fair-comparison discipline twice changed the conclusions.** Frozen-backbone decomposition looked ahead (+5.1 pts) until both paths received the same LoRA adaptation (−23.8 pts); A2's benefit could have been supervision until A3 received the same auxiliary targets (architectural superiority held).
7. **What remains genuinely open**: UNKNOWN/partially observed worlds (defined but not evaluated), harder benches beyond the B5/B6 saturation, multi-seed confirmation, OOD generalisation — all declared out of V2.2 scope.

## 4. Methodological core (the durable part)

- **Pre-registration with hashed configs** before every run; no threshold moved afterwards.
- **Independent QA agent** recalculating metrics from archived per-item predictions, not from executor logs (REG-74→81; all V2.2 gates closed by QA).
- **Sealed test sets** never opened: V1's reserved test opened exactly once; `E5v2_eval` (seed 1107) sealed forever; V2.1 benches pure evaluation; V2.2 selection only on seed 2213.
- **Anti-shortcut contracts**: unique successor, multiple terminals, renamed entities, shuffled facts, no private field in public inputs — all tested.
- **Causal interventions over probes**; oracle diagnostics in separate tables, never counted as scores.
- **Mechanism before benefit**, and **equal budgets before claiming architectural effects** (F1 applied to representations in V2-T, then to auxiliary supervision in V2.2/A3).
- **Honest incidents**: E0 bugs, an lr collapse, a defective benchmark, duplicate-id matching, OOM-by-`train()`-after-forward, overlapping eval windows, a PEFT loader silently loading 28/224 keys, an archive contamination — all documented with root causes and invariant-based detection.

## 5. Reading paths

- **Just the results:** [`paper/PAPER.md`](../paper/PAPER.md) then [`docs/10-results-reference.md`](10-results-reference.md).
- **The model:** [`docs/04-v2-transition-executor.md`](04-v2-transition-executor.md) and [`docs/02-v1-frozen-backbone-sidecar.md`](02-v1-frozen-backbone-sidecar.md).
- **The final resolution:** [`docs/07-v22-interface-ablations.md`](07-v22-interface-ablations.md).
- **The data:** [`docs/08-data-generation.md`](08-data-generation.md).
- **The method:** [`docs/09-methodology.md`](09-methodology.md) and [`docs/12-timeline.md`](12-timeline.md).
- **The story:** this file, then [`docs/13-lessons.md`](13-lessons.md).
