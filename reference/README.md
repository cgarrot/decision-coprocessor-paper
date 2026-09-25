# Reference snapshots

Read-only copies of the core model code, frozen configs, gate protocols and key reports, taken on **2026-09-25** from the two source repositories. They exist so this compendium is self-contained and auditable; the source repositories (with runs, per-item predictions and full history) remain authoritative.

Every file's sha256 is recorded in [`PROVENANCE.json`](PROVENANCE.json).

## Layout

```text
reference/
├── v1/
│   ├── model/       sidecar.py · heads.py · backbone.py · controls.py
│   ├── configs/     fast_head.yaml · sidecar_main.yaml · controls_main.yaml · gate.yaml
│   └── reports/     final.md (V1 final report) · preregistration.md
└── v2/
    ├── model/       executor.py · extractor.py · propagation.py · relation_data.py ·
    │                extraction_data.py · train.py · solver.py
    ├── data/        bfamily.py · textfamily.py · pools.py · v21benches.py · det_parser.py
    ├── configs/     e1.yaml · e3bis.yaml · e4b_train.yaml · e5v2_reader_it3.yaml ·
    │                e5v3a_lora_reader.yaml · e5v3a_lora_direct.yaml ·
    │                v22_a2.yaml · v22_a3.yaml
    ├── protocols/   data_contract.md · V2*_PROTOCOL.md · V22_A1BIS_SPEC.md ·
    │                V22_A3_SPEC.md · V22_A2_ADDENDUM.md · MODEL_NOTES.md ·
    │                research_register.md (REG-01…REG-81)
    └── reports/     final_v2.md · v21_results.md · v22_a{1,2,3}_qa_review.md ·
                     v22_final.md · v22_final_qa_review.md · v22_couts_COUT_TABLE.md
```

Some source documents are in French (the project working language); this compendium's paper and documentation are in English and summarise them with exact numbers.

## What is deliberately *not* here

- Datasets and pools (`data/*.jsonl`) — large, hash-pinned in the source repositories' manifests; the small compendium documents their contracts instead.
- Checkpoints and bundles (`*.pt`, `*.safetensors`) — binary artefacts with sha256 manifests in the source bundles.
- Raw runs and per-item predictions — the source repositories' `runs/` and `predictions/` directories.
- Sealed evaluation pools — never generated/opened by design.

## License

Snapshot code is MIT-licensed; documentation and reports remain under the source repositories' terms (see the top-level [`LICENSE`](../LICENSE)).
