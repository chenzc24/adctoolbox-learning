# Source Note: ADC Performance Metrics Chapter

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
rigor:
  - source-confirmed
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This raw note gives the learner vocabulary for ADC performance: static errors
describe the transfer curve, while dynamic metrics describe the spectrum under
a sine input.

## Key Extracted Ideas

- Offset error is an additive shift in the transfer curve.
- Gain error is a slope error after offset is removed.
- DNL describes local code-width error.
- INL describes accumulated deviation from the ideal transfer line.
- SNR compares signal power to noise power.
- SNDR includes both noise and distortion.
- ENOB translates SNDR into an equivalent ideal ADC bit count.
- SFDR measures distance from the fundamental to the largest spur.
- THD measures harmonic distortion power.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)

## Rigor Notes

Metric names alone are not enough. A metric claim also needs measurement
conditions: input amplitude, input frequency, FFT length, window, side-bin
rule, harmonic handling, and in-band bandwidth.

## Open Follow-Up

Turn this source into a learner-facing comparison table that separates static
metrics, dynamic metrics, and calibration targets.
