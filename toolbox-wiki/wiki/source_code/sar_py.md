# `sar.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/01_向量矩阵与线性组合.md
source_links:
  - ../../../../../python/src/adctoolbox/models/sar.py
  - ../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
  - ../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
  - ../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
rigor:
  - source-confirmed
  - example-verified
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

`sar.py` is the behavior-level SAR ADC model: it converts an input waveform to
raw bit decisions and reconstructs those decisions with an explicit weight list.

## Public Functions

- `sar_ideal_weights(num_bits, redundant_bit=None)`: create normalized binary
  or one-duplicate redundant SAR weights.
- `sar_apply_cap_mismatch(weights, sigma, rng=None, cap_units=None)`: apply
  unit-cap/Pelgrom-style mismatch to capacitor weights.
- `sar_apply_mismatch(weights, sigma, rng=None)`: legacy same-relative-RMS
  mismatch helper.
- `sar_convert(vin, weights, quant_range=(0, 1), ...)`: perform SAR bit trials.
- `sar_reconstruct(codes, weights, quant_range=(0, 1))`: compute
  `codes @ weights`.

## Core Data Flow

```text
vin
  -> normalize to quant_range
  -> for each bit weight:
       v_test = v_dac + weight[j]
       bit[j] = 1 if vin_sampled + comparator_noise >= v_test else 0
       v_dac = v_test when bit[j] is 1
  -> bits
  -> sar_reconstruct(bits, digital_weights)
  -> aout
```

## Important Convention

`weights` are normalized by:

```text
sum(raw_bit_weights) + one_LSB
```

So an ideal 4-bit binary list is:

```text
[8, 4, 2, 1] / 16
```

not `/15`.

## Why The Weight Split Matters

The model keeps two roles separate:

- analog CDAC weights used by `sar_convert`,
- digital reconstruction weights used by `sar_reconstruct`.

That split is essential for calibration learning. An uncalibrated SAR can
encode with mismatched actual weights but reconstruct with nominal weights.
Calibration then tries to replace the nominal digital weights with estimated
weights.

## What The Model Includes

- Binary or redundant explicit weight lists.
- Capacitor mismatch via unit-cap scaling.
- Sampling noise.
- Comparator noise.
- Vectorized batch conversion.

## What The Model Does Not Include

The source docstring explicitly excludes full circuit effects such as DAC
settling errors, metastability delay, charge injection, and PVT drift. Those
effects may require transistor-level simulation or a richer behavioral model.

## Rigor And Risks

- `source-confirmed`: SAR bit decisions are implemented explicitly in
  `sar_convert`.
- `source-confirmed`: reconstruction is a linear weighted sum.
- `example-verified`: the mismatch and calibration examples use this model.
- `engineering-heuristic`: capacitor mismatch is a useful statistical model,
  not a replacement for layout-aware parasitic extraction.
- `open-question`: redundant SAR reachability and no-missing-code behavior are
  not proven merely by creating a redundant weight list.

## Related Pages

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Next Reading

Read `exp_d15_sar_unit_cap_mismatch_uncal_spectra.py` after this page to see
how mismatch becomes visible in the spectrum before calibration.
