# Source Note: Sampling Circuits

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/05_ch5_采样电路.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/05_ch5_采样电路.md
  - ../../../../../python/src/adctoolbox/models/sar.py
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch5.pdf
rigor:
  - source-confirmed
  - primary-source-spot-checked
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Sampling circuits turn a continuous input into a held voltage, but finite RC
settling, switch nonlinearity, kT/C noise, charge injection, and jitter make
the sampled value differ from the ideal mathematical sample.

## Key Extracted Ideas

- Track phase: the sampling capacitor follows the input through switch
  resistance.
- Hold phase: the switch opens and the held voltage is processed by later ADC
  stages.
- Finite acquisition time leaves residual settling error.
- MOS switch resistance can vary with input voltage and create distortion.
- Transmission gates, bootstrapped switches, and differential structures reduce
  switch nonlinearity.
- kT/C noise falls with larger capacitance, but larger capacitance increases
  area, loading, and power.
- Sampling jitter converts time error into voltage error; high input frequency
  makes jitter more harmful.

## Integration Into The Wiki

This source supports:

- [Switched-capacitor settling and noise](switched_cap_settling_noise_ch6.md)
- [SAR model source](../source_code/sar_py.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Rigor Notes

ADCToolbox behavioral models can include sampling/comparator noise terms, but
this source explains why real sampling errors can be signal-dependent,
history-dependent, and not fully captured by static weight calibration.

## Open Follow-Up

Add a future rigor page distinguishing sampling jitter, finite settling, and
CDAC weight mismatch as separate error mechanisms.
