# 02 — V1 architecture: frozen backbone + latent recurrent sidecar

*Source repository: `decision-coprocessor/` (20 commits, closed 2026-09-24).*
*Key files: `SPEC.md`, `src/decision_coprocessor/{backbone,heads,sidecar,controls}.py`, `configs/*.yaml`.*

## 1. Input contract

One example is a **decision problem**: a state described in text, a question, 2–16 candidate answers, and a compute budget.

```json
{
  "id": "example-001",
  "state": "Mila possède la clé. Posséder la clé donne accès au couloir. …",
  "question": "Mila peut-elle atteindre la salle d'après les règles fournies ?",
  "options": [
    {"id": "supported", "text": "Oui, cela est établi."},
    {"id": "refuted",   "text": "Non, le contraire est établi."},
    {"id": "unknown",   "text": "Les informations ne permettent pas de conclure."}
  ],
  "budget": 0
}
```

`budget ∈ {0, 1, 2, 4, "auto"}` selects how many times the shared recurrent block is applied. The candidate order varies across the dataset and candidate **ids carry no signal**; their descriptions are the semantic content.

The model never receives: the correct answer, the proof trace, the oracle depth, the split name, the generation seed, or diagnostic fields. This was enforced by tests and by an independent data audit (0 label error, 0 leak, 0 intra-dataset duplicate).

## 2. Serialisation and spans

The whole problem is serialised into one token sequence:

```text
STATE
…
QUESTION
…
OPTIONS
A: first candidate description
B: second candidate description
…
DECISION
```

Token spans of every candidate are recorded from the **actual tokenisation of the full text** (never re-tokenising segments independently — a classic off-by-token source of bugs). No trainable special tokens are added.

## 3. Frozen encoding

- Backbone `Qwen/Qwen3-0.6B`, revision pinned to a commit hash (loading an unresolved revision is refused at runtime).
- `eval()`, parameters frozen, `use_cache=False`, SDPA attention, bf16 by default.
- `H = Backbone(tokens, attention_mask).last_hidden_state ∈ B×L×1024`, computed under `torch.no_grad()`. (Deliberately **not** `inference_mode()`, because created tensors must remain usable by autograd downstream.)
- The LM head is never materialised: vocabulary logits are irrelevant and expensive.
- The "query vector" is the last **valid** token (right padding is present).

## 4. Direct decision head (B2)

A dynamic, shared scoring head — no neuron ever bound to a class:

```text
q_raw = last valid token of H                         [B, 1024]
c_raw = masked mean of each candidate's token span    [B, K, 1024]

q = Pq(LayerNorm(q_raw))                              [B, 256]
c = Pc(LayerNorm(c_raw))                              [B, K, 256]

features_i = concat(q, c_i, q ⊙ c_i, |q − c_i|)       [B, K, 1024]
logit0_i   = MLP_shared(features_i)                   [B, K]
p0         = masked_softmax(logit0)
```

Parameter count: **1,054,209**. This head is the **baseline reference** (`B2`) and was trained first (Phase A, 3 seeds).

## 5. Latent recurrent sidecar (R1/R2/R4)

The sidecar maintains `M = 8` latent slots of width `d = 256` with repeated access to the full token memory `H`:

```text
memory_keys   = Wk(LayerNorm(H))          (computed once per forward)
memory_values = Wv(LayerNorm(H))
Z₀ = learned_slots + broadcast(W_init(q))

repeat k times with ONE shared block:
    Z = Z + a · CrossAttention(LN(Z), keys, values, mask)
    Z = Z + a · SelfAttention(LN(Z))
    Z = Z + a · FFN(LN(Z))

r_i     = CandidateAttention(query = c_i, keys = Z_k, values = Z_k)
delta_i = CorrectionHead(concat(q, c_i, r_i))          ← the auditor's shortcut
logit_k = logit0 + delta                               (residual correction)
```

| Hyperparameter | Value |
|---|---|
| latent slots `M` | 8 |
| width `d` | 256 |
| attention heads | 4 |
| FFN width | 1,024 |
| shared blocks | **1** (applied k times) |
| residual scale `a` | 0.1 |
| step embedding | none (by design: allows later k increase) |
| recurrent dropout | 0.0 (deterministic tests) |
| train budgets | {1, 2, 4} |
| eval budgets | {0, 1, 2, 4} — same weights, no retraining |
| frozen parts | backbone + direct head (`logit0`, `q`, `c` detached) |
| **trainable parameters** | **2,110,465** |

Properties guaranteed by construction and tested: budget 0 returns the direct logits **exactly**; one backbone call per example per forward whatever k; memory never mixed across batch examples; candidates always masked; no text generation anywhere.

### The architectural shortcut (found by the audit)

`delta_i = CorrectionHead(concat(q, c_i, r_i))` gives the correction head **direct access to the query and the contextualised candidate**. The head can (and, evidence suggests, did) learn to answer without using `Z_k` at all. Additionally, the loss is a **single final cross-entropy**: nothing forces `Z₁ ≠ Z₂`, which explains the observed saturation at k = 1. Both points were corrected in V2 (§04): the readout may see only the computed state, and every intermediate state is supervised.

## 6. Controls

| Variant | Definition | Params |
|---|---|---|
| **B3** `NonRecurrentMemory` | same memory `H`, **one pass only**; block enlarged to keep parameter budget comparable (slots 8→16, FFN 1024→1152) | 2,178,177 |
| **B4** `UnsharedStack` | 4 **unshared** blocks applied sequentially (depth ≈ R4), d = 256 | 5,270,785 |
| **R1/R2/R4** | the same shared recurrent block evaluated at k = 1/2/4 (one checkpoint) | 2,110,465 |
| **B1** | frozen backbone, no trainable head (codes/random baseline) | 0 |
| **B0** uniform / majority | label-frequency baselines | 0 |
| **G4** gate | features {global rep, top-2 margin, entropy, #candidates, length} → choose k ∈ {0, 4}, 35,116 params | 35,116 |

## 7. Training protocol (V1)

| Setting | Value |
|---|---|
| Phases | A: B2 ×3 seeds; B: R ×3 seeds (init from same-seed B2 checkpoint, head frozen); C: B3/B4 ×3 seeds; then G4 on router split |
| Loss | masked cross-entropy on candidate logits |
| Optimiser | AdamW, lr 3e-4, wd 0.01, warmup 5 %, grad clip 1.0 |
| Batch | micro 2, effective 32 |
| Budget | max 1,200 optimizer steps / 3 epochs (≈1.28 epoch actually used) |
| Seeds | 17, 29, 43 |
| Selection | dev macro-accuracy (budget 4 for R), evaluated every 100 steps |
| Precision | backbone bf16, trainable modules FP32 (explicit cast at the H boundary) |
| GPU discipline | one job at a time under a lock file; no notebooks; scripts only |

The Phase A selection metric deviation and the bf16/fp32 discrepancy were documented, pre-registration amended (v1.1), and all paired comparisons kept aligned on the same checkpoint.

## 8. Latency anatomy (RTX 3070 Laptop, L512, batch 1)

| Component | B2 | R1 | R2 | R4 |
|---|---:|---:|---:|---:|
| Backbone encoding | 45.34 ms | 45.34 | 45.34 | 45.34 |
| Readout | 0.66 ms | 0.66 | 0.66 | 0.66 |
| Sidecar | — | 0.99 ms | 1.55 ms | 2.68 ms |
| **Total** | **46.18 ms** (p95 46.86) | ≈47.2* | ≈47.7* | **50.04 ms** (p95 50.71) |
| VRAM reserved | 1.199 GiB | — | — | 1.199 GiB |

\* R1/R2 estimated additively (not measured end-to-end). Throughput R4: 28.9 / 47.8 / 51.6 req/s at batch 1 / 4 / 8. A first latency pass was invalidated (laptop clocks at 210 MHz before ramp-up) and rerun with a 120-forward warm-up; only the second, monotone pass is published.

**Interpretation:** the sidecar costs +8.3 % latency and less than 0.2 GiB extra VRAM — cost was never the reason the idea failed on this machine.
