# Source Note: Vectors, Matrices, And Linear Combinations

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/01_向量矩阵与线性组合.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/01_向量矩阵与线性组合.md
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
rigor:
  - source-confirmed
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC calibration starts from linear combinations: bit or stage decisions form
vectors, physical weights form another vector, and their dot product produces a
digital reconstruction.

## Key Extracted Ideas

- SAR output can be written as `D = b1*w1 + b2*w2 + ... + bN*wN`.
- Pipeline output can be written as `D = d1*w1 + d2*w2 + ...`.
- A single conversion uses a code vector `b` and weight vector `w`.
- Reconstruction is the inner product `D = b dot w`.
- Many conversions can be stacked into `A x = y`.
- Matrix `A` represents which bit or stage combinations were observed.
- Unknown vector `x` represents the real circuit weights or parameters.
- Calibration estimates the underlying weights, not just individual output
  codes.

## Integration Into The Wiki

This source supports:

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Least-squares source note](least_squares_calibration_note.md)
- [Matrix rank and observability](matrix_rank_observability_note.md)

## Rigor Notes

This is the conceptual base for reading ADCToolbox calibration code. It also
explains why the bit matrix must contain enough varied rows for calibration to
be meaningful.

## Open Follow-Up

Create `wiki/concepts/least_squares_adc_calibration.md` as the polished concept
page that combines this note, rank, and least squares.
