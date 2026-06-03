# Source Note: Voltage Comparators

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/07_ch7_电压比较器.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/07_ch7_电压比较器.md
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

Comparators are ADC decision elements, and their offset, noise, kickback,
delay, and metastability can move or randomize conversion thresholds.

## Key Extracted Ideas

- An ideal comparator has infinite gain, zero delay, zero noise, and zero
  offset.
- Real dynamic comparators use precharge and regenerative positive feedback.
- Small input differential voltage takes longer to resolve.
- Comparator offset shifts the effective decision threshold.
- Comparator noise can randomize decisions; small noise may act like dither,
  while large noise reduces SNR.
- Kickback sends internal switching disturbance back to the sampling node.
- Metastability and insufficient decision time cause bit errors.

## Integration Into The Wiki

This source supports:

- [SAR model source](../source_code/sar_py.md)
- [Low-power SAR source note](sar_low_power_ch12a.md)
- [High-speed SAR source note](high_speed_sar_ch12b.md)

## Rigor Notes

Comparator offset can sometimes be calibrated as a deterministic error.
Comparator noise, metastability, and dynamic kickback usually require
probabilistic or circuit-level treatment rather than simple linear weight
calibration.

## Open Follow-Up

Add a future page on comparator error models if ADCToolbox gains explicit
comparator offset or metastability simulations.
