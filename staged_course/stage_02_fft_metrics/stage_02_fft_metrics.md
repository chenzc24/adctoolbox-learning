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

但因为离散时间频谱以 `Fs` 为周期，区间 `[0, Fs)` 和 `[-Fs/2, Fs/2)` 只是同一个
频谱周期的两种排法。

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

其中后半段可以减去一个 `Fs`，解释成负频率：

```text
5Fs/8 = -3Fs/8  (mod Fs)
6Fs/8 = -2Fs/8  (mod Fs)
7Fs/8 = -Fs/8   (mod Fs)
```

所以同一个 FFT 输出也可以解释成 centered two-sided spectrum：

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
工程上常选择 [-Fs/2, Fs/2] 这个周期作为 two-sided spectrum。
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

这一节继续从数学上解释 window。核心链条是：

```text
时域乘窗
-> 频域卷积
-> 单音谱线被窗函数频谱展开
-> leakage 的形状由窗函数频谱决定
-> 时域边界越平滑，远处旁瓣通常越低
-> 代价是主瓣变宽、幅度和噪声需要校正
```

#### 5.1 有限 FFT 本质上一定乘了 window

理想无限长离散信号的频谱可以用 DTFT 表示：

```text
X(e^{jω}) = sum_{n=-∞}^{∞} x[n] e^{-jωn}
```

但计算机只能拿到有限的 N 点：

```text
x[0], x[1], ..., x[N-1]
```

这等价于把无限长信号乘上一个长度为 N 的窗函数：

```text
y[n] = x[n] * w[n]
```

如果你说“不加 window”，实际使用的是 rectangular window：

```text
w_R[n] = 1,  0 <= n <= N-1
       = 0,  otherwise
```

所以：

```text
不加 window = 乘 rectangular window
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

#### 5.2 时域相乘为什么对应频域卷积

设：

```text
y[n] = x[n] w[n]
```

那么：

```text
Y(e^{jω}) = sum_n y[n] e^{-jωn}
          = sum_n x[n] w[n] e^{-jωn}
```

DTFT 的基本性质是：

```text
x[n] w[n]
<->
(1 / 2π) X(e^{jω}) * W(e^{jω})
```

这里 `*` 表示频域卷积：

```text
Y(e^{jω})
= (1 / 2π) ∫_{-π}^{π} X(e^{jθ}) W(e^{j(ω - θ)}) dθ
```

所以 window 的数学本质是：

```text
时域乘窗 = 频域卷积
```

这句话是理解所有 window 现象的根。

#### 5.3 单音为什么会变成 window 的频谱形状

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

#### 5.4 Rectangular window 的频谱和 leakage 公式

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

#### 5.5 Coherent 时 rectangular 为什么看起来没有 leakage

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

#### 5.6 主瓣和旁瓣是什么

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

#### 5.7 平滑性为什么降低旁瓣

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

#### 5.8 为什么 Hann 的主瓣会变宽

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

#### 5.9 一个具体例子：N=64，频率落在 10.3 bin

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

#### 5.10 Window 的 shortcoming

Window 不是消除 leakage，而是重新分配 leakage。主要代价有四个。

第一，主瓣变宽：

```text
两个靠得近的频率更难分开
```

第二，幅度需要校正。window 会降低单音的平均幅度，校正因子叫 coherent gain：

```text
CG = (1 / N) * sum_n w[n]
```

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

第三，噪声带宽会改变。等效噪声带宽：

```text
ENBW = N * sum_n w[n]^2 / (sum_n w[n])^2
```

这和本库 `_create_window` 中的：

```python
equiv_noise_bw_factor = N * np.sum(window_vector**2) / (np.sum(window_vector)**2)
```

直接对应。

第四，功率谱需要校正。本库在 `compute_spectrum.py` 中这样做：

```python
power_correction = _calculate_power_correction(window_gain, equiv_noise_bw_factor)
power_spectrum = power_spectrum * power_correction
```

而 `_calculate_power_correction(...)` 的公式是：

```text
power_correction = 4 / (window_gain^2 * ENBW)
```

这对应本库 `_window.py` 中：

```python
return 4 / (window_gain**2 * equiv_noise_bw_factor)
```

它把 window 带来的幅度缩放和噪声带宽影响纳入 dBFS 风格的功率谱标定。

#### 5.11 side_bin 和 window 主瓣的代码对应

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

harmonic power 也使用类似逻辑，在 `_harmonics.py` 中按 harmonic bin 的
`center ± side_bin` 合并。

noise 估计时，本库会把 DC、fundamental 主瓣、harmonic 主瓣排除掉。对应
`_estimate_noise_power.py` 中的逻辑：

```text
排除 DC 附近 bins
排除 fundamental_bin ± side_bin
排除 harmonic_bin ± side_bin
剩余 bins 用来估计 noise
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

#### 5.12 本阶段先记住的公式链

完整逻辑可以压缩成：

```text
y[n] = x[n] w[n]
```

```text
Y(e^{jω}) = (1 / 2π) X(e^{jω}) * W(e^{jω})
```

对单音：

```text
x[n] = A e^{jω0n}
```

有：

```text
Y(e^{jω}) = A W(e^{j(ω - ω0)})
```

所以：

```text
单音的 leakage 形状 = window 的频谱形状
```

Rectangular window：

```text
W_R(e^{jω}) = e^{-jω(N-1)/2} * sin(Nω/2) / sin(ω/2)
```

因此：

```text
rectangular:
    主瓣窄，频率分辨率好
    旁瓣高，远处 leakage 严重
    coherent 时其它 bin 正好采到零点

Hann / Blackman / Blackman-Harris:
    边界更平滑
    旁瓣更低
    主瓣更宽
    需要更大的 side_bin

Flattop:
    幅度测量更稳
    主瓣很宽
```

对应到 ADCToolbox：

```text
win_type
-> 选择 window_vector，也就是选择 W(e^{jω}) 的主瓣/旁瓣形状

window_gain
-> coherent gain，用于幅度/功率校正

equiv_noise_bw_factor
-> ENBW，用于噪声带宽/功率校正

side_bin
-> 决定 fundamental / harmonic 主瓣附近多少 bin 被合并或排除
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

NSD 是 noise spectral density：

```text
dBFS/Hz
```

它把总噪声归一化到带宽上，更适合比较不同采样率或带宽下的噪声。

如果使用 oversampling，`osr` 会改变等效噪声带宽：

```text
BW = fs / (2 * osr)
```

本库中常见转换工具：

```python
from adctoolbox import snr_to_nsd, nsd_to_snr

nsd = snr_to_nsd(snr_db=80, fs=1e6, osr=1)
snr = nsd_to_snr(nsd_dbfs_hz=nsd, fs=1e6, osr=1)
```

学习时先抓住：

```text
SNR 是某个带宽内的总噪声比；
NSD 是把这个噪声摊到每 Hz 后的密度。
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
