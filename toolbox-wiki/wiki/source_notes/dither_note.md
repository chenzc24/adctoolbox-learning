# Source Note: Dither

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/08_Dither_为什么噪声有时有帮助.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/08_Dither_为什么噪声有时有帮助.md
  - ../../../../../python/src/adctoolbox/calibration/_patch_rank_deficiency.py
rigor:
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Dither deliberately adds disturbance to break harmful correlation, reduce
deterministic spurs, and improve calibration observability.

## Key Extracted Ideas

- Dither is intentionally injected small disturbance.
- Without dither, small or periodic inputs can make quantization error
  correlated with the signal, producing harmonics or idle tones.
- Dither can trade a higher noise floor for fewer deterministic spurs.
- In calibration, dither can make more bit or stage combinations observable.
- Dither can improve matrix rank or condition number by exciting otherwise
  rarely changing states.
- Dither must be sized carefully: too small has little effect; too large lowers
  SNR or causes overload.
- Foreground calibration can use explicit training signals; background
  calibration must hide dither inside normal operation.

## Integration Into The Wiki

This source supports:

- [Matrix rank and observability](matrix_rank_observability_note.md)
- [Quantization noise model](quantization_noise_model_note.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## Rigor Notes

Dither is not "noise is always good." It is a controlled tradeoff between
observability/spur reduction and added noise or disturbance.

## Open Follow-Up

Add a calibration example note that explicitly shows dither improving rank,
conditioning, or spur behavior.
