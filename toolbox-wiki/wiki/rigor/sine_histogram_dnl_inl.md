# Sine Histogram DNL And INL

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/17_ch17_数据转换器测试.md
source_links:
  - ../source_notes/sun_testing_primary_pdf_distillation.md
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch17 Data Converter Testing.pdf
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

Sine-histogram DNL/INL extraction is a statistical estimator of ADC code widths.
It is useful when a highly linear ramp is impractical, but it depends on input
distribution correction, monotonicity, and noise assumptions.

## Evidence Map

- `ch17 Data Converter Testing.pdf`, pages 33-36: sine-input histogram and
  sinusoidal-PDF correction.
- `ch17 Data Converter Testing.pdf`, pages 37-38: MATLAB-style DNL/INL code.
- `ch17 Data Converter Testing.pdf`, page 39: limitations of histogram testing.
- `wiki/source_notes/sun_testing_primary_pdf_distillation.md`

## Why Sine Input Is Used

The PDF states the practical motivation:

- a linear ramp must be more linear than the ADC;
- for high-resolution ADCs this ramp requirement becomes difficult;
- a sinusoidal source can be much easier to make clean;
- the raw sine histogram is not flat, so it must be transformed.

## Core Algorithm

The slide code uses the cumulative histogram:

```text
h[k]  = count of output code k
ch[k] = cumulative sum of h
```

Then it maps cumulative probability through the inverse sine distribution. In
the slide code this appears as:

```text
T = -cos(pi * ch / sum(h))
```

Code widths are estimated by adjacent transition differences:

```text
hlin = T[2:end] - T[1:end-1]
```

After truncating unreliable edge bins, an average LSB is computed:

```text
lsb = sum(hlin_trunc) / length(hlin_trunc)
```

Then:

```text
DNL = hlin_trunc / lsb - 1
INL = cumulative sum of DNL
```

The PDF also uses a missing-code threshold:

```text
missing code if DNL < -0.9 LSB
```

## Amplitude And Offset Claim

The PDF notes that exact sine amplitude and offset do not need to be known for
this method. The reason is that the cumulative distribution is inverted after
observing the occupied code range, so the shape correction is driven by code
statistics rather than an externally known voltage ramp.

This does not mean amplitude and offset are irrelevant for every test. If the
sine does not sufficiently cover the code range, or if clipping/underdrive
affects edge bins, truncation and coverage become part of the uncertainty.

## Required Assumptions

- The ADC transfer is monotonic enough for code-density interpretation.
- The input is close enough to sinusoidal for the PDF correction to be valid.
- Enough samples are collected for stable code counts.
- Edge bins are truncated or handled consistently.
- Noise does not smear DNL beyond recognition.
- Sparkle-code or code-flip behavior is checked separately from the histogram.

## Failure Modes From The PDF

The testing PDF explicitly warns:

- histogram testing assumes monotonicity;
- code flips may not be detected;
- dynamic sparkle codes can create only minor DNL/INL changes;
- noise can smear DNL;
- INL may look more robust than local DNL, so both must be inspected.

## ADCToolbox Meaning

This page is currently a source-aligned rigor page, not a code page. If
ADCToolbox implements sine-histogram DNL/INL in Python, the source-code page
should map directly to this algorithm:

```text
histogram -> cumulative histogram -> inverse sine CDF -> code widths -> DNL -> INL
```

For calibration validation, this method should be separate from FFT ENOB/SNDR:

- FFT metrics test dynamic spectral behavior.
- Sine-histogram DNL/INL tests static-like code-width behavior under a known
  statistical input.

## What This Does Not Prove

- It does not prove no sparkle codes exist.
- It does not prove monotonicity.
- It does not replace direct transition-level measurement when that is
  available.
- It does not provide uncertainty intervals without sample-count analysis.

## Related Pages

- [Sun Testing primary PDF distillation](../source_notes/sun_testing_primary_pdf_distillation.md)
- [Training and validation split](../workflows/training_validation_split.md)
- [Spectrum metric statistical risks](spectrum_metric_statistical_risks.md)

## Next Work

Create a Python source-code page if or when ADCToolbox adds a sine-histogram
DNL/INL implementation.
