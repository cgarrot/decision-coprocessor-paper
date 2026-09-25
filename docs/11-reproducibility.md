# 11 — Reproducibility: artefacts, hashes, procedures

## 1. Source repositories

| Repo | Commits | Status | Contents |
|---|---:|---|---|
| `decision-coprocessor/` | 20 | closed | V1 code, data generators, 53,500-example corpus, runs, 66 prediction files, final report, bundle |
| `decision-coprocessor-v2/` | 51 (at snapshot) | V2/V2.1 closed, V2.2 running | executor, extractor, data pools, gates, reports, registry, bundles |

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

## 4. Registry and provenance

- `experiment_registry.jsonl` — append-only: `id`, stage, config sha256, start/finish, status (`registered` / `running` / `pass` / `fail` / `blocked` / annotations), 90+ entries.
- `registry/costs.jsonl` — measured seconds, examples seen, updates, FLOPs estimates (29 lines for V2).
- `research_register.md` — REG-01…REG-75 observations/hypotheses/tests, never rewritten, always appended.
- `reports/` — every gate has a report and a QA review; reports state denominators, thresholds and verdicts.
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
- **V2.2/A2** is running at snapshot; its registry entries are the only authoritative status.

## 7. What a reviewer can verify in under an hour

1. `reports/final.md` (V1) and QA recomputation paths → V1 negative.
2. `reports/final_v2.md` + `reports/e5v3a_dev.md` + QA addendum v1.9 → stage T verdict and fairness reversal.
3. `reports/v21_results.md` + `qa_v21_q1_metrics.json` → depth reversal table.
4. `reports/v22_a1_qa_review.md` addendum D → A1-bis PASS with zero training.
5. `experiment_registry.jsonl` + `research_register.md` → chronology and pre-registration order (hashes, dates, commit ids).
6. `figures/make_figures.py` (this repo) → every plot in the paper regenerated from the numbers published here.

A “where to check each claim” mapping exists in the original compaction dossiers (files 05 and 11 of the V2 review corpus).
