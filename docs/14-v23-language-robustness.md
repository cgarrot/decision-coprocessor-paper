# 14 — V2.3: language robustness, failure diagnosis, and the depth-generalisation repair

*Programme V2.3 + diagnostic P2 + E2-bis, 2026-09-26 ≈11:30 → 2026-09-27 06:12. Canonical verdict source: [`V23_CANONICAL_VERDICTS.md`](../reference/v2/protocols/V23_CANONICAL_VERDICTS.md) (QA, REG-74→94). Final documentary audit: “CLOS AVEC RÉSIDUS” — see §5.*

## 1. Question and design (V2.3)

**Question:** at constant graph and answer, how well does A2 understand *new formulations*? The scope was frozen (V2.3 proposal + review amendments): separate roles (`P_eval`, `V_sem`, `Renderer`, `PublicAdapter`), no circular round-trip, separate linguistic levels, a distinct adversarial lot, a separate GO for E2, and three separate evaluation questions. Coreference, negation and multi-relation units were explicitly deferred — not forgotten.

| Level | Content | Parser coverage |
|---|---|---|
| **L1-a** | paraphrases (surface variation, same semantics) | 1.00 / 1.00 |
| **L2-inv** | inverted syntax (“Y leads to X” instead of “X leads to Y”) | canonical 1.00 / **variant 0.00** by construction |
| **L3-lbl** | entity renaming / label bijection | 0.99 / 0.99 |
| **L3-adv** | adversarial lot (separate usage tag, outside the primary score) | 1.00 / 1.00 |

## 2. V2.3 results

### E1 — frozen weights, 4 matched cells (48 evaluations, QA REG-87/89)

| Cell | A2 variant (3 seeds) | A3 | Verdict |
|---|---|---|---|
| L1-a paraphrases | **1.000 / 1.000 / 1.000** | 0.951 | **PASS total** (Q2 −0.25 pt ns) |
| **L2-inv inversions** | **0.545 ×3** | **0.72** | **A2 breaks** (Q1 < 0.70; Q2 −45 pts; **A2 < A3** — the template-regime reversal flips) |
| L3-lbl prefixes | Δ ≈ 0 (0 / −1.5 / 0 pts) | ~0.93 | lexical cost null-to-marginal |
| L3-adv (separate) | 0.998–1.000 | 0.94 | holds |

### E2 — retraining on a frozen 25/30/45 mixture (GO user; QA REG-91)

- **L2-inv 0.545 → 0.9375 / 0.94** (2 seeds; gate ≥ 0.70 passed).
- **No significant regression:** L1-a −0.1/−0.5 pt; L3-lbl −1/−2 pts (published); L3-adv +0.2/+0.3 pt.
- **A2-E2 > A3-E2 on 16/16 cells×pairs** — the E1 reversal is inverted.
- Conclusion: the mixture was enough to learn the inverted orientation; E1's failure was **not a structural limit of the interface**.

### E3 — language × depth (96 evaluations, fresh benches, matched triples; QA REG-92, P0-restored)

| Path | Rendering | short | prof6 | prof8 | prof10 |
|---|---|---|---|---|---|
| A2-E1 (3 seeds) | canonical | 0.993–1.000 | 1.000 | 0.997–1.000 | 0.997–1.000 |
| A2-E1 | L1 paraphrase | 1.000 | 1.000 | 0.997–1.000 | 0.993–1.000 |
| A2-E1 | L2-inv | 0.57–0.59 | 0.25–0.28 | 0.23–0.25 | 0.26–0.27 |
| **A2-E2 (s22/s24)** | **L2-inv** | **0.957 / 0.927** | **0.847 / 0.823** | **0.797 / 0.753** | **0.797 / 0.680** |
| A3-E2 (s23/s25) | L2-inv | 0.860 / 0.863 | 0.400 / 0.370 | 0.287 / 0.277 | 0.303 / 0.297 |
| A3 (all eras) | all | 0.72–0.94 | 0.20–0.50 | 0.23–0.40 | 0.28–0.35 |

**Central E3 result — the interaction is real and asymmetric:**
- canonical and paraphrases: **very high robustness in the measured conditions** (0.99–1.00), reconfirmed on fresh benches (3 seeds);
- inversions: the robustness gained by E2 **extrapolates only partially** with depth (0.93 short → 0.68 at depth 10) — the mixture contained inversions only at depths 1–4;
- A3 (direct) stays collapsed in depth in **all** conditions.

## 3. P2 — decisive diagnosis (pre-registered, no training; QA REG-93)

Three falsifiable hypotheses: **H-A** composition of local errors · **H-B** long-context effect · **H-C** mass loss. Measurements: `p(edge, inversion)` by depth/tercile, `p_T` masses, trajectories, controlled variations V1/V2/V4, oracle surgery O1/O2/O3.

| Hypothesis | Status |
|---|---|
| **H-B** (context) | **not supported** (position terciles; V4 not executed — declared gap, weaker rejection than first announced) |
| **H-C** (top-1 < 0.99) | **rejected** (top-1 0.82–0.85) — does not refute all mass loss |
| **H-A** (error composition) | **partially supported**: `p(edge|inv)` is **constant with depth** (s22 0.845–0.854 · s24 0.819–0.839, below the predicted 0.93–0.96 range), and the mass-leak mechanism is established by the masses: **terminal 0.51→0.27, UNKNOWN 0.38→0.57** (s22; 0.42→0.20 / 0.47→0.64 s24). The fit criterion |acc − p^depth| ≤ 3 pts is violated, O1 failed (alignment, 0.007–0.017), so the complete H-A-vs-alternatives attribution is not clean. |

**Authorised formulation (final audit):** *the measurements are compatible with a composition of relational errors and an accumulation of UNKNOWN mass; attribution remains partial, some planned controls not executed or unavailable.* The “data ceiling exists” claim is **not established** — the 0.38–0.41 residue is an observation, not proof.

## 4. E2-bis — the coverage experiment (QA REG-94)

Protocol frozen before generation (`V23_E2BIS_PROTOCOL.md`, sha `4f0677af…`): mixture 25/30/45 (inversion share 25 % → 45 %), prefixed thresholds (inv×p10 ≥ 0.85; UNKNOWN ≤ 0.25; non-regression ±2 pts), **claim = coverage**, short-only selection.

| Path | short | p6 | p8 | **p10** |
|---|---:|---:|---:|---:|
| **A2-E2bis s26 (inv)** | **0.980** | **0.973** | **0.953** | **0.930** |
| **A2-E2bis s28 (inv)** | **0.977** | **0.940** | **0.937** | **0.900** |
| A2-E2bis (can / L1) | 0.993 / 1.000 | 0.997 / 0.997 | 1.000 / 1.000 | 0.993 / 0.990 |
| A3-E2bis s27/s29 (inv) | 0.85 / 0.83 | 0.42 / 0.30 | 0.26 / 0.24 | 0.28 / 0.29 |

**Multi-criteria verdict (hierarchy explicit, audit B2):**

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| accuracy inv×p10 (primary) | ≥ 0.85 | 0.930 / 0.900 | **PASS** |
| deep UNKNOWN mass (mechanistic) | ≤ 0.25 | 0.38–0.41 | **FAILED** (reduced from 0.57, not eliminated) |
| non-regression (guard) | ±2 pts | all cells | **PASS** |
| Δ(A2−A3) (fairness) | CI low > 0 | confirmed | **PASS** |

**Requalification by the final audit (B1):** because the mixture and the selection bench contain **only depths 1–4** (data-proven), E2-bis is a genuine **blind extrapolation** — stronger than the initial “coverage” qualification. But the mechanistic objective is **failed, not requalified**: the residual UNKNOWN mass (0.38–0.41) means the accuracy holds *through the argmax* despite a leaking distribution.

**What this changes:** the V2.3 frontier (0.93 short → 0.68 at depth 10) is **pushable with data** (+25 % → 45 % inversions, ×1.8, suffices to cover inv×depth-10 at 0.90–0.93). The residual leak suggests an interface that better conserves mass (e.g. the can↔inv coherence constraint) could push further — **recorded for V2.4 arbitration, not executed**.

## 5. Final documentary audit: “CLOS AVEC RÉSIDUS”

A sixth inspection (`AUDIT-CLOTURE-FINALE-DECISION-COPROCESSOR.md`, 2026-09-27 06:09) validated the experimental state and the canonical verdicts, and identified **five blocking documentary residuals** (none requiring a new experiment):

| ID | Residual | Resolution path |
|---|---|---|
| B1 | E2-bis domain contradiction (“in-domain” vs 1–4) | corrected by the data-proven requalification: **blind extrapolation** (this doc §4) |
| B2 | Multi-criteria verdict incomplete (failed threshold hierarchy) | explicit hierarchy table (§4) |
| B3 | P2 QA reserves not propagated into summaries | authorised partial-attribution formulation (§3) |
| B4 | Release/inventory not settled (unfrozen files, manifest, 83 vs 76 dirs, early closures not recertifiable) | designate the final archive, classify evaluations, attach closure pieces |
| B5 | Parser/adapter flow not consolidated (public inputs and semantic roles) | publish the existing schema or document the executed path — no leak claimed |

Minor residuals: mass definitions (populations/normalisation to be stated), anti-overwrite scope (previous-version preservation and atomic publication), chronology/convention housekeeping; cosmetic: “doubling” = ×1.8. **None changes a number.**

**Established in one sentence (audit wording):** *in a synthetic French relation-tracking domain, an adapted reader coupled with explicit distribution propagation outperformed the compared direct models, with confirmation and depth generalisation in the documented conditions, then reached 90–93 % on inversions at depth 10 after E2-bis — without eliminating the residual UNKNOWN mass or establishing general reasoning ability or product validation.*

## 6. What remains open (V2.4 arbitration)

1. **Residual leak:** improve top-1, the full distribution, or the UNKNOWN mass — which objective, which trade-off?
2. **UNKNOWN semantics:** distinguish declared terminal / missing fact / reading uncertainty / exhausted compute budget — currently grouped.
3. **can↔inv coherence:** which relational invariant to impose between equivalent formulations while remaining sensitive to genuine inversions.
4. Lot C3 items from before (new renderings, multi-question contexts, larger graphs) remain listed but unstarted.

No further training is running. All V2.3/P2/E2-bis thresholds were prefixed, all incidents documented, and the canonical verdicts (`V23_CANONICAL_VERDICTS.md`, REG-74→94) are the single document that makes faith, replacing historical formulations.
