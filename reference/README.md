# Reference snapshots

Read-only copies of the core model code, frozen configs, gate protocols, key reports and the three external audits, taken on **2026-09-26** from the two source repositories. They exist so this compendium is self-contained and auditable; the source repositories (with runs, per-item predictions and full history) remain authoritative.

Every file's sha256 is recorded in [`PROVENANCE.json`](PROVENANCE.json).

## Layout

```text
reference/
├── audits/          DECISION-COPROCESSOR-AUDIT-RELANCE-V2.md (audit #1 → V2)
│                    DECISION-COPROCESSOR-AUDIT-V2-VALIDATION.md (audit #2 → V2.1)
│                    DECISION-COPROCESSOR-AUDIT-V22-CONFIRMATION.md (audit #3 → C0/C1/C2)
│                    DECISION-COPROCESSOR-REVUE-C2-AMENDEMENTS-V23.md (audit #4 → V2.3)
│                    DECISION-COPROCESSOR-AUDIT-V23-DIAGNOSTIC-V24.md (audit #5 → P2/E2-bis)
│                    AUDIT-CLOTURE-FINALE-DECISION-COPROCESSOR.md (final: closed with residuals)
├── v1/
│   ├── model/       sidecar.py · heads.py · backbone.py · controls.py
│   ├── configs/     fast_head.yaml · sidecar_main.yaml · controls_main.yaml · gate.yaml
│   └── reports/     final.md (V1 final report) · preregistration.md
└── v2/
    ├── model/       executor.py · extractor.py · propagation.py · relation_data.py ·
    │                extraction_data.py · train.py · solver.py
    ├── data/        bfamily.py · textfamily.py · pools.py · v21benches.py · det_parser.py
    ├── configs/     e1.yaml · e3bis.yaml · e4b_train.yaml · e5v2_reader_it3.yaml ·
    │                e5v3a_lora_{reader,direct}.yaml · v22_a{2,3}.yaml ·
    │                c2/c2{a,b}_a{2,3}_s{18..21}.yaml
    ├── protocols/   data_contract.md · V2*_PROTOCOL.md · V22_A{1BIS,2,3}_SPEC/ADDENDUM ·
    │                V22_C2_PROTOCOL.md · V2.3_PROPOSAL.md · V23_P2_PROTOCOL.md ·
    │                V23_E2BIS_PROTOCOL.md · MODEL_NOTES.md · research_register.md
    │                (REG-01…REG-94) · v22_release_manifest.json ·
    │                **V23_CANONICAL_VERDICTS.md (QA source of truth)**
    └── reports/     final_v2.md · v21_results.md · v22_a{1,2,3}_qa_review.md ·
                     v22_final.md · v22_final_qa_review.md · v22_couts_COUT_TABLE.md ·
                     v22_scope_erratum.md · v22_public_inference_audit.md ·
                     v22_loader_impact_matrix.md · c1_complements_ag3.md ·
                     c2_final.md · v22_confirmation_qa_review.md ·
                     v22_c2_qa_review.md · v23_final.md · v23_e{1a,1_l2l3,2,3}_qa_review.md ·
                     qa_e*_metrics.json · p_cell_v21_summary.json
```

Some source documents are in French (the project working language); this compendium's paper and documentation are in English and summarise them with exact numbers.

## What is deliberately *not* here

- Datasets and pools (`data/*.jsonl`) — large, hash-pinned in the source repositories' manifests; the small compendium documents their contracts instead.
- Checkpoints and bundles (`*.pt`, `*.safetensors`) — binary artefacts with sha256 manifests in the source bundles and the release manifest.
- Raw runs and per-item predictions — the source repositories' `runs/` and `predictions/` directories.
- Sealed evaluation pools — never generated/opened by design.

## License

Snapshot code is MIT-licensed; documentation, reports and audits remain under the source repositories' terms (see the top-level [`LICENSE`](../LICENSE)).
