# Source Note: Matrix Rank And Observability

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md
  - ../../../../../python/src/adctoolbox/calibration/_patch_rank_deficiency.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
rigor:
  - source-confirmed
  - theory-supported
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC calibration needs independent observations, not just many observations;
rank and conditioning decide what can actually be estimated.

## Key Extracted Ideas

- Calibration can be written as `A x = y`, where `x` contains unknown weights,
  gain, or offset.
- Unique recovery needs at least as many independent observations as unknowns.
- `rank(A)` measures independent information in the observation matrix.
- If two bits always switch together, their individual weights are not
  separately observable from that data.
- Rich excitation, dither, pseudo-random inputs, and multiple calibration
  records can improve observability.
- Even full-rank matrices can be poorly conditioned; noise can make the
  solution unstable.

## Integration Into The Wiki

This source supports:

- [Identifiability conditions](../rigor/identifiability_conditions.md)
- [Rank patch source](../source_code/patch_rank_deficiency_py.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)

## Rigor Notes

This source is the clearest raw justification for treating rank deficiency and
condition number as calibration validity checks, not merely numerical details.

## Open Follow-Up

Create `wiki/concepts/rank_deficiency.md` and a numerical example comparing
full rank, rank deficient, and ill-conditioned bit matrices.
