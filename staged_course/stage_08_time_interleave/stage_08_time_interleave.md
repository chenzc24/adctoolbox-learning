# Stage 08：Time-Interleaved ADC（时间交织 ADC）的失配与校准

## 本阶段如何承接 Stage 00–07

Stage 04–07 全部围绕**单通道 SAR ADC**：

```text
vin -> sar_convert(vin, weights) -> bits -> reconstruct/calibrate
```

其中唯一的失配来源是 CDAC capacitor mismatch（bit weight error）。校准做的事是：

```text
从 bits 估计 digital weights，让 bits @ weights 更接近真实输入。
```

但真实的高速 ADC（GS/s 量级）几乎都不是单通道转换，而是**多个子 ADC 交替采样**，
这叫 Time-Interleaved ADC（TI-ADC）。比如 4 个 250 MS/s 的子 ADC 交织成 1 GS/s。

TI-ADC 引入了一类**全新的、单通道里不存在的失配**：

```text
offset mismatch   每个通道的 DC 偏置不同
gain mismatch     每个通道的增益不同
skew mismatch     每个通道的采样时刻不精确等间隔
```

这些失配不是 CDAC 权重错误，而是在**通道间**产生的。它们在频谱上形成的位置、
需要用到的校准方法，都和 SAR bit-weight 校准完全不同。

这一阶段就讲清楚：

```text
TI 失配是什么；
它在频谱上长什么样（这是和单通道最不一样的地方）；
怎么从输出反推失配；
怎么校准。
```

## 本阶段目标

学完本阶段，你应该能解释：

- TI-ADC 为什么需要多个子 ADC 交织，交织后采样率怎么算。
- offset / gain / skew 三类失配分别在哪产生 spur。
- 为什么 TI spur 的位置是 `k·fs/M` 和 `fin ± k·fs/M`，而不是输入谐波。
- 怎么用单音正弦 + DFT 相量法从输出提取每通道的 offset/gain/skew。
- foreground 校准和 background 校准的区别。
- TI 校准和 SAR bit-weight 校准在数学结构上的相似与不同。
- 怎么验证 TI 校准效果（和 Stage 07 的思路一致）。

## 初学者先抓住的主线

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

```text
deinterleave(x, M=4) -> (4, N/4) 的矩阵，每行是一个通道的连续样本
```

如果 M 个通道**完全一致**，交织后的输出就和一个真正的 `fs` 采样器没区别。
但真实通道总有 offset / gain / skew 差异，这些差异在交织后变成周期性的调制，
调制频率是 `fs/M`，于是在频谱上产生 TI spur。

## TI 失配在频谱上的位置（最重要的知识点）

这是 TI-ADC 和单通道 ADC 最不一样的地方，也是这一阶段的核心。

### 1. offset mismatch → spur 在 k·fs/M

如果每个通道有不同的 DC 偏置 `offset_m`，那么交织后的输出相当于：

```text
x[n] = signal(n) + offset_{n mod M}
```

这里要特别小心一个直觉误区：**每个通道自己的 offset 是常数**，不是随时间变化。
但是交织后的总输出每个采样点轮流来自不同通道，所以总误差序列变成：

```text
e[0] = offset_0
e[1] = offset_1
...
e[M-1] = offset_{M-1}
e[M] = offset_0
e[M+1] = offset_1
...
```

也就是：

```text
e[n] = offset_{n mod M}
```

从单个通道看，它是常数；从交织后的整体采样流看，它是一个**以 M 个样本为周期**
重复的序列。这个周期性误差就是 offset spur 的来源。

把这个 M 点周期序列写成离散傅里叶级数：

```text
e[n] = Σ_{k=0}^{M-1} C_k · exp(j·2π·k·n/M)
```

其中 `k=0` 是平均 offset，也就是 DC；`k=1..M-1` 是通道间 offset 差异造成的
周期分量。因为数字频率 `k/M` cycles/sample 对应模拟频率：

```text
f_k = k · fs / M
```

所以 offset mismatch 产生的 spur 固定在：

```text
fs/M, 2fs/M, ..., (M-1)fs/M
```

注意：**这些 spur 的位置只由 M 和 fs 决定，和输入频率 fin 无关**。
输入换一个频率，offset spur 还在原地。这是 offset spur 的判别特征。

为什么不是 `fs/(M·k)`？因为 `fs/(M·k)` 对应的是 `M·k` 个样本才重复一次的周期。
而 TI offset pattern 是每 M 个样本重复一次，所以它的基频是 `fs/M`，
更高的 Fourier 分量是这个基频的整数倍 `k·fs/M`，不是分数倍。

对 M=4, fs=1 GHz：

```text
offset spur 在 250 MHz, 500 MHz, 750 MHz
```

### 2. gain + skew mismatch → spur 在 fin ± k·fs/M

如果每个通道的增益或采样时刻不同，那么交织后是对 signal 的**幅度/相位调制**，
调制频率同样是 fs/M。调制产生的边带出现在信号频率两侧：

```text
fin ± fs/M, fin ± 2fs/M, ..., fin ± (M-1)fs/M
```

（折叠到 Nyquist 内）。所以 gain/skew spur 的位置**依赖 fin**：输入换频率，
这些 spur 跟着移动。这是 gain/skew spur 的判别特征。

用时域相乘、频域卷积可以把这个位置严格推出来。先只看 gain mismatch。设交织后的
通道增益序列为：

```text
a[n] = gain_{n mod M}
```

它同样是 M 点周期序列，所以可以展开为：

```text
a[n] = Σ_{k=0}^{M-1} C_k · exp(j·2π·k·n/M)
```

若输入是一个实数单音：

```text
s[n] = A · cos(ω0 n)
     = A/2 · exp(jω0 n) + A/2 · exp(-jω0 n)

ω0 = 2π · fin / fs
```

gain mismatch 后：

```text
y[n] = a[n] · s[n]
```

代入傅里叶级数：

```text
y[n]
= A/2 · Σ C_k · exp(j(ω0 + 2πk/M)n)
 + A/2 · Σ C_k · exp(j(-ω0 + 2πk/M)n)
```

因此频率分量出现在：

```text
f =  fin + k·fs/M
f = -fin + k·fs/M
```

换成常见写法就是：

```text
fin ± k·fs/M
```

最后再折叠到 Nyquist 频带内。

从频域卷积角度看，是同一件事：

```text
periodic gain sequence a[n]  ->  频谱在 k·fs/M 上有离散线
input sine s[n]              ->  频谱在 ±fin 上有离散线
time-domain multiply         ->  frequency-domain convolution
```

卷积会把 `±fin` 这两根谱线平移到 `±fin + k·fs/M`，所以产生边带。

skew 和 gain 在一阶近似下可以合并：skew 等价于一个频率相关的复数增益
`alpha_m = gain_m · exp(j·2π·fin·skew_m)`。这是因为对复单音：

```text
s(t + skew_m)
= exp(j·2π·fin·(t + skew_m))
= exp(j·2π·fin·t) · exp(j·2π·fin·skew_m)
```

所以每个通道的 skew 等价于给该通道乘上一个相位因子。小 skew 时：

```text
exp(j·2π·fin·skew_m) ≈ 1 + j·2π·fin·skew_m
```

这也说明 skew spur 的严重程度会随 `fin` 增大而增大。代码里 `predict_spurs`
把 gain 和 skew 一起处理成 "gain_skew" spur，就是利用了这个“频率相关复数增益”
的近似。

### 3. 实测验证（exp_ti01）

exp_ti01 用 M=4, fs=1 GHz, fin≈17 MHz，注入三类失配：

```text
gain spread   = 3.96% peak-to-peak
offset spread = 10.39 mV peak-to-peak
skew spread   = 5.20 ps peak-to-peak
```

未校准频谱上你能看到：

```text
offset spur 在 250 / 500 / 750 MHz（固定，与 fin 无关）
gain/skew spur 在 17 ± 250 = -233/267 MHz（折叠后），17 ± 500 MHz 等
```

未校准 SFDR 由这些 TI spur 主导，远比量化噪声底高。

### 4. 一张对照表：TI spur vs 单通道 harmonic

| | 单通道 ADC | TI-ADC |
|---|---|---|
| 失配来源 | CDAC bit weight error | offset/gain/skew 通道间差 |
| spur 位置 | fin 的整数倍（2fin, 3fin）| k·fs/M 和 fin±k·fs/M |
| spur 是否随 fin 移动 | 是（跟随 fin）| offset spur 不动，gain/skew spur 动 |
| 校准对象 | digital bit weights | per-channel offset/gain/skew |
| 校准数学 | B @ w ≈ sine（最小二乘）| DFT 相量拟合 / 后台盲搜索 |

**最关键的区别**：单通道的 spur 是输入的谐波（跟着 fin 走），
TI 的 spur 是采样结构的周期性调制产物（钉在 fs/M 的网格上）。
看到 spur 在 fs/M 整数倍上，基本可以判定是 TI 失配，不是模拟非线性。

## 怎么从输出反推失配：DFT 相量法

给定一段交织输出 `x`（单音正弦输入），`extract_mismatch_sine` 做的事：

```text
1. deinterleave(x, M) 拆成 M 个通道
2. 对每个通道，用 DFT 在已知 fin 处求相量：
     phasor_m = (2/K) Σ (y - offset_m) · exp(-j·2π·fin·t)
3. offset_m = 通道样本的均值（DC）
4. gain_m = |phasor_m| 的相对值（均值归一为 1）
5. skew_m = 相位残差 / (2π·fin)（去掉整体延迟后）
```

### 1. 先拆通道：把一个交织流变回 M 条低速流

`deinterleave(x, M)` 的结果是：

```text
channels[m, k] = x[k·M + m]
```

也就是说，第 `m` 个通道的第 `k` 个样本，在总采样流里的原始 sample index 是：

```text
n = k·M + m
```

所以它的绝对采样时间是：

```text
t_m[k] = (k·M + m) / fs
```

源码里正是这样写的：

```python
t = (k * M + m) * T
```

这里不能只用每个子通道自己的局部时间 `k / (fs/M)`。因为通道 0、1、2、...
本来就错开了 `1/fs` 的理想采样相位；如果不用绝对时间，理想交织相位会被误认为
通道 skew。

### 2. 每个通道看到的是同一个正弦的不同版本

对第 `m` 个通道，可以把样本近似写成：

```text
y_m[k]
= offset_m
 + A_m · cos(2π·fin·t_m[k] + φ_m)
```

这里：

```text
offset_m  -> 通道 DC 偏置
A_m       -> 通道看到的正弦幅度，反映 gain mismatch
φ_m       -> 通道相位，包含共同输入相位 + 该通道 skew 引入的相位
```

如果第 `m` 个通道有采样时刻偏差 `skew_m`，那么：

```text
φ_m = φ_common + 2π·fin·skew_m
```

所以只要能估计出每个通道在 `fin` 处的幅度和相位，就能得到 gain 和 skew。

### 3. offset：通道均值

代码先取每个通道的均值：

```python
offsets[m] = y.mean()
```

在相干采样、正弦覆盖完整周期时：

```text
mean(cos(...)) ≈ 0
```

所以：

```text
mean(y_m) ≈ offset_m
```

如果输入不是相干采样，或者记录太短、只覆盖半个周期，正弦本身的平均值不再接近 0，
offset 提取就会被污染。

### 4. DFT 相量：在已知 fin 处投影

去掉 offset 后，对每个通道计算：

```text
P_m = (2/K) · Σ_k (y_m[k] - offset_m) · exp(-j·2π·fin·t_m[k])
```

代码对应：

```python
phasors[m] = (2.0 / K) * np.sum(
    (y - offsets[m]) * np.exp(-1j * 2 * np.pi * fin * t)
)
```

为什么这个相量能给出幅度和相位？令：

```text
y_m[k] - offset_m = A_m · cos(ω0 t_m[k] + φ_m)
ω0 = 2π·fin
```

用复指数展开：

```text
A_m · cos(ω0 t + φ_m)
= A_m/2 · exp(j(ω0 t + φ_m))
 + A_m/2 · exp(-j(ω0 t + φ_m))
```

乘上 DFT 的基函数 `exp(-jω0t)`：

```text
A_m · cos(ω0 t + φ_m) · exp(-jω0t)
= A_m/2 · exp(jφ_m)
 + A_m/2 · exp(-j(2ω0t + φ_m))
```

第一项是常数，求和后保留下来；第二项是一个 `2fin` 的旋转项，求和时近似抵消。
所以：

```text
P_m ≈ A_m · exp(jφ_m)
```

这就是 DFT 相量法的核心：

```text
abs(P_m)   -> 该通道的 fundamental 幅度
angle(P_m) -> 该通道的 fundamental 相位
```

### 5. 为什么二倍频项约等于零

上面出现的二倍频项是：

```text
Σ exp(-j(2ω0t_m[k] + φ_m))
```

它不是说 ADC 输出里真的没有二倍频，而是说：**当我们在 fundamental 频率上做投影时，
这个二倍频旋转项和 DC/基波投影正交**。

如果采样是 coherent 的，也就是记录窗口里包含整数个输入周期，那么：

```text
Σ exp(-j2ω0t_m[k]) = 0
```

直观地看，复平面上的这些向量绕完整圈，头尾相消。于是 DFT 投影只留下
`A_m · exp(jφ_m)`，二倍频项不贡献相量。

如果不是 coherent sampling，或者窗口太短、fin 估计不准、泄漏很大，这个求和就不会
严格为 0。此时二倍频项会以 leakage 的形式污染相量，所以 `extract_mismatch_sine`
才强调已知频率和相干采样更可靠。

### 6. gain：幅度比

代码取相量幅度：

```python
amps = np.abs(phasors)
```

再用平均幅度归一：

```python
A_mean = amps.mean()
gain = amps / A_mean
```

所以返回的 `gain` 是相对 gain：

```text
gain_m = A_m / mean(A_m)
```

它不试图估计信号源真实幅度，而是只回答：

```text
这个通道比平均通道大多少 / 小多少？
```

### 7. skew：相位差除以角频率

代码取相量相位：

```python
phases = np.angle(phasors)
phases_u = np.unwrap(phases)
```

由于前面 DFT 用的是绝对时间 `t_m[k] = (kM+m)/fs`，理想交织造成的通道相位差已经被
参考基函数消掉。剩下的通道间相位差主要来自 skew：

```text
Δφ_m = 2π·fin·skew_m
```

所以：

```text
skew_m = Δφ_m / (2π·fin)
```

源码里：

```python
skew = (phases_u - phases_u.mean()) / (2 * np.pi * fin)
```

这里减掉 `phases_u.mean()`，是因为整体公共延迟不可观测。所有通道一起晚 2 ps，
单次 capture 只会看到一个共同相位，无法区分是信号源相位还是 ADC 整体延迟。
因此 `extract_mismatch_sine` 返回的是**相对 skew**，均值为 0。

### 8. 这个方法的适用边界

DFT 相量法很干净，但它依赖几个条件：

```text
输入主要是单音；
fin 已知或估计准确；
采样尽量 coherent，减少 leakage；
通道 offset / gain / skew 在记录期间稳定；
输入幅度足够高，否则相位估计会被噪声放大；
相位差不要大到 unwrap 出错。
```

所以 foreground TI 校准常用一条专门的单音校准记录。它不是“从任意波形里自动知道
全部失配”，而是在一个受控输入下，把每个通道的 DC、fundamental 幅度和 fundamental
相位测出来。

实测（exp_ti01，真实 vs 提取）：

```text
注入 gain  = [1.012, 0.977, 1.014, 0.998]（随机，spread 3.96%）
提取 gain  = [1.001, 0.975, 1.010, 1.014]   <- 高度吻合

注入 skew  ~ 3 ps 量级随机
提取 skew  = [-0.64, -3.15, 2.05, 1.74] ps  <- 吻合
```

单音 + 已知频率就能精确提取三类失配，这是 foreground 校准的基础。

注意一个可辨识性细节（和 Stage 06 类似）：skew 的**整体均值**不可观测
（整体平移时钟等效一个公共延迟，单次 capture 看不出），所以代码减掉均值，
只保留相对 skew。这和 Stage 06 里 "整体尺度靠 fundamental 归一" 是同一类处理。

## 两种校准范式：foreground vs background

### 1. foreground 校准（exp_ti01）

用一段已知单音输入，先 `extract_mismatch_sine` 提取失配参数，再
`calibrate_foreground` 逐通道补偿。skew 补偿有两种实现：

```text
skew_method='fft'    在频域做精确的分数延迟（数值上最优）
skew_method='farrow' 用 Farrow 滤波器在时域近似分数延迟（可硬件实现）
```

实测对比（exp_ti01）：

```text
未校准:           TI spur 主导，SFDR 很差
FFT 校准:         spur 掉进噪声底（数值精度极限）
Farrow 校准:      spur 干净压下，但不如 FFT 低（受 Lagrange 截断 + 边界瞬态限制）
```

FFT 法精度最高，但需要在频域操作，硬件不易实现；Farrow 法是可综合的折中。
这正是工程里"精度 vs 可实现性"的典型权衡。

### 2. background 校准（exp_ti02）

不需要专门的校准输入，在正常工作（输入未知信号）时后台持续微调。
exp_ti02 用一个**可变延迟线（Variable Delay Line, VDL）**，每通道有一个
数字控制的延迟 trim code，算法盲搜索让 SFDR 最大的 trim 组合：

```text
循环 200 次:
  调整各通道 trim code
  测当前 SFDR
  保留更优的 trim
```

实测（exp_ti02）收敛过程：

```text
iter   1:  SFDR = 61.29 dBc  (未校准)
iter 100:  SFDR = 75.27 dBc
iter 140:  SFDR = 100.39 dBc  (接近收敛)
iter 150:  SFDR = 101.43 dBc  (best)
```

从 61 dBc 收敛到 101 dBc，改善了 40 dB。最终 trim 收敛到
`[512, 468, 552, 648]`，和理论最优 `[512, 468, 552, 647]` 只差 1 个 LSB
（VDL 量化误差）。

background 的代价是：收敛慢、需要后台算力、且对噪声敏感（实测 best-of-batch
101 dBc 但单次 99 dBc，差 2 dB 来自噪声）。优点是**不打断正常采样**，
这是产品里更常用的方式。

### 3. VDL：用数字 code 微调采样时刻

VDL 是 **Variable Delay Line**，可变延迟线。它不是 ADC 输出码校正器，也不是
数字滤波器，而是一个用数字码控制的**采样时钟/采样开关延迟调节器**。

可以把它想成一个很细的时间旋钮：

```text
trim code = 512  -> 约 0 fs 延迟（中心码）
trim code = 513  -> 约 +10 fs 延迟
trim code = 514  -> 约 +20 fs 延迟
trim code = 511  -> 约 -10 fs 延迟
...
```

所以 VDL 的基本映射是：

```text
code -> delay_sec
```

在代码里，`VariableDelayLine` 生成一个查表曲线：

```text
delays[code] = 这个 trim code 对应的实际延迟
```

然后每个通道的实际采样 skew 是：

```text
effective_skew_m = intrinsic_skew_m + VDL_m(trim_code_m)
```

源码对应：

```python
vdl_delay = np.array([self.vdls[m](self.trim_codes[m]) for m in range(self.M)])
return self.intrinsic_skew_sec + vdl_delay
```

这说明 VDL 只改变**采样时刻**，因此它只能直接校 timing skew。它不能改变通道的
DC 偏置，也不能改变通道增益：

```text
offset error:
  需要减 DC / offset DAC / 数字扣除。

gain error:
  需要幅度归一 / PGA trim / 数字乘法校正。

skew error:
  可以用 VDL 改采样边沿位置。
```

所以 exp_ti02 不是完整的 offset/gain/skew background demo，而是一个
**VDL-based background timing-skew calibration** demo。它假设 offset/gain 不存在、
已校掉，或小到不是本实验关注对象。

#### VDL LSB 不是 ADC LSB

这里的 `LSB` 指的是 VDL trim code 的最小时间步进，不是 ADC 量化电压步长。

```text
ADC LSB:
  电压 / 数字码分辨率，例如 FS / 2^N。

VDL LSB:
  时间分辨率，例如 1 个 trim code 约等于 10 fs。
```

在 exp_ti02 的当前参数里：

```text
n_codes      = 1024
code_center  = 512
lsb_mean_sec = 10 fs
total_range  ≈ 10.2 ps / channel
```

所以：

```text
ideal code = 647
actual code = 648
```

表示：

```text
actual 比 ideal 多 1 个 VDL LSB
≈ 采样边沿多延迟约 10 fs
```

不是 ADC 输出值差 1 个码，也不是延迟后的波形幅度差 1 LSB。

这个 10 fs 的残余时间误差会变成相位误差：

```text
Δφ = 2π · fin · Δt
```

以 exp_ti02 的 `fin≈300 MHz` 为例：

```text
Δt = 10 fs
Δφ ≈ 2π · 300e6 · 10e-15
   ≈ 1.9e-5 rad
```

非常小。这就是为什么 `exp_ti02_lsb_sensitivity.png` 里，多个通道都偏 1 个 VDL LSB
时，SFDR 几乎不掉；此时限制主要来自 demo 里故意加入的 `HD3_DBC=-100`，不是
VDL 分辨率。

#### DNL：每一步不一定刚好一样

真实 VDL 的每个 code step 不会完全相等。代码用 `step_cv=0.15` 给每一级延迟步长
加入约 15% 的随机变化，同时保证每一步为正，因此曲线是单调的：

```text
code 增大 -> delay 大体增大
但每一步可能是 8 fs、10 fs、12 fs ...
```

这就是 VDL 的 DNL（differential nonlinearity）直觉。校准算法不能假设每一步完全理想，
所以脚本最后还会比较：

```text
理论最优 code
算法找到的 best code
偏离 ideal 若干个 VDL LSB 后 SFDR 怎么掉
```

这个敏感度图回答的是：VDL 的有限时间分辨率和 DNL，会不会限制最终 skew 校准效果。

### 4. foreground vs background 对照

| | foreground (ti01) | background (ti02) |
|---|---|---|
| 需要已知校准输入 | 是（单音正弦）| 否（盲搜索）|
| 打断正常工作 | 是 | 否 |
| 收敛速度 | 快（一次提取）| 慢（迭代搜索）|
| 精度 | 高（解析解）| 受噪声/量化限制 |
| 硬件实现 | 复杂 | VDL 较易实现 |
| 适用场景 | 上电/出厂校准 | 运行时跟踪漂移 |

这张表的核心不是说哪一个“更高级”，而是说明两条路线在回答不同工程问题。

foreground 的逻辑是：

```text
我先停下来，给 ADC 一个我知道的校准输入；
然后一次性把 offset / gain / skew 算出来。
```

所以 ti01 里使用单音正弦，`extract_mismatch_sine` 直接通过通道均值、DFT 相量幅度
和相位求出每个通道的失配。它快、准，适合上电、出厂、实验室 characterization。
但它需要已知输入，通常意味着正常数据流要暂停；如果温度、电源或老化让 skew 后续漂移，
foreground 本身不会自动跟踪，除非再次进入校准模式。

background 的逻辑是：

```text
ADC 继续工作；
后台不断微调 trim；
用某个观测指标判断当前 trim 是变好还是变坏。
```

所以 ti02 不需要已知单音输入，而是用 VDL 改变每个通道的采样延迟，再用 SFDR 或
自相关类指标评价 trim code。它慢，因为它是迭代搜索；它也更受噪声、量化和输入内容影响。
但它最大的优点是**不打断正常工作**，能追踪温漂和慢变化。

两种不是互斥的。产品里常见组合是：

```text
上电 / 出厂:
  foreground 先把大 offset / gain / skew 误差校掉。

正常运行:
  background 继续用 VDL 或其他 trim 机制跟踪慢漂移。
```

## TI 校准 vs SAR bit-weight 校准（和 Stage 06 对比）

这一节把两条线对齐，因为它们的数学结构有相似之处，但解的对象完全不同。

| 维度 | SAR 校准 (Stage 06) | TI 校准 (Stage 08) |
|---|---|---|
| 待估参数 | 每个位的 digital weight | 每通道的 offset/gain/skew |
| 参数数量 | = bit 数（十几）| = 3 × 通道数（M=4 时 12 个）|
| 观测 | bits 矩阵 B | 交织输出 x |
| 目标信号 | 正弦（cos/sin basis）| 正弦（DFT 相量）|
| 核心方法 | 最小二乘 `B @ w ≈ sine` | DFT 相量拟合 / 盲搜索 |
| spur 性质 | 输入谐波（2fin, 3fin）| 采样网格 spur（k·fs/M）|
| 是否需要 deinterleave | 否（单通道）| 是（必须先拆通道）|
| 整体尺度/延迟不可观测 | fundamental 归一 | skew 减均值 |

这张表要解决的是：Stage 06 和 Stage 08 都在“校准 ADC”，但它们校准的对象完全不同。

Stage 06 的问题是：

```text
同一个 SAR ADC 内部，每个 bit 的真实权重不等于 nominal weight。
```

所以它的待估参数是：

```text
w0, w1, w2, ...
```

观测量是 bit matrix：

```text
B[n, i] = 第 n 个样本的第 i 个 bit decision
```

校准目标是找一组权重，让：

```text
B @ w ≈ sine
```

因此 Stage 06 本质上是一个线性回归 / 最小二乘问题。

Stage 08 的问题是：

```text
多个子 ADC 交织时，通道之间 offset / gain / skew 不一致。
```

所以待估参数是每个通道的：

```text
offset_m, gain_m, skew_m
```

观测量不是 bit matrix，而是交织输出 `x`。第一步必须 `deinterleave`，因为 offset
要从每个通道的均值看，gain 要从每个通道的 fundamental 幅度看，skew 要从每个通道的
fundamental 相位看。

如果是 foreground，核心方法是：

```text
offset -> 通道均值
gain   -> fin 处 DFT 相量幅度
skew   -> fin 处 DFT 相量相位 / (2πfin)
```

如果是 background，核心方法则是在线搜索或统计优化，不再要求一条已知单音校准记录。

**最本质的相似**：两者都是“从一段正弦相关观测里反推一组参数，使数字重构更接近真实输入”。
Stage 06 反推的是 weights，Stage 08 反推的是 per-channel mismatch。

**最本质的不同**：
- Stage 06 的参数（weights）和输入无关，是静态的（每颗芯片固定）。
- Stage 08 的 skew 对应的相位 `2π·fin·skew` **依赖 fin**，所以 foreground
  校准得到的 skew 在换输入频率后仍然适用（skew 是时间量，与 fin 无关），
  但提取它时必须用某个 fin，且 fin 越高对 skew 越敏感（skew 误差 → 更大相位误差）。

两者还有一个共同的可辨识性细节：都有一个“公共自由度”无法从单次记录里直接决定。

```text
SAR:
  整体尺度不唯一，所以 weights 要靠 fundamental 幅度归一。

TI:
  所有通道一起延迟同样的时间不可观测，所以 skew 要减均值，只保留相对 skew。
```

这也解释了为什么 exp_ti02 故意用高频输入（fin≈300 MHz 而非 17 MHz）：
**频率越高，同样的 skew 产生越大的 spur，校准的信噪比越好。**

## 本库对应代码

主入口（公开 API）：

```text
python/src/adctoolbox/timeinterleave/deinterleave.py     拆/并通道
python/src/adctoolbox/timeinterleave/extract_mismatch_sine.py  提取 offset/gain/skew
python/src/adctoolbox/timeinterleave/predict_spurs.py    失配 → spur 预测
python/src/adctoolbox/timeinterleave/calibrate_foreground.py   foreground 校准
python/src/adctoolbox/timeinterleave/fractional_delay.py  分数延迟（FFT/Farrow）
```

官方示例：

```text
python/src/adctoolbox/examples/08_time_interleave/exp_ti01_compare_skew_methods.py
python/src/adctoolbox/examples/08_time_interleave/exp_ti02_autocorr_background_skew_calibration.py
python/src/adctoolbox/examples/08_time_interleave/variable_delay_line.py  (helper，非独立 example)
```

## 对应 API

```python
from adctoolbox import (
    deinterleave, interleave,
    extract_mismatch_sine, predict_spurs,
    calibrate_foreground,
    find_coherent_frequency,
)
```

典型 foreground 流程：

```python
params = extract_mismatch_sine(x, M=4, fs=fs, fin=fin)      # 提取失配
x_cal = calibrate_foreground(x, M=4, params=params, fs=fs,  # 校准
                             skew_method="farrow", n_taps=9)
# predict_spurs 可在提取后预测 spur 位置/幅度，用于诊断
spurs = predict_spurs(params, fs=fs)
```

## 实验 1：foreground skew 校准方法对比

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\08_time_interleave\exp_ti01_compare_skew_methods.py
```

观察：

```text
未校准频谱的 TI spur 位置（对照 fs/M 网格）；
offset spur 是否固定（与 fin 无关）；
gain/skew spur 是否跟随 fin；
FFT vs Farrow 校准后的残差异。
```

输出图：

```text
.../08_time_interleave/output/exp_ti01_compare_skew_methods.png
```

三联图：未校准 / FFT 校准 / Farrow 校准的频谱对比，每张图标了 SNDR/SFDR/ENOB。

## 实验 2：background 自相关 skew 校准

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\08_time_interleave\exp_ti02_autocorr_background_skew_calibration.py
```

观察：

```text
SFDR 随迭代收敛的曲线（61 → 101 dBc）；
trim code 收敛到的值 vs 理论最优；
best-of-batch 与单次的差异（噪声影响）；
VDL LSB 量化对最终 SFDR 的限制。
```

输出图：

```text
.../08_time_interleave/output/exp_ti02_summary.png
.../08_time_interleave/output/exp_ti02_lsb_sensitivity.png
```

这个实验特别适合和 Stage 07 连起来看：它展示了**校准在噪声下的统计行为**——
不是一次就收敛到最优，而是受噪声扰动，需要看分布而非单点。

## 本阶段边界：TI 失配，不是 debug 下采样或 noise shaping

Stage 08 只处理 TI-ADC 本身的交织结构：

```text
M 个子 ADC -> 通道间 offset/gain/skew -> fs/M 网格 spur -> TI 校准
```

这里有一个刻意保留的边界：**bandwidth mismatch** 暂不展开。带宽失配也是 TI-ADC
的重要问题，但它和 skew 的 spur 位置相似，通常需要 multi-tone 或 swept-tone 输入
才能可靠分离。当前 `timeinterleave/` 源码也把它标为 not covered yet，并计划后续
`analyze_ti_spectrum` 一类工具。

所以本阶段先把最常见、最适合单音学习的三类失配讲清：

```text
offset mismatch
gain mismatch
timing skew mismatch
```

后面两个阶段会继续处理“采样率/带宽变化”，但它们不是同一个问题：

| 阶段 | 主题 | 和 Stage 08 的区别 |
|---|---|---|
| Stage 09 | subsample debug output | 低速输出口如何折叠已有 spur，重点是 `fs_out=fs/N` 和 N 与 M 是否互质 |
| Stage 10 | oversampling / NTF | 如何缩小 signal band、用 NTF 降低带内噪声，重点是 OSR 和 noise shaping |

一个实用判断：

```text
如果 spur 源自通道间失配，先用 Stage 08。
如果 spur 已经存在，只是被低速输出口折叠，读 Stage 09。
如果你关心带内噪声随 OSR/NTF 下降，读 Stage 10。
```

## 容易混淆的点

- **TI spur 不是输入谐波**。它在 fs/M 网格上，不是 fin 的整数倍。
  这是 TI 和单通道失真最关键的区别。
- **offset spur 固定，gain/skew spur 跟随 fin**。看频谱时先判别 spur 是否
  随 fin 移动，能快速判断失配类型。
- **skew 在提取时必须减均值**。整体时钟延迟单次 capture 不可观测，只保留相对 skew。
- **foreground 的 skew 校准结果与 fin 无关**（skew 是时间量），但提取精度依赖 fin：
  fin 越高，相位差越显著，提取越准。
- **background 不等于免校准**。它仍需要算法 + 硬件（VDL），只是不打断正常采样。
- **FFT 校准精度最高但不可硬件实现，Farrow 是可综合的折中**。
- **TI 校准和 SAR 校准是两条平行线**：一个修通道间失配，一个修位权重。
  真实高速 ADC 可能两者都需要。

## 进入后续前要带走什么

Stage 08 的核心是建立**第二类校准问题**的模型：

```text
观测 = 已知采样结构 + 未知 per-channel mismatch + 调制产生的 spur
```

最重要的判断是：

```text
频谱上的 spur 在 fs/M 网格上吗？
是 → TI 失配，走 TI 校准路径。
否（在 fin 倍频上）→ 单通道失真，走 SAR 校准路径。
```

一句话总结：

```text
TI-ADC 把"通道间一致性"变成了一个新的校准维度；
失配在 fs/M 网格上产生 spur，可以用单音 DFT 提取、用 foreground 或 background 校准。
```

## 阶段检查问题

1. 为什么 GS/s 级 ADC 通常用多个子 ADC 交织，而不是单个高速转换器？
2. M=4, fs=1 GHz 的 TI-ADC，offset spur 在哪些频率？为什么和 fin 无关？
3. gain/skew spur 在哪些频率？为什么随 fin 移动？
4. 为什么 skew 在一阶近似下可以和 gain 合并成一个复数增益？
5. `extract_mismatch_sine` 怎么从单音输出同时提取 offset/gain/skew？
6. 为什么提取的 skew 要减均值？
7. foreground 和 background 校准各自的优缺点？产品里通常怎么组合？
8. FFT 和 Farrow 两种 skew 补偿，精度和可实现性上各是什么定位？
9. 为什么 background 校准实验（ti02）要用高频输入（300 MHz）而非低频？
10. TI spur 和 SAR harmonic spur，在频谱上怎么一眼区分？

这些问题如果能讲清楚，就补上了 staged course 里原本缺失的 TI-ADC 这一大块。
