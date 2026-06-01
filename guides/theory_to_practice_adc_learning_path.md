# ADC 理论到实践学习路线

面向对象：ADC 初学者，但具备较强代码能力。

目标：不是只会跑脚本，而是理解从 ADC 建模、数据分析到校准的完整路径，并知道本代码库中每一段理论对应哪些代码。

运行环境默认从 Python 子项目执行：

```powershell
cd E:\ADCToolbox\python
```

本学习目录位于：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\
```

## 0. 先建立全局地图

ADCToolbox 的主线不是“画几个 FFT 图”，而是下面这条 ADC 验证路径：

```text
信号/激励生成
  -> ADC 行为建模或导入实测数据
  -> 频域动态性能分析
  -> 时域/统计误差分析
  -> 数字 bit/code 诊断
  -> 位权重校准
  -> 校准前后对比
  -> dashboard / 报告 / MATLAB 参考对比
```

本库最成熟的方向是：

- 单音 ADC 动态性能分析：SNR、SNDR、SFDR、THD、ENOB、NSD
- SAR ADC 行为建模：权重、bit decisions、mismatch、采样/比较器噪声
- sine-based foreground calibration：从 bit matrix 估计 bit weights
- analog output 误差分析：PDF、autocorrelation、error spectrum、phase/value debug
- digital output 诊断：bit activity、overflow、radix、ENOB sweep

它不是晶体管级仿真器，不模拟完整 comparator metastability、DAC settling、switch charge injection、PVT corner。代码里的 SAR model 是行为级模型，适合算法学习、校准验证和数据分析流程训练。

## 1. 采样、量化和相干采样

### 理论要点

先理解三个概念：

1. 采样：连续时间输入 `x(t)` 变成离散序列 `x[n]`。
2. 量化：连续幅度变成有限 code，理想 N-bit ADC 的 LSB 约为 `full_scale / 2^N`。
3. 相干采样：采样窗口里刚好包含整数个输入周期，FFT 能量集中在一个 bin 上。

相干采样的条件：

```text
Fin / Fs = k / N
```

其中：

- `Fin` 是输入频率
- `Fs` 是采样频率
- `N` 是采样点数
- `k` 是 FFT bin index

如果不相干，能量会泄漏到很多 bin，需要窗口函数；如果相干，可以用 rectangular window 得到更干净的频谱解释。

### 本库对应代码

```text
python/src/adctoolbox/fundamentals/frequency.py
python/src/adctoolbox/fundamentals/units.py
python/src/adctoolbox/examples/01_basic/
python/src/adctoolbox/examples/02_spectrum/exp_s00_fft_fundamentals.py
python/src/adctoolbox/examples/01_basic/exp_b02_coherent_vs_non_coherent.py
```

核心 API：

```python
from adctoolbox import find_coherent_frequency, freq_to_bin, bin_to_freq
```

### 实验

复制官方示例：

```powershell
uv run adctoolbox-get-examples C:\Users\90590\adctoolbox_examples
```

运行：

```powershell
cd C:\Users\90590\adctoolbox_examples
python 01_basic\exp_b02_coherent_vs_non_coherent.py
python 02_spectrum\exp_s00_fft_fundamentals.py
```

观察：

- 相干采样时主频能量集中。
- 非相干采样时出现 leakage。
- FFT bin spacing 是 `Fs / N`。

## 2. FFT 动态性能指标

### 理论要点

ADC 动态性能通常用频域指标描述：

| 指标 | 含义 |
|---|---|
| SNR | 信号功率 / 噪声功率，不含谐波 |
| SNDR 或 SINAD | 信号功率 / 噪声+失真功率 |
| SFDR | 主信号到最大 spur 的距离 |
| THD | 谐波总功率 / 主信号功率 |
| ENOB | 由 SNDR 推导的等效位数 |
| NSD | 噪声谱密度，常用 dBFS/Hz |

关键公式：

```text
ENOB = (SNDR - 1.76) / 6.02
```

理想 N-bit ADC 的量化噪声极限约为：

```text
SNR_ideal = 6.02N + 1.76 dB
```

频谱分析的坑：

- DC 要排除。
- fundamental bin 要识别。
- harmonics 要折叠回 Nyquist 内。
- 信号 bin、谐波 bin、噪声 bin 不能混在一起。
- window 会改变等效噪声带宽，需要功率修正。

### 本库对应代码

```text
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/spectrum/compute_spectrum.py
python/src/adctoolbox/spectrum/_window.py
python/src/adctoolbox/spectrum/_harmonics.py
python/src/adctoolbox/spectrum/_estimate_noise_power.py
python/docs/source/algorithms/analyze_spectrum.md
```

核心 API：

```python
from adctoolbox import analyze_spectrum, analyze_spectrum_polar, quick_sndr
```

### 实验

运行：

```powershell
cd C:\Users\90590\adctoolbox_examples
python 02_spectrum\exp_s01_analyze_spectrum_simplest.py
python 02_spectrum\exp_s08_windowing_deep_dive.py
python 02_spectrum\exp_s04_sweep_dynamic_range.py
```

也可以运行本地整合 demo：

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\whole_workflow_demo.py
```

输出位置：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\
```

观察：

- `01_spectrum_clean_vs_nonideal.png`
- `spectrum_metrics.csv`
- clean sine 的 ENOB 可能非常高，因为它不是量化 ADC，只是数学干净信号。
- generated ADC output 的 ENOB 才更像真实 ADC 输出。

## 3. 信号非理想建模

### 理论要点

ADC 测试中你经常需要区分“ADC 自身问题”和“输入信号/采样过程问题”。

常见非理想：

| 非理想 | 频域表现 | 时域/统计表现 |
|---|---|---|
| thermal noise | 噪声底上升，SNR 下降 | PDF 接近 Gaussian |
| quantization | 理想白化时为均匀噪声近似 | error bounded in LSB |
| jitter | 高频输入时 SNR 明显下降 | 相位误差 |
| static nonlinearity | HD2/HD3 谐波增强 | error 与输入值相关 |
| dynamic/memory effect | spur、调制边带 | error 自相关不为 0 |
| clipping | 谐波、宽带失真 | PDF 重尾或边界堆积 |

### 本库对应代码

```text
python/src/adctoolbox/siggen/nonidealities.py
python/src/adctoolbox/examples/03_generate_signals/
python/src/adctoolbox/examples/04_debug_analog/nonideality_cases.py
```

核心 API：

```python
from adctoolbox.siggen import ADC_Signal_Generator
```

### 实验

```powershell
cd C:\Users\90590\adctoolbox_examples
python 03_generate_signals\exp_g01_generate_signal_demo.py
python 03_generate_signals\exp_g04_sweep_jitter_fin.py
python 03_generate_signals\exp_g05_sweep_static_nonlin.py
python 03_generate_signals\exp_g06_sweep_dynamic_nonlin.py
```

观察：

- jitter 对高 `Fin` 更敏感。
- static HD2/HD3 会直接体现在 harmonic bins。
- dynamic nonlinearity 往往不能只靠 THD 判断，还要看 error phase/value。

## 4. 正弦拟合与 residual 思维

### 理论要点

ADC 单音测试的核心不是只看原始波形，而是：

```text
measured_signal = ideal_sine + error
```

先用四参数拟合得到：

```text
ideal_sine = A*cos(wt) + B*sin(wt) + C
```

然后：

```text
error = measured_signal - ideal_sine
```

后续很多诊断都基于这个 error：

- PDF：看 error 分布
- ACF：看 error 是否有记忆
- error spectrum：看 error 的频率结构
- error by value：看是否与输入幅度相关
- error by phase：看 AM/PM 类误差

### 本库对应代码

```text
python/src/adctoolbox/fundamentals/fit_sine_4param.py
python/src/adctoolbox/aout/analyze_error_pdf.py
python/src/adctoolbox/aout/analyze_error_autocorr.py
python/src/adctoolbox/aout/analyze_error_spectrum.py
python/src/adctoolbox/aout/analyze_error_by_value.py
python/src/adctoolbox/aout/analyze_error_by_phase.py
python/docs/source/algorithms/fit_sine_4param.md
python/docs/source/algorithms/analyze_error_pdf.md
python/docs/source/algorithms/analyze_error_autocorr.md
```

核心 API：

```python
from adctoolbox import fit_sine_4param
from adctoolbox import analyze_error_pdf, analyze_error_autocorr, analyze_error_spectrum
```

### 实验

```powershell
cd C:\Users\90590\adctoolbox_examples
python 04_debug_analog\exp_a01_fit_sine_4param.py
python 04_debug_analog\exp_a21_analyze_error_pdf.py
python 04_debug_analog\exp_a23_analyze_error_autocorrelation.py
python 04_debug_analog\exp_a22_analyze_error_spectrum.py
```

本地整合 demo 的对应输出：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\02_analog_error_debug.png
```

观察：

- PDF 接近 Gaussian：热噪声占主导。
- ACF 除 lag=0 外接近 0：误差更像白噪声。
- ACF 有周期峰：可能有 clock/feedthrough/memory。
- error spectrum 有尖峰：确定性 spur 或 harmonic residue。

## 5. INL/DNL 与静态线性

### 理论要点

动态频谱指标告诉你“这个 ADC 对一个 sine 的动态表现如何”；INL/DNL 告诉你“ADC 转移曲线的 code width 和积分误差如何”。

概念：

```text
DNL(code) = 实际 code width 相对 1 LSB 的偏差
INL(code) = DNL 的累计积分误差
```

解释：

- DNL 接近 0：code width 接近理想 1 LSB
- DNL = -1：missing code
- INL 大：转移曲线弯曲，容易产生 harmonic distortion

本库用 sine histogram 方法估计 INL/DNL。它利用正弦输入的理论 PDF/CDF，把非均匀的正弦分布转换成 code width 信息。

### 本库对应代码

```text
python/src/adctoolbox/aout/analyze_inl_from_sine.py
python/src/adctoolbox/aout/compute_inl_from_sine.py
python/src/adctoolbox/aout/plot_dnl_inl.py
python/docs/source/algorithms/analyze_inl_from_sine.md
```

核心 API：

```python
from adctoolbox import analyze_inl_from_sine
```

### 实验

```powershell
cd C:\Users\90590\adctoolbox_examples
python 04_debug_analog\exp_a32_inl_from_sine_sweep_length.py
```

观察：

- 样本数越少，INL/DNL 越 noisy。
- 对高分辨率 ADC，sine histogram 需要远多于 `2^N` 的样本。
- clipping 会破坏边缘 code 的估计。

## 6. SAR ADC 行为建模

### 理论要点

SAR ADC 的基本过程：

```text
sample input
  -> MSB trial
  -> comparator decides keep/drop
  -> next bit trial
  -> repeat until LSB
  -> output bit vector
```

理想二进制 SAR 权重：

```text
[1/2, 1/4, 1/8, ..., 1/2^N]
```

本库的归一化 convention 是：

```text
raw weights = [2^(N-1), ..., 1]
normalized by sum(raw_weights) + 1 LSB
```

这样 4-bit 为：

```text
[8, 4, 2, 1] / 16
```

建模时要区分两类权重：

| 权重 | 含义 |
|---|---|
| actual analog weights | 真正参与 SAR decision 的 CDAC 权重 |
| digital reconstruction weights | 后端把 bits 转回数值时使用的权重 |

有 mismatch 时：

```text
encode with actual mismatched weights
reconstruct with nominal weights
```

这就是未校准 ADC。

### 本库对应代码

```text
python/src/adctoolbox/models/sar.py
python/src/adctoolbox/examples/02_spectrum/exp_s09_sar_fft_length_near_nyquist.py
python/src/adctoolbox/examples/05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
```

核心 API：

```python
from adctoolbox.models import sar_ideal_weights
from adctoolbox.models import sar_apply_cap_mismatch, sar_convert, sar_reconstruct
```

### 实验

本地 SAR 学习脚本：

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\sar_adc_model_study.py
```

官方示例：

```powershell
cd C:\Users\90590\adctoolbox_examples
python 02_spectrum\exp_s09_sar_fft_length_near_nyquist.py
python 05_debug_digital\exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
```

观察：

- `sar_adc_model_study.py` 会打印一个 sample 的 bit-trial trace。
- 增大 `cap_mismatch_sigma` 后，SFDR 往往先变差。
- 增大 comparator noise 后，SNR/ENOB 下降。
- mismatch 是 deterministic error，noise 是 stochastic error。

## 7. Digital Output：bit matrix 的诊断

### 理论要点

对 SAR 或 bit-weighted ADC，原始输出不是单一电压，而是：

```text
bits: shape = (N_samples, N_bits)
```

你可以从 bit matrix 看出很多问题：

- bit activity 是否接近 50%
- MSB/LSB 是否异常偏置
- 权重 radix 是否接近二进制或 sub-radix
- 是否有 overflow / redundancy margin 问题
- 使用不同 bit 子集时 ENOB 如何变化

### 本库对应代码

```text
python/src/adctoolbox/dout/analyze_bit_activity.py
python/src/adctoolbox/dout/analyze_weight_radix.py
python/src/adctoolbox/dout/analyze_overflow.py
python/src/adctoolbox/dout/analyze_enob_sweep.py
python/src/adctoolbox/examples/05_debug_digital/
```

核心 API：

```python
from adctoolbox.dout import analyze_bit_activity, analyze_weight_radix
```

### 实验

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d11_bit_activity.py
python 05_debug_digital\exp_d12_sweep_bit_enob.py
python 05_debug_digital\exp_d13_weight_scaling.py
python 05_debug_digital\exp_d14_overflow_check.py
```

本地整合 demo 对应输出：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\04_digital_debug_bits_and_weights.png
```

观察：

- bit activity 偏离 50% 可能意味着 DC offset、输入范围不对、clipping。
- radix 接近 2 是二进制 SAR；小于 2 往往表示冗余。
- ENOB sweep 可以帮助判断低位是否主要是噪声。

## 8. 位权重校准

### 理论要点

校准的目标是从 raw bits 中估计更好的 reconstruction weights。

未校准：

```text
y_nominal[n] = sum(bits[n, i] * nominal_weight[i])
```

校准后：

```text
y_calibrated[n] = sum(bits[n, i] * calibrated_weight[i]) + offset
```

为什么 sine 可以校准？

因为理想输入应该是一个正弦，校准过程寻找一组权重，使 bit matrix 的加权和尽可能像正弦，同时可以排除部分谐波项。

抽象成线性代数：

```text
B @ w ≈ sine_basis + offset + selected_harmonics
```

其中：

- `B` 是 bit matrix
- `w` 是未知 bit weights
- sine basis 用 `sin(2πfn)` 和 `cos(2πfn)` 表示

本库 full calibration 还处理：

- 频率自动估计和 refine
- harmonic rejection
- rank deficiency
- redundant bit 的权重恢复
- 数值 conditioning

### 本库对应代码

```text
python/src/adctoolbox/calibration/calibrate_weight_sine.py
python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
python/src/adctoolbox/calibration/_prepare_input.py
python/src/adctoolbox/calibration/_lstsq_solver.py
python/src/adctoolbox/calibration/_patch_rank_deficiency.py
python/docs/source/algorithms/calibrate_weight_sine.md
```

核心 API：

```python
from adctoolbox import calibrate_weight_sine
```

### 实验

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d01_cal_weight_sine_lite.py
python 05_debug_digital\exp_d02_cal_weight_sine.py
python 05_debug_digital\exp_d16_sar_unit_cap_mismatch_mc.py
python 05_debug_digital\exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

本地整合 demo 对应输出：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\03_sar_model_and_calibration.png
```

观察：

- 校准通常先改善 SFDR/THD，因为 mismatch 是确定性非线性。
- 如果噪声已经主导，校准对 ENOB 改善有限。
- 训练样本太少会 overfit 或估计不稳。
- 冗余 ADC 的 rank deficiency 需要 nominal weights 帮助分配权重。

## 9. Time-Interleaved ADC

### 理论要点

时间交织 ADC 用多个子 ADC 轮流采样，提高总采样率：

```text
channel 0, channel 1, ..., channel M-1, repeat
```

主要误差：

| mismatch | 结果 |
|---|---|
| offset mismatch | 在 `k*Fs/M` 产生 spur |
| gain mismatch | 在 `Fin + k*Fs/M` 附近产生 spur |
| timing skew | 与输入频率成正比的 spur |

### 本库对应代码

```text
python/src/adctoolbox/timeinterleave/
python/src/adctoolbox/examples/08_time_interleave/
```

核心 API：

```python
from adctoolbox import deinterleave, interleave, predict_spurs
from adctoolbox import extract_mismatch_sine
```

### 实验

```powershell
cd C:\Users\90590\adctoolbox_examples
python 08_time_interleave\exp_ti01_compare_skew_methods.py
python 08_time_interleave\exp_ti02_autocorr_background_skew_calibration.py
```

本地整合 demo 中也有一个轻量 `predict_spurs` 示例，输出在：

```text
workflow_summary.json
```

## 10. Dashboard 和报告化

### 理论要点

当你已经理解基础分析后，dashboard 用于快速检查一组数据，不适合作为第一学习入口。

Analog dashboard 适合：

```text
已经有 ADC waveform
想同时看 spectrum、error PDF、ACF、phase/value、polar 等
```

Digital dashboard 适合：

```text
已经有 bit matrix
想同时看 calibration、bit activity、overflow、ENOB sweep、radix
```

### 本库对应代码

```text
python/src/adctoolbox/toolset/generate_aout_dashboard.py
python/src/adctoolbox/toolset/generate_dout_dashboard.py
python/src/adctoolbox/examples/06_use_toolsets/
```

### 实验

```powershell
cd C:\Users\90590\adctoolbox_examples
python 06_use_toolsets\exp_t01_aout_dashboard_single.py
python 06_use_toolsets\exp_t03_dout_dashboard_single.py
```

## 11. MATLAB 与 Python 对照

### 理论要点

这个仓库有 MATLAB 历史实现和 Python 迁移实现。`reference_output/` 中保存了 MATLAB 参考结果，用于验证 Python 算法是否一致。

### 本库对应位置

```text
matlab/src/
matlab/tests/
python/tests/compare/
reference_dataset/
reference_output/
```

MATLAB 核心函数：

- `plotspec`
- `plotphase`
- `sinfit`
- `inlsin`
- `errsin`
- `wcalsin`
- `adcpanel`

Python 对应方向：

- `analyze_spectrum`
- `fit_sine_4param`
- `analyze_inl_from_sine`
- `analyze_error_*`
- `calibrate_weight_sine`

### 实验

MATLAB：

```matlab
addpath(genpath('E:\ADCToolbox\matlab\src'))
```

Python 比较测试可以在需要时再看，不建议作为第一学习入口，因为当前有部分旧 import 测试未更新。

## 推荐学习顺序

### Phase A：建立 ADC 测试基础

1. 相干采样和 FFT bin
2. SNR/SNDR/SFDR/THD/ENOB
3. window、leakage、harmonic folding

跑：

```powershell
python 01_basic\exp_b02_coherent_vs_non_coherent.py
python 02_spectrum\exp_s01_analyze_spectrum_simplest.py
python 02_spectrum\exp_s08_windowing_deep_dive.py
```

### Phase B：理解误差来源

1. thermal noise
2. quantization noise
3. jitter
4. static/dynamic nonlinearity
5. clipping/memory/interference

跑：

```powershell
python 03_generate_signals\exp_g01_generate_signal_demo.py
python 03_generate_signals\exp_g04_sweep_jitter_fin.py
python 03_generate_signals\exp_g05_sweep_static_nonlin.py
python 03_generate_signals\exp_g06_sweep_dynamic_nonlin.py
```

### Phase C：用 residual debug 问题

1. sine fitting
2. error PDF
3. error ACF
4. error spectrum
5. error by value/phase

跑：

```powershell
python 04_debug_analog\exp_a01_fit_sine_4param.py
python 04_debug_analog\exp_a21_analyze_error_pdf.py
python 04_debug_analog\exp_a23_analyze_error_autocorrelation.py
python 04_debug_analog\exp_a22_analyze_error_spectrum.py
```

### Phase D：进入 SAR 建模

1. ideal weights
2. SAR bit trial
3. cap mismatch
4. comparator/sampling noise
5. nominal vs actual reconstruction

跑：

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\sar_adc_model_study.py
```

### Phase E：进入校准

1. bit matrix
2. nominal reconstruction
3. sine-based weight solve
4. harmonic rejection
5. calibration before/after spectrum
6. rank deficiency/redundancy

跑：

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d02_cal_weight_sine.py
python 05_debug_digital\exp_d16_sar_unit_cap_mismatch_mc.py
python 05_debug_digital\exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

### Phase F：完整贯通

跑：

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\whole_workflow_demo.py
```

看：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\
```

你应该能把这些输出和理论对应起来：

| 输出 | 对应理论 |
|---|---|
| `01_spectrum_clean_vs_nonideal.png` | 频谱动态性能 |
| `02_analog_error_debug.png` | residual PDF/ACF |
| `03_sar_model_and_calibration.png` | SAR mismatch 与 calibration |
| `04_digital_debug_bits_and_weights.png` | bit activity 与 weight radix |
| `spectrum_metrics.csv` | 数值指标 |
| `workflow_summary.json` | 全流程摘要 |

## 不建议一开始钻的地方

暂时不要先从这些入口开始：

- 全量测试套件：部分旧 import 路径未更新。
- dashboard：适合已理解基础后做快速体检，不适合第一性学习。
- MATLAB compare 测试：适合验证算法一致性，不适合初学。
- oversampling/NTF：本库有工具，但不是当前最完整的主线。

## 你作为代码资深者可以重点看的抽象

这几个数据结构贯穿全库：

```text
signal: 1D ndarray, shape = (N,)
bits:   2D ndarray, shape = (N_samples, N_bits), MSB first
weights: 1D ndarray, shape = (N_bits,)
metrics: dict, contains snr_dbc/sndr_dbc/sfdr_dbc/enob/...
calibration result: dict, contains weight/calibrated_signal/error/refined_frequency
```

最关键的软件边界：

```text
siggen: 生成被测信号
models: 把输入变成 ADC 数字输出
spectrum/aout/dout: 分析结果
calibration: 从 bits 估计权重
toolset: 把多个分析打包成 dashboard
```

如果你想继续深入源码，推荐阅读顺序：

```text
python/src/adctoolbox/__init__.py
python/src/adctoolbox/fundamentals/frequency.py
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/models/sar.py
python/src/adctoolbox/calibration/calibrate_weight_sine.py
python/src/adctoolbox/calibration/_lstsq_solver.py
python/src/adctoolbox/aout/analyze_error_pdf.py
python/src/adctoolbox/dout/analyze_bit_activity.py
```

