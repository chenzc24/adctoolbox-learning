# `calibrate_weight_sine_lite.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
  - ../../../../../python/docs/source/algorithms/calibrate_weight_sine_lite.md
rigor:
  - source-confirmed
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: high
```

## One-Sentence Takeaway

The lite calibrator is the minimal least-squares form of ADC weight
calibration for a known-frequency sine input.

## Inputs And Output

Input:

```text
bits: shape (N_samples, N_bits), values 0 or 1
freq: normalized Fin/Fs, known accurately
```

Output:

```text
weights: ndarray of length N_bits, normalized and polarity-corrected
```

## Core Model

The function assumes:

```text
bits @ weights = A*cos(2*pi*f*n) + B*sin(2*pi*f*n) + C
```

It chooses a cosine-unity basis:

```text
[bits, 1, sin(2*pi*f*n)] @ [weights, C, B] = -cos(2*pi*f*n)
```

Then it solves this overdetermined system with least squares.

## Implementation Flow

1. Build `cos_basis` and `sin_basis` from the known normalized frequency.
2. Build design matrix `A = [bits, offset_col, sin_basis]`.
3. Solve `A @ coeffs ~= -cos_basis`.
4. Extract raw bit weights from `coeffs`.
5. Normalize by `sqrt(1 + sin_coeff**2)`.
6. Flip polarity if the weight sum is negative.

## Why This Is A Good Learning Entry Point

This file is short and direct. It reveals the mathematical heart of
foreground sine-weight calibration without the additional engineering details
of the full solver.

## Assumptions

- Frequency is known and accurate.
- The bit matrix is well-conditioned.
- The ADC is binary-weighted or at least not rank deficient.
- The input is mainly a single sine.
- Harmonic distortion is not explicitly separated.

## Rigor And Risks

- `source-confirmed`: the least-squares matrix and normalization are directly
  visible in the source.
- `theory-supported`: the method follows standard overdetermined linear least
  squares.
- `open-question`: the function does not quantify uncertainty or condition
  number.
- `open-question`: rank-deficient or redundant bit matrices can produce
  unstable or non-physical weights.

## Related Pages

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Full calibration source](calibrate_weight_sine_py.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Next Reading

After this page, read the full calibrator to see how the project handles
frequency search, dual basis, rank patching, harmonics, and diagnostics.
