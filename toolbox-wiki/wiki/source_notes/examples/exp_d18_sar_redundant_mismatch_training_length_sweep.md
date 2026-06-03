# Example Note: exp_d18_sar_redundant_mismatch_training_length_sweep

```yaml
stage_link:
  - ../../../wiki/workflows/example_ingest_map.md
source_links:
  - ../../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
rigor:
  - example-source-reviewed
  - statistical-simulation
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This example directly demonstrates why calibration needs an independent
validation capture: short training records can look good on the training data
while failing on a separate test capture.

## Example Path

- `python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py`
- Generated figures:
  - `python/src/adctoolbox/examples/05_debug_digital/output/exp_d18_sar_redundant_mismatch_training_length_sweep.png`
  - `python/src/adctoolbox/examples/05_debug_digital/output/exp_d18_sar_redundant_mismatch_training_capture_overfit.png`
  - `python/src/adctoolbox/examples/05_debug_digital/output/exp_d18_sar_redundant_mismatch_training_capture_overlay.png`

## APIs Used

- `adctoolbox.calibrate_weight_sine`
- `adctoolbox.quick_sndr`
- `adctoolbox.sar_apply_cap_mismatch`
- `adctoolbox.sar_convert`

## Inputs

- Redundant 16-bit radix-approximately-1.8 SAR weight list.
- Unit-cap mismatch sigma of `1%`.
- Training lengths from very short records through `2**14`, with additional
  short-record points.
- `32` Monte Carlo trials.
- Independent fixed-length test capture.
- Different mismatch realizations and sine starting phases.

## Outputs

- Calibrated ENOB distribution versus training length on independent test data.
- Calibrated ENOB distribution versus training length on the calibration
  capture itself.
- Overlay plot that exposes ill-conditioned and overfitting regions.

## What This Demonstrates

This example is one of the most important rigor anchors in the codebase. It
turns the general warning "do not overfit calibration data" into a concrete
ADC calibration experiment.

The conceptual chain is:

```text
too few calibration samples
  -> underdetermined or ill-conditioned weight solve
  -> training-capture metric can look optimistic
  -> independent test capture reveals generalization failure
```

## What This Does Not Prove

- It does not derive the exact minimum sample count required for all SAR
  architectures.
- It does not report design-matrix singular values, so the ill-conditioning
  label is empirical rather than formally quantified.
- It does not test all input frequencies, amplitudes, or mismatch models.
- It does not prove that the chosen validation metric is sufficient by itself.

## Related Pages

- [Full sine-weight calibration source](../../source_code/calibrate_weight_sine_py.md)
- [Calibration helper chain](../../source_code/calibration_helper_chain_py.md)
- [Identifiability conditions](../../rigor/identifiability_conditions.md)
- [Spectrum metric statistical risks](../../rigor/spectrum_metric_statistical_risks.md)
- [SAR model to calibration](../../workflows/sar_model_to_calibration.md)
- [SAR reachability example weight audit](../../../audits/sar_reachability_example_weight_audit_2026-06-03.md)

## Follow-Up

Promote `wiki/workflows/training_validation_split.md` from planned to written
using this example as the primary evidence page.
