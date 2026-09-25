# 07 — V2.2: interface ablations (ongoing at snapshot)

*Protocol pre-registered 2026-09-25 14:03; A1 14:11; A1-bis 14:35–14:40; A2 launched 15:04, restarted 15:31, still running at this snapshot (2026-09-25 ≈16:00).*

## 1. Central hypothesis (pre-registered before any implementation)

> The pipeline's depth deficit comes from the **discretisation at the interface** (per-edge argmax: one missing edge kills the chain), **not** from the reader's inability (edge F1 0.93; the deterministic parser reaches ≈0.95 from public text). Propagating **successor distributions** — `p_{t+1} = p_t A`, terminals self-looping — should recover a measurable part of the gap to the ceiling.

Ceiling reference: parser (p) = 0.95 (bounded to templates, an existence proof, not the target).

## 2. Ablations (one at a time, fixed order)

| id | Content | Training |
|---|---|---|
| **A1** | propagation `p_{t+1} = p_t A` on the **frozen reader's** distributions: `p₀ = one-hot(start)`, `A[i,:] = softmax(successor_logits[i])`, terminal column = self-loop, T = 20, answer = argmax over **candidate nodes** of `p_T` | **none** |
| **A2** | reader retrained with **distributional supervision** (transitions + states + answer, progressive weights) + explicit **INCONNU** class | yes (LoRA) |
| **A3** | direct path with an **equal** auxiliary head (same annotations) if a benefit is claimed | after A2, conditional |
| **A4** | lazy relation reading (relation needed at the current step) | conditional |

### Frozen criteria (before any run)

- Evaluation on the **sealed V2.1 benches** (B1–B8) — pure evaluation, no selection.
- **Success A1/A2:** Δ(c_prop − c_discret) ≥ **+5.0 pts on B3 (depth 8)**, paired by `base_group_id`, grouped bootstrap 2000, **CI low > 0**; short-chain non-regression: c_prop ≥ c_discret − 2.0 pts on B1.
- Systematic publication: Δ vs direct (descriptive), gap to the (p) ceiling, coverage.
- CPU/GPU tie-break: any argmax comparison within `eps = 1e-3` logit scale resolved by stable key (alphabetical label order), applied from V2.2 onward.

## 3. A1: failure, and why it was informative

A1 propagated distributions from the frozen reader — but used `successor_logits`, the **bilinear head**. In `fact` mode, `extract()` uses the fact-level heads (`fact_logits`) and **never touches the bilinear head**, which the training script never supervised. Measured top-1 of that head: **0.054 ≈ chance**. A1 propagated **noise**. Result: c_prop 0.19–0.32 vs c_discret 0.56–0.81 → Δ B3 = **−38.25 pts**, flagrant FAIL.

**Archive incident (transparency):** while recovering the A1 archive, the QA imported the A1 runner, which executed at import and rewrote B1 in CPU mode (0.3450). The aggregate published before contamination (0.3225) was verified item-by-item by the QA; B2–B8 were untouched. The runner was regenerated on GPU with **bit-identical aggregates (8/8)**; `if __name__ == "__main__"` guards were added to all V2.2 runners (verified by `grep`).

A1 remains a documented failure; its "0.75^k mass-leak" explanation was **withdrawn** — the real cause was an unsupervised head.

## 4. A1-bis: propagation from supervised fact-level distributions (PASS)

**Transition matrix** (`transition_matrix_from_facts`, no training):

```text
A[u, v] = Σ_f P(subject_f = u) · P(object_f = v)
terminal: identity self-loop (the reached terminal is preserved)
INCONNU: absorbing global sink  max(0, 1 − Σ_f P(subject_f = u))   (no silent renormalisation)
tie-break: eps = 1e-3, stable key
```

Frozen reader, zero training, zero optimiser, `no_grad`; start = deterministic `extract()` start.

### QA-validated results (8/8 benches, recalculated independently)

| Bench | c_prop | c_disc | Δ (pts) [CI95] | Δ vs direct (pts) |
|---|---:|---:|---|---:|
| B1-court | 0.8550 | 0.8000 | **+5.50** [+1.50,+9.25] | −8.25 |
| B2-prof6 | 0.8375 | 0.6675 | **+17.00** [+12.50,+21.50] | +31.25 |
| B3-prof8 | 0.8525 | 0.5975 | **+25.50** [+20.75,+30.00] | **+57.25** |
| B4-prof10 | 0.8550 | 0.5600 | **+29.50** [+24.50,+34.75] | +54.75 |
| B5-surface | 0.8525 | 0.8100 | **+4.25** [+0.25,+8.25] | −8.75 |
| B6-distract | 0.8325 | 0.7725 | **+6.00** [+2.25,+9.75] | −10.50 |
| B7-options | 0.8550 | 0.8000 | **+5.50** [+1.50,+9.25] | −8.50 |
| B8-depart | 0.8575 | 0.7650 | **+9.25** [+5.25,+13.50] | +1.75 |

- **c_prop ≈ 0.83–0.86, invariant in depth** — the depth decay (0.80 → 0.56 for discretisation) disappears.
- Main criterion: B3 +25.5 pts, CI low +20.75 > 0 ✓; B1 non-regression +5.5 ✓ → **PASS**.
- CI > 0 on **all 8 benches** (tightest: B5 +4.25 [+0.25,+8.25] — published as is).
- Remaining gap to the (p) ceiling ≈ 9–12 pts; INCONNU semantics unused in A1-bis.
- QA: 0 disagreement item/flag with the archived metrics; pre-registration spec committed as `V22_A1BIS_SPEC.md` (QA reserve n°4 resolved).

**Interpretation:** the bottleneck was indeed the interface (audit §6.2), demonstrated by the cheapest possible proof: **zero training** on top of frozen checkpoints.

## 5. A2: distributional retraining (running)

**Design (co-signed pre-registration):**

- Reader initialised from `reader_lora_best.pt`; only the INCONNU head is new; identical LoRA recipe (r16/α32, q/k/v/o, dropout 0.05, two LRs, 1200 steps, seed 17);
- **distributional losses added to the loop**: transitions supervised as distributions, propagation `p_{t+1} = p_t A` **inside** the graph so the answer CE backpropagates through the propagation to the edge distributions (this is the defining difference vs A1);
- state supervision per step; answer CE with γ = 1.0; state CE weight β = 0 before step 200, linear 0→1 on [200, 600), 1.0 after;
- **INCONNU semantic:** a mention with neither a subject fact nor a terminal fact becomes `−2`; INCONNU is a distinct absorbing category, **not** a trash class and **not** a terminal ("absence of information ≠ terminal", audit §5);
- **training-only augmentation:** 25 % of items with one fact (+ its recalls) removed, seed 17 deterministic; answer/state CEs masked on those items (local CEs only). Evaluation benches are **not** augmented — they measure raw performance, not robustness;
- transition space: N successors + TERMINAL (index N) + INCONNU (index N+1), T = 20, no silent renormalisation; answer = argmax over candidate nodes; same `eps` tie-break;
- **selection:** fresh bench seed 2213 (never used): primary = c_prop, tie-break = discretisation then smallest step; `eval_every = 100`; **strict dependency**: if the bench is absent, A2 waits — no fallback selection on sealed benches;
- evaluation on sealed V2.1 benches with the extended A1 harness (INCONNU sink + tie-break); the A1 grid applies unchanged.

**Incidents:** run 1 (15:04–15:28) was cancelled for two reasons: an OOM because gradient checkpointing was never actually active in the trainer (infrastructure patch, maths unchanged), and an evaluation bug where a gold/predicted mismatch corrupted c_prop. A2 was relaunched with the **frozen config unchanged** after fixes.

**Status at snapshot (15:42, run 2):** step 300 on the selection bench (n = 400): c_prop **0.990–0.995**, b_discret 0.9125–0.9675 (best at step 200: 0.99 / 0.9675). The run has 1200 steps planned. **No conclusion is drawn from a running experiment**; interim numbers are shown only to document the state of work.

## 6. What comes after (pre-registered chain)

1. **A2 verdict** on the sealed benches under the A1 grid; publication of Δ vs A1-bis, vs discretisation, vs direct, coverage, and gap to ceiling.
2. **A3 only if a benefit is claimed**: direct path with an equal auxiliary head (same annotations, same targets) — otherwise A2 is descriptive.
3. **Router oracle bound** (complementarity 123/172/163 items): measure the achievable gain before building any router; the direct path's NLL (8.85 nats at depth 10 when wrong) is the routing signal candidate.
4. **End-to-end costs** (text→decision): p50/p95 latency, throughput, memory, both paths batched with equal rights.

## 7. Why this sequence matters

V2.2 is the first stage of the project where **the counter-intuitive result survives** and the method protects it:

- A1 failed for a real reason (unsupervised head) and the failure was kept;
- A1-bis passed **without any training**, which excludes several alternative explanations (no new parameters, no new data, sealed benches);
- A2 exists only because A1-bis left ≈9–12 pts to the ceiling, and it was pre-registered before implementation;
- the fairness rule (A3) is already armed so that any claimed benefit is immediately contested on equal terms.
