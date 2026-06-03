# Spectrum Helper Chain

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/_prepare_fft_input.py
  - ../../../../../python/src/adctoolbox/spectrum/_locate_fundamental.py
  - ../../../../../python/src/adctoolbox/spectrum/_side_bin_auto.py
  - ../../../../../python/src/adctoolbox/spectrum/_harmonics.py
  - ../../../../../python/src/adctoolbox/spectrum/_spectrum_averaging.py
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
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

The spectrum helper chain turns raw time samples into robust bin choices before
metric formulas are applied.

## Helper Map

- `_prepare_fft_input.py`: shape normalization, DC removal, full-scale
  normalization.
- `_spectrum_averaging.py`: power averaging or coherent averaging.
- `_window.py`: window vector, ENBW, coherent gain, side-bin defaults.
- `_locate_fundamental.py`: in-band peak search and parabolic interpolation.
- `_side_bin_auto.py`: leakage-aware side-bin detection.
- `_harmonics.py`: harmonic folding, THD bins, collided harmonics, highest spur.
- `_estimate_noise_power.py`: SNR noise estimator.

## Core Data Flow

```text
data
  -> shape and amplitude normalization
  -> window and FFT averaging
  -> power correction
  -> fundamental location
  -> side-bin choice
  -> harmonic folding and spur extraction
  -> noise estimation
  -> metrics and plot_data
```

## Why This Matters

The headline metric values in `compute_spectrum.py` are downstream of many
measurement choices. A code-linked learning path should inspect helper outputs
such as `fundamental_bin`, `fundamental_bin_fractional`, `sig_bin_start`,
`sig_bin_end`, `harmonic_bins`, `collided_harmonics`, and `noise_parts`.

## Important Engineering Choices

- Fundamental search excludes DC and only searches in-band.
- Parabolic interpolation is suppressed for very coherent-looking peaks with
  floor-level neighbors.
- Harmonics are folded to Nyquist bins.
- THD excludes harmonics that collide with the fundamental.
- Auto side-bin compares ideal leakage against a median-like floor.
- Noise estimation has multiple policy modes.

## Assumptions

- The largest in-band non-DC component is the fundamental.
- Full-scale normalization matches the intended dBFS convention.
- Harmonic folding is sufficient for the distortion definition being used.
- The selected `osr` correctly defines the in-band region.

## Rigor And Risks

- `source-confirmed`: helper responsibilities are visible in source files.
- `engineering-heuristic`: auto-detection and estimator choices are designed
  for useful ADC measurements, not for every possible spectrum.
- `open-question`: spectrum-validation pages should compare settings instead
  of treating a single ENOB number as absolute truth.

## Related Pages

- [compute_spectrum source](compute_spectrum_py.md)
- [window helper](window_py.md)
- [noise power helper](estimate_noise_power_py.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum validation workflow](../workflows/spectrum_validation_before_after_calibration.md)

## Next Reading

Read `compute_spectrum_py.md` after this page to see how these helpers are
assembled into one public calculation engine.
