# Training And Validation Split For ADC Calibration

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/17_ch17_数据转换器测试.md
source_links:
  - ../source_notes/sun_testing_primary_pdf_distillation.md
  - ../source_notes/sun_sar_primary_pdf_distillation.md
  - ../source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md
  - ../source_notes/examples/exp_d02_cal_weight_sine.md
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/analyze_spectrum.py
rigor:
  - source-confirmed
  - primary-source-direct-distilled
  - example-verified
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC calibration should solve parameters on training data and report final
performance on independent validation data, with identical metric settings and
explicit test-bench assumptions.

## Why This Exists

The Sun testing PDF stresses that ADC metrics depend on source quality, clock
jitter, histogram assumptions, and FFT settings. The `exp_d18` example adds a
software-side lesson: short calibration records can look excellent on the data
used for fitting while failing on an independent capture.

Together, these sources imply a workflow rule:

```text
Do not use a training-record metric as the final evidence of calibration.
```

## Formula And Figure Review

From the primary testing PDF:

- DNL/INL from histogram testing depends on code-density assumptions.
- Sine-input histograms require distribution linearization.
- Histogram testing assumes monotonicity and can miss dynamic sparkle codes.
- Clock jitter noise scales with input frequency and amplitude.
- FFT-based metrics are meaningful only with controlled source, clock, and
  analysis settings.

From the SAR training-length example:

- The calibration-capture ENOB curve and independent-test ENOB curve can
  diverge for short training records.
- The overlay figure marks ill-conditioned and overfitting regions.
- The example explicitly uses separate training and test tones.

## Required Data Split

Use at least two captures:

```text
training capture:
  used to estimate calibration parameters

validation capture:
  not used in the solve
  used to report final metrics
```

For stronger claims, add:

```text
stress captures:
  different frequency
  different amplitude
  different phase
  different temperature/corner/mismatch seed
```

## Minimal Workflow

1. Define the calibration target:
   weight recovery, offset/gain correction, residue-gain correction, harmonic
   fitting, or static nonlinearity fitting.
2. Capture or generate training data.
3. Record the training setup:
   `N`, `fs`, input frequency, amplitude, phase, window plan, and model seed.
4. Solve calibration parameters on training data only.
5. Record solve diagnostics:
   rank, singular values or condition number, merged columns, residual RMS, and
   fitted frequency.
6. Capture or generate validation data that was not used in the solve.
7. Reconstruct validation data with nominal and calibrated parameters.
8. Run identical metric settings before and after calibration.
9. Report both training and validation metrics.
10. Treat success as credible only if validation improves and diagnostics are
    consistent with the claimed model.

## Required Metric Settings

For every before/after spectrum comparison, record:

- `N`
- `fs`
- input frequency or fundamental bin
- input amplitude
- coherent or non-coherent condition
- `win_type`
- `side_bin`
- `max_harmonic`
- `nf_method`
- `osr`
- bandwidth definition
- whether this is training, validation, or stress data

## Required Calibration Diagnostics

For weight calibration, record:

- number of samples;
- number of fitted parameters;
- rank of the design matrix;
- singular values or condition number;
- rank-deficiency patching or merged columns;
- frequency used for solving;
- whether frequency was known, estimated, or refined;
- residual RMS on training data;
- residual RMS or metric delta on validation data.

## Required Static Checks

When claiming static linearity or no missing codes, record:

- DNL/INL method;
- input distribution assumption;
- monotonicity assumption;
- missing-code threshold;
- noise level;
- whether code-density testing could be smeared by noise;
- whether direct output-code inspection was performed.

## Decision Table

| Training metric | Validation metric | Interpretation |
| --- | --- | --- |
| improves | improves | credible calibration evidence, subject to diagnostics |
| improves | unchanged | likely overfit, wrong model, or metric mismatch |
| improves | worsens | harmful calibration or train/test mismatch |
| unchanged | improves | check metric settings and stochastic variation |
| worsens | improves | possible regularization effect, but needs explanation |

## Project Implementation

Relevant ADCToolbox paths:

- `calibrate_weight_sine.py`: solves weights from bit decisions.
- `compute_spectrum.py`: computes dynamic metrics.
- `analyze_spectrum.py`: wrapper for spectrum analysis and plots.
- `quick_sndr.py`: lean metric path used in sweeps.
- `exp_d18_sar_redundant_mismatch_training_length_sweep.py`: current best
  example of training/validation separation and overfitting detection.

## What This Does Not Prove

- It does not prove calibration generalizes to all PVT corners.
- It does not prove physical parameters are uniquely identified.
- It does not prove FFT metrics capture every failure mode.
- It does not replace static DNL/INL or missing-code validation.
- It does not eliminate the need for source and clock quality checks in real
  measurements.

## Related Pages

- [Spectrum validation before and after calibration](spectrum_validation_before_after_calibration.md)
- [Sun Testing primary PDF distillation](../source_notes/sun_testing_primary_pdf_distillation.md)
- [Sun SAR primary PDF distillation](../source_notes/sun_sar_primary_pdf_distillation.md)
- [Example: SAR training-length sweep](../source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md)
- [Full sine-weight calibration source](../source_code/calibrate_weight_sine_py.md)
- [Spectrum source](../source_code/compute_spectrum_py.md)
- [Spectrum metric statistical risks](../rigor/spectrum_metric_statistical_risks.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## Next Work

Add a small example checklist or script wrapper that writes the required train
and validation diagnostics beside each calibration result.
