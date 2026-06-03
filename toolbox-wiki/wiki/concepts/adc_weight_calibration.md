# ADC Weight Calibration

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/models/sar.py
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC weight calibration estimates the true digital reconstruction weights so a
raw bit-decision matrix can be converted into a better analog estimate.

## Why This Matters

For SAR and bit-weighted ADCs, capacitor mismatch or architecture redundancy
means the nominal binary weights are not always the weights that best
reconstruct the sampled input. ADCToolbox uses sine-wave foreground calibration
to estimate those weights from data.

## Core Model

The central reconstruction model is:

```text
aout[n] = sum_i bits[n, i] * weight[i]
```

For sine calibration, ADCToolbox fits that weighted sum to a sine basis:

```text
sum_i bits[n, i] * weight[i]
  ~= A*cos(2*pi*f*n) + B*sin(2*pi*f*n) + offset
```

The full calibration can add harmonic basis terms and frequency refinement.

## Project Mapping

- `sar_convert` generates raw bit decisions from an analog SAR model.
- `sar_reconstruct` applies a chosen digital weight list to those bits.
- `calibrate_weight_sine_lite` solves a minimal least-squares calibration when
  the sine frequency is known.
- `calibrate_weight_sine` adds frequency estimation, rank-deficiency handling,
  harmonic terms, conditioning, and diagnostics.

## Explanation

The calibration problem is a bridge between ADC architecture and linear
algebra. The ADC gives many observations: each sample has a row of 0/1 bit
decisions. If the input is a clean sine, the correct weighted sum of those bits
should look like that sine plus an offset. The unknowns are the bit weights and
the sine coefficients.

This creates an overdetermined linear system: many samples, relatively few
unknown weights. Least squares finds the weights that make the reconstructed
waveform closest to the fitted sine model.

## Assumptions

- The bit matrix contains enough variation to identify the weights.
- The input training signal is mainly a single sine tone.
- The digital output can be modeled as a linear weighted sum of bit decisions.
- Frequency is known or can be estimated accurately enough.
- Residual errors not explained by weights are acceptable as noise/distortion,
  or explicitly modeled with harmonic basis terms.

## Rigor And Risks

- `source-confirmed`: the weighted-sum reconstruction is directly implemented
  by `sar_reconstruct`.
- `source-confirmed`: the lite calibration constructs a least-squares system
  from `[bits, offset, sine_basis]`.
- `engineering-heuristic`: harmonic rejection and rank patching improve
  practical behavior, but do not by themselves prove production-grade
  calibration correctness.
- `open-question`: a full proof of identifiability requires conditions on the
  bit matrix rank, training signal coverage, frequency, and noise model.

## Related Pages

- [SAR model source](../source_code/sar_py.md)
- [Lite calibration source](../source_code/calibrate_weight_sine_lite_py.md)
- [Full calibration source](../source_code/calibrate_weight_sine_py.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)

## Next Reading

Read `calibrate_weight_sine_lite_py.md` before the full calibration page. The
lite version is the cleanest way to see the least-squares idea.
