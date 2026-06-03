# Source Note: Sun Course Testing Primary PDF Distillation

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/17_ch17_数据转换器测试.md
source_links:
  - ../../raw/resources/ADCtoolbox/ADC基础/孙老师课件/ch17 Data Converter Testing.pdf
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/17_ch17_数据转换器测试.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/analyze_spectrum.py
  - ../../../../../python/src/adctoolbox/fundamentals/fit_sine_4param.py
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

The original testing PDF stresses that ADC metrics are only credible when the
test setup, source quality, clock jitter, histogram assumptions, and FFT
analysis settings are controlled.

## Direct PDF Distillation

- Testing a high-performance ADC can be almost as difficult as designing it
  because instruments must exceed the ADC under test.
- Signal-source linearity, filter distortion, clock source quality, and clock
  interface jitter can dominate the measured ADC result.
- Jitter-induced noise has a recognizable signature: it scales with input
  frequency and input amplitude.
- DNL/INL for an ADC require decision-level information; histogram testing
  estimates code widths rather than directly measuring all transition voltages.
- A sine-input histogram is useful because a very linear ramp is hard to
  generate, but the sine histogram must be linearized because it is not flat.
- Histogram testing assumes monotonicity; code flips and dynamic sparkle codes
  can be missed.
- Noise can smear DNL, while INL is often more robust, so both DNL and INL must
  be inspected.
- FFT-based spectral testing measures dynamic metrics, but the test setup and
  analysis choices determine whether those metrics are comparable.

## ADCToolbox Meaning

This PDF is a primary-source anchor for the validation workflow:

```text
controlled source and clock
  -> captured ADC output
  -> histogram or FFT analysis
  -> metric interpretation
  -> calibration comparison
```

For ADCToolbox, the important consequence is that `compute_spectrum.py` and
`analyze_spectrum.py` are only the analysis layer. They cannot by themselves
guarantee that the input source, clock, filtering, or capture setup was valid.

## Static Metrics Meaning

Histogram-based DNL/INL extraction is a statistical method with assumptions:

- the input distribution must be known or recoverable;
- the converter should be monotonic for the method to be reliable;
- noise can hide local DNL features;
- missing codes require direct attention, not only smooth INL curves.

## Dynamic Metrics Meaning

FFT metrics should not be recorded without:

- sample rate;
- input frequency;
- input amplitude;
- coherent/non-coherent condition;
- window choice;
- FFT length;
- side-bin policy;
- harmonic count;
- bandwidth definition;
- source and clock quality assumptions.

## Integration Into The Wiki

This source supports:

- [Data converter testing](data_converter_testing_ch17.md)
- [ADC test analysis and calibration PDF](adc_test_analysis_calibration_pdf.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum source](../source_code/compute_spectrum_py.md)
- [Spectrum validation before and after calibration](../workflows/spectrum_validation_before_after_calibration.md)
- [Spectrum metric statistical risks](../rigor/spectrum_metric_statistical_risks.md)

## Rigor Notes

- A spectrum improvement after calibration is not sufficient unless the before
  and after captures use comparable settings.
- Histogram DNL/INL is not a universal static truth; it is a model-dependent
  estimator with monotonicity and noise assumptions.
- Clock jitter and signal-source distortion can masquerade as ADC limitations.
- Calibration papers or examples should state whether validation is done on
  independent data.

## Open Follow-Up

Write `wiki/workflows/training_validation_split.md` and include a required
measurement-settings checklist for any before/after metric claim.
