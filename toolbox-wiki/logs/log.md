# Toolbox Wiki Log

## [2026-06-03] ingest | Core spectrum, sine fit, rank, and source-note pass

- Added source-code pages for `compute_spectrum.py`, `fit_sine_4param.py`, and `_patch_rank_deficiency.py`.
- Added concept page `wiki/concepts/fft_metrics.md`.
- Added rigor page `wiki/rigor/identifiability_conditions.md`.
- Added source notes for ADC metrics, FFT/sampling, least squares, and low-power SAR raw notes.
- Added `tools/lint_wiki.py` for automated wiki bookkeeping checks.
- Updated rules, template, indexes, coverage matrix, open questions, and progress tracking.
- Updated the health audit and added `audits/lint_2026-06-03.md` after automated lint passed.

## [2026-06-03] improve | Seed code-linked calibration wiki pages

- Added first reusable pages for SAR modeling, sine-weight calibration, and mathematical rigor.
- Added source-code pages for `models/sar.py`, `calibrate_weight_sine_lite.py`, and `calibrate_weight_sine.py`.
- Added the workflow page `wiki/workflows/sar_model_to_calibration.md`.
- Added the rigor page `wiki/rigor/mathematical_rigor_gaps.md`.
- Added `schema/LINT_CHECKLIST.md` for future completeness, code-linkage, source-linkage, and rigor audits.
- Added `audits/knowledge_base_health_2026-06-03.md` as a baseline health audit.
- Added `coverage_matrix.md` and `open_questions.md` to make gaps explicit and maintainable.
- Updated `wiki/index.md`, `index.md`, and `progress.md` so the new pages are discoverable and tracked.

## [2026-06-03] setup | Create ADCToolbox learner toolbox wiki

- Created `toolbox-wiki/` as a sidecar LLM Wiki inside `adctoolbox-learning`.
- Imported available resources from `E:\ADCToolbox\agent_playground\resources` into `toolbox-wiki/raw/resources`.
- Preserved existing `adctoolbox-learning` course content outside `toolbox-wiki/`.
- Added initial index, progress, schema rules, page template, and curriculum bridge files.
- Imported raw source count: 95 filesystem entries, including 38 Markdown files.
