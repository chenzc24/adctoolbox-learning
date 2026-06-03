# Example Note: exp_a01_fit_sine_4param

```yaml
stage_link:
  - ../../../wiki/workflows/example_ingest_map.md
source_links:
  - ../../../../../../python/src/adctoolbox/examples/04_debug_analog/exp_a01_fit_sine_4param.py
  - ../../../../../../python/docs/source/examples/expected_output_04_debug_analog.rst
rigor:
  - example-verified
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This example demonstrates that `fit_sine_4param` can recover amplitude, DC
offset, frequency, and phase from a noisy sine wave closely enough for a
controlled synthetic test.

## Example Path

- `python/src/adctoolbox/examples/04_debug_analog/exp_a01_fit_sine_4param.py`
- Expected output summary:
  `python/docs/source/examples/expected_output_04_debug_analog.rst`
- Generated figure:
  `python/src/adctoolbox/examples/04_debug_analog/output/exp_a01_fit_sine_4param.png`

## APIs Used

- `adctoolbox.fit_sine_4param`

## Inputs

- `N = 2**13`
- `Fs = 800e6`
- `Fin = 10.1234567e6`
- amplitude `A = 0.499`
- DC offset `0.5`
- additive Gaussian noise with RMS `20e-3`

## Outputs

- Fitted DC offset, amplitude, normalized frequency, phase, and fitted signal.
- Residual RMS check against injected noise RMS.
- Frequency error, phase error, and reconstruction RMS checks.
- Time-domain figure comparing noisy samples with fitted waveform.

## What This Demonstrates

The example is evidence that the sine-fitting path works for a clean synthetic
case with moderate noise and enough samples. It is the practical bridge between
least-squares sine modeling and the calibration functions that rely on sine
parameters or sine residuals.

## What This Does Not Prove

- It does not prove robustness under strong harmonics, clipping, missing codes,
  drift, or nonstationary noise.
- It does not prove the frequency estimator is unbiased for all coherent and
  non-coherent sampling conditions.
- It does not replace a statistical uncertainty analysis of fitted parameters.

## Related Pages

- [Sine fitting source](../../source_code/fit_sine_4param_py.md)
- [Least-squares ADC calibration](../../concepts/least_squares_adc_calibration.md)
- [Least squares and calibration](../least_squares_calibration_note.md)
- [Identifiability conditions](../../rigor/identifiability_conditions.md)

## Follow-Up

Use this example as evidence in a future workflow page for sine fitting and
residual validation.
