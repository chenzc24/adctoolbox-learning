# Wiki Content Index

This file catalogs generated wiki pages. Update it whenever a new wiki page is
created or materially changed.

## Concepts

- [ADC weight calibration](concepts/adc_weight_calibration.md): Connect bit-weight reconstruction, sine input, least squares, and the main assumptions behind calibration.
- [FFT metrics](concepts/fft_metrics.md): Explain SNDR, SFDR, THD, ENOB, windows, side bins, and metric comparability.
- [Least-squares ADC calibration](concepts/least_squares_adc_calibration.md): Explain the calibration design matrix, weight solving, identifiability, and misuse risks.
- [Rank deficiency](concepts/rank_deficiency.md): Explain dependent bit columns, effective weights, and why rank controls calibration observability.

Planned:

- `concepts/redundant_sar.md`: Explain redundancy, reachability, and effective span.

## Source Code

- [SAR model source](source_code/sar_py.md): Explain ideal weights, mismatch injection, SAR conversion, and reconstruction in `models/sar.py`.
- [Lite sine-weight calibration source](source_code/calibrate_weight_sine_lite_py.md): Explain the minimal least-squares calibration model.
- [Full sine-weight calibration source](source_code/calibrate_weight_sine_py.md): Explain rank patching, conditioning, frequency estimation, solve path, and post-processing.
- [Spectrum source](source_code/compute_spectrum_py.md): Explain FFT preparation, windowing, side bins, harmonic bins, and ADC metrics.
- [Sine fitting source](source_code/fit_sine_4param_py.md): Explain least-squares sine fitting and frequency refinement.
- [Rank deficiency patch source](source_code/patch_rank_deficiency_py.md): Explain effective-column compression and physical-weight recovery.
- [Window helper source](source_code/window_py.md): Explain window generation, coherent gain, ENBW, side-bin defaults, and power correction.
- [Noise power helper source](source_code/estimate_noise_power_py.md): Explain SNR noise estimators and noise-floor policy choices.
- [Spectrum helper chain](source_code/spectrum_helper_chain_py.md): Map the internal helper path behind `compute_spectrum`.
- [Calibration helper chain](source_code/calibration_helper_chain_py.md): Map the internal helper path behind `calibrate_weight_sine`.
- [Spectrum wrapper source](source_code/analyze_spectrum_py.md): Explain the public compute-and-plot wrapper around `compute_spectrum`.
- [Quick SNDR source](source_code/quick_sndr_py.md): Explain the lightweight SNDR/ENOB path for fast gates and optimization loops.
- [Frequency utilities source](source_code/frequency_py.md): Explain coherent frequency search, Nyquist folding, bin folding, and sine-fit frequency estimation.

Planned:

- `source_code/metrics_py.md`
- `source_code/units_py.md`

## Workflows

- [SAR model to calibration](workflows/sar_model_to_calibration.md): End-to-end path from SAR model, bit decisions, calibration, reconstruction, and spectrum validation.
- [Example ingest map](workflows/example_ingest_map.md): Structural queue for turning ADCToolbox examples into reusable evidence notes.
- [Spectrum validation before and after calibration](workflows/spectrum_validation_before_after_calibration.md): Required FFT settings and diagnostics for calibration metric comparisons.
- [Training and validation split](workflows/training_validation_split.md): Required split, diagnostics, and metric settings for credible calibration claims.

## Rigor

- [Mathematical rigor gaps](rigor/mathematical_rigor_gaps.md): Current assumptions, risks, missing proofs, and validation obligations for ADCToolbox learning.
- [Identifiability conditions](rigor/identifiability_conditions.md): State rank, excitation, conditioning, and validation conditions for ADC weight calibration.
- [Spectrum metric statistical risks](rigor/spectrum_metric_statistical_risks.md): Explain why FFT metric claims depend on window, side-bin, harmonic, noise, and validation settings.
- [Redundant SAR reachability](rigor/redundant_sar_reachability.md): Formalize redundancy as interval reachability, static coverage, dynamic decision margin, and validation obligations.
- [SAR noise formula alignment](rigor/sar_noise_formula_alignment.md): Align ch12 kT/C, DAC noise, and comparator noise formulas with ADCToolbox SAR modeling limits.
- [Sine histogram DNL/INL](rigor/sine_histogram_dnl_inl.md): Align ch17 sine-input code-density DNL/INL extraction, assumptions, and failure modes.
- [Pipeline residue box and gain observability](rigor/pipeline_residue_box_gain_observability.md): Align ch10/ch11 residue-box, gain calibration, DAC calibration, and backend observability claims.

## Source Notes

- [ADC metrics chapter](source_notes/adc_metrics_ch3.md): Source note for static and dynamic ADC performance metrics.
- [ADC FOM chapter](source_notes/adc_fom_ch16.md): Source note for Walden FOM, Schreier FOM, and calibration-cost tradeoffs.
- [ADC key metric and concept DOCX](source_notes/adc_metric_concept_docx.md): Learner note bridge for sampling, DNL, INL, SNDR, ENOB, and metric caveats.
- [ADC physical system structure DOCX](source_notes/adc_physical_system_structure_docx.md): Learner note bridge from sampling, residue, code assembly, and physical weights to calibration.
- [ADC test analysis and calibration PDF](source_notes/adc_test_analysis_calibration_pdf.md): Source note for test bench discipline, FFT interpretation, linear-equation calibration, and dither calibration.
- [Data Conversion Handbook](source_notes/data_conversion_handbook_note.md): Broad reference anchor for sampled-data fundamentals, architectures, and converter testing.
- [Data converter testing](source_notes/data_converter_testing_ch17.md): Source note for test benches, static testing, dynamic testing, and calibration validation.
- [Sampling, DFT, and FFT](source_notes/fft_sampling_note.md): Source note for sampling, DFT bins, leakage, coherence, and windowing.
- [Matrix rank and observability](source_notes/matrix_rank_observability_note.md): Source note for rank, independent information, observability, and conditioning.
- [Least squares and calibration](source_notes/least_squares_calibration_note.md): Source note for overdetermined systems, residuals, rank, and ADC calibration.
- [Noise, RMS, power, and variance](source_notes/noise_rms_power_variance_note.md): Source note for noise power bookkeeping and dB conventions.
- [Quantization noise model](source_notes/quantization_noise_model_note.md): Source note for quantization error, white-noise assumptions, ideal SNR, and dither.
- [Low-power SAR ADC](source_notes/sar_low_power_ch12a.md): Source note for SAR decision flow, CDAC weights, noise, power, and calibration-relevant mismatch.
- [Switched-capacitor settling and noise](source_notes/switched_cap_settling_noise_ch6.md): Source note for charge redistribution, settling error, kT/C noise, and calibration limits.
- [Time-interleaved ADCs](source_notes/time_interleaving_ch13.md): Source note for interleaving, offset/gain/timing mismatch, and spur behavior.
- [Reading ADC MATLAB code](source_notes/matlab_code_reading_note.md): Source note for reading MATLAB ADC code by input/output, math type, and data flow.
- [Example: sine fit 4-parameter](source_notes/examples/exp_a01_fit_sine_4param.md): Evidence note for noisy sine fitting and residual checks.
- [Example: lite sine weight calibration](source_notes/examples/exp_d01_cal_weight_sine_lite.md): Evidence note for fast bit-weight calibration and before/after spectrum comparison.
- [Example: full sine weight calibration](source_notes/examples/exp_d02_cal_weight_sine.md): Evidence note for full bit-weight calibration, spectrum comparison, and weight error comparison.
- [Example: redundancy comparison](source_notes/examples/exp_d03_redundancy_comparison.md): Evidence note for strict binary versus redundant calibration under MSB mismatch.
- [Example: SAR unit-cap mismatch Monte Carlo](source_notes/examples/exp_d16_sar_unit_cap_mismatch_mc.md): Evidence note for mismatch sigma sweeps and ENOB distributions.
- [Example: SAR training-length sweep](source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md): Evidence note for training/test separation and overfitting in redundant SAR calibration.
- [Comparator chapter](source_notes/comparator_ch7.md): Source note for comparator offset, noise, speed, metastability, and calibration limits.
- [Flash ADCs](source_notes/flash_adc_ch8.md): Source note for parallel threshold comparison, thermometer codes, bubble errors, and Flash complexity.
- [Folding and interpolating ADCs](source_notes/folding_interpolating_adc_ch9.md): Source note for reducing Flash complexity through analog preprocessing.
- [Convolution and filtering](source_notes/convolution_filtering_note.md): Source note for convolution, filtering, and frequency-domain multiplication.
- [Dither](source_notes/dither_note.md): Source note for why added noise can decorrelate quantization error.
- [Complex phase and systems view](source_notes/complex_phase_systems_note.md): Source note for complex spectra, phase, transfer functions, STF, and NTF.
- [High-speed SAR ADC](source_notes/high_speed_sar_ch12b.md): Source note for high-speed SAR timing, comparator, DAC, and reference constraints.
- [Linear algebra vectors and matrices](source_notes/linear_algebra_vectors_matrices_note.md): Source note for vector/matrix language used in calibration.
- [Oversampling ADC](source_notes/oversampling_adc_ch14.md): Source note for oversampling, noise shaping, and sigma-delta context.
- [Pipeline ADC concept](source_notes/pipeline_adc_concept_ch10.md): Source note for pipeline ADC architecture and residue amplification.
- [Pipeline ADC implementation](source_notes/pipeline_adc_implementation_ch11.md): Source note for pipeline implementation errors and calibration hooks.
- [Sampling circuit](source_notes/sampling_circuit_ch5.md): Source note for sample-and-hold, aperture, kT/C, and sampling nonidealities.
- [MATLAB fundamentals bridge](source_notes/matlab_fundamentals_bridge.md): Source note for MATLAB arrays, indexing, operators, functions, structs, plotting, and debugging.
- [Sun SAR primary PDF distillation](source_notes/sun_sar_primary_pdf_distillation.md): Direct distillation from original SAR PDFs on CDAC, comparator, redundancy, timing, and calibration tolerance.
- [Sun Pipeline primary PDF distillation](source_notes/sun_pipeline_primary_pdf_distillation.md): Direct distillation from original Pipeline PDFs on residue, gain, sub-DAC error, and calibration.
- [Sun Testing primary PDF distillation](source_notes/sun_testing_primary_pdf_distillation.md): Direct distillation from original testing PDF on test setup, histogram DNL/INL, FFT metrics, and validation caveats.
