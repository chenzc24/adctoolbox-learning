# Toolbox Wiki Log

## [2026-06-03] ingest | Distill calibration-critical Sun-course PDFs

- Added direct primary-PDF distillation notes for SAR, Pipeline, and testing chapters.
- Connected SAR PDF material to CDAC/comparator noise, redundancy, timing, calibration tolerance, and SAR example evidence notes.
- Connected Pipeline PDF material to residue, interstage gain, sub-DAC error, backend-observable calibration, and stage-level rigor questions.
- Connected testing PDF material to histogram DNL/INL, clock/source limits, FFT metric comparability, and validation workflow requirements.
- Updated `wiki/index.md`, `coverage_matrix.md`, `progress.md`, `open_questions.md`, and `logs/log.md`.

## [2026-06-03] audit | Spot-check Sun-course notes against original PDFs

- Added original Sun-course PDF links to 14 core ADC source notes that were previously derived mainly from pre-extracted Markdown.
- Added `primary-source-spot-checked` rigor tags to those notes after `pdftotext` extraction and chapter-keyword checks.
- Added `audits/source_fidelity_sun_course_2026-06-03.md` and updated `index.md`, `coverage_matrix.md`, and `progress.md`.

## [2026-06-03] ingest | Add redundancy and SAR example evidence notes

- Added example notes for redundancy comparison, SAR unit-cap mismatch Monte Carlo, and SAR redundant training-length sweep.
- Updated `wiki/workflows/example_ingest_map.md` to mark the initial calibration evidence queue as ingested and add next example candidates.
- Updated `wiki/index.md`, `coverage_matrix.md`, `open_questions.md`, `progress.md`, and `audits/raw_distillation_2026-06-03.md`.

## [2026-06-03] ingest | Add first example evidence notes

- Added example notes for `exp_a01_fit_sine_4param.py`, `exp_d01_cal_weight_sine_lite.py`, and `exp_d02_cal_weight_sine.py`.
- Updated `wiki/workflows/example_ingest_map.md` to mark the first three queued examples as ingested.
- Updated `wiki/index.md`, `coverage_matrix.md`, `open_questions.md`, `progress.md`, and `audits/raw_distillation_2026-06-03.md`.

## [2026-06-03] ingest | Start PDF and DOCX source distillation

- Added source notes for `ADC测试分析与校准.pdf`, `Data Conversion Handbook.pdf`, `ADC关键metric及concept.docx`, and `ADC工作物理系统结构.docx`.
- Connected the new notes to ADC metrics, physical structure, test bench discipline, FFT validation, linear-equation calibration, dither calibration, and ADCToolbox source pages.
- Updated `wiki/index.md`, `coverage_matrix.md`, `open_questions.md`, `progress.md`, and `audits/raw_distillation_2026-06-03.md`.

## [2026-06-03] ingest | Complete high-priority Markdown source distillation

- Added source notes for Flash ADCs, folding/interpolating ADCs, complex phase/systems view, and MATLAB fundamentals.
- Updated `wiki/index.md`, `coverage_matrix.md`, `open_questions.md`, `progress.md`, and `audits/raw_distillation_2026-06-03.md`.
- This pass completes the current high-priority Markdown raw-source distillation queue; remaining high-value work shifts to PDF/DOCX source notes and example evidence notes.

## [2026-06-03] code | Extend core source-code chain

- Added source-code pages for spectrum windows, noise estimation, spectrum helpers, calibration helpers, `analyze_spectrum`, `quick_sndr`, and `fundamentals/frequency`.
- Added concept pages for least-squares ADC calibration and rank deficiency.
- Added workflow page for before/after spectrum validation after calibration.
- Added rigor page for spectrum metric statistical risks.
- Updated wiki index, coverage matrix, open questions, and progress tracking.

## [2026-06-03] ingest | Expand circuit and math raw-source distillation

- Added source notes for sampling circuits, voltage comparators, Pipeline ADC concept, Pipeline ADC implementation, high-speed SAR, oversampling ADCs, convolution/filtering, dither, and vectors/matrices/linear combinations.
- Updated `wiki/index.md`, `coverage_matrix.md`, `open_questions.md`, `progress.md`, and `audits/raw_distillation_2026-06-03.md`.
- This pass strengthens the bridge from circuit nonidealities to calibration observability, spectrum interpretation, and ADCToolbox source-code learning.

## [2026-06-03] ingest | Expand raw Markdown source-note distillation

- Added source notes for ADC FOM, data-converter testing, matrix rank/observability, noise/RMS/power/variance, quantization noise, switched-capacitor settling/noise, time-interleaving, and MATLAB code reading.
- Updated `wiki/index.md`, `coverage_matrix.md`, and `open_questions.md` to track the expanded raw distillation coverage.
- Added `audits/raw_distillation_2026-06-03.md` to record distilled raw notes and remaining source gaps.
- This pass focuses on raw Markdown notes that directly support calibration, spectrum metrics, noise modeling, and future MATLAB bridge work.

## [2026-06-03] structure | Cap maintenance rules and retrieval structure

- Added `schema/PROMOTION_RULES.md` for `draft`, `usable`, `stable`, and `deprecated` page status.
- Added `schema/SEMANTIC_LINT_CHECKLIST.md` for contradictions, stale claims, semantic islands, and promotion review.
- Added `schema/PROOF_PAGE_TEMPLATE.md` and `schema/EXAMPLE_NOTE_TEMPLATE.md`.
- Added `tools/search_wiki.py` for dependency-free keyword search over wiki and optional raw sources.
- Extended `tools/lint_wiki.py` to validate page status values.
- Added `wiki/workflows/example_ingest_map.md` as the structural queue for example evidence notes.
- Updated indexes, rules, lint checklist, coverage matrix, open questions, and progress tracking.
- Added `audits/structure_cap_2026-06-03.md` after lint and search smoke tests passed.

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
