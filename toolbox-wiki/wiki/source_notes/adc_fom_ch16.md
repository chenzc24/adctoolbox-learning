# Source Note: ADC Figures Of Merit

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/16_ch16_ADC_FOM.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/16_ch16_ADC_FOM.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch16 ADC Figures of Merit.pdf
rigor:
  - primary-source-spot-checked
  - source-confirmed
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC FOM compresses power, speed, bandwidth, and effective resolution into a
comparison number, but it should never replace the full measurement context.

## Key Extracted Ideas

- Walden FOM is commonly written as `Power / (2^ENOB * fs)`.
- Walden FOM is suited to Nyquist ADC energy-per-conversion-step comparison.
- Schreier FOM combines dynamic range, bandwidth, and power.
- Lower Walden FOM is usually better, but only within comparable ADC classes.
- FOM hides important details such as bandwidth, latency, area, reference
  requirements, temperature stability, and calibration overhead.
- Calibration can improve FOM by improving ENOB/SNDR or by relaxing analog
  precision requirements, but calibration itself has power, area, time, and
  complexity cost.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [ADC metrics source note](adc_metrics_ch3.md)

## Rigor Notes

Any FOM claim should state which FOM is being used, which bandwidth or sampling
rate is used, how ENOB or SNDR was measured, and whether calibration overhead
is included.

## Open Follow-Up

Add a future concept page for ADC FOM after spectrum validation pages are more
complete.
