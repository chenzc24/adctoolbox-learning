# Example Note: exp_d16_sar_unit_cap_mismatch_mc

```yaml
stage_link:
  - ../../../wiki/workflows/example_ingest_map.md
source_links:
  - ../../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
rigor:
  - example-source-reviewed
  - statistical-simulation
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This example compares strict binary and radix-approximately-1.8 SAR weight
lists under Pelgrom-style unit-cap mismatch using Monte Carlo ENOB envelopes.

## Example Path

- `python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py`
- Generated figure:
  `python/src/adctoolbox/examples/05_debug_digital/output/exp_d16_sar_unit_cap_mismatch_mc.png`

## APIs Used

- `adctoolbox.analyze_weight_radix`
- `adctoolbox.calibrate_weight_sine`
- `adctoolbox.quick_sndr`
- `adctoolbox.sar_apply_cap_mismatch`
- `adctoolbox.sar_convert`
- `adctoolbox.sar_ideal_weights`
- `adctoolbox.sar_reconstruct`

## Inputs

- 16-bit strict binary weights.
- 16-bit redundant integer weight list with average radix near `1.8`.
- Pelgrom-style capacitor mismatch sweep from `0%` to `10%` sigma.
- `32` Monte Carlo trials per mismatch point.
- Separate training and test tones.

## Outputs

- ENOB distributions before and after foreground calibration.
- Median lines plus min/max and percentile envelopes for strict binary and
  redundant architectures.
- A figure comparing mismatch tolerance across architectures and calibration
  states.

## What This Demonstrates

This is the first example evidence note that treats calibration as a
statistical experiment rather than a single happy-path demo. It links mismatch
sigma, architecture choice, calibration, and ENOB distribution.

## What This Does Not Prove

- It does not prove a closed-form probability of calibration success.
- It does not prove the chosen radix-1.8 list is optimal.
- It does not prove independence from training tone, test tone, amplitude, or
  solver settings.
- It summarizes ENOB distributions, but does not yet record rank, condition
  number, or singular-value distributions.

## Related Pages

- [SAR model source](../../source_code/sar_py.md)
- [Full sine-weight calibration source](../../source_code/calibrate_weight_sine_py.md)
- [ADC weight calibration](../../concepts/adc_weight_calibration.md)
- [Rank deficiency](../../concepts/rank_deficiency.md)
- [Identifiability conditions](../../rigor/identifiability_conditions.md)

## Follow-Up

Extend this evidence with rank/condition-number logging so the Monte Carlo
result can support a rigorous calibration-success argument.
