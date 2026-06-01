# ADCToolbox Whole Workflow Guide

This guide is for a novice who wants to understand what this repository can do
and how the pieces connect.

The runnable demo is:

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

Outputs are written to:

```text
E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\
```

This folder is ignored by git, so it is safe for experiments.

## What This Repository Can Do

ADCToolbox is a Python and MATLAB toolbox for ADC characterization. The Python
package is under `python/src/adctoolbox/`, and the MATLAB toolbox is under
`matlab/`.

Main capability map:

| Area | What it is for | Typical APIs or folders |
|---|---|---|
| Fundamentals | Frequency bins, coherent sampling, dB/unit conversions, ENOB/SNR/NSD, ADC FoM | `find_coherent_frequency`, `snr_to_nsd`, `calculate_walden_fom` |
| Signal generation | Make synthetic ADC input/output signals with noise, jitter, distortion, clipping, memory, AM, reference errors | `adctoolbox.siggen.ADC_Signal_Generator` |
| Spectrum analysis | FFT-based SNR, SNDR, SFDR, THD, ENOB, NSD, noise floor, harmonics, polar spectrum | `analyze_spectrum`, `analyze_spectrum_polar`, `quick_sndr` |
| Analog-output debug | Fit sine, analyze residual/error PDF, autocorrelation, error versus phase/value, INL/DNL, harmonic decomposition | `fit_sine_4param`, `analyze_error_pdf`, `analyze_error_autocorr`, `analyze_inl_from_sine` |
| SAR modeling | Behavioral SAR conversion from input waveform to raw bit decisions, with capacitor mismatch and noise | `sar_ideal_weights`, `sar_apply_cap_mismatch`, `sar_convert`, `sar_reconstruct` |
| Digital-output debug | Inspect raw bit matrices, bit activity, overflow, ENOB sweep, radix/weight structure | `analyze_bit_activity`, `analyze_weight_radix`, `analyze_enob_sweep` |
| Calibration | Estimate ADC bit weights from a sine input and raw bit decisions | `calibrate_weight_sine`, `calibrate_weight_sine_lite` |
| Time-interleaved ADCs | Split/rejoin channels, estimate/predict offset/gain/skew spurs, fractional delay correction | `deinterleave`, `interleave`, `predict_spurs`, `extract_mismatch_sine` |
| Oversampling | Noise-transfer-function performance checks | `ntf_analyzer` |
| Dashboards | One-command plot panels for analog output and digital output workflows | `toolset.generate_aout_dashboard`, `toolset.generate_dout_dashboard` |
| Examples | 59 runnable examples grouped by topic | `adctoolbox-get-examples` |
| MATLAB parity | MATLAB implementation and reference outputs for comparison | `matlab/`, `reference_output/`, `python/tests/compare/` |
| Codex skills | Bundled user/contributor guide skills for Codex | `python/src/adctoolbox/_bundled_skills/skills/` |

## Mental Model

Most ADC analysis has this shape:

```text
generate or load signal/data
  -> analyze analog waveform OR raw digital bits
  -> optionally calibrate
  -> reconstruct corrected output
  -> measure spectrum and debug residuals
  -> save figures/tables
```

For an analog output waveform:

```text
sampled waveform
  -> fit sine
  -> spectrum metrics
  -> residual/error PDF, autocorrelation, phase/value debug
```

For a SAR or bit-weighted ADC:

```text
input waveform
  -> SAR model produces bit matrix
  -> reconstruct with nominal weights
  -> calibrate bit weights from sine capture
  -> reconstruct with calibrated weights
  -> compare before/after SNDR and ENOB
```

## What The Demo Runs

`whole_workflow_demo.py` runs five small workflows.

### 1. Create A Coherent Input

The demo starts by choosing a coherent sine frequency:

```python
fin, fin_bin = find_coherent_frequency(FS, FIN_TARGET, N)
```

Coherent means the record contains an integer number of input cycles. This
makes the FFT easier to interpret because the tone lands exactly on one bin.

### 2. Generate A Nonideal ADC Output

The signal generator creates a clean sine, then adds:

- static HD2/HD3 distortion
- white thermal noise
- quantization to 12 bits

This gives a synthetic ADC output waveform. You can treat it like a measured
ADC capture from lab equipment.

### 3. Run Spectrum Analysis

The demo compares:

- clean sine
- generated nonideal ADC output

It saves:

```text
01_spectrum_clean_vs_nonideal.png
```

Important metrics:

- `SNDR`: signal-to-noise-and-distortion ratio
- `SNR`: signal-to-noise ratio, excluding harmonic distortion
- `SFDR`: largest spur relative to signal
- `THD`: harmonic distortion
- `ENOB`: effective number of bits
- `NSD`: noise spectral density

### 4. Debug The Analog Error

The demo fits an ideal sine to the generated ADC output, subtracts it, and
analyzes the error.

It saves:

```text
02_analog_error_debug.png
```

The left plot is error PDF. It answers: is the residual shaped like random
Gaussian noise, or does it have structure?

The right plot is error autocorrelation. It answers: is the residual white, or
does it remember previous samples?

### 5. Model A SAR ADC And Calibrate It

The demo creates a behavioral SAR ADC:

```text
input sine
  -> ideal binary SAR weights
  -> capacitor mismatch
  -> sampling/comparator noise
  -> raw SAR bit decisions
  -> reconstruct with nominal weights
  -> estimate calibrated weights from the bit matrix
  -> reconstruct calibrated output
```

It saves:

```text
03_sar_model_and_calibration.png
04_digital_debug_bits_and_weights.png
sar_model_data.npz
```

This is the most important workflow if you want to study ADC modeling. The raw
bit matrix is the simulated ADC digital output. Calibration estimates better
weights for those bits.

### 6. Use Utility Workflows

The demo also shows:

- `deinterleave` and `interleave` for time-interleaved ADC data
- `predict_spurs` for offset/gain/skew mismatch spurs
- SNR/NSD/ENOB conversions
- jitter-limited SNR
- Walden FoM

These results are saved in:

```text
workflow_summary.json
spectrum_metrics.csv
```

## How To Read The Output Files

Main files:

| File | Meaning |
|---|---|
| `01_spectrum_clean_vs_nonideal.png` | Basic FFT comparison |
| `02_analog_error_debug.png` | Residual PDF and autocorrelation |
| `03_sar_model_and_calibration.png` | SAR ideal vs mismatch vs calibrated spectrum |
| `04_digital_debug_bits_and_weights.png` | Bit activity and calibrated radix |
| `spectrum_metrics.csv` | Numeric spectrum metrics |
| `workflow_summary.json` | All important numeric results |
| `sar_model_data.npz` | Numpy arrays: input, bits, weights, reconstructed outputs |

To inspect the saved SAR arrays:

```python
import numpy as np

data = np.load(r"E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\sar_model_data.npz")
print(data.files)
print(data["nonideal_bits"].shape)
print(data["calibrated_weights"])
```

## What To Edit First

Open:

```text
E:\ADCToolbox\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

Start with these constants:

```python
FS = 100e6
N = 2**13
FIN_TARGET = 6.1e6
ADC_BITS = 12
INPUT_AMPLITUDE = 0.49
```

Then edit the nonidealities:

```python
noise_rms=70e-6
sigma=0.004
sampling_noise_rms=40e-6
comparator_noise_rms=40e-6
```

Suggested experiments:

1. Set all noise and mismatch to zero. Confirm the ideal ENOB is near the ADC
   bit count.
2. Increase capacitor mismatch. Watch the SAR nominal-weight spectrum degrade.
3. Increase comparator noise. Watch SNR and ENOB degrade.
4. Increase HD3 distortion. Watch THD/SFDR degrade.
5. Change `ADC_BITS` from 8 to 16 and compare ideal ENOB.

## Where To Go Next

Copy the official examples to a separate study folder:

```powershell
cd E:\ADCToolbox\python
uv run adctoolbox-get-examples C:\Users\90590\adctoolbox_examples
```

Good examples to study first:

```text
01_basic/exp_b01_environment_check.py
02_spectrum/exp_s01_analyze_spectrum_simplest.py
03_generate_signals/exp_g01_generate_signal_demo.py
04_debug_analog/exp_a21_analyze_error_pdf.py
05_debug_digital/exp_d02_cal_weight_sine.py
05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
06_use_toolsets/exp_t01_aout_dashboard_single.py
08_time_interleave/exp_ti01_compare_skew_methods.py
```

For MATLAB:

```matlab
addpath(genpath('E:\ADCToolbox\matlab\src'))
```

Then start with MATLAB functions like `plotspec`, `sinfit`, `inlsin`, and
`adcpanel`.

## Practical Advice

Use top-level imports when learning:

```python
from adctoolbox import analyze_spectrum, calibrate_weight_sine
from adctoolbox.models import sar_convert
```

Avoid old test imports such as `adctoolbox.common`; this checkout has some
stale tests that still use old names.

For local study, keep your scripts in:

```text
E:\ADCToolbox\learning\adctoolbox-learning\
```

That keeps experiments out of tracked source.
