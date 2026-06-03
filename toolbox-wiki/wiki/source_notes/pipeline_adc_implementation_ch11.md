# Source Note: Pipeline ADC Implementation

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/11_ch11_Pipeline_ADC实现.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/11_ch11_Pipeline_ADC实现.md
rigor:
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Pipeline implementation centers on the MDAC, where capacitor ratios, op-amp
gain/bandwidth, settling, noise, and DAC errors determine residue accuracy and
therefore calibration needs.

## Key Extracted Ideas

- A typical stage includes sample/hold, sub-ADC, sub-DAC, subtractor, and
  residue amplifier.
- MDAC combines DAC generation and residue amplification.
- Switched-capacitor MDAC behavior depends on capacitor ratios.
- Ideal residue can be written as `Vres = G*(Vin - Vdac)`.
- Finite op-amp gain creates closed-loop gain error.
- Finite bandwidth and slew rate create dynamic settling errors.
- Capacitor mismatch changes both MDAC gain and DAC levels.
- Noise reduces SNR and cannot be simply calibrated away.
- Digital redundancy corrects limited comparator and residue errors, but not
  severe saturation, nonlinearity, or overload.
- Weight calibration can be written as `Dout_corrected = sum d_i*w_i_actual`.

## Integration Into The Wiki

This source supports:

- [Pipeline concept source note](pipeline_adc_concept_ch10.md)
- [Switched-capacitor settling and noise](switched_cap_settling_noise_ch6.md)
- [Matrix rank and observability](matrix_rank_observability_note.md)

## Rigor Notes

Pipeline calibration is not abstract least squares detached from hardware. The
unknown weights correspond to actual MDAC gain, capacitor mismatch, residue
path, and stage alignment errors.

## Open Follow-Up

Add an evidence note if ADCToolbox includes or later adds Pipeline-specific
calibration examples.
