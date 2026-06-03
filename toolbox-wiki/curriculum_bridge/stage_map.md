# Stage Map

This bridge preserves the staged learning path while allowing the wiki to grow
as a cross-linked knowledge base.

## Existing Staged Materials In Raw Resources

Imported Markdown materials are currently under:

```text
toolbox-wiki/raw/resources/ADCtoolbox/学习整理_MD/
```

Detected stage-style directories:

- `01_ADC学习_孙老师课件主线/`
- `02_数学学习_ADC校准所需/`
- `03_MATLAB学习/`

These are treated as existing learning assets, not as wiki pages to rewrite.

## Stage To Wiki Mapping

### Stage 1: ADC Concepts

Supports future wiki topics:

- SAR ADC.
- Pipeline ADC.
- ADC performance metrics.
- Testing and FOM.

### Stage 2: Mathematics For Calibration

Supports future wiki topics:

- Least squares.
- Matrix rank and identifiability.
- FFT and sampling.
- RMS, power, noise, and quantization error.

### Stage 3: MATLAB Reading

Supports future wiki topics:

- MATLAB-to-Python parity.
- Reading MATLAB reference implementation.
- Understanding matrix and FFT code patterns.

### Wiki Bridge: ADCToolbox Source Learning

The wiki will connect existing staged knowledge to:

- `sar.py`
- `compute_spectrum.py`
- `fit_sine_4param.py`
- `calibrate_weight_sine_lite.py`
- `calibrate_weight_sine.py`

## Rule

Stage files remain the learning path. Wiki pages are cross-links, synthesis,
source-code maps, rigor notes, and preserved answers.
