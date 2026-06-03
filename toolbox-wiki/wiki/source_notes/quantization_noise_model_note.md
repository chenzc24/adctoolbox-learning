# Source Note: Quantization Error And White Noise Model

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/05_量化误差与白噪声模型.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/02_数学学习_ADC校准所需/05_量化误差与白噪声模型.md
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

The ideal quantization-noise model is a useful approximation, but it depends on
input coverage and decorrelation assumptions that often fail in real tests.

## Key Extracted Ideas

- Quantization error is `e = Q(x) - x`.
- For an ideal uniform quantizer, error is usually bounded by `-LSB/2` to
  `+LSB/2`.
- If error is uniform over that interval, variance is `LSB^2 / 12`.
- This assumption supports the ideal ADC SNR approximation
  `SNR ~= 6.02N + 1.76 dB` for a full-scale sine.
- The model works best when the input spans many codes, avoids overload, and
  makes error approximately independent of the input.
- It can fail for small signals, DC inputs, coherent periodic error, idle tones,
  and simple input/sample frequency relationships.
- Dither can trade a higher noise floor for reduced deterministic spurs.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [ADC metrics source note](adc_metrics_ch3.md)
- [Data converter testing source note](data_converter_testing_ch17.md)

## Rigor Notes

Do not treat the ideal SNR formula as a measurement guarantee. It is a model
with assumptions about quantization error distribution and independence.

## Open Follow-Up

Create a future rigor page on when quantization error becomes a spur rather
than white noise.
