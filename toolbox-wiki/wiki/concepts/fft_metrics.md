# FFT Metrics

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../source_notes/adc_metrics_ch3.md
  - ../source_notes/fft_sampling_note.md
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

FFT-based ADC metrics are only meaningful when the signal bin, harmonic bins,
noise bins, window, coherence, and in-band range are defined consistently.

## Core Metrics

- SNR: signal power divided by noise power.
- SNDR/SINAD: signal power divided by noise plus distortion.
- ENOB: `(SNDR - 1.76) / 6.02`.
- SFDR: signal power relative to the largest spur.
- THD: total harmonic power relative to the signal.
- NSD: noise density after normalizing by in-band bandwidth.

## Why Settings Matter

An FFT record is a finite observation. If the input tone is not coherent with
the record length, energy leaks into neighboring bins. A window reduces leakage
but changes gain and equivalent noise bandwidth. A side-bin rule decides which
nearby bins count as the signal and which count as noise.

Therefore, "ENOB improved" is incomplete unless the page also records:

- record length `N`;
- sampling rate `fs`;
- input frequency or fundamental bin;
- window type;
- side-bin rule;
- OSR or in-band range;
- harmonic and noise exclusion method.

## Connection To ADCToolbox

`compute_spectrum.py` encodes these choices through `win_type`, `side_bin`,
`osr`, `max_harmonic`, `nf_method`, `coherent_averaging`, and `cutoff_freq`.

The function returns both final metrics and `plot_data`, so a learning note can
inspect not only the number but also the bin choices that produced the number.

## Assumptions

- The fundamental is correctly located.
- The FFT settings match the measurement scenario.
- Harmonics fold to the expected bins.
- Noise and distortion are separated according to the intended metric
  definition.

## Rigor And Risks

- `source-confirmed`: ADCToolbox reports the bins and settings used by
  `compute_spectrum`.
- `theory-supported`: DFT binning, leakage, windowing, and ENOB formulas are
  standard ADC-test concepts.
- `engineering-heuristic`: automatic bin choices are convenient defaults.
- `open-question`: metric pages should eventually include a comparison between
  coherent and non-coherent records for the same waveform.

## Related Pages

- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [ADC metrics source note](../source_notes/adc_metrics_ch3.md)
- [FFT sampling source note](../source_notes/fft_sampling_note.md)
- [SAR model to calibration workflow](../workflows/sar_model_to_calibration.md)

## Next Reading

Read `compute_spectrum_py.md` after this page to see how these metric concepts
are implemented.
