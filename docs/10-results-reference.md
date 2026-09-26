# 10 — Results reference: every published number and its source

*This is the audit table: each figure below recalculated by QA (or explicitly labelled as executor-reported) and traceable to a versioned artefact. “Env.” = environment-bound (GPU RTX 3070 Laptop, bf16).*

## V1 — reserved test (macro A/B/C, mean of 3 seeds)

Sources: `decision-coprocessor/reports/final.md`, `runs/p6/*.jsonl`, `artifacts/test_exclusions.json`.

| Quantity | Value | Source |
|---|---|---|
| B2 IID / depth / composition | 0.4884 / 0.3418 / 0.4081 | final.md, recalculated |
| R4 IID / depth / composition | 0.4908 / 0.3359 / 0.4073 | final.md, recalculated |
| Δ(R4−B2) depth | **−0.59 pt [−1.25; +0.07]** | final.md |
| Δ(R4−B2) IID / comp. | +0.24 [−0.33; +0.74] / −0.08 [−0.64; +0.44] | final.md |
| Δ(B3−B2) depth | −0.75 [−1.40; −0.08] (significant) | final.md |
| Δ(B4−B2) depth | −0.36 [−1.02; +0.32] | final.md |
| Δ(R4−R1) depth | −0.02 [−0.20; +0.15] (saturation k=1) | final.md |
| R4−B3 / R4−B4 depth | +0.16 [−0.17; +0.48] / −0.23 [−0.63; +0.16] | final.md |
| Corrections/degradations depth (R4) | 181 / 238 (net −57) | final.md |
| Family breakdown (A/B/C) | 6/39 · 139/148 · 36/51 | final.md |
| Accuracy by depth (B2 d6/8/10) | 0.3411 / 0.3945 / 0.3072 | final.md |
| Accuracy by depth (R4) | 0.3358 / 0.3857 / 0.3025 | final.md |
| NLL B2 depth / R4 depth | 1.3511 / 1.3540 | final.md |
| ECE B2 depth | 0.1254 | final.md |
| Gate G4 depth (s17) | 0.3420 vs B2 0.3418; activations 47.9/53.1/56.7 % | final.md, p5_gate.md |
| Latency B2 / R4 (L512, batch 1) | 46.18 ms (p95 46.86) / 50.04 ms (p95 50.71) | runs/p6/latency/latency.json |
| Sidecar module R1/R2/R4 | 0.99 / 1.55 / 2.68 ms | final.md |
| VRAM B2/R4 reserved | 1.199 GiB (1228 MiB) | final.md |
| Coverage `test_depth` | retained 3080/4000 (920 excluded >512 tok) | test_exclusions.json |
| Trainable params B2/B3/B4/R/G4 | 1,054,209 / 2,178,177 / 5,270,785 / 2,110,465 / 35,116 | final.md |
| Backbone | 596,049,920, frozen | environment.json |
| Memory-branch Δlogits | ≤ 0.004 (s43); 0 argmax flips /500 masking-shuffle | p4_diagnostics*.md |
| Per-instance permutation instability | ≈ 39 % (B2/R4/B3), 70 % (B1) | p4b_permutation_audit.md |

## V2 stage S — transition executor (CPU, 92,802 params, α = 0.5, budget 16)

Sources: `reports/{e1,e2,e3,e4,e4b}.md`, QA reviews, `predictions/*`.

| Gate | Value | Cost |
|---|---|---|
| E1 autonomous trajectory | **1.000** (128/128), final 1.000, loss 2.2696→7.84e-05 | 452 s, 700 updates, 22,400 ex. |
| E2 zero-shot next-state (exact input states) | **919/919 = 1.000**; depth 4 unseen 1.000; base 767/767, decisive 152/152 | 1.32 s |
| E2 secondary anomaly: autonomous readout | 0.725 overall; answer index >9 → 25.3 % (n=87) | — |
| E3 trajectory / conditional transition | **1.000** (255/255) / **1.000** | 132.96 s, 800 steps |
| E3 answer by depth d1..d4 | 1.000 everywhere | — |
| E3 executor vs direct (final) | 1.000 vs 0.204; 203 corrections, 0 degradations | — |
| E3 k-sweep final answer | 0.188 / 0.271 / 0.522 / **1.000** / 1.000 / 1.000 at k = 0/1/2/4/8/16 | — |
| E4/E4b zero-shot (all depths 1–16) | **399/399 = 1.000** trajectory + final; 0 state divergences | 174.12 s train + 2.32 s eval |
| E4b k-sweep | 0.286 (k0) → 0.584 (k6) → 0.759 (k8) → 0.960 (k10) → **1.000 (k16)** | — |
| pad16 vs pad20 common range | 1.000 vs 1.000 (exact parity) | — |

## V2 stage T — text

Sources: `reports/e5*.md`, `final_v2.md`, `E5_GATE_CRITERIA.md` (v1.0→v1.9), QA addenda.

| Quantity | Value |
|---|---|
| E5 v1 bench status | **defective, archived**; direct 0.7775 was a template lever; probe at chance |
| E5v2 lexical probe | dev 0.2179–0.2429 vs chance 0.2205 → NEAR_CHANCE |
| Direct on sound bench (frozen) | 0.326 (E5v2 dev) |
| Reader it1 / it2 / it3 gates | 1/4 · 3/4 · 3/4 (solve 0.0625 → 0.2044 → 0.2482) |
| Reader it3 edges | 0.7252 harness / 0.7043 QA definition (FIN difference; QA reproduces 0.7252 with FIN) |
| it3 cells (a/b/c/cn/d) | 1.000 / 0.2482 / 0.2482 / 0.3382 / 0.2871 |
| it3 Δ(cn−d) | +5.11 [−1.72; +11.74] grey zone → mechanism failed → issue (iii) |
| E5v3-A reader gates | entities 1.000 · **edge 0.9278** · start 1.000 · **solve 0.7616** (4/4); validity 0.917, abstention 0.083 |
| E5v3-A edge trajectory | 0.331@100 → 0.812@400 → 0.919@700 → 0.928@1200 |
| E5v3-A direct trajectory | 0.552@100 → 0.973@200 → 0.998@600 → **1.000@1000** → 0.998@1200 |
| E5v3-A cells (a/b/c/cn/d) | 1.000 / 0.7616 / 0.7616 / 0.8200 / **1.0000** |
| **Δ(c−d)** | **−23.84 pts [−28.33; −19.60]** → issue (iii) |
| Causal profile (c) | 0.780 / 0.588 / 0.932 (decisive/distractor/permutation) |
| Causal profile (d) | **0.996 / 0.996 / 0.988** |
| Broken chain | det 0/411 (structural limitation) |
| V2 total compute | **4.96 h** registered; VRAM peak ≈ 2.1 GiB |
| Bundle final V2 | reload 8/8 + 8/8, 14/14 hashes conform (QA) |

## V2.1 — frozen checkpoints, 8 sealed benches (n = 400, env.)

Sources: `reports/v21_results.md`, `reports/qa_v21_q1_metrics.json`, `runs/v21_eval/`.

| Bench | (a) | (b) | (c) | (cn) | (d) | Δ(c−d) |
|---|---:|---:|---:|---:|---:|---:|
| B1-court | 1.000 | 0.800 | 0.800 | 0.853 | 0.9375 | −13.75 |
| B5-surface | 1.000 | 0.810 | 0.810 | 0.868 | 0.9400 | −13.00 |
| B6-distract | 1.000 | 0.772 | 0.772 | 0.848 | 0.9375 | −16.50 |
| B7-options | 1.000 | 0.800 | 0.800 | 0.853 | 0.9400 | −14.00 |
| B8-depart | 1.000 | 0.765 | 0.765 | 0.820 | 0.8400 | −7.50 |
| B2-prof6 | 1.000 | 0.667 | 0.667 | 0.693 | 0.5250 | **+14.25** |
| B3-prof8 | 1.000 | 0.598 | 0.598 | 0.618 | 0.2800 | **+31.75** |
| B4-prof10 | 1.000 | 0.560 | 0.560 | 0.593 | 0.3075 | **+25.25** |
| Depth curves | direct 1.00/0.97/0.91/0.87 then 0.53/0.28/0.31 | pipeline 0.92/0.81/0.76/0.71 then 0.67/0.60/0.56 | crossing 4→6 |
| Path-only oracle corrector | 0.950 / 0.965 / 0.9825 / 0.9825 (B1→B4) | vs baseline 0.800/0.667/0.598/0.560 |
| Active successor / END | ~0.89 / 98.7–99 % | |
| Direct NLL B1→B4 | 0.59 / 5.43 / 8.85 / 7.45 nats | |
| ECE B1 (direct) | 0.061 | |
| Complementarity | 123 / 172 / 163 of 400 (depths 6/8/10) | |
| Parser (p) | coverage 1.0000, agreement 1.0000, 3200/3200 (control, diagnostic) | |
| GPU batch1 vs batch8 (B1) | b/c 0.805/0.800 · cn 0.8575/0.8525 · d 0.935/0.9375 | ≤ 0.5 pt |
| CPU↔GPU variance (dev) | ≈ 6 pts (b 0.82 CPU vs 0.7616 GPU) | env.-bound labels |

## V2.2 — interface ablations (closed)

Sources: `reports/v22_a1_qa_review.md`, `v22_a2_qa_review.md`, `v22_a3_qa_review.md`, `v22_final.md`, `v22_final_qa_review.md`, specs `V22_A1BIS_SPEC.md` / `V22_A3_SPEC.md`, `runs/v22_*`. All numbers QA-recalculated.

| Quantity | Value |
|---|---|
| A1 (bilinear head) c_prop by bench | 0.3225 / 0.2125 / 0.2150 / 0.1850 / 0.2775 / 0.2375 / 0.2650 / 0.2575 |
| A1 Δ vs discret on B3 | **−38.25 pts [−44.75; −31.75]** FAIL (unsupervised head, top-1 0.054) |
| A1-bis c_prop | **0.8325–0.8575, invariant in depth**; Δ vs discret +4.25…+29.50, IC>0 8/8; zero training |
| **A2 c_prop** | **0.9950 / 0.9975 / 0.9975 / 0.9975 / 1.0000\* / 1.0000\* / 0.9950 / 0.9975** (B1→B8) |
| A2 Δ vs discret [QA CI] | +19.50 / +33.00 / **+40.00** / +43.75 / +19.00 / +22.75 / +19.50 / +23.25, all IC low > 0 |
| A2 Δ vs direct V2.1 [QA CI] | **+5.75** [+3.25,+8.25] / +47.25 / **+71.75** [+67.00,+76.25] / +69.00 / +6.00 / +6.25 / +5.50 / +15.75, **8/8 IC>0** |
| A2 probabilistic quality | NLL 0.0044–0.0294; `gold_class_squared_error` = mean((1−p_gold)²) 0.0007–0.0061. **Erratum (C0):** the direct path's NLL (0.59→8.85) means degraded probabilistic quality — *not* demonstrated error awareness |
| A2 selection | bench 2213, best = step 1200 (c_prop 1.0, discret 0.7975); training 4054.64 s |
| **A3 (direct + equal aux.)** | 0.9625 / 0.4925 / 0.2475 / 0.2825 / 0.9575 / 0.9450 / 0.9600 / 0.8550 |
| **Δ(A2−A3)** | **+3.25 / +50.50 / +75.00 / +71.50 / +4.25 / +5.50 / +3.50 / +14.25**, CI low > 0 on 8/8 → **architectural superiority of propagation** |
| A3 vs direct V2.1 | only B1 significant (+2.50 [0.25,4.75]); depth −2.50/−3.25/−3.25 with IC ∋ 0 → auxiliary supervision alone does not repair depth |
| Router oracle bound | A2∪A3 = 0.9975–1.0000 → **+0.00 to +0.50 pts** over A2 alone; A3-only 0–2 items/bench → no router built for accuracy |
| Costs (batch 8) | B1 p50 A2 40.32 ms vs A3 32.65 (×1.235); B3 51.59 vs 40.52 (×1.273); throughput ×0.78–0.79; **propagation 0.59–0.66 ms ≈ 1.3–1.5 % of A2 p50 (“low in this profile”, not “free”)**; VRAM 1472–1512 MiB parity |
| **Parser + exact solver (templates)** | **1.0000 on 8/8 benches (3200/3200)** — bounded symbolic upper bound; A2 joins, does not exceed it. The earlier “parser ceiling 0.95” was a framing error (path-only diagnostics 0.95–0.98, C0 erratum) |
| Declared saturation | B5/B6 = 1.000 (benches no longer separate systems above 0.995) |
| QA closure | REG-76→81, all V2.2 gates closed (protocol, A1, A1-bis, A2, A3, router bound, report, costs) |

## Confirmation programme C0/C1/C2 (closed 2026-09-26)

Sources: `reports/{v22_scope_erratum.md,v22_public_inference_audit.md,c1_complements_ag3.md,c2_final.md,v22_confirmation_qa_review.md,v22_c2_qa_review.md}`, `V22_C2_PROTOCOL.md`, `runs/c1_ablation/`, `runs/c2_eval/`. All QA-recalculated (REG-82→86).

| Quantity | Value |
|---|---|
| A2 public inference path | `MemoryExtractor.extract → fact_logits → transition_matrix_from_facts → start_distribution → propagate(T=20) → answer_index` — **the S executor is NOT invoked in A2** (verified by code) |
| Anti-leak (3 layers) | structural 3200/3200 inputs identical under private randomisation; public-only 64/64; behavioural 64/64 ×2 |
| **C1 — same-reader 2×2** | R0 (E5v3-A) hard 0.55–0.82 / soft 0.83–0.86 · R1 (A2) hard 0.785–0.875 / soft **0.995–1.000** → **both factors contribute** (soft > hard at fixed reader: +14…+22 pts for R1; R1 > R0 in hard) |
| Identities | R0-soft ≡ A1-bis (400/400 ×8); R1-soft ≡ A2 (400/400 ×8) |
| Budget sweep 0–20 | R0 converges ≈ depth+1 then **decays** (B5 0.910@4 → 0.853@20; INCONNU leak); R1 converges earlier and **plateaus 0.998–1.0** |
| Complete multiclass Brier (candidates ∪ {AUTRE}) | R1 **0.0016–0.0119** vs R0 **0.2998–0.5826** (R0 INCONNU mass ≈0.20 at depth 8 = the measured leak) |
| Toolchain divergence | torch 2.6.0+cu124 = published (0/3200 flips ×2); torch 2.14 diverges 18/3200 — first divergent stage = **backbone forward** |
| CPU/GPU localisation | first divergent stage = backbone h14 (16/16 items), relative drift ≈0.49 % (bf16); decisions stable 0/16 on the sample |
| Tie-break semantics | real ties and near-ties ≤ eps = 1e-3 → alphabetical key; renaming = equivariance, not invariance |
| **C2-a (3 seeds)** | Δ(A2−A3) pooled deep: s17 **+65.30** [+62.6,+68.1] · s18 **+64.05** [+61.3,+66.8] · s19 **+68.14** [+65.6,+70.9] · **mean +65.83**, CI low > 0 all; A2 dispersion 0.9950/0.9983/0.9983 (≤0.33 pt); A3 pooled deep 0.342/0.358/0.317; A2 short mean 0.9992 |
| **C2-b (blind extrapolation)** | A2 s20-blind pooled deep **0.9867** (short 0.9950 · prof6 0.9825 · prof8 0.9950 · prof10 0.9825) vs A3 s21-blind **0.2710**; criterion ≥0.90 → **largely successful** |
| C2 incident | 1/2000 item: reader rendering 484 tokens vs direct-prompt rendering 518 (>512) — generator measured a different rendering than the consumer; excluded identically for all paths, evals replayed on the common population |
| C2 margins top-2 | A2 medians 0.9963/0.9955/0.9914 (s17/s18/s19), 0.9882 blind; A3 all-cells 0.9631; A2 deep-only ≤1e-2 on 0.08–1.50 % |
| C2 cost | 6 trainings ≈70 min each + 8 evals ≈40 s ≈ **7 h GPU** under the single-job lock |
| QA closure | REG-82→86; C2-a PASS + C2-b largely successful validated; reserves R-C2-0/1/2 closed (exact incident cause, top-2 margins archived, “pooled” convention named) |

## Cost ledger

| Phase | Registered compute |
|---|---|
| V1 all phases (P0–P7) | several GPU hours across a ~12 h execution window; exact per-run numbers in `decision-coprocessor/runs` |
| V2 stage S (CPU) | E1 452 s · E3 133 s · E4b 174 s + 2.3 s (plus failed attempts) |
| V2 stage T | V2 total 4.96 h GPU, including E5v3-A ≈ 2.5 h (reader 74 min, direct 46 min, evals ≈ 25 min) |
| V2.2 | A2 training 4054.64 s (≈68 min); A3 run under lock; end-to-end cost harness 137.9 s; propagation alone 0.59–0.66 ms/item measured |
| C0/C1/C2 confirmation | C1 no training (frozen outputs); C2 night: 6 trainings ≈70 min each + 8 evals ≈40 s ≈ **7 h GPU** under the single-job lock |
| VRAM peak | V2 ≈ 2.1 GiB; V2.2 batch 8: 1472–1512 MiB allocated (parity A2/A3); V1 1.199 GiB reserved |
| Hardware | RTX 3070 Laptop 8 GiB, i7-11800H, 29.34 GiB RAM |

No experiment in the project ever required more than ~2 GB of the 8 GB available, and no paid API was used.
