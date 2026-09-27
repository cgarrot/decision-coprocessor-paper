# Glossary

| Term | Definition |
|---|---|
| **Sidecar / coprocessor** | A small trainable module attached after a frozen backbone's encoding, adding computation without generating text. In V1: the latent recurrent sidecar (`LatentSidecar`, R1/R2/R4). |
| **Direct path (B2 / d)** | One backbone pass → decision head → probabilities over candidates. The baseline to beat. |
| **Transition executor (S)** | V2 model: explicit state `(h, p)`, one shared transition `F` applied repeatedly, exact state-trace supervision, anti-shortcut readout. 92,802 parameters, CPU stage. |
| **State `s_t = (h_t, p_t)`** | `h`: one vector per entity; `p`: pointer distribution over nodes marking the active position. |
| **Absorbing terminal** | A node with no successor; once the pointer reaches it, it no longer moves (structural, public information). |
| **Anti-shortcut readout** | Final scoring that receives only the computed state summary and raw candidate features — never the question or contextualised candidates. |
| **Family B (simplified)** | Synthetic relational task: disjoint chains, unique successor, no cycles, ≥3 terminals, unreachable distractors, opaque renamed entities, shuffled facts/options. |
| **Trace loss weights** | Per-slot weights summing to 1, spreading the absorbing-state mass so short problems are not overweighted. |
| **k-sweep** | Evaluating one trained model at different numbers of transition steps (k = 0/1/2/4/8/16) to test whether iterations are causally necessary. |
| **Gate (E5 criteria)** | Frozen numeric thresholds a stage must pass (e.g. reader entities ≥ 0.85, edges ≥ 0.65, solve ≥ 0.35). |
| **Sealed set** | An evaluation set generated but never opened, or opened exactly once after pre-registration; `E5_eval`/`E5v2_eval` are sealed forever. |
| **Pre-registration** | A dated, hashed protocol document (hypothesis, thresholds, stops, prohibitions) committed before the run. |
| **Selection bench** | A reserved pool used only to choose checkpoints (e.g. seed 2213 for A2); never used for evaluation. |
| **QA (independent)** | The agent that re-implements oracles and recalculates metrics from archived predictions; its findings can block gates. |
| **Pair / group_id** | Controlled variants (decisive edge retargeted, distractor changed, paraphrase, permutation) always kept in the same split; the unit of paired statistics. |
| **Decisive vs distractor edge** | On-path edge whose retargeting must change the answer vs off-path edge whose retargeting must not. |
| **All-in vs covered** | All-in: abstentions counted as errors. Covered: accuracy conditional on answering; coverage/risk published separately. |
| **Pairwise coupled bootstrap** | Resampling `group_id` units jointly across variants (2000 replicates) to build CIs on paired deltas. |
| **Fairness F1** | Rule: identical representation/adaptation budgets for pipeline and direct control before any comparison. |
| **Mechanism precedence** | Registered rule: mechanism evidence (causal profile) outranks a positive delta; a grey-zone delta cannot validate a decomposition. |
| **Discretisation (interface)** | Taking per-edge argmax of reader distributions before execution; a single missing edge breaks the chain. |
| **Propagation (`p_{t+1} = p_t A`)** | Replacing argmax by distribution propagation through a transition matrix `A`; terminals self-loop; UNKNOWN is an absorbing sink. |
| **A1 / A1-bis / A2 / A3 / A4** | V2.2 ablations: frozen-reader propagation via the (unsupervised) bilinear head → failed; propagation from supervised fact-level heads → passed with zero training (0.85 invariant); distributional retraining + UNKNOWN → **passed total** (0.995–1.000, 8/8); direct with equal auxiliary supervision → direct stays collapsed in depth, proving architectural superiority of propagation; A4 (lazy relation reading) not triggered. |
| **R0 / R1 (C1)** | Same-reader ablation conditions: R0 = E5v3-A frozen reader; R1 = A2 reader. Combined with hard/soft decoding to attribute the gain. |
| **hard / soft decoding** | hard = discretise the reader's distributions then walk the graph; soft = propagate the distributions (`p_{t+1} = p_t A`). C1's identity: R0-soft ≡ A1-bis, R1-soft ≡ A2 (item-identical). |
| **C0 / C1 / C2 (confirmation)** | Programme driven by audit #3: **C0** scope errata + public inference audit + release manifest; **C1** same-reader 2×2 attribution, anti-leak, complete Brier, sweep, toolchain/CPU-GPU localisation; **C2** three-seed confirmation (C2-a) + blind extrapolation with short-only selection (C2-b). C3 (one extension axis) remains out of scope. |
| **`gold_class_squared_error`** | The published score mean((1−p_gold)²) — *not* the standard multiclass Brier. The complete multiclass Brier (classes = candidates ∪ {AUTRE}, INCONNU + off-candidate mass split) was computed in C1: R1 0.0016–0.0119 vs R0 0.30–0.58. |
| **Blind extrapolation (C2-b)** | Depth performance measured after training **and checkpoint selection** restricted to short chains (depths ≤ 4); criterion ≥0.90 → A2-blind pooled deep 0.9867. |
| **Development evaluation vs independent confirmation** | Benches held out from training/selection but observed during an adaptive campaign are *development* evaluation (V2.1/V2.2 benches). Independent confirmation requires fresh benches, fresh seeds and a protocol frozen before generation (C2). |
| **A2 public inference path** | `extract → fact_logits → transition_matrix_from_facts → start_distribution → propagate(T=20) → answer`. The S executor is **not invoked**; only LoRA + fact heads + explicit propagation. |
| **V2.3 linguistic levels** | **L1-a** paraphrases (surface variation), **L2-inv** inverted syntax, **L3-lbl** label bijection, **L3-adv** separate adversarial lot. `P_eval` (canonical parser) vs variant coverage is explicit. |
| **P2 (diagnosis)** | Pre-registered, no-training failure diagnosis: `p(edge|inv)` constant with depth, mass leak to UNKNOWN 0.38→0.57; H-A partially supported (O1 failed), H-B not supported (V4 unrun), H-C rejected. |
| **E2-bis** | Retraining mixture with the inversion share raised 25 % → 45 % (×1.8); depth-10 inversions 0.90–0.93 with mixture **and** selection restricted to depths 1–4 → **blind extrapolation**; residual UNKNOWN mass 0.38–0.41 (threshold ≤0.25 **failed, published**). |
| **Canonical verdicts** | `V23_CANONICAL_VERDICTS.md` (QA, REG-74→94): the single document that makes faith, replacing historical formulations; multi-criteria verdicts with explicit hierarchy; environment-bound and adaptive-campaign labels. |
| **Documentary residuals (B1–B5)** | Final audit items blocking a “no-residual” certification: E2-bis domain wording (solved by requalification), verdict hierarchy, P2 reserves, release inventory (83 vs 76 dirs), parser/adapter flow. No new experiment required. |
| **INCONNU (UNKNOWN)** | Explicit category for “no information”, distinct from terminal: a mention with neither a subject fact nor a terminal fact. |
| **Environment-bound (env.)** | A number valid under the recorded measurement environment (GPU RTX 3070 Laptop, bf16, batch 8); CPU/GPU can differ by ≈ 6 pts on near ties. |
| **Experience stop** | A project-level decision to stop investing in a configuration on clearly unfavourable results — distinct from a general scientific claim. |
| **Product validation** | A deployment-grade claim; never made anywhere in this project. |
| **Entropy / ECE / Brier / NLL** | Probabilistic quality metrics published together (ECE alone can mislead — see the uniform baseline). |
