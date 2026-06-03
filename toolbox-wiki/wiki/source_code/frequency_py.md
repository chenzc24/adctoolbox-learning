# `frequency.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/fundamentals/frequency.py
  - ../../../../../python/src/adctoolbox/fundamentals/fit_sine_4param.py
  - ../../../../../python/src/adctoolbox/spectrum/_harmonics.py
  - ../../../../../python/src/adctoolbox/calibration/_estimate_frequencies.py
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

`frequency.py` provides the coherent-sampling, alias-folding, bin-folding, and
frequency-estimation utilities that keep spectrum and calibration code using
consistent frequency conventions.

## Public API Purpose

Important functions:

- `find_coherent_frequency(fs, fin_target, n_fft, force_odd=True, search_radius=200)`
- `fold_frequency_to_nyquist(fin, fs)`
- `fold_bin_to_nyquist(bin_idx, n_fft)`
- `estimate_frequency(data, frequency_estimate=None, fs=1.0)`

## Core Data Flow

```text
target frequency + fs + N
  -> coherent bin search
  -> exact coherent frequency

arbitrary frequency or harmonic bin
  -> fold to first Nyquist zone

signal data
  -> fit_sine_4param
  -> normalized frequency
  -> Hz frequency
```

## Why This Matters

Spectrum metrics and harmonic analysis depend on whether a tone or harmonic is
inside the first Nyquist zone or aliases back into it. Calibration also needs
frequency estimates when the training sine frequency is not provided.

## Important Implementation Choices

- Coherent search can force odd bins and coprime bin/N relation.
- Undersampling is allowed by not rejecting bins above `N/2`.
- `fold_bin_to_nyquist` supports fractional bins, which matters after
  fundamental interpolation.
- `estimate_frequency` delegates to `fit_sine_4param`.

## Assumptions

- Coherent-frequency search radius is large enough.
- Odd/coprime bin preferences match the test goal.
- Sine fitting can estimate the dominant tone.
- Folding to first Nyquist zone is the intended representation for real-signal
  FFT analysis.

## Rigor And Risks

- `source-confirmed`: frequency utilities are implemented directly in the
  source.
- `theory-supported`: coherent sampling and Nyquist folding follow standard DFT
  and sampling theory.
- `engineering-heuristic`: choosing odd/coprime bins is a test practice, not a
  mathematical requirement for all tasks.

## Related Pages

- [fit_sine_4param source](fit_sine_4param_py.md)
- [Spectrum helper chain](spectrum_helper_chain_py.md)
- [Calibration helper chain](calibration_helper_chain_py.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [FFT sampling source note](../source_notes/fft_sampling_note.md)

## Next Reading

Read `_harmonics.py` through the spectrum helper chain to see how folded bins
are used for THD and collided-harmonic detection.
