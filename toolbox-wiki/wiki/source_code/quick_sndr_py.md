# `quick_sndr.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/quick_sndr.py
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/_window.py
  - ../../../../../python/src/adctoolbox/spectrum/_locate_fundamental.py
rigor:
  - source-confirmed
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: high
```

## One-Sentence Takeaway

`quick_sndr.py` is a lean SNDR/ENOB path for optimization loops and fast gates,
not a full spectrum analysis replacement.

## Public API Purpose

`quick_sndr(data, fs=1.0, win_type="hann", side_bin=None, max_scale_range=None)`
returns:

- `sndr_dbc`
- `enob`

## Core Data Flow

```text
data
  -> _prepare_fft_input
  -> _create_window
  -> _power_average
  -> _calculate_power_correction
  -> _locate_fundamental
  -> signal bin sum
  -> noise+distortion bin sum
  -> SNDR and ENOB
```

## Difference From `compute_spectrum`

`quick_sndr` omits:

- THD;
- SFDR;
- SNR noise estimator;
- harmonic bin diagnostics;
- auto side-bin detection;
- plot data.

It is useful when only SNDR/ENOB is needed and the side-bin policy is already
known.

## Assumptions

- Single 1D capture.
- The largest in-band peak is the fundamental.
- Default coherent side-bin is acceptable, or the caller passes `side_bin`.
- Harmonics and noise are intentionally grouped together as noise+distortion.

## Rigor And Risks

- `source-confirmed`: the simplified metric path is visible in the source.
- `engineering-heuristic`: useful for speed, but it hides diagnostics needed
  for serious validation claims.
- Do not use `quick_sndr` alone to justify calibration robustness.

## Related Pages

- [compute_spectrum source](compute_spectrum_py.md)
- [Spectrum helper chain](spectrum_helper_chain_py.md)
- [Window helper](window_py.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum validation workflow](../workflows/spectrum_validation_before_after_calibration.md)

## Next Reading

Use `compute_spectrum.py` when a metric claim needs auditability.
