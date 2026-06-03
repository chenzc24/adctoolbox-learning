# Example Note: exp_d01_cal_weight_sine_lite

```yaml
stage_link:
  - ../../../wiki/workflows/example_ingest_map.md
source_links:
  - ../../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d01_cal_weight_sine_lite.py
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

This example demonstrates a fast sine-based bit-weight calibration flow and
compares before/after spectra for a SAR-like ADC with an injected MSB mismatch.

## Example Path

- `python/src/adctoolbox/examples/05_debug_digital/exp_d01_cal_weight_sine_lite.py`
- Expected output summary:
  `python/docs/source/examples/expected_output_05_debug_digital.rst`
- Generated figure:
  `python/src/adctoolbox/examples/05_debug_digital/output/exp_d01_cal_weight_sine_lite.png`

## APIs Used

- `adctoolbox.freq_to_bin`
- `adctoolbox.analyze_spectrum`
- `adctoolbox.calibration.calibrate_weight_sine_lite`

## Inputs

- `n_samples = 2**13`
- `fs = 1e9`
- coherent input near `80 MHz`
- 12-bit SAR-like decision matrix
- nominal binary capacitor weights
- injected `-1%` MSB capacitor mismatch

## Outputs

- Recovered bit weights from `calibrate_weight_sine_lite`.
- Calibrated digital reconstruction.
- Before/after spectrum overlay.
- Before/after SNDR, ENOB, SFDR, SNR, NSD, noise floor, and signal power.
- Console summary showing a large ENOB/SNDR improvement in the synthetic case.

## What This Demonstrates

The example is evidence for the practical calibration loop:

```text
inject known SAR weight mismatch
  -> collect bit-decision matrix under sine excitation
  -> solve effective weights
  -> reconstruct calibrated signal
  -> compare FFT metrics before and after calibration
```

It is especially useful as a minimal learner path because it keeps the
calibration model simple and puts the result directly in spectrum terms.

## What This Does Not Prove

- It does not prove the recovered weights are unique under arbitrary bit
  activity or frequency choices.
- It does not prove the manual SNDR calculation in the script is equivalent to
  the spectrum-derived SNDR under all normalization choices.
- It does not cover rank-deficient or strongly redundant cases.
- It does not prove real silicon behavior because the nonideality is synthetic.

## Related Pages

- [Lite calibration source](../../source_code/calibrate_weight_sine_lite_py.md)
- [ADC weight calibration](../../concepts/adc_weight_calibration.md)
- [SAR model to calibration](../../workflows/sar_model_to_calibration.md)
- [Spectrum validation before and after calibration](../../workflows/spectrum_validation_before_after_calibration.md)
- [Identifiability conditions](../../rigor/identifiability_conditions.md)

## Follow-Up

Use this example in a future validation-split workflow: train weights on one
sine record and validate spectrum metrics on another record.
