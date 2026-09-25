# 04 — V2 stage S: the supervised transition executor

*Source repository: `decision-coprocessor-v2/` (V2 runs: 2026-09-24 22:49 → 2026-09-25 00:36).*
*Key files: `src/v2model/{executor,relation_data,train}.py`, `data_contract.md`, `MODEL_NOTES.md`, reports `e1.md`–`e4b.md`.*

## 1. Why a supervised executor

The V1 audit concluded that the target mechanism had never been demonstrated: the correction head could bypass latent computation (direct access to `q, c_i`) and a single final cross-entropy imposed no state progression. V2's stage S isolates the mechanism entirely:

- **input:** an exact structured graph (no language);
- **state:** an explicit execution state `s_t = (h_t, p_t)` where `p_t` is a pointer distribution over nodes;
- **transition:** one **shared** function `F` applied repeatedly;
- **supervision:** every intermediate state is supervised with the exact pointer trajectory from the oracle;
- **readout:** the final answer is scored from the computed state and *raw* candidate features only — **no direct access to the question nor to contextualised candidates**;
- **budget:** fixed 16 transitions, absorbing terminal, never chosen from the private oracle depth.

Everything runs on **CPU** (92,802 parameters) — GPU is forbidden until stage T.

## 2. Data contract (family B simplified)

A problem is a set of disjoint directed chains with:

- **unique successor** per node, **no cycles**;
- **≥ 3 terminals** (mandatory anti-shortcut: with a single terminal the answer could be found without following the start);
- candidates = all terminals + at most one eliminable internal node (minority);
- non-answer candidates are **not reachable** from the start;
- entities are **opaque codes renamed per problem**; fact order shuffled; option order shuffled; id order statistically uncorrelated with chain position.

Public input (`input`) contains only: `nodes`, `edges`, `query.start`, `options`. **Forbidden and tested absent:** answer, trajectory, depth, terminal flags, group id, pair metadata.

Private supervision (`private`), never fed to inference:

```json
{
  "answer_node": "k7m", "answer_id": "a4t7k", "depth": 4,
  "trace_indices": [3, 0, 5, 2, 1],
  "trace_padded_indices_budget16": [3, 0, 5, 2, 1, 1, 1, …, 1],
  "trace_loss_weights_budget16": [w, w, w, w, w, w/12, …, w/12],
  "is_terminal_flags": [0, 0, 0, 0, 0, 1, 0, 1, …],
  "terminals": ["k7m", "x4c", "p8n"],
  "group_id": "gb2-000042-7kd93m", "pair": {"role": "base"}
}
```

### Loss normalisation (anti-overweighting)

`trace_loss_weights` sum to 1 per example: every unique state `t = 0..depth` receives `w = 1/(depth+2)`; the single conceptual "absorbing state" receives `w` **spread uniformly over its repetitions**. Short problems are not overweighted by their many padding repetitions; long traces are not overweighted either.

```text
L = CE(final answer) + α · Σ_t weight_t · CE(state_t, exact_t)     α = 0.5 (pilot, then registered)
```

### Controlled pairs (causal interventions)

| Variant | Transformation | Oracle requires |
|---|---|---|
| `decisive_edge` | retarget one edge **on the answer path** to another terminal | answer **changes** |
| `distractor_edge` | retarget one edge **off the path** to a terminal | answer **stays** |

Same nodes, same candidates, same number of edges; variants of a group always stay in the same split.

## 3. Architecture

```text
init:      h₀ = state_init([memory_encoder(entity features), question])     [B, N, d]
           p₀ = one-hot(start)                    (task-constrained, never a free summary)

step:      m_i(t) = Σ_j p_j · φ(h_j, h_i, rel_ji) / Σ_j p_j      (wavefront emitted by the pointer)
           h_i(t+1) = GRUCell([m_i, question, p_i], h_i)          (SHARED transition)
           p_t       = softmax(pointer_head(h_t))                 (active pointer)
           terminal already pointed at ⇒ frozen (absorbing structurally)

readout:   summary = Σ_i p_T,i · h_T,i
           score_c = MLP_shared([summary, RAW features of candidate c])   (no question, no contextualised candidate)
```

| Component | Design |
|---|---|
| `memory_encoder` | Linear(feature_dim→64) + LayerNorm + GELU; features = **one-hot entity identity only** (no terminal flag — that is private) |
| `state_init` | MLP(d+question_dim → 128 → 64) + LayerNorm |
| `SharedTransition` | message MLP `φ: (h_j, h_i, relation) → d` + `GRUCell(d + q + 1 → d)` + LayerNorm; **one copy**, applied 16 times |
| `PointerHead` | Linear(d→1) + masked softmax; `p_t` is both supervision target and message emitter |
| `CandidateReadout` | Linear(feature→d) + MLP([summary, candidate]) — anti-shortcut |
| `DirectScorer` | **separate module**, no shared parameters: mean-pooled entity encoding → same readout form (control) |
| Budget | `max_steps = 16` fixed; absorbing terminal once pointed at |
| Params | **92,802** |
| α | 0.5 (fixed at pilot, then recorded) |

### Anti-shortcut guarantees (E0)

- The final readout receives neither the question nor contextualised candidates — only the computed state summary and raw candidate features.
- `p₀` is the one-hot start pointer (a task constraint), not a learned summary.
- The absorbing terminal is structural and uses only public information (a node with no successor).
- `batch.hops` (depth) is **never** read by the executor forward.

## 4. The two E0 bugs (and why they matter)

Diagnostic over-training on 128 short problems plateaued at ~52–55 % full trajectory. Root causes:

1. **Pointer not reinjected.** Without `p_i` in the transition cell and without messages emitted by the pointer, the state had no marker of the active node: the model could not chain more than ~2 hops. Fix: state = `(h, p)`, wavefront carried by `p`, emitter mass normalised.
2. **Terminals frozen at initialisation.** `has_successor` froze terminal `h` from step 0, so the wavefront could never reach them; the model only learned internal nodes. Fix: freeze applies only to a terminal **already pointed at**.

After the fixes: **100 % full trajectory on E1 in 500 steps** (α = 0.5, lr 3e-3), depths 1/2/3 pooled.

> **Meta-lesson (registered):** a ~2-hop ceiling can come from the assembly, not from the task. This retroactively weakens — without changing — V1's saturation interpretation.

## 5. Gate results

### E1 — overfit a small set (128 problems, depths 1–3, 9 nodes)

| Metric | Value | Criterion |
|---|---:|---|
| Autonomous full trajectory | **1.000** (128/128) | ≥ 0.90 |
| Autonomous final answer | 1.000 | — |
| Teacher-forced final | 1.000 | — |
| Loss | 2.2696 → 7.84e-05 | — |
| Cost | 452 s CPU, 700 updates, 22,400 examples | — |

### E2 — zero-shot transition on unseen graphs (335 problems, 13–15 nodes, depths 1–4)

| Metric | Value |
|---|---:|
| Next-state accuracy given exact states | **919/919 = 1.000** |
| By depth (incl. depth 4 unseen) | 1.000 everywhere |
| Base 767/767 · decisive-edge pairs 152/152 | 1.000 |
| Cost | 1.32 s CPU |

**Secondary anomaly (outside criterion):** autonomous pointers 100 %, but final readout 0.725 overall — split by entity index: answer > 9 → 25.3 % (n = 87) because E1 only had ≤ 10 nodes. The transition was intact; the **readout identity generalisation** was the issue. E3 (13–16 nodes) was required before any autonomous-answer claim.

### E3 — depths 2/3/4, 13–16 nodes, branch A (`concat`)

| Metric | Value | Criterion |
|---|---:|---:|
| Autonomous full trajectory | **1.000** (255/255) | ≥ 0.90 |
| Conditional transition (exact states) | **1.000** | ≥ 0.98 |
| Final answer autonomous | 1.000 | — |
| Per depth d1/d2/d3/d4 | 1.000 everywhere | — |
| Executor vs direct (final answer) | **1.000 vs 0.204** | diagnostic |
| Transitions vs direct | 203 corrections · 0 degradations · 52 both-correct | — |
| Cost | 132.96 s CPU, 800 steps | — |

**Attempt 1 failed** (trajectory 0.000, pointer diffuse): optimisation collapse at lr 3e-3 on the full 855-problem pool. Diagnostic over-training proved expressivity was fine (single problem 100 %, subsets 100 %, full pool at lr 1e-3 100 %). Attempt 2 (lr 1e-3, 800 steps) passed; both runs are kept with their registry ids.

#### k-sweep on the same checkpoint (same weights, varying steps)

| k | State at k correct | Full trajectory prefix | Final answer | Answer change vs k−1 |
|---:|---:|---:|---:|---:|
| 0 | 1.000 | 1.000 | 0.188 | — |
| 1 | 1.000 | 1.000 | 0.271 | 0.780 |
| 2 | 1.000 | 1.000 | 0.522 | 0.722 |
| 4 | 1.000 | 1.000 | **1.000** | 0.478 |
| 8 | 1.000 | 1.000 | 1.000 | 0.000 |
| 16 | 1.000 | 1.000 | 1.000 | 0.000 |

The states advance one hop per iteration; the answer becomes readable only once the terminal is reached (k ≥ depth); saturation at k = 4 = max depth. **Iterations are causally necessary and sufficient.**

### E4 / E4b — zero-shot depths 6/8/10/16 and stress 20 nodes

Trained on E3_train **only** (depths 2/3/4), with `index_space = 20` — random entity re-indexation each step, because indices are arbitrary positions by contract; without it the model never uses columns 16–19.

| Subset | n | Full trajectory | Final | States |
|---|---:|---:|---:|---:|
| Common range (≤16 nodes) | 369 | **1.000** | 1.000 | 1.000 |
| Stress (20 nodes) | 30 | **1.000** | 1.000 | 1.000 |
| **Total** | **399** | **1.000** | **1.000** | 1.000 |

- Depth curve d1..d16: **1.000 everywhere** (d6 n=115, d8 n=99, d10 n=98, d16 n=24).
- Base 312/312, decisive-edge pairs 87/87.
- **Zero state divergence** (0 first divergences) — no accumulation analysis needed.
- k-sweep: final answer 0.286 (k0) → 0.584 (k6) → 0.759 (k8) → 0.960 (k10) → **1.000 (k16)**.
- Cost: 174.12 s training + 2.32 s evaluation, CPU.

**Exact pad16 parity on the common range** (both 1.000) → no regression from the range lever.

## 6. Honest limits of stage S

- E4b's pad20 index range was **exposed by retraining** (random re-indexation), not "never seen"; the *depth* generalisation is separate and clean.
- S uses exact structured memory: it is a **diagnostic of the executor**, evidence about nothing linguistic.
- Saturated at 1.000 means "on this task distribution"; it does not predict text performance — that is exactly what stage T tests.
