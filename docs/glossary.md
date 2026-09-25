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
| **A1 / A1-bis / A2 / A3 / A4** | V2.2 ablations: frozen-reader propagation via the (unsupervised) bilinear head → failed; propagation from supervised fact-level heads → passed with zero training; distributional retraining + UNKNOWN → running; equal auxiliary head for the direct path (conditional); lazy relation reading (conditional). |
| **INCONNU (UNKNOWN)** | Explicit category for “no information”, distinct from terminal: a mention with neither a subject fact nor a terminal fact. |
| **Environment-bound (env.)** | A number valid under the recorded measurement environment (GPU RTX 3070 Laptop, bf16, batch 8); CPU/GPU can differ by ≈ 6 pts on near ties. |
| **Experience stop** | A project-level decision to stop investing in a configuration on clearly unfavourable results — distinct from a general scientific claim. |
| **Product validation** | A deployment-grade claim; never made anywhere in this project. |
| **Entropy / ECE / Brier / NLL** | Probabilistic quality metrics published together (ECE alone can mislead — see the uniform baseline). |
