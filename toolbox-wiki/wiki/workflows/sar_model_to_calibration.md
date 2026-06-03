# SAR Model To Calibration Workflow

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md
source_links:
  - ../../../../../python/src/adctoolbox/models/sar.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
  - ../../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
rigor:
  - source-confirmed
  - example-verified
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

The core ADCToolbox SAR learning loop is: generate a sine, convert it with
actual SAR weights, reconstruct with nominal or calibrated weights, and verify
the spectrum before and after calibration.

## Workflow

```text
1. Choose nominal SAR weights
2. Optionally apply capacitor mismatch to create actual analog weights
3. Generate a coherent sine input
4. Convert vin -> bits using actual analog weights
5. Reconstruct bits -> aout_before using nominal digital weights
6. Analyze aout_before with spectrum metrics
7. Calibrate weights from training bits
8. Reconstruct bits -> aout_after using calibrated weights
9. Analyze aout_after with spectrum metrics
10. Compare ENOB, SNDR, SFDR, THD, and weight error
```

## Minimal Conceptual Code

```python
nominal_weights = sar_ideal_weights(num_bits)
actual_weights = sar_apply_cap_mismatch(nominal_weights, sigma=sigma, rng=rng)

bits_train = sar_convert(vin_train, actual_weights)
bits_test = sar_convert(vin_test, actual_weights)

aout_before = sar_reconstruct(bits_test, nominal_weights)
cal = calibrate_weight_sine(bits_train, freq=train_bin / n_samples,
                            nominal_weights=nominal_weights)
aout_after = bits_test.astype(float) @ cal["weight"]
```

## Why Train And Test Separately

Training and validation separation is more rigorous than evaluating only on
the same sine used for calibration. A calibrated weight vector should improve
or preserve performance on a different coherent sine, not only fit the
training waveform.

## What To Measure

- ENOB and SNDR before/after calibration.
- SFDR and THD before/after calibration.
- Difference between calibrated weights and actual simulated weights when
  actual weights are known.
- Sensitivity to input frequency, amplitude, sample count, and noise.

## Assumptions

- The actual SAR errors are dominated by static weight mismatch.
- The bit decisions contain enough information for calibration.
- The test condition is close enough to training for weights to remain valid.

## Rigor And Risks

- `example-verified`: ADCToolbox examples perform this workflow.
- `engineering-heuristic`: improvement in a Monte Carlo example is not the
  same as production calibration signoff.
- `open-question`: true engineering validation needs multi-frequency,
  multi-amplitude, corner, and real-data testing.

## Related Pages

- [SAR model source](../source_code/sar_py.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Full calibration source](../source_code/calibrate_weight_sine_py.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Next Reading

Read the `exp_d16` Monte Carlo example to see how binary and redundant SAR
architectures respond to capacitor mismatch before and after calibration.
