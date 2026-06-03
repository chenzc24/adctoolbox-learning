# Source Note: ADC Test Analysis And Calibration PDF

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/ADC基础/ADC测试分析与校准.pdf
source_links:
  - ../../raw/resources/ADCtoolbox/ADC基础/ADC测试分析与校准.pdf
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine.py
  - ../../../../../python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This PDF is the closest raw source to the ADCToolbox learning path because it
connects ADC test bench discipline, FFT metric interpretation, linear-equation
calibration, and dither-based background calibration.

## Key Extracted Ideas

- ADC testing has two levels: functional correctness and performance
  characterization.
- Performance tests must record power, bias, signal source, clock source, DUT,
  capture path, and analysis method.
- Static precision includes offset, gain, DNL, and INL.
- Dynamic precision includes SNR, SNDR/SINAD, ENOB, SFDR, THD, IMD, bandwidth,
  aperture delay, and jitter.
- FFT analysis is useful only after the sampling setup, normalization, window,
  and bin policy are known.
- Spectrum shapes can diagnose different failures: broadband noise, harmonic
  distortion, clipping/dead zones, interleaving mismatch, coupling, and shaped
  noise.
- Calibration is framed as reducing the total error between analog input and
  corrected digital output.
- Many ADC error models can be written as linear equations in unknown
  parameters, especially bit weights, gain, offset, harmonic coefficients, and
  weak polynomial terms.
- Sine-input weight calibration becomes a least-squares problem when enough
  `Ain` and `Dout` samples are collected.
- Frequency-domain equations are legitimate for some calibration goals because
  the DFT is linear, but the objective then becomes explicitly band-limited.
- Dither calibration is presented as a background calibration family: inject a
  known pseudo-random perturbation and estimate error parameters by correlation.

## Integration Into The Wiki

This source supports:

- [ADC weight calibration](../concepts/adc_weight_calibration.md)
- [Least-squares ADC calibration](../concepts/least_squares_adc_calibration.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum source](../source_code/compute_spectrum_py.md)
- [Full sine-weight calibration source](../source_code/calibrate_weight_sine_py.md)
- [Spectrum validation before and after calibration](../workflows/spectrum_validation_before_after_calibration.md)
- [Identifiability conditions](../rigor/identifiability_conditions.md)

## ADCToolbox Learning Meaning

This PDF justifies the overall toolbox workflow:

```text
build a test bench or behavioral test case
  -> collect ADC output under controlled excitation
  -> interpret static and dynamic errors
  -> solve a parametric calibration model
  -> validate with independent spectrum and residual metrics
```

For the learner, the most important bridge is that `calibrate_weight_sine.py`
is not just "fitting numbers." It is an implementation of the linear-equation
calibration viewpoint, with the sine stimulus used to generate a sufficiently
rich set of equations.

## Rigor Notes

- The PDF gives the engineering idea of a full-rank or overdetermined equation
  system, but the wiki still needs a formal proof page stating exact
  identifiability assumptions.
- A least-squares result is not automatically a valid calibration. It still
  needs rank, conditioning, residual, and validation-set checks.
- Dither calibration requires assumptions about the injected signal:
  zero-mean, known amplitude, low correlation with user signal, and observable
  coupling to the target error parameter.
- Frequency-domain calibration must explicitly state whether it minimizes
  total error or only in-band error.

## Open Follow-Up

Create a workflow page that separates foreground sine-based calibration from
background dither-based calibration, including what data each method is allowed
to use.
