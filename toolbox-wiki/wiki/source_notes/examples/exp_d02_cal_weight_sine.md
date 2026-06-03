# Example Note: exp_d02_cal_weight_sine

```yaml
stage_link:
  - ../../../wiki/workflows/example_ingest_map.md
source_links:
  - ../../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d02_cal_weight_sine.py
  - ../../../../../../python/docs/source/examples/expected_output_05_debug_digital.rst
rigor:
  - example-verified
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This example demonstrates the full `calibrate_weight_sine` path on a SAR-like
decision matrix, including calibrated reconstruction, spectrum comparison, and
weight-error comparison against known synthetic truth.

## Example Path

- `python/src/adctoolbox/examples/05_debug_digital/exp_d02_cal_weight_sine.py`
- Expected output summary:
  `python/docs/source/examples/expected_output_05_debug_digital.rst`
- Generated figures:
  - `python/src/adctoolbox/examples/05_debug_digital/output/exp_d02_cal_weight_sine.png`
  - `python/src/adctoolbox/examples/05_debug_digital/output/exp_d02_weight_error_comparison.png`

## APIs Used

- `adctoolbox.freq_to_bin`
- `adctoolbox.calibrate_weight_sine`
- `adctoolbox.analyze_spectrum`

## Inputs

- `n_samples = 2**13`
- `fs = 1e9`
- coherent input near `300 MHz`
- nominal 12-bit SAR-style capacitor array with repeated LSB/comparator bit
- injected `-1%` MSB mismatch
- normalized nominal reconstruction weights

## Outputs

- Calibrated signal from `results['calibrated_signal'][0]`.
- Calibrated weight vector from `results['weight']`.
- Before/after spectrum figures.
- Weight error bar plot comparing nominal error and calibrated error.
- Expected output reports ENOB improvement from roughly 8 bits to roughly 12
  bits in the synthetic case.

## What This Demonstrates

The example is evidence that the full calibration API can recover useful
effective weights for a simple SAR mismatch case and that spectrum validation
can show a major improvement after reconstruction.

It also demonstrates a subtle bookkeeping issue: `calibrate_weight_sine` returns
weights in a differential convention, while the example normalizes them for
single-ended comparison.

## What This Does Not Prove

- It does not prove the calibration is identifiable for all redundant SAR
  arrays.
- It does not prove the last-bit/comparator convention is universal.
- It does not test training/validation separation; the same synthetic scenario
  supplies calibration and demonstration.
- It does not prove that a good weight match diagnoses the exact physical
  capacitor mismatch source.

## Related Pages

- [Full sine-weight calibration source](../../source_code/calibrate_weight_sine_py.md)
- [Calibration helper chain](../../source_code/calibration_helper_chain_py.md)
- [Rank deficiency patch source](../../source_code/patch_rank_deficiency_py.md)
- [ADC weight calibration](../../concepts/adc_weight_calibration.md)
- [Rank deficiency](../../concepts/rank_deficiency.md)
- [Identifiability conditions](../../rigor/identifiability_conditions.md)

## Follow-Up

Use this example as the baseline evidence page for `training_validation_split`
and `least_squares_uncertainty` pages.
