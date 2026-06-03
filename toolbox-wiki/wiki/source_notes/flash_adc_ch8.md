# Source Note: Flash ADCs

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/08_ch8_Flash_ADC.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/08_ch8_Flash_ADC.md
  - comparator_ch7.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch8.pdf
rigor:
  - source-confirmed
  - primary-source-spot-checked
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Flash ADCs perform parallel threshold comparison with extremely low latency,
but comparator count, reference loading, offset, noise, and encoding complexity
grow rapidly with resolution.

## Key Extracted Ideas

- An `N`-bit Flash ADC needs `2^N - 1` transition levels and comparators.
- A resistor ladder often generates the reference thresholds.
- Comparator outputs form a thermometer code before binary encoding.
- Bubble errors occur when the thermometer code has local decision mistakes.
- DNL/INL mainly come from reference-ladder mismatch and comparator offset.
- Flash ADCs are often too costly for high resolution, but low-bit Flash
  sub-ADCs appear inside Pipeline, Folding, and other fast ADCs.

## Integration Into The Wiki

This source supports:

- [Voltage comparators](comparator_ch7.md)
- [Pipeline ADC concept](pipeline_adc_concept_ch10.md)
- [Data converter testing](data_converter_testing_ch17.md)

## Rigor Notes

Flash ADC calibration is more threshold-oriented than SAR weight calibration.
Transition-level measurement, bubble correction, and comparator offset matter
more than bit-weight least squares.

## Open Follow-Up

Add a future concept page for threshold calibration if Flash/sub-ADC examples
become central.
