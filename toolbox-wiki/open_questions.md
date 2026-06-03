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
  - Needed page: `wiki/rigor/least_squares_uncertainty.md`

- How much frequency error can be tolerated before solved weights are biased?
  - Current link: `wiki/source_code/calibrate_weight_sine_py.md`
  - Needed page: `wiki/rigor/frequency_weight_coupling.md`

## Redundant SAR

- When does redundant bit design guarantee reachability rather than only a
  larger nominal code span?
  - Current link: `wiki/source_code/sar_py.md`
  - Needed page: `wiki/rigor/redundant_sar_reachability.md`

- How should missing-code, DNL, INL, and calibration success be separated in
  redundant SAR examples?
  - Current link: `wiki/workflows/sar_model_to_calibration.md`
  - Needed page: `wiki/workflows/redundant_sar_validation.md`

## Spectrum Validation

- Which FFT settings are required before comparing pre/post calibration ENOB?
  - Partial answer: `wiki/concepts/fft_metrics.md`
  - Source page: `wiki/source_code/compute_spectrum_py.md`
  - Still needed: workflow page for before/after spectrum validation.

- How should coherent sampling, window choice, side-bin removal, and noise
  estimation be recorded in every metric claim?
  - Needed page: `wiki/rigor/spectrum_metric_statistical_risks.md`

## Knowledge Base Maintenance

- Which raw Markdown resources have been ingested into reusable source notes?
  - Current link: `coverage_matrix.md`
  - Current source notes:
    `wiki/source_notes/adc_metrics_ch3.md`,
    `wiki/source_notes/fft_sampling_note.md`,
    `wiki/source_notes/least_squares_calibration_note.md`,
    `wiki/source_notes/sar_low_power_ch12a.md`

- What exact rule promotes a page from `draft` to `stable`?
  - Answered structurally by: `schema/PROMOTION_RULES.md`
  - Related checks: `schema/SEMANTIC_LINT_CHECKLIST.md`,
    `tools/lint_wiki.py`
  - Remaining content-layer work: actually promote pages only after semantic
    review and evidence checks.

- How should future example notes be organized?
  - Answered structurally by: `schema/EXAMPLE_NOTE_TEMPLATE.md` and
    `wiki/workflows/example_ingest_map.md`
  - Remaining content-layer work: ingest individual examples.

- How should future proof pages be organized?
  - Answered structurally by: `schema/PROOF_PAGE_TEMPLATE.md`
  - Remaining content-layer work: write individual proof pages.
