# Source Note: ADC Key Metric And Concept DOCX

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/ADC关键metric及concept.docx
source_links:
  - ../../raw/resources/ADCtoolbox/ADC关键metric及concept.docx
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/metrics.py
rigor:
  - source-confirmed
  - learner-note
  - theory-supported
  - open-question
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

This DOCX is a learner-oriented metric bridge: it links sampling, quantization,
static linearity, dynamic metrics, and the reminder that every mathematical
operation should map back to a physical circuit or test condition.

## Key Extracted Ideas

- ADC converts continuous-time, continuous-amplitude signals into sampled and
  quantized digital codes.
- Sampling theory explains aliasing; high-frequency components must be moved
  away, attenuated, or sampled fast enough.
- Quantization creates a bounded error under ideal assumptions, but practical
  ADCs add circuit-dependent nonidealities.
- LSB and full-scale range must be defined before comparing errors.
- DNL describes local code-width deviation; DNL near `-1 LSB` indicates missing
  or nearly missing codes.
- INL describes accumulated deviation of the transfer curve from a chosen
  reference line.
- SNR excludes distortion, while SNDR/SINAD includes both noise and distortion.
- ENOB is a derived dynamic metric from SNDR, not an independent physical bit
  count.
- Static DNL/INL and dynamic SNDR/ENOB can disagree because they stress
  different aspects of the converter.
- Dither appears both as a quantization-error decorrelation idea and as a
  calibration/estimation aid.

## Integration Into The Wiki

This source supports:

- [FFT metrics](../concepts/fft_metrics.md)
- [ADC performance metrics chapter](adc_metrics_ch3.md)
- [Data converter testing](data_converter_testing_ch17.md)
- [Dither](dither_note.md)
- [Spectrum source](../source_code/compute_spectrum_py.md)
- [Spectrum metric statistical risks](../rigor/spectrum_metric_statistical_risks.md)

## ADCToolbox Learning Meaning

This note is useful when reading ADCToolbox metric outputs. It keeps the learner
from treating metric names as pure software labels. Each metric has a circuit
or measurement origin:

```text
transfer curve width errors -> DNL
transfer curve accumulated deviation -> INL
spectral noise power -> SNR
spectral noise plus distortion -> SNDR/SINAD
largest spur relative to signal -> SFDR
SNDR converted to ideal-bit equivalent -> ENOB
```

## Rigor Notes

- ENOB derived from SNDR assumes the ideal quantization-noise relationship; it
  should not be used as a complete description of converter quality.
- DNL and INL depend on the chosen transition-level model and reference line.
- Metric claims need units, bandwidth, amplitude, input frequency, and analysis
  method.
- This is a learner note, so formal definitions should be checked against
  handbook or code pages before promotion to `stable`.

## Open Follow-Up

Create a compact comparison table linking `metrics.py` outputs to formulas,
units, required FFT settings, and failure modes.
