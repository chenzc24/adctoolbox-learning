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
| Rank deficiency / redundancy | yes | yes | partial | yes | yes | usable |
| FFT spectrum metrics | yes | yes | yes | yes | yes | usable |
| Sine fitting | partial | yes | planned | partial | yes | seed |
| Validation split | planned | no | yes | partial | yes | seed |
| Testing and FOM | partial | yes | planned | partial | yes | seed |
| Noise and quantization model | partial | yes | planned | partial | yes | seed |
| Sampling/comparator circuit nonidealities | partial | yes | planned | yes | yes | usable |
| Pipeline ADC calibration context | partial | planned | planned | partial | yes | usable |
| Oversampling and filtering context | partial | yes | planned | partial | yes | seed |
| Raw ADC course notes | partial | n/a | n/a | partial | yes | usable |
| Sun-course source fidelity | partial | n/a | n/a | partial | yes | usable |
| PDF/DOCX source distillation | partial | n/a | planned | partial | yes | seed |
| MATLAB learning bridge | partial | n/a | partial | n/a | yes | seed |
| Example evidence notes | partial | yes | partial | partial | yes | usable |
| Retrieval and maintenance structure | yes | n/a | yes | yes | n/a | stable |

## Existing Coverage

- `wiki/concepts/adc_weight_calibration.md`
- `wiki/source_code/sar_py.md`
- `wiki/source_code/calibrate_weight_sine_lite_py.md`
- `wiki/source_code/calibrate_weight_sine_py.md`
- `wiki/source_code/compute_spectrum_py.md`
- `wiki/source_code/fit_sine_4param_py.md`
- `wiki/source_code/patch_rank_deficiency_py.md`
- `wiki/source_code/window_py.md`
- `wiki/source_code/estimate_noise_power_py.md`
- `wiki/source_code/spectrum_helper_chain_py.md`
- `wiki/source_code/calibration_helper_chain_py.md`
- `wiki/source_code/analyze_spectrum_py.md`
- `wiki/source_code/quick_sndr_py.md`
- `wiki/source_code/frequency_py.md`
- `wiki/workflows/sar_model_to_calibration.md`
- `wiki/workflows/spectrum_validation_before_after_calibration.md`
- `wiki/workflows/training_validation_split.md`
- `wiki/rigor/mathematical_rigor_gaps.md`
- `wiki/rigor/identifiability_conditions.md`
- `wiki/rigor/spectrum_metric_statistical_risks.md`
- `wiki/rigor/redundant_sar_reachability.md`
- `wiki/rigor/sar_noise_formula_alignment.md`
- `wiki/rigor/sine_histogram_dnl_inl.md`
- `wiki/rigor/pipeline_residue_box_gain_observability.md`
- `wiki/rigor/pipeline_ota_settling_noise_budget.md`
- `wiki/concepts/fft_metrics.md`
- `wiki/concepts/least_squares_adc_calibration.md`
- `wiki/concepts/rank_deficiency.md`
- `wiki/source_notes/adc_metrics_ch3.md`
- `wiki/source_notes/adc_metric_concept_docx.md`
- `wiki/source_notes/adc_physical_system_structure_docx.md`
- `wiki/source_notes/adc_test_analysis_calibration_pdf.md`
- `wiki/source_notes/data_conversion_handbook_note.md`
- `wiki/source_notes/adc_fom_ch16.md`
- `wiki/source_notes/data_converter_testing_ch17.md`
- `wiki/source_notes/sampling_circuit_ch5.md`
- `wiki/source_notes/comparator_ch7.md`
- `wiki/source_notes/flash_adc_ch8.md`
- `wiki/source_notes/folding_interpolating_adc_ch9.md`
- `wiki/source_notes/pipeline_adc_concept_ch10.md`
- `wiki/source_notes/pipeline_adc_implementation_ch11.md`
- `wiki/source_notes/fft_sampling_note.md`
- `wiki/source_notes/complex_phase_systems_note.md`
- `wiki/source_notes/matrix_rank_observability_note.md`
- `wiki/source_notes/least_squares_calibration_note.md`
- `wiki/source_notes/noise_rms_power_variance_note.md`
- `wiki/source_notes/quantization_noise_model_note.md`
- `wiki/source_notes/sar_low_power_ch12a.md`
- `wiki/source_notes/high_speed_sar_ch12b.md`
- `wiki/source_notes/switched_cap_settling_noise_ch6.md`
- `wiki/source_notes/time_interleaving_ch13.md`
- `wiki/source_notes/oversampling_adc_ch14.md`
- `wiki/source_notes/convolution_filtering_note.md`
- `wiki/source_notes/dither_note.md`
- `wiki/source_notes/linear_algebra_vectors_matrices_note.md`
- `wiki/source_notes/matlab_code_reading_note.md`
- `wiki/source_notes/matlab_fundamentals_bridge.md`
- `wiki/source_notes/sun_sar_primary_pdf_distillation.md`
- `wiki/source_notes/sun_pipeline_primary_pdf_distillation.md`
- `wiki/source_notes/sun_testing_primary_pdf_distillation.md`
- `wiki/source_notes/examples/exp_a01_fit_sine_4param.md`
- `wiki/source_notes/examples/exp_d01_cal_weight_sine_lite.md`
- `wiki/source_notes/examples/exp_d02_cal_weight_sine.md`
- `wiki/source_notes/examples/exp_d03_redundancy_comparison.md`
- `wiki/source_notes/examples/exp_d16_sar_unit_cap_mismatch_mc.md`
- `wiki/source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md`
- `audits/source_fidelity_sun_course_2026-06-03.md`
- `audits/sun_course_slide_evidence_map_2026-06-03.md`
- `audits/sar_reachability_example_weight_audit_2026-06-03.md`
- `schema/PROMOTION_RULES.md`
- `schema/SEMANTIC_LINT_CHECKLIST.md`
- `schema/PROOF_PAGE_TEMPLATE.md`
- `schema/EXAMPLE_NOTE_TEMPLATE.md`
- `tools/lint_wiki.py`
- `tools/search_wiki.py`
- `tools/audit_sar_reachability.py`
- `wiki/workflows/example_ingest_map.md`

## Highest Priority Gaps

1. `wiki/source_code/metrics_py.md`
2. `wiki/source_code/units_py.md`
3. Add train/validation diagnostic export support to calibration examples.
4. Automate regeneration of
   `audits/sar_reachability_example_weight_audit_2026-06-03.md` from example
   weight lists.
5. Source notes for remaining PDF/DOCX sources: `ADC核心概念详细解析.pdf`,
   `ADC工作物理系统结构.docx` follow-up details, `MATLAB.docx`, and selected
   handbook chapter-level pages.
6. Next example candidates from `wiki/workflows/example_ingest_map.md`
7. MATLAB-to-Python translation comparison table.
8. Slide-level primary-source formula/figure review for the most
   calibration-critical Sun-course PDFs.

## Promotion Rule

A row can move from `seed` to `usable` only when it has:

- One concept page.
- One source-code page, if code exists.
- One workflow or example note.
- One rigor entry listing assumptions and validation obligations.
- At least one source note when raw learning material exists.

A row can move from `usable` to `stable` only when links are checked, examples
are mapped, and open questions are either answered or explicitly deferred.
