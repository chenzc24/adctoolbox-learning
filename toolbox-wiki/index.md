# Toolbox Wiki Index

## Start Here

- [Progress](progress.md): current learning state and protection rules.
- [Coverage Matrix](coverage_matrix.md): topic coverage across concepts, source code, workflows, rigor, and raw source notes.
- [Open Questions](open_questions.md): unresolved mathematical, engineering, and maintenance questions.
- [Wiki Rules](schema/WIKI_RULES.md): required workflow for future LLM work.
- [Page Template](schema/PAGE_TEMPLATE.md): default format for new pages.
- [Proof Page Template](schema/PROOF_PAGE_TEMPLATE.md): default format for mathematical and rigor proof pages.
- [Example Note Template](schema/EXAMPLE_NOTE_TEMPLATE.md): default format for example evidence notes.
- [Promotion Rules](schema/PROMOTION_RULES.md): criteria for moving pages from draft to usable to stable.
- [Semantic Lint Checklist](schema/SEMANTIC_LINT_CHECKLIST.md): conceptual health check for contradictions, stale claims, and semantic islands.
- [Lint Checklist](schema/LINT_CHECKLIST.md): review checklist for completeness, source linkage, rigor, and maintenance.
- [Knowledge Base Health Audit](audits/knowledge_base_health_2026-06-03.md): current completeness, code relevance, rule maturity, and next gaps.
- [Structure Cap Audit](audits/structure_cap_2026-06-03.md): structural closure status for retrieval, maintenance, promotion, and lint workflows.
- [Raw Distillation Audit](audits/raw_distillation_2026-06-03.md): current raw-source distillation coverage and next content gaps.
- [Sun Course Source Fidelity Audit](audits/source_fidelity_sun_course_2026-06-03.md): Markdown-to-original-PDF spot-check status for Sun-course source notes.
- [Operation Log](logs/log.md): chronological record of changes.
- [Wiki Content Index](wiki/index.md): catalog of generated wiki pages.
- [Stage Map](curriculum_bridge/stage_map.md): how current staged learning maps to wiki topics.

## Raw Sources

- `raw/resources/ADCtoolbox/学习整理_MD/`: imported Markdown learning notes.
- `raw/resources/ADCtoolbox/ADC基础/`: imported ADC source materials.
- `raw/resources/ADCtoolbox/*.pdf`, `*.docx`: imported source documents.

Raw sources are source-of-truth material. Do not rewrite them as part of wiki
maintenance.

## Wiki Areas

- `wiki/concepts/`: reusable concept pages such as least squares, rank, FFT metrics, ENOB, SNDR, SAR weights.
- `wiki/source_code/`: pages explaining ADCToolbox source files and functions.
- `wiki/workflows/`: end-to-end procedures such as SAR modeling to calibration.
- `wiki/rigor/`: mathematical and engineering rigor notes, assumptions, open questions, checklists.
- `wiki/source_notes/`: notes created when ingesting a source document, example, or code file.
- `wiki/source_notes/examples/`: example evidence notes created with `schema/EXAMPLE_NOTE_TEMPLATE.md`.
- `audits/`: periodic health checks for completeness, code relevance, and maintenance maturity.
- `tools/`: local maintenance helpers such as `lint_wiki.py` and `search_wiki.py`.

## Current High-Value Pages

- [ADC weight calibration](wiki/concepts/adc_weight_calibration.md)
- [SAR model source](wiki/source_code/sar_py.md)
- [Lite sine-weight calibration source](wiki/source_code/calibrate_weight_sine_lite_py.md)
- [Full sine-weight calibration source](wiki/source_code/calibrate_weight_sine_py.md)
- [Spectrum source](wiki/source_code/compute_spectrum_py.md)
- [Spectrum helper chain](wiki/source_code/spectrum_helper_chain_py.md)
- [Window helper source](wiki/source_code/window_py.md)
- [Noise power helper source](wiki/source_code/estimate_noise_power_py.md)
- [Spectrum wrapper source](wiki/source_code/analyze_spectrum_py.md)
- [Quick SNDR source](wiki/source_code/quick_sndr_py.md)
- [Frequency utilities source](wiki/source_code/frequency_py.md)
- [Sine fitting source](wiki/source_code/fit_sine_4param_py.md)
- [Rank deficiency patch source](wiki/source_code/patch_rank_deficiency_py.md)
- [Calibration helper chain](wiki/source_code/calibration_helper_chain_py.md)
- [FFT metrics](wiki/concepts/fft_metrics.md)
- [Least-squares ADC calibration](wiki/concepts/least_squares_adc_calibration.md)
- [Rank deficiency](wiki/concepts/rank_deficiency.md)
- [SAR model to calibration workflow](wiki/workflows/sar_model_to_calibration.md)
- [Spectrum validation before and after calibration](wiki/workflows/spectrum_validation_before_after_calibration.md)
- [Example ingest map](wiki/workflows/example_ingest_map.md)
- [Mathematical rigor gaps](wiki/rigor/mathematical_rigor_gaps.md)
- [Identifiability conditions](wiki/rigor/identifiability_conditions.md)
- [Spectrum metric statistical risks](wiki/rigor/spectrum_metric_statistical_risks.md)

## Current Policy

This wiki is additive. It does not replace the staged course and does not edit
existing `adctoolbox-learning` material outside `toolbox-wiki/`.
