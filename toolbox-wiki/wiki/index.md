# Wiki Content Index

This file catalogs generated wiki pages. Update it whenever a new wiki page is
created or materially changed.

## Concepts

- [ADC weight calibration](concepts/adc_weight_calibration.md): Connect bit-weight reconstruction, sine input, least squares, and the main assumptions behind calibration.
- [FFT metrics](concepts/fft_metrics.md): Explain SNDR, SFDR, THD, ENOB, windows, side bins, and metric comparability.

Planned:

- `concepts/least_squares_adc_calibration.md`: Explain the calibration design matrix and identifiability assumptions.
- `concepts/rank_deficiency.md`: Explain redundant bits and column dependency.

## Source Code

- [SAR model source](source_code/sar_py.md): Explain ideal weights, mismatch injection, SAR conversion, and reconstruction in `models/sar.py`.
- [Lite sine-weight calibration source](source_code/calibrate_weight_sine_lite_py.md): Explain the minimal least-squares calibration model.
- [Full sine-weight calibration source](source_code/calibrate_weight_sine_py.md): Explain rank patching, conditioning, frequency estimation, solve path, and post-processing.
- [Spectrum source](source_code/compute_spectrum_py.md): Explain FFT preparation, windowing, side bins, harmonic bins, and ADC metrics.
- [Sine fitting source](source_code/fit_sine_4param_py.md): Explain least-squares sine fitting and frequency refinement.
- [Rank deficiency patch source](source_code/patch_rank_deficiency_py.md): Explain effective-column compression and physical-weight recovery.

Planned:

- `source_code/_window_py.md`
- `source_code/_estimate_noise_power_py.md`

## Workflows

- [SAR model to calibration](workflows/sar_model_to_calibration.md): End-to-end path from SAR model, bit decisions, calibration, reconstruction, and spectrum validation.

Planned:

- `workflows/spectrum_validation_before_after_calibration.md`
- `workflows/training_validation_split.md`

## Rigor

- [Mathematical rigor gaps](rigor/mathematical_rigor_gaps.md): Current assumptions, risks, missing proofs, and validation obligations for ADCToolbox learning.
- [Identifiability conditions](rigor/identifiability_conditions.md): State rank, excitation, conditioning, and validation conditions for ADC weight calibration.

Planned:

- `rigor/spectrum_metric_statistical_risks.md`
- `rigor/redundant_sar_reachability.md`

## Source Notes

- [ADC metrics chapter](source_notes/adc_metrics_ch3.md): Source note for static and dynamic ADC performance metrics.
- [Sampling, DFT, and FFT](source_notes/fft_sampling_note.md): Source note for sampling, DFT bins, leakage, coherence, and windowing.
- [Least squares and calibration](source_notes/least_squares_calibration_note.md): Source note for overdetermined systems, residuals, rank, and ADC calibration.
- [Low-power SAR ADC](source_notes/sar_low_power_ch12a.md): Source note for SAR decision flow, CDAC weights, noise, power, and calibration-relevant mismatch.
