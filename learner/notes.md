# ADC Toolbox Notes
## 1. Modeling ADC 的输入/输出 systems

### 代码 I/O 数据流

```text
最简数据流：理想正弦波参数
    -> 在 t[n] = n / Fs 上逐点取样，得到 vin
    -> sar_convert 得到 raw bit decisions / codes
    -> sar_reconstruct 得到 aout
```

Evidence:

```python
n = np.arange(N)
vin = DC + A * np.sin(2 * np.pi * Fin * n / Fs)  # shape == (N,)

weights = sar_ideal_weights(n_bits)       # shape == (n_bits,), MSB first
bits = sar_convert(vin, weights)          # shape == (N, n_bits), raw bit decisions
aout = sar_reconstruct(bits, weights)     # shape == (N,)
```

### Question: coherent sampling

逻辑链条：

```text
N 点 DFT 会把有限长度数据看成 N 点周期延拓
    -> 时间窗口长度 T = N / Fs
    -> 周期延拓的基频 f0 = 1 / T = Fs / N
    -> 第 k 个 DFT bin 对应 f_k = k * Fs / N
    -> DFT 系数 = 信号和第 k 个复指数基底取内积
    -> 如果 Fin = k * Fs / N，能量集中在第 k 个 bin
    -> 如果 Fin 不是 Fs/N 的整数倍，能量泄漏到多个 bin
```

所以 coherent sampling 是让采样窗口里刚好包含整数个输入周期：

```text
Fin / Fs = fin_bin / N
Fin = fin_bin * Fs / N
```

其中 `fin_bin` 就是 DFT 的 bin index，也是 N 点窗口里的正弦周期数。

如果 `Fin` 已定，就要选合适的 `Fs` 和 `N`，让：

```text
fin_bin = Fin * N / Fs
```

是整数。若 `Fs` 和 `N` 已定，则通常调整 `Fin` 到最近的 coherent frequency。

本库用 `find_coherent_frequency(fs, fin_target, n_fft)` 在目标频率附近找合适的 `fin_bin`，减少 FFT leakage。

连续傅里叶 vs DFT：

```text
CTFT：连续时间、无限长度/非周期信号 -> 连续频率
傅里叶级数：连续时间、周期 T 信号 -> k/T 离散频率
DFT：N 点离散数据，默认 N 点周期延拓 -> k*Fs/N 离散 bin
```

### Question: ADCToolbox 的系统闭环是什么？非理想 ADC 行为在哪些步骤加入？

ADCToolbox 的核心能力：

```text
造数据：ADC 建模
看数据：数据分析
修数据：校准方法
```

最终目的：

```text
把 ADC 的非理想问题变成可复现、可诊断、可校准、可反馈到电路设计和测试验证的工程流程。
```

核心闭环：

```text
1. 程序建模 / 数字校准闭环
   理想模型 -> 加非理想 -> 生成 bits/aout -> 分析 -> 校准 -> 比较校准前后
   目的：验证非理想的数据表现，以及数字校准是否有效。

2. 电路设计 / 仿真验证闭环
   电路设计 -> Spectre/SPICE/Verilog-A 仿真 -> 导入 ADCToolbox 分析
   -> 和行为模型比对 -> 判断误差来源 -> 改电路或交给数字校准 -> 再仿真
   目的：判断性能问题来自哪块电路，以及该改电路还是用数字校准。

3. 芯片测试 / 数据诊断闭环
   测试数据 -> ADCToolbox 分析 -> 和非理想模型对照 -> 尝试校准
   -> 改测试条件 / 反馈电路 / 修改算法
   目的：从真实数据中诊断问题来源。

4. 架构探索 / 规格权衡闭环
   架构假设 -> 行为级仿真 -> 加噪声/失配/非线性预算
   -> 分析指标 -> 评估校准需求 -> 调整架构
   目的：在电路细节完成前判断规格是否可达。

5. 算法开发 / 回归验证闭环
   新算法 -> 可控模型数据 -> 跑算法 -> 和 truth 对比 -> 加测试
   目的：保证分析和校准算法可靠、可复现。
```

非理想 ADC 行为加入的位置：

```text
1. 输入波形阶段：vin -> vin_nonideal
   例：thermal noise, jitter, static nonlinearity, clipping, drift

2. SAR 权重阶段：nominal_weights -> actual_weights
   例：sar_apply_cap_mismatch(...)

3. SAR 转换阶段：vin -> bits
   例：sampling_noise_rms, comparator_noise_rms

4. 数字重构阶段：bits -> aout
   例：nominal_weights / actual_weights / calibrated_weights
```

关键判断：

```text
这个 ADC 性能问题是什么造成的？
它能不能在数字域校准？
如果不能，应该回到哪一块电路或测试条件去修改？
```

### Monte Carlo 仿真

Monte Carlo 不是“加一次随机噪声”，而是：

```text
定义随机模型
    -> 抽一次 realization
    -> 跑完整 ADC 仿真
    -> 换 seed 重复很多次
    -> 统计 ENOB / SNDR / calibration error 的分布
```

本库中的体现：

```text
sar_apply_cap_mismatch(...)
    -> 抽一颗随机 CDAC mismatch 芯片

sar_convert(..., sampling_noise_rms=..., comparator_noise_rms=...)
    -> 加入采样噪声和比较器噪声

exp_d16_sar_unit_cap_mismatch_mc.py
    -> 对每个 mismatch sigma 跑 N_MC 次，统计 calibration 前后的 ENOB 分布
```

关键区别：

```text
一次随机噪声 = 一个 realization
很多次 realization + 统计分布 = Monte Carlo
```

seed 只是为了复现某一次 realization：

```python
rng = np.random.default_rng(seed)
```
## 2. Stage 01: ADC 基础、采样、量化、LSB

### 本阶段学习目标

- ADC 的输入、采样值、数字 code、重构输出。
- sampling、quantization、code、LSB、full-scale。
- 为什么 `2^N` 个 code 只能表示有限精度。
- 理想 N-bit ADC 的 SNR 约为 `6.02N + 1.76 dB`。
- 为什么真实 ADC 的 ENOB 通常用 measured SNDR 换算，而不一定等于 nominal bit 数。

### ADC I/O 数据流物理过程

```text
连续电压      -> 采样 sampling      -> 一串时间样本 vin
时间样本 vin  -> 量化 quantization  -> 一串 code / bits
code / bits   -> 数字重构           -> 可分析的输出波形 aout
```

对应到 ADCToolbox 的 SAR 模型：

```text
vin   -> 输入采样点，shape == (N,)
bits  -> 每个采样点的一组 SAR bit decision，shape == (N, n_bits)
aout  -> bits 按 digital weights 重构后的 waveform，shape == (N,)
```

具体 SAR bit trial 原理放到 Stage 04；Stage 01 先抓住 `vin`、`bits`、`aout` 不是同一个对象。

### 数学过程

#### 采样 sampling

```text
连续时间信号 x(t) 在离散时间点 t[n] = n / Fs 上被采样：

x[n] = x(n / Fs)
```

奈奎斯特采样定律：

```text
Fs > 2 * Fmax
```

其中 `Fmax` 是输入信号中需要保留的最高频率。若不满足这个条件，高频分量会 alias 到低频，导致数字序列中的频率含义被混淆。

相干采样在 Stage 00 中已经提及；Stage 02 会继续用它解释 FFT bin 和 spectral leakage。

questions: 奈奎斯特采样定律

#### 量化 quantization

```text
离散时间信号 x[n] 被量化为有限个数字 code。

输入范围：      [Vmin, Vmax]
full-scale：    FS = Vmax - Vmin
code 数量：     2^N
最大 code：     2^N - 1
量化步长：      LSB = FS / 2^N

理想量化 code = floor((x[n] - Vmin) / LSB)
合法范围：      0 <= code <= 2^N - 1
```

注意：

```text
Vmax 是输入范围上边界，不是额外多出来的 code。
2^N 是 code 数量，最大 code 是 2^N - 1。
LSB 是一个电压间隔，不是最低 bit 本身。
```

code 和 bits 的关系可以写成 MSB-first：

```text
bits = [b0, b1, ..., b(N-1)]
code = b0*2^(N-1) + b1*2^(N-2) + ... + b(N-1)*2^0
```

ADCToolbox 的 SAR `bits` 约定：

```text
bits[:, 0]  -> MSB
bits[:, -1] -> LSB
```

questions: 量化过程在本库代码中如何体现？本库有体现非理想量化的 ADC 建模吗？

#### 量化误差

理想量化误差可以定义为：

```text
e[n] = quantized_value[n] - x[n]
```

有些资料会反过来写 `x[n] - quantized_value[n]`。符号会变，但 RMS 和噪声功率不变。这里建议统一用课程里的 `quantized - input`。

经典近似中：

```text
e ~ Uniform(-LSB/2, +LSB/2)
RMS(root mean square) quantization noise = LSB / sqrt(12)
```

这个均匀分布是假设近似，不是永远严格成立。它通常要求输入足够丰富、不超量程，并且量化误差和输入近似不相关。(因为假设了分布均匀，而实现分布均匀的条件是足够大的样本)

questions: 这里涉及到的统计分布知识推导，以及代码体现

answer - key points:

```text
1. 经典模型讨论的是去均值后的量化噪声：
   e_noise ~ Uniform(-LSB/2, +LSB/2)
   E[e_noise] = 0

2. 设 Δ = LSB，p(e) = 1/Δ：
   E[e^2] = ∫_{-Δ/2}^{+Δ/2} e^2 * (1/Δ) de
          = Δ^2 / 12
   RMS/std = Δ / sqrt(12) = LSB / sqrt(12)

3. 当前库的 apply_quantization_noise 是 floor + lower-edge reconstruction：
   code = floor((x - Vmin) / LSB)
   quantized_value = code * LSB + Vmin

4. 所以直接误差 e = quantized_value - x 更接近：
   e ~ Uniform(-LSB, 0)
   E[e] = -LSB/2
   E[e^2] = LSB^2/3
   direct RMS = LSB/sqrt(3)
   但去均值后的 std 仍是 LSB/sqrt(12)

5. SNR/FFT 分析通常排除 DC bias，因此量化噪声功率仍使用：
   noise_rms = LSB / sqrt(12)

6. Dither 逻辑链：
   无 dither -> 量化误差可能和输入相关 -> spur/harmonic
   加 dither -> 量化前随机扰动 -> 误差更接近独立噪声
              -> spur/harmonic 减少 -> noise floor 上升
   物理对应：可刻意注入小噪声，也可由 thermal noise、kT/C noise、
             comparator noise、reference noise 等天然噪声等效提供
   工程意义：牺牲一点 SNR/noise floor，换更少的确定性失真和更好的 SFDR/THD
```

#### 理想 SNR 和 ENOB

```text
full-scale 范围：FS = Vmax - Vmin
满幅正弦 peak amplitude：A = FS / 2
信号 RMS：signal_rms = A / sqrt(2) = FS / (2 * sqrt(2))
量化噪声 RMS：noise_rms = LSB / sqrt(12) = FS / (2^N * sqrt(12))

SNR_ideal = 20 * log10(signal_rms / noise_rms)
          = 6.02N + 1.76 dB
```

理想情况下，用理想 SNR 反推：

```text
ENOB_ideal = (SNR_ideal - 1.76) / 6.02 ~= N
```

真实 ADC 中更常用 measured SNDR 换算：

```text
ENOB = (SNDR_measured - 1.76) / 6.02
```

因为真实 ADC 的有效位数受到随机噪声和失真共同影响，所以 ENOB 不一定等于 nominal bit 数。

questions: 理想 SNR 和 ENOB 的推导过程，以及代码体现。为什么满幅正弦 A = FS / 2，简要说明过程。

answer - key points:

```text
1. 满幅正弦刚好填满 ADC 输入范围：
   FS = Vmax - Vmin
   peak-to-peak = 2A = FS
   A = FS / 2

2. 正弦 RMS：
   x(t) = A sin(ωt)
   x_rms = sqrt(mean(x(t)^2))
         = sqrt(mean(A^2 sin^2(ωt)))
         = A * sqrt(mean(sin^2(ωt)))
         = A / sqrt(2)

3. 积分背景：
   mean(sin^2(ωt)) = (1/T) * ∫_0^T sin^2(ωt) dt = 1/2

4. 所以：
   signal_rms = A / sqrt(2) = FS / (2 * sqrt(2))

5. 若信号含 DC：
   total_rms = sqrt(DC^2 + A^2/2)
   但 ADC SNR/SNDR 中的 signal power 通常只看 AC fundamental，不把 DC 算入 signal power
```

### 基本 ADC 电路

```text
SAR ADC 基本电路框架：

sampling switch
  -> 控制什么时候把输入接到采样节点
  -> 主要直觉：on-resistance、charge injection、thermal noise

sampling capacitor
  -> 存住采样瞬间的输入电压
  -> 基本关系：Q = C * V
  -> C 越大，kT/C noise 越小，但面积、驱动难度和功耗更高

reference
  -> ADC 的电压基准，决定 full-scale 和 CDAC trial voltage
  -> 常见符号：Vref、Vrefp/Vrefn、Vcm

DAC / CDAC
  -> DAC = Digital-to-Analog Converter
  -> CDAC = Capacitive Digital-to-Analog Converter，也叫 Capacitor DAC
  -> SAR ADC 中用加权电容产生逐位试探电压
  -> 例：4-bit 理想权重可理解为 [8C, 4C, 2C, 1C]

comparator
  -> 比较输入和 CDAC 试探电压，输出 0/1 判决
  -> 主要直觉：noise、offset、metastability、kickback

SAR logic
  -> 控制 CDAC 从 MSB 到 LSB 逐位试探
  -> 读取 comparator 判决并记录 bits
```

角色分工：

```text
CDAC       -> 产生试探电压
comparator -> 判断大小
SAR logic  -> 安排试探顺序并记录 bits
```

#### ADC 噪声和误差的来源

| 来源 | 电路含义 | 常见表现 |
|---|---|---|
| 量化误差 | 有限 bit 数 | 理想噪声底 |
| 热噪声 | 电阻、开关、电容采样噪声 | SNR 降低 |
| comparator noise | 比较器输入等效噪声 | code decision 抖动 |
| reference noise | 参考电压不稳 | 增益误差、噪声增加 |
| offset | 比较器或前端偏置 | code 偏移 |
| 非线性 | 开关、参考、DAC/CDAC 非理想 | harmonic、spur、SFDR 下降 |
