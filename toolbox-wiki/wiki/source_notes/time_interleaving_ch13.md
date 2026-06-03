# Source Note: Time-Interleaved ADCs

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/13_ch13_Time_Interleaving.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/13_ch13_Time_Interleaving.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch13.pdf
rigor:
  - source-confirmed
  - primary-source-spot-checked
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Time interleaving increases sample rate by using multiple ADC channels, but it
turns ADC calibration into a channel-mismatch problem.

## Key Extracted Ideas

- `M` interleaved channels can achieve an aggregate rate of roughly `M*fs`.
- Channels sample in a repeated order, then digital logic recombines outputs.
- Offset mismatch creates periodic errors and fixed-position spurs.
- Gain mismatch amplitude-modulates the input and creates input-dependent image
  spurs.
- Timing mismatch shifts each channel's sample time; its error grows with input
  slope and frequency.
- Interleaving errors are periodic, so they tend to appear as spurs rather than
  white noise.
- Offset and gain correction are usually simpler than timing-skew correction.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [Data converter testing source note](data_converter_testing_ch17.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Rigor Notes

Time-interleaving is not currently a central ADCToolbox wiki path, but it is
important context for spur interpretation and multi-channel calibration.

## Open Follow-Up

Add a future topic page if ADCToolbox examples or source code begin covering
time-interleaved ADC calibration.
