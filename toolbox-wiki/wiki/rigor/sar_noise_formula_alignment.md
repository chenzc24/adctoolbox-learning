# SAR Noise Formula Alignment

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md
source_links:
  - ../source_notes/sun_sar_primary_pdf_distillation.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch12 - low power.pdf
  - ../../../../../python/src/adctoolbox/models/sar.py
rigor:
  - source-confirmed
  - primary-source-direct-distilled
  - formula-reviewed
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## Claim

The SAR noise slides separate sampling noise, DAC noise, and comparator noise.
Only some of these can be represented by ADCToolbox's current behavioral model,
and none of them should be confused with deterministic bit-weight mismatch.

## Evidence Map

- `ch12 - low power.pdf`, pages 16-20: `kT/C` and DAC noise.
- `ch12 - low power.pdf`, pages 22-29: comparator noise, offset, and design
  tradeoff.
- `wiki/source_notes/sun_sar_primary_pdf_distillation.md`
- `python/src/adctoolbox/models/sar.py`

## kT/C Sampling Noise

The PDF gives the standard RC sampling-noise result:

```text
integrated sampled noise power = kT / C
```

It also gives the equipartition argument:

```text
0.5*C*v_n^2 = 0.5*kT
=> v_n^2 = kT/C
```

The slide then compares `kT/C` noise to ideal quantization noise:

```text
kT/C = Delta^2 / 12
```

This produces a capacitor-size requirement that grows rapidly with target
resolution. The important learning point is not the exact table value, but the
scaling: high-resolution SAR ADCs pay a real input capacitance cost if sampled
thermal noise must be pushed below quantization noise.

## DAC Noise

The PDF separates DAC noise from sampling noise:

- DAC noise power spectral density is set by switch resistance.
- DAC settling bandwidth is set by the CDAC.
- DAC noise bandwidth can be set by parasitic capacitance.
- The total integrated DAC noise can be large, but not all of it affects the
  comparator decision.
- If DAC bandwidth is much larger than comparator bandwidth, much of the DAC
  noise is filtered before it matters.

This is a major modeling caveat. A digital weight-calibration model can correct
repeatable effective-weight errors, but it does not remove random DAC noise.

## Comparator Noise And Offset

The PDF decomposes comparator input-referred noise into preamp and latch terms:

```text
sigma_n^2 = sigma_preamp^2 + sigma_latch^2 / G^2
```

The same structure is used for offset:

```text
sigma_os^2 = sigma_os_preamp^2 + sigma_os_latch^2 / G^2
```

For a dynamic integrator, the slides connect gain, integration time, energy,
and input-referred noise. The key engineering result is a noise-energy tradeoff:

```text
input_referred_noise^2 * energy is tied to kT, gamma, and gm/ID
```

Design consequences:

- Larger preamp gain attenuates latch noise and offset.
- Too much preamp gain slows the comparator.
- Larger `gm/ID` improves energy efficiency, but too large a value increases
  input capacitance and can slow the comparator.
- Comparator offset follows a similar tradeoff to noise.

## Mapping To ADCToolbox

`sar_convert` currently exposes:

- `sampling_noise_rms`
- `comparator_noise_rms`

It does not explicitly model:

- DAC settling noise;
- DAC bandwidth filtering;
- metastability delay;
- common-mode-dependent comparator offset;
- dynamic reference behavior;
- random noise whose statistics vary by bit cycle.

Therefore, an ADCToolbox SAR experiment should label whether it is testing:

```text
weight mismatch
sampling noise
comparator noise
or an unmodeled circuit noise source
```

## Calibration Consequence

Do not use a weight-calibration success to claim that these noise sources are
corrected. Weight calibration can improve deterministic reconstruction errors.
It cannot remove irreducible sampled noise or random comparator decisions.

For redundancy, the relevant bridge is:

```text
per-cycle comparator/DAC error budget
  -> redundancy margin
  -> dynamic reachability
  -> validation under noise and mismatch
```

This connects directly to:

- [Redundant SAR reachability](redundant_sar_reachability.md)
- [Training and validation split](../workflows/training_validation_split.md)

## Failure Modes

- Treating `kT/C` as a calibratable weight error.
- Reporting ENOB improvement without separating deterministic distortion from
  random noise.
- Using one `comparator_noise_rms` value while the real circuit has
  bit-dependent comparator conditions.
- Ignoring that comparator common-mode and DAC switching scheme can change
  offset/noise.

## Next Work

Add an example or audit script that sweeps `sampling_noise_rms` and
`comparator_noise_rms` separately from capacitor mismatch, then reports which
metric changes are calibratable and which remain as noise floor.
