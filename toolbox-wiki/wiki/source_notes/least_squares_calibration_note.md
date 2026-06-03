# Source Note: Least Squares From Overdetermined Equations To Calibration

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/fundamentals/fit_sine_4param.py
rigor:
  - source-confirmed
  - theory-supported
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This raw note gives the mathematical foundation for ADC calibration as an
overdetermined least-squares problem.

## Key Extracted Ideas

- Real measurements are noisy, so exact equations are usually impossible.
- Least squares chooses the parameter vector that minimizes residual energy.
- The normal-equation view is `A.T A x = A.T y`, but stable implementations
  usually prefer QR, SVD, or library least-squares solvers.
- In ADC calibration, rows of the design matrix can come from bit decisions,
  while unknowns can be bit weights and sine parameters.
- Noise assumptions matter. Biased or correlated noise can bias the solution.
- A model can underfit systematic error or overfit random noise.

## Integration Into The Wiki

This source supports:

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [fit_sine_4param source](../source_code/fit_sine_4param_py.md)
- [Lite calibration source](../source_code/calibrate_weight_sine_lite_py.md)
- [Full calibration source](../source_code/calibrate_weight_sine_py.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## Rigor Notes

Least squares is not automatically a proof of correct calibration. The design
matrix must have enough independent information, and residual assumptions must
match the experiment.

## Open Follow-Up

Add a small numerical example showing a full-rank bit matrix, a rank-deficient
bit matrix, and a poorly conditioned bit matrix.
