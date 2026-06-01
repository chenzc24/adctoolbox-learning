# ADC Modeling Playground

This folder is ignored by git and is safe for local learning experiments.

Run the SAR ADC study:

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\sar_adc_model_study.py
```

The model flow is:

```text
coherent sine input
  -> ideal SAR weights
  -> optional capacitor mismatch
  -> sampling and comparator noise
  -> SAR bit decisions
  -> digital reconstruction
  -> spectrum metrics: SNDR, SNR, SFDR, ENOB
```

Start by editing `ADCConfig` in `sar_adc_model_study.py`:

```python
num_bits = 12
cap_mismatch_sigma = 0.002
sampling_noise_rms = 30e-6
comparator_noise_rms = 30e-6
```

Useful experiments:

1. Set both noise values and mismatch to zero, then confirm ENOB is close to
   the ideal quantization limit.
2. Increase `cap_mismatch_sigma` and compare nominal reconstruction against
   sine-calibrated reconstruction.
3. Increase `comparator_noise_rms` and observe how SNR/ENOB degrade.
4. Change `num_bits` to 8, 10, 12, 14, or 16 and compare the ideal limit.

Generated files are written to `agent_playground/adctoolbox_learning/outputs/sar_adc_model/`.
