# Example Ingest Map

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/README.md
source_links:
  - ../../../../../python/src/adctoolbox/examples/README.md
rigor:
  - example-verified
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This page is the structural queue for turning ADCToolbox examples into
source-note evidence pages.

## Purpose

Examples should not remain as isolated scripts. Each important example should
be ingested into `wiki/source_notes/` so future answers can distinguish what an
example demonstrates from what it does not prove.

## Example Note Location

Use:

```text
wiki/source_notes/examples/
```

Use `schema/EXAMPLE_NOTE_TEMPLATE.md` for every new example note.

## Priority Queue

- done: `examples/04_debug_analog/exp_a01_fit_sine_4param.py`
  -> [Example: sine fit 4-parameter](../source_notes/examples/exp_a01_fit_sine_4param.md)
- done: `examples/05_debug_digital/exp_d01_cal_weight_sine_lite.py`
  -> [Example: lite sine weight calibration](../source_notes/examples/exp_d01_cal_weight_sine_lite.md)
- done: `examples/05_debug_digital/exp_d02_cal_weight_sine.py`
  -> [Example: full sine weight calibration](../source_notes/examples/exp_d02_cal_weight_sine.md)
- `examples/05_debug_digital/exp_d03_redundancy_comparison.py`
- `examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py`
- `examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py`

## Required Links Per Example

Each example note should link to:

- one source-code page;
- one concept page;
- one workflow or rigor page;
- any output artifact or metric definition it relies on.

## What This Map Does Not Do

This page does not ingest the examples itself. It only defines the queue and
required structure.

## Related Pages

- [SAR model to calibration workflow](sar_model_to_calibration.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)
