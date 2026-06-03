# `calibrate_weight_sine.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/calibration/_lstsq_solver.py
  - ../../../../../python/src/adctoolbox/calibration/_patch_rank_deficiency.py
  - ../../../../../python/src/adctoolbox/calibration/_post_process.py
  - ../../../../../python/docs/source/algorithms/calibrate_weight_sine.md
  - ../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d02_cal_weight_sine.py
  - ../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
rigor:
  - source-confirmed
  - example-verified
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

The full sine-weight calibrator is a robust engineering wrapper around the
least-squares calibration idea, adding frequency handling, rank patching,
conditioning, harmonic terms, and diagnostics.

## Public API Purpose

`calibrate_weight_sine(bits, freq=None, ...)` estimates per-bit weights from
raw bit decisions captured under a sine input.

It returns a dictionary containing:

- `weight`
- `offset`
- `calibrated_signal`
- `ideal`
- `error`
- `refined_frequency`
- `snr_db`
- `enob`

## Pipeline

The wrapper delegates to helper modules:

```text
bits
  -> _prepare_input
  -> _patch_rank_deficiency
  -> _scale_columns_for_conditioning
  -> _estimate_frequencies
  -> _solve_weights_searching_freq OR _solve_weights_with_known_freq
  -> recover scaling
  -> recover rank deficiency
  -> _post_process
  -> result dict
```

## What Full Adds Beyond Lite

- Supports unknown frequency through coarse estimation and optional refinement.
- Tries both cosine-unity and sine-unity basis choices.
- Handles multi-dataset calibration.
- Adds harmonic basis terms through `harmonic_order`.
- Patches rank-deficient bit matrices.
- Scales columns for numerical conditioning.
- Returns diagnostics and reconstructed signals, not only weights.

## Rank Deficiency Handling

The rank patcher detects dependent or constant bit columns. Independent
columns remain as effective columns. Dependent columns are merged into an
effective column using nominal-weight ratios, then recovered back to physical
bit positions after solving.

This is important for redundant SAR architectures where multiple physical bits
may not be independently observable in the training data.

## Harmonic Terms

The solver can add multiple sine/cosine harmonic bases. This can prevent
harmonic distortion from being treated entirely as weight error, but it also
introduces an attribution question: some harmonic content may come from weight
mismatch, source distortion, or static nonlinearity.

## Assumptions

- The training input is a sufficiently clean sine.
- The bit matrix contains enough information to estimate the weights or
  effective weights.
- Frequency estimation/refinement is accurate enough not to bias weights.
- The weighted-sum model is a reasonable reconstruction model.
- Residual memory effects, settling errors, reference transients, and
  time-varying errors are either small or outside the calibration target.

## Rigor And Risks

- `source-confirmed`: the pipeline and helper calls are visible in the source.
- `example-verified`: examples compare ENOB before and after calibration.
- `engineering-heuristic`: rank patching and harmonic inclusion are practical
  calibration strategies, not full mathematical proofs.
- `open-question`: the project does not yet provide uncertainty intervals,
  identifiability theorem, or full production validation workflow.
- `open-question`: harmonic rejection can improve fitting while obscuring
  error attribution.

## Related Pages

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Least-squares ADC calibration](../concepts/least_squares_adc_calibration.md)
- [Calibration helper chain](calibration_helper_chain_py.md)
- [Lite calibration source](calibrate_weight_sine_lite_py.md)
- [SAR model source](sar_py.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Next Reading

Read `_patch_rank_deficiency.py` next when studying redundant SAR calibration.
