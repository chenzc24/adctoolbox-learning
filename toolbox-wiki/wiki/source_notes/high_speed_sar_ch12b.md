# Source Note: High-Speed SAR ADC

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12b_ch12_高速SAR_ADC.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12b_ch12_高速SAR_ADC.md
  - ../../../../../python/src/adctoolbox/models/sar.py
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch12 - high speed.pdf
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

High-speed SAR keeps the bit-trial SAR idea but compresses DAC settling,
comparator decision, and logic timing, which exposes more dynamic nonidealities.

## Key Extracted Ideas

- A traditional `N`-bit SAR needs multiple DAC-settle, compare, and logic
  update cycles.
- Faster DAC settling can come from smaller capacitors, lower parasitics,
  faster switches, and optimized timing.
- Faster comparators reduce regeneration time but trade against noise, offset,
  and power.
- Asynchronous SAR starts the next bit when the previous comparison completes
  instead of waiting for a fixed bit clock.
- Multi-bit-per-cycle SAR reduces comparison rounds but increases hardware
  complexity.
- Time interleaving increases aggregate sample rate but introduces
  channel-to-channel mismatch spurs.
- High-speed SAR is often limited by DAC incomplete settling, metastability,
  clock skew, reference transients, and input-drive limits.

## Integration Into The Wiki

This source supports:

- [SAR model source](../source_code/sar_py.md)
- [Low-power SAR source note](sar_low_power_ch12a.md)
- [Time-interleaved ADCs](time_interleaving_ch13.md)
- [Comparator source note](comparator_ch7.md)

## Rigor Notes

The current SAR behavior model is a good static weight and bit-decision model,
but high-speed SAR requires caution: dynamic settling, reference recovery,
clock skew, and metastability may dominate performance.

## Open Follow-Up

Add a future rigor page on static versus dynamic SAR calibration limits.
