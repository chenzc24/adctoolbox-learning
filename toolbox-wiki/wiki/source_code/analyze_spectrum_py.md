# `analyze_spectrum.py`

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md
source_links:
  - ../../../../../python/src/adctoolbox/spectrum/analyze_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/compute_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/plot_spectrum.py
  - ../../../../../python/src/adctoolbox/spectrum/plot_spectrum_virtuoso.py
rigor:
  - source-confirmed
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: high
```

## One-Sentence Takeaway

`analyze_spectrum.py` is the user-facing wrapper that computes spectrum metrics
and optionally plots them.

## Public API Purpose

Public functions:

- `analyze_spectrum(...)`
- `analyze_spectrum_virtuoso(...)`

Both call `compute_spectrum(...)`, optionally plot, and return only
`results["metrics"]`.

## Core Data Flow

```text
data and spectrum settings
  -> compute_spectrum(...)
  -> optional warning for collided harmonics
  -> optional plot_spectrum or plot_spectrum_virtuoso
  -> metrics dict
```

## Important Difference From `compute_spectrum`

`compute_spectrum.py` returns both `metrics` and `plot_data`. The wrapper
returns only the metric dictionary. Use `compute_spectrum` when you need bin
diagnostics or want to audit exactly how a number was produced.

## Virtuoso Variant

`analyze_spectrum_virtuoso` uses the same calculation engine but defaults to a
rectangular window and a Virtuoso-style plotter. This is a display/workflow
choice, not a different metric theory.

## Assumptions

- Plotting is optional and should not be confused with metric calculation.
- Returned metrics are downstream of the same `compute_spectrum` assumptions.
- Users who need reproducible comparisons should record all spectrum settings.

## Rigor And Risks

- `source-confirmed`: wrapper calls and return shape are visible in the source.
- `engineering-heuristic`: default plot styles and wrapper defaults are
  workflow choices.
- The wrapper can hide useful diagnostic fields by returning only `metrics`.

## Related Pages

- [compute_spectrum source](compute_spectrum_py.md)
- [Spectrum helper chain](spectrum_helper_chain_py.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Spectrum validation workflow](../workflows/spectrum_validation_before_after_calibration.md)

## Next Reading

Use `compute_spectrum_py.md` for metric internals and this page for the public
plotting workflow.
