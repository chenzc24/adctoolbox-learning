# Coverage Matrix

```yaml
scope: toolbox-wiki
status: draft
last_updated: 2026-06-03
```

Use this file to track whether important ADCToolbox topics have concept,
source-code, workflow, rigor, and source-note coverage.

| Area | Concept | Source Code | Workflow | Rigor | Source Notes | Status |
| --- | --- | --- | --- | --- | --- | --- |
| SAR behavioral model | partial | yes | partial | partial | yes | seed |
| ADC weight calibration | yes | yes | yes | partial | yes | usable |
| Full sine-weight calibration | partial | yes | yes | partial | yes | seed |
| Lite sine-weight calibration | partial | yes | partial | partial | yes | seed |
| Rank deficiency / redundancy | planned | yes | partial | partial | yes | seed |
| FFT spectrum metrics | yes | yes | planned | partial | yes | seed |
| Sine fitting | partial | yes | planned | partial | yes | seed |
| Validation split | planned | no | planned | planned | no | gap |
| Raw ADC course notes | partial | n/a | n/a | partial | yes | seed |
| MATLAB learning bridge | planned | n/a | planned | n/a | planned | gap |

## Existing Coverage

- `wiki/concepts/adc_weight_calibration.md`
- `wiki/source_code/sar_py.md`
- `wiki/source_code/calibrate_weight_sine_lite_py.md`
- `wiki/source_code/calibrate_weight_sine_py.md`
- `wiki/source_code/compute_spectrum_py.md`
- `wiki/source_code/fit_sine_4param_py.md`
- `wiki/source_code/patch_rank_deficiency_py.md`
- `wiki/workflows/sar_model_to_calibration.md`
- `wiki/rigor/mathematical_rigor_gaps.md`
- `wiki/rigor/identifiability_conditions.md`
- `wiki/concepts/fft_metrics.md`
- `wiki/source_notes/adc_metrics_ch3.md`
- `wiki/source_notes/fft_sampling_note.md`
- `wiki/source_notes/least_squares_calibration_note.md`
- `wiki/source_notes/sar_low_power_ch12a.md`

## Highest Priority Gaps

1. `wiki/workflows/spectrum_validation_before_after_calibration.md`
2. `wiki/rigor/spectrum_metric_statistical_risks.md`
3. `wiki/rigor/redundant_sar_reachability.md`
4. `wiki/concepts/rank_deficiency.md`
5. `wiki/concepts/least_squares_adc_calibration.md`
6. `wiki/source_notes/matlab_bridge_note.md`

## Promotion Rule

A row can move from `seed` to `usable` only when it has:

- One concept page.
- One source-code page, if code exists.
- One workflow or example note.
- One rigor entry listing assumptions and validation obligations.
- At least one source note when raw learning material exists.

A row can move from `usable` to `stable` only when links are checked, examples
are mapped, and open questions are either answered or explicitly deferred.
