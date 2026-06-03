# Source Note: Low-Power SAR ADC Chapter

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
  - ../../../../../python/src/adctoolbox/models/sar.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch12 - low power.pdf
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

This raw note connects the SAR decision process, capacitor DAC weights, noise,
switching energy, and calibration-relevant capacitor mismatch.

## Key Extracted Ideas

- SAR conversion is a bit-by-bit search using a DAC hypothesis and comparator
  decision.
- A capacitive DAC is common because it can both sample and generate trial
  voltages.
- Larger capacitors reduce kT/C noise and mismatch, but increase area and
  switching energy.
- Comparator noise and decision speed trade against power.
- Low-power SAR design often reduces reference switching energy through
  switching-scheme choices.
- Capacitor mismatch changes the actual bit weights, making digital weight
  calibration useful.

## Integration Into The Wiki

This source supports:

- [SAR model source](../source_code/sar_py.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## Rigor Notes

The ADCToolbox SAR model captures the bit-decision and weight-mismatch view,
but it does not fully model switching energy, DAC settling, comparator
metastability, charge injection, or reference transient behavior.

## Open Follow-Up

Create a richer SAR modeling gap page that separates calibration-relevant
weight mismatch from circuit-level effects that require another model.
