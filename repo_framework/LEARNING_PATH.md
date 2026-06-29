# 新手学习路线

这份路线面向当前目标：学习 ADCToolbox Python 版 ADC 建模，尤其是 SAR ADC、频谱分析、bit matrix 诊断和 sine-based calibration。

## 第 0 步：确认环境

```powershell
cd E:\ADCToolbox\python
uv run python -c "import adctoolbox; print(adctoolbox.__version__)"
```

如果这一步失败，先不要进入建模学习。

## 第 1 步：先补 Python 数值仿真基础

阅读：

```text
staged_course/stage_00_python_numerics/stage_00_python_numerics.md
```

必须先理解：

```text
bits.shape == (n_samples, n_bits)
weights.shape == (n_bits,)
aout = bits @ weights
```

这是后面 SAR 重构和校准的共同底座。

## 第 2 步：读 staged_course 的主线

从总览开始：

```text
staged_course/overview.md
```

推荐顺序：

```text
Stage 00 Python 数值仿真基础
Stage 01 ADC 基础、采样、量化、LSB
Stage 02 FFT 和动态性能指标
Stage 03 正弦拟合和 residual 误差分析
Stage 04 SAR ADC 行为建模
Stage 05 bit matrix 数字诊断
Stage 06 sine-based 位权重校准
Stage 07 校准验证、模型边界与工程严谨性
Stage 08 Time-Interleaved ADC 失配与校准
Stage 09 Subsample debug output 与 alias
Stage 10 Oversampling、NTF 与 noise shaping
Stage 11 ADCToolbox Examples 全量专题
```

每个阶段都要回答检查问题，再进入下一阶段。

## 第 3 步：运行完整流程 demo

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

看输出目录：

```text
E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\
```

优先打开：

```text
01_spectrum_clean_vs_nonideal.png
02_analog_error_debug.png
03_sar_model_and_calibration.png
04_digital_debug_bits_and_weights.png
spectrum_metrics.csv
```

观察问题：

- clean signal 和 nonideal signal 的频谱差异是什么？
- SAR mismatch nominal reconstruction 为什么变差？
- calibration 后 SFDR、THD、ENOB 哪些改善？
- SNR 是否也明显改善？如果没有，为什么？

## 第 4 步：单独学习 SAR ADC 建模

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\sar_adc_model_study.py
```

然后修改 `ADCConfig`：

```python
num_bits = 12
cap_mismatch_sigma = 0.002
sampling_noise_rms = 30e-6
comparator_noise_rms = 30e-6
```

观察 ENOB、SNDR、SFDR 如何变化。

建议重点读：

```text
python/src/adctoolbox/models/sar.py
```

按顺序理解：

```text
sar_ideal_weights
sar_apply_cap_mismatch
sar_convert
sar_reconstruct
```

## 第 5 步：复制并运行官方示例

```powershell
cd E:\ADCToolbox\python
uv run adctoolbox-get-examples C:\Users\90590\adctoolbox_examples
```

推荐顺序：

```text
01_basic/exp_b01_environment_check.py
02_spectrum/exp_s01_analyze_spectrum_simplest.py
02_spectrum/exp_s08_windowing_deep_dive.py
03_generate_signals/exp_g01_generate_signal_demo.py
04_debug_analog/exp_a01_fit_sine_4param.py
04_debug_analog/exp_a21_analyze_error_pdf.py
05_debug_digital/exp_d02_cal_weight_sine.py
05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
08_time_interleave/exp_ti01_compare_skew_methods.py
09_downsample/exp_d00_subsample_aliasing.py
10_oversampling/exp_o01_noise_shaping_spectrum.py
02_spectrum/exp_s12_polar_coherent_averaging.py
```

不要只看图片。每跑一个示例，都要问：

- 输入是什么？
- 输出是什么？
- 哪个变量对应 ADC 物理对象？
- 指标为什么变好或变差？

## 第 6 步：按模块读源码

按这个顺序读：

1. `python/src/adctoolbox/fundamentals/frequency.py`
2. `python/src/adctoolbox/siggen/nonidealities.py`
3. `python/src/adctoolbox/spectrum/compute_spectrum.py`
4. `python/src/adctoolbox/spectrum/analyze_spectrum.py`
5. `python/src/adctoolbox/fundamentals/fit_sine_4param.py`
6. `python/src/adctoolbox/models/sar.py`
7. `python/src/adctoolbox/dout/analyze_bit_activity.py`
8. `python/src/adctoolbox/dout/analyze_weight_radix.py`
9. `python/src/adctoolbox/dout/analyze_overflow.py`
10. `python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py`
11. `python/src/adctoolbox/calibration/calibrate_weight_sine.py`
12. `python/src/adctoolbox/timeinterleave/extract_mismatch_sine.py`
13. `python/src/adctoolbox/timeinterleave/calibrate_foreground.py`
14. `python/src/adctoolbox/oversampling/ntf_analyzer.py`
15. `python/src/adctoolbox/spectrum/sweep_performance_vs_osr.py`
16. `python/src/adctoolbox/aout/compute_inl_from_sine.py`
17. `python/src/adctoolbox/spectrum/analyze_spectrum_polar.py`

先读函数 docstring 和输入输出，再读主体逻辑。

## 第 7 步：做自己的最小实验

把自己的实验放在：

```text
E:\ADCToolbox\learning\adctoolbox-learning\learner\
```

或新建：

```text
E:\ADCToolbox\learning\adctoolbox-learning\demos\my_experiments\
```

建议第一个自定义实验：

```text
固定一个 12-bit SAR
扫 cap_mismatch_sigma = 0, 0.001, 0.003, 0.01
分别记录 before/after calibration 的 SNDR/SFDR/THD/ENOB
把结果写成 CSV
```

## 第 8 步：学习工程严谨性

阅读：

```text
staged_course/stage_07_validation_rigor/stage_07_validation_rigor.md
```

记住：

```text
训练集 ENOB 变好，不等于校准工程上可靠。
```

更专业的流程必须包含：

- train/test 分离
- 多频点验证
- 多幅度验证
- 多 noise seed / mismatch seed
- before/after 多指标比较
- 模型假设和边界说明

这一步完成后，你才真正从“能跑 ADCToolbox”进入“能判断 ADC 建模与校准结论是否可信”。

## 第 9 步：学习高速和带宽相关进阶主题

读完 Stage 07 后，再进入三块互不重复的进阶主题：

```text
Stage 08:
  TI-ADC offset/gain/skew 失配、spur 网格、foreground/background 校准。

Stage 09:
  无滤波 subsample debug output、alias、spur 高度守恒、TI 通道覆盖。

Stage 10:
  OSR、NTF、noise shaping、带内噪声积分、performance vs OSR。

Stage 11:
  59 个 runnable examples 的运行与解释地图，并重点补 polar 频谱、相平面、
  谐波分解、INL/DNL、频谱平均等诊断工具。
```

推荐运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\08_time_interleave\exp_ti01_compare_skew_methods.py
uv run python src\adctoolbox\examples\09_downsample\exp_d00_subsample_aliasing.py
uv run python src\adctoolbox\examples\10_oversampling\exp_o01_noise_shaping_spectrum.py
uv run python src\adctoolbox\examples\10_oversampling\exp_o02_ntf_band_analysis.py
uv run python src\adctoolbox\examples\10_oversampling\exp_o03_snr_vs_osr.py
uv run python src\adctoolbox\examples\02_spectrum\exp_s12_polar_coherent_averaging.py
uv run python src\adctoolbox\examples\04_debug_analog\exp_a32_inl_from_sine_sweep_length.py
```
