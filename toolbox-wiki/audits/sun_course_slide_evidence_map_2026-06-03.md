# Sun Course Slide Evidence Map 2026-06-03

```yaml
scope: toolbox-wiki
status: draft
last_updated: 2026-06-03
```

## Purpose

This audit maps calibration-critical Sun-course PDF slides to wiki pages. It
turns the previous source-fidelity work from chapter-level alignment into
page-level evidence tracking.

The map does not reproduce the slides. It records where each important formula,
figure, assumption, or caveat has been absorbed into the wiki, and where the
wiki still needs deeper formula/figure review.

## Status Labels

- `captured`: the slide's main claim is represented in a source note, rigor
  page, or workflow page.
- `partial`: the topic is represented, but formulas, figures, assumptions, or
  caveats need more detail.
- `missing`: the slide contains useful content that is not yet explicitly
  represented in the wiki.
- `defer`: the slide is lower priority for the current ADCToolbox calibration
  learning path.

## Source PDFs Reviewed

| PDF | Pages | Primary wiki anchor |
| --- | ---: | --- |
| `ch12 - low power.pdf` | 74 | `wiki/source_notes/sun_sar_primary_pdf_distillation.md` |
| `ch12 - high speed.pdf` | 40 | `wiki/source_notes/sun_sar_primary_pdf_distillation.md` |
| `ch17 Data Converter Testing.pdf` | 40 | `wiki/source_notes/sun_testing_primary_pdf_distillation.md` |
| `ch10.pdf` | 50 | `wiki/source_notes/sun_pipeline_primary_pdf_distillation.md` |
| `ch11.pdf` | 57 | `wiki/source_notes/sun_pipeline_primary_pdf_distillation.md` |

## Ch12 Low-Power SAR

| Page | Evidence Topic | Formula / Figure / Assumption | Wiki Mapping | Status | Follow-Up |
| ---: | --- | --- | --- | --- | --- |
| 3 | SAR binary search | DAC threshold trajectory and comparator-controlled search | `sun_sar_primary_pdf_distillation.md`, `sar_py.md` | captured | none |
| 4 | Direct implementation nonidealities | Comparator common-mode variation, parasitic capacitance, gain/INL risk | `sun_sar_primary_pdf_distillation.md` | partial | add circuit-error taxonomy page if needed |
| 5 | Classic charge redistribution | Reusing SAR DAC for sampling and subtraction | `sun_sar_primary_pdf_distillation.md`, `sar_low_power_ch12a.md` | captured | none |
| 13 | SAR limitations | Capacitor size, driver load, comparator noise, DAC settling, N-cycle delay | `sun_sar_primary_pdf_distillation.md` | captured | connect to validation checklist |
| 15 | SAR noise categories | Sampling noise, DAC noise, comparator noise | `sun_sar_primary_pdf_distillation.md`, `switched_cap_settling_noise_ch6.md` | captured | none |
| 16-19 | kT/C noise | kT/C derivation and capacitor-size implication | `sar_noise_formula_alignment.md` | captured | add simulation sweep if needed |
| 20 | DAC noise | DAC noise and settling bandwidth tradeoff | `sar_noise_formula_alignment.md` | captured | add DAC settling/noise model only if code appears |
| 22-29 | Comparator noise | Static/dynamic comparator noise, gain, offset, speed tradeoff | `sar_noise_formula_alignment.md` | captured | add bit-cycle noise budget script |
| 35 | Comparator in SAR | Only some comparison cycles are noise-critical | `sun_sar_primary_pdf_distillation.md`, `redundant_sar_reachability.md` | captured | connect to per-cycle error budget script |
| 36 | No redundancy | Every comparison must be accurate | `redundant_sar_reachability.md` | captured | none |
| 37 | Radix < 2 redundancy | Redundancy range tolerates comparator noise, DAC settling, offset mismatch | `redundant_sar_reachability.md`, `sar_reachability_example_weight_audit_2026-06-03.md` | captured | automate regeneration of example-weight audit |
| 38 | Redundant bit | Extra comparison/bit can provide local recovery range | `redundant_sar_reachability.md` | captured | compare duplicate-bit model to code |
| 40-42 | Comparator switching / offset mismatch | Comparator offset reduction and mismatch handling | `sun_sar_primary_pdf_distillation.md` | partial | add offset calibration note if examples require it |
| 45 | Background regulation | Background calibration based on target-cycle monitoring | `sun_sar_primary_pdf_distillation.md` | missing | future background calibration page |
| 47-51 | Statistical estimation | Noise enables residue estimation and comparator noise estimation | none | missing | important if studying noise-assisted estimation |
| 59 | Adaptive tracking | Averaging can tolerate incomplete settling with extra LSB DAC cells | `sun_sar_primary_pdf_distillation.md` | partial | add if modeling settling calibration |
| 60 | SAR low-noise recap | Circuit and architectural noise reduction summary | `sun_sar_primary_pdf_distillation.md` | captured | none |
| 66-70 | DAC switching/common-mode/mismatch | Monotonic switching, common-mode variation, split MSB mismatch | `sar_low_power_ch12a.md` | partial | lower priority unless studying DAC switching |
| 72-74 | Low-power recap | Sub-ranging, SAR logic power, noise categories | `sun_sar_primary_pdf_distillation.md` | captured | none |

## Ch12 High-Speed SAR

| Page | Evidence Topic | Formula / Figure / Assumption | Wiki Mapping | Status | Follow-Up |
| ---: | --- | --- | --- | --- | --- |
| 4 | SAR timing budget | `T_loop = t_comp + t_logic + max(t_DAC, t_reset)`, `T_SAR ≈ t_sample + N*T_loop` | `sun_sar_primary_pdf_distillation.md`, `redundant_sar_reachability.md` | captured | add exact formula to timing concept if created |
| 8 | Asynchronous SAR | Comparator ready generation | `sun_sar_primary_pdf_distillation.md` | partial | lower priority for calibration wiki |
| 9 | Logic delay | Comparator-to-DAC update path limits settling time | `sun_sar_primary_pdf_distillation.md` | partial | connect to high-speed SAR source note |
| 15 | DAC settling and redundancy | Redundancy relaxes required DAC settling accuracy | `redundant_sar_reachability.md` | captured | quantify margin with reachability script |
| 16 | DAC self-timing | Replica/self-timing prevents over-design across PVT | `sun_sar_primary_pdf_distillation.md` | partial | lower priority |
| 18 | Loop-unrolled SAR | Removes logic/reset delay but adds comparator offset mismatch and Vcm issue | `sun_sar_primary_pdf_distillation.md` | partial | add offset calibration caveat if needed |
| 19-21 | Comparator offset calibration | Foreground/background offset calibration loops | `sun_sar_primary_pdf_distillation.md` | partial | future offset-calibration source note |
| 25 | Two-stage sub-ranging SAR | Shared DAC avoids interstage gain calibration; preamp attenuates offset | `sun_sar_primary_pdf_distillation.md` | partial | compare to Pipeline gain calibration note |
| 28 | 2b/cycle SAR | Reduces cycles but adds DAC/comparator mismatch burden | `sun_sar_primary_pdf_distillation.md` | partial | defer unless multi-bit SAR examples appear |
| 31-37 | Multi-bit/cycle DAC schemes | REF/SIG DAC, gain mismatch, common-mode dimension | none | defer | not central to current ADCToolbox calibration path |

## Ch17 Data Converter Testing

| Page | Evidence Topic | Formula / Figure / Assumption | Wiki Mapping | Status | Follow-Up |
| ---: | --- | --- | --- | --- | --- |
| 4-5 | ADC test setup and target specs | Test instrumentation must exceed DUT requirements | `sun_testing_primary_pdf_distillation.md`, `training_validation_split.md` | captured | add measurement checklist if real bench work begins |
| 6-8 | Signal-source linearity and filtering | Source distortion and filter distortion can dominate SFDR | `sun_testing_primary_pdf_distillation.md` | captured | none |
| 12-15 | Clock jitter | Phase noise/jitter and jitter-induced noise behavior | `sun_testing_primary_pdf_distillation.md` | captured | add jitter-specific workflow if examples use it |
| 25 | Spectral and DNL/INL split | FFT for spectral metrics; histogram for ADC DNL/INL decision levels | `sun_testing_primary_pdf_distillation.md`, `training_validation_split.md` | captured | none |
| 26 | Histogram test | Code width proportional to code occurrence; slow ramp assumption | `sun_testing_primary_pdf_distillation.md` | captured | none |
| 27-32 | Ideal/nonideal histogram DNL/INL | DNL from normalized counts; INL from cumulative DNL | `sun_testing_primary_pdf_distillation.md` | captured | add formula page if static metrics become central |
| 33-36 | Sine-input histogram | Sinusoidal PDF correction and amplitude/offset question | `sine_histogram_dnl_inl.md` | captured | add Python code page if implemented |
| 37-38 | MATLAB DNL/INL code | Transition levels and linearized histogram implementation | `sine_histogram_dnl_inl.md` | captured | map to future Python implementation |
| 39 | Histogram limitations | Monotonicity assumption, sparkle-code blind spot, noise smearing | `training_validation_split.md`, `sun_testing_primary_pdf_distillation.md` | captured | none |
| 40 | DNL smeared by noise | Noise can hide local DNL defects | `sun_testing_primary_pdf_distillation.md` | captured | none |

## Ch10 Pipeline Concept

| Page | Evidence Topic | Formula / Figure / Assumption | Wiki Mapping | Status | Follow-Up |
| ---: | --- | --- | --- | --- | --- |
| 18-20 | Gain after subtraction | Fine quantizer precision relaxed by residue gain | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 21 | Pipeline characteristics | Latency-speed tradeoff and linear hardware scaling | `pipeline_adc_concept_ch10.md` | captured | none |
| 22-27 | Stage analysis/decomposition | Ideal DACs, matched analog/digital gains, aggregate gain | `sun_pipeline_primary_pdf_distillation.md` | captured | add formula-level derivation if Pipeline modeling starts |
| 28 | Nonidealities list | Sub-ADC errors, amplifier offset/gain error, sub-DAC error | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 30-31 | Stage gain upper bound | Backend overload from sub-ADC decision-level errors | `pipeline_residue_box_gain_observability.md` | captured | add model when Pipeline code exists |
| 36 | Sub-ADC redundancy | Residue stays inside box or downstream stage returns it inside | `sun_pipeline_primary_pdf_distillation.md` | captured | future Pipeline residue reachability page |
| 37 | Amplifier offset | Global offset and sub-ADC offset interpretation | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 38-41 | Digital gain calibration | Digital gain must match analog gain; backend measures gain | `pipeline_residue_box_gain_observability.md` | captured | add model when Pipeline code exists |
| 42 | DAC calibration | Sweep DAC codes and measure transition errors with backend | `pipeline_residue_box_gain_observability.md` | captured | none |
| 43 | Recursive stage calibration | Calibrate less significant stage first, move toward stage 1 | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 45 | Foreground/background schemes | Drift motivates background calibration | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 46-48 | Bit combining with redundancy | Digital combining examples with/without stage redundancy | `pipeline_adc_concept_ch10.md` | partial | add if Pipeline digital correction is implemented |

## Ch11 Pipeline Implementation

| Page | Evidence Topic | Formula / Figure / Assumption | Wiki Mapping | Status | Follow-Up |
| ---: | --- | --- | --- | --- | --- |
| 2 | Stage implementation | Flash sub-ADC + multiplying DAC + switched-capacitor circuit | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 8 | Design parameters | Stage resolution, scaling, redundancy, OTA, SHA-less, calibration, time interleaving | `pipeline_adc_implementation_ch11.md` | captured | none |
| 9 | Thermal noise | Thermal noise versus quantization noise budget | `pipeline_adc_implementation_ch11.md` | partial | formula-level noise budget review |
| 13-14 | Capacitor scaling | Scaling factor tied to stage gain, then refined by circuit info | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 17-18 | Bits per stage tradeoff | OTA gain/speed and stage count tradeoff | `pipeline_adc_implementation_ch11.md` | partial | lower priority |
| 22 | Residue plot | Residue transition accuracy requirement | `pipeline_residue_box_gain_observability.md` | captured | add model when Pipeline code exists |
| 24 | Capacitor matching | Matching requirement, digital calibration or multi-bit first stage | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 26 | Comparator tolerance | Redundancy can tolerate large offset/noise | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 28-30 | OTA gain and settling | Static gain error, dynamic settling, loop-gain requirement | `pipeline_ota_settling_noise_budget.md` | captured | add Pipeline model only if code appears |
| 34-38 | Settling behavior | Linear settling regions and simulation behavior | `pipeline_ota_settling_noise_budget.md` | captured | defer simulation until Pipeline model exists |
| 41-43 | Noise analysis/budgeting | Switch/OTA noise and budget partitioning | `pipeline_ota_settling_noise_budget.md` | captured | defer implementation until Pipeline model exists |
| 44-45 | SHA-less architecture | MDAC/sub-ADC acquisition timing mismatch; redundancy absorbs skew | `sun_pipeline_primary_pdf_distillation.md` | captured | none |
| 46 | Amplifier sharing | Memory effects caveat | `pipeline_adc_implementation_ch11.md` | partial | lower priority |
| 52 | Comparator-based switched-capacitor | Efficient charge transfer and cyclic reuse | none | defer | outside current calibration path |

## Highest-Value Missing Or Partial Items

1. Automate regeneration of
   `audits/sar_reachability_example_weight_audit_2026-06-03.md` from example
   weight lists.
2. DAC settling/noise behavioral model only if ADCToolbox adds code for it.
3. Python implementation mapping for sine-histogram DNL/INL if such code is
   added.
4. Pipeline behavioral model and example before deeper Pipeline calibration
   proofs.

## Maintenance Rule

When a wiki page makes a calibration-critical claim based on these PDFs, add a
short "Evidence Map" line pointing back to this audit or to a future
chapter-specific slide review. Do not mark `primary-source-reviewed` unless the
relevant slide row is `captured` and any formula/figure caveat is either
resolved or explicitly deferred.
