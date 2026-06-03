# Spectrum Metric Statistical Risks

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/_window.py
  - ../../../../../python/src/adctoolbox/spectrum/_estimate_noise_power.py
  - ../../../../../python/src/adctoolbox/spectrum/_side_bin_auto.py
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

FFT metrics are reproducible only when their statistical and bin-selection
conditions are recorded.

## Claim Or Risk

Two runs can produce different ENOB, SNDR, SNR, THD, or SFDR numbers for the
same underlying ADC behavior if they use different record lengths, windows,
side bins, in-band ranges, harmonic rules, or noise estimators.

## What The Project Does

ADCToolbox exposes these choices through:

- `win_type`
- `side_bin`
- `osr`
- `max_harmonic`
- `nf_method`
- `coherent_averaging`
- `cutoff_freq`
- `assumed_sig_pwr_dbfs`

It also returns diagnostic fields in `plot_data` and `noise_parts`.

## What Is Not Proven

- That auto side-bin detection is best for every waveform.
- That one `nf_method` is universally correct.
- That an ENOB improvement generalizes beyond the analyzed record.
- That harmonics, spurs, and broadband noise are separated in the physically
  intended way.

## Validation Recipe

For any important metric claim:

1. Save the full `compute_spectrum` settings.
2. Save `metrics` and `plot_data`.
3. Compare at least two window/side-bin strategies when leakage is possible.
4. Compare `nf_method` choices if SNR or noise floor is central.
5. Use held-out data when claiming calibration improvement.
6. Record collided harmonics and folded bins.

## Related Pages

- [FFT metrics](../concepts/fft_metrics.md)
- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [window helper](../source_code/window_py.md)
- [noise power helper](../source_code/estimate_noise_power_py.md)
- [Spectrum validation workflow](../workflows/spectrum_validation_before_after_calibration.md)

## Next Reading

Read the before/after validation workflow and then inspect actual examples that
compare pre-calibration and post-calibration spectra.
