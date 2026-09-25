# 06 — V2.1: frozen-checkpoint validation and the depth reversal

*Protocol pre-registered 2026-09-25 ≈11:40; runs and QA published the same day. No retraining, no checkpoint change.*

## 1. Mandate

The external V2-validation audit required an independent diagnostic program on the **existing** V2 checkpoints, with explicit prohibitions:

1. `E5v2_eval` (seed 1107) stays sealed forever;
2. no test constructed from the direct path's errors; transformations pre-registered and independent of any observed error;
3. oracle diagnostics (exact graph, path corrector) are **localisation tools, never benchmark scores** — published in separate "diagnostic" tables;
4. one GPU job at a time, scripts committed before use, thresholds frozen before any prediction.

**Frozen artefacts:**
`executor_s_e4b_pad20.pt` (S), `reader_lora_best.pt` (E5v3-A reader best@1200), `direct_lora_best.pt` (E5v3-A direct best@1000).

## 2. Eight fresh benches (n = 400 each, seeds 2205–2212)

| Bench | Content | Control |
|---|---|---|
| **B1-court** | depth 1–4, new groups/seeds/names | comparable to dev |
| **B2-prof6 / B3-prof8 / B4-prof10** | chains of 6 / 8 / 10 edges | token length covered by construction (≤512); node counts controlled across cells |
| **B5-surface** | paraphrases + new names, same logic as B1 | matched by graph signature to B1 |
| **B6-distract** | +50 % useless facts | matched to B1 |
| **B7-options** | permuted candidates + admissible distractors | question unchanged, scoring by stable id |
| **B8-depart** | same graph, **different start node** | matched by graph |

K ∈ {4,5,6}, ≤ 20 nodes (pad20), French, E5v2 surfaces. `example_uid` unique, `base_group_id` for matched variants, public hash per example, dedup signatures enforced against E5v2 train+dev and internally. The pools deliberately include cases where an **intermediate path node is a candidate**, to make broken-chain "det" evaluable in the future (infrastructure; **never counted** in any V2.1 score).

## 3. Paths evaluated (same rights, same batching/encoding)

- **(d)** frozen direct LoRA;
- **(c)** frozen pipeline: reader → validator → executor (pre-registered abstention) + naked variant (diagnostic);
- **(b)** reader → exact solver (extraction pure);
- **(a)** exact memory → executor (anchor, diagnostic);
- **(p)** deterministic parser bounded to the templates (public text only) — an engineering control, not a general reader.

Metrics: all-in (abstention = error) plus coverage/risk; per bench and per depth; numerators/denominators/groups published; paired Δ by `base_group_id`, grouped bootstrap 2000; **descriptive first** (one existing seed): no general claim.

## 4. Results (n = 400 per bench, GPU bf16, batch 8)

| Bench | (a) anchor | (b) solver | (c) abst | (cn) naked | (d) direct | Δ(c−d) [CI95] |
|---|---:|---:|---:|---:|---:|---|
| **B1 (1–4)** | 1.000 | 0.800 (abst .087) | 0.800 | 0.853 | 0.9375 | −13.75 [−18.2,−9.2] |
| B5-surface | 1.000 | 0.810 (.075) | 0.810 | 0.868 | 0.9400 | −13.00 [−17.2,−8.7] |
| B6-distract | 1.000 | 0.772 (.110) | 0.772 | 0.848 | 0.9375 | −16.50 [−21.2,−12.0] |
| B7-options (K=6) | 1.000 | 0.800 (.087) | 0.800 | 0.853 | 0.9400 | −14.00 [−18.5,−9.8] |
| B8-depart | 1.000 | 0.765 (.087) | 0.765 | 0.820 | 0.8400 | −7.50 [−12.8,−2.0] |
| **B2-prof6** | 1.000 | 0.667 (.095) | 0.667 | 0.693 | 0.5250 | **+14.25 [+7.5,+21.0]** |
| **B3-prof8** | 1.000 | 0.598 (.125) | 0.598 | 0.618 | 0.2800 | **+31.75 [+25.0,+38.5]** |
| **B4-prof10** | 1.000 | 0.560 (.165) | 0.560 | 0.593 | 0.3075 | **+25.25 [+18.3,+32.0]** |

### The depth reversal

| Depth | 1 | 2 | 3 | 4 | 6 | 8 | 10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct (d) | 1.00 | 0.97 | 0.91 | 0.87 | 0.53 | **0.28** | 0.31 |
| Pipeline (c) | 0.92 | 0.81 | 0.76 | 0.71 | **0.67** | **0.60** | **0.56** |

**Crossing between depth 4 and depth 6.** Below depth 5 the direct path wins by 9–16 pts; at depth 6 and beyond the pipeline wins by +14 to +32 pts, with CIs excluding 0.

## 5. Mechanism: where the deficit lives

- **(a) = 1.000 everywhere, including depth 10** → the executor composes; **the entire pipeline deficit is in reading**.
- **Oracle corrector "path only"**: 0.950 / 0.965 / 0.9825 / 0.9825 (B1→B4) vs baseline 0.800 / 0.667 / 0.598 / 0.560. Correcting only the **useful-path edges** recovers almost everything; correcting only the start or only off-path edges changes nothing. **The deficit is precisely the path edges.**
- Active-successor accuracy ~0.89 (stable), END detection 98.7–99 %.
- **Direct NLL:** 0.59 → 5.43 → 8.85 → 7.45 nats (B1→B4). The direct path "knows" it is uncertain at depth (ECE on B1 = 0.061).
- **Abstention filter:** naked > filtered by +5.25 to +6.0 pts all-in (c ≡ b: executor ≡ solver on valid graphs) → published as a coverage/risk ablation.
- **Complementarity** (pipeline right, direct wrong): 123 / 400 at depth 6, 172 at depth 8, 163 at depth 10 → a router line is relevant; **an oracle router bound must be measured before building anything**.
- **(p) deterministic parser:** coverage 1.0000 and agreement 1.0000 on 8/8 benches (3200/3200, zero UNKNOWN), public-text only, QA-reproduced. Reading: deterministic extraction from public text **is possible** (existence proof); the deficit is in the **learned extraction + interface**, not in the information (bounded to templates; this does not quantify learning difficulty).

## 6. Q4 decision

Pre-registered matrix line **"direct drops with depth, S works, reading degrades" → work on the interface** (audit §6: uncertain transitions / propagation, separate pre-registration). The router line is documented as a possible follow-up **after** measuring the oracle bound.

## 7. Environment-bound numbers (QA reserve R7)

- **Inter-environment variance measured:** CPU vs GPU ≈ 6 pts on dev (b = 0.82 CPU vs 0.7616 GPU) — due to near-tie successor logits in the reader, stable by batch configuration, not by platform; even in fp32 CPU, 11/32 memories differ → **not merely bf16 rounding**. Published numbers are therefore labelled environment-bound (GPU RTX 3070 Laptop / bf16 / batch 8).
- **GPU batch = 1 vs 8 (B1):** b/c 0.805 vs 0.800 · cn 0.8575 vs 0.8525 · d 0.935 vs 0.9375 · Δ −0.130 vs −0.1375 — differences ≤ 0.5 pt, no effect on conclusions. Outputs are now separated per mode.
- **Fix for future runs:** stable tie-break at a declared `eps = 1e-3` (CPU/GPU) or per-example inference (audit §4.4). Applied in V2.2, not retroactively.

## 8. Self-testing harness (A5)

`--selftest` proves before any run: sizes 1/7/8/9/16/17/411, incomplete last minibatch, shuffled order ≡ sorted order (exact identity), batched ≡ unit (identity), duplicate ids handled positionally, every example exactly once. The log is archived (`runs/v21_eval/SELFTEST_Q0.log`).

## 9. What V2.1 changed

Before V2.1, the published conclusion was "the decomposed path is dominated" (dev, depth 1–4). After V2.1, that sentence must be **scoped by depth**:

> On frozen checkpoints and new benches: the direct path is superior for short chains (depth ≤ 4) and **collapses beyond depth 6**, where the decomposed pipeline takes over. The bottleneck of the pipeline is the **discretisation of the extracted graph**, not the executor (a = 1.000 at depth 10) nor the availability of information (parser = 1.000).

This is the finding that V2.2's interface ablations attack — and resolve: see [doc 07](07-v22-interface-ablations.md) for the final outcome (A2 0.995–1.000 on all eight benches, architectural superiority over an equal-supervision direct control, router unnecessary, costs measured).
