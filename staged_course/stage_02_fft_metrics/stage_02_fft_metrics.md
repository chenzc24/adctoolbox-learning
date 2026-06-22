# Stage 02：FFT 与 ADC 动态性能指标

## 本阶段如何承接 Stage 01

Stage 00 建立了 ADCToolbox 的数组语言：

```text
vin.shape     == (N,)
bits.shape    == (N, n_bits)
weights.shape == (n_bits,)
aout.shape    == (N,)
```

Stage 01 解释了这些数组为什么会出现：

```text
连续输入电压
-> sampling 得到 vin
-> quantization / SAR decision 得到 bits
-> sar_reconstruct 得到 aout
```

Stage 02 从这里继续。它不再问 ADC 怎么把电压变成 code，而是问：

```text
已经得到一串 ADC 输出波形 aout 后，
怎样判断它的动态性能到底好不好？
```

也就是说，本阶段的输入对象通常是：

```text
aout.shape == (N,)
```

它可以来自行为模型、Spectre 仿真、芯片测试数据，或者本库的信号生成器。
Stage 02 的任务是把这串时间波形变成频谱，再从频谱里分出：

```text
信号、噪声、谐波、杂散、DC
```

一句话承接：

```text
Stage 01 讲“ADC 为什么产生 aout”；
Stage 02 讲“拿到 aout 后，怎样用 FFT 看 SNR / SNDR / SFDR / THD / ENOB”。
```

## 本阶段目标

学完本阶段，你应该能解释：

- 为什么 ADC 动态性能测试常用单音 sine。
- DFT / FFT bin、频率分辨率、single-sided spectrum 是什么。
- 什么是 coherent sampling，为什么它会让频谱分析更干净。
- spectral leakage 为什么会出现，window 为什么有用但不是魔法。
- SNR、SNDR、SFDR、THD、ENOB、NSD 分别衡量什么。
- 为什么频谱分析必须排除 DC、fundamental 和 harmonics。
- `analyze_spectrum` 的关键参数和返回字段代表什么。
- 如何从频谱现象反推常见 ADC 非理想来源。

如果这一阶段不稳，后面看 Stage 03 的 residual / error spectrum，或者 Stage 06 的
calibration before / after ENOB，就容易只盯一个 ENOB 数字，而看不出性能到底坏在哪里。

## 初学者先抓住的主线

FFT 阶段不是为了“画一张漂亮频谱图”，而是为了把 ADC 输出拆成几类能量：

```text
DC                  -> 偏置，通常不算动态信号
fundamental          -> 你真正输入的单音正弦
harmonics            -> 非线性失真
other spurs          -> 杂散、失配、干扰、时序误差
remaining bins       -> 噪声底
```

所有动态指标都来自这些能量的分类和相除。你可以先记住：

| 指标 | 初学者直觉 |
|---|---|
| SNR | 信号比随机噪声高多少 |
| SNDR | 信号比噪声加失真高多少 |
| SFDR | 最大单个 spur 离信号多远 |
| THD | 谐波失真总共有多强 |
| ENOB | 把 SNDR 翻译成“等效多少 bit” |
| NSD | 噪声摊到每 Hz 后是多少 |

所以看到 `analyze_spectrum` 的结果时，先不要只盯 ENOB。先问：

```text
到底是 noise floor 坏了，
还是 harmonic / spur 坏了？
```

这一个问题会贯穿后面的 error analysis、SAR mismatch、数字校准和测试诊断。

## 数学需要补什么

### 1. 正弦信号和 normalized frequency

单音测试信号通常写成：

```text
x[n] = DC + A sin(2π Fin n / Fs)
```

其中：

```text
Fs  -> sampling frequency，单位 Hz
Fin -> input frequency，单位 Hz
N   -> FFT 点数，也就是这一段数据的样本数
```

用 normalized frequency 表示：

```text
f = Fin / Fs
x[n] = DC + A sin(2π f n)
```

本库很多函数会使用 normalized frequency。读代码时要区分：

```text
Fin, fs -> Hz
freq    -> Fin / fs，归一化频率
bin     -> FFT bin index
```

在 coherent sampling 的例子里，本库也常写成：

```python
n = np.arange(N)
vin = INPUT_DC + INPUT_AMPLITUDE * np.sin(2.0 * np.pi * fin_bin * n / N)
```

这里 `fin_bin / N` 就是归一化频率 `Fin / Fs`。

### 2. DFT 分析的不是无限长连续信号

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

这也是 FFT 的频率分辨率：

```text
df = Fs / N
```

DFT 的第 `k` 个 bin 对应的物理频率就是：

```text
f_k = k * Fs / N
```

从“时域到频域”的角度看，DFT 系数就是信号和第 `k` 个复指数基底取内积：

```text
X[k] = sum_n x[n] * exp(-j 2π k n / N)
```

频谱幅度就是这个复系数的模，或经过缩放后的模。也就是说，频域里看到的第 `k`
个 bin，本质上是在问：

```text
这段数据里有多少 k * Fs / N 这个频率成分？
```

FFT 只是快速计算 DFT 的算法。学习本阶段时，可以先把 FFT 和 DFT 理解成同一件事：

```text
time-domain samples -> frequency-domain bins
```

注意区分连续傅里叶变换、傅里叶级数和 DFT：

| 方法 | 分析对象 | 频域形式 | 本阶段要记住什么 |
|---|---|---|---|
| 连续傅里叶变换 CTFT | 连续时间、无限长度或非周期信号 | 连续频率 | 不是本库 FFT 数据流的直接模型 |
| 傅里叶级数 | 连续时间、周期为 `T` 的信号 | `k / T` 离散频率 | 基频由周期 `T` 决定 |
| DFT / FFT | `N` 点离散数据，默认 N 点周期延拓 | `k * Fs / N` 离散 bin | coherent sampling 要让 `Fin` 对齐某个 bin |

### 3. FFT bin 和相干采样

如果输入正弦频率刚好满足：

```text
Fin / Fs = fin_bin / N
```

等价于：

```text
Fin = fin_bin * Fs / N
```

那么它正好等于 DFT 的某个基底频率，能量会集中在对应的 `fin_bin` 上。
这里的 `fin_bin` 同时有两个含义：

```text
1. 输入正弦在 DFT / FFT 里的 bin index
2. N 个采样点窗口里正弦完成的周期数
```

这就是 coherent sampling：采样窗口里正好包含整数个输入周期。

如果 `Fin` 不是 `Fs / N` 的整数倍，N 点数据首尾不能无缝周期延拓。DFT 只能用多个
bin 一起表示这个频率，频域上就表现为 spectral leakage。

实际使用时要分两种情况：

```text
Fin 已定：
    选择合适的 Fs 和 N，让 fin_bin = Fin * N / Fs 是整数

Fs 和 N 已定：
    调整 Fin 到最近的 coherent frequency，即 Fin = fin_bin * Fs / N
```

本库里的 `find_coherent_frequency(fs, fin_target, n_fft)` 属于第二种情况：
在目标 `Fin` 附近找一个合适的整数 `fin_bin`，再返回真正用于仿真的 `Fin_actual`。
这样做的主要目的，是让单音频谱分析时能量落在 FFT bin 上，减少 leakage，方便后续看
SNR、SNDR、SFDR、THD 和 sine-based calibration。

对应 API：

```python
from adctoolbox import find_coherent_frequency

Fin_actual, fin_bin = find_coherent_frequency(fs=Fs, fin_target=Fin_target, n_fft=N)
```

### 4. Two-sided 和 single-sided spectrum

这一节要把三件容易混在一起的事分开：

```text
1. 复指数基底
   -> 解释为什么 DFT 里有正频率和负频率

2. 采样后的离散时间频率
   -> 解释为什么频谱以 Fs 为周期重复

3. 实数信号的共轭对称性
   -> 解释为什么 ADC 常画 single-sided spectrum
```

不要把“使用复指数”误解成“频谱只能看到 `Fs/2`”。更底层的逻辑是：

```text
复指数基底让 DFT 可以区分正负旋转方向；
采样让离散时间频谱以 Fs 为周期重复；
实数信号让负频率半边成为正频率半边的共轭镜像。
```

#### 4.1 复指数解释正负频率

DFT 使用复指数基底：

```text
exp(+j 2π f n / Fs)
exp(-j 2π f n / Fs)
```

这两个基底可以理解成复平面上两个方向的旋转：

```text
+f -> 逆时针旋转
-f -> 顺时针旋转
```

一个实数余弦可以拆成一对正负频率复指数：

```text
cos(2π f n / Fs)
= 0.5 * exp(+j 2π f n / Fs)
  + 0.5 * exp(-j 2π f n / Fs)
```

所以，如果 ADC 输出是实数序列，一个真实的单音正弦在 two-sided DFT 里天然会出现
两根谱线：

```text
+Fin 一根
-Fin 一根
```

这解释的是“为什么有正负频率”，但它还没有解释“为什么常说只看 `0 ~ Fs/2`”。

#### 4.2 采样后，频率以 Fs 为周期

设连续时间复指数为：

```text
x_c(t) = exp(j 2π f t)
```

采样后：

```text
x[n] = x_c(n / Fs)
     = exp(j 2π f n / Fs)
```

现在看另一个频率 `f + Fs`：

```text
exp(j 2π (f + Fs) n / Fs)
= exp(j 2π f n / Fs) * exp(j 2π n)
= exp(j 2π f n / Fs)
```

因为对整数 `n`：

```text
exp(j 2π n) = 1
```

所以对离散采样序列来说：

```text
f 和 f + Fs 完全不可区分
```

更一般地：

```text
f, f ± Fs, f ± 2Fs, ...
```

都会采样成同一个离散时间频率。因此：

```text
离散时间频谱以 Fs 为周期。
```

这才是理解 Nyquist 频率和 aliasing 的核心。

#### 4.3 FFT 不是只能算到 Fs/2，而是给出一个 Fs 宽度的周期

N 点 FFT 原始 bin 顺序通常写成：

```text
k = 0, 1, 2, ..., N-1
```

对应频率可以先写成：

```text
0, Fs/N, 2Fs/N, ..., (N-1)Fs/N
```

也就是区间：

```text
[0, Fs)
```

但这里要说得更严谨一点。raw FFT 后半段之所以可以解释成负频率，不只是因为我们
在频率数值上“减去一个 `Fs`”，而是因为 DFT 的复指数基底本身具有 modulo-N 等价性：

```text
exp(j 2π k n / N)
= exp(j 2π (k - N) n / N)
```

原因是：

```text
exp(j 2π (k - N)n / N)
= exp(j 2π k n / N) * exp(-j 2π n)
= exp(j 2π k n / N)
```

对整数 `n`：

```text
exp(-j 2π n) = 1
```

所以：

```text
k 和 k - N 表示同一个离散时间复指数基底。
```

换成物理频率，就是：

```text
f_k = k * Fs / N
f_{k-N} = (k - N) * Fs / N
```

二者相差一个 `Fs`，对采样后的离散序列来说等价。区间 `[0, Fs)` 和
`[-Fs/2, Fs/2)` 因此是同一个离散频谱周期的两种重标方式。

以 `N = 8` 为例，raw FFT 顺序可以写成：

```text
k = 0 -> 0
k = 1 -> Fs/8
k = 2 -> 2Fs/8
k = 3 -> 3Fs/8
k = 4 -> 4Fs/8 = Fs/2
k = 5 -> 5Fs/8
k = 6 -> 6Fs/8
k = 7 -> 7Fs/8
```

其中后半段 `k = 5, 6, 7` 更自然地用等价索引 `k - N` 重标为负频率：

```text
k = 5 -> k - N = -3 -> -3Fs/8
k = 6 -> k - N = -2 -> -2Fs/8
k = 7 -> k - N = -1 -> -Fs/8
```

所以同一个 FFT 输出也可以解释成：

```text
0, +Fs/8, +2Fs/8, +3Fs/8, +Fs/2, -3Fs/8, -2Fs/8, -Fs/8
```

如果用 `fftshift` 重新排列，则常画成：

```text
-Fs/2, ..., -Fs/8, 0, +Fs/8, ..., +Fs/2
```

因此更严谨的说法是：

```text
FFT 给出一个宽度为 Fs 的离散频谱周期；
DFT bin index 是 modulo N 的；
工程上常把 raw FFT 后半段按 k-N 重标为负频率；
再选择 [-Fs/2, Fs/2] 这个 centered 周期作为 two-sided spectrum。
```

任意长度为 `Fs` 的频率区间都包含同样的信息，例如：

```text
[-Fs/2, Fs/2)
[0, Fs)
[Fs/2, 3Fs/2)
[-Fs, 0)
```

它们只是同一个周期频谱的不同窗口。

#### 4.4 Nyquist 频率是频谱周期的边界，也是 aliasing 的边界

采样会让连续时间频谱复制到每个 `Fs` 的整数倍附近：

```text
X_s(f) = ... + X_c(f - Fs) + X_c(f) + X_c(f + Fs) + ...
```

如果原始信号是 baseband，最高频率为 `B`，它的频谱主要在：

```text
[-B, B]
```

为了采样后的频谱副本不重叠，需要：

```text
B < Fs/2
```

这就是 Nyquist 条件的频域直觉：

```text
Fs/2 不是 FFT 的计算极限；
Fs/2 是以 0 为中心、宽度为 Fs 的一个频谱周期的边界；
也是 baseband 信号不发生 aliasing 的最高频率。
```

如果连续输入频率高于 `Fs/2`，它不会“消失”，而会折叠回 `[-Fs/2, Fs/2]`
这个基本频率区间。例如：

```text
Fin = 0.8 Fs
```

在离散时间里等价于：

```text
0.8Fs - Fs = -0.2Fs
```

如果只看实数信号的幅度 single-sided spectrum，它会出现在：

```text
0.2Fs
```

这就是 aliasing。

#### 4.5 为什么实数 ADC 输出常画 single-sided

ADC 输出通常是实数序列。对实数 `x[n]`，DFT 有共轭对称性：

```text
X[-k] = conj(X[k])
```

等价地，在 N 点 DFT 索引中：

```text
X[N-k] = conj(X[k])
```

所以幅度满足：

```text
|X[-k]| = |X[k]|
```

因此在 centered two-sided spectrum：

```text
[-Fs/2, Fs/2]
```

里，负频率半边没有新的幅度信息，只是正频率半边的镜像。于是 ADC 频谱通常只画：

```text
0 到 Fs/2
```

这就是 single-sided spectrum。

注意逻辑顺序：

```text
采样 -> 频谱以 Fs 为周期
选 [-Fs/2, Fs/2] -> 得到一个 centered two-sided 周期
实数信号 -> 正负频率共轭对称
只保留 [0, Fs/2] -> single-sided spectrum
```

#### 4.6 Single-sided 幅度和功率为什么要补偿

对一个幅度为 `A` 的余弦：

```text
x[n] = A cos(2π m n / N)
```

用复指数展开：

```text
x[n] = A/2 * exp(+j 2π m n / N)
     + A/2 * exp(-j 2π m n / N)
```

所以 two-sided spectrum 里，普通 AC 正频率和负频率各拿到一半幅度：

```text
+m bin -> A/2
-m bin -> A/2
```

如果 single-sided spectrum 只保留正频率，就要把普通 AC bin 的幅度乘 2：

```text
single-sided amplitude = 2 * |X[k]| / N
```

如果用功率谱理解，则正负两边各有一半功率，single-sided 时要把普通 AC bin 的功率加倍：

```text
single-sided power = 2 * two-sided power
```

但是有两个例外。

DC bin：

```text
k = 0
```

DC 没有 `+0` 和 `-0` 两个不同频率，所以不乘 2。

偶数 N 的 Nyquist bin：

```text
k = N/2
f = Fs/2
```

因为：

```text
exp(+j π n) = exp(-j π n) = (-1)^n
```

所以 `+Fs/2` 和 `-Fs/2` 在离散时间里是同一个频率，也不乘 2。

single-sided amplitude 的规则是：

```text
偶数 N：
    k = 0         -> 不乘 2
    k = 1..N/2-1 -> 乘 2
    k = N/2       -> 不乘 2

奇数 N：
    k = 0              -> 不乘 2
    k = 1..floor(N/2)  -> 乘 2
```

这也是为什么 `exp_s00_fft_fundamentals.py` 值得先跑一遍：它专门展示 raw two-sided
FFT 怎样变成 single-sided amplitude spectrum，并展示 DC / Nyquist bin 的特殊性。

### 5. Spectral leakage 和 window

前面已经从 DFT 周期延拓解释了 leakage：

```text
coherent sampling
-> N 点窗口首尾可以无缝周期延拓
-> 主频能量集中在对应 bin 或很窄的主瓣里
```

```text
non-coherent sampling
-> N 点窗口首尾不能无缝周期延拓
-> DFT 需要用多个 bin 共同表示输入频率
-> spectral leakage
```

在继续解释 window 之前，需要补三个基础概念：

```text
1. 冲激函数的筛选性质
2. 卷积的定义
3. 冲激和函数卷积 = 平移这个函数
```

#### 5.1 必要基础：冲激函数和卷积

冲激函数 `δ(ω)` 可以先理解成：

```text
一个无限窄、面积为 1 的尖峰
```

它最重要的性质不是“形状”，而是筛选性质：

```text
∫ f(θ) δ(θ - θ0) dθ = f(θ0)
```

意思是：

```text
δ(θ - θ0) 会在积分中只挑出 θ = θ0 这一点的值。
```

所以在频谱里：

```text
δ(ω - ω0)
```

可以理解为：

```text
位于 ω0 的一根理想谱线。
```

例如一个复单音：

```text
x[n] = A e^{jω0 n}
```

它的理想 DTFT 是：

```text
X(e^{jω}) = 2π A δ(ω - ω0)
```

这里的 `2π` 来自 DTFT 的归一化约定。你现在先抓住物理意义：

```text
单音在频域是一根位于 ω0 的冲激谱线。
```

连续卷积定义为：

```text
(f * g)(ω) = ∫ f(θ) g(ω - θ) dθ
```

这个公式可以读成：

```text
对所有 θ：
    取 f(θ)
    取 g(ω - θ)
    相乘
    再累加 / 积分
```

对 window 分析最重要的例子是冲激和函数的卷积。计算：

```text
[δ(· - ω0) * W](ω)
= ∫ δ(θ - ω0) W(ω - θ) dθ
```

利用冲激筛选性质：

```text
∫ δ(θ - ω0) W(ω - θ) dθ
= W(ω - ω0)
```

所以：

```text
δ(ω - ω0) * W(ω) = W(ω - ω0)
```

这条结论非常重要：

```text
冲激和函数卷积，会把这个函数平移到冲激所在的位置。
```

直觉上：

```text
δ(ω - ω0) -> 一个定位点
W(ω)      -> 一个频谱形状
δ * W     -> 把 W 这个形状搬到 ω0
```

如果有多个单音：

```text
X(ω) = A1 δ(ω - ω1) + A2 δ(ω - ω2)
```

那么：

```text
X * W = A1 W(ω - ω1) + A2 W(ω - ω2)
```

也就是说：

```text
每一根谱线都会复制一份 window 频谱形状到自己的频率位置。
```

这就是为什么 ADC 频谱里一个很强的 fundamental 可能通过 window 旁瓣盖住远处小 spur。

这一节继续从数学上解释 window。核心链条是：

```text
有限观测 = 时域乘上一个 analysis window
-> 频域卷积
-> 单音谱线被窗函数频谱展开
-> leakage 的形状由窗函数频谱决定
-> 时域边界越平滑，远处旁瓣通常越低
-> 代价是主瓣变宽、幅度和噪声需要校正
```

#### 5.2 有限截取为什么可以建模成 rectangular window

先澄清一个容易误会的点：

```text
乘 window 不是把 DFT “变成连续傅里叶变换”。
采样本身也不等于乘 rectangular window。
```

真实计算仍然是 N 点 DFT / FFT：

```text
Y[k] = sum_{n=0}^{N-1} y[n] e^{-j2πkn/N}
```

我们引入 DTFT，是为了分析“这 N 点 DFT 究竟在采样什么频谱形状”。更准确地说：

```text
先把有限观测写成 y[n] = x[n] w[n]
再看 y[n] 的 DTFT: Y(e^{jω})
最后 N 点 DFT 等于在 ω_k = 2πk/N 上采样这个 DTFT
```

也就是：

```text
Y[k] = Y(e^{jω}) |_{ω = 2πk/N}
```

所以本节用 DTFT 不是替代 DFT，而是为了看清楚 DFT bin 背后的连续频率响应。
更严谨地说，本节讨论的是：

```text
无限长离散序列 x[n]
-> 只截取其中 N 点用于 FFT
```

这个“只截取 N 点”的观测动作，才等价于乘一个 rectangular observation mask。
不是说 ADC 采样动作本身等价于乘窗，也不是说 DFT 算法内部偷偷多乘了一次窗。

为什么这个 rectangular mask 不是凭空多出来的？看 DFT 的求和范围：

```text
Y[k] = sum_{n=0}^{N-1} x[n] e^{-j2πkn/N}
```

这个式子也可以完全等价地写成：

```text
Y[k] = sum_{n=-∞}^{∞} x[n] r_N[n] e^{-j2πkn/N}
```

其中：

```text
r_N[n] = 1,  0 <= n <= N-1
       = 0,  otherwise
```

所以 `r_N[n]` 不是新增的物理操作，而是求和上下限 `0 <= n <= N-1` 的另一种写法。
在有限向量内部，乘 `ones(N)` 的确什么都没改变；在无限序列分析视角里，`r_N[n]`
表达的是：

```text
N 点内参与分析
N 点外不参与分析
```

这就是“有限观测”的数学指示函数。

理想无限长离散信号的频谱可以用 DTFT 表示：

```text
X(e^{jω}) = sum_{n=-∞}^{∞} x[n] e^{-jωn}
```

但进入 FFT 的通常只有有限的 N 点：

```text
x[0], x[1], ..., x[N-1]
```

如果把这 N 点看成从某个无限长离散信号中截取出来的观测片段，那么这个截取动作
可以写成把无限长信号乘上一个长度为 N 的 analysis mask/window：

```text
y[n] = x[n] w[n]
```

如果你说“不显式加 window”，更准确的意思是：

```text
在截取 N 点之外，不再额外乘 Hann / Blackman / flattop 等 taper window。
```

这时用于描述“有限截取”的隐含 observation mask 是 rectangular：

```text
w_R[n] = 1,  0 <= n <= N-1
       = 0,  otherwise
```

所以：

```text
不显式加 taper window
= 只做有限截取
= 用 rectangular mask 描述这个有限观测
```

这里最容易误解的一点是：

```text
“理想单音在频域是一根谱线”
```

这句话说的是无限长单音的 DTFT；或者说，在有限 DFT 里，它必须刚好 coherent，
落在某一个 DFT basis 上，才会只出现在一个 bin。

如果频率不是整数 bin，例如：

```text
x[n] = A e^{j2π(10.3)n/N}
```

那么它不是第 10 个 DFT 基底：

```text
e^{j2π10n/N}
```

也不是第 11 个 DFT 基底：

```text
e^{j2π11n/N}
```

而是处在两个 DFT basis 之间。N 点 DFT 只能用这 N 个固定基底去表示这段有限序列，
所以它必须把这个非整数周期的有限片段分解到多个 bin 上：

```text
non-coherent finite record
-> not exactly one DFT basis vector
-> needs many DFT basis vectors
-> many nonzero FFT bins
```

从频域卷积角度看，同一件事就是：

```text
无限长单音谱线 δ(ω - ω0)
经过有限截取，也就是乘上 rectangular observation window w_R[n]
-> 频域 δ(ω - ω0) * W_R(e^{jω})
-> 得到平移后的 Dirichlet kernel
```

如果 coherent，FFT bin 刚好采到 Dirichlet kernel 的中心峰和其它零点，所以看起来
只有一个 bin；如果 non-coherent，FFT bin 不再采到那些零点，于是多个 bin 都有值。

因此更准确地说：

```text
不是“只有额外加 window 才有 leakage”；
而是“只要把无限信号截成有限 N 点去分析，就可以等价建模为乘了一个 observation window”。

不显式加 taper window -> rectangular observation window -> 仍然会 leakage
显式加 Hann/Blackman/... -> 把 rectangular 改成其它 window -> 改变 leakage 的形状
```

这和本库代码直接对应。在 `python/src/adctoolbox/spectrum/compute_spectrum.py` 中：

```python
window_vector, window_gain, equiv_noise_bw_factor = _create_window(win_type, N)
data_windowed = data_normalized * window_vector
```

而 `window_vector` 来自 `python/src/adctoolbox/spectrum/_window.py` 的
`_create_window(win_type, N)`。例如：

```text
win_type='rectangular' -> window_vector = ones(N)
win_type='hann'        -> scipy.signal.windows.hann(N, sym=False)
win_type='blackman'    -> scipy.signal.windows.blackman(N, sym=False)
win_type='flattop'     -> scipy.signal.windows.flattop(N, sym=False)
```

也就是说，`analyze_spectrum(..., win_type="hann")` 的第一步并不是神秘算法，
而是：

```text
把输入数据逐点乘上 Hann window。
```

那么显式选择 Hann、Blackman、flattop 这些 taper window 的目的是什么？

```text
目的不是“让原本没有 leakage 的东西产生 leakage”，
而是改变有限观测已经带来的 leakage 形状。
```

因为后面会看到：

```text
单音在 FFT 图上的扩散形状 = window 的频谱形状
```

选择不同 window，就是选择不同的频谱分析核：

```text
rectangular
-> 主瓣窄，旁瓣高

Hann / Blackman
-> 主瓣宽，旁瓣低
```

所以 window 的工程目的可以说成：

```text
用可控的主瓣/旁瓣形状，改善 signal / spur / noise 的分类可靠性。
```

#### 5.3 时域相乘为什么对应频域卷积

设：

```text
y[n] = x[n] w[n]
```

那么：

```text
Y(e^{jω}) = sum_n y[n] e^{-jωn}
          = sum_n x[n] w[n] e^{-jωn}
```

现在不直接引用性质，而是从逆 DTFT 推一次。

DTFT 的逆变换是：

```text
x[n] = (1 / 2π) ∫_{-π}^{π} X(e^{jθ}) e^{jθn} dθ
```

代入 `Y(e^{jω})`：

```text
Y(e^{jω})
= sum_n w[n] e^{-jωn}
  * [(1 / 2π) ∫_{-π}^{π} X(e^{jθ}) e^{jθn} dθ]
```

把求和和积分交换顺序：

```text
Y(e^{jω})
= (1 / 2π) ∫_{-π}^{π} X(e^{jθ})
   [sum_n w[n] e^{-j(ω - θ)n}]
   dθ
```

括号里的求和正是 `w[n]` 的 DTFT，只是频率变量变成了 `ω - θ`：

```text
sum_n w[n] e^{-j(ω - θ)n}
= W(e^{j(ω - θ)})
```

因此：

```text
Y(e^{jω})
= (1 / 2π) ∫_{-π}^{π} X(e^{jθ}) W(e^{j(ω - θ)}) dθ
```

这就是频域卷积：

```text
Y(e^{jω})
= (1 / 2π) X(e^{jω}) * W(e^{jω})
```

所以：

```text
x[n] w[n]
<->
(1 / 2π) X(e^{jω}) * W(e^{jω})
```

这里的 `*` 表示在 `[-π, π]` 周期频率上的卷积：

```text
X * W
= ∫_{-π}^{π} X(e^{jθ}) W(e^{j(ω - θ)}) dθ
```

所以 window 的数学本质是：

```text
时域乘窗 = 频域卷积
```

这句话是理解所有 window 现象的根。

对应到 N 点 DFT，也可以说：

```text
长度 N 的时域逐点相乘
<-> 长度 N 的 DFT 频域循环卷积
```

但为了理解 leakage、主瓣和旁瓣，使用 DTFT 视角更直观，因为它能看到 DFT bin
之间连续的窗函数频谱形状。

#### 5.4 单音为什么会变成 window 的频谱形状

考虑一个复单音：

```text
x[n] = A e^{jω0 n}
```

它的理想频谱是一根冲激：

```text
X(e^{jω}) = 2π A δ(ω - ω0)
```

乘窗后：

```text
Y(e^{jω})
= (1 / 2π) [2π A δ(ω - ω0)] * W(e^{jω})
= A W(e^{j(ω - ω0)})
```

这说明：

```text
单音乘窗后的频谱形状
= window 的频谱 W(e^{jω}) 平移到单音频率 ω0 附近
```

所以 FFT 图里一个单音周围出现的主瓣、旁瓣，本质上不是正弦信号自己“长成那样”，
而是 window 的频谱形状被搬到了单音频率附近。

#### 5.5 Rectangular window 的频谱和 leakage 公式

Rectangular window：

```text
w_R[n] = 1, 0 <= n <= N-1
```

它的 DTFT 是一个等比数列：

```text
W_R(e^{jω})
= sum_{n=0}^{N-1} e^{-jωn}
```

求和得：

```text
W_R(e^{jω})
= e^{-jω(N-1)/2} * sin(Nω/2) / sin(ω/2)
```

幅度是：

```text
|W_R(e^{jω})|
= |sin(Nω/2) / sin(ω/2)|
```

这个形状叫 Dirichlet kernel，可以把它理解成离散时间里的 sinc-like 形状。

它的零点来自：

```text
sin(Nω/2) = 0
```

所以：

```text
Nω/2 = mπ
ω = 2πm / N
```

第一个零点在：

```text
ω = ±2π / N
```

换成 FFT bin，就是：

```text
rectangular window 的主瓣 null-to-null 宽度约 2 bins
```

这就是 rectangular 的优点：

```text
主瓣窄 -> 频率分辨率好
```

但 rectangular 的边界有硬跳变：

```text
0 -> 1
1 -> 0
```

因此频谱旁瓣高，第一旁瓣约为：

```text
-13.26 dB
```

这就是 rectangular 的缺点：

```text
旁瓣高 -> 强 fundamental 的远处 leakage 可能盖住小 spur
```

#### 5.6 Coherent 时 rectangular 为什么看起来没有 leakage

N 点 DFT 是在这些频率点采样 DTFT：

```text
ω_k = 2π k / N
```

如果单音刚好 coherent，落在第 `m` 个 bin：

```text
ω0 = 2π m / N
```

那么第 `k` 个 FFT bin 看到的是：

```text
W_R(ω_k - ω0)
= W_R(2π(k - m) / N)
```

当 `k != m` 时：

```text
sin(N * [2π(k - m) / N] / 2)
= sin(π(k - m))
= 0
```

也就是说：

```text
coherent + rectangular
-> 其它 bin 正好采到 rectangular window 频谱的零点
-> 看起来能量只集中在一个 bin
```

如果 non-coherent，例如：

```text
ω0 = 2π * 10.3 / N
```

那么 FFT bin 不再刚好采到这些零点，window 频谱的旁瓣会被采出来，于是出现 leakage。

#### 5.7 主瓣和旁瓣是什么

现在可以严格定义前面一直提到的两个词。

对一个单音乘窗后的频谱：

```text
Y(e^{jω}) = A W(e^{j(ω - ω0)})
```

`W` 在中心频率附近最大。中心峰到两侧第一个零点之间的主要区域叫：

```text
main lobe，主瓣
```

主瓣外侧的一串较小峰值叫：

```text
side lobes，旁瓣
```

它们的工程意义：

```text
主瓣宽度
-> 决定一个单音占多少 bin
-> 决定能不能分开相邻频率

旁瓣高度
-> 决定强信号泄漏到远处频率的强度
-> 影响小 spur 是否会被 fundamental leakage 盖住
```

因此：

```text
主瓣窄 -> 频率分辨率好
旁瓣低 -> 远处 leakage 小，适合看小 spur
```

但这两个目标通常冲突。

#### 5.8 平滑性为什么降低旁瓣

从时域看，rectangular window 在边界处不连续：

```text
w_R[n] 从 0 突然跳到 1，再从 1 突然跳回 0
```

这种边界跳变会让频域尾部衰减慢。直觉规律是：

```text
边界越硬、越不连续
-> 需要越多高频成分描述这个突变
-> 旁瓣越高，下降越慢
```

Hann window 形如：

```text
w_H[n] = 0.5 - 0.5 cos(2πn / N)
```

本库使用的是 SciPy 的 periodic Hann：

```python
windows.hann(N, sym=False)
```

它让窗口两端平滑接近 0，降低周期延拓边界的硬跳变。频域结果是：

```text
旁瓣更低，下降更快
```

但它也会带来代价：

```text
主瓣变宽
```

#### 5.9 为什么 Hann 的主瓣会变宽

Hann 可以看成 rectangular window 和余弦权重的组合。频域上，它近似等价于几个
移位的 rectangular-window 频谱相加：

```text
W_H(ω)
≈ 0.5 W_R(ω)
  - 0.25 W_R(ω - 2π/N)
  - 0.25 W_R(ω + 2π/N)
```

这个公式的直觉是：

```text
几个 Dirichlet kernel 组合
-> 旁瓣处发生抵消
-> 旁瓣降低
-> 主瓣附近被展开
-> 主瓣变宽
```

典型数值可以先记住：

| window | null-to-null 主瓣宽度 | 第一旁瓣 | ENBW |
|---|---:|---:|---:|
| rectangular | 约 2 bins | 约 -13.26 dB | 1.00 bins |
| Hann | 约 4 bins | 约 -31.5 dB | 1.50 bins |
| Blackman | 约 6 bins | 更低 | 约 1.73 bins |
| Blackman-Harris | 更宽 | 很低 | 约 2.00 bins |
| Flattop | 很宽 | 较低 | 约 3.77 bins |

这些 ENBW 数值和本库 `_window.py` 的默认参数一致：

```text
rectangular:    enbw = 1.00
hann:           enbw = 1.50
blackman:       enbw = 1.73
blackmanharris: enbw = 2.00
flattop:        enbw = 3.77
```

#### 5.10 一个具体例子：N=64，频率落在 10.3 bin

设：

```text
N = 64
x[n] = cos(2π * 10.3 * n / 64)
```

它不是 coherent，因为频率在：

```text
10.3 bin
```

不是整数 bin。

对复单音来说，第 `k` 个 FFT bin 的幅度近似由 window 频谱决定：

```text
|Y[k]| ∝ |W(2π(10.3 - k) / N)|
```

也就是说：

```text
FFT 每个 bin 读到的值
= window 频谱在不同频率偏移处的采样
```

对 rectangular window，归一化幅度响应可以写成：

```text
H_R(δ)
= |sin(πδ) / (N sin(πδ/N))|
```

其中：

```text
δ = 真实频率与某个 FFT bin 的距离，单位是 bin
```

如果真实频率刚好落在两个 bin 中间：

```text
δ = 0.5
```

大 N 时：

```text
H_R(0.5)
≈ |sin(π/2) / (π/2)|
= 2/π
≈ 0.637
```

换成 dB：

```text
20 log10(0.637) ≈ -3.92 dB
```

这就是 rectangular window 的 scalloping loss：

```text
单音不在 bin center 时，最大 bin 会低估幅度。
```

Hann 的主瓣更宽，但主瓣顶部更平一些，所以最坏幅度低估约为：

```text
约 -1.42 dB
```

因此：

```text
rectangular:
    bin-centered 时非常准
    bin-between 时最大 bin 幅度低估明显

Hann:
    远处旁瓣更低
    scalloping loss 更小
    但主瓣更宽，需要合并更多 bin
```

#### 5.11 Window 的 shortcoming

Window 不是消除 leakage，而是重新分配 leakage。数学上，它用不同的 `W(e^{jω})`
去卷积原始频谱。工程上，它用更低的远处旁瓣，换来更宽的主瓣，以及更复杂的幅度和
噪声标定。

主要代价有四个。

##### 5.11.1 主瓣变宽：频率分辨率下降

前面已经看到：

```text
单音乘窗后的频谱 = A W(e^{j(ω - ω0)})
```

所以一个单音在频谱中占多宽，直接由 `W(e^{jω})` 的主瓣宽度决定。

更平滑的 window 会降低远处旁瓣，但通常会让主瓣变宽：

```text
rectangular:
    主瓣窄，旁瓣高

Hann / Blackman / Blackman-Harris:
    主瓣更宽，旁瓣更低
```

这意味着：

```text
两个靠得近的频率更难分开。
```

在 ADC 频谱里，这会影响：

```text
fundamental 和附近 spur 是否能分开
harmonic 和附近 spur 是否能分开
side_bin 应该合并多少 bin
```

这也是为什么 window 选择和 `side_bin` 必须一起考虑。

##### 5.11.2 Coherent gain：window 会缩小单音幅度

假设有一个 coherent 复单音：

```text
x[n] = A e^{j2πm n/N}
```

乘窗后：

```text
y[n] = A w[n] e^{j2πm n/N}
```

看第 `m` 个 DFT bin：

```text
Y[m] = sum_{n=0}^{N-1} y[n] e^{-j2πm n/N}
```

代入：

```text
Y[m]
= sum_{n=0}^{N-1} A w[n] e^{j2πm n/N} e^{-j2πm n/N}
= A sum_{n=0}^{N-1} w[n]
```

如果不加 window，也就是 rectangular：

```text
sum_n w[n] = N
Y[m] = A N
```

所以常见 FFT 幅度归一化会除以 `N`。但一般 window 下：

```text
Y[m] / N = A * (sum_n w[n] / N)
```

这说明 window 会把 coherent 单音幅度缩小一个因子：

```text
CG = (1 / N) * sum_n w[n]
```

这个因子叫 coherent gain。

例如：

```text
rectangular: CG = 1
Hann:        CG ≈ 0.5
```

这和本库 `_create_window` 中的：

```python
window_gain = np.sum(window_vector) / N
```

直接对应。

如果不做 coherent gain 校正：

```text
Hann-windowed coherent sine 的中心 bin 幅度会大约低 6 dB
```

因为：

```text
20 log10(0.5) ≈ -6.02 dB
```

注意：实际 `analyze_spectrum` 里通常会把主瓣多个 bin 合并为 signal power，
所以不要把“中心 bin 高度”直接等同于最终 `sig_pwr_dbfs`。

##### 5.11.3 ENBW：window 会改变白噪声落入每个 bin 的功率

先从 ENBW 的定义出发。ENBW 是 equivalent noise bandwidth，等效噪声带宽。
它不是主瓣宽度，也不是两个零点之间的宽度，而是这样定义的：

```text
找一个理想矩形滤波器，
让它的峰值增益等于当前 window 分析滤波器的峰值增益，
让它通过的白噪声功率等于当前 window 分析滤波器通过的白噪声功率。

这个理想矩形滤波器的宽度，就是 ENBW。
```

为什么这里会出现“滤波器”和“带宽”？因为 DFT 的第 `k` 个 bin 可以写成：

```text
Y[k] = sum_n x[n] w[n] e^{-jω_k n}
```

其中：

```text
ω_k = 2πk / N
```

这可以理解成两步：

```text
1. 乘 e^{-jω_k n}，把 ω_k 附近的成分搬到 DC
2. 用 w[n] 做有限长度加权求和
```

所以第 `k` 个 bin 不是一个无限窄的频率点，而是一个以 `ω_k` 为中心的分析滤波器。
这个滤波器的频率响应形状是：

```text
H_k(e^{jω}) = W(e^{j(ω - ω_k)})
```

也就是说：

```text
FFT bin 的频率选择性由 window 的频谱 W 决定。
```

对单音，我们关心这个滤波器在中心频率的幅度增益：

```text
H_k(e^{jω_k}) = W(e^{j0}) = sum_n w[n]
```

所以 coherent 单音幅度和：

```text
sum_n w[n]
```

有关。这就是上一节的 coherent gain。

对白噪声则不同。白噪声不是集中在一个频率点，而是在整个频率轴上有平坦的功率谱密度。
因此一个 bin 收到多少白噪声，取决于这个分析滤波器的功率响应面积：

```text
noise power passed by bin k
∝ ∫_{-π}^{π} |H_k(e^{jω})|^2 dω
```

由于 `H_k(e^{jω})` 只是 `W(e^{jω})` 的频移，平移不改变面积：

```text
∫ |H_k(e^{jω})|^2 dω
= ∫ |W(e^{jω})|^2 dω
```

所以白噪声功率看的是：

```text
window 频谱的功率面积
```

而不是只看中心峰高度。

用 Parseval 定理，可以把频域面积转回时域：

```text
(1 / 2π) ∫_{-π}^{π} |W(e^{jω})|^2 dω
= sum_n w[n]^2
```

这就是为什么噪声功率会和 `sum(w[n]^2)` 有关。

设输入噪声为零均值白噪声：

```text
E[v[n]^2] = σ^2
E[v[n]v[m]] = 0, n != m
```

乘窗后：

```text
y[n] = v[n] w[n]
```

某个 DFT bin 的噪声项：

```text
Y[k] = sum_n v[n] w[n] e^{-j2πkn/N}
```

噪声功率期望中，交叉项因为不相关而消失，只剩：

```text
E[|Y[k]|^2] = σ^2 sum_n w[n]^2
```

这和上面的频域解释是同一件事：

```text
时域推导 -> 噪声功率和 sum(w^2) 有关
频域推导 -> 噪声功率和 ∫|W|^2 dω 有关
Parseval  -> 二者等价
```

现在定义 ENBW。滤波器的中心增益是：

```text
W(e^{j0}) = sum_n w[n]
```

功率增益峰值是：

```text
|W(e^{j0})|^2 = (sum_n w[n])^2
```

频域功率面积是：

```text
∫ |W(e^{jω})|^2 dω
```

所以以 rad/sample 为单位的 ENBW 是：

```text
B_ENBW
= [∫_{-π}^{π} |W(e^{jω})|^2 dω] / |W(e^{j0})|^2
```

利用 Parseval：

```text
B_ENBW
= [2π sum_n w[n]^2] / (sum_n w[n])^2
```

一个 FFT bin 的频率间隔是：

```text
Δω = 2π / N
```

所以把 ENBW 换成“多少个 FFT bin”的单位：

```text
ENBW_bins
= B_ENBW / Δω
= [2π sum_n w[n]^2 / (sum_n w[n])^2] / (2π / N)
= N * sum_n w[n]^2 / (sum_n w[n])^2
```

这就是常用 ENBW 公式：

```text
ENBW = N * sum_n w[n]^2 / (sum_n w[n])^2
```

也就是本库 `_create_window` 中的：

```python
equiv_noise_bw_factor = N * np.sum(window_vector**2) / (np.sum(window_vector)**2)
```

例如：

```text
rectangular: ENBW = 1.00 bins
Hann:        ENBW ≈ 1.50 bins
Flattop:     ENBW ≈ 3.77 bins
```

含义是：

```text
如果用 coherent gain 把单音幅度标定到同一标准，
Hann window 的每个 FFT bin 接收的白噪声功率，
相当于 rectangular window 的约 1.5 个 bin。
```

到这里需要把三个量分清楚：

```text
coherent 单音中心 bin：
    由中心增益 sum(w) 决定
    如果只用中心 bin 估计功率，会涉及 window_gain^2

主瓣合并后的单音总功率：
    由 windowed waveform 的平均平方 mean(w^2) 决定
    mean(w^2) = window_gain^2 * ENBW

白噪声每个 bin 的期望功率：
    与 sum(w^2) 有关
    也就是与 window 的功率响应面积有关
```

因此不要把代码里的：

```text
1 / (window_gain^2 * ENBW)
```

理解成“两次功率校正”。更准确地说：

```text
window_gain:
    描述 W(0)，也就是分析滤波器中心高度

ENBW:
    描述 ∫|W|^2 / |W(0)|^2
    也就是功率面积相对于中心高度平方的等效宽度

window_gain^2 * ENBW:
    = mean(w^2)
    描述 window 对总功率的 RMS 缩放
```

##### 5.11.3b ENBW 的另一面：noise floor 为什么有的光滑、有的全是毛刺

跑实验 3（`exp_s08_windowing_deep_dive.py`）的 non-coherent 场景时，会看到一个现象：
同一个信号，换不同 `win_type`，**noise floor 的视觉光滑度差别非常大**。
Hann / Blackman / Flattop 的 noise floor 像一条平滑的带子，而 rectangular 和
Hamming 的 noise floor 全是上下跳动的毛刺。这和 SNR/NSD 指标几乎无关（同样 window
下 NSD 都在 -154 dBFS/Hz 附近），纯粹是频谱"长相"的差异。

这个差异不是 bug，也不是图渲染问题，而是 ENBW 的另一个直接后果。前面把 ENBW
理解成"power correction 的一个参数"，但它在频谱形状上还有第二个角色。

先回忆一个事实：对零均值白噪声做 N 点 FFT，单个 bin 的功率是一个随机变量，
服从指数分布。这个分布有一个麻烦的性质：

```text
std(power_per_bin) ≈ mean(power_per_bin)
```

也就是说，单个 bin 的功率天然波动就和均值差不多大，换算成 dB 大约是 5-6 dB 的
bin-to-bin 波动。所以真正的白噪声 FFT 看起来本来就应该是锯齿状的直线，不是平的。

那为什么 ENBW 大的 window 看起来会光滑？因为第 k 个 FFT bin 实际上是一个以
ω_k 为中心的分析滤波器：

```text
H_k(e^{jω}) = W(e^{j(ω - ω_k)})
```

相邻 bin 的滤波器主瓣会有重叠，重叠多少由 window 的主瓣宽度决定。ENBW 正是描述
这个重叠程度的一个等效宽度（注意它不是主瓣 null-to-null 宽度，是功率等效宽度，
但二者强相关）：

```text
ENBW = 1.0 (rectangular)
    -> 相邻 bin 的滤波器主瓣几乎不重叠
    -> 每个 bin 收集的是近似独立的 noise 样本
    -> bin-to-bin 不相关
    -> noise floor 全是毛刺

ENBW = 1.5 (Hann)
    -> 相邻 bin 主瓣显著重叠
    -> 相邻 bin 收集的 noise 高度相关
    -> bin-to-bin 平滑
    -> noise floor 较光滑

ENBW = 3.77 (flattop)
    -> 好几个相邻 bin 的主瓣都重叠
    -> 每个 bin 实际上混合了约 3.77 个独立 noise 样本
    -> noise floor 非常平滑，看起来像一条画出来的线
```

换句话说，**ENBW > 1 在频域上相当于做了滑动平均**。ENBW 越大，平均窗口越宽，
noise floor 视觉上越平滑。这和 5.11.3 里 power correction 的角色是同一件事的
两面：

```text
5.11.3 的角色：
    每个 bin 收到的白噪声功率 ∝ sum(w^2) ∝ ENBW
    -> 影响 noise 功率绝对值，所以 power_correction 要除掉它

本节的角色：
    相邻 bin 收到的白噪声样本相关性 ∝ 主瓣重叠 ∝ ENBW
    -> 影响 noise floor 的视觉方差，所以 ENBW 大的看起来光滑
```

对应到本库代码，这条性质直接来自 `_window.py` 的 `equiv_noise_bw_factor`：

```python
equiv_noise_bw_factor = N * np.sum(window_vector**2) / (np.sum(window_vector)**2)
```

`exp_s08_windowing_deep_dive.py` 的 8 个 window，ENBW 从小到大大致是：

```text
rectangular:    ENBW = 1.00   -> noise floor 全是毛刺
hamming:        ENBW ≈ 1.36   -> 仍然毛刺（且远处旁瓣不衰减，另有 leakage 干扰）
hann:           ENBW ≈ 1.50   -> 较光滑
blackman:       ENBW ≈ 1.73   -> 光滑
blackmanharris: ENBW ≈ 2.00   -> 光滑
flattop:        ENBW ≈ 3.77   -> 最光滑，像画出来的线
```

肉眼数子图的光滑度，和这个 ENBW 排序几乎完全一致。

这里有一个容易上当的工程陷阱：

```text
noise floor 看起来光滑 ⟹ 测量更准？
```

不。光滑只是 ENBW 平均效应的视觉效果。Flattop 把约 3.77 个独立 noise 样本平均
进了一个 bin，方差降了，但频率分辨率也降了（5.11.1：主瓣变宽 -> 分辨率下降）。
所以同样这段数据：

```text
Flattop:     noise 光滑，但两个靠近的 spur 分不开
rectangular: noise 毛刺，但频率分辨率最好
```

这也是为什么实验 3 场景 3（short FFT, N=128）里，主瓣宽的 window ENOB 反而虚高。
主瓣宽的 window 会把 fundamental 附近多个 noise bin 平均进 signal 主瓣的合并范围
（`sig_bin_start:sig_bin_end`，见 5.12），让 noise 估计偏低，SNR/SNDR 虚高。
N 越小、bin 数越少，这个效应越明显。

一句话总结这一节：

```text
ENBW 不只参与 power correction，
它还决定了相邻 bin 的相关性，因而决定了 noise floor 的视觉光滑度。
光滑 ⟹ 频率分辨率下降，不光滑 ⟹ 分辨率好但需要更多 bin 平均才能降方差。
```

##### 5.11.4 Power correction：本库怎样把 window 影响纳入功率谱标定

本库在 `compute_spectrum.py` 中这样做：

```python
power_correction = _calculate_power_correction(window_gain, equiv_noise_bw_factor)
power_spectrum = power_spectrum * power_correction
```

而 `_calculate_power_correction(...)` 的公式是：

```text
power_correction = 4 / (window_gain^2 * ENBW)
```

把 `window_gain` 和 `ENBW` 展开：

```text
window_gain = sum(w) / N
ENBW = N * sum(w^2) / (sum(w))^2
```

所以：

```text
window_gain^2 * ENBW
= [sum(w)^2 / N^2] * [N * sum(w^2) / sum(w)^2]
= sum(w^2) / N
= mean(w^2)
```

因此：

```text
power_correction
= 4 / mean(w^2)
```

这说明本库的功率谱校正也可以理解成：

```text
先按 window RMS power 做归一化，
再乘 one-sided / dBFS 风格标定中的 4。
```

这在代码层面意味着：

```text
window_gain 和 ENBW 是两个 window 参数；
它们的乘积刚好等于 mean(w^2)；
代码用这个乘积做一次 window RMS power normalization。
```

如果只看 coherent 单音的中心 bin，那么中心 bin 的幅度确实由 `window_gain` 决定；
如果看白噪声，每个 bin 的噪声功率确实和 `sum(w^2)` 有关。但本库这里不是分别对
signal 和 noise 做两套校正，而是先把整个 `power_spectrum` 标定到同一个功率尺度。

因此这里真正的逻辑是：

```text
raw windowed power spectrum
-> 乘 4 / mean(w^2)
-> 得到统一 dBFS 风格的 calibrated power spectrum
-> 再按 bins 分类为 signal / noise / harmonic / spur
```

其中：

```text
4
```

来自本库对 one-sided FFT power / dBFS 风格的 plotspec 标定约定。源码注释里也说明：

```text
The correction is equivalent to applying the window with RMS normalization
and then multiplying the one-sided FFT power by 4.
```

所以这里不要把 `4` 单独理解成 window 的数学性质；它是本库 power spectrum
归一化方式的一部分，和 single-sided / dBFS 风格标定有关。

用 Hann coherent sine 可以看出为什么不能把“中心 bin 校正”和“主瓣总功率校正”混在一起：

```text
Hann:
    window_gain = 0.5
    ENBW = 1.5
    mean(w^2) = 0.375

中心 bin power 校正:
    用 4 / window_gain^2

主瓣合并 power 校正:
    用 4 / mean(w^2)
    = 4 / (window_gain^2 * ENBW)
```

本库计算 `sig_pwr_dbfs` 时合并 fundamental 主瓣多个 bin，所以采用后者。

这和 `compute_spectrum.py` 中的变量命名直接对应：

```python
sig_linear = float(np.sum(power_spectrum[sig_bin_start:sig_bin_end]))
sig_pwr_linear = sig_linear
sig_pwr_dbfs = 10 * np.log10(max(sig_pwr_linear, 1e-30))
sig_peak = float(power_spectrum[fundamental_bin])
```

这里有两个不同的量：

```text
sig_peak:
    校正后的 fundamental center bin power
    仍然只是中心 bin 高度

sig_linear / sig_pwr_linear:
    校正后的 fundamental 主瓣合并功率
    由 fundamental_bin ± side_bin 的 power sum 得到
```

因此代码没有先用 `window_gain` 单独恢复 `sig_peak`，再用 `ENBW` 再恢复一次。
它的实际流程是：

```text
1. _create_window(...)
   -> 计算 window_gain = sum(w)/N
   -> 计算 ENBW = N*sum(w^2)/sum(w)^2

2. _calculate_power_correction(...)
   -> 组合成 4/(window_gain^2 * ENBW)
   -> 等价于 4/mean(w^2)

3. power_spectrum *= power_correction
   -> 全谱只标定一次

4. sig_linear = sum(fundamental main-lobe bins)
   -> 用 side_bin 合并主瓣得到 signal power
```

也就是说：

```text
window_gain:
    在代码里不是单独乘到 signal 上的校正器；
    它只是参与构造 mean(w^2) 的一个 window 参数。

ENBW:
    在代码里也不是第二次校正器；
    它和 window_gain^2 相乘后，给出 window RMS power。
```

后续指标使用这两个 signal 量时也有差别：

```text
SNR / SNDR:
    使用 sig_linear，也就是主瓣合并后的 signal power。

SFDR / harmonic dBc / THD dBc:
    当前 plotspec-style 实现使用 sig_peak 作为参考。
```

这个差别是代码当前的工程约定，后面学习 SFDR、THD 时需要单独注意。

把这一段压缩成代码链，就是：

```text
_create_window(...)
-> window_vector
-> window_gain = sum(w) / N
-> equiv_noise_bw_factor = N * sum(w^2) / sum(w)^2

compute_spectrum(...)
-> data_windowed = data_normalized * window_vector
-> power_spectrum = FFT power of data_windowed
-> power_correction = 4 / (window_gain^2 * ENBW)
-> power_spectrum *= power_correction
```

后面所有 signal、noise、spur、harmonic 的分类都基于这个已经标定过的
`power_spectrum`。真正需要小心的是 `side_bin` 是否把主瓣收全，以及不同指标到底使用
`sig_linear` 还是 `sig_peak`。

#### 5.12 side_bin 和 window 主瓣的代码对应

因为 window 会让单音能量分布在一个主瓣范围内，计算 fundamental power 时不能总是只拿
一个 bin。

本库在 `compute_spectrum.py` 中：

```python
sig_bin_start = max(fundamental_bin - side_bin, 0)
sig_bin_end = min(fundamental_bin + side_bin + 1, n_inband)
sig_linear = sum(power_spectrum[sig_bin_start:sig_bin_end])
```

也就是说：

```text
side_bin = 1
-> 合并 fundamental 左右各 1 个 bin

side_bin = 3
-> 合并 fundamental 左右各 3 个 bin
```

注意：当前 `compute_spectrum.py` 调用的是 `_calculate_harmonic_power_plotspec(...)`。
这个 plotspec-style 路径下，harmonic power 不是按 `center ± side_bin` 合并，
而是取 harmonic center bin 的单 bin power：

```python
p = float(power_spectrum[h_bin])
```

这里 `side_bin` 主要用于判断 harmonic 是否和 fundamental / DC 区域碰撞：

```python
if abs(h_bin - fundamental_bin) <= 2 * side_bin:
    collided_harmonics.append(harmonic_order)
    continue
if h_bin <= side_bin:
    continue
```

所以当前实现里要区分：

```text
fundamental signal power:
    用 side_bin 合并主瓣

harmonic power / THD:
    plotspec-style 下取 harmonic center bin
    side_bin 主要用于 collision 判断
```

noise 估计时，本库一定会把 DC 附近 bins 和 fundamental 主瓣排除掉。harmonic 的
处理取决于 `nf_method`：

```text
排除 DC 附近 bins
排除 fundamental_bin ± side_bin

nf_method = 0/1/2:
    median / trimmed 等统计方式估计 noise，不显式排除 harmonic 主瓣

nf_method = 3:
    exclude 方法中排除 harmonic center bin

nf_method = 4:
    legacy wide exclude 中排除 harmonic_bin ± side_bin
```

所以 `side_bin` 的工程意义是：

```text
告诉分析器：这个 window 下，单音主瓣大约占多少 bin。
```

如果 `side_bin` 太小：

```text
主瓣没收全
-> 一部分 signal / harmonic 被误算成 noise 或 spur
-> SNR / SNDR / SFDR 可能偏差
```

如果 `side_bin` 太大：

```text
附近真实 spur 被吞进 fundamental 或 harmonic
-> SFDR 可能虚高
```

本库 `_window.py` 中有 coherent 默认值，例如：

```text
rectangular:    coherent side_bin = 0
hann:           coherent side_bin = 1
blackman:       coherent side_bin = 2
blackmanharris: coherent side_bin = 3
flattop:        coherent side_bin = 4
```

当 `side_bin=None` 时，`compute_spectrum.py` 会调用 `_detect_side_bin_auto(...)`
尝试根据窗口和谱形自动检测；但代码注释也强调：

```text
Non-coherent captures must pass a larger side_bin explicitly.
```

也就是说，对真实 non-coherent 测试数据，不能盲目信任一个固定默认值。

#### 5.13 本阶段先记住的公式链

这一节的核心可以压缩成四条。

第一，有限观测和 window：

```text
y[n] = x[n] w[n]
```

```text
Y(e^{jω}) = (1 / 2π) X(e^{jω}) * W(e^{jω})
```

第二，单音的 leakage 形状：

```text
x[n] = A e^{jω0n}
Y(e^{jω}) = A W(e^{j(ω - ω0)})
单音的 leakage 形状 = window 频谱 W 的形状
```

第三，window tradeoff：

```text
rectangular:
    主瓣窄，频率分辨率好
    旁瓣高，远处 leakage 严重

Hann / Blackman / Blackman-Harris:
    边界更平滑
    旁瓣更低
    主瓣更宽
    需要更大的 side_bin

Flattop:
    幅度测量更稳
    主瓣很宽
```

第四，ADCToolbox 代码对应：

```text
win_type
-> 选择 window_vector
-> 选择 W(e^{jω}) 的主瓣/旁瓣形状

window_gain = sum(w) / N
-> W(0)/N，window 频率响应中心高度

equiv_noise_bw_factor = N * sum(w^2) / sum(w)^2
-> ENBW，功率面积相对中心高度平方的等效宽度

power_correction = 4 / (window_gain^2 * ENBW)
                 = 4 / mean(w^2)
-> 全谱只做一次 window RMS power normalization

side_bin
-> fundamental 主瓣合并范围
-> harmonic collision / noise exclusion 边界
```

### 6. 功率、dB 和 dBFS

功率比转 dB：

```text
dB = 10 log10(P1 / P2)
```

幅度比转 dB：

```text
dB = 20 log10(A1 / A2)
```

ADC 频谱指标通常基于功率，所以 SNR / SNDR / THD / SFDR 都是在比较频谱能量。

`dBFS` 表示相对于 full-scale 的功率或幅度标尺。使用 `analyze_spectrum` 时，
`max_scale_range` 会影响 full-scale 归一化参考：

```text
max_scale_range=None         -> 自动根据数据估计 full-scale 参考
max_scale_range=[-0.5, 0.5]  -> 明确指定 full-scale range
max_scale_range=[0.0, 1.0]   -> 常见归一化单端 ADC 范围
```

如果 full-scale 参考不一致，`sig_pwr_dbfs`、`noise_floor_dbfs`、`nsd_dbfs_hz`
这些 dBFS 量就不适合直接比较。

### 7. 动态指标

设：

```text
P_signal   = fundamental power
P_noise    = noise power excluding DC, fundamental, harmonics
P_harm     = harmonic distortion power
P_spur_max = largest non-signal spur power
```

则：

```text
SNR  = 10 log10(P_signal / P_noise)
SNDR = 10 log10(P_signal / (P_noise + P_harm))
THD  = 10 log10(P_harm / P_signal)
SFDR = 10 log10(P_signal / P_spur_max)
ENOB = (SNDR - 1.76) / 6.02
```

关键区别：

```text
SNR  -> 只看随机噪声，不把 harmonic distortion 算进去
SNDR -> 同时看噪声和失真
THD  -> 只看 harmonic distortion
SFDR -> 只看最大单个 spur
ENOB -> 由 SNDR 换算，所以噪声和失真都会影响它
```

这解释了一个常见现象：

```text
THD 变差时，SNDR / ENOB 可能变差；
但 SNR 不一定变差。
```

### 8. NSD 和 OSR

NSD 是 noise spectral density，噪声谱密度：

```text
dBFS/Hz
```

它的核心不是“另一个 SNR 写法”，而是把：

```text
某个带宽内的总噪声功率
```

换成：

```text
每 1 Hz 带宽内平均有多少噪声功率
```

所以要先区分两个量：

```text
noise_power_total:
    在某个带宽 BW 内积分得到的总噪声功率

noise_spectral_density:
    每 Hz 的噪声功率密度
```

如果噪声在带宽内近似是白噪声，也就是噪声谱密度近似平坦，那么：

```text
P_noise_total = NSD_linear * BW
```

换成 dB：

```text
P_noise_total_dBFS = NSD_dBFS_Hz + 10log10(BW)
```

因此：

```text
NSD_dBFS_Hz = P_noise_total_dBFS - 10log10(BW)
```

这就是“把总噪声摊到每 Hz”的数学含义。

SNR 则是信号功率和这个总噪声功率的比：

```text
SNR_dB = P_signal_dBFS - P_noise_total_dBFS
```

所以：

```text
P_noise_total_dBFS = P_signal_dBFS - SNR_dB
```

代入 NSD 公式：

```text
NSD_dBFS_Hz
= P_noise_total_dBFS - 10log10(BW)
= P_signal_dBFS - SNR_dB - 10log10(BW)
```

反过来，如果已知 NSD：

```text
P_noise_total_dBFS = NSD_dBFS_Hz + 10log10(BW)
SNR_dB = P_signal_dBFS - P_noise_total_dBFS
```

也就是：

```text
SNR_dB = P_signal_dBFS - NSD_dBFS_Hz - 10log10(BW)
```

这解释了两个指标的分工：

```text
SNR:
    关心某个指定带宽内，信号比总噪声大多少。

NSD:
    关心噪声本身的密度，把带宽因素除掉。
```

所以 NSD 更适合比较不同采样率、不同 OSR、不同分析带宽下的噪声水平。

如果使用 oversampling，`osr` 会改变等效噪声带宽：

```text
BW = fs / (2 * osr)
```

这里要特别区分两个概念：

```text
Nyquist bandwidth:
    fs / 2
    这是采样后离散频谱的可表示范围。

in-band bandwidth:
    fs / (2 * osr)
    这是动态指标计算时真正统计 noise / distortion 的目标信号带宽。
```

所以 OSR 不是让 FFT 频谱只能到 `fs/(2*osr)`，也不是让 ADC 的 Nyquist 频率变小。
FFT 频谱仍然可以画到：

```text
fs / 2
```

OSR 的作用是告诉分析器：

```text
我的目标信号带宽只占 Nyquist 带宽的一部分；
计算 SNR / SNDR / NSD / ENOB 等 in-band 指标时，只统计 0 ~ fs/(2*osr)。
```

从定义上：

```text
osr = fs / (2 * BW_signal)
```

所以：

```text
BW_signal = fs / (2 * osr)
```

`osr=1` 时，默认分析整个 Nyquist 带宽：

```text
BW = fs / 2
```

如果 `osr=4`：

```text
BW = fs / 8
```

对于同样的白噪声密度 `NSD`，积分带宽变小，总噪声功率也会变小：

```text
P_noise_total = NSD_linear * BW
```

所以 SNR 会提高：

```text
BW 变成原来的 1/osr
-> 总噪声功率降低 10log10(osr)
-> SNR 提高 10log10(osr)
```

注意：这是对白噪声、并且只统计 in-band noise 的情况成立。OSR 不是让噪声物理消失，
而是把评价带宽缩小，或者在 ADC 系统中配合滤波/抽取，只关心较窄信号带宽内的噪声。

一个直观例子：

```text
fs = 1 MHz
Nyquist bandwidth = 500 kHz

如果目标信号带宽 BW_signal = 125 kHz：
    osr = fs / (2 * BW_signal)
        = 1 MHz / (2 * 125 kHz)
        = 4

FFT 仍然可以显示 0 ~ 500 kHz；
但 in-band 指标只统计 0 ~ 125 kHz。
```

和本库 `compute_spectrum.py` 对应：

```python
n_inband = rfft_inband_bin_count(N, osr)
freq = np.arange(len(power_spectrum)) * (fs / N)
```

这里：

```text
freq:
    仍然覆盖 rFFT 的完整频率轴，也就是 0 ~ fs/2。

n_inband:
    根据 osr 计算 in-band bin 数量；
    后续 fundamental search、noise sum、spur search 等动态指标只看 spectrum[:n_inband]。
```

`rfft_inband_bin_count(N, osr)` 内部的核心逻辑是：

```python
edge_bin = N / (2 * osr)
count = floor(edge_bin) + 1
```

对应频率边界：

```text
f_edge = edge_bin * fs / N = fs / (2 * osr)
```

NSD 的计算也使用同一个 in-band bandwidth：

```python
noise_floor_dbfs = sig_pwr_dbfs - snr_dbc

nsd_dbfs_hz = (
    noise_floor_dbfs - 10 * np.log10(fs / (2 * osr))
    if np.isfinite(noise_floor_dbfs)
    else np.nan
)
```

这里：

```text
noise_floor_dbfs
```

不是“每个 FFT bin 的噪声底”，而是：

```text
in-band total noise power in dBFS
```

然后：

```text
noise_floor_dbfs - 10log10(BW)
```

才得到：

```text
dBFS/Hz
```

本库中常见转换工具：

```python
from adctoolbox import snr_to_nsd, nsd_to_snr

nsd = snr_to_nsd(snr_db=80, fs=1e6, osr=1)
snr = nsd_to_snr(nsd_dbfs_hz=nsd, fs=1e6, osr=1)
```

学习时先抓住：

```text
SNR:
    signal power / in-band total noise power

NSD:
    in-band total noise power / BW

OSR:
    改变 BW = fs / (2 * osr)
    因而改变同一 NSD 下积分出来的 total noise
```

## 电路需要理解什么

### 1. SNR 差通常意味着随机噪声

如果频谱里没有特别突出的 harmonic 或 spur，但 noise floor 整体偏高，常见来源包括：

- thermal noise
- sampling capacitor kT/C noise
- comparator input-referred noise
- reference noise
- clock jitter
- 测试仪器或输入源噪声

这些问题通常表现为：

```text
noise floor 上升
SNR 下降
SNDR 和 ENOB 也跟着下降
```

### 2. THD 差通常意味着确定性非线性

如果二次、三次或更高次 harmonic 很明显，常见来源包括：

- sampling switch nonlinear
- input buffer / amplifier nonlinear
- CDAC capacitor mismatch
- reference settling nonlinear
- comparator kickback
- clipping 或输入幅度过大

这些问题通常表现为：

```text
harmonics 变高
THD 变差
SNDR / ENOB 下降
SNR 不一定下降
```

### 3. SFDR 差说明有突出的单个 spur

SFDR 只关心最大那个非信号 spur。这个 spur 可能是 harmonic，也可能不是 harmonic。

常见来源包括：

- capacitor mismatch
- time-interleaving offset / gain / skew mismatch
- clock spur
- reference ripple
- 电源或输入源干扰
- 数字耦合

所以 SFDR 差时，不要只问“噪声大不大”，而要先找：

```text
最大 spur 在哪个频率？
它是不是 harmonic？
它会不会随 Fin、Fs、温度、电源或输入幅度移动？
```

### 4. Jitter 与输入频率相关

jitter-limited SNR 近似为：

```text
SNR_jitter = -20 log10(2π Fin σt)
```

所以同样的 clock jitter，在高输入频率下更差。输入频率每翻倍，jitter 限制的 SNR
大约下降 6 dB。

本库对应工具：

```python
from adctoolbox import calculate_jitter_limit

snr_jitter = calculate_jitter_limit(freq=Fin, jitter_rms_sec=50e-15)
```

#### 4.1 公式是怎么推出来的：从时刻偏移到电压误差

上面那条公式不是经验拟合，而是可以一步步推出来的。把它拆开之后，"为什么高频
更敏感"和"为什么 SNR 与信号幅度无关"这两件事会同时变清楚。

设理想采样时刻是 `t[n] = n/Fs`，有 jitter 时实际采样时刻偏移了随机量 `δt[n]`：

```text
t_actual[n] = n/Fs + δt[n]
```

`δt[n]` 是零均值随机变量，标准差 `σt` 就是数据手册里的 aperture jitter。三个关键
假设：`δt[n]` 在不同 n 之间不相关（白噪声假设）、和信号不相关、`2π·Fin·δt[n] << 1`
（小抖动）。

输入单音正弦：

```text
x(t) = A·sin(2π·Fin·t)
```

有 jitter 的采样值：

```text
x_jit[n] = A·sin(2π·Fin·(n/Fs + δt[n]))
         = A·sin(2π·Fin·n/Fs + 2π·Fin·δt[n])
```

对小角度 `ε`，`sin(θ+ε) ≈ sin(θ) + ε·cos(θ)`，所以：

```text
x_jit[n] ≈ A·sin(2π·Fin·n/Fs) + A·cos(2π·Fin·n/Fs) · 2π·Fin·δt[n]
          = x[n]               + Δx[n]
```

其中 jitter 引起的电压误差：

```text
Δx[n] = A·cos(2π·Fin·n/Fs) · 2π·Fin·δt[n]
      = (dx/dt)|_{t=n/Fs} · δt[n]
```

**这一行就是 jitter 的物理本质**：电压误差 = 信号在该时刻的斜率 × 时间偏移。
信号变化越快（高频 / 大幅度），同一时刻偏移造成的电压差越大。这就解释了为什么
高频输入对 jitter 更敏感——不是 jitter 变大了，而是信号的 `dx/dt` 大了。

误差功率（用 `δt[n]` 和余弦独立，乘积方差 = 方差相乘；以及 `mean(cos²) = 1/2`）：

```text
E[(Δx)²] = E[(A·cos(·))²] · E[(2π·Fin·δt)²]
         = (A²/2) · (2π·Fin)² · σt²

noise_rms_jitter = (A/√2) · 2π·Fin · σt
                 = signal_rms · 2π·Fin · σt
```

所以：

```text
SNR_jitter = signal_rms / noise_rms_jitter
           = signal_rms / (signal_rms · 2π·Fin · σt)
           = 1 / (2π·Fin · σt)
```

`signal_rms = A/√2` 在分子分母同时出现，约掉了。换 dB：

```text
SNR_jitter_dB = -20·log10(2π·Fin·σt)
```

这条推导里有一个工程上很重要的副产物：**SNR_jitter 和信号幅度 A 无关**。这是
jitter 和 thermal noise 的本质区别——增大信号幅度能压过 thermal / quantization
噪声，但压不过 jitter。所以实验 5 用固定 A=0.5 就能直接测出 SNR_jitter，不需要
扫幅度；也所以高速 RF ADC 即使输入很大，SNR 也被时钟死死锁住。

| 噪声源 | noise_rms | SNR 与幅度的关系 |
|---|---|---|
| thermal noise | σ_thermal（固定）| SNR ∝ A |
| quantization | LSB/√12（固定）| SNR ∝ 2^N |
| **jitter** | **signal_rms · 2π·Fin·σt** | **SNR 与 A 无关** |

#### 4.2 jitter 噪声在频谱上长什么样：fundamental 两侧的裙边

公式只给了 SNR 一个数字，没说 jitter 噪声在频谱里长什么样。但这是判断"频谱上
鼓起来的部分到底是不是 jitter"的关键诊断特征。

回到电压误差那一行：

```text
Δx[n] = A·cos(2π·Fin·n/Fs) · 2π·Fin·δt[n]
```

它是一个**确定性单音乘上一个宽带白噪声**。用 5.3 节"时域相乘 = 频域卷积"展开。
余弦的 DTFT 是两根冲激谱线（5.1 节）：

```text
cos(2π·Fin·n/Fs)  ⟷  π·δ(ω - ωin) + π·δ(ω + ωin)
```

白噪声 `δt[n]` 的 DTFT 近似平坦：

```text
δt[n]  ⟷  G(e^{jω}) ≈ 平坦
```

卷积时用到冲激的筛选性质（5.1 节）：

```text
G(e^{jω}) * δ(ω - ω0) = G(e^{j(ω - ω0)})
```

冲激就像一个定位锚：它位于哪里，G 就整体平移到哪里。所以两份白噪声分别被搬移
到 +Fin 和 -Fin：

```text
ΔX(e^{jω}) = 0.5·G(e^{j(ω - ωin)}) + 0.5·G(e^{j(ω + ωin)})
              ↑                        ↑
              搬到 +Fin                 搬到 -Fin
```

这是通信里"调制 = 频移"的同一件事：把一个基带噪声搬到载波附近。在 ADC 里，
jitter 把时钟的相位噪声搬到了输入信号频率附近。

只看一根冲激的卷积，结果还是平坦的。所以 jitter 在频谱上看起来不是"只在 Fin 一个
bin 有值"，而是 fundamental 两侧抬起来形成"裙边"或"肩膀"。三个因素决定裙边的
具体形状：

```text
1. 真实时钟的 δt 不是严格白噪声
   -> close-in phase noise 在低频偏移更强
   -> G(e^{jω}) 本身在 0 频附近抬升
   -> 搬到 ±Fin 后，fundamental 正下方最厚，远处衰减

2. 有限 N 点 FFT 等价于乘 window
   -> 实际看到的是 G(e^{jω}) * W(e^{jω})
   -> window 主瓣和旁瓣让裙边进一步展开（5.2-5.6 节）

3. fundamental 主瓣（window leakage）和搬来的 jitter 噪声在 Fin 附近叠加
   -> Fin 周围几个 bin 是两者的混合
```

合起来，jitter 主导时的频谱形状大致是：

```text
                            裙边（jitter 噪声）
                            ↙   ↓   ↘
                          /    /│\    \
  ____                    /   / │ \   \                    ____
  flat \                /   /  │  \   \                 /  flat
   noise\______________/   /   │   \   \_______________/ noise
         0                Fin   │   -Fin               Fs/2
```

远处是纯白噪声（平坦的 NSD），Fin 附近因为 jitter 被搬过来而抬升。这是 jitter
主导的判据：

```text
thermal / quantization 主导 -> 整段 noise floor 平坦
jitter 主导                -> fundamental 两侧抬起裙边，远处反而干净
```

实验 5 的 `exp_g04_sweep_jitter_fin.png` 可以直接看到这个形状：每个子图
fundamental 尖峰两侧不是平的，而是有本地抬升；Fin 越大，SNR 越差，裙边也越高。
数据手册里 RF 时钟的 phase noise 曲线，本质就是时域 jitter 在频域的体现。

### 5. 诊断索引：Stage 02 只做第一层判断

上面四类现象在本阶段只需要作为“索引”来理解，不需要一次性把所有电路细节展开。
Stage 02 的任务是先从频谱指标提出假设；Stage 03 开始用 residual 去验证这些假设。

| Stage 02 看到的现象 | 第一层问题 | Stage 03 怎么继续看 | 后续主要展开 |
|---|---|---|---|
| `SNR` 差，noise floor 整体高 | 更像随机噪声，还是被某些 spur 污染？ | 看 residual PDF 是否接近 Gaussian，ACF 是否接近 white，error spectrum 是否没有固定 spur | Stage 03 residual；Stage 04 的 comparator / sampling noise |
| `THD` 差，harmonic 明显 | 失真是否和输入幅度、相位或 code 有确定关系？ | 看 residual spectrum 的 harmonic；看 error by value / phase 是否有结构 | Stage 03 residual；Stage 04 非理想 ADC；Stage 06 calibration |
| `SFDR` 差，有一个突出 spur | 最大 spur 在哪里？它是否随 `Fin`、`Fs` 或测试条件移动？ | 看 error spectrum 是否有固定频率线；再和 phase / value dependency 对照 | Stage 03 residual；Stage 04/06 的 deterministic error |
| 高频输入下 `SNR` 明显变差 | 是否接近 jitter limit？ | residual 可能呈现和输入斜率/相位相关的结构，先用 `calculate_jitter_limit` 做理论边界 | Stage 02 jitter 实验；后续按系统噪声问题继续分析 |

可以把这张表当成后续学习地图：

```text
frequency-domain symptom
-> candidate error class
-> residual view
-> circuit / system source
-> possible calibration or design action
```

## 本库对应代码

核心频谱分析：

```text
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/spectrum/compute_spectrum.py
python/src/adctoolbox/spectrum/plot_spectrum.py
python/src/adctoolbox/spectrum/_window.py
python/src/adctoolbox/spectrum/_harmonics.py
python/src/adctoolbox/spectrum/_estimate_noise_power.py
```

频率工具：

```text
python/src/adctoolbox/fundamentals/frequency.py
```

指标转换：

```text
python/src/adctoolbox/fundamentals/snr_nsd.py
python/src/adctoolbox/fundamentals/units.py
python/src/adctoolbox/fundamentals/metrics.py
```

官方示例：

```text
python/src/adctoolbox/examples/01_basic/exp_b02_coherent_vs_non_coherent.py
python/src/adctoolbox/examples/02_spectrum/
python/src/adctoolbox/examples/03_generate_signals/exp_g04_sweep_jitter_fin.py
python/src/adctoolbox/examples/07_conversions/exp_c05_convert_nsd_snr.py
```

本地学习脚本：

```text
learning/adctoolbox-learning/demos/whole_workflow_demo.py
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

## 对应 API

```python
from adctoolbox import analyze_spectrum
from adctoolbox import find_coherent_frequency
from adctoolbox import snr_to_nsd, nsd_to_snr
from adctoolbox import snr_to_enob, enob_to_snr
from adctoolbox import calculate_jitter_limit
```

最常用入口：

```python
metrics = analyze_spectrum(
    aout,
    fs=fs,
    max_scale_range=[0.0, 1.0],
    win_type="hann",
    create_plot=True,
)
```

`analyze_spectrum` 返回一个 dict，常用字段包括：

```text
enob
sndr_dbc
sfdr_dbc
snr_dbc
thd_dbc
sig_pwr_dbfs
noise_floor_dbfs
nsd_dbfs_hz
```

关键参数先抓住这些：

```text
data            -> 输入 waveform，通常是一维 aout
fs              -> 采样率
osr             -> oversampling ratio，用于噪声带宽
max_scale_range -> full-scale 归一化参考
win_type        -> 窗口类型
side_bin        -> 主频或谐波附近合并多少 bin
max_harmonic    -> THD 统计到第几次谐波
create_plot     -> 是否画频谱图
```

## 实验 0：先看 FFT bin 的原始含义

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s00_fft_fundamentals.py
```

观察控制台输出和图片：

```text
python/src/adctoolbox/examples/02_spectrum/output/exp_s00_fft_fundamentals.png
```

重点看：

- raw two-sided FFT 为什么有正负频率对称。
- single-sided amplitude 为什么要处理 DC 和 Nyquist bin。
- 偶数 N 和奇数 N 的 Nyquist bin 有什么不同。

这个实验不用先懂 ADC，只是让你知道“FFT bin 到底是什么”。

## 实验 1：最小频谱分析

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s01_analyze_spectrum_simplest.py
```

观察控制台输出：

```text
ENoB
SNDR
SFDR
SNR
NSD
```

问自己：

- SNDR 和 SNR 为什么不完全一样？
- SFDR 是看最大 spur，不是看总噪声。
- ENOB 为什么是由 SNDR 换算，而不是由 nominal bit 数直接决定？

## 实验 2：coherent 和 non-coherent 的区别

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\01_basic\exp_b02_coherent_vs_non_coherent.py
```

观察：

- arbitrary frequency 不一定落在整数 bin。
- coherent frequency 会让主频能量更集中。
- `find_coherent_frequency` 返回的是实际用于测试的 `Fin_actual`。

这一步的目标不是追求某个固定指标，而是看懂：

```text
为什么同样是正弦输入，频率是否 coherent 会影响频谱形状。
```

## 实验 3：窗口函数和 leakage

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s08_windowing_deep_dive.py
```

观察输出图片：

```text
python/src/adctoolbox/examples/02_spectrum/output/exp_s08_windowing_1_leakage.png
python/src/adctoolbox/examples/02_spectrum/output/exp_s08_windowing_2_coherent.png
python/src/adctoolbox/examples/02_spectrum/output/exp_s08_windowing_3_short_fft.png
```

重点看：

- rectangular window 对 coherent signal 很直接。
- non-coherent 时 rectangular leakage 严重。
- window 牺牲主瓣宽度，换取旁瓣抑制。
- FFT 点数太少时，频率分辨率会变粗。

## 实验 4：动态范围 sweep

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s04_sweep_dynamic_range.py
```

观察：

- 输入幅度过小，信号功率低，SNR 下降。
- 输入幅度过大，可能 clipping，THD / SFDR 变差。
- 最好的动态指标通常出现在“接近 full-scale 但不过载”的区域。

这一步会把 Stage 01 的 full-scale / clipping 和 Stage 02 的动态指标连起来。

## 实验 5：jitter 对高频输入更致命

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\03_generate_signals\exp_g04_sweep_jitter_fin.py
```

观察输出图片：

```text
python/src/adctoolbox/examples/03_generate_signals/output/exp_g04_sweep_jitter_fin.png
```

重点看：

- jitter RMS 固定时，输入频率越高，SNR 越差。
- 理论值来自 `SNR_jitter = -20 log10(2π Fin σt)`。
- 高频 ADC 里 clock quality 会直接限制动态性能。

## 本阶段代码阅读

建议先读：

```text
python/src/adctoolbox/fundamentals/frequency.py
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/spectrum/compute_spectrum.py
python/src/adctoolbox/spectrum/_window.py
python/src/adctoolbox/spectrum/_harmonics.py
python/src/adctoolbox/spectrum/_estimate_noise_power.py
```

阅读重点：

- `find_coherent_frequency` 怎么把目标频率变成 coherent frequency。
- `analyze_spectrum` 为什么只是 wrapper，核心计算在 `compute_spectrum`。
- fundamental bin 怎么找。
- harmonic bin 怎么折叠到 Nyquist 区间。
- noise bin 怎么排除 DC、fundamental 和 harmonics。
- `enob` 是用 `sndr_dbc` 计算的。

读 `analyze_spectrum` 时，可以只追踪这条逻辑：

```text
输入 waveform
-> compute_spectrum
-> 找 fundamental
-> 找 harmonics
-> 剩下的 bins 估计 noise
-> 汇总 SNR / SNDR / SFDR / THD / ENOB / NSD
-> 可选 plot_spectrum
```

如果你读不懂所有参数，先抓住这些参数：

```text
fs              -> 采样率
osr             -> 过采样比，影响噪声带宽
win_type        -> 窗口类型
side_bin        -> 主频附近合并多少 bin
max_harmonic    -> 统计到第几次谐波
max_scale_range -> full-scale 归一化参考
create_plot     -> 是否画图
```

## 容易混淆的点

- `SNR` 不包含 harmonic distortion；`SNDR` 包含。
- `SFDR` 只看最大的单个 spur，不代表总噪声。
- `ENOB` 是由 `SNDR` 换算来的，所以失真也会拉低 ENOB。
- coherent sampling 不是玄学，它只是让信号能量刚好落在 FFT bin 上。
- window 不是“让结果更好”，而是在 non-coherent 时减少 leakage 带来的误判。
- `max_scale_range` 会影响 dBFS 参考，不应随手乱填。
- `side_bin` 太小可能把主频泄漏算成噪声或 spur。
- DC bias 通常要从动态噪声计算中排除，不应把偏置误当作随机噪声。
- THD 差不一定说明 noise floor 差，SNR 差也不一定说明非线性差。

## 进入 Stage 03 前要带走什么

Stage 02 的核心成果是：

```text
把 aout 的频谱拆成 signal / noise / harmonic / spur / DC。
```

进入 Stage 03 前，你需要能根据频谱指标做第一层判断：

```text
SNR 差
-> 先怀疑随机噪声、jitter、thermal noise、reference noise

THD 差
-> 先怀疑非线性、clipping、CDAC mismatch、reference settling

SFDR 差
-> 先定位最大 spur，再判断它是不是 harmonic 或外部干扰

ENOB 差
-> 不够具体，要继续拆成 SNR / THD / SFDR 看原因
```

Stage 03 会从这个判断继续深入：不只看频谱上的指标，还要看 error、residual、
phase、value dependency，进一步定位误差结构。

一句话版：

```text
Stage 02 负责告诉你“性能坏成什么频谱形状”；
Stage 03 继续追问“这个误差在时域和输入空间里长什么样”。
```

## 阶段检查问题

如果你能回答这些问题，就可以进入 Stage 03：

1. 为什么非相干采样会导致 spectral leakage？
2. `Fin = k * Fs / N` 里的 `k` 同时代表哪两个含义？
3. 为什么 window 会降低旁瓣，但也会让主瓣变宽？
4. 为什么 THD 高会让 SNDR 变差，但不一定让 SNR 变差？
5. SNR、SNDR、SFDR 三者分别对什么问题敏感？
6. 为什么 jitter 对高频输入更致命？
7. 为什么理想 N-bit ADC 的 ENOB 接近 N，但真实 ADC 往往低于 N？
8. `max_scale_range` 填错会影响哪些 dBFS 指标？
9. 如果 ENOB 变差，你会先看 SNR、THD 还是 SFDR？为什么？
