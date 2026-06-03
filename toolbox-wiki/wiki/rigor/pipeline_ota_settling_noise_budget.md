# Pipeline OTA Settling And Noise Budget

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/11_ch11_Pipeline_ADC实现.md
source_links:
  - ../source_notes/sun_pipeline_primary_pdf_distillation.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch11.pdf
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

Pipeline stage accuracy is limited not only by digital calibration, but also by
OTA finite gain, dynamic settling, switch behavior, and sampled thermal noise.
These limits determine whether a residue can be measured accurately enough for
calibration to matter.

## Evidence Map

- `ch11.pdf`, pages 28-30: OTA static gain and dynamic settling requirements.
- `ch11.pdf`, pages 32-33: switch RC and front-end SHA concerns.
- `ch11.pdf`, pages 34-38: settling behavior and simulation model.
- `ch11.pdf`, pages 41-43: switch/OTA noise analysis and budget partitioning.
- `wiki/source_notes/sun_pipeline_primary_pdf_distillation.md`
- `wiki/rigor/pipeline_residue_box_gain_observability.md`

## Static Gain Error

The PDF states:

```text
static amplifier error ~= 1 / loop_gain
```

For a first stage in a 10-bit Pipeline ADC, the slide gives a rough
requirement:

```text
loop_gain > 60 dB
```

This is a circuit-level condition, not a digital-calibration theorem. If finite
gain is stable and observable, calibration may compensate part of the resulting
gain error. If it is nonlinear, time-varying, or signal-dependent, a single
digital coefficient is insufficient.

## Dynamic Settling

The PDF says stage outputs should settle to roughly a fraction of an LSB within
about half a clock cycle. The speed slide uses these assumptions:

- non-dominant pole in a two-stage amplifier is hard to move beyond about
  `fT/5`;
- optimum fast settling uses about `73 deg` phase margin;
- linear settling to `0.1%` precision takes about `7` loop time constants;
- practical design often budgets around `10` time constants;
- only about `60%` of half a cycle may be available for linear settling.

The resulting slide-level rule of thumb is:

```text
fCLK,max ~= fT / 80
```

This is useful as a sanity check. It is not a replacement for transient
simulation, because slewing, parasitic poles, clock non-overlap, and feedback
factor change the result.

## Switch And SHA Constraints

The PDF recommends switch RC significantly faster than the OTA:

```text
switch RC path ~= 10x faster than OTA path
```

Reasons:

- avoid settling speed degradation;
- reduce switch noise contribution;
- avoid feedback-network stability issues;
- maintain constant `Ron` for high-swing front-end sampling.

For SHA-less Pipeline architectures, MDAC/sub-ADC acquisition timing mismatch
becomes a calibration-relevant error source.

## Noise Budget

The PDF separates noise contributions across clock phases and gives a
switched-capacitor-style output noise expression. The important structure is:

```text
total output noise = switch/capacitor term + OTA-dependent term
```

The slide-level expression has the form:

```text
v_o,total^2 = (kT/Cf)*(1 + Cs/Cf) + alpha*gamma*(1/beta)*(kT/CLtot)
```

The exact constants depend on the stage topology and assumptions, but the
engineering meaning is stable:

- sampling and feedback capacitors set one part of the noise;
- OTA transconductance/device noise sets another part;
- feedback factor and total load capacitance matter;
- capacitor sizing is tied to both noise and settling.

The PDF also gives a first-order input-referred budget for a 10-bit, 1 V
differential full-scale example:

```text
thermal noise ~= quantization noise
SHA: about 1/3
stage 1: about 1/3
remaining stages: about 1/3
```

## Calibration Consequence

Pipeline calibration should state which errors it targets:

```text
repeatable gain error -> potentially calibratable
repeatable DAC transition error -> potentially calibratable
linear settling residue -> maybe calibratable as gain/error term
random thermal noise -> not digitally removable
slewing/nonlinear settling -> not captured by one gain coefficient
memory effects -> require dynamic model or validation
```

This page complements:

- [Pipeline residue box and gain observability](pipeline_residue_box_gain_observability.md)

The residue must first remain observable. Then the OTA/noise budget determines
whether the observation is accurate enough and whether the error is stable
enough to calibrate.

## Failure Modes

- Treating finite OTA gain as a constant when it is signal-dependent.
- Ignoring settling tails or slewing and reporting only static gain.
- Calibrating a gain coefficient on one operating point and applying it across
  amplitude, frequency, or PVT without validation.
- Confusing random thermal noise with deterministic calibration residual.
- Ignoring SHA-less timing mismatch between MDAC and sub-ADC sampling paths.

## What This Does Not Prove

- It does not implement a Pipeline ADC model in ADCToolbox.
- It does not derive a full OTA design equation from device physics.
- It does not quantify PVT drift.
- It does not prove background calibration convergence.

## Next Work

If ADCToolbox adds a Pipeline behavioral model, include parameters for finite
gain, settling time constant, noise, and residue-box overload, then validate
calibration separately from noise-limited performance.
