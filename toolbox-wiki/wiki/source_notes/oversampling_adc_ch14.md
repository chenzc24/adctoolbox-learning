# Source Note: Oversampling ADCs And Noise Shaping

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/14_ch14_过采样ADC.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/14_ch14_过采样ADC.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
rigor:
  - theory-supported
  - engineering-heuristic
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

Oversampling spreads quantization noise over a wider Nyquist band, while
Sigma-Delta noise shaping pushes more quantization noise out of the signal band
so digital filtering can remove it.

## Key Extracted Ideas

- `OSR = fs / (2*fB)`, where `fB` is signal bandwidth.
- If quantization noise is white over `0..fs/2`, only `1/OSR` of it falls in
  the signal band.
- Plain oversampling improves in-band SNR by about `10*log10(OSR)` dB.
- Doubling OSR gives roughly 3 dB, or about half a bit, without noise shaping.
- Sigma-Delta uses feedback and integrators so STF is near one and NTF is small
  in band but large out of band.
- Higher-order shaping improves in-band noise reduction but creates stability
  and overload challenges.
- One-bit quantizers avoid multi-bit feedback DAC mismatch, but need high OSR.
- Multi-bit quantizers reduce noise and OSR needs, but feedback DAC linearity
  becomes important.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [Quantization noise model](quantization_noise_model_note.md)
- [Convolution and filtering](convolution_filtering_note.md)

## Rigor Notes

OSR only improves in-band noise under a noise-distribution assumption. Noise
shaping adds loop stability and out-of-band filtering requirements that are not
captured by a simple Nyquist ADC spectrum metric alone.

## Open Follow-Up

Add a Sigma-Delta topic page only after the core SAR/calibration path is more
complete.
