# Learning Progress

## Current State

The learner already has staged materials in the broader `adctoolbox-learning`
workspace. This wiki was added as a sidecar so future synthesis can compound
without disturbing the existing staged course.

## Protected Existing Work

- Do not batch rewrite existing staged course files outside `toolbox-wiki/`.
- Do not rename existing staged course directories.
- Do not move existing `adctoolbox-learning` content into this wiki.
- Imported raw materials under `toolbox-wiki/raw/resources/` are read-only sources.

## Current Learning Direction

The next learning bridge is from staged ADC/math/MATLAB foundations into:

- ADCToolbox project structure.
- SAR behavioral modeling.
- FFT metric calculation.
- Sine fitting and residual analysis.
- Weight calibration by least squares.
- Mathematical rigor limits of ADC calibration.

## Completed Wiki Seed Pages

- `wiki/concepts/adc_weight_calibration.md`
- `wiki/source_code/sar_py.md`
- `wiki/source_code/calibrate_weight_sine_lite_py.md`
- `wiki/source_code/calibrate_weight_sine_py.md`
- `wiki/source_code/compute_spectrum_py.md`
- `wiki/source_code/fit_sine_4param_py.md`
- `wiki/source_code/patch_rank_deficiency_py.md`
- `wiki/workflows/sar_model_to_calibration.md`
- `wiki/rigor/mathematical_rigor_gaps.md`
- `wiki/rigor/identifiability_conditions.md`
- `wiki/concepts/fft_metrics.md`
- `wiki/source_notes/adc_metrics_ch3.md`
- `wiki/source_notes/fft_sampling_note.md`
- `wiki/source_notes/least_squares_calibration_note.md`
- `wiki/source_notes/sar_low_power_ch12a.md`

These pages form the first reusable map from ADCToolbox source code to ADC
modeling, calibration, validation, and rigor questions.

## Maintenance Baseline

- `coverage_matrix.md` tracks which concepts, source-code pages, workflows,
  rigor pages, and source notes exist.
- `open_questions.md` tracks mathematical, engineering, and maintenance
  questions that should not be silently lost.
- `audits/knowledge_base_health_2026-06-03.md` records the current baseline:
  structurally safe, code-linked at seed level, but not yet complete.
- `tools/lint_wiki.py` runs automated checks for links, metadata, index
  coverage, log headings, and raw directory presence.

## Next Wiki Pages To Create

- `wiki/concepts/least_squares_adc_calibration.md`
- `wiki/concepts/rank_deficiency.md`
- `wiki/rigor/spectrum_metric_statistical_risks.md`
- `wiki/rigor/redundant_sar_reachability.md`
- `wiki/workflows/spectrum_validation_before_after_calibration.md`
