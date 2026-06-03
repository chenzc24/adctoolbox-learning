# Open Questions

```yaml
scope: toolbox-wiki
status: active
last_updated: 2026-06-03
```

This queue tracks unresolved mathematical, engineering, and learning-structure
questions. Do not silently delete an item; close it by linking the page that
answered it.

## Mathematical Calibration

- What rank and excitation conditions make ADC weight estimation identifiable?
  - Current link: `wiki/rigor/mathematical_rigor_gaps.md`
  - Partial answer: `wiki/rigor/identifiability_conditions.md`
  - Still needed: numerical examples and condition-number reporting rules.

- How should condition number, singular values, and weight covariance be
  reported for `calibrate_weight_sine`?
  - Current link: `wiki/source_code/calibrate_weight_sine_py.md`
  - Related code-chain page: `wiki/source_code/calibration_helper_chain_py.md`
  - Related primary source notes:
    `wiki/source_notes/sun_sar_primary_pdf_distillation.md`,
    `wiki/source_notes/sun_pipeline_primary_pdf_distillation.md`
  - Needed page: `wiki/rigor/least_squares_uncertainty.md`

- How much frequency error can be tolerated before solved weights are biased?
  - Current link: `wiki/source_code/calibrate_weight_sine_py.md`
  - Needed page: `wiki/rigor/frequency_weight_coupling.md`

## Redundant SAR

- When does redundant bit design guarantee reachability rather than only a
  larger nominal code span?
  - Current link: `wiki/source_code/sar_py.md`
  - Primary PDF source note:
    `wiki/source_notes/sun_sar_primary_pdf_distillation.md`
  - Needed page: `wiki/rigor/redundant_sar_reachability.md`

- How should missing-code, DNL, INL, and calibration success be separated in
  redundant SAR examples?
  - Current link: `wiki/workflows/sar_model_to_calibration.md`
  - Needed page: `wiki/workflows/redundant_sar_validation.md`

## Spectrum Validation

- Which FFT settings are required before comparing pre/post calibration ENOB?
  - Partial answer: `wiki/concepts/fft_metrics.md`
  - Source page: `wiki/source_code/compute_spectrum_py.md`
  - Workflow answer: `wiki/workflows/spectrum_validation_before_after_calibration.md`
  - Primary PDF source note:
    `wiki/source_notes/sun_testing_primary_pdf_distillation.md`
  - Still needed: example evidence notes using real before/after scripts.

- How should coherent sampling, window choice, side-bin removal, and noise
  estimation be recorded in every metric claim?
  - Partial answer: `wiki/rigor/spectrum_metric_statistical_risks.md`
  - Still needed: compare multiple examples and noise methods.

## Knowledge Base Maintenance

- Which raw Markdown resources have been ingested into reusable source notes?
  - Current link: `coverage_matrix.md`
  - Current source notes:
    `wiki/source_notes/adc_metrics_ch3.md`,
    `wiki/source_notes/adc_fom_ch16.md`,
    `wiki/source_notes/data_converter_testing_ch17.md`,
    `wiki/source_notes/fft_sampling_note.md`,
    `wiki/source_notes/matrix_rank_observability_note.md`,
    `wiki/source_notes/least_squares_calibration_note.md`,
    `wiki/source_notes/noise_rms_power_variance_note.md`,
    `wiki/source_notes/quantization_noise_model_note.md`,
    `wiki/source_notes/sar_low_power_ch12a.md`,
    `wiki/source_notes/sampling_circuit_ch5.md`,
    `wiki/source_notes/comparator_ch7.md`,
    `wiki/source_notes/pipeline_adc_concept_ch10.md`,
    `wiki/source_notes/pipeline_adc_implementation_ch11.md`,
    `wiki/source_notes/high_speed_sar_ch12b.md`,
    `wiki/source_notes/switched_cap_settling_noise_ch6.md`,
    `wiki/source_notes/time_interleaving_ch13.md`,
    `wiki/source_notes/oversampling_adc_ch14.md`,
    `wiki/source_notes/convolution_filtering_note.md`,
    `wiki/source_notes/dither_note.md`,
    `wiki/source_notes/linear_algebra_vectors_matrices_note.md`,
    `wiki/source_notes/matlab_code_reading_note.md`,
    `wiki/source_notes/flash_adc_ch8.md`,
    `wiki/source_notes/folding_interpolating_adc_ch9.md`,
    `wiki/source_notes/complex_phase_systems_note.md`,
    `wiki/source_notes/matlab_fundamentals_bridge.md`,
    `wiki/source_notes/adc_test_analysis_calibration_pdf.md`,
    `wiki/source_notes/data_conversion_handbook_note.md`,
    `wiki/source_notes/adc_metric_concept_docx.md`,
    `wiki/source_notes/adc_physical_system_structure_docx.md`,
    `wiki/source_notes/sun_sar_primary_pdf_distillation.md`,
    `wiki/source_notes/sun_pipeline_primary_pdf_distillation.md`,
    `wiki/source_notes/sun_testing_primary_pdf_distillation.md`,
    `wiki/source_notes/examples/exp_a01_fit_sine_4param.md`,
    `wiki/source_notes/examples/exp_d01_cal_weight_sine_lite.md`,
    `wiki/source_notes/examples/exp_d02_cal_weight_sine.md`,
    `wiki/source_notes/examples/exp_d03_redundancy_comparison.md`,
    `wiki/source_notes/examples/exp_d16_sar_unit_cap_mismatch_mc.md`,
    `wiki/source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md`
  - Still missing high-priority raw notes:
    remaining PDF/DOCX source details, next example candidates, and a
    MATLAB-to-Python translation comparison table.

- What exact rule promotes a page from `draft` to `stable`?
  - Answered structurally by: `schema/PROMOTION_RULES.md`
  - Related checks: `schema/SEMANTIC_LINT_CHECKLIST.md`,
    `tools/lint_wiki.py`
  - Remaining content-layer work: actually promote pages only after semantic
    review and evidence checks.

- What exact rule promotes a Sun-course source note from
  `primary-source-spot-checked` to `primary-source-reviewed`?
  - Current link: `audits/source_fidelity_sun_course_2026-06-03.md`
  - Current status: topic/keyword level PDF spot-check has been completed for
    14 core ADC source notes.
  - Still needed: slide-level formula, figure, assumption, and caveat review
    for calibration-critical chapters.

- How should future example notes be organized?
  - Answered structurally by: `schema/EXAMPLE_NOTE_TEMPLATE.md` and
    `wiki/workflows/example_ingest_map.md`
  - First ingested examples:
    `wiki/source_notes/examples/exp_a01_fit_sine_4param.md`,
    `wiki/source_notes/examples/exp_d01_cal_weight_sine_lite.md`,
    `wiki/source_notes/examples/exp_d02_cal_weight_sine.md`,
    `wiki/source_notes/examples/exp_d03_redundancy_comparison.md`,
    `wiki/source_notes/examples/exp_d16_sar_unit_cap_mismatch_mc.md`,
    `wiki/source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md`
  - Remaining content-layer work: ingest next candidates listed in
    `wiki/workflows/example_ingest_map.md`.

- How should future proof pages be organized?
  - Answered structurally by: `schema/PROOF_PAGE_TEMPLATE.md`
  - Remaining content-layer work: write individual proof pages.
