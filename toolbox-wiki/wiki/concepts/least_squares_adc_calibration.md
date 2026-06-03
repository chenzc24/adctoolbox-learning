# Least-Squares ADC Calibration

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/calibration/_lstsq_solver.py
  - ../source_notes/least_squares_calibration_note.md
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Least-squares ADC calibration turns many bit-decision observations into an
estimated set of digital reconstruction weights.

## Core Model

The simplest reconstruction model is:

```text
y_hat[n] = bits[n, :] @ weights + offset
```

Sine-based calibration does not require a known analog target sample by sample.
Instead, it constrains the reconstructed signal to match a sine basis:

```text
bits @ weights + offset + sine_basis @ coeffs ~= 0
```

ADCToolbox variants differ in how much machinery surrounds this idea.

## Lite Versus Full

`calibrate_weight_sine_lite.py` exposes the cleanest model: known frequency,
one dataset, minimal least squares.

`calibrate_weight_sine.py` adds:

- input reshaping and multi-dataset support;
- rank-deficiency patching;
- column conditioning;
- frequency estimation or frequency search;
- harmonic terms;
- result post-processing and diagnostics.

## Identifiability View

The key mathematical question is not "can NumPy return a solution?" It is
"does the design matrix contain enough independent information to identify the
weights we care about?"

The answer depends on:

- bit-column rank;
- input excitation across codes;
- sine frequency and record length;
- offset and harmonic columns;
- noise and residual assumptions;
- redundant-bit architecture.

## Misuse Pattern

A low residual or improved ENOB does not automatically prove that every
physical bit weight was uniquely recovered. It may prove only that the
effective reconstruction space fits the training waveform.

## Related Pages

- [ADC weight calibration](adc_weight_calibration.md)
- [Calibration helper chain](../source_code/calibration_helper_chain_py.md)
- [Lite calibration source](../source_code/calibrate_weight_sine_lite_py.md)
- [Full calibration source](../source_code/calibrate_weight_sine_py.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## Next Reading

Read `rank_deficiency.md` next, because least squares becomes fragile when bit
columns are dependent or nearly dependent.
