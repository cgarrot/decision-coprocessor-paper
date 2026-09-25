# 07 — V2.2: interface ablations — closed (A1 FAIL, A1-bis PASS, A2 PASS, A3 architectural superiority)

*Protocol pre-registered 2026-09-25 14:03; A1 14:11; A1-bis 14:37; A2 run 15:29–16:32; A3 17:20–18:48; router bound and end-to-end costs 18:30–18:54; QA closure REG-81 at 19:06. **All V2.2 gates are closed.***

## 1. Central hypothesis (pre-registered before any implementation)

> The pipeline's depth deficit comes from the **discretisation at the interface** (per-edge argmax: one missing edge kills the chain), **not** from the reader's inability (edge F1 0.93; the deterministic parser reaches ≈0.95 from public text). Propagating **successor distributions** — `p_{t+1} = p_t A`, terminals self-looping — should recover a measurable part of the gap to the ceiling.

The hypothesis was validated **twice**: once with zero training (A1-bis), once with supervised distributional training (A2).

## 2. Ablations (one at a time, fixed order)

| id | Content | Training | Outcome |
|---|---|---|---|
| **A1** | propagation `p_{t+1} = p_t A` on the **frozen reader's** bilinear successor head | none | **FAIL** — propagated noise from an unsupervised head |
| **A1-bis** | same propagation, matrix built from the **supervised fact-level** heads | none | **PASS** — c_prop ≈ 0.85 invariant in depth |
| **A2** | reader retrained with **distributional supervision** + propagation in the loop + explicit **UNKNOWN** (INCONNU) class | yes (LoRA) | **PASS TOTAL** — c_prop 0.995–1.000 on 8/8 benches, above the parser ceiling |
| **A3** | direct path with an **equal** auxiliary head (same annotations, same targets, same augmentation, same selection) | yes (LoRA) | direct stays collapsed in depth (0.25–0.28) → **architectural superiority of propagation, 8/8** |

Frozen criteria (before any run): Δ(c_prop − c_discret) ≥ **+5.0 pts on B3 (depth 8)**, paired by `base_group_id`, grouped bootstrap 2000, **CI low > 0**; short-chain non-regression c_prop ≥ c_discret − 2.0 pts on B1; sealed V2.1 benches as pure evaluation; stable `eps = 1e-3` tie-break; new selection bench seed 2213 only.

## 3. A1: failure, and why it was informative

A1 propagated distributions from the frozen reader — using `successor_logits`, the **bilinear** head. In `fact` mode, `extract()` never touches that head, and training never supervised it (top-1 **0.054 ≈ chance**). A1 propagated **noise**: c_prop 0.19–0.32 vs discretisation 0.56–0.81 → Δ B3 = **−38.25 pts**, flagrant FAIL.

**Archive incident (transparency):** while recovering the A1 archive, QA imported the A1 runner, which executed at import and rewrote B1 in CPU mode (0.3450). The aggregate published before contamination (0.3225) was verified item-by-item by QA; B2–B8 untouched. The runner was regenerated on GPU with **8/8 aggregates bit-identical**; `__main__` guards added to all runners. The initial “0.75^k mass-leak” explanation was **withdrawn** and replaced by the real cause (unsupervised head).

## 4. A1-bis: zero-training repair (PASS)

**Transition matrix** (`transition_matrix_from_facts`, no training):

```text
A[u, v] = Σ_f P(subject_f = u) · P(object_f = v)
terminal: identity self-loop;  UNKNOWN: absorbing global sink max(0, 1 − Σ_f P(subject_f = u))
no silent renormalisation;  tie-break eps = 1e-3, stable key
```

Frozen reader, zero training, zero optimiser, `no_grad`; start = deterministic `extract()` start.

| Bench | c_prop | c_disc | Δ [CI95] | Δ vs direct |
|---|---:|---:|---|---:|
| B1 short | 0.8550 | 0.8000 | **+5.50** [+1.50; +9.25] | −8.25 |
| B2 depth 6 | 0.8375 | 0.6675 | **+17.00** [+12.50; +21.50] | +31.25 |
| **B3 depth 8** | 0.8525 | 0.5975 | **+25.50** [+20.75; +30.00] | **+57.25** |
| B4 depth 10 | 0.8550 | 0.5600 | **+29.50** [+24.50; +34.75] | +54.75 |
| B5 surface | 0.8525 | 0.8100 | **+4.25** [+0.25; +8.25] | −8.75 |
| B6 distractors | 0.8325 | 0.7725 | **+6.00** [+2.25; +9.75] | −10.50 |
| B7 options | 0.8550 | 0.8000 | **+5.50** [+1.50; +9.25] | −8.50 |
| B8 other start | 0.8575 | 0.7650 | **+9.25** [+5.25; +13.50] | +1.75 |

c_prop ≈ 0.83–0.86, invariant in depth; CIs exclude zero on 8/8; QA validated (0 item/flag disagreement). The bottleneck was the interface — proven by the cheapest possible experiment.

## 5. A2: supervised propagation (PASS TOTAL)

### Design (co-signed pre-registration)

- Reader initialised from `reader_lora_best.pt`; identical LoRA recipe (r16/α32 q/k/v/o, dropout 0.05, two LRs, 1200 steps, seed 17);
- **distributional losses**: transitions supervised as distributions, propagation `p_{t+1} = p_t A` **inside** the graph so the answer CE back-propagates to the edge distributions; per-step state supervision; answer CE γ = 1.0; state CE weight β = 0 before step 200, linear 0→1 on [200, 600), 1.0 after;
- **UNKNOWN (INCONNU)**: a mention with neither a subject fact nor a terminal fact becomes `−2`; distinct absorbing category, not a terminal (“absence of information ≠ terminal”). Training-only augmentation: 25 % of items with one fact (+ recalls) removed, seed 17, answer/state CEs masked — evaluation benches unaugmented;
- transition space: N successors + TERMINAL + UNKNOWN, T = 20, no silent renormalisation, answer = argmax over candidate nodes, stable tie-break;
- **selection**: bench seed 2213 only (c_prop primary, then discretisation, then smallest step); sealed V2.1 benches are evaluation-only;
- incidents: run 1 cancelled (inactive gradient checkpointing → OOM; selection eval anchored gold vs predicted); relaunched with frozen config unchanged. A PEFT loader bug (`.default` keys silently ignored, **28/224** LoRA keys loaded) was exposed and fixed (`pm.load_state_dict` + load assertions, 100 %).

### Results — 8/8 benches (QA-recalculated, identical)

| Bench | c_disc | A1-bis | **A2** | Δ A2 vs disc [QA CI] | Δ A2 vs direct [QA CI] |
|---|---:|---:|---:|---|---|
| B1 short (1–4) | 0.800 | 0.855 | **0.9950** | +19.50 [+15.25; +23.50] | **+5.75** [+3.25; +8.25] |
| B2 depth 6 | 0.667 | 0.838 | **0.9975** | +33.00 [+28.25; +38.00] | **+47.25** [+42.50; +52.25] |
| **B3 depth 8** | 0.598 | 0.853 | **0.9975** | **+40.00** [+34.75; +45.00] | **+71.75** [+67.00; +76.25] |
| B4 depth 10 | 0.560 | 0.855 | **0.9975** | +43.75 [+39.00; +48.75] | **+69.00** [+64.50; +73.25] |
| B5 surface | 0.810 | 0.853 | **1.0000**\* | +19.00 [+15.25; +23.00] | **+6.00** [+4.00; +8.50] |
| B6 distractors | 0.773 | 0.833 | **1.0000**\* | +22.75 [+19.00; +27.00] | **+6.25** [+4.00; +8.75] |
| B7 options (K=6) | 0.800 | 0.855 | **0.9950** | +19.50 [+15.25; +23.50] | **+5.50** [+3.25; +8.00] |
| B8 other start | 0.765 | 0.858 | **0.9975** | +23.25 [+19.25; +27.50] | **+15.75** [+12.25; +19.75] |

\* **Declared saturation**: B5/B6 no longer separate systems above 0.995.

- **Grid PASS**: B3 Δ = +40.0 pts (≥ +5), CI low +34.75 > 0; baseline control c_prop B3 0.9975 ≥ A1-bis 0.8525; B1 non-regression +19.5.
- **Δ vs direct positive on 8/8, CI > 0 everywhere** (tightest: B1 +5.75 [+3.25; +8.25]).
- **c_prop > parser ceiling 0.95** on every bench.
- **Probabilistic quality (dedicated capture, prediction identity asserted 400/400 × 8):** NLL **0.0044–0.0294**, Brier gold-class (1−p_oracle)² 0.0007–0.0061 — versus the direct path's NLL 0.59→8.85 nats with depth (ECE B1 0.061). A2 is exact *and* calibrated.
- Cost: training 4054.64 s (≈68 min) GPU under the single-job lock; selection best = step 1200 (c_prop 1.0 on bench 2213).

## 6. A3: equal auxiliary supervision for the direct path (the audit's obvious attack, answered)

A2's benefit could have been an artefact of additional supervision. A3 gives the **direct LoRA path the exact same auxiliary targets**: relation heads (same fact-level subject/object targets), state trajectory heads (same gold-path targets, same β schedule), same losses, same INUNKNOWN augmentation, same recipe and selection bench. Pre-registered conclusion rule: if Δ(A2−A3) > 0 with CI low > 0 per bench → architectural superiority of propagation; otherwise publish descriptive results.

| Bench | A3 (direct + equal aux.) | direct V2.1 | Δ(A2−A3) [QA CI] | Δ(A3−direct) [QA CI] |
|---|---:|---:|---|---|
| B1 short | 0.9625 | 0.9375 | **+3.25** [+1.50; +5.25] | +2.50 [+0.25; +4.75] |
| B2 depth 6 | 0.4925 | 0.5250 | **+50.50** [+45.50; +55.50] | −3.25 [−8.50; +2.25] |
| B3 depth 8 | 0.2475 | 0.2800 | **+75.00** [+70.50; +79.01] | −3.25 [−8.50; +1.75] |
| B4 depth 10 | 0.2825 | 0.3075 | **+71.50** [+66.75; +75.76] | −2.50 [−7.75; +2.75] |
| B5 surface | 0.9575 | 0.9400 | **+4.25** [+2.25; +6.25] | +1.75 [−0.25; +3.75] |
| B6 distractors | 0.9450 | 0.9375 | **+5.50** [+3.49; +7.75] | +0.75 [−1.25; +2.75] |
| B7 options | 0.9600 | 0.9400 | **+3.50** [+1.50; +5.50] | +2.00 [0.00; +4.00] |
| B8 other start | 0.8550 | 0.8400 | **+14.25** [+10.75; +18.00] | +1.50 [−1.50; +4.75] |

**Verdict (QA REG-78): architectural superiority of propagation validated, per bench, 8/8**, no saturation (A2 0.9975 vs A3 0.2475–0.2825 in depth). The asymmetry is quantified: **+3.25 to +5.5 pts at short depth versus +50.5 to +75 pts in depth**. A3 ≈ direct V2.1 (only B1 significant, +2.5 pts): **auxiliary supervision alone does not repair depth; propagation is what carries the gain.** A3's `relations` head is not used at inference (training shaping only).

## 7. Router oracle bound: measured, then declared useless

Pre-committed rule: measure the oracle router bound before building anything. Using the QA-validated archive:

- Oracle (A2 **or** A3): 0.9975–1.0000 per bench → **+0.00 to +0.50 pts over A2 alone**;
- A3-only correct items: **0–2 per bench**;
- The V2.1 complementarity (123/172/163 items) is **absorbed by A2 at 0.995+**.

→ **No router is needed; none was built.** (REG-79)

## 8. End-to-end costs (QA-validated, REG-81)

Measured on both paths with equal batches, same order, warmup 2, CUDA sync, LoRA load asserted 100 % ×2 (224/224).

| Measure | A2 pipeline | A3 direct | Ratio |
|---|---:|---:|---:|
| B1 item p50 / p95 (batch 8) | 40.32 / 46.20 ms | 32.65 / 38.12 ms | ×1.235 / ×1.21 |
| B3 item p50 / p95 (batch 8) | 51.59 / 55.42 ms | 40.52 / 43.51 ms | ×1.273 / ×1.27 |
| Throughput B1 / B3 | 22.65 / 18.66 it/s | 28.98 / 23.55 it/s | ×0.78–0.79 |
| **Propagation step alone** | **0.59–0.66 ms/item (≈1.3–1.5 % of A2 p50)** | — | negligible |
| Peak allocated VRAM | 1472–1512 MiB | parity | — |

**Operational reading:** A2 pays **+23–27 % latency** for +5.75 pts (B1) and **+50–75 pts** in depth; the architectural core (propagation) is **free**. The cost is carried by extraction (the reader), not by the transition math. Multi-question cache amortisation remains a noted future measurement (no cross-question cache in the harness).

## 9. Incidents (all published, no impact on published numbers)

| Incident | Cause | Correction | Impact |
|---|---|---|---|
| A1 mechanism “0.75^k” withdrawn | bilinear head never supervised in fact mode | retraction; A1-bis pre-registered on the true (fact-level) source | interpretation replaced; A1 kept as a valid failure artefact |
| A2 run 1 cancelled | OOM (GC never active) + selection eval anchored gold vs predicted candidates | GC enabled + predicted re-anchoring + cross-check `--self-check` (tests 143+) | no published number from run 1 |
| PEFT loader `.default` (3 false starts) | `set_peft_model_state_dict` silently ignores `.default` keys → LoRA loaded nearly empty (28/224) | `pm.load_state_dict` + **load assertions** (now 100 %) | no published number from a broken state |
| A3 tool kill + `encode→adapter.encode` fix | harness timeout at launch (0 steps); signature mismatch at selection | relaunch; interface fix | none |
| B1-A1 archive contaminated | QA imported a runner without `__main__` guard (CPU re-run) | guards everywhere; A1 regenerated on GPU, **8/8 aggregates bit-identical** | aggregates intact; accidental CPU value nonexistent |

## 10. Limits and scope (conclusions ≠ claims)

- **“Architectural superiority on these benches”**: synthetic French templated task, **1 seed**, checkpoints selected on 2213 — **no OOD generalisation claimed**.
- **UNKNOWN is defined but not evaluated**: chain-broken / partially observed worlds require new benches (task extension, separate protocol) — declared remaining milestone.
- **Saturation B5/B6**: harder benches would be required to separate systems above 0.995.
- A3's `relations` head unused at inference; load assertions raised from 90 % to 100 %.
- All numbers environment-bound (GPU RTX 3070 Laptop, bf16, batch 8; CPU↔GPU ≈ 6 pts variance on this near-tie reader, R7).

## 11. What V2.2 changed

Before V2.2, the project's final story was: *“decomposition is dominated on short chains; beyond depth 6 the frozen pipeline wins while the direct path collapses; the remaining gap is the interface.”*

After V2.2, the story is:

> **The interface was the whole deficit.** Propagating successor distributions from supervised fact-level heads — first with zero training, then with distributional training — makes the decomposed pipeline accurate (0.995–1.000) **and depth-invariant**, beating the direct path on all 8 sealed benches with CIs excluding zero, beating its own parser ceiling, and dominating **even when the direct path receives identical auxiliary supervision** (+50 to +75 pts in depth). The gain is architectural, not a supervision artefact; the router is useless because the pipeline absorbed the complementarity; and the architectural core costs ≈1.3–1.5 % of end-to-end latency.

The V2 arc is therefore complete: **the mechanism was demonstrated (S), the naive assembly was refuted (T), the refutation was scoped (V2.1), and the deficit was fixed and attributed (V2.2)** — every step under pre-registered, independently recalculated gates.
