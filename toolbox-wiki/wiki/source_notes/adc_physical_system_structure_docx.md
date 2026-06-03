# Source Note: ADC Physical System Structure DOCX

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/ADC工作物理系统结构.docx
source_links:
  - ../../raw/resources/ADCtoolbox/ADC工作物理系统结构.docx
  - ../../../../../python/src/adctoolbox/models/sar.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
rigor:
  - source-confirmed
  - learner-note
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This DOCX is a physical-structure bridge from sampling, hold behavior, residue
amplification, multi-stage quantization, code assembly, and bit-weight
calibration to the behavioral abstractions used by ADCToolbox.

## Key Extracted Ideas

- Sampling and hold circuits are the boundary between analog input and digital
  conversion logic.
- Track-and-hold behavior depends on acquisition time, RC settling, bandwidth,
  switch behavior, and capacitor noise.
- Quantization is not only a numerical rounding operation; it is implemented by
  physical comparators, DACs, residue paths, and digital decision logic.
- Pipeline ADCs rely on residue generation and amplification; errors in residue
  gain or stage decisions appear as digital weight and correction problems.
- SAR ADCs rely on CDAC decisions; mismatch and settling errors perturb the
  effective bit weights.
- Multi-stage quantization and code stitching require a consistent mapping from
  physical decisions to final digital code.
- Weight calibration is the mathematical layer that tries to recover the
  effective physical weights seen by the converter.

## Integration Into The Wiki

This source supports:

- [SAR model source](../source_code/sar_py.md)
- [Full sine-weight calibration source](../source_code/calibrate_weight_sine_py.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Low-power SAR ADC](sar_low_power_ch12a.md)
- [High-speed SAR ADC](high_speed_sar_ch12b.md)
- [Pipeline ADC concept](pipeline_adc_concept_ch10.md)
- [Pipeline ADC implementation](pipeline_adc_implementation_ch11.md)
- [Sampling circuit](sampling_circuit_ch5.md)
- [Switched-capacitor settling and noise](switched_cap_settling_noise_ch6.md)

## ADCToolbox Learning Meaning

This source helps prevent a common learning mistake: treating `bits` and
`weights` as purely software variables. In ADCToolbox, a bit matrix or code
matrix is a compressed representation of physical decisions made by a converter.

The important bridge is:

```text
sampling and hold error
  -> comparator / CDAC / residue decision error
  -> effective bit or stage weight error
  -> least-squares parameter estimation
  -> corrected digital reconstruction
```

## Rigor Notes

- Physical causality matters. A calibration model should state which physical
  errors it can represent and which errors it only hides in residuals.
- A single effective weight can absorb multiple circuit errors, but that does
  not prove the underlying physical error was uniquely identified.
- For Pipeline ADCs, stage-gain, residue nonlinearity, and digital correction
  can be coupled. A source-code page should avoid presenting one solved weight
  vector as a complete circuit diagnosis.

## Open Follow-Up

Create a concept page on "effective digital weights versus physical circuit
parameters" before promoting weight-calibration explanations to `stable`.
