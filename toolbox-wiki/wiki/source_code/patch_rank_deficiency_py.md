# `_patch_rank_deficiency.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/_patch_rank_deficiency.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/docs/source/algorithms/calibrate_weight_sine.md
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

`_patch_rank_deficiency.py` compresses unobservable or dependent bit columns
into an effective bit space before calibration, then maps solved weights back
to physical bit positions.

## Public API Purpose

Internal helpers:

- `_patch_rank_deficiency(bits_stacked, nominal_weights, verbose=0)`
- `_recover_rank_deficiency(w_effective, bit_to_col_map, bit_weight_ratios)`

The first returns an effective bit matrix and mapping metadata. The second
recovers physical weights from solved effective weights.

## Core Data Flow

```text
bits_stacked + nominal_weights
  -> check rank of [bits, ones]
  -> keep independent non-constant columns
  -> drop constant columns
  -> merge dependent columns using nominal weight ratios
  -> solve calibration in effective space
  -> recover physical weights
```

## What The Patch Does

The helper distinguishes three cases:

- full rank: return the original bit matrix unchanged;
- constant bit column: drop it because it carries no dynamic information;
- dependent bit column: merge it into a previous effective column when the
  centered correlation is close to plus or minus one.

## Why This Matters

Redundant SAR architectures can intentionally produce bit decisions that are
not all independently observable in a given training record. A plain least
squares solve can then become singular or unstable. The patcher changes the
problem from "estimate every physical bit independently" to "estimate the
observable effective columns, then distribute weights back by a nominal rule."

## Assumptions

- Linear dependency can be detected from the available training data.
- Nominal weight ratios are an acceptable way to distribute merged weights.
- Constant columns contribute no dynamic reconstruction information.
- Recovering physical weights from effective weights is meaningful for the
  downstream reconstruction goal.

## Rigor And Risks

- `source-confirmed`: the rank check, constant-column drop, correlation-based
  merge, and recovery mapping are visible in the source.
- `theory-supported`: rank deficiency is a linear-algebra identifiability
  issue.
- `engineering-heuristic`: nominal-ratio recovery is a practical choice, not a
  proof that each physical capacitor weight has been individually identified.
- `open-question`: a full redundant SAR proof must distinguish effective
  reconstruction quality from physical-weight observability and missing-code
  behavior.

## Related Pages

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Full calibration source](calibrate_weight_sine_py.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)
- [Least-squares source note](../source_notes/least_squares_calibration_note.md)

## Next Reading

Read this together with an SVD or QR view of least squares. The implementation
is easier to understand when "rank" means "how many independent columns the
training data actually contains."
