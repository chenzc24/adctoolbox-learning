# Pipeline Residue Box And Gain Observability

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/10_ch10_Pipeline_ADC概念.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/11_ch11_Pipeline_ADC实现.md
source_links:
  - ../source_notes/sun_pipeline_primary_pdf_distillation.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch10.pdf
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch11.pdf
rigor:
  - source-confirmed
  - primary-source-direct-distilled
  - formula-reviewed
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## Claim

Pipeline redundancy and gain calibration are meaningful only if the stage
residue remains observable by the backend ADC. The central rigor condition is
not "has redundancy" but "the residue stays inside the backend observable box,
or a later stage returns it there before final quantization."

## Evidence Map

- `ch10.pdf`, pages 30-36: stage gain upper bound, backend overload, and
  sub-ADC redundancy.
- `ch10.pdf`, pages 38-42: gain error, digital gain calibration, and DAC
  calibration.
- `ch11.pdf`, pages 22-28: residue plot, capacitor matching, comparator
  tolerance, and OTA design constraints.
- `wiki/source_notes/sun_pipeline_primary_pdf_distillation.md`

## Residue Box Condition

The Pipeline concept PDF states:

- backend ADC overload occurs when stage gain is too high;
- sub-ADC decision-level errors can push residue out of backend range;
- redundancy is useful when the residue stays inside the box, or downstream
  stages return it into the box before the last quantizer.

In abstract form:

```text
residue = G * (Vin - Vdac(D)) + error_terms
```

For a backend input range:

```text
Vres in [Vmin_backend, Vmax_backend]
```

A conservative stage-level condition is:

```text
for all allowed Vin and decision errors:
    G * (Vin - Vdac(D)) + error_terms remains inside backend range
```

If this fails, the backend cannot observe the residue correctly, so a
calibration algorithm using backend information may lose identifiability.

## Stage Gain Upper Bound

The PDF states that a backend can overload for too-large stage gain. It then
lists mitigation ideas:

- extend backend decision levels;
- choose `G` slightly less than the nominal maximum;
- use a power-of-two gain lower than the maximum;
- use a 1.5-bit-style stage.

The rigorous translation is:

```text
stage gain must be chosen with sub-ADC error, DAC error, amplifier offset,
and backend range in mind
```

not merely from the nominal bits-per-stage value.

## Digital Gain Calibration

The PDF gives the key idea:

```text
analog gain error is tolerable if digital gain matches analog gain
```

A simplified calibration observation is:

```text
Db = G * (Vin - Vdac) + backend_quantization_error
```

The PDF's two-step gain calibration subtracts two backend observations forced
around different DAC values:

```text
Db_1 - Db_2 = known_delta * G + backend_error_difference
```

This makes `G` observable only if:

- the forced DAC difference is known;
- the backend response is not overloaded;
- quantization error is reduced by averaging, noise dither, or extra backend
  resolution;
- gain nonlinearity is small enough for the desired ENOB.

## DAC Calibration

The PDF describes DAC calibration as the same concept as gain calibration:

```text
sweep DAC codes
use backend ADC to measure transition errors
store correction coefficients
```

This is backend-observable only if the backend itself is accurate enough over
the forced residue range, or if its error can be averaged or separated.

## Mapping To ADCToolbox

ADCToolbox currently has strong SAR weight-calibration examples, but not a full
Pipeline behavioral calibration model. This page should therefore be used as a
future design constraint:

```text
if Pipeline model is added:
  represent residue
  represent backend observable range
  record stage gain
  record sub-DAC transition errors
  separate foreground and background calibration assumptions
```

## Failure Modes

- Backend overload makes residue information unusable.
- Sub-ADC offset is larger than redundancy can tolerate.
- Analog gain drifts after foreground calibration.
- DAC transition errors are repeatable but not sufficiently observed.
- Backend quantization error is not averaged down.
- Gain nonlinearity limits ENOB even if small-signal gain is calibrated.

## What This Does Not Prove

- It does not derive a complete Pipeline calibration theorem.
- It does not implement Pipeline calibration in ADCToolbox.
- It does not quantify OTA settling or thermal noise limits.
- It does not prove background calibration convergence.

## Related Pages

- [Sun Pipeline primary PDF distillation](../source_notes/sun_pipeline_primary_pdf_distillation.md)
- [Pipeline ADC concept](../source_notes/pipeline_adc_concept_ch10.md)
- [Pipeline ADC implementation](../source_notes/pipeline_adc_implementation_ch11.md)
- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Identifiability conditions](identifiability_conditions.md)

## Next Work

Create a Pipeline calibration concept page only after a behavioral Pipeline
model or example exists in ADCToolbox.
