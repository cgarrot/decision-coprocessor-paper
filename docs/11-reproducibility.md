# 11 — Reproducibility: artefacts, hashes, procedures

## 1. Source repositories

| Repo | Commits | Status | Contents |
|---|---:|---|---|
| `decision-coprocessor/` | 20 | closed | V1 code, data generators, 53,500-example corpus, runs, 66 prediction files, final report, bundle |
| `decision-coprocessor-v2/` | 124 | **closed and attestable** (V2, V2.1, V2.2, C0/C1/C2, V2.3/P2/E2-bis) | executor, extractor, propagation, data pools, gates, reports, registry, bundles, all run archives |

Both are local Git repositories (no remote at snapshot). This compendium is the public-facing entry point; core code is snapshotted under [`reference/`](../reference/) with provenance.

## 2. Pinned environment

| Item | Value |
|---|---|
| OS | Debian GNU/Linux 13 (trixie), kernel 6.12 |
| CPU / RAM | i7-11800H / 29.34 GiB |
| GPU | RTX 3070 Laptop 8 GiB, driver 595.91, CUDA 12.8 |
| Python | 3.11 (uv), torch 2.11.0+cu128, bf16 verified by real GPU matmuls |
| Backbone | `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca` (596,049,920 params, Apache-2.0) |
| Tokenizer | Qwen2TokenizerFast, vocab 151,643 |

## 3. Frozen artefacts

### V1 bundle (`decision-coprocessor/artifacts/bundle_final/`)
Contains B2 + R4 (seed 17), gate G4, pre-registration v2.1, configs, manifests with sha256. Reload in a fresh process: **max_abs_diff = 0.0, argmax 100 %** (B2 and R4). Dataset manifest: 11 sha256-pinned files. Exclusions: `artifacts/test_exclusions.json` (id by id).

### V2 bundle (`decision-coprocessor-v2/artifacts/bundle_final_v2/`)
```
executor_s_e4b_pad20.pt     # stage S executor (92,802 params)
reader_lora_best.pt         # E5v3-A reader, best@1200
direct_lora_best.pt         # E5v3-A direct, best@1000
configs/…                   # hashed pre-registrations
criteria/E0_E2_…, E5_…      # frozen gate criteria (v1.0→v1.9)
metrics/…                   # authoritative re-evaluated metrics
bundle_manifest.json        # 14/14 hashes conform (QA)
```
Fresh-process reload verified **8/8 + 8/8 PASS** (both adapter paths, QA-validated).

### V2.2 archives (`decision-coprocessor-v2/runs/`)
```
v22_a1/      A1 FAIL predictions (aggregate regenerated bit-identically on GPU)
v22_a1bis/   zero-training propagation metrics + verdict
v22_a2/      A2 checkpoint (best.pt), metrics.json, train_log.txt (selection per step)
v22_a2_eval/ 8×pred_prop + a2_eval_metrics.json + a2_eval_verdict.json
v22_a2_probs/ probabilistic capture (NLL/Brier), prediction identity assertions 400/400×8
v22_a3/      A3 checkpoint, metrics.json, train_log.txt (selection best@800)
v22_a3_eval/ 8×pred_a3 + a3_eval_verdict.json
v22_couts/   end-to-end cost harness outputs (couts_metrics.json, COUT_TABLE.md)
```
Pre-registrations: `V22_PROTOCOL.md` (6fc9d7d4), A2 amendment (2334c67b), A1-bis spec (d9337317), A3 spec (2f58f02b), C2 protocol (6dd53719); selection benches sha `7089876d` (2213) and seeds 2214–2216 (C2). All hashes are mirrored in the registry entries.

### Confirmation-programme archives (`decision-coprocessor-v2/`)
```
runs/c1_ablation/   anti-leak JSON, sweep + decoder v2, 16 per-item probability archives,
                    complete-Brier inputs (toolchain-stamped)
runs/c2*/           six training checkpoints/logs (s18/s19 confirmation, s20/s21 blind),
runs/c2_eval/       8 evaluations with per-item predictions and margins
v22_release_manifest.json   checkpoints + sha256 + loaders + inference path (C0)
reports/{v22_scope_erratum.md, v22_public_inference_audit.md,
         c1_complements_ag3.md, c2_final.md,
         v22_confirmation_qa_review.md, v22_c2_qa_review.md}
scripts/{qa_c1_replay.py, qa_c2_review.py, qa_diff_stages.py, run_c1_complement.py}
```
The A2 public inference path (`MemoryExtractor.extract → propagation → answer`) is published in `v22_public_inference_audit.md` and the release manifest; **the S executor is not invoked**.

### V2.3 / P2 / E2-bis archives (`decision-coprocessor-v2/`)
```
V23_CANONICAL_VERDICTS.md   QA canonical verdicts, REG-74→94 (source of truth)
V23_PROPOSAL.md             V2.3 scope (frozen)
V23_P2_PROTOCOL.md          P2 pre-registration (cpu, no training)
V23_E2BIS_PROTOCOL.md       E2-bis pre-registration (mixture 25/30/45)
reports/v23_final.md        V2.3 + P2 + E2-bis consolidated report
reports/{v23_e1a_,v23_e1_l2l3_,v23_e2_,v23_e3_}qa_review.md
reports/qa_{e1a,e1_l2l3,e2,e3,e2bis}_metrics.json
predictions/{p_cell_L2-inv,p_cell_L3-lbl,p_cell_L3-adv}.json
FINAL_SYNTHESIS.md         document of record: claims + conditions, corrected formulations, open items, publication anchor
v23_adapter_flow.md        B5: 5 roles, INFERENCE vs TARGETS, ≤512 limit binding the direct prompt
v23_release_manifest.json  B4: checkpoints, loaders 224/224, predictions 83+sha, replay, environment, seals
```
Final documentary audit and fifth audit live at the workspace top level (see `reference/audits/`).

## 4. Registry and provenance

- `experiment_registry.jsonl` — append-only: `id`, stage, config sha256, start/finish, status (`registered` / `running` / `pass` / `fail` / `blocked` / annotations), 160+ entries.
- `registry/costs.jsonl` — measured seconds, examples seen, updates, FLOPs estimates.
- `research_register.md` — 86 entries REG-01…REG-86 observations/hypotheses/tests, never rewritten, always appended.
- `reports/` — every gate has a report and a QA review; reports state denominators, thresholds and verdicts. V2.2 closure: `v22_final.md` + `v22_final_qa_review.md` (nine QA requirements, four formulation micro-corrections M1–M4 applied, cost section validated as the last gate, REG-81).
- `predictions/` — per-item predictions with raw logits where required, so QA can recompute every metric.

## 5. Reproduce one experiment

```bash
# V2 repository layout
cd decision-coprocessor-v2
uv sync                       # pinned deps (CPU stage S; cu128 for stage T)
uv run pytest -q              # contract tests (metrics, masks, gradients, data invariants)

# Example: stage-S executor gate on frozen data
uv run python scripts/run_e3.py --config configs/e3bis.yaml

# Example: V2.1 evaluation harness self-test (must pass before any run)
uv run python scripts/run_v21_eval.py --selftest

# GPU jobs always under the single-job lock
scripts/with_gpu_lock.sh <command>
```

Ground rules: scripts committed **before** use; config hashed and registered **before** start; data hash gate; one GPU job at a time; no notebooks; sealed sets never touched.

## 6. Reproducibility guarantees and caveats

**Guaranteed:**
- deterministic seeds and pinned revisions; corpus hashes; checkpoint hashes;
- eval harness self-tests (sizes, batch invariance, order invariance, duplicate ids);
- per-item archives allowing full metric recomputation;
- bundle reload in a fresh process.

**Caveats (published):**
- **environment-bound numbers**: CPU vs GPU can differ by ≈ 6 pts on dev because of near-tie successor logits; published V2.1/V2.2 figures are labelled GPU/bf16/batch 8; a stable `eps = 1e-3` tie-break was introduced in V2.2 (not retroactive);
- **sealed sets are absent by design**: `E5_eval` (1007) and `E5v2_eval` (1107) were never generated/archived; no reproduction can open them (this is a feature);
- **adaptive campaigns**: V2-T and V2.1 used dev/selection data for checkpoint choices; reproducing the exact best checkpoints requires the same data and selection code, which is versioned;
- **thermal/laptop**: V1 latency figures come from a warm second pass on a laptop; they are not transposable to server hardware;
- **V2.3 / P2 / E2-bis archives** and the **canonical verdicts** (`V23_CANONICAL_VERDICTS.md`) are the authoritative status for the final programme; the canonical document replaces historical formulations, and the final documentary audit lists the remaining traceability residuals.

## 7. What a reviewer can verify in under an hour

1. `reports/final.md` (V1) and QA recomputation paths → V1 negative.
2. `reports/final_v2.md` + `reports/e5v3a_dev.md` + QA addendum v1.9 → stage T verdict and fairness reversal.
3. `reports/v21_results.md` + `qa_v21_q1_metrics.json` → depth reversal table.
4. `reports/v22_a1_qa_review.md` addendum D → A1-bis PASS with zero training.
5. `reports/v22_a1_qa_review.md` + `v22_a2_qa_review.md`, `v22_a3_qa_review.md`, `v22_final.md`, `v22_final_qa_review.md` → A2 PASS, architectural superiority of propagation 8/8, router bound, costs, closure.
6. `reports/v22_scope_erratum.md`, `v22_public_inference_audit.md`, `c1_complements_ag3.md`, `c2_final.md`, `v22_confirmation_qa_review.md`, `v22_c2_qa_review.md` → audit #3 corrections, same-reader attribution, three-seed confirmation, blind extrapolation, all reserves closed.
7. `experiment_registry.jsonl` + `research_register.md` (REG-01…REG-86) → chronology and pre-registration order (hashes, dates, commit ids).
8. `figures/make_figures.py` (this repo) → every plot in the paper regenerated from the numbers published here.

A “where to check each claim” mapping exists in the original compaction dossiers (files 05 and 11 of the V2 review corpus).
