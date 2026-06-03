# Source Note: Sun Course Pipeline Primary PDF Distillation

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/10_ch10_Pipeline_ADC概念.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/11_ch11_Pipeline_ADC实现.md
source_links:
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch10.pdf
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch11.pdf
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/10_ch10_Pipeline_ADC概念.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/11_ch11_Pipeline_ADC实现.md
rigor:
  - source-confirmed
  - primary-source-direct-distilled
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

The original Pipeline PDFs explain calibration as a consequence of residue
generation: sub-ADC errors, interstage gain error, sub-DAC error, capacitor
matching, amplifier error, and digital correction all affect the final code.

## Direct PDF Distillation

- Pipeline ADCs turn sequential conversion delay into latency by adding a
  sample-and-hold after each stage.
- A stage performs coarse quantization, subtracts a DAC reconstruction, then
  amplifies the residue for later stages.
- Pipeline speed is limited by one stage delay, while total conversion latency
  increases with the number of stages.
- With ideal DACs and matched analog/digital gains, earlier-stage quantization
  errors can be suppressed by downstream gain.
- Effective stage resolution can be represented by `log2(G)`, so stage gain is
  directly tied to resolution contribution.
- Sub-ADC errors can overload the backend unless redundancy or extra decision
  range keeps the residue inside the allowable region.
- Amplifier offset can often be referred to input as global offset or absorbed
  as sub-ADC offset when redundancy is present.
- Analog gain error is not fatal if the digital gain used for reconstruction
  matches the actual analog gain.
- DAC calibration can be done by sweeping DAC codes and using the backend ADC
  to measure transition errors.
- Recursive foreground calibration can start from the least significant stage
  needing calibration and move toward the first stage.
- Background calibration is needed when errors drift with temperature, aging,
  or operating condition.
- Implementation limits include capacitor matching, OTA finite gain, settling
  error, thermal noise, front-end SHA versus SHA-less timing mismatch, and
  comparator offset/noise.

## Calibration Meaning

Pipeline calibration is not only a software correction table. It reflects this
physical chain:

```text
sub-ADC decision + sub-DAC reconstruction
  -> residue
  -> interstage gain
  -> backend measurement
  -> digital correction or coefficient update
```

This differs from a simple SAR weight model because a Pipeline stage can have
both local quantization decisions and analog residue dynamics. The same final
code error may arise from gain error, DAC transition error, finite amplifier
gain, settling, or residue nonlinearity.

## Integration Into The Wiki

This source supports:

- [Pipeline ADC concept](pipeline_adc_concept_ch10.md)
- [Pipeline ADC implementation](pipeline_adc_implementation_ch11.md)
- [ADC physical system structure DOCX](adc_physical_system_structure_docx.md)
- [ADC test analysis and calibration PDF](adc_test_analysis_calibration_pdf.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## Rigor Notes

- Matching digital gain to analog gain is an identifiability claim: the backend
  measurement must contain enough information to estimate the analog gain.
- Redundancy in Pipeline stages should be stated as a residue-range condition,
  not as a vague "extra bit" statement.
- A lookup-table DAC calibration can correct repeatable transition errors, but
  it does not automatically correct drift or dynamic residue nonlinearity.
- A stage-level calibration result should state whether it is foreground or
  background, whether it interrupts normal conversion, and what errors can
  drift after calibration.

## Open Follow-Up

Create a concept page on effective Pipeline stage gain, residue-range
redundancy, and backend-observable calibration parameters.
