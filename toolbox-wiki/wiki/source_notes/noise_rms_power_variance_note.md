# Source Note: Probability, Noise, RMS, Power, And Variance

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/04_概率噪声_RMS_功率_方差.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/04_概率噪声_RMS_功率_方差.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/_estimate_noise_power.py
rigor:
  - source-confirmed
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

ADC noise and dynamic metrics are power questions: signal, noise, and
distortion must be compared through RMS, variance, and dB conventions.

## Key Extracted Ideas

- Noise sources such as thermal noise, comparator noise, clock jitter, supply
  noise, and quantization error are modeled as random variables.
- Nonzero mean behaves like offset; zero-mean random error contributes noise
  power.
- For zero-mean noise, average power is tied to variance.
- RMS is `sqrt(E[x^2])`.
- For a sine with amplitude `A`, RMS is `A/sqrt(2)`.
- Power ratios use `10*log10`; amplitude ratios use `20*log10` when impedance
  is equal.
- White noise is approximately flat in frequency, but the white quantization
  noise model requires independence assumptions.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [ADC metrics source note](adc_metrics_ch3.md)

## Rigor Notes

SNDR, SNR, NSD, and ENOB claims should be traced to explicit signal and noise
power definitions. Mixing amplitude and power dB conventions is a common source
of metric mistakes.

## Open Follow-Up

Create a short concept page for ADC noise-power bookkeeping if future metric
pages become too dense.
