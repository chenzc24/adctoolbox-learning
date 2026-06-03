# Source Note: Sampling, DFT, And FFT

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/fundamentals/fit_sine_4param.py
rigor:
  - source-confirmed
  - theory-supported
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This raw note explains why ADC spectrum analysis depends on sampling rate,
record length, DFT bin spacing, leakage, coherence, and windowing.

## Key Extracted Ideas

- Sampling replicates spectra around multiples of the sampling frequency.
- Aliasing occurs when replicated spectra overlap in the band of interest.
- Nyquist rate avoids baseband overlap only when out-of-band content is also
  controlled.
- DFT bin spacing is `df = fs / N`.
- Non-coherent input frequencies leak energy into neighboring bins.
- Windows and coherent sampling are two different ways to manage leakage.
- FFT is the fast algorithm for computing the DFT, not a different transform.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [compute_spectrum source](../source_code/compute_spectrum_py.md)
- [fit_sine_4param source](../source_code/fit_sine_4param_py.md)

## Rigor Notes

When a page cites FFT-derived ENOB, SNDR, SNR, THD, or SFDR, it should specify
the sampling and binning conditions. Otherwise the number may be hard to
compare across experiments.

## Open Follow-Up

Add a worked example showing the same ADC waveform analyzed with coherent
sampling, Hann windowing, and an intentionally bad non-coherent record.
