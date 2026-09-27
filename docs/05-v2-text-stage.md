# 05 — V2 stage T: reconnecting language

*Period: 2026-09-25 01:15 → 10:34. Key files: `src/v2model/extractor.py`, `src/v2data/textfamily.py`, `E5_GATE_CRITERIA.md`, reports `e5*.md`, `final_v2.md`.*

## 1. The question

Stage S proved the executor works on **exact** structured memory. Stage T asks the only question that matters for a text product:

> Can the memory be **predicted from French text** well enough that the pipeline (text → graph → executor) beats the direct path (text → answer)?

The factorisation is explicit: {exact memory / predicted memory} × {exact solver / learned executor}. Five cells are tracked:

| Cell | Memory | Execution | Role |
|---|---|---|---|
| (a) | exact | learned executor (E4b S) | **anchor**: 1.000 means the executor's part is solved |
| (b) | **predicted** | exact solver | extraction pure |
| (c) | predicted | learned executor | **the pipeline under test** (+ pre-registered abstention filter) |
| (cn) | predicted | learned executor | naked, no filter (diagnostic) |
| (d) | — | direct text→answer | the reference to beat, with identical rights |

## 2. The reader (MemoryExtractor)

Input: frozen backbone hidden states `H` on the **text only** (no vocabulary logits). Output: a memory consumable by the S executor.

1. **Entity detection:** token-level IN/OUT tagger (with one trainable Transformer encoder layer in-context, class balancing, mention normalisation/merging/dedup).
2. **Relations, fact mode:** each *visible line* becomes a fact representation (masked mean + intra-fact attention). Two heads score `(subject, object-or-TERMINAL)`:
   `subject ∈ B×F×N`, `object ∈ B×F×N+1`. Decoding picks, per subject, the highest-confidence `P(subject)·P(object)` fact. Conflicts resolved by confidence.
3. **Start:** question-conditioned classifier over mentions (token-to-token matching between mentions and question tokens); plus a **deterministic containment** rule — since the question always cites the start label, exact word-boundary containment selects the start, with the learned head as fallback (hybrid, introduced in it2; declared in all conclusions).
4. `successor = −1` denotes a terminal; the legacy rule "entity without a fact ⇒ terminal" was later identified as a semantic bug (absence of information ≠ terminal) and corrected by an explicit INCONNU class in V2.2/A2.

The learned bilinear `successor_logits` variant exists but is **not supervised in fact mode** — a fact that later explained the failure of V2.2/A1.

## 3. The E5 v1 benchmark was defective

First text pools (`E5_train/dev`) were built with templates. A lexical probe (trivial bag-of-words logistic model, stdlib only) reached the answer, and paired interventions on the direct path showed a dominant **surface shortcut** (decisive-fact following 0.438, distractor stability 0.656). All E5 v1 numbers were archived as `bench-deficient`; **no E5 v1 number is reused**; `E5_eval` v1 (seed 1007) was sealed forever.

The corrected pools (`E5v2`, seed 1105/1106) fixed six generator defects, all detected by the probe itself:

| # | Symptom | Fix |
|---|---|---|
| I1 | terminal-declaration template predicted the answer (+8.56 log-odds) | template deck shuffled at creation; terminals emitted in random order |
| I4 | template draw order followed chain construction (answer first) | edges and terminals emitted in independent shuffled order |
| I5 | "longest chain terminal" solved the task | `distractor_length_mode="varied"` + post-pass ensuring ≥ 1 distractor as long as the answer chain |
| I2 | mention counts leaked | edge recalls (p = 0.30, different formulations) + second declarations (p = 0.25) |
| I6 | option wrappers leaked | wrapper drawn per option (deck of 10) |
| I3 | line lengths leaked | narrow node band; random recall lines |

**Lexical probe on E5v2:** dev accuracy 0.2179–0.2429 versus chance 0.2205 at every training size → `NEAR_CHANCE`. The benchmark is sound for a lexical-shortcut criterion.

On the sound bench, the direct path collapsed from 0.7775 (defective bench) to **0.326** — the earlier 0.78 was a distributional template lever, not reasoning and not mere lexical matching.

## 4. Frozen reader: three iterations, bounded budget

Rules: max 3 iterations, one variable per iteration, official metric = stripped + de-duplicated mentions, `best` and `last` archived, `E5v2_eval` sealed.

| Iteration | Entities ≥0.85 | Edges ≥0.65 | Start ≥0.50 | Solve ≥0.35 | Notes |
|---|---|---|---|---|---|
| it1 | 0.9999 ✓ | 0.3967 ✗ | 0.4275 ✗ | 0.0625 ✗ | 334/375 edge errors = missing edge |
| it2 | 0.9998 ✓ | 0.7028 ✓ | **1.000** ✓ | 0.2044 ✗ | deterministic/hybrid start added; validity 0.5085, abstention 0.4915 |
| it3 | 0.9998 ✓ | 0.7252 ✓ | 1.000 ✓ | **0.2482 ✗** | **3/4**; layers frozen after a train-only choice (mean of L14+L21, dim 1024) |

The **layer choice** for the representation (mean of layers 14 and 21 versus concat) was made **on train only** after a QA finding that an earlier pre-check had been computed on dev (forbidden). This is one of the project's strongest methodological episodes: the selection rule was reconstructed, a train_sel split produced, and the simpler/frozen mode ("mean", dim 1024) retained on a ≤0.01 tie-break.

### Controlled-noise experiment (D1)

Is the learned executor more robust to corrupted graphs than the exact solver? No: executor 0.8881 vs strict solver 0.8808 and best-effort solver 0.8832 — differences ~0.005, not significant; repair correctness 0.035–0.067 ≪ 0.26. The apparent (c) > (b) advantage was an **abstention-policy artefact**, and the claim "the executor repairs broken chains" was withdrawn.

### it3 verdict and the precedence rule

Cells full-dev (n = 411, GPU bf16): (a) 1.000 · (b) 0.2482 · (c) 0.2482 · (cn) 0.3382 · (d) 0.2871 → Δ(cn−d) = **+5.11 pts** [−1.72 ; +11.74]: grey zone. But the **mechanism profile failed** (decisive follow 0.388, distractor stability 0.128–0.136; broken-chain not evaluable: 0/411 structurally) and the B4-4 requirement was non-conforming. New rule, registered:

> **Mechanism takes precedence over benefit.** A Δ without a causal profile cannot validate a decomposition; a strong causal profile without Δ does not justify it either. → documented **local failure (iii)** + "inconclusive benefit" published separately. No fourth iteration. `E5v2_eval` sealed.

## 5. E5v3-A: representation fairness (LoRA on both sides)

**Pre-registered hypothesis:** adaptation of the backbone lifts the extraction bottleneck that three frozen iterations could not fix.

**Design (identical for both paths, configs hashed before start):**
LoRA rank 16 / α 32 on q, k, v, o (all layers), dropout 0.05; head lr 3e-4, LoRA lr 1e-4; wd 0.01; warmup 5 %; clip 1.0; micro 8 × accum 4; 1200 steps; seed 17; H = mean(L14, L21) in fp32 recomputed with the adapter active (cache invalidated by design); the same recipe, budget and seed are given to the direct path (fairness rule F1).

### Reader: 4/4 gates for the first time

| Metric | Threshold | Frozen it3 | **LoRA E5v3-A** |
|---|---:|---:|---:|
| Entity F1 (stripped) | ≥ 0.85 | 0.9998 | **1.000** ✓ |
| Edge F1 (stripped) | ≥ 0.65 | 0.7252 | **0.9278** ✓ |
| Start | ≥ 0.50 | 1.000 | **1.000** ✓ |
| Solve all-in | ≥ 0.35 | 0.2482 | **0.7616** ✓ |
| Validity | — | 0.620 | **0.917** |
| Abstention | — | 0.380 | 0.083 |

Edge trajectory: 0.331@100 → 0.812@400 → 0.919@700 → **0.928@1200** (monotone; best = last; **ceiling not demonstrated**). Hypothesis validated: adaptation, not head architecture, was the lever.

### Direct path: 1.000

Same recipe: 0.552@100 → 0.973@200 → 0.998@600 → **1.000@1000 (best)** → 0.998@1200.

### Full-dev cells and verdict

| Cell | Accuracy | Causal profile (decisive / distractor / permutation) |
|---|---:|---|
| (a) exact→executor | 1.000 | 1.000 / 1.000 / 1.000 |
| (b) solver | 0.7616 (abst. 0.083) | 0.780 / 0.588 / 0.932 |
| (c) pipeline (pre-registered abstention) | 0.7616 | 0.780 / 0.588 / 0.932 |
| (cn) naked | 0.8200 | 0.840 / 0.632 / 1.000 |
| **(d\|LoRA) direct** | **1.0000** | **0.996 / 0.996 / 0.988** |

**Δ(c − d) = −23.84 pts, CI95 [−28.19 ; −19.76] → issue (iii), definitive.**

- P+ fails (pipeline distractor stability 0.588 < 0.80).
- D− fails (the direct path is causally superior).
- B4-4 not conforming (det structurally absent: 0/411).
- `E5v2_eval` remains sealed forever; no conclusion depends on it.

### Mechanistic reading (the central result)

1. **Frozen regime:** pipeline 0.338 ≈ direct 0.287 (Δ +5.1, inconclusive) — decomposition *looked* marginally useful **because the direct path was crippled by the frozen backbone**.
2. **Adapted regime (fair):** direct **1.000** ≫ pipeline **0.762**. Extraction (edge 0.928 → solve 0.762) becomes the pipeline's own bottleneck, while end-to-end adaptation learns composition directly.
3. The pipeline's progress on its own bottleneck is real (solve 0.248 → 0.762) — but never enough to overtake the adapted direct path on this bench: **decomposition adds a fallible step with no residual benefit.**
4. **Conclusion (T):** on this protocol, the decomposed path is not justified; the adapted direct path wins on accuracy **and** causal profile. Clean, pre-registered, complete negative.

## 6. Incidents (all published)

1. **OOM1** (~step 150): `train()` called after the forward → gradient checkpointing inactive + LoRA dropout silently off. Run cancelled entirely; fix (train() before forward, empty_cache around evals); relaunched with **unchanged config hash**. Proof archived in `runs/e5v3a_reader_oom1/`.
2. **Corrupted eval windows** (stride 8 instead of chunk 16 → n = 814): training healthy; re-evaluation exactly n = 411 confirmed best = last@1200. Authoritative numbers live in `eval_recheck.json`; the run's `eval_history` is obsolete.
3. **Duplicate ids → positional matching** lesson from it1, repeated in it3 (kept as errata), eliminated by construction in E5v3-A (`opt_map` archived).

Costs: reader 74 min + direct 46 min + re-evals/cells/interventions ≈ 25 min GPU (about 2.5 h for E5v3-A inside the 4.96 h V2 total).

## 7. What stage T establishes

**Established:** under equal LoRA adaptation, on a French synthetic bench with n = 411 dev items and one seed per path, the decomposed text→graph→executor pipeline is clearly inferior to the adapted direct path: **experience stop**, with a complete causal profile for both sides. The extraction bottleneck is real and can be partially lifted by adaptation (edge 0.928, solve 0.762).

**Not established:** generalisation of either path beyond this bench (depth 6/8/10 textual, new surfaces, OOD); any confirmatory claim (no test set was opened, dev was used for checkpoint selection — adaptive campaign); the 1.000 direct score is a single run; a product-level recommendation.

Those gaps are exactly what V2.1 was mandated to address — without retraining. The full arc (V2.1 depth reversal, then V2.2 interface repair and architectural attribution) is in [doc 06](06-v21-frozen-validation.md) and [doc 07](07-v22-interface-ablations.md).
