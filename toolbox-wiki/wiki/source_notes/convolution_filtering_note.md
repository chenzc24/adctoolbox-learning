# Source Note: Convolution, Filtering, And Frequency-Domain Multiplication

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/07_卷积_滤波_频域乘法.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/07_卷积_滤波_频域乘法.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
rigor:
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Filtering is convolution in time and multiplication in frequency, which is the
core language behind anti-alias filters, decimation filters, averaging, and
Sigma-Delta noise removal.

## Key Extracted Ideas

- Discrete convolution can be written as `y[n] = sum x[k]*h[n-k]`.
- The impulse response `h` describes how a linear time-invariant system
  responds to a single impulse.
- Low-pass filters preserve low frequencies and attenuate high frequencies.
- Time-domain convolution corresponds to frequency-domain multiplication.
- Anti-alias filtering, decimation filtering, and reconstruction filtering all
  rely on this idea.
- Moving average is also convolution; it reduces random noise but changes the
  frequency response and bandwidth.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [Oversampling ADCs](oversampling_adc_ch14.md)
- [Data converter testing](data_converter_testing_ch17.md)

## Rigor Notes

Averaging is not free. Any claim that averaging or filtering improves noise
should also state what bandwidth or frequency response changed.

## Open Follow-Up

Add decimation-filter detail when Sigma-Delta or oversampling workflows become
central.
