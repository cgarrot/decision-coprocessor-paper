# 13 — Lessons across the whole project

*These lessons are the part of the work most likely to transfer to other projects. Each one is backed by a concrete episode of this study.*

## 1. Demonstrate the mechanism before benchmarking it

**Episode.** V1 trained a recurrent sidecar and tested it on a reserved benchmark. The result was negative (Δ = −0.59 pt). The external audit then showed that the correction head received `q, c_i` directly and that a final CE alone imposed no state progression — the mechanism was **never forced to exist** before being measured.

**Lesson.** Before benchmarking a mechanism, run a stage that *cannot* succeed unless the mechanism exists: a tiny overfit set, an exact-input version, an explicit-state supervision, a zero-shot composition test. If the mechanism cannot be shown in the small, a benchmark result — positive or negative — is uninterpretable.

**Applied in V2:** stage S (structured exact input, CPU) preceded every linguistic comparison.

## 2. Equalise representation budgets before comparing architectures

**Episode.** On the frozen backbone the decomposed pipeline was marginally ahead (+5.1 pts, inconclusive). With the same LoRA adaptation given to both sides: direct 1.000 vs pipeline 0.762 → **Δ = −23.8 pts**. The apparent benefit was an artefact of crippling the baseline.

**Lesson (F1, registered as a rule).** In any pipeline-vs-direct comparison, every representation advantage must be offered identically to both paths, with hashed configs. Otherwise the experiment measures the asymmetry, not the architecture.

**Corollary.** Inconclusive-but-positive deltas deserve a fairness re-run before any claim.

## 3. Validate the benchmark before the model

**Episode.** E5 v1 looked fine; a trivial lexical probe plus causal interventions revealed a template shortcut (the direct path scored 0.7775 by exploiting template distributions). The corrected E5v2 dropped the direct path to 0.326 — the “strong baseline” was a mirage.

**Lesson.** A benchmark needs its own adversarial validation:
- a trivial learned probe must be at chance;
- causal interventions must show the model cannot shortcut;
- mention counts, template decks, option wrappers, line lengths must be statistically flat between the answer and distractors;
- the probe itself can discover generator bugs (three of six fixes in E5v2 were found this way).

## 4. Seal sets, pre-register, hash configs

**Episode.** `E5_eval` v1 and `E5v2_eval` were sealed forever; V1's reserved test was opened exactly once. The order "pre-registration → open → predictions" is verifiable from commits and mtimes. Several gates were blocked by QA findings *before* runs (v1.1, v1.3, v1.7bis, R7) — proof the seals were not decorative.

**Lesson.** A result is only as trustworthy as the constraints that bound it:
- thresholds, layers, abstention rules and selection metrics frozen **before** the run, in a hashed config;
- selection only on train/dev (or a dedicated fresh selection bench);
- evaluation benches never used for selection; sealed benches never opened;
- scripts committed before use (no result-tuned analysis code).

## 5. Mechanism takes precedence over benefit

**Episode.** it3 showed Δ = +5.1 pts (grey zone) but the causal profile failed (decisive-fact following 0.388; distractor stability 0.13). Publishing the benefit as a win would have been easy; the registered rule forced issue (iii).

**Lesson.** A delta without a causal profile cannot validate a decomposition; a strong causal profile without a delta does not justify it either. Publish grey zones as grey zones.

## 6. Always publish the controls that could replace your mechanism

**Episode.** B3 (non-recurrent, same parameter budget) and B4 (unshared stack) matched or beat the sidecar in V1. That is what killed H2 — and it is a *feature* of the study, not a failure of the run.

**Lesson.** For every “special” mechanism, build the boring alternative at comparable cost. If the boring alternative wins, the special mechanism is not needed. Budget controls in the design phase, not after.

## 7. Assert your denominators

**Episode.** An evaluation loop with the wrong stride produced n = 814 instead of 411; the drop to 2.1 GiB VRAM and a denominator check exposed it. Duplicate ids silently mismatched gold/predicted pairs (2–14/250 mismatches) until positional matching and an archived `opt_map` fixed it. V2.2/A2's first run had a gold/predicted mismatch that corrupted the selection metric.

**Lesson.** Every metric should carry its numerator and denominator and be asserted against an expected population. Silent windowing, deduplication and id-matching bugs are the most common source of unreal numbers.

## 8. Invariants are better incident detectors than intuition

**Episode.** OOM1 was caught because VRAM read 7.6 GiB vs the usual 2.1 GiB; the E0 bugs were caught because the overfit trajectory plateaued; the pod-quality issues were caught by a specific number moving without a committed reason.

**Lesson.** Record the expected invariants (VRAM, n, loss floor, best=last, hash counts) and assert them. When a number moves, find out why before touching anything else.

## 9. Cost is often not the bottleneck

**Episode.** The sidecar added only +8.3 % latency and < 0.2 GiB VRAM on an 8 GB laptop. The idea did not fail for cost reasons.

**Lesson.** Don't default to “too expensive” as an explanation for a negative result; measure. Conversely, the compute ledger (~5 h GPU for V2, 1.2 GiB VRAM for V1) shows how much science is possible on modest hardware with disciplined design.

## 10. Small models, big process

**Episode.** 92,802 parameters on CPU produced the project's cleanest mechanistic result (E1–E4b), and a zero-training propagation matrix produced a depth-invariant reader improvement (A1-bis).

**Lesson.** Separate *capability* questions from *scale* questions. A 93 K-parameter executor can establish that an operator is learnable and composable; a 5-hour GPU budget can establish that a pipeline is dominated under fair comparison. Scaling studies should be motivated by a demonstrated mechanism, not replace it.

## 11. Decomposition is a trade, not a virtue

**Episode.** The decomposed pipeline wins when the direct path collapses (depth ≥ 6 on frozen checkpoints: +14 to +32 pts) and loses when the direct path can learn end-to-end (fair adaptation: −23.8 pts on short chains). Its bottleneck is the extraction interface, which can be partially repaired without retraining (A1-bis) but still leaves a gap to the 0.95 ceiling.

**Lesson.** The value of explicit decomposition is conditional on (i) the baseline's failure profile and (ii) the fidelity of the interface. State the conditions; never claim "decomposition helps" as a general law.

## 12. The pivot is part of the science

**Episode.** The final V2 state is: stage S demonstrated, stage T refuted under fairness, then V2.1 found the depth reversal, then V2.2 attacked the interface, found that the bottleneck was the discretisation, fixed it (A2), proved the fix was architectural rather than a supervision artefact (A3), measured that routing had become unnecessary, and closed with costs. The “conclusion” moved three times — each time under pre-registered diagnostics, never by reinterpretation of existing numbers.

**Lesson.** When a result is overturned by a new *fair* comparison, publish both states: the original verdict, the reason it was incomplete, and the new protocol. The value of the project is not a single claim; it is the chain of constraints that made each claim falsifiable.

## 13. When you claim a benefit, give the baseline the same supervision

**Episode.** A2 (distributionally trained reader + propagation) dominated the frozen direct path on 8/8 benches. The QA immediately identified the obvious audit attack: A2 received extra supervision (relations, states, UNKNOWN augmentation) that the direct path did not. A3 gave the direct path the **same auxiliary heads, targets, losses, augmentation and recipe**. Result: the direct path stayed collapsed in depth (0.2475–0.2825 at depths 8/10 vs A2 0.9975), Δ(A2−A3) rising from +3.25 pts (short chains) to **+75.0 pts** (depth 8), CI low > 0 on all eight benches.

**Lesson.** Fairness F1 does not stop at representations: it applies to every form of extra information, including auxiliary supervision. A superiority claim that has not answered "what if the baseline had exactly the same heads?" is not yet a claim about architecture.

## 14. Measure the oracle ceiling before building the router

**Episode.** V2.1 had found strong complementarity (123/172/163 items where the pipeline is right and the direct path wrong) and flagged a router as a possible next step. The pre-committed rule was to measure the oracle router bound first. It came out at **+0.00 to +0.50 pts** over A2 alone — the propagation pipeline had absorbed the complementarity. No router was built.

**Lesson.** A routing mechanism can only capture the gap between the best single expert and the best possible per-item choice. Measure that bound before designing the router: in this project it saved an entire engineering branch, and it shows that "complementarity exists" is not the same as "complementarity is exploitable after improving the experts."

## 15. What we would do differently

1. Design text compactness and depth coverage from the start (V1 lost 23 % of the depth test to the 512-token limit).
2. Fix the representation-fairness rule before the first pipeline/direct comparison (it inverted a conclusion).
3. Make the model comparison 2×2 ({direct,recurrent} × {final CE, state supervision}) part of the main plan, not an addendum.
4. Treat selection-metric and evaluation-environment choices as protocol items from day one (the dev/CPU/GPU ≈ 6-pt variance would have been measured earlier).
5. Build the deterministic parser control earlier: it proved the information was extractable (coverage 1.0) and localised the deficit to learned extraction + interface, for a few minutes of work.
