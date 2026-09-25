# 01 — Context, questions, hypotheses, verdict frames

## 1. Origin and scope

The project asks a narrow question with a broad motivation: **can a small, explicitly computational module improve multi-step decisions made by a small language model, without generating intermediate text, on consumer hardware?**

Target hardware, common to all experiments:

| Component | Specification |
|---|---|
| CPU | 11th Gen Intel Core i7-11800H (8 physical / 16 threads) |
| RAM | 29.34 GiB |
| GPU | NVIDIA GeForce RTX 3070 Laptop, 8,192 MiB VRAM (driver 595.91, CUDA 12.8) |
| OS | Debian GNU/Linux 13 (trixie), kernel 6.12 |
| Python | 3.11 (uv-managed), PyTorch 2.11.0+cu128, bf16 supported |
| Backbone | `Qwen/Qwen3-0.6B`, revision `c1899de2…`, 596,049,920 parameters, Apache-2.0 |

The province of the study is deliberately bounded:

- **not** about generative reasoning chains — no intermediate natural language at decision time;
- **not** about scaling — the backbone is frozen (V1) or lightly adapted with LoRA (V2);
- **not** a product claim — all conclusions are local to the protocol and benchmark measured;
- **a negative result is a valid result** (V1's own specification, §1.4), and the project repeatedly acted on that principle.

## 2. V1: the initial question

> **V1 question.** Does a small recurrent module appended after the encoding of a frozen backbone improve decisions that require several dependent operations, at an acceptable real cost on the target machine?

Two inference paths share one frozen backbone call per example:

```text
DIRECT PATH
state + question + candidates → frozen backbone → decision head → probabilities

COPROCESSOR PATH
state + question + candidates → frozen backbone (once) → H
                                  ├─ direct head → logits₀, q, c
                                  └─ latent sidecar (shared recurrent block, k steps)
                                       → residual correction Δ
                                       → logits_k = logits₀ + Δ → probabilities
```

### V1 hypotheses (as pre-registered)

| ID | Hypothesis | Outcome frame |
|---|---|---|
| H1 | The sidecar improves multi-step accuracy vs the direct path using the same backbone | primary |
| H2 | Part of the gain persists against a non-recurrent module and an unshared stack at comparable parameter/inference cost | controls |
| H3 | The gain is not limited to training-time formulations and depths | generalisation |
| H4 | An allocation policy (gate) keeps a measurable fraction of the gain without always activating the sidecar | efficiency |
| H5 | Errors, calibration and degraded decisions are measured too | reliability |

The possibility that H1 is true while H2 is false ("we improved a classifier without showing any specific value of recurrence") was written down before running.

### V1 verdict frame

Three levels: **N1 feasibility** (the whole measurement chain works and is auditable), **N2 prediction gain** (paired improvement on the reserved test), **N3 specific interest** (recurrence beats its controls).

## 3. The external audit and the pivot to V2

After V1 closed, an independent critical review (546 lines) established three things:

1. **The mechanism was never demonstrated before being benchmarked.** In V1 the correction head received the query `q` and the contextualised candidate `c_i` directly (`delta_i = CorrectionHead(concat(q, c_i, r_i))`), so the network could answer without executing any latent composition. Moreover, a final cross-entropy alone imposes no progression of intermediate states — nothing forces step 2 to differ from step 1. This explains the observed saturation at k=1 *without* refuting the idea of a coprocessor.
2. **Three benchmark defects** mattered (depth test confounded with answer proportions; 512-token exclusions amputating the deep-relation population; ~39 % per-instance instability under option permutation).
3. **A rebuild plan**: a *supervised transition executor* with an explicit state, a shared transition, exact state traces as supervision, an anti-shortcut readout, and a ladder of conditional gates E0–E8.

### V2 question (DECISION-V2)

> **V2 question.** Is a transition **learned**, **composed**, and **causally useful** — before reconnecting language?

Three labelled stages:

- **S — structured exact input**: diagnostic of the executor itself (no language, CPU only);
- **T — memory predicted from text**: factorisation {exact/predicted memory} × {exact/learned executor};
- **A — backbone adaptation**: only if extraction diagnostics justify it, with the direct control receiving the same adaptation.

### V2 hypotheses and stop conditions

- A transition must be *conditionally* correct given a correct input state (not just globally accurate).
- Autonomous roll-out must hold at depths never trained on (6/8/10/16).
- Causal interventions (decisive edge retargeted → answer must change; distractor edge retargeted → answer must stay; option permutation → answer by stable id; state replacement → compatible continuation) are required; probes alone never suffice.
- **Stop rules**: no mastered transition → stop depth claims; gains only from auxiliary targets that also help the direct path → no recurrence claim; structured input OK but text fails → attack extraction; symbolic baseline better → it's a product path, not a reasoning proof; no gain at higher cost → no gate to hide it.

## 4. V2.1 and V2.2: after closure

The V2 close was validated (issue (iii), decomposition dominated under fairness), but the QA flagged reserves: negative measured on dev only (n = 411, 1 seed), no confirmatory test opened, and generalisation untested. An external V2-validation audit mandated a **diagnostic program without any retraining**:

- **V2.1 (pre-registered before generation):** 8 fresh benches × 400 items (seeds 2205–2212), frozen checkpoints, all-in + coverage/risk, error attribution with oracle correctors (diagnostic tables only), end-to-end cost measurement. Q4 decision matrix pre-registered; **no "revenge gate"**.
- **V2.2 (pre-registered):** one ablation at a time on the interface. A1 = propagate distributions from the **frozen** reader (`p_{t+1} = p_t A`) at zero training cost; A2 = retrain the reader with distributional supervision + an explicit UNKNOWN class (absence of information ≠ terminal); A3 = direct path with the same auxiliary head if any benefit is claimed; A4 = lazy relation reading, conditional.

## 5. What counts as a conclusion

Every result in this compendium is published at one of three levels, explicitly:

| Level | Meaning | Example |
|---|---|---|
| **Experiment stop** | stopping investment in a configuration on a clearly unfavourable result | stage T under fairness (Δ = −23.8 pts) |
| **Local scientific conclusion** | valid for the measured domain and protocol | "the executor composes zero-shot to depth 16 on this task" |
| **Product validation** | never claimed anywhere in this project | direct path = "best reference, priority candidate for independent validation", not a validated product |

This vocabulary matters: the V2 final report explicitly refuses to upgrade a dev-only, 1-seed, adaptive-campaign observation into a confirmatory conclusion.
