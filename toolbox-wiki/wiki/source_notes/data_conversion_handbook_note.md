# Source Note: Data Conversion Handbook

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/ADC基础/Data Conversion Handbook.pdf
source_links:
  - ../../raw/resources/ADCtoolbox/ADC基础/Data Conversion Handbook.pdf
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/fundamentals/fit_sine_4param.py
rigor:
  - source-confirmed
  - theory-supported
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

The handbook is a broad reference anchor for sampled-data fundamentals,
converter specifications, ADC architectures, and converter test methods.

## Key Extracted Ideas

- The handbook separates sampled-data fundamentals, converter architectures,
  process technology, test methods, signal conditioning, support circuits, and
  applications.
- Chapter 2 is the most relevant theory anchor for quantization, coding,
  sampling, AC errors, SNR, SINAD, ENOB, SFDR, aperture jitter, and general
  specifications.
- Chapter 3 anchors architecture vocabulary: DAC structures, Flash ADCs, SAR
  ADCs, subranging, pipelined ADCs, folding ADCs, integrating converters, and
  sigma-delta converters.
- Chapter 5 anchors test practice: static transfer tests, DNL/INL measurement,
  histogram or code-density tests, sine-fitting ENOB tests, FFT setup, NPR
  tests, and aperture jitter measurement.
- The handbook treats Flash as a direct architecture and also as a sub-block
  inside higher-speed subranging and pipelined ADCs.
- SAR and Pipeline ADC histories show why the same calibration vocabulary
  appears across architectures: DAC weight errors, comparator behavior, residue
  gain, and digital correction are recurring themes.

## Integration Into The Wiki

This source supports:

- [ADC metrics chapter](adc_metrics_ch3.md)
- [Data converter testing](data_converter_testing_ch17.md)
- [Flash ADCs](flash_adc_ch8.md)
- [Folding and interpolating ADCs](folding_interpolating_adc_ch9.md)
- [Pipeline ADC concept](pipeline_adc_concept_ch10.md)
- [Low-power SAR ADC](sar_low_power_ch12a.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Sine fitting source](../source_code/fit_sine_4param_py.md)

## ADCToolbox Learning Meaning

Use this source as a reference map rather than a single linear lesson. When a
wiki page mentions a metric or architecture, the handbook usually provides the
standard engineering context and vocabulary.

For ADCToolbox specifically:

- `compute_spectrum.py` aligns with the handbook's dynamic ADC testing path.
- `fit_sine_4param.py` aligns with sine-wave curve-fitting based performance
  measurement.
- SAR and Pipeline model pages should use the handbook as a terminology check
  when defining bit weights, residue, and dynamic metrics.

## Rigor Notes

- The handbook is broad and authoritative, but a source note should not import
  claims blindly. Each wiki page still needs a local assumption list and a code
  linkage.
- Historical and architecture sections are useful context, but calibration
  proofs should rely on explicit mathematical pages in `wiki/rigor/`.
- Dynamic metric definitions must be paired with test configuration details:
  coherent sampling, FFT length, windowing, harmonic treatment, and bandwidth.

## Open Follow-Up

Add chapter-specific source notes only when a page needs them. The highest
value targets are Chapter 2 sampled-data fundamentals and Chapter 5 converter
testing.
