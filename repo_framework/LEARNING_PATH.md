# 新手学习路线

## 第 1 步：确认环境

```powershell
cd E:\ADCToolbox\python
uv run python -c "import adctoolbox; print(adctoolbox.__version__)"
```

## 第 2 步：运行完整流程 demo

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\whole_workflow_demo.py
```

看输出目录：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\
```

优先打开：

```text
01_spectrum_clean_vs_nonideal.png
02_analog_error_debug.png
03_sar_model_and_calibration.png
04_digital_debug_bits_and_weights.png
```

## 第 3 步：单独学习 SAR ADC 建模

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\sar_adc_model_study.py
```

然后修改 `ADCConfig`：

```python
num_bits = 12
cap_mismatch_sigma = 0.002
sampling_noise_rms = 30e-6
comparator_noise_rms = 30e-6
```

观察 ENOB、SNDR、SFDR 如何变化。

## 第 4 步：复制官方示例

```powershell
cd E:\ADCToolbox\python
uv run adctoolbox-get-examples C:\Users\90590\adctoolbox_examples
```

推荐顺序：

```text
01_basic/exp_b01_environment_check.py
02_spectrum/exp_s01_analyze_spectrum_simplest.py
03_generate_signals/exp_g01_generate_signal_demo.py
04_debug_analog/exp_a21_analyze_error_pdf.py
05_debug_digital/exp_d02_cal_weight_sine.py
05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
```

## 第 5 步：读源码

按这个顺序读：

1. `python/src/adctoolbox/__init__.py`
2. `python/src/adctoolbox/spectrum/analyze_spectrum.py`
3. `python/src/adctoolbox/models/sar.py`
4. `python/src/adctoolbox/calibration/calibrate_weight_sine.py`
5. `python/src/adctoolbox/aout/analyze_error_pdf.py`
6. `python/src/adctoolbox/dout/analyze_bit_activity.py`

## 第 6 步：开始做自己的实验

把自己的实验放在：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\
```

不要直接放到 `python/src/adctoolbox/`，除非你准备贡献正式源码。
