# 03 — V1 results: a documented negative

*All numbers recalculated independently by the QA agent from the 66 archived prediction files — never from the executor's logs. Reserved test opened exactly once after pre-registration v2.1.*

## 1. Verdicts

| Level | Declaration |
|---|---|
| **N1 feasibility** | **REACHED** — 66 conforming files, counts 3997/3080/3993, recomputable scores, checkpoint hash gate 33/33 PASS, id-by-id exclusions |
| **N2 prediction gain** | **NOT REACHED** — Δ(R4−B2) on `test_depth` = **−0.59 pt, CI95 [−1.25 ; +0.07]** |
| **N3 specific interest** | **NOT REACHED** — R4 beats neither B3 (−0.16 pt in favour of B3, ns) nor B4 (ns); the gate G4 brings no gain to retain |

> **Honest conclusion:** the learned direct head is real (B2 ≫ B1/B0), but **recurrence is not demonstrated** (saturation from k = 1; B3/B4 equal or better) and **the latent memory is not exploited**. The sidecar slightly *degrades* depth decisions on the reserved test.

## 2. Central table (macro A/B/C, mean of 3 seeds)

| Variant | Trained params | IID | Depth | Composition | Simple (D) | NLL | Latency L512 | VRAM reserved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **B2** direct | 1,054,209 | 0.4884 | **0.3418** | 0.4081 | 0.7473 | 1.3511 | 46.18 ms | 1228 MiB |
| B3 non-recurrent | 2,178,177 | 0.4918 | 0.3343 | 0.4070 | 0.7477 | 1.3541 | — (module 1.05 ms) | — |
| B4 unshared ×4 | 5,270,785 | 0.4930 | 0.3382 | 0.4062 | 0.7468 | 1.3521 | — (module 2.58 ms) | — |
| R1 | 2,110,465 | 0.4910 | 0.3361 | 0.4066 | 0.7460 | 1.3543 | ≈47.2 ms* | — |
| R2 | 2,110,465 | 0.4915 | 0.3366 | 0.4058 | 0.7464 | 1.3543 | ≈47.7 ms* | — |
| R4 | 2,110,465 | 0.4908 | 0.3359 | 0.4073 | 0.7473 | 1.3540 | 50.04 ms | 1228 MiB |
| G4 (s17) | 35,116 | 0.4934 | 0.3420 | 0.4070 | 0.7494 | 1.3322 | — (gate 0.70 ms) | — |
| B0 majority | 0 | 0.2785 | 0.3334 | 0.2830 | 0.2595 | 1.3122 | — | — |
| B1 frozen codes | 0 | 0.2741 | 0.2827 | 0.2715 | 0.3101 | 3.0578 | — | — |

\* estimated additively, not measured end-to-end. Empty cells were never measured — nothing was invented.

### Paired comparisons vs B2 (Δ in points, CI95, coupled grouped bootstrap 2000)

| Variant | test_iid | test_depth | test_composition | corrections / degradations (depth) |
|---|---:|---:|---:|---:|
| B3 | +0.33 [−0.23 ; +0.84] | **−0.75 [−1.40 ; −0.08]** | −0.11 [−0.66 ; +0.42] | 177 / 241 |
| B4 | +0.46 [−0.10 ; +0.99] | −0.36 [−1.02 ; +0.32] | −0.19 [−0.74 ; +0.34] | 206 / 242 |
| R1 | +0.26 [−0.30 ; +0.77] | −0.57 [−1.23 ; +0.09] | −0.15 [−0.70 ; +0.40] | 182 / 235 |
| R2 | +0.30 [−0.25 ; +0.80] | −0.52 [−1.19 ; +0.16] | −0.23 [−0.77 ; +0.30] | 188 / 239 |
| **R4** | +0.24 [−0.33 ; +0.74] | **−0.59 [−1.25 ; +0.07]** | −0.08 [−0.64 ; +0.44] | **181 / 238** |
| R4−B3 | −0.09 [−0.35 ; +0.16] | +0.16 [−0.17 ; +0.48] | +0.03 [−0.23 ; +0.27] | — |
| R4−B4 | −0.22 [−0.52 ; +0.09] | −0.23 [−0.63 ; +0.16] | +0.11 [−0.19 ; +0.41] | — |
| R4−R1 | −0.02 [−0.16 ; +0.12] | −0.02 [−0.20 ; +0.15] | +0.07 [−0.08 ; +0.23] | — |

### Accuracy by depth (test_depth, mean of seeds)

| Variant | d=6 | d=8 | d=10 |
|---|---:|---:|---:|
| B2 | 0.3411 | 0.3945 | 0.3072 |
| R4 | 0.3358 | 0.3857 | 0.3025 |
| B3 | 0.3342 | 0.3841 | 0.3038 |
| B4 | 0.3375 | 0.3896 | 0.3030 |
| G4 | 0.3467 | 0.4014 | 0.3013 |
| B1 | 0.1963 | 0.4453 | 0.1949 |

**Coverage caveat:** `test_depth` lost 920/4000 examples beyond 512 tokens (81 % of family-B depth-10 items were excluded); retained population = 3,080. Depth conclusions are conditional on this truncated population.

## 3. Diagnostics that carry the conclusion (P4)

1. **Latent memory not exploited.** Masking or shuffling `H` produced **0 argmax flips / 500** and Δlogits ≤ 0.004 (s43). *Post-audit nuance:* "the memory branch is barely read" ≠ "facts are ignored" — the query `q` and contextualised candidates `c_i` can themselves carry the facts. The locally correct statement is that the *extra* memory branch brought little sensitivity in the diagnosed conditions.
2. **Saturation at k = 1.** R4−R1 = −0.02 pt. Steps 2–4 amplify a frozen correction (norms increase, answer unchanged). *Post-audit nuance:* such a ceiling can come from the assembly (see the two V2 E0 bugs), not from the task.
3. **Information is readable via candidates, not via Z** (directional probes, 25 examples/family).
4. **Per-instance instability under option permutation ≈ 39 %** (shared with B2/B3/R4; 70 % for B1). The aggregate is stable, individual predictions are not. The audit qualified this as a **serious functional defect** to be treated architecturally.
5. **Error taxonomy of B2** (n = 2,997 dev): chain_interrupted 30.2 % · arithmetic 26.9 % · other 18.2 % · negation 10.6 % · indeterminate 9.8 % · permutation 4.2 %. Labels are descriptive; they are **not** mechanistic evidence.

## 4. Calibration / probabilistic quality

| Variant | Split | NLL | Brier | ECE (15 bins) |
|---|---|---:|---:|---:|
| B2 | iid | 0.9728 | 0.5370 | 0.0246 |
| B2 | depth | 1.3511 | 0.7463 | 0.1254 |
| R4 | depth | 1.3540 | 0.7477 | 0.1295 |
| G4 | depth | 1.3322 | 0.7370 | 0.1224 |
| B1 | depth | 3.0578 | 1.0505 | 0.4098 |

R4 is marginally *less* calibrated than B2 on depth; the sidecar does not improve probabilistic quality. The uniform baseline's low ECE shows that ECE alone is insufficient — hence joint NLL/Brier publication.

## 5. Gate (G4) and adaptive allocation

G4 (k ∈ {0,4}) reached depth 0.3420 vs B2 0.3418 (paired −0.62 pt [−1.47 ; +0.18], ns) with **47.9 % / 53.1 % / 56.7 %** activation (iid/depth/composition) and λ = 0. The gate is **not selective**: with no gain to preserve, H4 is not measurable, not "confirmed".

## 6. What the external audit changed (interpretation only)

The audit did **not** contest the numbers or the verdicts. It corrected six over-strong interpretations:

1. "Memory branch barely read" → local sensitivity statement, not "facts ignored"; the joint permutation ablation of keys/values/mask can be inconclusive (`Attention(Q, PK, PV) = Attention(Q, K, V)`).
2. Probes (25 examples/family, partial targets) **neither demonstrate nor exclude** LoRA.
3. Per-instance permutation instability is a serious functional defect (already noted).
4. Real budget ≈ **1.28 epoch**, not the 3-epoch ceiling; convergence is not settled by the available curves.
5. "B3 ≥ R on all 3 seeds" was inexact: R was slightly above on 2 seeds on dev (the conclusion "no established advantage" is unchanged).
6. The gate is not exonerated by "it learns on train" (overfit, rare useful transitions, feature quality remain possible); taxonomy labels are not proof of internal execution.

And it added the diagnosis that motivated V2:

> **V1 did not establish a mechanism and then show its uselessness; the targeted mechanism was never demonstrated** — notably because the correction head received `q, c_i` directly and a final CE alone imposes no state progression.

## 7. Cost summary

- ≈ 29 min GPU per Phase-A seed; all V1 training ran on one RTX 3070 Laptop.
- VRAM peak measured: 1.175 GiB allocated / 1.199 GiB reserved (target was 6.5 + 1 GiB).
- Latency ×1.083 (R4/B2) at L512 batch 1; module-only costs 0.99/1.55/2.68 ms (R1/R2/R4).
- **No OOM occurred**; the sidecar was never memory-bound.

## 8. Why this counts as a result

The project's own specification made it explicit before the runs: *"a documented negative result constitutes a valid result."* V1 produced, in addition to the negative:

- a reusable measurement chain (independent oracles, frozen datasets with hash manifests, grouped paired statistics, hash-gated checkpoints, id-by-id exclusions);
- exact controls at comparable parameter and inference cost;
- a complete diagnosis of *why* the assembly could not work — which is precisely what justified reopening the question in V2 with an anti-shortcut design.
