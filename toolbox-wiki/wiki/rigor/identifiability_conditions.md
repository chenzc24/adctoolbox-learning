# Identifiability Conditions For ADC Weight Calibration

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
source_links:
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/calibration/_patch_rank_deficiency.py
  - ../source_notes/least_squares_calibration_note.md
rigor:
  - source-confirmed
  - theory-supported
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC weight calibration is identifiable only up to the independent information
contained in the bit matrix and the chosen sine/offset basis.

## The Claim Or Risk

Least squares can always return a numerical answer, but the answer is not
necessarily a uniquely identified physical weight vector. If columns are
dependent, nearly dependent, constant, or poorly excited, many weight vectors
can explain the same observed waveform.

## Minimal Linear Model

A simplified sine-calibration model can be written as:

```text
B w + c0*1 + c1*cos(2*pi*f*n) + c2*sin(2*pi*f*n) = residual target
```

Equivalently, the solve depends on a design matrix made from:

```text
[bit columns, offset column, sine basis columns, optional harmonic columns]
```

The identifiable parameter combinations are determined by the rank and
conditioning of that design matrix.

## Necessary Conditions

For a stable interpretation, the training data should satisfy:

- each estimated bit column varies during the record;
- bit columns are not exact duplicates after accounting for offset;
- bit columns are not nearly collinear over the sampled input distribution;
- sine, cosine, offset, and harmonic basis columns do not absorb the same
  degrees of freedom as the bit columns;
- the number of samples is much larger than the number of fitted parameters;
- the input covers enough code transitions to excite the relevant bit weights.

## What ADCToolbox Currently Does

- `calibrate_weight_sine_lite.py` directly solves a least-squares system.
- `calibrate_weight_sine.py` adds conditioning and rank-deficiency handling.
- `_patch_rank_deficiency.py` collapses dependent bit columns into effective
  columns and later recovers physical weights by nominal ratios.

This is a good engineering response to singular systems, but it should be read
as effective-weight recovery unless additional evidence proves that each
physical bit has been separately observed.

## What Is Not Proven Yet

- A theorem specifying all training conditions that guarantee unique physical
  weights.
- A bound connecting condition number to expected weight error.
- A frequency-error bias analysis.
- A redundant SAR reachability and no-missing-code proof.
- A validation rule that says when recovered physical weights can be trusted
  outside the training waveform.

## How To Test Or Validate Next

For each calibration run, record:

- rank of the full design matrix;
- singular values or condition number;
- number of dropped or merged bit columns;
- train/test ENOB or residual metrics;
- frequency and amplitude sweep performance;
- Monte Carlo mismatch distribution;
- whether failures correlate with specific bit dependencies.

## Related Pages

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Full calibration source](../source_code/calibrate_weight_sine_py.md)
- [Rank patch source](../source_code/patch_rank_deficiency_py.md)
- [Mathematical rigor gaps](mathematical_rigor_gaps.md)
- [Open questions](../../open_questions.md)

## Next Reading

Read `_patch_rank_deficiency.py` after this page. It is the implementation
where identifiability limits become a concrete engineering workaround.
