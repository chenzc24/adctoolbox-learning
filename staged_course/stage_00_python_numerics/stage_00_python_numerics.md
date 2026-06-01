# Stage 00: Python 数值仿真与系统架构基础

## 本阶段目标

这一阶段不是学习普通 Python 语法，而是补齐 ADCToolbox 建模所需的数值计算直觉。学完后，你应该能解释：

- `np.ndarray` 的 shape 为什么比变量名更重要。
- `bits.shape == (n_samples, n_bits)` 为什么是后续校准的基础。
- `@` 矩阵乘法在 ADC 重构中代表什么。
- 为什么仿真脚本要固定随机种子。
- 为什么工程建模里要反复区分单位、归一化范围和 full-scale。
- ADCToolbox 如何用“建模、分析、校准”支撑 ADC 设计闭环。

如果这一阶段不稳，后面读 `sar_convert`、`sar_reconstruct`、`calibrate_weight_sine` 时会很容易把物理含义和数组维度混在一起。

## 初学者先抓住的主线

先不要急着背 NumPy 语法。你只需要先建立一个习惯：

```text
每看到一个变量，先问三件事：
1. 它是一维还是二维？
2. 每一维代表什么物理含义？
3. 它的单位是什么，或者它是不是归一化量？
```

例如：

```python
bits.shape == (8192, 12)
```

这句话比变量名更重要。它表示：

```text
8192 个采样点
每个采样点有 12 个 SAR bit decision
```

再例如：

```python
weights.shape == (12,)
```

它表示：

```text
每一列 bit 对应一个重构权重
```

所以：

```python
aout = bits @ weights
```

才会得到：

```text
8192 个重构输出点
```

这就是后面所有 SAR 建模和位权重校准的最小骨架。

## 数学需要补什么

### 1. 向量和矩阵不是抽象符号

在本项目里，一个采样序列通常写成一维数组：

```python
aout.shape == (n_samples,)
```

对 ADC 来说，最常见的数据流是：

```text
理想正弦波参数
    -> 离散采样后的 vin
    -> sar_convert 得到 raw bit decisions / codes
    -> sar_reconstruct 得到 aout
```

这里的“离散采样”不是卷积，而是在采样时刻上对正弦函数逐点取值。

这个数据流可以直接在本库代码里看到。

`python/src/adctoolbox/siggen/nonidealities.py` 里的
`ADC_Signal_Generator` 会先建立采样时间：

```python
self.t = np.arange(N) / Fs
```

然后生成干净正弦：

```python
signal = A * np.sin(2 * np.pi * Fin * t) + DC
```

也就是说，连续时间里的理想正弦：

```text
vin(t) = DC + A * sin(2π Fin t)
```

进入 Python 后会变成逐点采样的数组：

```text
t[n] = n / Fs
vin[n] = DC + A * sin(2π Fin n / Fs)
```

在 coherent sampling 的例子里，本库也常写成：

```python
n = np.arange(N)
vin = INPUT_DC + INPUT_AMPLITUDE * np.sin(2.0 * np.pi * fin_bin * n / N)
```

这里 `fin_bin / N` 就是归一化频率 `Fin / Fs`。

要理解 coherent sampling，先从 DFT 的性质开始。

DFT 不是在分析无限长的连续信号，而是在分析一段有限长度的离散数据：

```text
x[0], x[1], ..., x[N-1]
```

DFT 默认这 N 个点会按 N 点周期重复：

```text
x[n + N] = x[n]
```

换成真实时间，采样率是 `Fs`，所以这段数据的时间窗口长度是：

```text
T = N / Fs
```

这个周期延拓信号的基频是：

```text
f0 = 1 / T = Fs / N
```

DFT 的第 `k` 个 bin 对应的物理频率就是：

```text
f_k = k * Fs / N
```

从“时域到频域”的角度看，DFT 系数就是信号和第 `k` 个复指数基底取内积：

```text
X[k] = sum_n x[n] * exp(-j 2π k n / N)
```

频谱幅度就是这个复系数的模，或经过缩放后的模。也就是说，频域里看到的
第 `k` 个 bin，本质上是在问：

```text
这段数据里有多少 k * Fs / N 这个频率成分？
```

如果输入正弦频率刚好满足：

```text
Fin / Fs = fin_bin / N
```

等价于：

```text
Fin = fin_bin * Fs / N
```

那么它正好等于 DFT 的某个基底频率，能量会集中在对应的
`fin_bin` 上。这里的 `fin_bin` 同时有两个含义：

```text
1. 输入正弦在 DFT 里的 bin index
2. N 个采样点窗口里正弦完成的周期数
```

这就是 coherent sampling：采样窗口里正好包含整数个输入周期。

如果 `Fin` 不是 `Fs / N` 的整数倍，N 点数据首尾不能无缝周期延拓。
DFT 只能用多个 bin 一起表示这个频率，频域上就表现为 spectral leakage。

实际使用时要分两种情况：

```text
Fin 已定：
    选择合适的 Fs 和 N，让 fin_bin = Fin * N / Fs 是整数

Fs 和 N 已定：
    调整 Fin 到最近的 coherent frequency，即 Fin = fin_bin * Fs / N
```

本库里的 `find_coherent_frequency(fs, fin_target, n_fft)` 属于第二种情况：
在目标 `Fin` 附近找一个合适的整数 `fin_bin`，再返回真正用于仿真的
`Fin_actual`。这样做的主要目的，是让单音频谱分析时能量落在 FFT bin 上，
减少 leakage，方便后续看 SNR、SNDR、SFDR 和 sine-based calibration。

注意区分连续傅里叶变换、傅里叶级数和 DFT：

| 方法 | 分析对象 | 频域形式 | 本阶段要记住什么 |
|---|---|---|---|
| 连续傅里叶变换 CTFT | 连续时间、无限长度或非周期信号 | 连续频率 | 不是本库 FFT 数据流的直接模型 |
| 傅里叶级数 | 连续时间、周期为 `T` 的信号 | `k / T` 离散频率 | 基频由周期 `T` 决定 |
| DFT / FFT | `N` 点离散数据，默认 N 点周期延拓 | `k * Fs / N` 离散 bin | coherent sampling 要让 `Fin` 对齐某个 bin |

对应到数组形式，`vin` 通常是一维数组：

```python
vin.shape == (n_samples,)
```

它表示一串按时间排列的输入采样点。例如：

```text
vin[0] -> 第 0 个采样时刻的输入电压
vin[1] -> 第 1 个采样时刻的输入电压
...
```

然后 `python/src/adctoolbox/models/sar.py` 里的 `sar_convert` 接收这个
`vin` 和 SAR 权重：

```python
bits = sar_convert(vin, weights, quant_range=(0.0, 1.0))
```

注意，`sar_convert` 的直接输出还不是 `aout`，而是 raw bit decisions。
源码 docstring 里写的返回形状是：

```text
codes.shape == vin.shape + (B,)
```

如果 `vin.shape == (n_samples,)`，那么：

```python
bits.shape == (n_samples, n_bits)
```

这张矩阵的每一行对应一个输入采样点，每一列对应 SAR 转换过程中的一个 bit：

```text
bits[n, 0] -> 第 n 个样本的 MSB decision
bits[n, 1] -> 第 n 个样本的第 2 个 bit decision
...
bits[n, -1] -> 第 n 个样本的 LSB decision
```

也就是说，第 0 维是时间样本，第 1 维是 bit 位置。约定是：

```text
bits[:, 0]      -> MSB
bits[:, -1]     -> LSB
bits[n, :]      -> 第 n 个样本的完整 bit decision vector
```

例如：

```python
bits = np.array([
    [0, 0, 1],
    [0, 1, 0],
    [1, 0, 1],
])
```

它表示 3 个输入采样点，每个采样点有 3 位 SAR decision：

```text
第 0 行 [0, 0, 1] -> 第 0 个样本的完整 bit decision
第 1 行 [0, 1, 0] -> 第 1 个样本的完整 bit decision
第 2 行 [1, 0, 1] -> 第 2 个样本的完整 bit decision
第 0 列 [0, 0, 1] -> 所有样本的 MSB decision
第 1 列 [0, 1, 0] -> 所有样本的第 2 个 bit decision
第 2 列 [1, 0, 1] -> 所有样本的 LSB decision
```

重构之后的 `aout` 又回到一维数组：

```python
aout = sar_reconstruct(bits, weights, quant_range=(0.0, 1.0))
```

```python
aout.shape == (n_samples,)
```

它表示每个输入采样点对应的重构模拟值。

所以本库中最小的 SAR 数据流可以记成：

```python
n = np.arange(N)
vin = DC + A * np.sin(2 * np.pi * Fin * n / Fs)

weights = sar_ideal_weights(n_bits)
bits = sar_convert(vin, weights)
aout = sar_reconstruct(bits, weights)
```

对应的 shape 是：

```text
vin.shape     == (N,)
weights.shape == (n_bits,)
bits.shape    == (N, n_bits)
aout.shape    == (N,)
```

如果要加入更真实的 ADC 行为，非理想因素通常加在四个位置：

```text
1. 输入波形阶段
   vin -> vin_nonideal

2. SAR 权重阶段
   nominal_weights -> actual_weights

3. SAR 转换阶段
   vin + sampling noise / comparator noise -> bits

4. 数字重构阶段
   bits @ digital_weights -> aout
```

对应到本库代码，输入波形阶段的非理想性主要在
`python/src/adctoolbox/siggen/nonidealities.py`，例如：

```text
apply_thermal_noise
apply_jitter
apply_static_nonlinearity
apply_memory_effect
apply_reference_error
apply_clipping
apply_drift
```

SAR 权重阶段的非理想性可以用实际 CDAC 权重表示：

```python
nominal_weights = sar_ideal_weights(n_bits)
actual_weights = sar_apply_cap_mismatch(nominal_weights, sigma=0.004, rng=rng)
```

转换阶段的随机噪声由 `sar_convert` 参数加入：

```python
bits = sar_convert(
    vin,
    actual_weights,
    sampling_noise_rms=40e-6,
    comparator_noise_rms=40e-6,
    rng=rng,
)
```

重构阶段要区分“实际模拟权重”和“数字重构权重”：

```python
aout_uncalibrated = sar_reconstruct(bits, nominal_weights)
aout_actual_weight = sar_reconstruct(bits, actual_weights)
aout_calibrated = sar_reconstruct(bits, calibrated_weights)
```

同一组 `bits`，使用不同的 `digital_weights`，会得到不同的 `aout`。
这就是后续位权重校准问题的核心。

### 2. ADC 数字重构就是矩阵乘法

给定 bit matrix 和权重：

```text
B shape = (N, M)
w shape = (M,)
```

重构输出是：

```text
y = B @ w
```

shape 变成：

```text
(N, M) @ (M,) -> (N,)
```

这不是单纯的编程技巧，而是 ADC 数字重构的核心模型：

```text
y[n] = b0[n]*w0 + b1[n]*w1 + ... + bM-1[n]*wM-1
```

后续校准就是估计这个 `w`。

### 3. Monte Carlo 仿真是在看随机系统的分布

Monte Carlo 不是“加一次随机噪声”的同义词。它的核心是：

```text
定义随机模型
    -> 抽一次随机 realization
    -> 跑完整仿真
    -> 换 seed / realization 重复很多次
    -> 统计输出指标的分布
```

所以它回答的不是：

```text
这个 seed 下 ENOB 是多少？
```

而是：

```text
在很多颗随机 mismatch 芯片或很多次随机噪声 realization 下，
ENOB / SNDR / calibration error 的 median、p10、p90、std 是多少？
```

在本库的 SAR 建模里，随机性常见在三层：

```text
1. 芯片级固定随机性
   nominal_weights -> actual_weights
   例如 capacitor mismatch。一次抽样代表一颗芯片。

2. 采样级随机性
   vin -> vin_sampled
   例如 sampling_noise_rms。每个采样点可以不同。

3. bit decision 级随机性
   comparator input -> bit decision
   例如 comparator_noise_rms。每个 sample、每个 bit trial 可以不同。
```

对应到源码：

```python
actual_weights = sar_apply_cap_mismatch(nominal_weights, sigma=0.004, rng=rng)

bits = sar_convert(
    vin,
    actual_weights,
    sampling_noise_rms=40e-6,
    comparator_noise_rms=40e-6,
    rng=rng,
)
```

其中 `sar_apply_cap_mismatch` 更像“抽一颗随机芯片”，而
`sampling_noise_rms` / `comparator_noise_rms` 更像“这次采集过程中的随机扰动”。

本库里的典型 Monte Carlo 例子是：

```text
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
```

它的结构可以简化成：

```python
N_MC = 32

for sigma in mismatch_sigma_list:
    for trial in range(N_MC):
        rng = np.random.default_rng(BASE_SEED + trial)

        actual_weights = sar_apply_cap_mismatch(nominal_weights, sigma=sigma, rng=rng)
        bits_train = sar_convert(vin_train, actual_weights)
        bits_test = sar_convert(vin_test, actual_weights)

        aout_before = sar_reconstruct(bits_test, nominal_weights)
        calibrated_weights = calibrate_weight_sine(bits_train, ...)
        aout_after = bits_test @ calibrated_weights

        # 记录 before / after calibration 的 ENOB
```

最后不是只看某一次结果，而是对很多次 `trial` 统计：

```text
min / p10 / median / p90 / max / mean / std
```

这才是 Monte Carlo 的价值：它让我们看到算法和架构在随机 mismatch 下是否稳健。

因此要区分：

```text
加一次随机噪声 = 一个随机 realization
重复很多次 realization 并统计分布 = Monte Carlo
```

固定 seed 的作用只是让某一次随机实验可复现。本库推荐使用：

```python
rng = np.random.default_rng(seed)
```

再把 `rng` 显式传给需要随机数的函数。seed 是工具，Monte Carlo 分布才是工程问题本身。

### 4. 归一化和单位必须分清

本项目常见两类频率：

```text
Fin, fs      -> Hz
freq         -> Fin / fs, normalized frequency
```

常见电压范围：

```text
quant_range = (0.0, 1.0)       # normalized single-ended
quant_range = (-Vref, +Vref)   # differential-style range
```

建模时先用归一化范围是合理的，因为它降低了无关复杂度；但学习时要始终知道“这个数是归一化量，还是物理单位”。

## 电路需要理解什么

数值数组只是物理系统的投影：

| 代码对象 | 电路/系统含义 |
|---|---|
| `vin` | ADC 输入电压 |
| `aout` | 重构后的模拟输出波形 |
| `bits` | SAR 每一位比较器决策 |
| `weights` | CDAC 或数字重构权重 |
| `noise_rms` | 输入等效 RMS 噪声 |
| `quant_range` | ADC 满量程范围 |
| `rng` | 某次芯片/噪声 realization |

学习时建议先读代码变量，再强迫自己说出它对应的物理对象。

## System Architecture: ADCToolbox 的系统闭环

Stage 00 不只是在学 NumPy。`vin`、`bits`、`weights`、`aout`
这些数组，是后面所有工程闭环的共同语言。

可以先把 ADCToolbox 的能力分成三类：

```text
造数据：ADC 建模
看数据：数据分析
修数据：校准方法
```

对应到代码模块，大致是：

```text
ADC 建模：
python/src/adctoolbox/models/
python/src/adctoolbox/siggen/
python/src/adctoolbox/oversampling/
python/src/adctoolbox/timeinterleave/

数据分析：
python/src/adctoolbox/spectrum/
python/src/adctoolbox/aout/
python/src/adctoolbox/dout/
python/src/adctoolbox/fundamentals/
python/src/adctoolbox/toolset/

校准方法：
python/src/adctoolbox/calibration/
python/src/adctoolbox/dout/
python/src/adctoolbox/timeinterleave/
```

这三类能力会组成几个不同层次的闭环。

### 1. 程序建模 / 数字校准闭环

功能类型：

```text
造数据 + 看数据 + 修数据
```

涉及模块：

```text
models/
siggen/
spectrum/
aout/
dout/
calibration/
fundamentals/
```

闭环逻辑：

```text
理想 ADC 行为模型
-> 加入指定非理想
-> 生成 vin / bits / aout
-> 分析频谱、残差、bit activity、INL/DNL
-> 判断非理想造成了什么数据特征
-> 运行数字校准算法
-> 用校准参数重新处理输出
-> 比较校准前后结果
-> 调整模型或校准算法
```

以 SAR 电容失配为例：

```text
sar_ideal_weights
-> sar_apply_cap_mismatch 得到 actual_weights
-> sar_convert(vin, actual_weights) 得到 bits
-> sar_reconstruct(bits, nominal_weights) 得到未校准输出
-> calibrate_weight_sine(bits) 估计 calibrated_weights
-> bits @ calibrated_weights 得到校准后输出
-> 比较校准前后 SNDR / ENOB / spur / residual
```

最终目的：

```text
验证某类非理想是否会造成目标现象；
验证数字校准算法能不能修正这个现象；
建立“非理想类型 -> 数据表现 -> 校准效果”的因果关系。
```

核心问题：

```text
这个误差能不能被数字校准修掉？
需要多少数据、什么输入、什么频率条件？
校准后的参数是否稳定、是否能泛化？
```

### 2. 电路设计 / 仿真验证闭环

功能类型：

```text
看数据 + 修数据 + 造数据对照
```

涉及模块：

```text
spectrum/
aout/
dout/
calibration/
models/
siggen/
fundamentals/
toolset/
```

闭环逻辑：

```text
电路设计
-> Spectre / SPICE / Verilog-A 仿真
-> 导出波形或数字码
-> 导入 ADCToolbox 分析
-> 和行为模型中的非理想特征比对
-> 判断主要误差来源
-> 判断是改电路，还是交给数字校准
-> 修改电路或数字后端
-> 再仿真
```

最终目的：

```text
把电路仿真中的性能问题映射到具体误差来源和设计决策。
```

核心问题：

```text
这个性能问题来自哪块电路？
是 CDAC mismatch、comparator noise、reference settling、sampling jitter，还是 clipping？
是修改电容/比较器/reference/clock，还是用数字校准补偿？
```

典型例子：

```text
电路仿真 SNDR 下降
-> ADCToolbox 分析 spur / harmonics / residual
-> 用 CDAC mismatch 行为模型复现类似结果
-> calibrate_weight_sine 后指标恢复
-> 判断主要问题可能是 bit weight error
-> 若校准足够：数字后端使用 calibrated_weights
-> 若校准不足：回到 CDAC 尺寸、版图匹配、冗余结构设计
```

### 3. 芯片测试 / 数据诊断闭环

功能类型：

```text
看数据 + 修数据 + 造数据对照
```

涉及模块：

```text
spectrum/
aout/
dout/
calibration/
timeinterleave/
models/
siggen/
toolset/
```

闭环逻辑：

```text
真实芯片测试数据
-> 导入 ADCToolbox
-> 分析 spectrum / residual / INL / DNL / bit activity
-> 和行为模型中的典型非理想模式对照
-> 反推可能问题来源
-> 尝试数字校准或补偿
-> 改变测试条件验证假设
-> 反馈到测试方案、电路设计或数字算法
```

最终目的：

```text
从真实测量数据中诊断 ADC 问题，并判断问题属于测试、算法还是电路。
```

核心问题：

```text
芯片上的异常像哪类非理想？
是测试 setup 问题，还是芯片设计问题？
校准能否改善真实数据？
不同输入频率、幅度、温度、电源条件下问题是否一致？
```

### 4. 架构探索 / 规格权衡闭环

功能类型：

```text
造数据 + 看数据，必要时修数据
```

涉及模块：

```text
models/
siggen/
spectrum/
aout/
oversampling/
timeinterleave/
calibration/
fundamentals/
```

闭环逻辑：

```text
设定 ADC 架构和目标规格
-> 选择 bit 数、采样率、OSR、冗余结构、输入范围
-> 行为级快速仿真
-> 加入噪声、失配、非线性预算
-> 分析 SNR / SNDR / SFDR / ENOB / INL / DNL
-> 评估校准需求
-> 调整架构参数
-> 重复仿真
```

最终目的：

```text
在电路细节完成前，快速判断某种架构是否可能达到目标规格。
```

核心问题：

```text
需要多少 bit？
需要多少冗余？
允许多少电容失配？
是否必须加入数字校准？
模拟设计压力能否通过数字校准降低？
性能、功耗、面积、复杂度如何取舍？
```

### 5. 算法开发 / 回归验证闭环

功能类型：

```text
造数据 + 修数据 + 看数据
```

涉及模块：

```text
calibration/
models/
siggen/
spectrum/
aout/
dout/
tests/
examples/
```

闭环逻辑：

```text
提出新的分析或校准算法
-> 用可控模型生成测试数据
-> 跑算法
-> 和已知 truth 对比
-> 看指标是否改善
-> 加入更多 corner case
-> 写测试和示例
-> 回归验证
```

最终目的：

```text
保证 ADCToolbox 的算法本身可靠、可复现、可维护。
```

核心问题：

```text
算法在理想条件下是否正确？
在噪声、失配、频率偏差、数据长度不足时是否稳定？
会不会只对某个训练数据有效，换一个输入就失败？
```

总结起来，ADCToolbox 不是单纯的 ADC 仿真器，也不是单纯的频谱工具。
它的最终目标是：

```text
建立 ADC 行为建模、数据分析、数字校准、电路仿真和芯片测试之间的工程闭环。
```

一句话版：

```text
ADCToolbox 用“造数据、看数据、修数据”三类能力，
把 ADC 的非理想问题变成可复现、可诊断、可校准、可反馈到电路设计和测试验证的工程流程。
```

最核心的工程判断是：

```text
这个 ADC 性能问题是什么造成的？
它能不能在数字域校准？
如果不能，应该回到哪一块电路或测试条件去修改？
```

## 本库对应代码

建议先读：

```text
python/src/adctoolbox/models/sar.py
python/src/adctoolbox/siggen/nonidealities.py
python/src/adctoolbox/fundamentals/validate.py
python/src/adctoolbox/fundamentals/frequency.py
```

重点 API：

```python
import numpy as np
from adctoolbox.models import sar_ideal_weights, sar_convert, sar_reconstruct
```

## 读代码时具体看什么

打开：

```text
python/src/adctoolbox/models/sar.py
```

先找这几个函数，不需要一次读完整文件：

```text
sar_ideal_weights    -> 权重向量怎么生成
sar_convert          -> vin 怎么变成 bits
sar_reconstruct      -> bits 怎么乘 weights 变成 aout
```

读 `sar_convert` 时，只追踪这几个变量：

```text
vin_norm
weights
v_dac
v_test
bits
```

读 `sar_reconstruct` 时，只追踪：

```text
bits @ weights
```

这一阶段不要被更复杂的参数吓到。先把“数组形状 + 物理含义 + 单位”对应起来。

## 实验 1: 手写一次数字重构

在 Python 交互环境或临时脚本里运行：

```python
import numpy as np

bits = np.array([
    [0, 0, 0],
    [0, 0, 1],
    [0, 1, 0],
    [0, 1, 1],
    [1, 0, 0],
])

weights = np.array([4, 2, 1])
aout = bits @ weights

print(bits.shape)
print(weights.shape)
print(aout)
```

你应该看到：

```text
bits 是 5 个样本、3 个 bit
weights 是 3 个 bit 的权重
aout 是每个样本的重构值
```

## 实验 2: 修改权重观察重构变化

把权重改成：

```python
weights_bad = np.array([4.2, 1.9, 1.0])
```

比较：

```python
print(bits @ weights)
print(bits @ weights_bad)
```

这个小实验就是 SAR mismatch 的最小雏形：同一组 `bits`，不同的重构权重，会得到不同的输出。

## 阶段检查问题

1. `bits.shape == (N, M)` 中 `N` 和 `M` 分别代表什么？
2. 为什么 `bits @ weights` 是 ADC 数字重构，而不只是矩阵运算？
3. `Fin` 和 `freq = Fin / fs` 有什么区别？
4. 为什么“加一次随机噪声”还不等于 Monte Carlo 仿真？
5. `actual_weights` 和 `digital_weights` 是同一个东西吗？

如果这些问题还答不稳，不建议进入 Stage 01。
