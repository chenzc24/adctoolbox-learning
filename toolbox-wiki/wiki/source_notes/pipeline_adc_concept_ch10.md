# Source Note: Pipeline ADC Concept

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/10_ch10_Pipeline_ADC概念.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/10_ch10_Pipeline_ADC概念.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch10.pdf
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

Pipeline ADCs split conversion across stages; each stage makes a coarse
decision, subtracts a DAC value, amplifies the residue, and passes the remaining
information to later stages.

## Key Extracted Ideas

- A pipeline stage performs coarse quantization, DAC reconstruction, subtraction
  to form residue, and residue amplification.
- Pipeline reduces hardware compared with high-resolution Flash ADCs.
- Residue represents the part of the input not explained by the current stage.
- Interstage gain controls how the residue fills the next stage range.
- Digital redundancy, such as 1.5-bit/stage, allows limited sub-ADC error
  correction.
- Pipeline has latency but high throughput after the pipeline fills.
- Final output can be interpreted as weighted stage outputs:
  `Dout = d1*w1 + d2*w2 + ...`.

## Integration Into The Wiki

This source supports:

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Least-squares source note](least_squares_calibration_note.md)
- [Pipeline implementation source note](pipeline_adc_implementation_ch11.md)

## Rigor Notes

Pipeline weight calibration has the same linear-combination intuition as SAR
weight calibration, but its physical error sources are MDAC gain, residue path,
sub-DAC levels, and digital alignment rather than only CDAC weights.

## Open Follow-Up

Add a future concept page for stage-weight calibration if ADCToolbox examples
or code paths focus on Pipeline ADC calibration.
