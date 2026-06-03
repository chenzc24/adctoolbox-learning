# Redundant SAR Reachability

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12b_ch12_高速SAR_ADC.md
source_links:
  - ../source_notes/sun_sar_primary_pdf_distillation.md
  - ../source_notes/examples/exp_d03_redundancy_comparison.md
  - ../source_notes/examples/exp_d16_sar_unit_cap_mismatch_mc.md
  - ../source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md
  - ../../../../../python/src/adctoolbox/models/sar.py
rigor:
  - source-confirmed
  - primary-source-direct-distilled
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## Claim

Redundant SAR design is useful only when the remaining decision space can
recover from the expected decision errors. A larger nominal code span or an
extra repeated bit is not by itself a proof of no missing codes, no overload,
or calibration identifiability.

## Model

For the ADCToolbox behavioral SAR model:

```text
weights: w[0], w[1], ..., w[B-1] > 0
prefix sum before bit j: S_j
test threshold: T_j = S_j + w[j]
remaining positive correction after bit j: R_j = sum(w[j+1:])
bit[j] = 1 if x + e_j >= T_j else 0
reconstruction: y = bits @ digital_weights
```

`e_j` represents comparator noise, comparator offset, effective DAC settling
error, or any other input-referred decision perturbation at cycle `j`.

The Sun SAR PDFs describe redundancy as an engineering way to tolerate
comparator noise, DAC incomplete settling, and offset mismatch. In this page,
that statement is translated into an interval condition.

## Assumptions

- The SAR can be modeled by an ordered decision sequence.
- Each decision has a bounded input-referred error budget `|e_j| <= E_j`.
- The digital reconstruction weights are known, nominal, or later calibrated.
- The input range and weight normalization are explicit.
- Static code coverage and dynamic decision-path reachability are treated as
  separate checks.

## Formula And Figure Review

From the SAR primary PDFs:

- Low-power SAR: the key architectural figure is binary search through a DAC
  output and comparator decision.
- Low-power SAR: redundancy is shown as a way to tolerate comparator noise,
  DAC incomplete settling, and offset mismatch.
- High-speed SAR: the timing formula is:

```text
T_loop = t_comp + t_logic + max(t_DAC, t_reset)
T_SAR  ≈ t_sample + N*T_loop
```

- High-speed SAR: redundancy relaxes `t_DAC` because each bit does not need to
  settle all the way to the final target resolution, only inside the redundancy
  range.

The formulas and figures support an engineering claim: redundancy trades extra
decision range or extra cycles for tolerance. They do not by themselves prove
the exact error bound for a given weight list.

## Derivation Or Argument

For a prefix `p` before decision `j`, define:

```text
S = sum(prefix bits * previous weights)
T = S + w[j]
R = sum(future weights)
```

If the branch chooses `0`, the future positive-weight ADCToolbox model can
represent:

```text
I_0 = [S, S + R]
```

If the branch chooses `1`, it can represent:

```text
I_1 = [S + w[j], S + w[j] + R]
```

The overlap or gap between these two intervals is:

```text
overlap_margin_j = R - w[j]
```

Interpretation:

- `R > w[j]`: the two branches overlap. Some wrong decisions can still land in
  a representable region.
- `R = w[j]`: the branches just touch. There is no margin for decision error.
- `R < w[j]`: there is a gap. Some inputs near the threshold become
  unreachable if the wrong branch is taken.

This is a necessary interval-level check for a monotone positive-weight SAR
model. It is not sufficient for full ADC correctness because dynamic decision
errors, calibration basis rank, and output-code density still matter.

For a bounded error budget `E_j`, an engineering sufficient condition is:

```text
usable redundancy margin after bit j >= decision error budget at bit j
```

The exact margin depends on the reconstruction convention and final quantization
cell. In the strict interval view above, a conservative check is:

```text
R_j - w[j] >= E_j
```

When this fails, redundancy may still help statistically, but it is no longer a
deterministic reachability guarantee for that decision.

## Static Coverage Check

Independently of the conversion path, compute all attainable digital sums:

```text
C = sort({bits @ weights | bits in {0,1}^B})
gaps = diff(C)
```

For a small `B`, exhaustive enumeration is possible. For large `B`, use
structured interval propagation or targeted Monte Carlo.

Static coverage answers:

- Are there large gaps in the possible reconstructed values?
- Does redundancy create overlapping or denser code sums?
- Are multiple codes mapping to similar values?

Static coverage does not answer whether the SAR decision path can actually
reach each useful code under comparator and settling errors.

## Dynamic Reachability Check

For each decision node:

1. Compute the prefix sum `S`.
2. Compute branch intervals `I_0` and `I_1`.
3. Compute the local overlap or gap.
4. Compare the overlap margin to the decision error budget.
5. Record which nodes have no margin.

Then validate with simulation:

1. Sweep input amplitude and phase.
2. Inject bounded comparator noise or DAC settling error.
3. Convert with actual analog weights.
4. Reconstruct with nominal and calibrated weights.
5. Check missing-code, DNL/INL, ENOB, SNDR, and failed calibration cases.

## Project Implementation

ADCToolbox currently provides:

- `sar_ideal_weights(num_bits, redundant_bit=None)`: creates ideal binary or
  one-duplicate redundant weights.
- `sar_apply_cap_mismatch`: applies Pelgrom/unit-cap mismatch.
- `sar_convert`: performs the ordered bit decisions.
- `sar_reconstruct`: performs `codes @ weights`.
- `calibrate_weight_sine`: estimates effective digital weights from bit
  decisions.

The examples provide evidence:

- `exp_d03_redundancy_comparison.py`: redundancy can improve calibration under
  MSB mismatch, but does not prove a general theorem.
- `exp_d16_sar_unit_cap_mismatch_mc.py`: mismatch tolerance should be treated
  statistically.
- `exp_d18_sar_redundant_mismatch_training_length_sweep.py`: calibration needs
  independent validation because short records can overfit.

## Failure Modes

- Redundant nominal weights exist, but branch intervals still have gaps.
- Code sums cover the range, but the decision path cannot reach useful codes.
- Comparator noise exceeds the local redundancy margin.
- DAC settling error is input- or bit-dependent and not captured by constant
  effective weights.
- The bit matrix is rank deficient, so calibration estimates only effective
  combinations of weights.
- A spectrum metric improves on the training record but fails on a held-out
  capture.

## Validation Recipe

For each redundant SAR experiment, record:

- weight list and normalization;
- per-bit `R_j - w[j]` margins;
- assumed comparator, DAC settling, and sampling error budgets;
- rank and condition number of the calibration design matrix;
- train and test input frequencies;
- train and test ENOB/SNDR;
- missing-code, DNL, and INL status when static validation is relevant;
- Monte Carlo seed, mismatch sigma, and failure rate.

## What This Does Not Prove

- It does not prove a universal theorem for all redundant SAR architectures.
- It does not cover signed residue implementations in full circuit detail.
- It does not model metastability delay or PVT drift.
- It does not prove physical capacitor values are uniquely identified by
  sine-weight calibration.

## Related Pages

- [Sun SAR primary PDF distillation](../source_notes/sun_sar_primary_pdf_distillation.md)
- [SAR model source](../source_code/sar_py.md)
- [Full sine-weight calibration source](../source_code/calibrate_weight_sine_py.md)
- [Rank deficiency](../concepts/rank_deficiency.md)
- [Identifiability conditions](identifiability_conditions.md)
- [Example: redundancy comparison](../source_notes/examples/exp_d03_redundancy_comparison.md)
- [Example: SAR unit-cap mismatch Monte Carlo](../source_notes/examples/exp_d16_sar_unit_cap_mismatch_mc.md)
- [Example: SAR training-length sweep](../source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md)

## Next Work

Implement a small reachability audit script that reports per-node interval
margins for each SAR weight list used in examples.
