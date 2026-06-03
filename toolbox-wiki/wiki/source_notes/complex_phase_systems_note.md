# Source Note: Complex Numbers, Phase, Laplace, And Systems View

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/09_复数_相位_拉普拉斯和系统观点.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/09_复数_相位_拉普拉斯和系统观点.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/fundamentals/fit_sine_4param.py
rigor:
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Complex numbers and systems thinking unify magnitude, phase, delay, filtering,
settling, and noise transfer in ADC analysis.

## Key Extracted Ideas

- `exp(j*w*t) = cos(w*t) + j*sin(w*t)` unifies sine and cosine.
- Frequency-domain points carry both magnitude and phase.
- Time delay becomes phase rotation at a given frequency.
- Sampling jitter, group delay, filter phase, and channel skew can be understood
  through phase.
- Laplace-domain transfer functions `H(s)` describe analog dynamics,
  stability, and transients.
- Discrete systems use related `z`-domain thinking.
- Sigma-Delta analysis uses STF and NTF to describe how signal and quantization
  noise transfer to the output.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [fit_sine_4param source](../source_code/fit_sine_4param_py.md)
- [Oversampling ADCs](oversampling_adc_ch14.md)
- [Convolution and filtering](convolution_filtering_note.md)

## Rigor Notes

This note is conceptual scaffolding. It does not prove a calibration algorithm,
but it explains why phase, complex spectra, group delay, and transfer functions
matter in ADC validation.

## Open Follow-Up

Use this source when writing future pages on jitter, channel skew, or
Sigma-Delta loop behavior.
