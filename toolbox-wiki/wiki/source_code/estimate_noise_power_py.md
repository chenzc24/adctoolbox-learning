# `_estimate_noise_power.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/04_概率噪声_RMS_功率_方差.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/_estimate_noise_power.py
  - ../../../../../python/src/adctoolbox/spectrum/_exclude_bins.py
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

`_estimate_noise_power.py` decides what counts as noise after DC, fundamental,
and sometimes harmonics have been removed from the in-band spectrum.

## Public API Purpose

This internal helper supports SNR, noise floor, and NSD estimation for
`compute_spectrum.py`.

Important helpers:

- `_estimate_noise_power(...)`
- `_zeroed_inband_spectrum(...)`
- `_calculate_noise_metrics(...)`

## Noise Methods

`nf_method` selects the estimator:

- `0`: auto, median of median/trimmed/exclude estimates.
- `1`: median estimator.
- `2`: trimmed mean estimator.
- `3`: exclude harmonics and sum remaining spectrum.
- `4`: legacy wide exclusion around DC, fundamental, and harmonics.

## Core Data Flow

```text
power_spectrum
  -> keep in-band bins
  -> zero DC and fundamental main lobe
  -> optionally remove harmonics
  -> estimate noise power
  -> SNR, noise_floor_dbfs, NSD
```

## Why This Matters

SNDR and SNR are not identical. SNDR in `compute_spectrum.py` sums everything
except the signal region. SNR uses a noise estimator that may treat harmonics
differently. This distinction matters when calibration improves harmonic
distortion but not broadband noise, or vice versa.

## Assumptions

- The fundamental bin and side-bin range are already correct.
- Harmonic bins are known well enough to exclude or include as intended.
- Median or trimmed estimators represent the broadband floor.
- Enough noise bins remain after exclusions.

## Rigor And Risks

- `source-confirmed`: all `nf_method` branches are visible in the source.
- `theory-supported`: median and trimmed estimators are robust noise-floor
  ideas.
- `engineering-heuristic`: choosing among noise estimators is a measurement
  policy decision.
- `open-question`: benchmark pages should compare `nf_method` choices on the
  same waveform before using SNR as a calibration claim.

## Related Pages

- [compute_spectrum source](compute_spectrum_py.md)
- [Spectrum helper chain](spectrum_helper_chain_py.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum metric statistical risks](../rigor/spectrum_metric_statistical_risks.md)

## Next Reading

Read `_harmonics.py` next, because the noise estimator depends on which bins
are considered harmonic bins.
