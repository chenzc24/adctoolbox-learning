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

