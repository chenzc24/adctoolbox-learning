# Source Note: Folding And Interpolating ADCs

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/09_ch9_Folding_Interpolating_ADC.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/09_ch9_Folding_Interpolating_ADC.md
  - flash_adc_ch8.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch9.pdf
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

Folding and interpolating ADCs reduce Flash ADC comparator complexity by using
analog preprocessing, but they introduce new threshold, path, bandwidth, and
linearity errors.

## Key Extracted Ideas

- Interpolation derives intermediate threshold information from neighboring
  preamplifier or comparator outputs.
- Interpolation trades fewer comparators for interpolation-network mismatch,
  bandwidth limits, and nonlinearity.
- Folding maps a wide input range into repeated smaller ranges, combining
  coarse location with folded fine decisions.
- Folding amplifiers need accurate zero-crossing positions, high bandwidth, and
  good linearity.
- Path delay mismatch can create dynamic errors at high input frequency.
- Calibration emphasis is threshold position, gain, and path consistency.

## Integration Into The Wiki

This source supports:

- [Flash ADCs](flash_adc_ch8.md)
- [Data converter testing](data_converter_testing_ch17.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Rigor Notes

This architecture is useful context for why ADC calibration varies by
architecture. Folding/interpolating calibration is not the same problem as SAR
CDAC weight calibration or Pipeline stage-weight calibration.

## Open Follow-Up

Leave this as context unless ADCToolbox later adds folding/interpolating
examples or source code.
