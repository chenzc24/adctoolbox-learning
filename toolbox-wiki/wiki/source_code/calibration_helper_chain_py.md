# Calibration Helper Chain

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/_prepare_input.py
  - ../../../../../python/src/adctoolbox/calibration/_scale_columns_for_conditioning.py
  - ../../../../../python/src/adctoolbox/calibration/_estimate_frequencies.py
  - ../../../../../python/src/adctoolbox/calibration/_lstsq_solver.py
  - ../../../../../python/src/adctoolbox/calibration/_post_process.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
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

The full weight calibrator is a helper pipeline around least squares, not a
single matrix solve.

## Helper Map

- `_prepare_input.py`: normalize single or multi-dataset bit matrices.
- `_patch_rank_deficiency.py`: collapse dependent bit columns.
- `_scale_columns_for_conditioning.py`: scale columns by powers of ten before
  solving.
- `_estimate_frequencies.py`: estimate or validate one frequency per dataset.
- `_lstsq_solver.py`: build harmonic basis and solve with dual sine/cosine
  basis choices.
- `_post_process.py`: recover physical weights, reconstruct signals, compute
  residual metrics, and format the result dictionary.

## Core Data Flow

```text
bits input
  -> reshape/stack and nominal weights
  -> rank deficiency patch
  -> column scaling
  -> frequency estimation or user freq
  -> known-frequency solve or frequency-search solve
  -> recover conditioned columns
  -> recover rank-deficient physical weights
  -> post-process reconstructed signal, ideal, error, ENOB
```

## Why This Matters

The top-level `calibrate_weight_sine.py` page explains the public behavior.
This page shows where each engineering choice enters the pipeline. When a
calibration result looks suspicious, the debugging question is usually which
helper made the decisive assumption.

## Key Assumptions By Stage

- Input preparation assumes bit matrices can be standardized into samples by
  bits.
- Rank patching assumes effective columns can represent dependent physical
  bits.
- Conditioning assumes column scaling improves numerical behavior without
  changing the physical result after recovery.
- Frequency estimation assumes active bit-derived signals expose the input
  tone.
- The least-squares solver assumes the design matrix contains enough
  independent information.
- Post-processing assumes residual energy is meaningful as calibration error.

## Rigor And Risks

- `source-confirmed`: helper sequence is visible in `calibrate_weight_sine.py`
  and helper modules.
- `theory-supported`: rank, conditioning, and least squares are standard
  numerical linear algebra issues.
- `engineering-heuristic`: frequency estimation and rank recovery use practical
  rules that should be validated for each architecture.
- `open-question`: production claims need condition numbers, uncertainty
  estimates, train/test validation, and architecture-specific reachability
  checks.

## Related Pages

- [Full calibration source](calibrate_weight_sine_py.md)
- [Rank deficiency patch source](patch_rank_deficiency_py.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Least-squares ADC calibration](../concepts/least_squares_adc_calibration.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## Next Reading

Read `_lstsq_solver.py` together with the least-squares concept page, because
that is where the calibration model becomes an actual design matrix.
