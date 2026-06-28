# ADC Toolbox Notes

## 1. Modeling ADC 的输入/输出 systems

### 代码 I/O 数据流

```text
最简数据流：理想正弦波参数
    -> 在 t[n] = n / Fs 上逐点取样，得到 vin
    -> sar_convert 得到 raw bit decisions / codes
    -> sar_reconstruct 得到 aout
```
#### Evidence:

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

##### questions: 奈奎斯特采样定律

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

##### questions: 量化过程在本库代码中如何体现？本库有体现非理想量化的 ADC 建模吗？

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

##### questions: 这里涉及到的统计分布知识推导，以及代码体现

##### answer - key points:

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

##### questions: 理想 SNR 和 ENOB 的推导过程，以及代码体现。为什么满幅正弦 A = FS / 2，简要说明过程。

##### answer - key points:

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

6. 6.02 和 1.76 两个魔数的来源（正文 stage_01 第 5 节有完整推导）：
   SNR_linear = signal_rms / noise_rms
              = [FS/(2√2)] / [FS/(2^N·√12)]
              = 2^N · √(12/8)
              = 2^N · √(3/2)
   注意 FS 约掉了：理想 SNR 与具体满幅电压无关，只取决于 N。

   SNR_ideal_dB = 20·log10(2^N · √(3/2))
               = 20N·log10(2) + 10·log10(3/2)
               ≈ 6.02·N + 1.76 dB

   6.02 = 20·log10(2)       -> "1 位 ≈ 6 dB" 的精确值
   1.76 = 10·log10(3/2)     -> 满幅正弦 vs 量化噪声的功率比常数

7. ENOB 是理想 SNR 公式的反函数，不是新物理量：
   SNDR = 6.02·ENOB + 1.76
   ENOB = (SNDR - 1.76) / 6.02

   - 用 SNDR 不用 SNR：理想 ADC 无失真 SNR=SNDR；真实 ADC 有失真，
     用 SNDR 反解才反映"信号被噪声+失真共同拖累"
   - 理想 N 位：ENOB ≈ N
   - 真实 ADC：噪声+失真 > 量化噪声 -> ENOB < N
   - 过采样 + 噪声成型：in-band ENOB 可能 > N（带内等效精度，非物理位数）
   - ENOB 是换算结果，不是 ADC 固有属性（纯软件正弦+噪声也能算 ENOB）
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

## 3. Stage 02: FFT 和动态性能指标

### 本阶段学习目标

- 理解 ADC 动态性能测试用单音sine的原因
- DFT/FFT bin、频率分辨率、single-sided-spectrum是什么
- 理解 coherent sampling 的概念和重要性
- spectral leakage 的原因和表现， windowing 的作用和局限
- SNR、SNDR、SFDR、THD、ENOB、NSD 分别衡量什么
- 为什么频谱分析必须排除DC、fundamental和harmonics
- analyze_spectrum 的输入输出是什么，如何对应到理论概念
- 如何从频谱现象分析 ADC 的性能问题

### 核心笔记

正弦信号、normalized frequency、DFT、coherent sampling 已经在 Stage 02 正文中系统展开；
notes 只保留后续容易混淆的核心逻辑。

#### 1. Two-sided 和 single-sided spectrum

核心逻辑不是“FFT 只能算到 `Fs/2`”，而是：

```text
采样后：
exp(j 2π (f + Fs) n / Fs)
= exp(j 2π f n / Fs) * exp(j 2π n)
= exp(j 2π f n / Fs)
```

因为 `exp(j 2π n) = 1`，所以：

```text
f 和 f + Fs 对离散序列完全等价
-> 离散时间频谱以 Fs 为周期
-> FFT 给出的是一个宽度为 Fs 的频谱周期
```

raw FFT 后半段解释成负频率，不只是人为把频率减去 `Fs`，而是因为 DFT 基底有
modulo-N 等价：

```text
exp(j 2π k n / N)
= exp(j 2π (k - N) n / N)
```

因为：

```text
exp(-j 2π n) = 1
```

所以：

```text
k 和 k-N 表示同一个离散时间复指数基底。
```

这个周期可以按 raw FFT 顺序看成：

```text
[0, Fs)
```

也可以重排成 centered two-sided spectrum：

```text
[-Fs/2, Fs/2)
```

所以 `Fs/2` 不是 FFT 的“计算上限”，而是以 0 为中心取一个完整频谱周期时的边界，也是 baseband 信号不 alias 的最高频率。

对于实数 ADC 输出：

```text
X[-k] = conj(X[k])
|X[-k]| = |X[k]|
```

负频率半边只是正频率半边的镜像，所以工程上常只画：

```text
[0, Fs/2]
```

这就是 single-sided spectrum。

single-sided 幅度补偿规则：

```text
普通 AC bin：
    正负频率各占一半幅度
    -> single-sided amplitude 要乘 2

DC bin:
    k = 0，没有 +0/-0 两个不同频率
    -> 不乘 2

Nyquist bin:
    k = N/2，仅偶数 N 存在
    exp(+jπn) = exp(-jπn) = (-1)^n
    -> +Fs/2 和 -Fs/2 是同一个离散频率
    -> 不乘 2
```

一句话总结：

```text
复指数 -> 解释正负频率
采样 -> 解释频谱以 Fs 为周期
实数信号 -> 解释负频率是共轭镜像
single-sided -> 只保留 0~Fs/2，并对普通 AC bin 做幅度/功率补偿
```

#### 2. Spectral leakage 和 window

核心数学链：

```text
有限 FFT 不是直接分析无限长 x[n]，
而是分析 y[n] = x[n] w[n]
```

注意：

```text
乘 window 不是把 DFT 变成连续傅里叶变换。
采样本身也不等于乘 rectangular window。
DTFT 只是分析工具，用来观察 windowed signal 的连续频率响应。
N 点 DFT = 在 ω_k = 2πk/N 上采样 Y(e^{jω})。
```

更严谨地说：

```text
ADC 采样 -> 得到离散序列
只取其中 N 点做 FFT -> 有限截取
有限截取 -> 可以建模成乘 rectangular observation mask
```

这个 rectangular mask 不是凭空多出来的，而是 DFT 求和范围的另一种写法：

```text
sum_{n=0}^{N-1} x[n] e^{-j2πkn/N}
= sum_{n=-∞}^{∞} x[n] r_N[n] e^{-j2πkn/N}

r_N[n] = 1, 0 <= n <= N-1
       = 0, otherwise
```

在有限向量内部，乘 `ones(N)` 的确什么都没改变；在无限序列视角里，`r_N[n]`
表示 N 点内参与分析、N 点外不参与分析。

所以“不显式加 window”的准确含义是：

```text
不额外乘 Hann / Blackman / flattop 等 taper window。
但有限截取本身仍然可用 rectangular mask/window 描述。
```

```text
w_R[n] = 1, 0 <= n <= N-1
```

关键澄清：

```text
理想单音是一根谱线
-> 指无限长单音的 DTFT
-> 或有限 DFT 中刚好 coherent，落在某一个 DFT basis 上
```

如果非相干：

```text
x[n] = A e^{j2π(10.3)n/N}
```

它不是任何一个整数 bin 的 DFT basis，所以有限 N 点 DFT 必须用多个 basis 共同表示它：

```text
non-coherent finite record
-> not exactly one DFT basis vector
-> many nonzero FFT bins
-> leakage
```

所以：

```text
不是“只有额外加 window 才有 leakage”；
而是“把无限信号截成有限 N 点去分析，可以等价建模为乘了 observation window”。

不显式加 taper window -> rectangular observation window -> 仍然会 leakage
显式加 Hann/Blackman/... -> 把 rectangular 改成其它 window -> 改变 leakage 的形状
```

乘 window 的目的：

```text
改变有限观测带来的 leakage 形状，选择一个频域分析核 W(e^{jω})
-> 单音在频谱上的扩散形状由 W 决定
-> 用主瓣/旁瓣 tradeoff 改善 signal / spur / noise 分类
```

时域相乘对应频域卷积：

```text
y[n] = x[n] w[n]
<->
Y(e^{jω}) = (1 / 2π) X(e^{jω}) * W(e^{jω})
```

最短推导：

```text
x[n] = (1 / 2π) ∫ X(e^{jθ}) e^{jθn} dθ

Y(e^{jω})
= sum_n x[n]w[n]e^{-jωn}
= (1 / 2π) ∫ X(e^{jθ}) [sum_n w[n]e^{-j(ω-θ)n}] dθ
= (1 / 2π) ∫ X(e^{jθ}) W(e^{j(ω-θ)}) dθ
```

对单音：

```text
x[n] = A e^{jω0n}
X(e^{jω}) = 2πA δ(ω - ω0)
```

所以：

```text
Y(e^{jω}) = A W(e^{j(ω - ω0)})
```

结论：

```text
单音的 leakage 形状 = window 频谱 W 的形状
```

Rectangular window 的频谱：

```text
W_R(e^{jω})
= e^{-jω(N-1)/2} * sin(Nω/2) / sin(ω/2)
```

它的零点在：

```text
ω = 2πm / N
```

所以 coherent + rectangular 时，其它 FFT bin 正好采到零点，看起来没有 leakage。
non-coherent 时，FFT bin 不再采到零点，旁瓣被采出来，形成 leakage。

主瓣和旁瓣：

```text
main lobe 主瓣：
    window 频谱中心峰附近的主要能量区域
    -> 决定一个单音占多少 bin
    -> 决定频率分辨率

side lobe 旁瓣：
    主瓣外侧的小峰
    -> 决定强信号向远处泄漏多少
    -> 影响小 spur 是否被盖住
```

Window 的 tradeoff：

```text
rectangular:
    主瓣窄，频率分辨率好
    旁瓣高，远处 leakage 强

Hann / Blackman:
    边界更平滑
    旁瓣更低
    主瓣更宽
    需要合并更多 bin

Flattop:
    幅度测量更稳
    主瓣很宽
```

必要校正：

```text
coherent gain:
    CG = sum(w[n]) / N
    -> W(0)/N，表示 window 频率响应的中心高度
    -> 只看 coherent tone 中心 bin 时，功率高度和 CG^2 有关

ENBW:
    ENBW = N * sum(w[n]^2) / (sum(w[n]))^2
    -> 不是主瓣宽度，而是等效白噪声带宽
    -> DFT bin 可看成由 W(e^{jω}) 决定的分析滤波器
    -> 单音看中心增益 W(0)=sum(w)
    -> 白噪声看功率面积 ∫|W|^2 dω
    -> Parseval: (1/2π)∫|W|^2 dω = sum(w^2)
    -> 用 FFT bin 宽度 2π/N 归一化后得到 ENBW
    -> 不要理解成“CG 校正 signal，ENBW 再校正 noise”
    -> CG^2 * ENBW = mean(w^2)，代码实际做一次 RMS power normalization
```

与 ADCToolbox 代码对应：

```text
python/src/adctoolbox/spectrum/_window.py
    _create_window(win_type, N)
        -> window_vector
        -> window_gain = sum(window_vector) / N
        -> equiv_noise_bw_factor = N*sum(w^2)/(sum(w)^2)

python/src/adctoolbox/spectrum/compute_spectrum.py
    data_windowed = data_normalized * window_vector
    power_correction = _calculate_power_correction(window_gain, equiv_noise_bw_factor)
    power_spectrum *= power_correction

    power_correction = 4 / (window_gain^2 * ENBW)
                     = 4 / mean(w^2)
    -> 按 window RMS power 归一化，再做 one-sided / dBFS 风格标定
    -> CG 和 ENBW 没有分别作用到 signal/noise；它们只合成一次 correction

    sig_peak = power_spectrum[fundamental_bin]
        -> center bin power

    sig_linear = sum(power_spectrum[fundamental_bin-side_bin :
                                    fundamental_bin+side_bin+1])
        -> fundamental 主瓣合并功率
        -> sig_pwr_dbfs 来自这个量

side_bin:
    fundamental_bin ± side_bin 被合并为 signal power
    当前 plotspec-style harmonic power 取 harmonic center bin
    side_bin 对 harmonic 主要用于 collision 判断
    noise 估计一定排除 DC 与 fundamental 主瓣
    harmonic 排除取决于 nf_method:
        nf_method=3 排除 harmonic center bin
        nf_method=4 排除 harmonic_bin ± side_bin
```

判断：

```text
side_bin 太小:
    主瓣没收全 -> 信号被误算成 noise/spur

side_bin 太大:
    附近真实 spur 被吞进 fundamental/harmonic
```

#### 3. SNR / NSD / OSR

核心关系：

```text
SNR 看总噪声：
    SNR_dB = P_signal_dBFS - P_noise_total_dBFS

NSD 看每 Hz 噪声密度：
    P_noise_total = NSD_linear * BW
    P_noise_total_dBFS = NSD_dBFS_Hz + 10log10(BW)

所以：
    NSD_dBFS_Hz = P_signal_dBFS - SNR_dB - 10log10(BW)
    SNR_dB = P_signal_dBFS - NSD_dBFS_Hz - 10log10(BW)
```

OSR 改变 in-band bandwidth：

```text
Nyquist bandwidth = fs/2
    -> FFT 仍然可以显示到这里

BW = fs / (2 * osr)
    -> in-band bandwidth
    -> 动态指标只统计 0 ~ BW_signal

osr = fs / (2 * BW_signal)
```

对白噪声：

```text
osr 增大
-> BW 变小
-> 积分总噪声变小
-> SNR 提高 10log10(osr)
-> NSD 本身不应因为只改分析带宽而改变
```

代码对应：

```text
compute_spectrum.py
    freq = arange(len(power_spectrum)) * fs/N
        -> 频率轴仍到 fs/2

    n_inband = rfft_inband_bin_count(N, osr)
        -> edge_bin = N/(2*osr)
        -> 只用 spectrum[:n_inband] 计算 in-band 指标

    noise_floor_dbfs = sig_pwr_dbfs - snr_dbc
    nsd_dbfs_hz = noise_floor_dbfs - 10log10(fs/(2*osr))
```

#### 3b. 动态指标的基本定义（SNR / SNDR / SFDR / THD / ENOB）

Stage 02 不要求深究每个指标，但要记住基本定义、公式、以及它们对什么问题敏感。

设频谱已分类为：`P_signal` / `P_noise`（排除 DC、fundamental、harmonics）/ `P_harm` / `P_spur_max`。

```text
SNR  = 10 log10(P_signal / P_noise)                   只看随机噪声
SNDR = 10 log10(P_signal / (P_noise + P_harm))        噪声 + 失真
THD  = 10 log10(P_harm / P_signal)                    只看 harmonic distortion
SFDR = 10 log10(P_signal / P_spur_max)                只看最大单个 spur
ENOB = (SNDR - 1.76) / 6.02                           由 SNDR 换算
```

##### 几个关键不等式和判据

```text
1. SNDR ≤ SNR 永远成立，等号当且仅当 P_harm = 0
   -> 实验 1: 纯噪声信号 SNR ≈ SNDR
   -> 实验 4: clipping 后 SNR 继续上升，SNDR 反而下降（harmonic 暴涨）

2. ENOB 完全由 SNDR 决定，不是 ADC nominal bit 数的属性
   -> ENOB = (SNDR-1.76)/6.02
   -> 一个纯软件生成的浮点正弦+噪声也能算出 ENOB（实验 1）

3. SFDR 通常比 SNR 高 10-20 dB
   -> SFDR 看单个最大 spur 峰值
   -> SNR 看所有 noise bin 功率之和
   -> 同样噪声下，单个 bin 峰值 < 总功率

4. SNR 与 signal_rms 的关系，取决于噪声类型：
   thermal/quantization 主导: SNR ∝ signal_rms（实验 4 小信号区，20 dB/decade）
   jitter 主导:              SNR 与 A 无关（见 jitter key points）
```

##### 实验中的大致情况分析

```text
实验 1 (clean sine + 白噪声):
    SNR ≈ SNDR        -> 无失真
    ENOB = 14.8       -> 纯由 noise_rms 决定，与 ADC 无关
    SFDR > SNR 20 dB  -> 噪声统计峰值效应

实验 4 (扫幅度，加 clipping):
    小信号区:    SNR ≈ SNDR, 随 A 线性上升（20 dB/decade）
    sweet spot:  SNDR 峰值 @ 0 dBFS, SNR ≈ SNDR
    过载区:      SNR 继续上升，SNDR 反而下降，THD 飙升变正
    SNR/SNDR 分叉点 = clipping 开始起作用的位置

实验 5 (固定 A，扫 Fin, 只加 jitter):
    SNR_jitter 每 octave 降 6 dB
    全频段 SNR ≈ SNDR（jitter 噪声虽是"裙边"形状，但仍是噪声不是 harmonic）
```

##### 指标选择直觉

```text
SNR 差  -> 先怀疑 thermal noise / jitter / reference noise
THD 差  -> 先怀疑非线性 / clipping / CDAC mismatch / settling
SFDR 差 -> 先定位最大 spur 频率，再判断它是 harmonic 还是外部干扰
ENOB 差 -> 不够具体，拆成 SNR/THD/SFDR 分别看原因
```

详细推导见 stage_02_fft_metrics.md 第 6、7 节。

#### 4. ENBW 的双重角色：power correction 与 noise floor 光滑度

##### question: 实验 3（windowing deep dive）里，同一个信号换不同 win_type，为什么 Hann/Blackman/Flattop 的 noise floor 看起来很光滑，rectangular/Hamming 全是毛刺？这和指标有关吗？

##### answer - key points:

```text
1. 单个 FFT bin 的白噪声功率服从指数分布：
   std(power_per_bin) ≈ mean(power_per_bin)
   -> bin-to-bin 天然波动 5-6 dB
   -> 白噪声 FFT 本来就该是锯齿状直线，不是水平线

2. ENBW 决定相邻 bin 的相关性：
   ENBW = 1.0 (rectangular)  -> 相邻 bin 主瓣几乎不重叠 -> 不相关 -> 全毛刺
   ENBW = 1.5 (Hann)         -> 相邻 bin 显著重叠       -> 相关   -> 较光滑
   ENBW = 3.77 (flattop)     -> 多个 bin 重叠           -> 非常光滑

3. ENBW > 1 在频域相当于做了滑动平均：
   ENBW 越大 -> 平均窗口越宽 -> noise floor 视觉方差越小

4. 这是 ENBW 的第二个角色。第一个角色是 5.11.3 的 power correction：
   每个 bin 收到 noise 功率 ∝ sum(w^2) ∝ ENBW
   所以 power_correction = 4/mean(w^2) 要除掉它

5. 易错点：noise floor 光滑 ⟹ 测量更准？不。
   光滑只是 ENBW 平均的视觉效果，代价是主瓣变宽 -> 频率分辨率下降
   Flattop noise 最光滑，但两个靠近的 spur 分不开
   rectangular noise 最毛刺，但频率分辨率最好

6. 这也解释了 short FFT (N=128) 下主瓣宽的 window ENOB 反而虚高：
   大主瓣把 fundamental 附近多个 noise bin 平均进了
   sig_bin_start:sig_bin_end 的合并范围 -> noise 估计偏低 -> SNDR 虚高
   N 越小、bin 越少，这个效应越明显

7. 代码锚点：python/src/adctoolbox/spectrum/_window.py
   equiv_noise_bw_factor = N*sum(w^2)/sum(w)^2

8. 详细推导见 stage_02_fft_metrics.md 5.11.3b
```

#### 5.jitter
理想采样：在精确时刻 t[n] = n/Fs 取样。

有 jitter 的采样：实际采样时刻偏移了一个随机量 δt[n]：
```text
t_actual[n] = n/Fs + δt[n]
```

关键假设：

- δt[n] 在不同 n 之间不相关（白噪声假设）
- δt[n] 和信号 x(t) 不相关
- δt[n] << 1/Fin（小抖动假设）

核心近似（小抖动线性化）：当 2π·Fin·δt[n] 很小时，sin(θ + ε) ≈ sin(θ) + ε·cos(θ)：

```text
x_jit[n] ≈ A·sin(2π·Fin·n/Fs) + A·cos(2π·Fin·n/Fs) · 2π·Fin·δt[n]
          = x[n]                              + Δx[n]

Δx[n] = A·cos(2π·Fin·n/Fs) · 2π·Fin·δt[n]
      = (dx/dt)|_{t=n/Fs} · δt[n]

噪声功率
E[(Δx)²] = E[(A·cos(·))²] · E[(2π·Fin·δt)²]
         = (A²/2) · (2π·Fin)² · σt²

SNR_jitter = signal_rms / noise_rms_jitter
           = signal_rms / (signal_rms · 2π·Fin · σt)
           = 1 / (2π·Fin · σt)

最终公式
SNR_jitter_dB = 20·log10(1/(2π·Fin·σt))
              = -20·log10(2π·Fin·σt)
```

##### key points:

```text
1. jitter 电压误差的本质：
   Δx[n] = (dx/dt)|_{t=n/Fs} · δt[n]
   = 信号在那一刻的斜率 × 时间偏移
   -> 高频 / 大幅度信号 dx/dt 大，同一 δt 造成更大 Δx
   -> 这就是"高频对 jitter 更敏感"的物理根源

2. SNR_jitter 和信号幅度 A 无关（A 在分子分母约掉）：
   这是 jitter 和 thermal/quantization noise 的本质区别。
   增大信号幅度能压过 thermal / quantization，但压不过 jitter。
   所以实验 5 用固定 A=0.5 就能直接测出 SNR_jitter。

   thermal noise:     SNR ∝ A
   quantization:      SNR ∝ 2^N
   jitter:            SNR 与 A 无关

3. jitter 噪声的频域形状——fundamental 两侧的"裙边"：
   Δx[n] = cos(2π·Fin·n/Fs) · δt[n]   (单音 × 白噪声)
   -> 时域相乘 = 频域卷积 (5.3 节)
   -> 余弦的 DTFT 是 ±Fin 两根冲激谱线 (5.1 节)
   -> 冲激卷积搬移：G(ω) * δ(ω-ω0) = G(ω-ω0)
   -> 白噪声被整体搬移到 ±Fin 附近

   只看一根冲激的卷积结果仍是平坦的，裙边来自：
   a) 真实时钟 δt 不是严格白噪声，close-in phase noise 在 0 频附近抬升
   b) 有限 FFT 的 window 主瓣/旁瓣让形状进一步展开
   c) fundamental 主瓣 leakage 和搬来的 jitter 噪声在 Fin 附近叠加

4. jitter 主导的频谱判据：
   thermal/quantization 主导 -> 整段 noise floor 平坦
   jitter 主导 -> fundamental 两侧抬起裙边，远处反而干净

5. 详细推导见 stage_02_fft_metrics.md 4.1 / 4.2
```

## stage03：正弦拟合与 residual 误差分析

### 本阶段目标
- 理解为什么ADC单音测试要拟合一个 ideal sine
- residual/error 的定义
- error PDF、error autocorrelation、error spectrum 分别回答什么问题
- 如何根据 residual 判断噪声、失真、Memory、glitch 等问题

### 核心问题

```text
原始输出 y[n]
--> 拟合 ideal sine 得到 y_fit[n]
--> residual/error = y[n] - y_fit[n]
--> 分析 residual 的形状
```

### 1. 模型分解：单音测试的写法 y[n] = ideal_sine + error

```text
y[n] = ideal_sine[n] + error[n]

残差 residual/error 的定义：
error[n] = y[n] - ideal_sine[n]

分解的意义：
理想正弦完全确定——A、f、phase、DC 四个参数，任何n的值都可以精确算出
--> ADC所有的非理想都被归结到 error[n] 里
--> 核心思路，将精确的信息提取出来，剩下的就是误差，分析误差就能分析 ADC 的非理想
```

### 2.线性最小二乘（频率已知时：3 参数 A, B, C 的解析解）

```text
y ≈ X·β

X = [cos(2πfn), sin(2πfn), 1]    (N×3 矩阵，每行是 n=k 时的三个基底值)
β = [A, B, C]ᵀ                   (3×1 未知参数)
y = [y[0], y[1], ..., y[N-1]]ᵀ  (N×1 观测数据)
```

最小二乘求：

```text
min ||X·β - y||²
```

对 β 求梯度等于零（假设 XᵀX 可逆；对 cos/sin/1 基底只要 N ≥ 3 且频率不为 0 或 0.5
即满足），得到正规方程（normal equation）：

```text
L(β) = ||X·β - y||² = (X·β - y)ᵀ(X·β - y)
∂L/∂β = 2·Xᵀ·(X·β - y) = 0
-> XᵀX·β = Xᵀy
-> β = (XᵀX)⁻¹·Xᵀy   (XᵀX 可逆时)
```

即决定出一组系数，使得拟合误差最小。

questions： 为什么要拟合一个新的 ideal sine，而不是直接用输入信号的理想正弦？这样算出来的误差准吗？

##### answer - key points:

```text
1. 为什么必须 fit，不能用标称参数：
   - 测试源（AWG）的 A、f、phase 都有偏差
   - 信号链（驱动放大器/滤波器/balun）会改变信号
   - ADC 实际看到的正弦 ≠ AWG 标称
   - error 是高斯白噪声时，最小二乘 = MLE，统计上最优

2. fit 的本质是"正交投影"（不是"平均"）：
   把信号投影到 [cos(ωn), sin(ωn), 1] 子空间
   正交于这个子空间的成分 → 完整留在 residual
   在这个子空间内的成分 → 被 fit 吸收

3. 哪些误差会完整进 residual（不污染 fit）：
   - 所有 harmonic（coherent 采样下与 fundamental 正交）
   - 高斯白噪声
   原因：X^T·error = 0，β 解不受影响
   实验证据：单音 + 100% HD2，fit_amp 偏差 < 0.05%

4. 哪些误差会被 fit 吸收（fit 的盲点）：
   - AM（边带接近 fundamental，弱不正交）→ fit_amp 偏高 0.1-0.3%
   - 频率估计偏差 → residual 出现假尖峰（§ 6.4）
   - non-coherent → harmonic 微量泄漏进 fit

5. fit 盲点正是 by_value / by_phase 存在的动机
   它们不依赖 fit，专门看 AM/PM 失真

6. 判断 fit 是否被污染：
   - fit_freq 偏离 coherent bin > 0.01 bin → 警惕
   - residual 在 fundamental 附近有尖峰 → 频率估计不准
   - rmse 远超预期噪声底 → 有大结构没被 fit 解释

7. 详细推导见 stage_03 § 3.5（正交投影）和 § 3.5.5（实验）
```

### 3.最小二乘（频率未知 --> 进行参数拟合和迭代）

实际测试中 f 可能不准确（测试源有偏差）、或完全未知
（真实芯片测量）。这时要同时拟合 (A, B, C, f) 四个参数——但频率 f 出现在 cos 和
sin 的**内部**，不再是线性参数：

```text
ideal_sine[n] = A·cos(2πfn) + B·sin(2πfn) + C
                     ↑ f 在三角函数里面
```
**不能直接套线性最小二乘**

#### 3.1 用FFT找初始频率估计

对 y[n] 做 FFT，找到最大 bin 对应的频率 f0 作为初始估计。
--> 对于主频非相干，代码使用**parabolic interpolation**

```python
if 0 < k < len(spec) - 1:
    r = 1 if spec[k + 1] > spec[k - 1] else -1
    delta = r * spec[k + r] / (spec[k] + spec[k + r])
    k += delta
```

直觉：如果真实峰在 bin k 和 k+1 之间，那 spec[k+1] > spec[k-1]，峰更靠近 k+1。
用三个点 `(k-1, k, k+1)` 的幅度拟合一条抛物线，顶点的 x 坐标就是 sub-bin 估计。

**纠正**：实际代码（fit_sine_4param.py 第 123-126 行）是**两点简化版**，不是标准三点抛物线：

```text
标准三点 log-domain 抛物线：
    α = log|spec[k-1]|,  β = log|spec[k]|,  γ = log|spec[k+1]|
    δ = 0.5·(α - γ) / (α - 2β + γ)
    精度: ~0.01-0.1 bin

本库简化两点版：
    r = sign(spec[k+1] - spec[k-1])
    δ = r·spec[k+r] / (spec[k] + spec[k+r])
    精度: ~0.1-0.3 bin（比标准版差）
```

本库用简化版是合理的：因为后续有 Taylor 迭代修正，初始估计精度不影响最终结果。

questions：插值的精度和 FFT bin 数量、信号幅度、噪声水平有关吗？parabolic interpolation 的原理是什么？为什么选择 parabolic 而不是其他曲线？

##### answer - key points:

```text
1. parabolic interpolation 是什么：
   FFT 找最大 bin k 后，真实峰通常不在整数 bin 上（落在 k 和 k±1 之间）
   parabolic = 用 k 附近的几个 spec 值拟合一条抛物线，顶点位置就是 sub-bin 精度的频率
   把精度从 1 bin 提到 ~0.1 bin（三点版可到 ~0.01 bin）

2. 为什么数学上是抛物线（核心原理）：
   rectangular window 的频域响应是 Dirichlet kernel: sin(Nω/2)/sin(ω/2)
   对 log|W_R| 在主瓣峰值 ω≈0 附近做 Taylor 展开:
       log|W_R(e^jω)| ≈ log(N) - (N²-1)·ω²/24
   这是 ω² 的一阶展开，就是抛物线
   -> 所以主瓣附近三个相邻 bin 在 dB 域共线于抛物线，顶点即真实峰

3. 为什么只适用于 rectangular window（不是其它曲线也不是其它 window）：
   其它 window（Hann/Blackman）的主瓣形状变了，log 域不再是抛物线
   本库 _estimate_frequency_fft 对原始数据做 FFT（不加分析窗）
   -> 用 rectangular 主瓣的抛物线性质是数学匹配，不是任意选择

4. 本库实现是简化版，不是标准三点抛物线：
   标准版（三点 log-domain）: δ = 0.5·(α-γ)/(α-2β+γ)，精度 ~0.01-0.1 bin
   本库版（两点线性）:        δ = r·spec[k+r]/(spec[k]+spec[k+r])，精度 ~0.1-0.3 bin
   差别：标准版用 dB 域三个点，本库版用线性域两个点
   合理性：parabolic 只是初始估计，后续 Taylor 迭代修正初始误差

5. 精度的主要影响因素：
   - N 越大，绝对精度（Hz）越好（bin 宽 = Fs/N）
   - SNR > 20-30 dB 才可靠；SNR 低时 noise 扰动 spec[k±1] 相对大小，可能给错方向
   - 和信号幅度理想情况无关（主瓣形状只取决于频率）

6. parabolic 是 Taylor 迭代收敛的必要前置（不是可选优化）：
   Taylor 展开要求 Δf << 1/(2πN)
   FFT 直接找 bin 的精度是 1/N，对 N=8192 是 1.2e-4，不满足条件
   parabolic 把精度提到 ~0.1/N = 1.2e-5，刚好满足
   -> 没有这步，Taylor 迭代会发散

7. 详细推导见 stage_03 § 3.6
```

#### 3.2 迭代优化：把频率误差当做线性参数处理（sin(δf) ≈ δf）

一阶 Taylor 展开，近似条件是 `2π·Δf·n` 在整个 n ∈ [0, N) 范围内都很小，即
`Δf << 1/(2πN)`。这正是 § 3.1 parabolic 插值的必要性来源——必须先把初始估计
精度提到 ~0.1/N，Taylor 迭代才能收敛：

```text
cos(2π(f_i + Δf)n) ≈ cos(2πf_i·n) - 2π·Δf·n·sin(2πf_i·n)
sin(2π(f_i + Δf)n) ≈ sin(2πf_i·n) + 2π·Δf·n·cos(2πf_i·n)
```

代入 `ideal_sine = A·cos + B·sin + C` 并整理，只保留 Δf 的一阶项：

```text
ideal_sine(n; A, B, C, Δf)
≈ A·cos(2πf_i·n) + B·sin(2πf_i·n) + C
  + Δf·2π·n·[-A·sin(2πf_i·n) + B·cos(2πf_i·n)]
```

最后一项的 `[-A·sin + B·cos]` 用上一次迭代的 A、B 代入，就是一个已知的向量。所以
`(A, B, C, Δf)` 又变回了**线性参数**，可以套最小二乘：

```text
X = [cos(2πf_i·n), sin(2πf_i·n), 1, 2π·n·(-A_old·sin + B_old·cos)]
β = [A, B, C, Δf]ᵀ
更新频率：
f_{i+1} = f_i + Δf
```
如果`Δf`很小，说明已经收敛。

questions：`Δf`的tolerance如何设置？如果`Δf`不小，说明还需要迭代，如何判断收敛？

##### answer - key points:

```text
1. tolerance 是什么：
   迭代终止的阈值。每次迭代算出频率修正量 Δf，
   如果 |Δf| < tolerance，认为已经收敛，停止迭代
   代码默认 tolerance = 1e-9（normalized frequency，cycle/sample）

2. tolerance = 1e-9 的物理含义：
   换算绝对频率 = tolerance × Fs
   对 Fs=100MHz: 0.1 Hz，对几乎所有 ADC 测试都够
   注意是 |Δf| 绝对值，不是相对值
   对低频信号宽松，对接近 Nyquist 的信号严苛

3. 收敛判据（满足任一即停止）：
   a) |Δf| < tolerance → 成功收敛
   b) 达到 max_iterations → 触发 RuntimeWarning "did not converge"

4. 没收敛的常见原因（按发生频率排序）：
   - max_iterations 太小（默认=1，non-coherent 或高噪声需要 3-5）
   - 信号不是单音（有强 harmonic 或多主频 → 用 fit_sine_harmonics）
   - 数据太短（N 小 → FFT 分辨率粗 → 初始估计偏差大）

5. max_iterations 选择建议：
   1   → coherent + SNR > 40dB + N ≥ 1024（默认，仿真/理想数据）
   3-5 → non-coherent + SNR 20-40dB（真实芯片测量）
   10+ → 极低 SNR + 精密校准（IEEE 1057 标准测试）

6. 判断迭代是否健康的办法：
   看 delta_freq 序列应该指数下降（1e-3 → 1e-5 → 1e-7 → 1e-9）
   震荡或下降慢 → 需要更多迭代或换方法

7. 详细推导见 stage_03 § 3.7
```

## 4.PDF：误差的幅度分布（probability density function）

**核心思路**：不同的类型的error在幅度分布上有不同的特征，分析PDF可以帮助我们区分噪声、失真、memory effect等问题。

**thermal noise → Gaussian**

thermal noise 是大量独立随机事件叠加的结果（电阻里电子的热运动）。中心极限定理
保证：大量独立同分布随机变量之和趋向高斯分布。所以 thermal noise 的幅度分布：

```text
p(e) = (1/(σ·√(2π))) · exp(-e²/(2σ²))
```

**quantization noise → 近似 Uniform**

Stage 01 已经推导过：如果输入足够丰富、不超量程、量化误差和输入不相关，量化误差
近似均匀分布：

```text
e ~ Uniform(-LSB/2, +LSB/2)
p(e) = 1/LSB,  -LSB/2 ≤ e ≤ +LSB/2
```

**harmonic distortion → 有结构的 PDF**

如果 error 含有 `cos(2π·k·f·n)` 成分（k 次谐波），error 的瞬时值会在谐波波峰
附近停留更久，PDF 会呈现**双峰**或**马鞍形**。阶数越高、幅度越大，结构越明显。

**glitch / burst noise → heavy tail**

偶发的大幅误差（比如 0.1% 概率出现 10σ 的尖峰）会让 PDF 出现长尾。高斯分布的
4σ 概率是 0.006%，如果实测 4σ 以上的样本明显多，基本就是 glitch。

### 4.2 KDE：从离散样本估计连续PDF

error 是一堆离散样本 `e[0], e[1], ..., e[N-1]`。要估连续 PDF，最简单的是直方图，
但直方图对 bin 宽度敏感、不光滑。`analyze_error_pdf` 用 **KDE（kernel density
estimation，核密度估计）**：

```text
对每个样本 e[i]，以它为中心放一个宽度 h 的高斯核
把所有 N 个高斯核叠加，再除以 N
得到连续的 PDF 估计

利用 silverman 规则选择 bandwidth h：
h = 1.06 * σ * N^(-1/5)
```

questions：上面只是讲了不同噪声的分布特征，从真正的噪声数据e[n]中如何算出PDF？给出详细推导过程。

questions：高斯核的定义是什么？为什么选择高斯核？

### 4.3 KL divergence（KL散度）：分析PDF与高斯分布的差异

```text
KL(p || q) = Σ p(x) · log(p(x) / q(x)) · dx
```

其中 `p` 是实测 PDF（KDE 估计），`q` 是同均值/同方差的高斯分布。直观含义：

```text
KL = 0       p 和 q 完全相同
KL 小        p 接近高斯，random noise 主导
KL 大        p 明显偏离高斯，有 deterministic 结构或 heavy tail
```
--> error 单位比较统一为LSB，lsb = full_scare / 2**resolution_bits。err_lsb = err / lsb。这样不同分辨率的 ADC 测试结果可以直接比较。

### 4.4 PDF 看图判据

| error PDF 形状 | 可能含义 | 对应 KL |
|---|---|---|
| Gaussian（零均值、对称、单峰）| thermal noise 主导 | 小 |
| Uniform（平顶、有界）| 理想量化噪声主导 | 中等 |
| 双峰 / 马鞍形 | 含低阶 harmonic | 大 |
| Heavy tail（4σ 以上异常多）| glitch / burst noise | 大 |
| 不对称（skewed）| offset / 奇偶不对称 | 中等 |
| Multi-modal（多峰）| code missing / deterministic | 大 |

--> 用看图是不靠谱的，这时需要使用ACF（autocorrelation function）来判断误差杨门间有没有Memory

## 5. ACF的数学定义

```text
R[k] = E[e[n] · e[n+k]]
```

直觉：把 error 序列平移 k 个样本，和平移前的逐点相乘，再取平均。

- 如果 e[n] 和 e[n+k] 独立，乘积的期望是 0
- 如果 e[n] 和 e[n+k] 倾向同号（正相关），R[k] > 0
- 如果倾向反号（负相关），R[k] < 0

### 5.1 ACF 看图判据

| ACF 形状 | 可能含义 |
|---|---|
| R[0]=1, 其它 lag 全 ≈ 0 | 白噪声主导（理想）|
| 小 lag 上明显 > 0，指数衰减 | memory effect（settling / reference droop）|
| 某个固定 lag 周期出现峰 | 周期性干扰（clock feedthrough / 电源耦合）|
| 负值明显（R[k]<0）| 交替结构（比如奇偶不对称、over-correction）|
| 噪声水平高、看不出结构 | 数据太短或随机噪声过大，需要更多样本 |

6. error spectrum

读完 § 5 ACF 再读这一节，自然会问：ACF 已经衡量了"时间结构"，error spectrum 又
衡量"频率结构"，**两者是不是重合？** 答案是：数学上对偶，工程上互补，不可互相
替代。这个关系背后的核心是 **Wiener-Khinchin 定理**。

对零均值广义平稳随机过程 `e[n]`，Wiener-Khinchin 定理：

```text
S_e(ω) = Σ_k R[k] · exp(-jωk)              (ACF 的 DTFT = 功率谱)
R[k]   = (1/2π) ∫ S_e(ω) · exp(jωk) dω     (功率谱的逆 DTFT = ACF)

其中:
    R[k]   = 自相关函数（§ 5）
    S_e(ω) = 功率谱密度（PSD）
```

**分工 1：ACF 看时间结构，spectrum 看频率结构**

```text
要回答的问题              ACF 更直接        spectrum 更直接
----------------------------------------------------------
相邻样本有没有 memory?      ✓ (小 lag)         ✗
memory 的衰减时间常数?     ✓ (指数衰减)       ✗
有没有固定频率干扰?         △ (周期峰)         ✓ (尖峰)
干扰的精确频率?            ✗ (要算)           ✓ (直接读)
多个 spur 各自频率?        ✗                  ✓
低频 drift / 1/f?          △ (长 lag)         ✓
```

### 6.1 error spectrum 看什么

```text
平坦的 noise floor
    -> error 是宽带随机噪声（thermal / quantization）
    -> 对应 PDF Gaussian、ACF white

固定频率尖峰（spur）
    -> error 含有确定性周期成分
    -> 可能是 harmonic（2f, 3f, ...）
    -> 可能是外部干扰（电源、时钟、数字耦合）
    -> 频率位置是关键诊断线索

谐波系列（fundamental 整数倍）
    -> nonlinearity（CDAC mismatch / settling / clipping）
    -> 在 error spectrum 里看，因为 fundamental 已减掉

低频抬升
    -> drift / slow memory effect
    -> 1/f noise（如果 ADC 或前端有贡献）

"裙边"（fundamental 频率附近抬起）
    -> jitter 主导（Stage 02 jitter 节推导过这个形状）
    -> 或 fit_sine_4param 频率估计略有偏差
```

## 8. 电路问题分类与诊断流程（实验 2 的 15 case 按 4 类归纳）

按物理机制分 4 类，每类的 residual 特征有共性。详细推导见 stage_03 § "电路需要理解什么"。

### 8.1 四类分类表

```text
类别           case                          KL       sigma     最敏感工具
--------------------------------------------------------------------
1 随机噪声     Thermal Noise                  0.0002   0.75      PDF（基准）
（不可校准）   Quantization                   0.12     1.17      PDF（平顶）
               Jitter                         0.05     1.77      spectrum 裙边

2 静态非线性   Static HD2 (-80dBc)            0.13     0.15      spectrum / by_value
（可校准）     Static HD3 (-70dBc)            0.26     0.46      spectrum / by_value
               Clipping                       0.72     0.11      PDF（边缘堆积）

3 动态/记忆    Memory Effect                  0.03     0.71      ACF（小 lag 相关）
（和前状态相关）Incomplete Settling            0.04     0.09      ACF / by_value
               Reference Error                0.23     0.68      ACF / by_value

4 调制/干扰    AM Noise                       0.05     0.72      by_phase
（乘性或周期） AM Tone (5%)                   0.06     48.8      spectrum spur
               RA Gain Error                  0.09     4.76      by_value（斜坡）
               RA Dynamic Gain                0.08     14.1      spectrum / by_value
               Drift                          0.21     9.87      时域图（包络）
               Glitch                         1.69     17.1      PDF（长尾）
```

### 8.2 每类的核心机制和特征

```text
类别 1 随机噪声（加性随机，stochastic）
  机制: thermal=CLT求和→Gaussian；quant=舍入几何→Uniform；jitter=斜率×δt→近Gaussian
  共性: PDF 是基准/可识别形状，ACF 白噪声，spectrum 平坦
  盲点: jitter 在 PDF 看不出，要 spectrum 裙边或扫频率

类别 2 静态非线性（deterministic，e=f(vin)）
  机制: 多项式 y=x+k2x²+k3x³ → 产生 HD2/HD3；饱和 → clipping
  共性: spectrum 有 harmonic spur，PDF 有结构（双峰/边缘堆积）
  特征: sigma 小但 KL 可能大（弱 harmonic、clipping）
        HD3 KL > HD2（奇阶在 fundamental 有分量，扰动更强）
        clipping 产生奇阶谐波系列（方波化）

类别 3 动态/记忆（e=f(vin, history)，相邻样本相关）
  机制: 电容残留(memory)、RC充不满(settling)、ref droop累积(reference)
  共性: PDF 近 Gaussian（KL 小）→ PDF 盲点
        ACF 小 lag 上 R[k] > 0，指数衰减 ← 招牌特征
       settling sigma 最小但 ACF 有结构，单看 sigma 会漏诊

类别 4 调制/干扰（乘性或外部周期）
  机制: AM=m(t)·sin(ωt)；RA gain error=(G-1)·x_lsb；drift=非平稳；glitch=瞬态
  共性: fit+PDF 双盲点（AM 边带被 fit 吸收，sigma 大但 PDF 正常）
        spectrum 看 AM Tone spur / drift 低频 / glitch 全频段
        by_value 看 RA gain error 斜坡
        by_phase 看 AM 失真
        glitch 是 PDF 招牌（KL=1.69 最大，长尾极敏感）
```

### 8.3 综合诊断流程（4 步决策树）

```text
第 1 步: 看 PDF 的 KL
  KL < 0.01   → 随机噪声主导（类别 1）
                 看 spectrum 区分 thermal/jitter/quant
  KL 0.01-0.1 → 弱结构（memory/AM/RA）
                 PDF 盲点，必须看 ACF/by_value/by_phase
  KL > 0.1    → 明显非高斯
                 看 PDF 形状: 双峰=harmonic, 长尾=glitch, 边缘=clipping

第 2 步: 看 ACF
  白噪声 (R[k≠0]≈0) → 确认随机噪声
  小 lag 相关       → memory/settling/reference（类别 3）
  周期峰           → harmonic 或 AM Tone

第 3 步: 看 error spectrum
  平坦             → 随机噪声
  fundamental 裙边 → jitter
  整数倍 spur      → harmonic
  非 harmonic spur → AM Tone / 外部干扰
  低频抬升         → drift / memory
  全频段抬升       → glitch（瞬态）

第 4 步: 看 by_value / by_phase（fit 盲点的补救）
  by_value 斜坡    → RA gain error / settling
  by_phase 结构    → AM / PM 失真
```

### 8.4 核心规律

```text
sigma 大 ≠ PDF 异常
  AM Tone sigma=48.8 但 KL=0.065（瞬时分布在大量样本平均后接近 Gaussian）

sigma 小 ≠ PDF 正常
  Clipping sigma=0.11 但 KL=0.72（只影响边缘样本但形状严重偏离）

KL 是"PDF 偏离 Gaussian"的客观指标，和 sigma 独立
  对 heavy tail（glitch）极敏感: KL=1.69
  对边缘堆积（clipping）敏感: KL=0.72
  对弱 harmonic（HD2 -80dBc）敏感: KL=0.13（比 thermal 大 650 倍）

没有任何单一工具能诊断所有问题
  PDF 强于:    heavy tail / 边缘堆积 / 明显 harmonic
  ACF 强于:    memory / settling / 短程相关
  spectrum 强于: 频率定位 (spur / jitter裙边 / AM边带)
  by_value/by_phase 强于: AM/PM / 幅度相关失真
  → 三件套 + by_value/by_phase = 完整诊断工具链
```

## 9. DSP 概念：因果性 / lfilter vs filtfilt

详细推导见 stage_03 § 4.2.5。

### 9.1 因果性定义

```text
因果系统:   y[n] 只依赖 x[n], x[n-1], ...（现在和过去）
非因果系统: y[n] 还依赖 x[n+1], ...（未来）

物理世界必然因果（时间单向）
非因果只在离线处理可能（整个信号已采集完，可访问"未来"）
```

### 9.2 lfilter vs filtfilt

```text
                    lfilter (因果)           filtfilt (非因果)
-----------------------------------------------------------------
依赖未来?           否                       是
能实时?             能                       不能（必须全部数据）
相位延迟?           有（相位失真）           无（零相位）
滤波效果            幅度滤波一次             幅度滤波两次（更陡）
适用场景            实时处理、硬件实现        离线数据分析、信号生成
```

### 9.3 filtfilt 的原理：相位抵消（非因果是代价不是目的）

```text
步骤 1: 正向 lfilter  -> 引入相位 +φ(f)
步骤 2: 时间反转
步骤 3: 反向 lfilter  -> 在反转轴上加 +φ(f)，换算回原轴是 -φ(f)
步骤 4: 再反转回来
总相位: +φ(f) + (-φ(f)) = 0  -> 零相位

为什么必然非因果:
  反向滤波处理时间反转序列
  -> 原始信号的"未来"变成反转序列的"过去"
  -> 输出依赖了原始信号的未来样本
  -> 非因果

最小例子: x=[1,2,3], 滤波器 y[n]=x[n]+x[n-1]
  filtfilt 后 drift[0] = 2·x[0] + x[1]
  -> n=0 的输出依赖了 x[1]（n=1 的"未来"）→ 非因果
```

### 9.4 在 drift 代码里的体现

```text
apply_drift 用 filtfilt（非因果）而不是 lfilter（因果）

动机: 让 drift 零相位，和 signal 时域对齐干净
代价: drift 非因果（依赖游走的未来），违反真实 drift 的物理

对实验的影响:
  - ACF≈1 是 butter 截止低（drift 变化慢）导致的，不是 filtfilt 导致的
  - drift 变化极慢（τ≈320 samples），非因果的"提前响应"几乎看不出来
  - 对教学够用；严格物理仿真应该改 lfilter（但会有相位延迟）

经验法则:
  实时（边来边处理）   -> 必须 lfilter
  离线（数据已采集完） -> 可以 filtfilt 享受零相位
```

### 9.5 DSP 全景串讲（一张图）

```text
DSP 处理对象: 离散信号 x[n]

三大分析工具:
  时域:   y[n] vs n           -> fit, residual, drift 包络
  频域:   X(k) vs f           -> FFT, spectrum, harmonic
  统计域: PDF/ACF              -> analyze_error_pdf/autocorr

两大操作:
  分析: 从信号提取信息（不改信号）-> FFT, ACF, fit
  滤波: 改造信号                -> lfilter, filtfilt, window

系统性质:
  线性 + 时不变 + 因果 -> 本库所有滤波器都满足前两个
  因果性是物理约束（实时必须因果，离线可以非因果）
```

## 5. stage_04 sar_modeling

### 1. SAR ADC （successive approximation register ADC）的基本数学原理
**核心思想**：逐次逼近

SAR ADC 想用一组二进制权重近似输入：

```text
vin ≈ b0·w0 + b1·w1 + ... + b(N-1)·w(N-1)

其中 bi ∈ {0, 1}
理想权重: w = [1/2, 1/4, 1/8, ..., 1/2^N]
```

逐次逼近过程（贪心搜索）：

```text
v_dac = 0
for each bit j (从 MSB 到 LSB):
    v_test = v_dac + w[j]
    if vin >= v_test:
        bit[j] = 1
        v_dac = v_test          ← 接受这一位
    else:
        bit[j] = 0
              ← 拒绝，v_dac 不变
```

### 2. 权重向量生成

本库的理想权重生成方式：

```text
raw = [2^(N-1), ..., 2, 1]          例如 4-bit: [8, 4, 2, 1]
weights = raw / (sum(raw) + raw[-1])          = [8,4,2,1] / 16
```

注意分母是 `sum(raw) + 1 LSB`，不是 `sum(raw)`。对 4-bit，是 `/16` 不是 `/15`。
这个 +1 LSB 的来源经常让人困惑，但它有严格的几何意义。

```text
N=4, 16 个 code:
  code 0:  重建电平 0/16 = 0.0000
  code 1:  重建电平 1/16 = 0.0625
  code 2:  重建电平 2/16 = 0.1250
  ...
  code 15: 重建电平 15/16 = 0.9375
```

注意**最高的 code (15) 对应 15/16，不是 1.0**。这是"lower-edge reconstruction"
（Stage 01 讲过）——每个 code 用区间的下界重建。

### 2.3 redundancy （冗余）



## 3. mismatch —— sigma ∝ 1/sqrt(C)

**核心思想**：建立相对失配模型，再乘标准高斯分布
实际电容不是理想值：

```text
w_actual = w_nominal · (1 + error)
```

本库 `sar_apply_cap_mismatch` 是 **unit-cap-scaled independent weight-error model**：
用单位电容统计推导每个 bit 的相对失配标准差，再把这个失配独立乘到每个 bit weight 上。
它抓住 `sigma ∝ 1/√C` 趋势，但不模拟完整 CDAC 的共享总电容分母、dummy cap、bridge/parasitic
造成的相关性。

### 3.1 unit-cap 模型

假设 bit j 由 `n[j]` 个单位电容 Cu 并联组成。理想容值 `C[j] = n[j]·Cu`。

每个单位电容的容值是随机变量：

```text
Cu_i = Cu_ideal · (1 + ε_i)
ε_i ~ N(0, σ_C²)    独立同分布，σ_C 是单位电容的相对失配
```

bit j 的总容值：

```text
C[j] = Σ_{i=1}^{n[j]} Cu_i = Cu_ideal · Σ_{i=1}^{n[j]} (1 + ε_i)
     = n[j]·Cu_ideal · (1 + (1/n[j])·Σ ε_i)
     = C[j]_ideal · (1 + ε̄[j])
```

其中 `ε̄[j] = (1/n[j])·Σ ε_i` 是 n[j] 个独立失配的平均。

### 3.2 sigma ∝ 1/√C 的推导

`ε̄[j]` 是 n[j] 个独立同分布 N(0, σ_C²) 随机变量的平均。由独立随机变量和的方差性质：

```text
Var(ε̄[j]) = Var((1/n[j])·Σ ε_i)
          = (1/n[j]²)·Σ Var(ε_i)         （独立性让方差直接相加）
          = (1/n[j]²)·n[j]·σ_C²
          = σ_C² / n[j]

所以:  std(ε̄[j]) = σ_C / √n[j]
```

**这就是 `sigma_relative ∝ 1/√n[j]` 的来源**——n[j] 个独立失配平均后，相对误差
的标准差按 `1/√n[j]` 衰减。

因为 `C[j] = n[j]·Cu`，所以 `n[j] = C[j]/Cu`，代入：

```text
std(ε̄[j]) = σ_C / √(C[j]/Cu) = σ_C·√(Cu/C[j])
           ∝ 1/√C[j]
```

**物理含义**：
```text
MSB (n 大, C 大):  相对失配小  -> 权重更准
LSB (n 小, C 小):  相对失配大  -> 权重更不准
```

这就是为什么 MSB 的权重通常比 LSB 准——不是因为 MSB 做得更精细，而是因为它由更多
单位电容并联，统计平均让随机偏差按 `1/√n` 衰减。这是集成电路里"用面积换精度"
的基本 tradeoff。

### 3.3 对应到 sar_apply_cap_mismatch 代码

`sar.py` 第 140-157 行：

```python
if cap_units is None:
    cap_units = weights / np.min(weights)          # 从权重推断单位电容数
                                                    # 例如 [8,4,2,1]/16 -> cap_units=[8,4,2,1]
relative_sigma = sigma / np.sqrt(cap_units)         # 每个 bit 的相对失配 std
return weights * (1.0 + relative_sigma * rng.standard_normal(len(weights)))
```

逐行：
- `cap_units = weights / min(weights)`：把权重除以最小权重，得到每个 bit 的"单位电容
  数"。对 `[8,4,2,1]/16`，`cap_units = [8,4,2,1]`——MSB 是 8 个 Cu，LSB 是 1 个 Cu。
- `relative_sigma = sigma / √cap_units`：精确对应 § 3.2 的 `σ_C/√n[j]`。
  MSB 的 relative_sigma = `σ/√8`，LSB 的 = `σ/√1 = σ`。
- `weights * (1 + relative_sigma·N(0,1))`：每个权重独立加一个高斯扰动，
  std 就是上面的 relative_sigma。

### 3.4 mismatch 全流程：nominal vs actual 对比（详细见 stage_04 § 3.4/3.5）

```text
核心问题: mismatch 怎么从权重偏差变成 aout 失真?
答: 不是"权重偏了"本身，而是权重偏移让 comparator 在 code 边界附近
    做出不同决策 (bit 翻转)，进而产生周期性失真。
```

##### 全流程链（5 步）

```text
1. 电容制造偏差 (物理)
   -> 每个 unit cap Cu 容值偏离设计值 (芯片固定, deterministic)

2. sar_apply_cap_mismatch (代码建模)
   -> actual[j] = nominal[j]·(1 + ε[j]), ε[j] ~ N(0, (σ/√n[j])²)
   -> 注意: 不重新归一化! sum(actual) ≠ sum(nominal)
   -> 产生增益误差 (线性, 全局缩放, 通常 < 1%)

3. sar_convert (转换, 模拟域)
   -> 用 actual 权重做贪心搜索
   -> trial 阈值 = v_dac + actual[j], 偏离 ideal 阈值 (v_dac + nominal[j])
   -> 当 vin 接近阈值时, bit 决策可能翻转
   -> 这是失真的核心来源 (非线性)

4. sar_reconstruct (重构, 数字域)
   -> aout = codes @ digital_weights (nominal 或 calibrated)

5. 失真 = aout_uncal - aout_ideal
   两种成分:
   (a) 增益误差: sum(actual) ≠ sum(nominal) 导致的全局缩放 (线性)
   (b) bit 翻转: 阈值偏移导致的决策错误 (非线性, 产生 harmonic)
   -> 主要矛盾是 (b)，因为 ADC 测试关心 SFDR/THD
```

##### bit 翻转的数值演示（vin=0.5, MSB 翻转）

```text
nominal = [0.5,    0.25,   0.125,  0.0625]
actual  = [0.5027, 0.2435, 0.1283, 0.0654]   (sigma=0.05, seed=42)

ideal 路径 (nominal):
  bit0: v_test=0.5,    vin=0.5 >= 0.5    -> bit0=1, v_dac=0.5
  后续 bit1-3 都不取 -> codes=[1,0,0,0], aout=0.5

actual 路径 (actual):
  bit0: v_test=0.5027, vin=0.5 < 0.5027  -> bit0=0  ★ MSB 翻转!
  bit1: v_test=0.2435, vin >= 0.2435     -> bit1=1, v_dac=0.2435
  bit2: v_test=0.3718, vin >= 0.3718     -> bit2=1, v_dac=0.3718
  bit3: v_test=0.4372, vin >= 0.4372     -> bit3=1, v_dac=0.4372
  codes=[0,1,1,1], aout(用nominal重构)=0.4375

误差 = -0.0625 = -1 LSB

关键: MSB 翻转了，但后续 bit 仍会在错误起点上继续做 lower-edge 搜索，
      最终只差 1 LSB。这不是严格意义的 redundancy；普通二进制没有
      正的 overrange margin，不能把早期错判完全修回来。
```

##### 扫描所有 code 的 error 规律

```text
error 要么是 0 (没翻转)，要么是 ±1 LSB (翻转)
不是每个 code 都翻转，只在 actual 阈值和 ideal 错位的 code 翻
翻转概率约 5-15% (取决于 sigma)

翻转是"块状"分布:
  code 1-3 翻, 4-7 不翻, 8-11 翻, 12-14 不翻
  -> 因为 bit0 阈值偏 +0.0027, 让 vin ∈ [0.5, 0.5027] 时 MSB 翻转
  -> 这个小区间影响整个 code 8-11 的决策路径

transfer curve 表现为"局部压缩":
  翻转的 code 段输出被压低, 多个 code 映射到相近 aout
  -> DNL/INL 异常 (某些 code 宽, 某些窄)
```

##### 为什么产生 harmonic（连接 Stage 03）

```text
error 是 vin 的分段常数函数: error = g(vin), 每 code 一个固定值
输入是正弦: vin(t) = A·sin(2πft)
复合: e(t) = g(A·sin(2πft))

vin(t) 每周期扫过 [0,A] 一次 -> 每周期经过每个 code 边界一次
-> e(t) 每周期重复同样的"翻转 pattern"
-> e(t) 是周期信号 (周期 = 1/f)
-> 任何周期信号可展开为 Fourier 级数 -> 含 fundamental 整数倍 = harmonic

所以 SAR mismatch 在频谱上表现为 HD2/HD3/.../
虽然 g(vin) 是分段常数 (不是连续 cos), 但周期性保证有 harmonic

harmonic 阶数和 mismatch 分布有关:
  对称 mismatch (bit 同向偏)  -> 主要偶阶 (HD2, HD4)
  非对称 (某些 bit 偏多偏少)  -> 含奇阶 (HD3, HD5)
  随机 mismatch (实际 chip)   -> 同时有各阶
```

##### 和 Stage 03 多项式失真的对比

```text
Stage 03 的 HD2/HD3 case:  y = x + k2·x² + k3·x³  (连续多项式)
SAR mismatch 失真:          error = g(vin) 分段常数

两者频谱表现类似 (都产生 harmonic spur)，因为都是周期性的
区别: 多项式失真的 harmonic 是单一干净 spur
      SAR mismatch 的 harmonic 可能更"脏" (g 不是平滑函数)

诊断工具通用:
  spectrum 看 harmonic -> 怀疑 deterministic 非线性 (Stage 03 § 5)
  by_value 看 g(vin) 的阶梯形状 -> 定位是哪个 bit 有问题
```

### 4. 两套权重—— nominal vs actual 的误差传递

#### 4.1 两套权重的数据流

```text
转换时（模拟域）:
  bits = sar_convert(vin, actual_weights)
  -> comparator 用 actual_weights 决策
  -> bits 是"在失真权重下做出的决策"

重构时（数字域）:
  aout = sar_reconstruct(bits, digital_weights)
  -> aout = bits · digital_weights
```

三种典型情况：

```text
1. 理想 ADC:
   actual_weights = nominal_weights
   digital_weights = nominal_weights
   -> aout = 理想量化输出，无失真

2. 未校准 ADC:
   actual_weights = nominal · (1 + mismatch)     ← 含失真
   digital_weights = nominal                      ← 数字端不知道失真
   -> aout 含 mismatch 引起的失真

3. 校准后:
   actual_weights = nominal · (1 + mismatch)     ← 失真还在（物理没变）
   digital_weights ≈ actual                       ← 数字端用同尺度权重重构
   -> aout 失真被补偿
```

注意：`calibrate_weight_sine()["weight"]` 的绝对尺度由正弦拟合归一化决定，在单端 SAR
例子中可能只和 actual weights 成比例；若要放进 `sar_reconstruct`，需要先确认或重缩放。

#### 4.2 误差传递：mismatch 怎么变成 aout 误差

设 `actual[j] = nominal[j]·(1 + ε[j])`。转换时用 actual 决策得到的 bits，
然后用 nominal 重构：

```text
aout_uncalibrated = Σ bits[j] · nominal[j]
aout_ideal      = Σ bits_ideal[j] · nominal[j]    （理想 bits）

误差:  e = aout_uncalibrated - aout_ideal
         = Σ (bits[j] - bits_ideal[j]) · nominal[j]
```

关键：bits 和 bits_ideal 在哪里不同？**当 mismatch 让某个 bit 的 trial 阈值偏移，
可能让 comparator 在边界附近做出不同决策**。

#### 4.3 数字校准与校准的极限

校准的目标是让 `digital_weights` 和 actual analog weights 在同一重构尺度上一致。
如果完全相等：

```text
aout = Σ bits[j] · digital_weights[j]
     = Σ bits[j] · actual[j]
     = sar_convert 内部的 v_dac_final    （因为转换时就是用 actual 累积的）

校准的局限：随机噪声修不了

以上校准讨论的是 deterministic mismatch（每次转换相同）。但 SAR 还有两种随机噪声：

```text
comparator noise: 每次 trial 的比较器噪声，让 bit 决策随机翻转
sampling noise:   采样时的 kT/C 噪声，进入 vin_sampled
```

这两种噪声是 stochastic——每次转换不同，不能用 digital_weights 补偿（因为
digital_weights 是固定的，而噪声是随机的）。所以：

```text
校准能修:  capacitor mismatch（deterministic）
校准不能修: comparator noise + sampling noise（stochastic）
```

## 5.5 电路部分

### 1. SAR ADC 电路块——整体架构

**电路图像**：典型 SAR ADC 包含五个块：

```text
               vin
                │
                ▼
        ┌───────────────┐
        │ sample-and-hold│  采样开关 + 保持电容
        └───────┬───────┘
                │ vin_sampled
                ▼
        ┌───────────────┐    v_dac（CDAC 输出）
        │   comparator  │◀──────────┐
        └───────┬───────┘           │
                │ bit decision      │
                ▼                   │
        ┌───────────────┐           │
        │  SAR logic    │───────────┤ 切换 CDAC 的 bit
        │  （逐次控制） │           │
        └───────┬───────┘           │
                │ final bits        │
                │                   │
        ┌───────▼───────┐           │
        │ reference     │───────────┘ Vref 供电给 CDAC
        │   driver      │
        └───────────────┘
```

### 2. comparator 基本结构 & comparator noise

详细推导见 stage_04 § 3.1/3.2。

##### comparator 的两阶段结构（preamp + latch）

```text
现代高速 comparator = preamp + latch:

  vin_sampled ──┐
                ├─ preamp (G≈5-20) ── latch (正反馈再生) ── digital out
  v_dac ────────┘

preamp: 线性放大 (vin - v_dac)，增益 G
        -> 把 latch 的等效输入噪声/offset 压低到 σ_latch/G
        -> input-referred noise = σ_latch / G
        -> 这就是代码 comparator_noise_rms 的物理含义

latch:  两个反相器交叉连接（正反馈）
        任何微小输入差被指数放大到 rail-to-rail
        -> 锁存瞬间承受的噪声被"冻结"
        -> comparator noise 的来源
```

##### 为什么需要两阶段（tradeoff）

```text
只有 latch:      offset/噪声直接决定决策，精度差（几 mV）
preamp + latch:  preamp 降噪（等效 σ_cmp = σ_latch/G），但 preamp 慢
G 大 -> 噪声小但建立慢（转换速度下降）
G 小 -> 噪声大但快
典型 G ≈ 5-20，SAR 设计的核心 tradeoff
```

##### comparator noise 的特殊性（和 thermal noise 不同）

```text
thermal noise (加性):    aout = ideal + w        直接加，线性
comparator noise (决策): bit 可能翻转 -> aout 偏离 ±weights[j]
                                                ↑ 整个 bit 权重
                         远大于 σ_cmp 本身

一个错误决策让 aout 偏差 ±weights[j]，非线性行为
这是 SAR 区别于其它架构的关键
```

##### residual 特征

```text
PDF:    近 Gaussian（KL 小）—— 随机噪声
ACF:    近白噪声（每次 trial 独立抽取）
spectrum: 抬高 noise floor -> SNR/ENOB 下降（不影响 SFDR）
诊断:   SNR 差但 SFDR 正常 + PDF Gaussian -> comparator/sampling noise 主导
校准:   不能完全消除（stochastic），靠 averaging/redundancy/降低噪声设计
```

### 3. sample-and-hold 基本结构 & sampling noise

详细推导见 stage_04 § 4.1/4.2。

##### S/H 的开关电容结构

```text
S/H = 开关 + 采样电容 Cs:

  vin ──[switch R_on]──●── output (vin_sampled)
                       │
                      ─┴─ Cs
                       │
                      GND

工作时序（两相位）:
  φ1 闭合 (track/采样):  Cs 通过 R_on 充电到 vin，持续 T_track
  φ1 断开 (hold/保持):   Cs 冻结电压，后续 bit trials 用这个电压
```

##### 两个关键参数（核心 tradeoff）

```text
1. 采样时间 T_track:
   Cs 充电是 RC: v_Cs(t) = vin·(1 - exp(-t/(R_on·Cs)))
   建立 0.5 LSB 精度需要: T_track > (N+1)·ln2·R_on·Cs ≈ 0.69·(N+1)·R_on·Cs
   12-bit: T_track > 9·R_on·Cs
   -> T_track 不够 = incomplete settling（Stage 03 实验 2 用过）
   -> error 和输入幅度相关（产生 HD3）

2. 采样电容 Cs:
   Cs 大 -> kT/C 噪声小，但建立慢 + 驱动难 + 面积大
   Cs 小 -> 噪声大，但快 + 易驱动 + 面积小
   -> SAR 核心设计 tradeoff: 噪声 vs 速度/功耗/面积
```

##### kT/C 噪声推导

```text
RC 低通的等效噪声带宽 = 1/(4RC)
电阻热噪声 PSD = 4kTR
积分: v_noise² = 4kTR · 1/(4RC) = kT/C
        v_noise_rms = √(kT/C)

关键: kT/C 只取决于 T 和 C，和 R 无关！
  R 大 -> 噪声 PSD 大，但带宽小，正好抵消
  -> 这是采样电路的基本极限

设计含义（12-bit, full-scale=1V）:
  理想量化噪声 LSB/√12 ≈ 70 µV
  要 sampling noise < 量化噪声: √(kT/C) < 70µV
  -> C > kT/(70µV)² ≈ 0.8 pF
  所以 12-bit SAR 的 Cs 至少 ~1 pF
```

##### 其它 S/H 非理想（代码不模拟）

```text
charge injection:    开关断开瞬间沟道电荷注入 Cs -> offset
clock feedthrough:   时钟边沿通过寄生电容耦合 -> offset
两者是 deterministic，可校准，代码归入 offset 不单独模拟

代码把 S/H 拆成两个函数:
  sar_convert 的 sampling_noise_rms  -> kT/C（随机）
  apply_incomplete_sampling          -> 建立不足（deterministic）
符合 Stage 03 "一种非理想一个 case"设计
```

##### residual 特征（和 thermal noise 一样）

```text
PDF:    完美 Gaussian（KL≈0）—— 纯加性高斯
ACF:    白噪声 δ[k]
spectrum: 平坦 noise floor
诊断:   和 thermal noise 无法区分（都是加性高斯白噪声）
        要区分: 改变 Cs 看 SNR 是否按 √(kT/C) 变化，或看绝对量级
```

### 4. SAR logic 基本结构

详细推导见 stage_04 § 1.1。

##### SAR logic = 有限状态机（FSM）

SAR logic 本质是控制 trial 顺序 + 存储 bit decision 的状态机。这就是 SAR 名字里
"Register" 的部分（Successive Approximation **Register**）。

```text
状态转移:
  IDLE -> SAMPLE -> HOLD -> TRIAL(循环 N 次) -> DONE -> IDLE
                              ↑
                         每次执行 5 步:
                         a. 切 CDAC bit j 到 Vref
                         b. 等待 CDAC 建立
                         c. comparator 比较
                         d. 锁存 bit[j]
                         e. bit=1 保留, bit=0 切回 GND
```

##### 和贪心算法的对应

```text
状态机 TRIAL 的 5 步     ↔  数学 § 1 贪心算法:
  a. 切 bit j 到 Vref        ↔  v_test = v_dac + weights[j]
  b. 等待建立                ↔  (代码假设瞬间建立)
  c. comparator 比较         ↔  bit = (vin_norm >= v_test)
  d. 锁存 bit[j]             ↔  codes[j] = bit
  e. 保留/切回               ↔  v_dac = where(bit, v_test, v_dac)

代码 sar_convert 的 for j in range(B) 就是状态机在 TRIAL 循环 N 次
```

##### 为什么 SAR logic 本身不产生失真

```text
SAR logic 是纯数字电路:
  - 状态转移确定（FSM）
  - bit 存储确定（寄存器）
  - 没有 analog 噪声

SAR 的失真来自它控制的"模拟块":
  - CDAC: 电容 mismatch（§ 2）
  - comparator: 噪声 + offset（§ 3）
  - S/H: kT/C + settling（§ 4）

所以代码 sar_convert 不模拟 SAR logic 本身——
它的 "for 循环" 就是 SAR logic 的抽象，没有非理想参数
```

##### 实现方式

```text
方式 1: 硬连线状态机（传统 SAR）
  D 触发器 + 逻辑门，固定 N 比特，快 + 小
  商用 SAR ADC 多用这种

方式 2: 微控制器（可编程）
  小型 MCU 控制 trial，灵活（redundancy、可变 bit），慢 + 大
  研究/校准型 ADC 用

代码 sar_convert 用 Python for 循环 -> 对应方式 2 的抽象
不模拟状态机时序（时钟周期、建立时间），只模拟逻辑决策
```

## 6.完整 SAR Modeling 代码

详细解读见 stage_04 "完整 SAR Modeling 代码——端到端示例"。

### 6.1 三种场景的完整代码框架

```text
# 1. 权重
nominal = sar_ideal_weights(12)                       # [0.5, 0.25, ..., 1/2^12]
actual  = sar_apply_cap_mismatch(nominal, sigma=0.005, rng)
                                                       # sigma=0.005 = 0.5% 单位电容失配

# 2. 信号
vin = 0.45·sin(2π·Fin·t) + 0.5                        # 单音 + DC, full-scale=1.0

# 3. 三种场景（两套权重的核心）
codes_ideal  = sar_convert(vin, nominal)              # (a) ideal
codes_actual = sar_convert(vin, actual)               # 模拟域用 actual

aout_ideal = sar_reconstruct(codes_ideal,  nominal)   # (a) nominal→nominal
aout_uncal = sar_reconstruct(codes_actual, nominal)   # (b) actual→nominal (未校准)
aout_cal   = sar_reconstruct(codes_actual, actual)    # (c) actual→actual (校准后)
```

### 6.2 三种场景的权重流

```text
(a) ideal: vin →[convert, nominal]→ codes →[reconstruct, nominal]→ aout
            模拟用 nominal, 数字用 nominal -> 无失真（参考基准）

(b) uncal: vin →[convert, actual] → codes →[reconstruct, nominal]→ aout
            模拟用 actual(含 mismatch), 数字用 nominal(不知道)
            -> mismatch 暴露成 harmonic

(c) cal:   vin →[convert, actual] → codes →[reconstruct, actual] → aout
            模拟用 actual, 数字用同尺度 actual(oracle 或校准后缩放)
            -> mismatch 被补偿

关键: sar_convert 和 sar_reconstruct 的 weights 参数独立
      这是"两套权重"设计的体现
      Stage 06 校准的核心 = 估计可用于数字重构的权重；若解释成 actual
      weights，需要先确认它和 SAR normalized weights 在同一尺度上
```

### 6.3 实测结果（12-bit, sigma=0.005, Fin≈10MHz）

```text
codes shape: (8192, 12)    ← 8192 样本 × 12 bit
翻转样本: 896/8192 (10.9%)  ← 11% 样本的 bit decision 因 mismatch 改变

频谱对比:
              SNDR        SFDR        THD         ENOB
ideal:       73.07 dB    95.13 dB   -105.37 dB   11.85
uncal:       72.38 dB    83.69 dB    -83.62 dB   11.73
cal:         73.07 dB    95.85 dB   -101.94 dB   11.85
```

### 6.4 三个核心观察

```text
观察 1: 未校准时 SFDR 明显变差，SNR 几乎不变
  ideal→uncal: SFDR 95→84 dB (恶化 11 dB), SNR 几乎不变
  -> CDAC mismatch 产生 deterministic harmonic（影响 SFDR/THD）
     不增加 noise floor（不影响 SNR），因为 mismatch 是 deterministic
  诊断含义: SFDR 差但 SNR 好 -> mismatch 主导

观察 2: 校准后 SFDR 恢复到接近理想
  uncal→cal: SFDR 84→96 dB (恢复 12 dB), ENOB 11.73→11.85
  -> 用 actual weights 重构能补偿 mismatch
  校准本质: 用数字权重复现转换时模拟域的真实累积

观察 3: 校准前后 SNR 几乎不变
  cal 的 SNDR (73.07) ≈ ideal 的 SNDR (73.07)
  -> SNR 由 stochastic noise 决定（量化 + sampling + comparator）
  -> 校准只修 deterministic mismatch，不修 stochastic noise
  -> 这是 Stage 06 校准的核心局限
```

### 6.5 三个观察的诊断含义（连接 Stage 03）

```text
SFDR 差 + SNR 好    -> mismatch 主导（deterministic, 可校准）
SFDR 好 + SNR 差    -> comparator/sampling noise 主导（stochastic, 不可校准）
两者都差            -> 多种非理想叠加，需逐个分析

校准后:
  SFDR 明显改善      -> 确认是 mismatch
  SNR 不变          -> 确认 noise 是 stochastic
这套诊断流程在 whole_workflow demo step_4 演示过
```

## 6. stage_05 Digital Output 与 bit metrix 诊断

### 本阶段目标

- Bit metrix
- bit activity、weight radix、overflow、ENOB sweep
- 为什么 `analyze_weight_radix` 不是 DNL/INL 证明，只是权重列表诊断。
- 为什么 `analyze_enob_sweep` 观察的是 bit 子集对频谱性能的贡献，不是重新发明校准。
- 为什么校准前必须检查 raw bits 是否提供了足够可观测性

### 1.bit metrix（数学格式）

假设 4 个采样点、3-bit SAR：

```text
B =
sample0: [0, 0, 1]
sample1: [0, 1, 0]
sample2: [1, 0, 0]
sample3: [1, 1, 0]
```

如果权重是：

```text
w = [4, 2, 1]
```

重构结果是：

```text
y = B @ w
  = [1, 2, 4, 6]
```

逐列看 activity：

```text
MSB:  [0, 0, 1, 1] -> 2/4 = 50%
bit1: [0, 1, 0, 1] -> 2/4 = 50%
LSB:  [1, 0, 0, 0] -> 1/4 = 25%
```

假设 4 个采样点、3-bit SAR：

```text
B =
sample0: [0, 0, 1]
sample1: [0, 1, 0]
sample2: [1, 0, 0]
sample3: [1, 1, 0]
```

如果权重是：

```text
w = [4, 2, 1]
```

重构结果是：

```text
y = B @ w
  = [1, 2, 4, 6]
```

逐列看 activity：

```text
MSB:  [0, 0, 1, 1] -> 2/4 = 50%
bit1: [0, 1, 0, 1] -> 2/4 = 50%
LSB:  [1, 0, 0, 0] -> 1/4 = 25%
```

### 2. 数字重构：bit metrix --> waveform

给定权重：

```text
w.shape == (M,)
```

数字重构是：

```text
y = B @ w
```

逐样本写：

```text
y[n] = b0[n] * w0 + b1[n] * w1 + ... + bM-1[n] * wM-1
```

shape 变化：

```text
(N, M) @ (M,) -> (N,)
```

### 3. bit activity

第 `i` 位的 activity 定义为：

```text
activity_i = mean(B[:, i]) * 100%
```

因为 `B[:, i]` 只有 0 和 1，所以均值就是“这一位为 1 的比例”。

直觉上：

```text
输入在某个阈值两侧都充分出现
-> 这一位既有 0，也有 1
-> activity 接近 50%
```

但这不是数学定理，更不是“好 ADC 的充分条件”。

activity 受输入分布影响很大。例如：

```text
输入 DC 偏高:
  高位更容易为 1，activity 可能整体偏高。

输入幅度太小:
  某些高位或低位可能很少翻转。

输入 clipping:
  高位 activity 可能异常，且端点 code 过度集中。

输入不是正弦而是 ramp:
  activity 模式又会不同。
```

所以 activity 的正确用法是：

```text
先检查“这段数据有没有充分激励 bit”，不要直接把 50% 当作好坏判据。
```

### 4. weight radix：看权重比例是否符合预期

纯二进制 SAR 的权重近似：

```text
[1/2, 1/4, 1/8, 1/16, ...]
```

相邻权重比例是：

```text
radix_i = |w[i-1]| / |w[i]|
```

理想二进制：

```text
radix ≈ 2
```

sub-radix 或冗余结构：

```text
radix < 2
```

ADCToolbox 的 `analyze_weight_radix.py` 直接按这个公式算：

```python
radix[i] = abs_weights[i-1] / abs_weights[i]
```

注意它用的是绝对值：

```text
abs(weight)
```

所以即使某些 trim weight 是负的，也会按幅度参与 radix / effective span 分析

#### radix 诊断能说明什么

它能说明：

```text
权重列表是不是接近二进制；
是否存在 sub-radix / redundancy；
某一位权重是否异常跳变；
校准后权重形状是否符合架构直觉。
```

它不能单独证明：

```text
DNL 合格；
INL 合格；
没有 missing code；
SAR decision 一定可达；
比较器和采样噪声足够小。
```

#### effective resolution 的意义短记

`analyze_weight_radix` 还返回：

```text
effres = log2(sum(abs_w_sig) / min(abs_w_sig) + 1)
```

直觉是：

```text
把显著权重按最小显著权重归一化成 LSB 单位；
看这些权重一共能覆盖多少个 LSB；
再换算成 bits。
```

代码里还有一个“显著权重集合”的筛选：

```text
把 abs(weights) 从大到小排序；
如果相邻权重比值第一次 >= 3，就认为后面的很小权重可能是 trim/noise tail；
只用前面的 significant weights 算 effres。
```

`effres` 不是动态 ENOB，而是权重列表体检：

```text
effres = 显著权重按最小显著权重归一化后，理论上覆盖了多少 levels。
```

它有用的地方：

```text
看校准权重有没有丢 bit；
看权重 span 是否接近 nominal bit 数；
把很小的 trim/noise tail 和主权重链区分开；
辅助判断 redundancy / sub-radix 结构是否合理。
```

它不能替代：

```text
ENOB/SNDR 动态测试；
DNL/INL 静态线性度测试；
missing-code 和 decision reachability 检查。
```

一句话：

```text
effres 看 weights 像几 bit；ENOB 看 ADC 输出真的还剩几 bit。
```

### 6. residue / overflow：看剩余低位是否有修正余量

```text
真实 analog / reconstruction residue:
  r_k[n] = input[n] - sum(first k accepted bit weights)

suffix-code distribution:
  z_i[n] = sum(bits from bit i to LSB) / sum(weights from bit i to LSB)
```

为什么这个量和 redundancy 有关？对 SAR 来说，前面某一位 trial 做错后，后续低位只能靠剩余权重补偿。
严格二进制权重几乎没有正的 overrange margin：

```text
w[i] ~= sum(w[i+1:]) + 1 LSB
```

如果第 `i` 位错过了太多，后面低位的所有组合也可能补不回来。
冗余 / sub-radix SAR 刻意让某些权重比例小于 2：

```text
sum(w[i+1:]) > w[i]
```

`analyze_overflow.py` 对每个 bit 位置 `ii` 计算：

```python
tmp = raw_code[:, ii:] @ weight[ii:]
sum_weight = np.sum(weight[ii:])
data_decom[:, ii] = tmp / sum_weight
```

数学上写成：

```text
B[n, j] = raw_code[n, j]
w[j]    = weight[j]

suffix_i[n] = Σ_{j=i}^{M-1} B[n, j] * w[j]
W_i         = Σ_{j=i}^{M-1} w[j]
z_i[n]      = suffix_i[n] / W_i
```
**注意**：这里计算的时候是有数字的冗余，数字乘权重，而不是单纯考虑权重。本质上是在考虑信号与权重在本系统上是否匹配且有足够的余地。

用一个 3-bit 的例子看会更直观。假设列顺序是 MSB -> LSB：

```text
B[n, :] = [b2, b1, b0]
w       = [4,  2,  1]
```

那么三个 suffix distribution 分别是：

```text
i = 0: z_0[n] = (4*b2 + 2*b1 + 1*b0) / 7
i = 1: z_1[n] = (       2*b1 + 1*b0) / 3
i = 2: z_2[n] = (              1*b0) / 1
```

```text
range_min[i] = min_n z_i[n]
range_max[i] = max_n z_i[n]

ovf_percent_zero[i] = count(z_i[n] <= 0) / N * 100%
ovf_percent_one[i]  = count(z_i[n] >= 1) / N * 100%
```

也就是说，对每一个 bit 位置 `i`，函数先得到一条 suffix distribution：

```text
z_i[0], z_i[1], ..., z_i[N-1]
```

然后问四个问题：

```text
这条分布最低到哪里？        -> range_min[i]
这条分布最高到哪里？        -> range_max[i]
有多少样本贴到下边界 0？    -> ovf_percent_zero[i]
有多少样本贴到上边界 1？    -> ovf_percent_one[i]
```

它的工程意义是：

- 贴下边界：这段剩余 bit 已经没有再向下修正的余量
- 贴上边界：这段剩余 bit 已经没有再向上修正的余量

所以这四个量合起来回答的是：

- 从某一位开始，后面的低位组合还有没有 correction margin？
- 还是经常已经被推到全 0 / 全 1 的极限？

### 7. residual scatter：看不同 bit stage 的残差结构

`plot_residual_scatter.py` 才是真正用 `signal` 做 partial-sum residual 的工具。
它的问题是：

```text
减掉前 k 个 bit 的重构贡献后，还剩下什么误差？
这个中间误差和最终误差之间有没有结构关系？
```

数学定义：

```text
r_k[n] = signal[n] - Σ_{j=0}^{k-1} bits[n, j] * weights[j]
```

这类图可以看出：

```text
某个 bit stage 之后的残差是否仍然带有结构；
最终误差是否和早期 partial residual 强相关；
某些 stage 是否出现分叉、条纹、弯曲等非线性模式；
冗余结构是否把早期残差压回较小范围。
```

### 8. ENOB sweep：逐步增加 bit 子集看贡献

`analyze_enob_sweep.py` 看的是：**在同一组全量校准权重下，只使用前 n 个 bit 时，动态性能如何变化**。
它不是每个 bit 数都重新校准一次。

核心流程：

```text
1. 先用所有 bits 跑一次 calibrate_weight_sine，得到 weights_all。
2. 对 n_bits = 1, 2, ..., M：
   bits_subset = bits[:, :n_bits]
   weights_subset = weights_all[:n_bits]
   calibrated_signal = bits_subset @ weights_subset
   用 analyze_spectrum 算 ENOB。
```

数学上：

```text
w_all = Calibrate(B[:, :M])
y_n[n] = Σ_{j=0}^{n-1} B[n, j] * w_all[j]
ENOB_n = SpectrumENOB(y_n)
```

所以 ENOB sweep 的正确解释不是“第 n 位单独有多少 ENOB”，而是：

```text
在当前 bit 顺序和当前全量校准权重下，prefix bit subset 对动态性能的贡献如何。
```

常见形态：

| sweep 形状 | 可能解释 |
|---|---|
| ENOB 随 bit 数上升 | 低位确实带来更多有效信息 |
| 后面进入平台 | 随机噪声、失真或测试条件已经主导 |
| 增加低位反而下降 | 低位主要是噪声、权重估计差、或输入未充分激励 |
| 某一位加入后突变 | 该 bit 权重/活动/决策可能异常 |

### Stage 05 实验短记

#### 实验 1：whole workflow

```text
看 Stage 05 在完整链路中的位置：
  spectrum / analog error -> SAR bits/weights -> calibration -> validation
```

本次运行中：

```text
sar_after_sine_calibration ENOB ~= 11.62 bits
weight_effres_bits ~= 12.01 bits
first four bit activities ~= 50%
```

读法：

```text
activity 约 50% + effres 接近 nominal bits，只说明 bit matrix 和权重 span 没有明显低级异常；
校准后 ENOB 只小幅提升，说明当前 case 的 SNDR 瓶颈不完全由可校准权重误差主导。
```

#### 实验 2：bit activity

```text
activity = mean(bits[:, i])
```

它能发现：

```text
恒定列；
几乎不翻转的列；
输入 DC 偏置；
输入幅度覆盖不足；
某个 bit 活动异常。
```

它不能证明：

```text
矩阵满秩；
列与列之间没有相关；
校准权重一定稳定。
```

#### 实验 3：ENOB sweep

```text
先全量校准一次；
再用前 n 个 bit 和对应权重重构；
最后看 ENOB 随 n_bits 如何变化。
```

本次运行中，thermal noise case 到 12 bits 仍提升；加入 LSB random 后最佳点停在 11 bits。
这说明最低位可能已经被随机扰动主导。

#### 实验 4：weight radix

```text
strict binary: average radix ~= 2
sub-radix:     average radix < 2
```

本次运行中：

```text
Strict Binary: EffRes ~= 12.00 bits, avg radix ~= 2.0000
Sub-Radix:     EffRes ~= 12.34 bits, avg radix ~= 1.8196
```

radix / effres 是权重列表体检，不是 ENOB、DNL/INL 或 missing-code 证明。

#### 实验 5：overflow check

`exp_d14_overflow_check.py` 最容易误读。它画的是 suffix-code distribution：

```text
z_i[n] = (raw_code[:, i:] @ weight[i:]) / sum(weight[i:])
```

不是直接的 analog residue。在正权重、0/1 bit 下，`z_i[n]` 理论上不会真正越过 `[0, 1]`，
所以百分比主要读成“贴边比例”。

本次运行规律：

```text
Binary normal:
  MSB_range ~= [0.010, 0.990]

Binary large signal:
  MSB_range ~= [0.000, 1.000]
  MSB 贴边比例明显增加

Sub-radix 第三/第四幅：
  当前参数下差异不够明显；
  标题想表达 redundancy sufficient vs insufficient，
  但 suffix 图没有形成强教学对照。
```

所以第三/第四幅看起来差不多，不是核心函数算错，更像 demo 设计不够锋利。
若要教学上更清楚，应标注目标 bit 附近的 `range_min/range_max`，设置合适 `ofb`，
或加入 decision error / 更激进输入来激发差异。

#### 实验 6：SAR mismatch Monte Carlo

`exp_d16_sar_unit_cap_mismatch_mc.py` 比较：

```text
Strict binary vs radix ~1.8
before cal vs after cal
unit-cap mismatch sigma sweep
32-run Monte Carlo ENOB distribution
```

图中：

```text
曲线 = 32 次 Monte Carlo 的 median ENOB
深色阴影 = p10 到 p90
浅色阴影 = min 到 max
```

读法：

```text
before cal:
  两条虚线随 mismatch 快速下降，说明 nominal reconstruction 被 actual CDAC mismatch 破坏。

after cal:
  实线远高于虚线，说明 foreground sine calibration 学到了实际权重。

radix ~1.8 after cal:
  更接近 16 bit 且阴影更窄，说明 redundancy + calibration 对随机 mismatch 更稳。
```

这张图不是说 sub-radix 未校准就天然高 ENOB，而是说：

```text
unit-cap mismatch 会破坏未校准 SAR；
校准能恢复 deterministic weight error；
redundancy 让校准后的结果更稳健。
```

### 9. bit matrix 和可观测性

Stage 06 的校准可以看成一个线性回归问题。简化形式是：

```text
B @ w + c ≈ sine
```

其中：

```text
B: bit matrix, shape = (N samples, M bits)
w: bit weights, shape = (M,)
c: DC offset
```

真实 `calibrate_weight_sine` 还会加入 sine basis、harmonic basis、rank-deficiency patch、
column conditioning 等处理，但核心仍然是：**用 bit matrix 的列去解释一个已知或估计频率的正弦**。

这时 `B` 的列是否“可观测”非常关键。
用线性代数语言说，这就是最小二乘设计矩阵的 **rank deficiency / ill-conditioning** 问题。
严格一点，真正求解时看的不是裸的 `B`，而是完整设计矩阵：

```text
A = [bit columns, DC offset column, harmonic basis columns, ...]
```

真正能严格判断可解性的是：

```text
rank(A)
singular values of A
condition_number(A)
column dependency / near dependency
```

Stage 05 的几个图和指标不能严格证明矩阵可解，它们只是症状检查：

```text
bit activity:
  能发现恒定列、几乎不翻转列、输入覆盖不足。

weight radix / effres:
  看权重列表是否像预期架构，是后验 sanity check。

overflow:
  看 suffix code 是否贴边，主要是 correction margin / 输入范围诊断。

residual scatter:
  看 partial residual 和 final residual 是否有 stage-wise 结构。

ENOB sweep:
  看前 n 个 bit 对动态性能的后验贡献。
```

所以更准确的边界是：

```text
rank / SVD / condition number:
  判断 Stage 06 的 least-squares 是否数学上可辨识、数值上稳定。

Stage 05 diagnostics:
  帮助解释为什么它可能不可辨识、为什么会病态、或为什么结果不符合架构直觉。
```

## 7. stage_06 Sine-based ADC 位权重校准

### 本阶段学习目标
- ADC 位权重校准要解决什么问题。
- 为什么 sine input 可以用于估计 bit weights。
- `calibrate_weight_sine` 的输入、输出和整体数学逻辑。
- 为什么 `freq` 必须是 normalized `Fin/Fs`，而不是 Hz。
- `harmonic_order` 在校准模型里扮演什么角色。
- 为什么 rank deficiency 会让某些权重不可独立估计。
- 为什么校准通常改善 SFDR/THD，但不一定显著改善随机噪声导致的 SNR。
- 如何用 spectrum、residual 和独立测试数据验证校准效果。

### 7.1 重构模型

对 bit matrix：

```text
B.shape == (N, M)
```

数字重构：

```text
y = B @ w + c
```

其中：

```text
B -> 已知，来自 ADC raw bits
w -> 未知或不准，是待估计 bit weights
c -> DC offset
```

如果输入是单音正弦，理想输出可以写成：

```text
s[n] = A*cos(2πf n) + D*sin(2πf n) + C
```

### 7.2 最小模型

### 3. `calibrate_weight_sine_lite` 的最小模型

最小版本 `calibrate_weight_sine_lite.py` 假设频率已知，构造：

```python
t = np.arange(n_samples)
phase = 2.0 * np.pi * freq * t
cos_basis = np.cos(phase)
sin_basis = np.sin(phase)

offset_col = np.ones((n_samples, 1))
A = np.column_stack([bits, offset_col, sin_basis])
b = -cos_basis
coeffs, _, _, _ = lstsq(A, b)
```

这等价于求：

```text
bits @ w_raw + offset + sin_coeff * sin(2πf n) ≈ -cos(2πf n)
```

为什么把 `cos` 放到右边？

因为 sine 的整体幅度未知。如果把 `cos` 和 `sin` 两个 fundamental 系数都放进未知量，同时又让 `w` 也自由缩放，就会出现尺度不唯一：

```text
把 w、cos coefficient、sin coefficient 同时乘一个常数，
相对误差形式可能仍然难以唯一固定。
```

lite 版本用一个约定固定尺度：

```text
假设 cos fundamental coefficient = 1
```

然后求出其他系数。最后用 fundamental 幅度归一化：

```python
norm_factor = np.sqrt(1.0 + sin_coeff**2)
weights = weights_raw / norm_factor
```

直觉是：

```text
cos coefficient 固定为 1，sin coefficient 由最小二乘求出；
fundamental 的真实幅度是 sqrt(1^2 + sin_coeff^2)；
weights 要除以这个幅度，回到归一化后的物理权重尺度。
```

最后还有 polarity correction：

```python
if np.sum(weights) < 0:
    weights = -weights
```

因为最小二乘本身可能给出整体符号相反的等价解。对 SAR 权重来说，我们通常希望权重总和为正。

### 7.3 完整模型

#### （1） 不只固定`cos=1`

也就是：

```python
A1 = column_stack([bits, offsets, cos_basis[:, 1:], sin_basis])
b1 = -cos_basis[:, 0]

A2 = column_stack([bits, offsets, sin_basis[:, 1:], cos_basis])
b2 = -sin_basis[:, 0]
```

然后比较 residual：

```python
err1 = norm(A1 @ coeffs1 - b1)
err2 = norm(A2 @ coeffs2 - b2)
```

选择误差更小的一边。

#### （2）支持harmonic_order

真实 ADC 输出不一定只有 fundamental。CDAC mismatch、静态非线性、参考动态误差等会产生 harmonic：

```text
2Fin, 3Fin, 4Fin, ...
```

如果校准模型只允许 fundamental，而真实数据里有明显 harmonic，那么最小二乘可能会试图用 `weights` 去解释这些 harmonic。这样会污染权重估计。

完整版本构造 harmonic basis：

```python
harmonics = np.arange(1, harmonic_order + 1)
phase = 2.0 * np.pi * freq * outer(t, harmonics)
cos_basis = cos(phase)
sin_basis = sin(phase)
```

#### （3） freq 必须是 normalized frequency：

`calibrate_weight_sine` 的 `freq` 参数不是 Hz，而是：

```text
freq = Fin / Fs
```

Nyquist 范围是：

```text
0 <= freq <= 0.5
```

代码里有明确保护：

```python
if np.any(_freq_check > 0.5):
    raise ValueError("freq must be normalized Fin/Fs ...")
```

#### （4） 频率估计和 frequency search

如果 `freq=None`，完整版本会尝试估计频率：

```python
freq_array = _estimate_frequencies(bits_stacked, segment_lengths, freq, verbose)
```

估计时会先用一部分 bit 按二进制假设重构出一个粗略信号：

```python
assumed_weights = 2 ** np.arange(n_use - 1, -1, -1)
sig = current_segment[:, indices] @ assumed_weights
f_est = estimate_frequency(sig)
```

然后如果需要，会进入 frequency refinement：

```python
_solve_weights_searching_freq(...)
```

这个过程迭代做：

```text
1. 用当前频率求最小二乘权重。
2. 计算 residual 对频率的导数。
3. 更新频率。
4. 重复直到 relerr 足够小或达到 max_iter。
```

### 7.4 rank deficiency

**核心思想**：从秩的角度讨论矩阵的解

如果 rank 不够，就逐列修补：

```text
Case A: constant column -> dead bit, drop
Case B: independent column -> keep
Case C: dependent column -> merge into existing effective column
```

对 dependent column，代码用 nominal weights 的比例来分配：

```python
bit_weight_ratios[bit_idx] = nominal_weights[bit_idx] / nominal_weights[founding_bit_idx]
bits_effective[:, col_idx] += col * bit_weight_ratios[bit_idx]
```

求解完成后，再恢复回原 bit 空间：

```python
weights_recovered = w_effective[bit_to_col_map] * bit_weight_ratios
weights_recovered[bit_to_col_map < 0] = 0.0
```

物理意义是：

```text
如果数据只能看见两个 bit 的组合，就先估计组合总权重；
再按 nominal ratio 分回每个 bit。
```

### 7.5 column scaling：给最小二乘换一个更舒服的坐标系

column scaling 的基本数学意义是：

```text
如果设计矩阵 A 的某些列很大、某些列很小，
先把列缩放到相近数量级；
让 least-squares 在更好的数值坐标系里求解；
求完再把权重恢复回原坐标。
```

对：

```text
y ≈ B @ w
```

若：

```text
B_scaled = B @ D
```

求解器解的是：

```text
y ≈ B_scaled @ alpha = B @ D @ alpha
```

所以原坐标权重是：

```text
w = D @ alpha
```

源码里 `D` 是 10 进制数量级缩放：

```python
max_vals = np.max(np.abs(col_extremes), axis=0)
bit_scales = np.floor(np.log10(max_vals + 1e-15))
bits_effective = bits * (10.0 ** (-bit_scales))
```

求解后恢复：

```python
w_recovered_eff = w_normalized * (10.0 ** (-bit_scales))
```

放到 SAR ADC 里，要记住：

```text
MSB/LSB 的大小在 weights 里；
bit columns 本身通常只是 0/1。
```

所以普通 SAR bits：

```text
max(abs(B[:, j])) = 1
bit_scales[j] = 0
B_scaled = B
```

也就是说：

```text
column scaling 对纯 0/1 SAR bit matrix 基本是 no-op。
它不会解决 16-bit 权重跨度问题，因为权重跨度不在 bits 列值里。
```

它真正可能有用的地方，是 rank patch 之后：

```text
Case C merge 后，effective column 可能不再是 0/1；
如果某个合并列到达 10、100 这种数量级，
decade scaling 会把它拉回 O(1)。
```

但它不能解决：

```text
列高度相关；
bit 不翻转；
rank deficiency；
输入激励不足；
radix 冗余 SAR 的相关性病态。
```

原因很简单：

```text
scaling 只改列长度，不改列方向。
两列几乎一样时，把一列乘 10 也不会创造新信息。
```

一句话：

```text
column scaling 是低成本数值防御；
对普通 SAR 0/1 bits 大多不出手；
真正要关注的是 rank、bit activity、列相关性和训练输入覆盖。
```

### 7.6 输出结果应该如何理解

`calibrate_weight_sine` 返回 dictionary，常见字段：

```text
weight
offset
calibrated_signal
ideal
error
refined_frequency
snr_db
enob
```

其中：

```text
weight:
  校准得到的 digital reconstruction weights。

offset:
  拟合出的 DC offset。

calibrated_signal:
  用校准权重对 bits 重构出的信号。
  它不是 ADC 重新采样得到的信号。
  返回值是 list；单个 capture 时使用 cal["calibrated_signal"][0]。

ideal:
  拟合模型重构出来的 reference sine / harmonic model。
  返回值同样是 list。

error:
  calibrated_signal 去掉 offset 后与 ideal 的差。
  返回值同样是 list。

refined_frequency:
  最终使用或估计出的 normalized frequency。

snr_db / enob:
  基于内部拟合误差计算的性能摘要。
```

实际验证时，不要只看返回的 `enob`。更稳的做法是：

```python
calibrated = cal["calibrated_signal"][0]
metrics = analyze_spectrum(calibrated, ...)
```

然后和校准前比较：

```text
SNDR
SNR
SFDR
THD
ENOB
harmonics
noise floor
```

## 8. stage_07 校准验证、模型边界与工程严谨性

### 本阶段目标

学完本阶段，你应该能解释：

- 为什么校准结果不能只看训练数据。
- 为什么 ENOB 变好不等于模型完全正确。
- 如何区分 deterministic mismatch 和 random noise。
- 如何设计 train/test 分离的验证。
- 为什么 Monte Carlo 要看分布，而不是只看一个 seed。
- ADCToolbox 的行为级 SAR 模型有哪些边界。
- 测试条件为什么是指标的一部分。
- 校准如何影响 FOM，以及为什么校准本身也有代价。
- 如何把 `harmonic_order`、rank patch、bit activity 和尺度约定纳入校准可信度检查。
- 什么时候可以相信结果，什么时候只能把它当学习或算法原型。

### 8.1 核心主线：从“会校准”到“会判断”

Stage 06 的结果是：

```text
bits -> calibrated_weights -> calibrated_signal
```

Stage 07 问的是：

```text
这组 calibrated_weights 在训练数据之外还可信吗？
```

不要用一句：

```text
ENOB 变好了
```

替代完整判断。更稳的检查是：

```text
训练和验证是否分开；
换 frequency / amplitude / phase 后是否仍有效；
改善来自 SFDR/THD 还是 SNR；
bit activity / rank patch 是否正常；
H=1 vs H=3 权重差异是否很大；
dBFS / full-scale 标尺是否一致；
模型边界和测试条件是否写清楚。
```

### 8.2 证据等级

```text
Level 0:
  只看 training capture。
  只能说明训练目标下降，不能说明校准可信。

Level 1:
  同一颗 chip / mismatch realization 上，用独立 test capture。
  可以说明 weights 对另一个输入仍有效。

Level 2:
  扫 frequency / amplitude / phase / noise seed。
  可以说明在这个输入范围内较稳定。

Level 3:
  多 mismatch seed / Monte Carlo 分布。
  可以说明对一组随机芯片有统计稳定性。

Level 4:
  同时说明模型边界、测试源限制、校准代价和失效案例。
  才接近工程或论文级论证。
```

### 8.3 校准前 preflight

调用 `calibrate_weight_sine` 前先查：

```text
freq 是否是 normalized Fin/Fs；
bits shape 和 bit order 是否正确；
bit activity 是否合理；
是否有 constant columns；
输入是否覆盖足够 code；
是否发生 rank patch；
是否需要比较 H=1 / H=3；
before / after / oracle 的 max_scale_range 是否一致。
```

如果 bit 不翻、freq 单位错、输入 clipping 或标尺不一致，先修测试条件，不要急着解释 ENOB。

### 8.4 失败时的排查顺序

```text
1. 复现性：
   同一 seed 和同一设置能不能复现。

2. 分析设置：
   window、side_bin、nf_method、max_scale_range、是否去 DC 是否一致。

3. raw bits：
   bit activity、constant columns、rank deficiency、bit order。

4. train/test：
   是否独立；是否换频率、相位、幅度、noise realization。

5. harmonic 假设：
   H=1 vs H=3 normalized weight delta 是否很大。

6. oracle：
   仿真里 actual-weight oracle 是否也不理想。

7. 模型边界：
   是否是 sar.py 没有建模的 settling、reference droop、metastability、kickback 等。
```

### 8.5 结果怎么写

弱结论：

```text
在这条训练记录上，拟合误差下降。
```

中等结论：

```text
在独立 test capture 上，SFDR/THD 仍然改善，SNR 基本不变；
这符合 deterministic weight error 被修正的预期。
```

强一点的结论：

```text
在多个 frequency / amplitude / phase 和多个 mismatch seed 下，
校准后 SFDR/THD 分布稳定改善；
并报告 bit activity、rank patch、H=1/H=3 sensitivity、模型边界和测试条件。
```

不要写：

```text
ENOB 变高，所以校准正确。
数字校准消除了噪声。
H=3 更好，所以 harmonic_order 越高越好。
行为模型证明真实芯片一定由 CDAC mismatch 主导。
```

## 9.stage_08: Time-Interleaved ADC的失配与校准

### 本阶段目标

学完本阶段，你应该能解释：

- TI-ADC 为什么需要多个子 ADC 交织，交织后采样率怎么算。
- offset / gain / skew 三类失配分别在哪产生 spur。
- 为什么 TI spur 的位置是 `k·fs/M` 和 `fin ± k·fs/M`，而不是输入谐波。
- 怎么用单音正弦 + DFT 相量法从输出提取每通道的 offset/gain/skew。
- foreground 校准和 background 校准的区别。
- TI 校准和 SAR bit-weight 校准在数学结构上的相似与不同。
- 怎么验证 TI 校准效果（和 Stage 07 的思路一致）。

### 9.1 TI-ADC 的基本结构

#### 9.1.1 交织采样

TI-ADC 的核心动作是**交织**（interleave）。M 个子 ADC，每个以 `fs/M` 的速率采样，
但它们的采样时刻错开，合起来等效一个 `fs` 的采样器：

```text
通道 0 在 t = 0,    M/fs,   2M/fs,   ...
通道 1 在 t = 1/fs,  (M+1)/fs, ...
通道 2 在 t = 2/fs,  (M+2)/fs, ...
...
通道 M-1 在 t = (M-1)/fs, (2M-1)/fs, ...
```

输出序列就是把 M 个通道的样本按时间顺序拼起来：

```text
x[0] = ch0, x[1] = ch1, ..., x[M-1] = ch(M-1), x[M] = ch0, ...
```

所以 `x[n]` 属于通道 `n mod M`。这是 ADCToolbox 里 `deinterleave` 做的事：

如果 M 个通道**完全一致**，交织后的输出就和一个真正的 `fs` 采样器没区别。
但真实通道总有 offset / gain / skew 差异，这些差异在交织后变成周期性的调制，
调制频率是 `fs/M`，于是在频谱上产生 TI spur。

#### 9.1.2 offset mismatch

如果每个通道有不同的 DC 偏置 `offset_m`，那么交织后的输出相当于：

```text
x[n] = signal(n) + offset_{n mod M}
```

关键点：每个通道自己的 offset 是常数，但交织后的总输出会轮流取到不同通道的 offset：

```text
e[n] = offset_{n mod M}
```

所以从整体采样流看，offset error 是一个 M 点周期序列。M 点周期序列可以展开为：

```text
e[n] = Σ C_k · exp(j·2π·k·n/M)
```

因此它的频谱只在 `k·fs/M`（k=1..M-1）有非 DC 分量。offset mismatch 产生的 spur 固定在：

```text
fs/M, 2fs/M, ..., (M-1)fs/M
```

不是 `fs/(M·k)`，因为 offset pattern 每 M 个样本重复一次，基频就是 `fs/M`；
更高项是这个基频的整数倍 `k·fs/M`。

#### 9.1.3 gain + skew mismatch

如果每个通道有不同的增益 `gain_m`，交织后的输出相当于：

```text
x[n] = signal(n) * gain_{n mod M}
```

注意这里和 offset 不同：offset 是**加性误差**，gain/skew 是对输入的**乘法调制**。
设：

```text
a[n] = gain_{n mod M}
a[n] = Σ C_k · exp(j·2π·k·n/M)
s[n] = A/2 · exp(jω0 n) + A/2 · exp(-jω0 n)
```

那么：

```text
y[n] = a[n] · s[n]
     = A/2 · Σ C_k · exp(j(ω0 + 2πk/M)n)
      +A/2 · Σ C_k · exp(j(-ω0 + 2πk/M)n)
```

所以 gain mismatch 的 spur 不固定在 `k·fs/M` 本身，而是出现在输入单音两侧：

```text
fin ± fs/M, fin ± 2fs/M, ..., fin ± (M-1)fs/M
```

频域上，这是“时域相乘 = 频域卷积”：周期 gain error 在 `k·fs/M` 有谱线，
输入在 `±fin` 有谱线，卷积后得到 `±fin + k·fs/M`。

skew 也可以并入这个框架。对单音：

```text
s(t + skew_m)
= exp(j·2π·fin·t) · exp(j·2π·fin·skew_m)
```

所以 skew 等价于每个通道有一个频率相关的复数增益：

```text
alpha_m = gain_m · exp(j·2π·fin·skew_m)
```

小 skew 时 `exp(j·2π·fin·skew_m) ≈ 1 + j·2π·fin·skew_m`，因此 skew spur 会随
`fin` 增大而变严重。

### 9.2 DFT 相量法：从输出反推 offset / gain / skew

`extract_mismatch_sine` 的思路：

```text
1. deinterleave(x, M)
   channels[m, k] = x[k·M + m]

2. 用绝对采样时间
   t_m[k] = (k·M + m) / fs

3. 先估计 offset
   offset_m = mean(channels[m])

4. 在 fin 处做 DFT 投影
   P_m = (2/K) Σ (y_m[k] - offset_m) · exp(-j·2π·fin·t_m[k])

5. 从相量拿 gain / skew
   gain_m = |P_m| / mean(|P|)
   skew_m = (unwrap(angle(P_m)) - mean_phase) / (2π·fin)
```

为什么要用绝对时间 `t_m[k] = (kM+m)/fs`？因为通道之间本来就错开 `1/fs`。
如果只用每个通道自己的局部时间，会把理想交织相位误认为 skew。

相量为什么等于幅度和相位？设：

```text
y_m - offset_m = A_m · cos(ω0t + φ_m)
ω0 = 2π·fin
```

则：

```text
A_m cos(ω0t + φ_m) · exp(-jω0t)
= A_m/2 · exp(jφ_m)
 + A_m/2 · exp(-j(2ω0t + φ_m))
```

第一项是常数，求和后保留；第二项是 `2fin` 旋转项。在 coherent sampling 下：

```text
Σ exp(-j2ω0t) ≈ 0
```

所以：

```text
P_m ≈ A_m · exp(jφ_m)
```

这就是：

```text
abs(P_m)   -> 通道 fundamental 幅度 -> gain
angle(P_m) -> 通道 fundamental 相位 -> skew
```

二倍频项“约等于零”的意思不是输出里没有二倍频，而是它在 fundamental DFT 投影里
与目标基函数正交，复平面向量绕完整圈后相消。若采样不相干、fin 估计不准或窗口太短，
这项不会完全抵消，会以 leakage 形式污染 gain/skew 提取。

skew 的相位关系：

```text
s(t + skew_m) = cos(2πfin t + φ + 2πfin·skew_m)
Δφ_m = 2πfin·skew_m
skew_m = Δφ_m / (2πfin)
```

代码减掉 mean phase，因为整体公共延迟不可观测，只能得到相对 skew。

### 9.3 foreground vs background

| | foreground (ti01) | background (ti02) |
|---|---|---|
| 需要已知校准输入 | 是，通常是单音正弦 | 否，可以正常工作时后台搜索 |
| 是否打断正常工作 | 是 | 否 |
| 求解方式 | 一次提取 offset / gain / skew | 迭代调 trim code |
| 收敛速度 | 快 | 慢 |
| 精度限制 | 主要受单音质量、DFT 泄漏、噪声影响 | 受噪声、量化、评价指标和搜索策略影响 |
| 典型硬件 | 不一定在线实现 | 常配合 VDL / trim DAC |
| 适用场景 | 上电、出厂、实验室 characterization | 运行时温漂和慢漂移跟踪 |

foreground 的逻辑：

```text
停下来 -> 输入已知校准信号 -> 一次性估出 offset/gain/skew。
```

所以它快、准，但需要校准模式。ti01 的 `extract_mismatch_sine` 就是 foreground：

```text
offset -> 通道均值
gain   -> fin 处 DFT 相量幅度
skew   -> fin 处 DFT 相量相位 / (2πfin)
```

background 的逻辑：

```text
系统继续工作 -> 后台调 trim -> 看指标变好还是变坏。
```

ti02 用 VDL 改变通道采样延迟，再通过 SFDR / 自相关类指标搜索更好的 trim code。
它不需要已知输入，也不打断工作，但慢、受噪声和量化影响。

两者通常组合使用：

```text
上电 / 出厂:
  foreground 先校掉大误差。

正常运行:
  background 跟踪温漂和慢变化。
```

### 9.4 VDL：Variable Delay Line

VDL 是可变延迟线，用数字 `trim code` 控制采样时钟/采样开关的延迟。

```text
trim code -> delay_sec
```

它不是 ADC 输出码校正器，也不是数字滤波器，而是一个时间微调旋钮：

```text
code = 512 -> 约 0 fs
code = 513 -> 约 +10 fs
code = 511 -> 约 -10 fs
```

在 exp_ti02 里，每个通道的总 skew 是：

```text
effective_skew_m = intrinsic_skew_m + VDL_m(trim_code_m)
```

所以 VDL 只能直接修 timing skew：

```text
offset:
  不能靠 VDL 修，需要减 DC / offset trim。

gain:
  不能靠 VDL 修，需要幅度归一 / gain trim。

skew:
  可以靠 VDL 改采样边沿位置。
```

这也是为什么 exp_ti02 是 **background skew calibration**，不是完整的
offset/gain/skew background calibration。

这里的 LSB 是 VDL LSB，不是 ADC LSB：

```text
ADC LSB:
  电压 / 码值步长。

VDL LSB:
  时间步长，一个 trim code 对应多少秒。
```

exp_ti02 当前参数：

```text
n_codes = 1024
center code = 512
1 VDL LSB ≈ 10 fs
total range ≈ 10.2 ps / channel
```

所以：

```text
ideal code = 647
actual code = 648
```

表示：

```text
actual 比 ideal 多 1 个 VDL code step
≈ 采样边沿多延迟 10 fs
```

不是 ADC 输出值差 1 个码。

残余时间误差会变成相位误差：

```text
Δφ = 2π · fin · Δt
```

在 `fin≈300 MHz`、`Δt=10 fs` 时：

```text
Δφ ≈ 1.9e-5 rad
```

很小，所以 `exp_ti02_lsb_sensitivity.png` 里差 1 个 VDL LSB 几乎不影响 SFDR。

VDL 还有 DNL：每个 code step 不一定刚好都是 10 fs。代码用 `step_cv=0.15`
模拟 15% 左右的 step variation，但保证每一步为正，所以 VDL 曲线单调。

### 9.5 TI 校准 vs SAR bit-weight 校准

| 维度 | SAR 校准 (Stage 06) | TI 校准 (Stage 08) |
|---|---|---|
| 待估参数 | 每个位的 digital weight | 每通道 offset / gain / skew |
| 观测 | bit matrix `B` | 交织输出 `x` |
| 第一步 | 构造 `B @ w` | `deinterleave` 拆通道 |
| 目标信号 | 正弦 basis | 单音 DFT 相量 / 在线指标 |
| 核心方法 | 最小二乘 `B @ w ≈ sine` | DFT 相量拟合或 background 搜索 |
| spur 性质 | 输入谐波，如 2fin / 3fin | TI 网格 spur，如 `k·fs/M` 和 `fin ± k·fs/M` |
| 不可观测自由度 | 整体尺度 | 整体公共延迟 |
| 处理方式 | fundamental 归一 | skew 减均值 |

Stage 06 解决的是：

```text
同一个 SAR ADC 内部，bit weight 不准。
```

它估计的是：

```text
w0, w1, w2, ...
```

并用：

```text
B @ w ≈ sine
```

做线性回归。

Stage 08 解决的是：

```text
多个子 ADC 交织时，通道之间不一致。
```

它估计的是：

```text
offset_m, gain_m, skew_m
```

所以必须先拆通道，再分别看均值、幅度和相位。

共同点：

```text
都是从正弦相关观测中反推一组数字校准参数。
```

区别：

```text
SAR:
  修的是 bit-weight reconstruction。

TI:
  修的是通道间对齐。
```

一个重要对应：

```text
SAR 的整体尺度不可观测 -> weights 用 fundamental 归一。
TI 的公共延迟不可观测 -> skew 减均值，只保留相对 skew。
```

## 10. stage_09:Subsample Debug Output（无滤波下采样调试窗口）

### 本阶段目标

学完本阶段，你应该能解释：

- subsample-only 和带抗混叠滤波的 DSP downsample 有什么本质区别。
- 为什么 debug port 下采样会保留 spur 高度，但改变 spur 频率位置。
- alias 公式如何用于 fundamental、harmonic 和 TI spur。
- 为什么无滤波下采样后 NSD 会恶化 `10*log10(N)`。
- 为什么 TI-ADC 的 debug 下采样因子要和 interleave 通道数互质。
- 如何运行 `09_downsample/exp_d00_subsample_aliasing.py` 检查这些现象。

### 10.1 DSP decimation vs debug subsampling

**核心思路**：Debug输出的采样率可能与输入采样率不同
真正的 DSP decimation 通常是：

```text
low-pass / band-limit -> keep every N-th sample
```

也就是先把 `fs_out/2` 以上的频率滤掉，再抽点：

```text
fs_out = fs_in / N
Nyquist_out = fs_out / 2
```

目的：

```text
得到一个低带宽、已抗混叠、可继续处理的干净信号。
```

Stage 09 的 debug output 是：

```text
y[m] = x[m·N]
```

也就是只保留每 N 个 ADC sample 中的 1 个，不先低通。因此所有频率成分都会按
`fs_out` 重新折叠：

```text
f, f ± fs_out, f ± 2fs_out, ...
```

在 debug 输出里可能落到同一个频率位置。

这不是 bug，而是目的不同：

```text
DSP decimation:
  带外 spur 是污染源，应该滤掉。

ADC debug / monitor output:
  带外 spur 可能正是调试证据，应该尽量保留。
```

debug 口想观察 raw ADC 行为，例如：

```text
harmonic；
spur；
code histogram；
TI channel pattern；
reference / clock / settling artifact。
```

如果先低通，这些证据可能被删掉。

代价是：低速 debug 频谱的频率轴不能直接当成原始模拟频率。正确读法是：

```text
1. 知道 fs_in 和 N。
2. 算 fs_out = fs_in / N。
3. 对可疑 spur 按 fs_out 反折叠。
4. 再判断它可能来自 fundamental、harmonic、TI spur 或其他 artifact。
```

一句话：

```text
DSP decimation 追求“干净低速信号”；
Stage 09 debug subsampling 追求“低速但尽量 raw 的观察窗口”。
```

### 10.2 aliasing 公式

设输出采样率：

```text
fs_out = fs_in / N
```

任意真实频率 `f` 在 debug output 中会落到：

```text
f_alias = | ((f + fs_out/2) mod fs_out) - fs_out/2 |
```

这和 Stage 02 的 Nyquist folding 是同一件事，只是这里的采样率从 `fs_in`
变成了低速输出口的 `fs_out`。

举例：

```text
fs_in  = 1 GHz
N      = 3
fs_out = 333.33 MHz
Nyq    = 166.67 MHz
```

如果输入 fundamental 是 100 MHz：

```text
HD2 = 200 MHz -> alias 到 133.33 MHz
HD3 = 300 MHz -> alias 到 33.33 MHz
```

### 10.3 NSD 为什么会恶化

总噪声功率没有因为简单丢样而神奇消失；但输出 Nyquist 带宽缩小成原来的 `1/N`。
如果同样的噪声功率挤进更窄的频带，单位 Hz 的噪声密度会上升：

```text
NSD_out ≈ NSD_in + 10*log10(N)
```

注意区分：

```text
SNR / SNDR:
  看带内总功率比，依赖你定义的带宽。

NSD:
  看每 Hz 噪声密度，输出采样率变小后很容易看起来变差。
```

所以 Stage 09 的重点不是“下采样提高 SNR”，而是“低速 debug 口如何解释频率轴和噪声密度”。

### 10.4 Debug output 的意义

Stage 09 的 debug output 不是低速精确频谱仪，也不是完整 ADC 性能测量口。
它更像：

```text
observability port:
  IO / 测试链路受限时，提供一个低速但尽量 raw 的观察窗口。
```

它的意义不是“测得准”，而是“看得到”。

关键区别：

```text
完整码字:
  每个被送出来的 sample 仍然保留完整 ADC code。

完整采样序列:
  每个采样时刻都保留下来，频率信息不因丢样而 alias。
```

subsample debug output 通常是：

```text
完整码字，稀疏时间序列。
```

例如：

```text
原始:
  x[0], x[1], x[2], x[3], x[4], ...

N=4 debug:
  x[3], x[7], x[11], ...
```

为什么不直接输出全速 raw code？主要是观测链路受限：

```text
pad / package IO 带宽；
FPGA / ATE capture 速率；
片上 debug bus 宽度；
高速持续输出功耗；
高速接口面积和验证成本；
片上 SRAM 只能短抓，不能长期 streaming。
```

所以本质是：

```text
ADC 内部太快，外部观察太慢；
用时间完整性换 IO 可观测性。
```

最终产品输出也不一定等于 ADC core 的 raw 输出，它可能已经经过：

```text
digital calibration；
channel alignment；
decimation filter；
DDC / averaging；
format packing / JESD framing。
```

这些处理可能把你想 debug 的 raw artifact 滤掉、校掉或平均掉。

debug output 适合看：

```text
有没有异常；
扫 trim / bias / supply / temperature 后异常是否变化；
channel pattern / code histogram；
校准前后的 alias spur 相对变化；
长期趋势。
```

不适合单独判断：

```text
某个 debug spur 的唯一原始频率；
完整未混叠频谱；
collision 后单个 spur 的真实幅度；
数据手册级最终性能。
```

一句话：

```text
Debug output 不是 performance characterization port；
它是 observability port。
```

### 10.5 和 TI-ADC 的连接：N 要和通道数互质

如果前一级是 M-way TI-ADC，原始样本通道序列是：

```text
ch0, ch1, ch2, ..., ch(M-1), ch0, ch1, ...
```

如果每 N 个样本取一个，取到的通道是：

```text
sample index: N-1, 2N-1, 3N-1, ...
channel:      (N-1) mod M, (2N-1) mod M, ...
```

如果 `gcd(N, M) != 1`，输出可能只访问部分通道。最坏情况：

```text
M = 4, N = 4
```

每次都取同一个通道，debug output 完全看不到 channel-to-channel mismatch。

所以经验规则是：

```text
gcd(N, M) = 1
```

常用选择：

```text
N = 31  适合很多 M，输出率低，覆盖通道均匀
N = 15  对 M = 2/4/8/16 互质
N = 7   对非 7 因子的 M 互质
```

避免在 binary-interleaved ADC 上用 `N = 2, 4, 8, 16` 这类因子。
