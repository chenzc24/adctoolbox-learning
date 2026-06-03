# Spectrum Validation Before And After Calibration

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/analyze_spectrum.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/models/sar.py
rigor:
  - source-confirmed
  - example-verified
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Before/after calibration validation should compare spectra with identical
settings and with enough bin diagnostics to explain the metric change.

## Workflow

1. Generate or capture bit decisions.
2. Reconstruct an uncalibrated signal with nominal weights.
3. Run `compute_spectrum` on the uncalibrated reconstruction.
4. Calibrate weights with `calibrate_weight_sine`.
5. Reconstruct a calibrated signal with the calibrated weights.
6. Run `compute_spectrum` again with the same FFT settings.
7. Compare metrics and bin diagnostics.
8. Record residual risks and whether test data differs from training data.

## Required Settings To Record

- `N`
- `fs`
- `osr`
- `win_type`
- `side_bin`
- `max_harmonic`
- `nf_method`
- `coherent_averaging`
- `max_scale_range`
- input frequency or fundamental bin
- whether the spectrum is training or test data

## Required Diagnostics To Compare

From `metrics`:

- `enob`
- `sndr_dbc`
- `snr_dbc`
- `sfdr_dbc`
- `thd_dbc`
- `noise_floor_dbfs`
- `harmonics_dbc`

From `plot_data`:

- `fundamental_bin`
- `fundamental_bin_fractional`
- `sig_bin_start`
- `sig_bin_end`
- `harmonic_bins`
- `collided_harmonics`
- `noise_parts`

## What Improved Metrics Can Mean

An ENOB or SNDR improvement may indicate:

- better digital weight reconstruction;
- reduced harmonic distortion caused by weight mismatch;
- changed attribution between harmonics and noise;
- better fit to the training waveform only.

## What This Does Not Prove

Before/after spectrum improvement does not by itself prove:

- physical capacitor weights were uniquely identified;
- redundant SAR has no missing codes;
- performance generalizes across amplitude/frequency/corners;
- the noise estimator is the right one for every use case;
- the same improvement appears on held-out data.

## Related Pages

- [SAR model to calibration workflow](sar_model_to_calibration.md)
- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [analyze_spectrum source](../source_code/analyze_spectrum_py.md)
- [Spectrum helper chain](../source_code/spectrum_helper_chain_py.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum metric statistical risks](../rigor/spectrum_metric_statistical_risks.md)

## Next Reading

Read the spectrum metric statistical risks page before treating one before/after
ENOB number as a robust engineering conclusion.
