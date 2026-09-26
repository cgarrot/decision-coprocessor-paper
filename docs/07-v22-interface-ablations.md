# 07 — V2.2 + confirmation programme: interface ablations, attribution, independent confirmation (closed)

*Timeline: protocol 2026-09-25 14:03 → V2.2 closure 19:06 → third audit 19:25 → C0/C1 same evening → C2 protocol frozen 22:20, night chain → C2 closed and QA-validated 2026-09-26 10:37. **All gates closed; all QA reserves closed.***

## 1. Central hypothesis (pre-registered before any implementation)

> The pipeline's depth deficit comes from **discretisation at the interface** (per-edge argmax: one missing edge kills the chain), **not** from the reader's inability (edge F1 0.93; the deterministic parser extracts the public text with coverage/agreement **1.000/1.000**). Propagating **successor distributions** — `p_{t+1} = p_t A`, terminals self-looping — should recover a measurable part of the gap.

The hypothesis was validated **twice**: once with zero training (A1-bis), once with supervised distributional training (A2). A third, independent audit then required (C0/C1) that the *specific* contribution of distribution conservation be isolated, and (C2) that the system be confirmed on fresh data, seeds and a blind-selection protocol.

## 2. Ablations (one at a time, fixed order)

| id | Content | Training | Outcome |
|---|---|---|---|
| **A1** | propagation on the frozen reader via the **bilinear** successor head | none | **FAIL** — head never supervised (top-1 0.054) → noise |
| **A1-bis** | propagation matrix from the **supervised fact-level** heads | none | **PASS** — c_prop ≈ 0.85 invariant in depth |
| **A2** | reader retrained with **distributional supervision** + propagation in the loop + explicit **UNKNOWN** class | yes (LoRA) | **PASS TOTAL** — c_prop 0.995–1.000 on 8/8 benches |
| **A3** | direct path with **equal** auxiliary supervision | yes (LoRA) | direct stays collapsed in depth → **architectural superiority of propagation, 8/8** |

Frozen criteria: Δ(c_prop − c_discret) ≥ **+5.0 pts on B3**, CI low > 0; short non-regression; sealed V2.1 benches as evaluation; **selection only on bench 2213**; stable `eps = 1e-3` tie-break; new selection bench for A2.

## 3. A1 → A1-bis → A2 → A3: results

### A1-bis (zero training)

| Bench | c_prop | c_disc | Δ [CI95] |
|---|---:|---:|---|
| B1 short | 0.8550 | 0.8000 | **+5.50** [+1.50; +9.25] |
| B2 depth 6 | 0.8375 | 0.6675 | **+17.00** [+12.50; +21.50] |
| **B3 depth 8** | 0.8525 | 0.5975 | **+25.50** [+20.75; +30.00] |
| B4 depth 10 | 0.8550 | 0.5600 | **+29.50** [+24.50; +34.75] |
| B5/B6/B7/B8 | 0.83–0.86 | 0.77–0.81 | +4.25 … +9.25, CI > 0 |

c_prop invariant in depth; CIs exclude zero on 8/8; QA validated.

### A2 (distributional training, PASS TOTAL)

| Bench | c_disc | A2 | Δ vs disc [QA CI] | Δ vs direct V2.1 [QA CI] |
|---|---:|---:|---|---|
| B1 short (1–4) | 0.800 | **0.9950** | +19.50 [+15.25; +23.50] | **+5.75** [+3.25; +8.25] |
| B2 depth 6 | 0.667 | **0.9975** | +33.00 [+28.25; +38.00] | **+47.25** [+42.50; +52.25] |
| **B3 depth 8** | 0.598 | **0.9975** | **+40.00** [+34.75; +45.00] | **+71.75** [+67.00; +76.25] |
| B4 depth 10 | 0.560 | **0.9975** | +43.75 [+39.00; +48.75] | **+69.00** [+64.50; +73.25] |
| B5 surface | 0.810 | **1.0000**\* | +19.00 [+15.25; +23.00] | **+6.00** [+4.00; +8.50] |
| B6 distractors | 0.773 | **1.0000**\* | +22.75 [+19.00; +27.00] | **+6.25** [+4.00; +8.75] |
| B7 options | 0.800 | **0.9950** | +19.50 [+15.25; +23.50] | **+5.50** [+3.25; +8.00] |
| B8 other start | 0.765 | **0.9975** | +23.25 [+19.25; +27.50] | **+15.75** [+12.25; +19.75] |

\* declared saturation (B5/B6 cannot separate systems above 0.995). Training 4054.64 s GPU; selection best = step 1200. Probabilistic quality: NLL 0.0044–0.0294; `gold_class_squared_error` 0.0007–0.0061.

### A3 (equal-supervision direct control)

| Bench | A3 | direct V2.1 | Δ(A2−A3) [canonical CI] | Δ(A3−direct) |
|---|---:|---:|---|---|
| B1 short | 0.9625 | 0.9375 | **+3.25** [+1.50; +5.25] | +2.50 [+0.25; +4.75] |
| B2 depth 6 | 0.4925 | 0.5250 | **+50.50** [+45.50; +55.50] | −3.25 [−8.50; +2.25] |
| B3 depth 8 | 0.2475 | 0.2800 | **+75.00** [+71.00; +79.25] | −3.25 [−8.50; +1.75] |
| B4 depth 10 | 0.2825 | 0.3075 | **+71.50** [+67.00; +75.75] | −2.50 [−7.75; +2.75] |
| B5 surface | 0.9575 | 0.9400 | **+4.25** [+2.50; +6.50] | +1.75 [−0.25; +3.75] |
| B6 distractors | 0.9450 | 0.9375 | **+5.50** [+3.25; +7.75] | +0.75 [−1.25; +2.75] |
| B7 options | 0.9600 | 0.9400 | **+3.50** [+1.50; +5.50] | +2.00 [0.00; +4.00] |
| B8 other start | 0.8550 | 0.8400 | **+14.25** [+11.00; +18.00] | +1.50 [−1.50; +4.75] |

**Architectural superiority of propagation, per bench, 8/8.** Canonical CI artefact = `runs/v22_a3_eval/a3_eval_verdict.json` (bootstrap seed 17, grouped by `base_group_id`). The asymmetry is the headline: **+3.25…+5.5 pts short vs +50.5…+75 pts deep**.

## 4. Third external audit (C0) — scope corrections

The audit (`DECISION-COPROCESSOR-AUDIT-V22-CONFIRMATION.md`, sha `d47186ec`, 596 lines) judged the positive result important but demanded seven corrections and an attribution program. C0 applied them **without touching any number** (`v22_scope_erratum.md`):

1. **“The direct path knows it fails” withdrawn.** A high NLL means the gold answer gets little probability, not error awareness (confident-wrong counter-example). Correct statement: *degraded probabilistic quality; capacity to detect its own errors remains to be measured*.
2. **“A2 calibrated” nuanced.** Good probabilistic quality on a near-solved domain; full calibration still to establish. The published score was renamed **`gold_class_squared_error`** = mean((1−p_gold)²); the complete multiclass Brier was computed separately (C1, below).
3. **Parser reconciliation — the “0.95 ceiling” was an error.** The deterministic parser measures **1.000/1.000 coverage/agreement on 3,200/3,200**; 0.95–0.98 described the *path-only oracle correctors*, not the parser. **A2 joins, but does not exceed, the bounded deterministic solution.** Parser+solver was added to the product table: **1.0000 on 8/8 benches (3200/3200)**.
4. **Bench status requalified.** B1–B8 are held out from gradients and checkpoint selection, but were **observed during an adaptive development campaign** → development evaluation, not independent confirmation. Bench 2213 (selection) contains 50 % depths 6/8 → A2's depth performance is **not** a blind extrapolation (C2-b was designed to test exactly that).
5. **Costs reworded.** “Propagation free” → **“low in this profile”** (1.3–1.5 % of p50, batch 8); units clarified (lots/s at batch 8; amortised per-example time ≠ isolated-request latency); ×1.273 vs a 1.25 target is not automatically a validation.
6. **Canonical CIs** = `a3_eval_verdict.json`; QA bounds differing by ≤0.5 pt come from the bootstrap seed.
7. **“Direct dominant on short” is V2.1-only**; in V2.2, A2 > direct on all 8 benches.

### Inference-path audit: the S executor is *not* in the A2 path

Verified by code (`v22_public_inference_audit.md`): A2's public inference is

```text
MemoryExtractor.extract → mention_reps / fact_reps / fact_logits
→ transition_matrix_from_facts → start_distribution
→ propagate(T = 20) → answer_index.
```

Only LoRA + fact-level heads + explicit propagation. The 92,802-parameter neural executor S is **not invoked** in A2; it remains a stage-S artefact. Consumed inputs: `input.{state,question,options}` + `private.graph.options` (public candidate mapping). A **three-layer anti-leak test** passes (structure: 3,200/3,200 inputs identical under private randomisation; public-only: 64/64; behavioural: 64/64 ×2).

## 5. C1 — attribution without retraining (the essential ablation)

Pre-registered 2×2 on identical, frozen reader outputs: reader {R0 = E5v3-A frozen, R1 = A2} × decoding {hard = discretisation, soft = propagation}. Identities verified: **R0-soft ≡ A1-bis (400/400 ×8)** and **R1-soft ≡ A2 (400/400 ×8)**.

| | hard (aligned v2) | soft (propagation) |
|---|---:|---:|
| **R0** (E5v3-A reader) | 0.55–0.82 | 0.83–0.86 |
| **R1** (A2 reader) | 0.785–0.875 | **0.995–1.000** |

**Both factors contribute**: soft > hard at fixed reader (+14 to +22 pts for R1), and R1 > R0 in hard reading (+~0.2 pts at depth for the same discretisation). The audit's interpretation 1 is confirmed — the gain is **not** reducible to uncertainty conservation alone, nor to better local reading alone.

Additional C1 measurements:

- **Budget sweep 0/1/2/4/8/16/20 (same weights, same problems):** R0 converges at ≈ depth+1 then **decays** (B5 0.910@4 → 0.853@20) — the frozen reader's INCONNU mass leaks and accumulates; R1 converges earlier (4 short, 8 deep-6/8, 16 deep-10) and **plateaus at 0.998–1.0**. Budget 0 ≈ chance; the budget-4 dip in depth = “no mass at the terminal yet” (tie-break decides).
- **Complete multiclass Brier** (candidates ∪ {AUTRE}, INCONNU + off-candidate mass split, recomputable from per-item archives): R1 **0.0016–0.0119** vs R0 **0.2998–0.5826**. R0's INCONNU mass reaches ≈0.20 in depth (the measured leak); R1's off-candidate ≤ INCONNU ≤ 0.008.
- **Toolchain divergence localised:** torch 2.6.0+cu124 reproduces the published predictions exactly (0/3,200 flips, two passes); torch 2.14 diverges on 18/3,200, and the **first divergent stage is the backbone forward `H`** (bitwise difference at h14/h21) — not the decoder logic.
- **CPU/GPU localisation (R-D):** same conclusion — first divergent stage is the backbone (h14, 16/16 items), ≈0.49 % relative bf16 drift; downstream decisions stable (0/16 flips on the sample). Consistent with R7: the historical ≈6-pt CPU/GPU gap concerned the old E5v3-A reader (narrow margins); A2 has wider margins.
- **Tie-break semantics (R-E):** real ties *and* near-ties ≤ eps = 1e-3 resolve by alphabetical key — even when that label's mass is slightly lower; renaming is **equivariance** (predictions transport), not invariance.

## 6. C2 — independent confirmation + blind extrapolation (night of 25–26/09)

Protocol frozen **before generation** (`V22_C2_PROTOCOL.md`, sha `6dd53719`): fresh benches seeds 2214–2216, total anti-duplicate constraints (no signature shared with any earlier pool), usage labels per line, same recipes, same bundle init.

**Structurally decisive fact:** `E5v2_train` contains **only depths 1–4** (128/715/619/587) — so the depth performance was *already* blind at the gradient level; the only non-blind element was the selection bench 2213 (50 % depths 6/8). C2-b therefore retrains with a **short-only selection bench** (2216).

### C2-a — confirmation of the system (3 seeds): **PASS**

Primary hypothesis (prefixed): Δ(A2−A3) on pooled deep cells (6+8+10, n = 1,200/pair), grouped bootstrap 2000, CI low > 0.

| seed | Δ pooled deep | IC95 |
|---|---|---|
| s17 (existing pair) | **+65.30 pts** | [+62.6, +68.1] |
| s18 | **+64.05 pts** | [+61.3, +66.8] |
| s19 | **+68.14 pts** | [+65.6, +70.9] |
| **mean** | **+65.83 pts** | CI low > 0 on all three |

- A2 dispersion across seeds (pooled deep): **0.9950 / 0.9983 / 0.9983 → 0.33 pt max** (near-perfect replication).
- A3 remains collapsed on all three seeds (pooled deep 0.342 / 0.358 / 0.317).
- Short non-regression: A2 short mean **0.9992** ≥ 0.93.

### C2-b — blind extrapolation (short-only selection): **LARGELY SUCCESSFUL**

Criterion: A2-blind pooled deep ≥ 0.90.

| | short | prof6 | prof8 | prof10 | **pooled deep** |
|---|---:|---:|---:|---:|---:|
| **A2 s20-blind** | 0.9950 | 0.9825 | 0.9950 | 0.9825 | **0.9867** |
| A3 s21-blind | 0.9475 | 0.3225 | 0.2625 | 0.2281 | 0.2710 |

**Depth invariance is acquired without ever selecting on depth** (and gradients never saw depths > 4). The direct control stays collapsed even under blind selection.

### Incident (published, corrected, QA-validated)

One item of C2a-prof10 measured 484 tokens at the reader but **518 at the direct prompt** (> 512): the generator measured the reader rendering, not the consumer's `collate_direct_text` rendering (+7 tokens). It was excluded **identically for all paths** (1/2,000), the eight evals replayed on the common population, and the generator rule corrected for future benches (measure with the real consumer collate). No conclusion affected.

### Margins and noise floor

Top-2 margins (risk of bf16-driven flips): A2 medians 0.9963 / 0.9955 / 0.9914 (s17/s18/s19) and 0.9882 (blind); A3 all-cells median 0.9631. Deep-only (the real fragility): A2 s19 median 0.9889, ≤1e-2 on 0.08 %; A2-blind deep ≤1e-2 on 1.50 %. Costs of the night: 6 trainings ≈ 70 min each + 8 evals ≈ 40 s ≈ **7 h GPU** under the single-job lock.

## 7. Router and costs

- **Router oracle bound: +0.00 to +0.50 pts over A2 alone** (A3-only correct on 0–2 items/bench) → no router built for accuracy. The audit's nuance: this does **not** prove a router couldn't save *compute*; that would need a pre-declared latency objective, and the propagation step is already ≈1.3–1.5 % of the pipeline.
- **Costs (batch 8, QA-validated):** B1 p50 A2 40.32 ms vs A3 32.65 (×1.235); B3 51.59 vs 40.52 (×1.273); throughput ×0.78–0.79; VRAM parity 1472–1512 MiB. Batch-1 measurements added in C0. The cost is carried by extraction, not by the transition math.

## 8. Final state and scope

**Everything is closed**: V2.2 protocol, A1 (fail), A1-bis, A2, A3, router bound, costs; C0 scope corrections; C1 attribution/anti-leak/Brier/sweep/toolchain/localisation/tie-break; C2-a confirmation (3 seeds) and C2-b blind extrapolation. QA verdicts REG-82→86, all reserves closed (R-C2-0/1/2 fixed: exact incident cause, top-2 margins archived, “pooled” convention named).

**Authorised formulation (audit §10, adjusted with C2 results):**

> On eight synthetic French relation-tracking benches, the A2 system — which learns relational distributions and applies an explicit propagation — reaches 99.5–100 % accuracy and outperforms direct models, including a direct model with comparable auxiliary supervision, especially on long chains. Independent confirmation on fresh benches and seeds, and a blind extrapolation protocol (no depth in training or selection), reproduce the result; the contribution is attributed to both better local reading and the conservation of distributions.

**What remains open (declared out of scope, Lot C3):** INCONNU / partially observed worlds (defined but not evaluated); harder benches (B5/B6 saturated); a single extension axis among {new linguistic renderings, multi-question contexts, larger graphs}. **No OOD generalisation, no product claim, no universal “LLMs don't compose” claim.**
