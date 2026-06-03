# Mathematical Rigor Gaps

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/calibration/_lstsq_solver.py
  - ../../../../../python/src/adctoolbox/calibration/_patch_rank_deficiency.py
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/models/sar.py
rigor:
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADCToolbox has a sound learning and prototyping direction, but the wiki should
track the mathematical conditions that are not yet proven or quantified.

## Main Gaps

### 1. Identifiability

The calibration system estimates weights from a bit matrix and sine basis.
For a unique, stable estimate, the effective design matrix must have adequate
rank and conditioning. The project patches rank deficiency, but a full theorem
of when weights are uniquely recoverable is not supplied.

### 2. Estimator Uncertainty

The calibrator returns one weight vector, but not confidence intervals,
covariance, condition number, or residual whiteness diagnostics. Without these,
the learner can see that a solution exists but not how stable it is.

### 3. Frequency-Weight Coupling

Frequency error can be absorbed into weights, phase, offset, or harmonic terms.
The full solver refines frequency, but the project does not yet provide a
formal error propagation analysis from frequency error to weight bias.

### 4. Harmonic Attribution

Including harmonic terms can make calibration residuals smaller, but harmonic
content may come from input-source distortion, static ADC nonlinearity, or bit
weight mismatch. The current workflow should treat this as an engineering
choice, not a complete attribution proof.

### 5. Redundant SAR Reachability

`analyze_weight_radix` and effective span are useful, but they do not prove
SAR reachability, no missing codes, DNL/INL, or successful correction after an
early wrong decision.

### 6. Spectrum Metric Statistics

ENOB, SNDR, SFDR, and THD depend on FFT length, coherence, window, side-bin
selection, harmonic folding, and noise-floor estimation. The implementation is
useful, but a single metric result is not a confidence interval.

### 7. Model Mismatch

The SAR model excludes or simplifies effects such as DAC settling,
metastability, reference transient behavior, charge injection, drift, and PVT.
These may break the static weight model.

## What The Project Currently Does Well

- Provides a clear behavior-model-to-calibration workflow.
- Separates actual SAR analog weights from digital reconstruction weights.
- Implements a minimal least-squares calibrator and a fuller robust wrapper.
- Provides examples that compare before/after calibration performance.
- Documents many key return shapes and conventions.

## What Would Make It More Rigorous

- Report design matrix rank, condition number, and singular values.
- Report weight covariance or bootstrap confidence intervals.
- Use train/test split systematically.
- Validate across frequency, amplitude, noise, and mismatch corners.
- Add explicit redundant SAR reachability checks.
- Provide source distortion checks or independent input-source model.
- Add residual diagnostics: whiteness, autocorrelation, code dependence, and
  phase/value dependence.

## Related Pages

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Full calibration source](../source_code/calibrate_weight_sine_py.md)
- [SAR model source](../source_code/sar_py.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)

## Next Validation Questions

- How does calibrated weight error scale with sample count?
- How sensitive are weights to frequency error?
- When does harmonic rejection improve weights, and when does it mask weight
  mismatch?
- Can a redundant weight list be certified for reachability and no missing
  codes from weights alone?
