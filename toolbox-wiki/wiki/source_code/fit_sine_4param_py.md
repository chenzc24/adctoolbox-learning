# `fit_sine_4param.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/fundamentals/fit_sine_4param.py
  - ../../../../../python/docs/source/algorithms/fit_sine_4param.md
  - ../../../../../python/src/adctoolbox/examples/04_debug_analog/exp_a01_fit_sine_4param.py
rigor:
  - source-confirmed
  - example-verified
  - theory-supported
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

`fit_sine_4param.py` estimates the best single-tone sine model for ADC data,
then uses the residuals as the part not explained by that ideal sine.

## Public API Purpose

`fit_sine_4param(data, frequency_estimate=None, max_iterations=1, tolerance=1e-9)`
returns:

- `fitted_signal`
- `residuals`
- `frequency`
- `amplitude`
- `phase`
- `dc_offset`
- `rmse`

For 2D input, each column is fit separately and scalar outputs become arrays.

## Core Model

The fixed-frequency model is:

```text
y[n] = A*cos(2*pi*f*n) + B*sin(2*pi*f*n) + C + residual[n]
```

When refinement is enabled, the next iterations add a frequency-correction
column derived from the derivative of the sine model with respect to frequency.

## Core Data Flow

```text
data
  -> optional FFT/parabolic initial frequency estimate
  -> least-squares fit of cos, sin, DC
  -> optional frequency-correction iterations
  -> fitted sine
  -> residuals and RMSE
```

## Why This Matters For ADC Learning

Sine fitting is the time-domain counterpart of spectrum analysis. It separates
the ideal single-tone component from residual error. Many ADC debug tools then
analyze the residual by time, value, phase, histogram, or spectrum.

In calibration, the same least-squares thinking appears again: choose a model,
build a design matrix, solve parameters, and interpret the residual.

## Assumptions

- The dominant input is a single sine tone.
- Initial frequency is close enough for refinement to converge.
- Residuals represent distortion, noise, or model mismatch rather than another
  intended signal.
- The sample record is long enough to distinguish frequency, phase, and DC.

## Rigor And Risks

- `source-confirmed`: the design matrix and frequency update are visible in the
  source.
- `example-verified`: `exp_a01_fit_sine_4param.py` demonstrates usage.
- `theory-supported`: the method follows least-squares sine fitting ideas used
  in ADC testing.
- `open-question`: the current page does not yet derive convergence radius,
  estimator variance, or bias under harmonic distortion.

## Related Pages

- [Least-squares source note](../source_notes/least_squares_calibration_note.md)
- [FFT sampling source note](../source_notes/fft_sampling_note.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Next Reading

Read the residual-analysis modules after this page, because the fitted sine is
mainly useful when its residual is interpreted carefully.
