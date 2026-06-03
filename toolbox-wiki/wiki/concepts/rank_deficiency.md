# Rank Deficiency

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/_patch_rank_deficiency.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
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

Rank deficiency means the calibration data does not contain enough independent
columns to estimate every requested parameter separately.

## Core Idea

For a design matrix `A`, rank tells how many independent directions the data
actually provides. If two bit columns always move together, least squares
cannot distinguish their individual weights from their combined effect.

In ADC weight calibration, this can happen because:

- one bit never toggles in the training data;
- two bits are exact or near duplicates;
- redundant architecture creates dependent decisions;
- the training waveform does not excite enough code regions;
- extra sine/harmonic/offset columns absorb similar variation.

## ADCToolbox Handling

`_patch_rank_deficiency.py` handles rank issues by:

- checking rank of `[bits, ones]`;
- dropping constant columns;
- keeping independent columns;
- merging dependent columns into an effective column;
- using nominal weight ratios to recover physical weight positions.

This is an effective-weight strategy. It stabilizes the solve but does not by
itself prove that all physical capacitor weights were independently observed.

## Practical Debug Questions

When calibration looks unstable, ask:

- Which bits toggled?
- Which columns were constant?
- Which columns were merged?
- Does the recovered weight vector reflect physical weights or effective
  reconstruction weights?
- Does test data outside the training waveform still improve?

## Rigor And Risks

- `source-confirmed`: the patch and recovery behavior are visible in source.
- `theory-supported`: rank controls linear identifiability.
- `engineering-heuristic`: nominal-ratio recovery is practical but not a full
  physical proof.
- `open-question`: redundant SAR reachability and missing-code behavior need
  separate proof and validation.

## Related Pages

- [Rank deficiency patch source](../source_code/patch_rank_deficiency_py.md)
- [Calibration helper chain](../source_code/calibration_helper_chain_py.md)
- [Least-squares ADC calibration](least_squares_adc_calibration.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Next Reading

Read the rank patch source page and then the identifiability page. The first
shows the implementation; the second explains what still needs proof.
