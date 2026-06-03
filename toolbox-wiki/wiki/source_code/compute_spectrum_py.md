# `compute_spectrum.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/_window.py
  - ../../../../../python/src/adctoolbox/spectrum/_locate_fundamental.py
  - ../../../../../python/src/adctoolbox/spectrum/_harmonics.py
  - ../../../../../python/src/adctoolbox/spectrum/_estimate_noise_power.py
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

`compute_spectrum.py` is the metric engine that turns ADC output samples into
FFT-domain quantities such as ENOB, SNDR, SFDR, SNR, THD, harmonics, and noise
floor.

## Public API Purpose

`compute_spectrum(data, fs=1.0, win_type="hann", side_bin=None, osr=1, ...)`
returns a dictionary with:

- top-level run parameters: `N`, `M`, `fs`, `osr`;
- `metrics`: `enob`, `sndr_dbc`, `sfdr_dbc`, `snr_dbc`, `sig_pwr_dbfs`,
  `noise_floor_dbfs`, `nsd_dbfs_hz`, `thd_dbc`, `harmonics_dbc`;
- `plot_data`: frequency axis, plotted spectrum, fundamental bin, side-bin
  region, harmonic bins, spur bin, coherent-averaging status, and noise parts.

## Core Data Flow

```text
data
  -> _prepare_fft_input
  -> window creation and windowing
  -> power or coherent averaging
  -> power correction
  -> optional cutoff removal
  -> fundamental location
  -> side-bin choice or auto detection
  -> signal power, harmonic power, spur power
  -> SNDR, ENOB, SNR, THD, SFDR, noise floor, NSD
```

## Metric Meaning

- SNDR uses fundamental signal power divided by all in-band non-signal power.
- ENOB is computed as `(SNDR - 1.76) / 6.02`.
- SNR uses a separate noise estimator that can exclude harmonic-related bins.
- THD uses harmonic bins derived from the fractional fundamental bin.
- SFDR compares the fundamental peak against the largest remaining spur.

## Important Implementation Choices

The function does not simply run an FFT and read one bin. It also corrects for
window power, decides how many bins around the fundamental count as signal, and
uses helper functions for harmonic and noise handling.

`side_bin=None` triggers automatic side-bin detection. This is practical, but it
also means metric comparability depends on the side-bin decision.

## Assumptions

- Input data is appropriate for FFT-based ADC metric analysis.
- The selected window and side-bin settings match the sampling condition.
- The fundamental is the largest meaningful in-band tone.
- The noise estimator matches the intended definition of SNR.
- Harmonics and folded harmonics are identified correctly enough for the metric
  claim being made.

## Rigor And Risks

- `source-confirmed`: metric fields and data flow are visible in the source.
- `theory-supported`: SNDR, ENOB, SNR, THD, and SFDR follow standard ADC
  spectral-test ideas.
- `engineering-heuristic`: automatic side-bin and noise-floor choices are
  practical defaults, not universal definitions.
- `open-question`: every before/after calibration comparison should record
  `win_type`, `side_bin`, `osr`, `nf_method`, sampling coherence, and signal
  amplitude.

## Related Pages

- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum helper chain](spectrum_helper_chain_py.md)
- [Window helper](window_py.md)
- [Noise power helper](estimate_noise_power_py.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)
- [Spectrum validation workflow](../workflows/spectrum_validation_before_after_calibration.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)
- [Spectrum metric statistical risks](../rigor/spectrum_metric_statistical_risks.md)
- [Spectrum source note](../source_notes/fft_sampling_note.md)
- [ADC metrics source note](../source_notes/adc_metrics_ch3.md)

## Next Reading

Read `_window.py`, `_side_bin_auto.py`, and `_estimate_noise_power.py` next when
studying why two spectrum runs may produce different metric numbers.
