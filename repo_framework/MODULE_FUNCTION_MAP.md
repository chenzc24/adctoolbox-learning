# ADCToolbox 模块功能地图

本文档按模块说明主要代码的用途。它不是 API 参考手册，而是新手阅读源码前的导航图。

## `adctoolbox.__init__`

位置：

```text
python/src/adctoolbox/__init__.py
```

作用：

- 汇总最常用的公共 API
- 允许用户直接写 `from adctoolbox import analyze_spectrum`
- 暴露主要子模块：`fundamentals`、`spectrum`、`aout`、`dout`、`models` 等

学习建议：新手优先使用顶层导入，不要从测试里的旧路径学习。

## `fundamentals/`

基础数学和 ADC 指标工具。

| 文件 | 主要功能 |
|---|---|
| `frequency.py` | 相干频率、bin 与频率转换、Nyquist 折叠、频率估计 |
| `fit_sine_4param.py` | 四参数正弦拟合：频率、幅度、相位、DC |
| `units.py` | dB、幅度、功率、LSB、电压、dBm 等转换 |
| `snr_nsd.py` | SNR 与 NSD 转换、由幅度估计 SNR |
| `metrics.py` | Walden FoM、Schreier FoM、热噪声极限、jitter 极限 |
| `validate.py` | 输入数据完整性检查 |
| `convert_cap_to_weight.py` | 电容阵列到 ADC 权重转换 |

常用入口：

```python
from adctoolbox import find_coherent_frequency, fit_sine_4param
from adctoolbox import snr_to_nsd, nsd_to_snr, calculate_walden_fom
```

## `siggen/`

生成 ADC 学习和测试用的信号。

核心类：

```python
from adctoolbox.siggen import ADC_Signal_Generator
```

主要能力：

- 生成干净正弦波
- 添加 thermal noise
- 添加 quantization
- 添加 jitter
- 添加 HD2/HD3 静态非线性
- 添加 memory effect、incomplete sampling、reference error、AM noise 等

适合用途：

- 没有真实 ADC 数据时，先生成可控测试数据
- 学习不同非理想效应如何影响 SNDR/SFDR/ENOB

## `spectrum/`

FFT 频谱分析模块，是这个库最常用的核心之一。

| 文件 | 主要功能 |
|---|---|
| `analyze_spectrum.py` | 一站式频谱分析，输出 SNR/SNDR/SFDR/THD/ENOB/NSD |
| `compute_spectrum.py` | 底层频谱计算 |
| `plot_spectrum.py` | 频谱绘图和标注 |
| `analyze_spectrum_polar.py` | 极坐标频谱，用于观察相位相关误差 |
| `quick_sndr.py` | 快速 SNDR 估计 |
| `sweep_performance_vs_osr.py` | OSR 扫描性能 |
| `_window.py` | 窗口函数和功率修正 |
| `_harmonics.py` | 谐波定位和功率计算 |
| `_estimate_noise_power.py` | 噪声功率估计 |

常用入口：

```python
from adctoolbox import analyze_spectrum, analyze_spectrum_polar, quick_sndr
```

输出指标重点：

- `snr_dbc`
- `sndr_dbc`
- `sfdr_dbc`
- `thd_dbc`
- `enob`
- `nsd_dbfs_hz`

## `aout/`

Analog output debug，即对 ADC 输出波形做误差诊断。

| 功能 | 常用 API |
|---|---|
| 误差 PDF | `analyze_error_pdf` |
| 误差自相关 | `analyze_error_autocorr` |
| 误差频谱 | `analyze_error_spectrum` |
| 按输入值/码值看误差 | `analyze_error_by_value` |
| 按正弦相位看误差 | `analyze_error_by_phase` |
| INL/DNL from sine | `analyze_inl_from_sine` |
| 谐波误差分解 | `analyze_decomposition_time`, `analyze_decomposition_polar` |
| 静态非线性拟合 | `fit_static_nonlin` |
| 相平面分析 | `analyze_phase_plane`, `analyze_error_phase_plane` |

典型流程：

```text
ADC waveform
  -> fit_sine_4param
  -> signal - fitted_sine = error
  -> PDF / ACF / spectrum / phase-value analysis
```

## `models/`

ADC 行为模型。目前重点是 SAR ADC。

| API | 作用 |
|---|---|
| `sar_ideal_weights` | 生成理想二进制或冗余 SAR 权重 |
| `sar_apply_cap_mismatch` | 添加单位电容/Pelgrom 风格 mismatch |
| `sar_apply_mismatch` | 旧版逐权重随机 mismatch |
| `sar_convert` | 把输入电压转换成 SAR bit decisions |
| `sar_reconstruct` | 用权重把 bit matrix 重构成输出波形 |

典型流程：

```text
vin
  -> sar_ideal_weights
  -> sar_apply_cap_mismatch
  -> sar_convert
  -> sar_reconstruct
  -> analyze_spectrum
```

## `calibration/`

ADC 位权重校准。

| API | 作用 |
|---|---|
| `calibrate_weight_sine` | 使用正弦输入和 bit matrix 估计 bit weights |
| `calibrate_weight_sine_lite` | 更轻量的校准版本 |

典型输入：

```text
bits: shape = (N_samples, N_bits)
freq: Fin / Fs
```

典型输出：

- `weight`
- `offset`
- `calibrated_signal`
- `refined_frequency`
- `error`

## `dout/`

Digital output debug，即对 ADC 原始 bit matrix 做诊断。

| API | 作用 |
|---|---|
| `analyze_bit_activity` | 统计每个 bit 为 1 的比例，检查偏置/削顶 |
| `analyze_overflow` | 分析残差分布，检查 SAR 冗余/溢出风险 |
| `analyze_weight_radix` | 分析权重 radix 和有效位宽 |
| `analyze_enob_sweep` | 扫描使用不同 bit 数时的 ENOB |
| `plot_residual_scatter` | 画残差散点 |

## `timeinterleave/`

时间交织 ADC 工具。

| API | 作用 |
|---|---|
| `deinterleave` | 把总输出拆成多个子 ADC 通道 |
| `interleave` | 把多个通道重新交织成总输出 |
| `extract_mismatch_sine` | 从正弦捕获中估计 offset/gain/skew |
| `predict_spurs` | 预测 offset/gain/skew 导致的 spur |
| `fractional_delay_fft` | FFT 法分数延迟 |
| `fractional_delay_farrow` | Farrow 法分数延迟 |
| `calibrate_foreground` | 前景校准 |

## `oversampling/`

过采样和噪声整形相关工具。

| API | 作用 |
|---|---|
| `ntf_analyzer` | 分析 NTF 在指定频带内的性能 |

## `toolset/`

一键 dashboard 生成器，适合快速看全局状态。

| API | 作用 |
|---|---|
| `generate_aout_dashboard` | 对模拟输出波形生成多图分析面板 |
| `generate_dout_dashboard` | 对 bit matrix 生成数字输出分析面板 |

## `examples/`

官方示例。建议复制到个人目录运行，不直接改源码内示例。

命令：

```powershell
cd E:\ADCToolbox\python
uv run adctoolbox-get-examples C:\Users\90590\adctoolbox_examples
```

## `tests/`

测试代码。

| 目录 | 作用 |
|---|---|
| `tests/unit/` | 单个函数或模块的测试 |
| `tests/integration/` | 更完整的工作流测试 |
| `tests/compare/` | Python 输出与 MATLAB 参考输出对比 |

注意：当前部分测试仍引用旧 API 名称，学习时不要把失败测试直接理解为核心 demo 不能运行。

## `matlab/`

MATLAB 版本。

| 目录/文件 | 作用 |
|---|---|
| `matlab/src/` | MATLAB 工具函数 |
| `matlab/tests/` | MATLAB 测试 |
| `matlab/data_generation/` | 生成参考数据 |
| `matlab/toolbox/` | `.mltbx` 工具箱包 |
| `matlab/setupLib.m` | 加入 MATLAB path |

核心函数包括：

- `plotspec`
- `plotphase`
- `sinfit`
- `inlsin`
- `errsin`
- `wcalsin`
- `adcpanel`

## 推荐学习路径

1. 先运行 `demos/whole_workflow_demo.py`。
2. 打开输出图片，看 spectrum、error PDF、SAR calibration。
3. 阅读 `guides/whole_workflow_guide.md`。
4. 阅读本文件，知道每个模块在哪里。
5. 再去官方 examples 里按主题学习。
