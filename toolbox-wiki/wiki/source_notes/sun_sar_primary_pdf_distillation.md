# Source Note: Sun Course SAR Primary PDF Distillation

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12b_ch12_高速SAR_ADC.md
source_links:
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch12 - low power.pdf
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch12 - high speed.pdf
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12b_ch12_高速SAR_ADC.md
  - ../../../../../python/src/adctoolbox/models/sar.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
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

## One-Sentence Takeaway

The original SAR course PDFs frame SAR ADC behavior as a coupled problem of
binary search, CDAC settling/noise, comparator noise/offset, redundancy, timing
loop delay, and calibration tolerance.

## Direct PDF Distillation

- A SAR ADC is fundamentally a DAC, comparator, and SAR logic loop performing
  a binary search over the DAC output.
- Classic charge-redistribution implementation reuses the SAR DAC for input
  sampling and subtraction, which reduces several direct-implementation
  nonidealities.
- SAR energy efficiency comes from mostly digital operation, no static power,
  and scaling-friendly circuits.
- High resolution stresses the capacitor array, input/reference drivers, DAC
  switching energy, comparator noise, and conversion-cycle count.
- The low-power lecture separates SAR noise into sampling noise, DAC noise, and
  comparator noise.
- `kT/C` sampling noise and DAC settling/noise are physical limits that cannot
  be removed by digital calibration after the fact.
- Comparator input-referred noise and offset are tied to preamp gain,
  regeneration, `gm/ID`, input capacitance, and speed.
- Architectural redundancy can allow some comparator noise, DAC incomplete
  settling, and offset mismatch to be tolerated, but only inside the redundancy
  range.
- High-speed SAR design is organized around the loop timing budget:
  comparator delay, logic delay, DAC settling, and reset time.
- Techniques such as asynchronous clocking, direct comparator-to-DAC paths,
  redundancy, self-timing, ping-pong operation, loop unrolling, and multi-bit
  per cycle all trade speed against mismatch, calibration, or hardware cost.

## Calibration Meaning

For ADCToolbox, the important chain is:

```text
CDAC / comparator / timing nonideality
  -> wrong bit decisions or shifted effective weights
  -> bit-decision matrix plus unknown weights
  -> sine-based least-squares calibration
  -> spectrum and residual validation
```

The PDFs support the idea that an effective digital weight model is useful, but
they also warn that not every physical SAR error is a recoverable weight error.
Some errors become noise, missing decision reachability, metastability, or
input-dependent distortion.

## Redundancy Meaning

The PDFs treat redundancy as an engineering tolerance mechanism:

- radix less than two or extra redundant bits create room for later decisions
  to recover earlier errors;
- incomplete DAC settling can be tolerated if the error stays inside the
  redundancy range;
- comparator noise or offset can be relaxed for some cycles;
- redundancy costs extra comparisons, logic, or effective bit decisions.

This is not yet a formal theorem. A rigorous page still needs to define the
reachable interval after every decision, the admissible error bound, and the
conditions under which a later decision can return the residue into range.

## Integration Into The Wiki

This source supports:

- [SAR model source](../source_code/sar_py.md)
- [Full sine-weight calibration source](../source_code/calibrate_weight_sine_py.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Rank deficiency](../concepts/rank_deficiency.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)
- [Example: redundancy comparison](examples/exp_d03_redundancy_comparison.md)
- [Example: SAR unit-cap mismatch Monte Carlo](examples/exp_d16_sar_unit_cap_mismatch_mc.md)
- [Example: SAR training-length sweep](examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md)

## Rigor Notes

- Weight calibration estimates effective digital weights, not a unique
  physical diagnosis of capacitor, comparator, reference, or timing errors.
- Redundancy must be stated as an interval/reachability property, not merely a
  larger nominal code span.
- Training data must excite enough independent bit patterns to make weights
  identifiable.
- A calibrated spectrum improvement is evidence, but not a proof that all SAR
  nonidealities are corrected.

## Open Follow-Up

Write `wiki/rigor/redundant_sar_reachability.md` using this primary PDF note
and the three SAR example evidence notes.
