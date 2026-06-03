# `_window.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/_window.py
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/quick_sndr.py
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

`_window.py` defines the FFT window vector, coherent gain, equivalent noise
bandwidth, default side-bin rules, and power correction used by spectrum
metrics.

## Public API Purpose

This is an internal helper used by `compute_spectrum.py` and `quick_sndr.py`.

Important helpers:

- `_create_window(win_type, N)`
- `_get_default_side_bin(win_type)`
- `_get_auto_side_bin_fallback(win_type)`
- `_calculate_power_correction(window_gain, equiv_noise_bw_factor)`

## Core Data Flow

```text
win_type + N
  -> window_vector
  -> window_gain
  -> equivalent_noise_bandwidth
  -> power correction
  -> default or fallback side-bin rule
```

## Why This Matters

Window choice changes both tone amplitude and noise bandwidth. ADCToolbox
therefore does not treat FFT bins as raw powers. It applies a power correction
derived from coherent gain and ENBW.

This is why spectrum pages must record `win_type` and `side_bin` before
comparing ENOB or SNDR numbers.

## Important Implementation Choices

- Unknown windows default to Hann.
- Rectangular/boxcar has coherent `side_bin = 0`.
- Hann and Hamming default to `side_bin = 1`.
- Wider windows such as flat-top and Blackman-Harris use wider coherent
  main-lobe defaults.
- Auto side-bin fallback is separate from coherent default side-bin.

## Assumptions

- The chosen side-bin rule captures the intended signal main lobe.
- The window model is appropriate for the capture coherence.
- Non-coherent captures need explicit or auto side-bin handling rather than
  blindly using coherent defaults.

## Rigor And Risks

- `source-confirmed`: window defaults and correction formula are implemented
  directly in `_window.py`.
- `theory-supported`: coherent gain and ENBW are standard FFT measurement
  concepts.
- `engineering-heuristic`: default side bins are practical rules, not universal
  metric definitions.

## Related Pages

- [compute_spectrum source](compute_spectrum_py.md)
- [Spectrum helper chain](spectrum_helper_chain_py.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum validation workflow](../workflows/spectrum_validation_before_after_calibration.md)

## Next Reading

Read `_side_bin_auto.py` after this page to see how ADCToolbox handles
non-coherent or leakage-heavy captures.
