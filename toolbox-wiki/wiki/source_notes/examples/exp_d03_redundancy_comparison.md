# Example Note: exp_d03_redundancy_comparison

```yaml
stage_link:
  - ../../../wiki/workflows/example_ingest_map.md
source_links:
  - ../../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d03_redundancy_comparison.py
  - ../../../../../../python/docs/source/examples/expected_output_05_debug_digital.rst
rigor:
  - example-verified
  - theory-supported
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This example compares sine-weight calibration with and without redundant
weights under positive and negative MSB mismatch.

## Example Path

- `python/src/adctoolbox/examples/05_debug_digital/exp_d03_redundancy_comparison.py`
- Expected output summary:
  `python/docs/source/examples/expected_output_05_debug_digital.rst`
- Generated figures:
  - `python/src/adctoolbox/examples/05_debug_digital/output/exp_d03_redundancy_comparison.png`
  - `python/src/adctoolbox/examples/05_debug_digital/output/exp_d03_weight_error_comparison.png`

## APIs Used

- `adctoolbox.freq_to_bin`
- `adctoolbox.calibrate_weight_sine`
- `adctoolbox.analyze_spectrum`

## Inputs

- `n_samples = 2**13`
- `fs = 1e9`
- coherent input near `300 MHz`
- four cases:
  strict binary with `-2%` MSB mismatch;
  strict binary with `+2%` MSB mismatch;
  redundant list with `-2%` MSB mismatch;
  redundant list with `+2%` MSB mismatch.

## Outputs

- Before/after spectrum plots for each case.
- Weight-error comparison plots.
- Expected output shows that the redundant cases recover close to 12-bit ENOB
  for both mismatch signs, while the strict binary positive mismatch case
  recovers less well.

## What This Demonstrates

This example is evidence that redundancy can improve calibration tolerance, but
the direction and structure of mismatch still matter. It is also a good prompt
for asking what "redundancy" mathematically guarantees.

## What This Does Not Prove

- It does not prove a general reachability theorem for redundant SAR weights.
- It does not prove that every redundant list improves every mismatch case.
- It does not separate code-span redundancy, decision reachability, and
  calibration identifiability.
- It uses synthetic single-tone foreground calibration, not a production
  calibration protocol.

## Related Pages

- [Full sine-weight calibration source](../../source_code/calibrate_weight_sine_py.md)
- [Rank deficiency](../../concepts/rank_deficiency.md)
- [Identifiability conditions](../../rigor/identifiability_conditions.md)
- [Mathematical rigor gaps](../../rigor/mathematical_rigor_gaps.md)
- [SAR model to calibration](../../workflows/sar_model_to_calibration.md)
- [SAR reachability example weight audit](../../../audits/sar_reachability_example_weight_audit_2026-06-03.md)

## Follow-Up

Use this example as the starting evidence for
`wiki/rigor/redundant_sar_reachability.md`.
