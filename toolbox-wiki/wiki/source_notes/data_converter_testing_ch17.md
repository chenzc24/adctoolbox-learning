# Source Note: Data Converter Testing

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/17_ch17_数据转换器测试.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/17_ch17_数据转换器测试.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC test results are only meaningful together with the test bench, signal
source, clock source, input condition, and analysis method that produced them.

## Key Extracted Ideas

- A test bench includes power, biasing, signal source, clock source, DUT, data
  capture, and data analysis.
- Source distortion can be mistaken for ADC distortion.
- Clock jitter can limit measured SNR.
- Supply or reference noise can create spurs.
- Static testing measures transition levels, code widths, DNL, and INL.
- Dynamic testing uses sine input and FFT analysis for SNR, SNDR, ENOB, SFDR,
  and THD.
- Coherent sampling reduces leakage; non-coherent sampling requires windowing
  and correct normalization.
- Calibration validation should be layered: parameter convergence, static
  linearity, then dynamic spectrum improvement.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)

## Rigor Notes

Before/after calibration comparisons should record input amplitude, input
frequency, sampling rate, FFT length, window, averaging, clock quality, source
quality, and bandwidth definition.

## Open Follow-Up

Create `wiki/workflows/spectrum_validation_before_after_calibration.md` using
this source as the measurement-discipline anchor.
