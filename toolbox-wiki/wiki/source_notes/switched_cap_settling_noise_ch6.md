# Source Note: Switched-Capacitor Settling And Noise

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/06_ch6_开关电容建立与噪声.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/06_ch6_开关电容建立与噪声.md
  - ../../../../../python/src/adctoolbox/models/sar.py
rigor:
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Switched-capacitor ADC circuits turn charge redistribution into sampling, DAC,
gain, and residue operations, but every operation pays settling, noise, and
power costs.

## Key Extracted Ideas

- Capacitor charge follows `Q = C*V`.
- Switching phases rearrange capacitor connections to sample, add, subtract,
  amplify, or implement DAC behavior.
- Finite bandwidth, switch resistance, and load capacitance create settling
  error.
- Settling error often decays roughly like `error(t) = error(0)*exp(-t/tau)`.
- High resolution requires settling error below a fraction of an LSB.
- kT/C noise is a fundamental sampled-noise floor.
- Amplifier noise and reference noise can also enter the conversion result.
- Speed, accuracy, and power form a design triangle.
- Calibration can compensate some deterministic gain or weight errors, but not
  random noise or complex time-varying settling behavior.

## Integration Into The Wiki

This source supports:

- [SAR model source](../source_code/sar_py.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Mathematical rigor gaps](../rigor/mathematical_rigor_gaps.md)

## Rigor Notes

The current ADCToolbox SAR model is useful for weight mismatch and bit-decision
learning, but this source explains circuit effects that remain outside the
simple behavioral model: settling, reference dynamics, and kT/C limits.

## Open Follow-Up

Add a future rigor page separating calibratable deterministic weight errors
from non-calibratable noise and dynamic settling errors.
