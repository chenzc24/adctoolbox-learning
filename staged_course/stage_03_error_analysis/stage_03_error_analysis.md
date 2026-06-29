# Stage 03：正弦拟合与 residual 误差分析

## 本阶段目标

学完本阶段，你应该能解释：

- 为什么 ADC 单音测试要拟合一个 ideal sine。
- residual/error 是什么。
- error PDF、error autocorrelation、error spectrum 分别回答什么问题。
- 如何根据 residual 判断噪声、失真、memory、glitch 等问题。

## 从 Stage 02 到 Stage 03：学习衔接

Stage 02 已经让你能从 FFT 频谱里拆出：

```text
signal / noise / harmonic / spur / DC
```

并进一步用：

```text
SNR / SNDR / THD / SFDR / ENOB / NSD
```

描述“性能坏成什么频谱形状”。但这些指标本身还不是最终归因。例如：

```text
SNR 差
```

只能说明“信号相对噪声或非信号成分不够干净”，还不能直接说明它一定来自 thermal
noise、comparator noise、reference noise、jitter，还是测试源问题。

Stage 03 的任务是接着问：

```text
把最主要的 sine 成分拿掉以后，剩下的 error 到底长什么样？
```

因此本阶段的核心衔接链条是：

```text
analyze_spectrum(...)
-> 频谱指标提出第一层怀疑
-> fit_sine_4param(...) 拟合并移除主信号
-> residual = measured - fitted
-> PDF / ACF / error spectrum / by value / by phase
-> 判断误差更像 random、deterministic、memory、clipping 还是 jitter-related
```

对应关系先记成这张索引：

| Stage 02 的频谱现象 | Stage 03 的验证视角 | 先用哪些工具 |
|---|---|---|
| `SNR` 差、noise floor 高 | residual 是否像随机白噪声 | `analyze_error_pdf`、`analyze_error_autocorr` |
| `THD` 差、harmonic 明显 | residual 是否有确定性的周期结构 | `analyze_error_spectrum`、`analyze_error_by_value`、`analyze_error_by_phase` |
| `SFDR` 差、单个 spur 突出 | residual 里是否有固定频率线，spur 是否随条件移动 | `analyze_error_spectrum` |
| 高频输入下 `SNR` 更差 | error 是否和输入相位/斜率相关，是否接近 jitter limit | `analyze_error_by_phase`、`calculate_jitter_limit` |
| clipping 或接近 full-scale | residual 是否在波峰/波谷、码边界或幅度边缘异常 | `analyze_error_pdf`、`analyze_error_by_value` |

本阶段不会把所有电路来源一次性讲完。这里先训练一种诊断动作：

```text
先看频谱指标提出假设；
再看 residual 形状验证假设。
```

更具体的 ADC 非理想来源，例如 sampling noise、comparator noise、CDAC mismatch、
settling、reference error，会在 Stage 04 继续展开；deterministic error 为什么可以校准、
随机噪声为什么不能简单校准，会在 Stage 06 继续展开。

## 初学者先抓住的主线

Stage 02 的频谱指标回答：

```text
这个 ADC 输出有多差？
```

Stage 03 的 residual 分析回答：

```text
它像是哪一种差法？
```

核心流程是：

```text
原始输出 y[n]
-> 拟合一个最像它的 ideal sine
-> residual = y[n] - fitted_sine[n]
-> 分析 residual 的形状
```

你可以把 fitted sine 看成“ADC 应该输出的主信号”，把 residual 看成“主信号解释不了的剩余部分”。剩余部分越有结构，越说明问题可能不是纯随机噪声。

本阶段建议按这个顺序学：

```text
1. 先理解为什么要 fit sine：建立“主信号模型”
2. 再理解 residual：只看主信号解释不了的部分
3. 看 PDF：误差幅度分布像不像随机噪声
4. 看 ACF：误差样本之间有没有 memory
5. 看 error spectrum：误差里有没有确定性频率成分
6. 看 by value / by phase：误差是否依赖输入值或输入相位
```

## 几类 residual 图分别看什么

如果 demo 给你几类 residual 图，按这个顺序看：

| 图 | 先问什么 |
|---|---|
| error vs sample/time | 有没有周期、突变、包络变化 |
| error PDF | 像 Gaussian、uniform，还是有长尾/多峰 |
| error autocorrelation | 相邻样本之间是否相关 |
| error spectrum | residual 里有没有固定频率 spur |

初学者最常见误区是只看 PDF。PDF 能看幅度分布，但看不出“这个误差是不是每隔固定周期出现”。所以 PDF、ACF、spectrum 要一起看。

## 数学需要补什么

### 1. 模型分解：为什么单音测试要写成 y[n] = ideal_sine + error

Stage 02 已经让你相信"单音正弦是 ADC 动态测试的标准输入"。Stage 03 要在这个
基础上建立一个更强的假设：**ADC 输出可以分解成两部分**。

```text
y[n] = ideal_sine[n] + error[n]
```

其中 ideal_sine 是"ADC 应该输出的完美正弦"，error 是"主信号解释不了的剩余"。

为什么这个分解有意义？因为理想正弦是完全确定性的——给定 A、f、phase、DC 四个
参数，任何 n 的值都可以精确算出来。所以"理想正弦"这一部分不携带任何 ADC 信息，
**ADC 的非理想行为大部分会出现在 error[n] 里**。但要注意一个边界：与 fundamental
不正交的误差（AM 边带、与 fundamental 同频的 PM、频率估计偏差）会被 fit 部分吸收，
不会完整留在 error 中。这个边界在 § 3.5（fit 的正交投影性质和盲点）会展开。

这就是 Stage 03 的核心思路：

```text
把能精确建模的主信号抽掉
-> 剩下的 error 浓缩了所有非理想信息
-> error 的统计/频域/时域形状 -> 反推非理想来源
```

error 越像随机噪声 -> 越像 thermal/quantization；error 越有结构（周期、尖峰、
幅度依赖）-> 越像 deterministic 失真或 memory effect。

理想正弦写成哪两种等价形式：

```text
形式 1：ideal_sine[n] = A·cos(2πfn) + B·sin(2πfn) + C
    -> 用于最小二乘拟合（A、B、C 是线性参数）
    -> C 是 DC offset

形式 2：ideal_sine[n] = Amp·sin(2πfn + phase) + DC
    -> 用于物理理解（Amp 是幅度，phase 是相位）
    -> 两种形式用三角恒等式互相转换
```

注意 `fit_sine_4param` 的代码里写的是 `phase = np.arctan2(-b, a)`，多了一个负号。
这是因为代码的拟合基底用的是 `a·cos(ωt) + b·sin(ωt)`，和上面 `A·cos + B·sin`
的符号约定略有差别——具体推导在代码追踪那一节展开。

残差的定义：

```text
error[n] = y[n] - ideal_sine[n]
```

注意符号约定：error = measured − fitted。有些教材写成 fitted − measured，
符号反了 RMS 不变但 PDF 会镜像，所以同一份课程内要统一。

### 2. 最小二乘：为什么这是拟合 ideal sine 的正确方法

已知频率 f 时，拟合 A、B、C 是一个**线性最小二乘**问题。这一节先讲清楚"为什么
最小二乘是对的"，再讲代码怎么实现。

#### 2.1 最小二乘在统计上意味着什么

假设 error 是零均值、等方差、独立的随机变量（这是 thermal noise 的标准模型）：

```text
y[n] = ideal_sine[n] + error[n]
error[n] ~ N(0, σ²)，各 n 之间独立
```

在这种假设下，**最大似然估计（MLE）** 等价于最小二乘。直觉推导：

```text
似然函数 = 在参数 (A, B, C) 下观测到数据 y 的概率
        ∝ exp(-Σ(y[n] - ideal_sine[n])² / (2σ²))

最大化似然  ⟺  最小化 Σ(y[n] - ideal_sine[n])²
            ⟺  最小化 residual 的平方和
```

所以最小二乘不是任意选择的"拟合准则"，而是**在 error 是高斯白噪声的假设下，
统计学上最优的估计方法**。这个假设在 ADC 测试里基本成立（thermal noise 主导），
所以 IEEE 1057/1241 标准也用最小二乘。

#### 2.2 线性最小二乘的矩阵形式

把理想正弦写成矩阵：

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

对 β 求导等于零，得到正规方程（normal equation）：

```text
XᵀX·β = Xᵀy
β = (XᵀX)⁻¹·Xᵀy
```

数值上 `(XᵀX)⁻¹` 可能不稳定（XᵀX 接近奇异时），所以代码用 `np.linalg.lstsq`
而不是显式求逆——`lstsq` 内部用 SVD 分解，对病态矩阵更稳健。

#### 2.3 对应到 fit_sine_4param 代码

`python/src/adctoolbox/fundamentals/fit_sine_4param.py` 第 0 次迭代：

```python
design_matrix = np.column_stack((cos_vec, sin_vec, np.ones(n)))
coeffs = np.linalg.lstsq(design_matrix, y, rcond=None)[0]
a, b, c = coeffs[:3]
```

精确对应上面的 `X = [cos, sin, ones]`、`β = [A, B, C]`。`a, b, c` 就是拟合出来的
`A, B, C`，重构 fitted sine：

```python
fitted_sig = a * np.cos(omega * t) + b * np.sin(omega * t) + c
```

注意代码的列顺序是 `[cos, sin, ones]`，所以 `a` 是 cos 系数、`b` 是 sin 系数、
`c` 是 DC。这个顺序和正文 2.1 节的符号约定一致。

### 3. 频率也未知时：4 参数拟合和迭代

第 2 节假设频率 f 已知。但实际测试中 f 可能不准确（测试源有偏差）、或完全未知
（真实芯片测量）。这时要同时拟合 (A, B, C, f) 四个参数——但频率 f 出现在 cos 和
sin 的**内部**，不再是线性参数：

```text
ideal_sine[n] = A·cos(2πfn) + B·sin(2πfn) + C
                     ↑ f 在三角函数里面
```

所以不能直接套线性最小二乘。本库的做法分两步：FFT 找初始频率，再迭代精化。

#### 3.1 用 FFT 找初始频率估计

代码 `_estimate_frequency_fft(y)`：

```python
spec = np.abs(np.fft.fft(y))
spec[0] = 0                # 去掉 DC
spec = spec[:n // 2]       # 只看正频率半边
k = np.argmax(spec)        # 找最大峰所在 bin
```

这一步就是 Stage 02 学过的内容：对 y 做 FFT，幅度谱最大的 bin 就是主频所在。但
离散 FFT 的频率分辨率是 `Fs/N`，真实主频可能落在两个 bin 之间。代码用 **parabolic
插值**做 sub-bin 精化：

```python
if 0 < k < len(spec) - 1:
    r = 1 if spec[k + 1] > spec[k - 1] else -1
    delta = r * spec[k + r] / (spec[k] + spec[k + r])
    k += delta
```

直觉：如果真实峰在 bin k 和 k+1 之间，那 spec[k+1] > spec[k-1]，峰更靠近 k+1。
用三个点 `(k-1, k, k+1)` 的幅度拟合一条抛物线，顶点的 x 坐标就是 sub-bin 估计。

这正好是 Stage 02 实验 3 讨论过的 **scalloping loss** 的反面——scalloping 是
"频率不在 bin 中心导致幅度低估"，parabolic 插值是"用相邻 bin 信息反推真实频率"。

#### 3.2 迭代精化：把频率当线性参数处理

有了初始频率估计 `f₀`，开始迭代。核心技巧：把频率修正量 `Δf` 也当成线性参数。

在第 i 次迭代，当前频率 `f_i`，对理想正弦做一阶 Taylor 展开令 `f = f_i + Δf`：

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
```

代码里的这一行：

```python
freq_corr = t * (-a * sin_vec + b * cos_vec)
design_matrix = np.column_stack((cos_vec, sin_vec, np.ones(n), freq_corr))
```

`freq_corr` 就是上面 Taylor 展开里的 `2π·n·(-A·sin + B·cos)` 这一项（代码把 `2π`
吸收进 `Δf` 的更新里）。求解后：

```python
delta_freq = coeffs[3] / (2 * np.pi)
freq += delta_freq
```

更新频率，进入下一次迭代。如果 `Δf` 很小（小于 tolerance），说明收敛了。

#### 3.3 fit_sine_4param 的完整返回值

```text
frequency      拟合出的 normalized frequency (0~0.5)
amplitude      sqrt(a² + b²)
phase          atan2(-b, a)   ← 注意负号
dc_offset      c
fitted_signal  a·cos + b·sin + c
residuals      y - fitted_signal
rmse           sqrt(mean(residuals²))
```

`phase = atan2(-b, a)` 的负号来源：代码的拟合形式是 `a·cos(ωt) + b·sin(ωt)`，
把它写成 amplitude·cos(ωt + phase) 形式：

```text
a·cos(ωt) + b·sin(ωt)
= Amp·cos(ωt + phase)
= Amp·cos(phase)·cos(ωt) - Amp·sin(phase)·sin(ωt)

-> a = Amp·cos(phase)
-> b = -Amp·sin(phase)
-> Amp = sqrt(a² + b²)
-> phase = atan2(-b, a)
```

所以负号是因为代码用 cos 作为相位基准（`cos(ωt + phase)`），而不是 sin。这是
IEEE 1057 的惯例——很多 ADC 标准用 cos 作为参考相位。

#### 3.4 fit_sine_4param 不是滤波

一个容易混淆的点：`fit_sine_4param(data)` 不是对 data 做"滤波"（filtering），
而是**找一个最能解释 data 的理想正弦**。区别在于：

```text
滤波：
    y[n] -> 系统 H(z) -> y_filtered[n]
    -> 输出仍然是波形，只是被改造了

正弦拟合：
    y[n] -> 找 (A, B, C, f) -> fitted_sine + residual
    -> 输出是一个参数化的模型 + 残差
    -> 模型是 4 个数，残差是和输入同样长度的数组
```

滤波改造信号，拟合解释信号。Stage 03 后续所有分析（PDF/ACF/spectrum）都建立在
residual 上，所以先要把"拟合 ≠ 滤波"分清楚。

### 3.5 为什么必须拟合，不能直接用输入信号的标称参数

一个自然的疑问：既然输入就是 `A·sin(2π·f·t)`，为什么不直接用这组 (A, f, phase)
构造 ideal_sine，而要花力气去拟合？答案是：**几乎一定要拟合**，原因有四个，互相
独立。

#### 原因 1：测试源本身不理想

实验室信号发生器（AWG）标称输出 `A·sin(2π·f·t)`，但实际参数都有偏差：

```text
幅度:    标称 0.5 V，实际可能是 0.498 V（AWG 自身精度 ±0.5%）
频率:    标称 10 MHz，实际可能是 10.00003 MHz（即使 OCXO 也有 ppm 级偏差）
相位:    完全未知（ADC 采样时钟和 AWG 输出之间没有同步对齐）
DC:      AWG 输出级可能带几 mV 的 DC 偏移
```

如果直接用标称参数构造 ideal_sine，这四类误差全部会被算进 residual——你会测出
"AWG + ADC"的合成误差，而不是 ADC 本身的误差。比如 AWG 频率偏差 1 ppm，对 10 MHz
输入就是 10 Hz 偏差，在 N=8192 / Fs=100MHz 的记录里累积成约 0.8 个周期错位，
residual 会大量增加。

#### 原因 2：信号链会改变信号

ADC 之前的信号链（驱动放大器、抗混叠滤波器、balun）会引入：

```text
增益:        信号幅度改变（驱动放大器可能 +6 dB）
群延迟:      信号相位改变（滤波器群延迟不是常数）
插入损耗:    信号幅度衰减
```

所以 ADC 实际看到的正弦已经不是 AWG 输出的那个了。你要拟合的是 **ADC 输入端的
实际正弦**，不是 AWG 标称参数。

#### 原因 3：fit 的目的是反推"ADC 实际看到的 ideal sine"

Stage 03 的核心假设是 `y[n] = ideal_sine[n] + error[n]`，其中 ideal_sine 是"ADC
应该输出的"。但"应该输出"由 ADC 实际看到的信号决定，不是 AWG 标称参数决定。
**fit 的过程就是从 y 反推出这个 ADC 实际看到的理想正弦**——这是为什么
fit_sine_4param 一次就把 (A, B, C, f) 全部从数据估计，而不是接受外部参数。

#### 原因 4：拟合在统计上最优

假设 error 是零均值高斯白噪声（thermal noise 主导时的标准模型），最小二乘估计
等价于最大似然估计（MLE）——这是 § 2.1 已建立的结论。MLE 在大样本下是渐近无偏、
渐近有效的，所以 fit 出来的 ideal_sine 在统计意义上是最好的估计。

IEEE 1057（ waveform 测试）和 IEEE 1241（ADC 测试）标准都用最小二乘正弦拟合作为
推荐方法，正是基于这个统计性质。

#### 误差估计准不准：fit 的正交投影性质

只要真实信号确实是"单音正弦 + 高斯白噪声"，4 参数拟合就是 MLE 最优估计，residual
的无偏估计就是真实的 error。但现实信号往往还有别的成分——关键问题是这些成分
**会不会污染 fit**。答案取决于一个数学性质：**正交性**。

##### 为什么 harmonic 不污染 fit（正交投影）

一个常见误解是"如果信号含强 harmonic，fitted sine 会把一部分 harmonic 平均掉"。
**这是错的**。正确的解释要用到正交投影。

在 coherent 采样下（频率是整数 bin），cos(ωn), sin(ωn), cos(2ωn), sin(2ωn), ...
这些 DFT 基底**两两正交**：

```text
<sin(ωn), cos(2ωn)> = Σ_n sin(ωn)·cos(2ωn) = 0
<cos(ωn), cos(2ωn)> = Σ_n cos(ωn)·cos(2ωn) = 0
<sin(ωn), sin(3ωn)> = Σ_n sin(ωn)·sin(3ωn) = 0
... 所有不同 bin 的基底都正交
```

回到 § 2.2 的 normal equation：

```text
XᵀX·β = Xᵀy
```

`X` 的列是 `[cos(ωn), sin(ωn), 1]`。如果误差 `error[n]` 含有 HD2 成分
`B·cos(2ωn)`，那：

```text
Xᵀ·error = [<cos(ωn), B·cos(2ωn)>, <sin(ωn), B·cos(2ωn)>, <1, B·cos(2ωn)>]
         = [0, 0, 0]    （正交性）
```

所以 `Xᵀy` 里 HD2 的贡献是 0，β 的解完全不受 HD2 影响。**fit 是把 y 投影到
"fundamental + DC"子空间，正交于这个子空间的所有成分（HD2/HD3/.../白噪声）完整
留在 residual 里**。

##### 实验验证：harmonic 不污染 fit

下面这个实验（详细数据见 § 3.5.5）：

```text
Case 1 (纯单音):              fit_amp = 0.500000  (true 0.5)
Case 2 (+ 40% HD2):           fit_amp = 0.500080  (偏差 +0.016%)
Case 3 (+ 100% HD2):          fit_amp = 0.500204  (偏差 +0.04%)

所有 case 的 residual std ≈ HD2_amplitude / √2
-> HD2 完整进入 residual，没有被 fit 吸收
```

所以即使 HD2 和 fundamental 一样大，fit 仍然精确恢复 fundamental，HD2 完整保留在
residual 里供后续分析。这正说明 fit 是对的方法。

##### fit 的盲点：哪些误差会被吸收

正交投影的"反面"是：**不与 fundamental 正交的误差会被 fit 部分吸收**。三种典型：

```text
1. amplitude modulation (AM)
   y[n] = A·sin(ωn)·[1 + m·cos(ωm·n)]
        = A·sin(ωn) + (A·m/2)·[sin((ω+ωm)n) + sin((ω-ωm)n)]
                        ↑ 边带，频率接近 fundamental

   边带 (ω±ωm) 如果离 fundamental 很近（ωm 小），和 cos(ωn)/sin(ωn) 弱不正交
   -> fit_amp 略偏高（~0.1-0.3%）
   -> AM 的 envelope 信息被 fit 吸收，residual 看不到 envelope
   -> 这是 fit_sine_4param 看不到 AM 失真的原因

2. fundamental 频率上的误差成分
   某些非线性（比如偶阶非线性 y²）的产物在 fundamental bin 有微量泄漏
   -> 但 cos/sin 双基底的对消作用让大部分泄漏被吸收到 b 系数
   -> 对 amplitude 的影响通常 < 0.05%

3. 频率估计偏差（fit 没收敛）
   fitted sine 的频率略偏
   -> cos((ω+δω)n) 和真实 cos(ωn) 不完全正交
   -> fundamental 能量泄漏到 residual
   -> residual 在 fundamental 附近出现假尖峰（见 § 6.4）
   -> 这不是真实 ADC 问题，而是 fit 质量问题
```

##### 为什么需要 by_value / by_phase

fit 的正交投影性质决定了它的**本质盲点**：

```text
fit 能干净分离：
    fundamental  vs  所有正交成分（harmonic + 白噪声）
    -> PDF/ACF/error spectrum 三件套对这些有效

fit 看不见的：
    1. AM 的 envelope 信息（边带被算进 fundamental 主瓣）
    2. 与 fundamental 同频的 PM（部分被吸收）
    3. 慢漂移（如果在 fundamental 主瓣宽度内）
    -> 这些必须用 by_value / by_phase 分析
```

`by_value` 把样本按输入电压 bin 分组，看每个 voltage level 的 error 分布；
`by_phase` 把样本按输入相位 bin 分组，看每个相位区间的 error。这两套工具分析的
仍然是 residual（`signal - fitted_signal`），所以它们**不能恢复已经被 fit 吸收的
同频或近同频误差**。它们真正的价值在于：把 residual 按 value / phase 维度重新组织，
让 fit 盲点里的那些结构（AM envelope、与相位相关的 PM）在 residual 的条件化切片里
重新变得可见。这两套工具和 fit + 三件套是互补的，合起来才能更完整地诊断 ADC 的
非理想行为。

判断 fit 是否被污染：

```text
看 fit_freq 是否偏离 coherent bin（> 0.01 bin 就要警惕）
看 residual 在 fundamental 附近有没有"假尖峰"（§ 6.4）
看 rmse 是否远超预期噪声底（说明有大结构没被 fit 解释）
看 residual 是否有 low-frequency envelope（说明有 AM 被 fit 吸收）
```

### 3.5.5 实验：正交与不正交误差对 fit 的影响

§ 3.5 解释了 fit 的正交投影性质。这一节用三个对照实验直接验证：

```text
Case A: harmonic（正交，不应该污染 fit）
Case B: amplitude modulation（弱不正交，应该轻微污染 fit）
Case C: 频率偏差（fundamental 自身不正交，应该让 residual 出现假结构）
```

公共参数：N=8192, f0=0.01（bin 82，coherent）, A_true=0.5。

#### Case A：harmonic 完整进入 residual

```text
y[n] = 0.5·sin(ωn) + B·cos(2ωn)   （fundamental + HD2）

Case A1: B=0    (纯单音)      fit_amp = 0.500000  rmse = 1.7e-7
Case A2: B=0.2  (40% HD2)     fit_amp = 0.500080  rmse = 0.141
Case A3: B=0.5  (100% HD2)    fit_amp = 0.500204  rmse = 0.353
```

观察：

```text
1. fit_amp 偏差 < 0.05%，几乎不受 HD2 影响
   -> 验证了 § 3.5 的正交投影性质
   -> HD2 与 fundamental 正交，不进入 X^T·y

2. rmse 完整反映了 HD2 的 RMS:
   B=0.2 -> rmse=0.141 ≈ 0.2/√2  ✓
   B=0.5 -> rmse=0.353 ≈ 0.5/√2  ✓
   -> HD2 完整进入 residual，没有被 fit 吸收
```

这个实验推翻了"fit 会平均掉 harmonic"的直觉——**只要 coherent 采样，harmonic
再大也不污染 fit**。这是 fit_sine_4param 可靠性的数学根基。

#### Case B：amplitude modulation 弱污染 fit

```text
y[n] = 0.5·sin(ωn)·[1 + m·cos(ωm·n)]   （AM 调制）

m=0.1, fm=0.002:  fit_amp = 0.500295  (偏差 +0.06%)
m=0.3, fm=0.002:  fit_amp = 0.500885  (偏差 +0.18%)
m=0.1, fm=0.0005: fit_amp = 0.501134  (偏差 +0.23%)
```

观察：

```text
1. fit_amp 略偏高，说明 AM 边带确实污染了 fit
   -> 边带 (ω±ωm) 与 cos(ωn)/sin(ωn) 弱不正交

2. fm 越小（ωm 越接近 0），边带越接近 fundamental，污染越严重
   -> fm=0.0005 偏差 (+0.23%) > fm=0.002 偏差 (+0.06%)
   -> 边带离 fundamental 越近，正交性越差

3. m 越大（调制深度越深），污染越大
   -> m=0.3 偏差 (+0.18%) > m=0.1 偏差 (+0.06%)
```

后果：fit_amp 不再等于"理想 fundamental 幅度"，而是被 AM envelope 抬高。更严重
的是，AM 的 envelope 信息（m 和 ωm）被 fit 吸收了，**residual 看不到 AM**。要
诊断 AM 必须用 by_value（按输入电压分组看 error）。

#### Case C：频率偏差让 residual 出现假结构

```text
y[n] = 0.5·sin(ω_true·n) + 0.1·cos(2·ω_true·n)
       （真实频率不在整数 bin）

f_true=0.01000 (bin 81.92): fit_freq=0.0100000  rmse=0.0707
f_true=0.01005 (bin 82.33): fit_freq=0.0100500  rmse=0.0707
f_true=0.01010 (bin 82.74): fit_freq=0.0101000  rmse=0.0707
```

观察：

```text
1. fit_freq 能精确恢复非整数 bin 的真实频率
   -> Taylor 迭代（§ 3.2）的 sub-bin 精度发挥作用
   -> parabolic + 迭代能把 0.0001 级别的偏差找到

2. rmse 恒为 0.0707 ≈ 0.1/√2（HD2 的 RMS）
   -> HD2 仍完整进入 residual，即使频率不在整数 bin
   -> 说明只要 fit_freq 收敛到真实频率，正交性条件仍近似成立

3. 但如果 fit_freq 没收敛（比如 max_iterations=0），
   cos(ω'n) 和真实 cos(ωn) 不完全正交
   -> fundamental 能量泄漏到 residual
   -> residual 在 fundamental 附近出现"假尖峰"（见 § 6.4）
```

#### 总结：正交性是 fit 可靠性的数学根基

```text
误差类型                    与 fundamental 关系     对 fit 的后果
--------------------------------------------------------------
harmonic (HD2/HD3/...)     正交（coherent）       几乎无影响（Case A）
高斯白噪声                  统计正交               几乎无影响
AM 边带                    弱不正交              fit_amp 偏高 0.1-0.3%（Case B）
频率估计偏差                fundamental 自身不正交  residual 假尖峰（Case C, § 6.4）
non-coherent               harmonic 微量不正交    residual 略偏小

工程结论：
    对纯 thermal + harmonic 失真（最常见）: fit + 三件套够用
    对含 AM/PM/drift 的失真:              必须配 by_value / by_phase
    判断 fit 是否被污染:                    看 fit_freq 偏差、residual 在
                                            fundamental 附近的形状、rmse 合理性
```

这个表格是 § 3.5 "fit 的盲点"小节的具体证据，也是后续 by_value / by_phase 章节的
动机——它们的存在就是为了补 fit 的盲点。

### 3.6 parabolic interpolation 的原理和精度

§ 3.1 已经展示了 `_estimate_frequency_fft` 的代码。这一节回答三个深入问题：为什么
选抛物线？精度受什么影响？本库的实现和标准版有什么区别？

#### 3.6.1 为什么抛物线是数学上正确的选择

关键事实：**rectangular window 的主瓣在 dB 域近似抛物线**。

回忆 Stage 02 § 5.5：rectangular window 的频域响应是 Dirichlet kernel：

```text
W_R(e^{jω}) = sin(N·ω/2) / sin(ω/2)
```

在主瓣峰值（ω ≈ 0）附近，对 `log|W_R|` 做 Taylor 展开：

```text
log|W_R(e^{jω})| ≈ log(N) - (N²-1)·ω²/24
```

——这是 ω² 的一阶展开，就是抛物线。所以在 log 幅度谱上，rectangular 主瓣峰值
附近的三个相邻 bin 一定落在一条抛物线上，用三点拟合就能找到顶点（真实峰）。

这个性质只对 rectangular window 严格成立。如果数据先乘了 Hann / Blackman 再做
FFT，主瓣形状变了，抛物线近似就不准——但本库的 `_estimate_frequency_fft` 对原始
数据做 FFT（不加分析窗），所以用抛物线是数学上匹配的选择。

#### 3.6.2 标准三点 log-domain 抛物线公式

常见的工程实现（广泛用于 FFT 频率估计）用三个点 `(k-1, k, k+1)` 的 log 幅度：

```text
α = log|spec[k-1]|
β = log|spec[k]|
γ = log|spec[k+1]|

δ = 0.5 · (α - γ) / (α - 2β + γ)
```

δ ∈ [-0.5, +0.5]，真实峰位置 = `k + δ`。推导：把三点坐标代入抛物线
`y = a(x-k)² + b(x-k) + c`，对 x 求导等于 0，解出顶点偏移 δ。

精度：约 0.01-0.1 bin（依赖 SNR 和 N）。

#### 3.6.3 本库的简化两点版本

本库代码（`fit_sine_4param.py` 第 123-126 行）：

```python
if 0 < k < len(spec) - 1:
    r = 1 if spec[k + 1] > spec[k - 1] else -1
    delta = r * spec[k + r] / (spec[k] + spec[k + r])
    k += delta
```

注意几个关键差别：

```text
1. 只用 k 和 k+r 两个点（不是标准的三点 k-1, k, k+1）
2. 在线性 spec 上运算（不是 log spec）
3. 公式是 r·spec[k+r] / (spec[k] + spec[k+r])
   -> 等价于"看 k+r 和 k 哪个更大，按比例分配"
   -> 数学上是加权平均，不是严格抛物线顶点
```

精度约 0.1-0.3 bin，比标准三点版差 3-10 倍。但本库用这个简化版是合理的——因为
后续 Taylor 迭代（§ 3.7）会修正初始估计的误差，**初始估计的精度不影响最终结果**
（只要它落在 Taylor 展开的有效范围内）。

#### 3.6.4 精度和 N / 幅度 / 噪声的关系

```text
和 N 的关系：
    FFT bin 宽 = Fs/N
    parabolic 把精度从 1 bin 提到约 0.1 bin（两点版）或 0.01 bin（三点版）
    所以 N 越大，绝对精度（Hz）越好
    但相对精度（bin 的比例）不变

和信号幅度的关系：
    理想情况无关（主瓣形状只取决于频率，和幅度无关）
    但 SNR 固定时：幅度小 -> spec 峰相对 noise floor 不突出
    -> 峰位置估计受 noise 干扰 -> 精度变差

和噪声水平的关系（最关键）：
    noise 扰动 spec[k-1], spec[k], spec[k+1] 的相对大小
    -> SNR > 20-30 dB: parabolic 可靠
    -> SNR < 10 dB: parabolic 可能给错方向（峰位置被 noise 移走）
    -> 经验阈值：SNR > 20 dB 才信任 parabolic 结果
```

#### 3.6.5 parabolic 是 Taylor 迭代收敛的必要前置

这一点连接 § 3.1 和 § 3.7，非常重要。Taylor 展开（§ 3.2）要求 `2π·Δf·n` 在整个
n 范围内都很小：

```text
2π·Δf·N << 1
Δf << 1/(2πN)
```

对 N=8192，这要求 Δf << 2e-5（normalized frequency）。

FFT 直接找 bin（不插值）的精度是 1 bin = `1/N`，对 N=8192 就是 `1.2e-4`——**比
Taylor 展开的有效范围大 6 倍**，直接用会让迭代发散。

parabolic 把初始估计精度提到约 `0.1/N = 1.2e-5`，刚好满足 `Δf << 1/(2πN)`。
**所以 § 3.1 不是可选优化，而是 § 3.2 Taylor 迭代收敛的必要前置条件**。

### 3.7 迭代收敛判据和 tolerance 设置

§ 3.2 展示了迭代公式，但没说什么时候停止、tolerance 怎么定。这一节补完。

#### 3.7.1 代码的收敛逻辑

`fit_sine_4param.py` 第 77-79 行：

```python
if abs(delta_freq) < tol:
    converged = True
    break
```

两条收敛判据，满足任一即停止：

```text
1. |Δf| < tolerance
   -> 频率更新已经极小
   -> 继续迭代改善有限
   -> converged = True（成功收敛）

2. 达到 max_iterations
   -> 没在预算次数内满足判据 1
   -> 触发 RuntimeWarning: "fit_sine_4param did not converge"
   -> 这是 fit 质量不好的信号
```

#### 3.7.2 tolerance = 1e-9 意味着什么

默认 `tolerance=1e-9`（normalized frequency，单位 cycle/sample）。换算成绝对频率：

```text
绝对频率精度 = tolerance × Fs
            = 1e-9 × Fs

Fs = 100 MHz: tolerance = 0.1 Hz
Fs = 1 GHz:   tolerance = 1 Hz
Fs = 1 MHz:   tolerance = 0.001 Hz
```

0.1 Hz 级别的精度对几乎所有 ADC 测试都够（ADC 关心 Hz 量级，不关心 sub-Hz）。

注意 tolerance 是 **|Δf| 的绝对值**，不是相对值。所以对不同主频严格度不同：

```text
低频信号 f=0.01:   tolerance 是 f 的 1e-7 倍（宽松）
Nyquist f=0.49:    tolerance 是 f 的 2e-9 倍（严苛 50 倍）
```

如果想统一相对精度，可以手动调 tolerance（比如 `tolerance = 1e-7 * freq_init`），
但本库默认绝对值，简单且对常规应用够用。

#### 3.7.3 没收敛（Δf 还很大）的四种原因

如果到 max_iterations 时 |Δf| 还大于 tolerance，说明迭代没收敛。四种可能：

**原因 1：max_iterations 太小**

默认 `max_iterations=1` 只迭代一次。如果初始估计偏差较大（non-coherent 采样、
SNR 中等），一次迭代可能不够。解决：增大 max_iterations 到 3-5。

**原因 2：信号不是单音正弦**

如果信号含有强 harmonic（比如 HD2 只比 fundamental 低 30 dB），或含有多个主频
（双音测试），fit 单一正弦永远收敛不了——每次迭代都被 harmonic 干扰。解决：
检查频谱，改用 `fit_sine_harmonics`（同时拟合多阶谐波）。

**原因 3：frequency_estimate 给错**

如果手动传了 `frequency_estimate` 但离真实主频太远，Taylor 展开只在一阶项附近
有效，初始偏差大可能不收敛甚至发散。解决：不传 frequency_estimate，让 FFT 自动找。

**原因 4：数据太短**

N 小 → FFT 分辨率粗 → 初始估计偏差大 → 迭代可能发散。解决：增加数据长度，至少
N > 512（推荐 N ≥ 1024）。

#### 3.7.4 max_iterations 工程建议

```text
max_iterations=1（默认）
    适合: coherent 采样 + SNR > 40 dB + N ≥ 1024
    场景: 仿真、理想数据、coherent 测量

max_iterations=3-5
    适合: non-coherent + SNR 20-40 dB + 真实芯片测量
    场景: 实验室测量、生产测试、大多数真实数据

max_iterations=10+
    适合: 极低 SNR + 精密校准 + IEEE 1057 标准测试
    场景: 计量级测试、标准制定、研究
```

判断是否够：看 verbose 输出的 `delta_freq` 序列。如果收敛，序列应该指数下降
（比如 1e-3 → 1e-5 → 1e-7 → 1e-9）；如果震荡或下降慢，说明需要更多迭代或换方法。

### 4. PDF：误差的幅度分布像不像随机噪声

PDF（probability density function，概率密度函数）回答一个问题：

```text
error 取某个值的概率有多大？
```

它是 error 在幅度轴上的统计直方图。看 PDF 的核心目的：**判断 error 是不是像
零均值高斯白噪声**——这是"random noise 主导"的标志特征。

#### 4.1 为什么不同噪声源有不同 PDF 形状

**thermal noise → Gaussian**

thermal noise 是电阻、开关、电容等元件里电子热运动的宏观表现。每一时刻的总噪声
电压可以看成**海量独立小随机事件的相加**：

```text
e_thermal = δe_1 + δe_2 + ... + δe_M    (M 极大)
```

每个 δe_i 独立、零均值、同分布（即使各自分布不一定是高斯）。**中心极限定理
（CLT）**保证：M 个独立同分布随机变量之和趋向高斯分布，不论 δe_i 自己是什么
形状。所以 thermal noise 的幅度分布：

```text
p(e) = (1/(σ·√(2π))) · exp(-e²/(2σ²))
```

零均值、单峰、对称、指数衰减的尾巴。代码里 `analyze_error_pdf` 把这个理想
Gaussian 拟合出来和实际 PDF 对比。

**关键直觉**：thermal noise 的 Gaussian 形状来自"求和"——多个随机变量相加时，
极值互相抵消，平均值最常见，极端值（所有项同号）罕见。

**quantization noise → 近似 Uniform**

这一段要回答一个根本问题：**为什么量化误差是均匀分布？** 推导要从 ADC 量化操作的
几何性质出发。

回忆 Stage 01 的量化规则（round-to-nearest）：

```text
code = round(vin / LSB)
量化后的重建电压: vout = code · LSB
误差:           e = vin - vout
```

把电压轴切成以 LSB 为宽度的区间，区间 k 中心在 `k·LSB`：

```text
区间 k:   [k·LSB - LSB/2,  k·LSB + LSB/2]
落在区间 k 内的 vin -> 都被量化为 vout = k·LSB
误差:     e = vin - k·LSB ∈ [-LSB/2, +LSB/2]
```

所以 **e 完全等于 vin 相对于它所在 LSB 区间中心的偏移**。问题变成：vin 在一个
LSB 区间内取每个相对位置的**概率**是多少？

关键假设：**输入信号相对 LSB 有足够丰富的运动**。如果输入是满幅正弦（幅度远
大于 LSB），它扫过每个 LSB 区间时，在区间内的瞬时位置是"随机"的——可能在任何
位置，没有偏好中心。所以 e 在 [-LSB/2, +LSB/2] 内**每个值出现的机会均等**：

```text
p(e) = 1/LSB,  -LSB/2 ≤ e ≤ +LSB/2
p(e) = 0,      其它
```

这就是 uniform 分布——**一条平的水平线，高度 1/LSB，宽度 LSB**。

```text
quantization PDF:
    p(e)
       │
 1/LSB ┤────────────────
       │      LSB 宽
       │  ┌──────────┐
       │  │          │
  ─────┼──┴──────────┴── e
       -LSB/2      +LSB/2
```

注意几个细节：

```text
1. 形状是"水平线"，不是中间高两头低
   -> 原因：量化是"一次舍入"，e 只取决于 vin 在区间内的位置
            没有多个随机变量相加的"中心倾向"

2. 硬截断（超过 ±LSB/2 概率为 0）
   -> 原因：按定义 e 永远在区间内
   -> 对比 Gaussian 的长尾：thermal noise 没有"理论上限"

3. 宽度由 LSB 决定，高度 1/LSB（保证总面积 = 1）
   -> σ = LSB/√12（Stage 01 推导过）
   -> LSB 越小，quantization 越弱，PDF 越窄越高

4. 假设成立的条件：输入跨过足够多 code、不过载、量化误差与输入不相关
   -> 不满足时（比如输入刚好是 LSB 的整数倍），误差高度结构化，不是 uniform
   -> 这就是 Stage 01 提过的"dither 的作用"——加噪声让假设成立
```

但注意 Stage 01 也强调过：本库的 `apply_quantization_noise` 是 lower-edge
reconstruction，直接误差是 `Uniform(-LSB, 0)`，去均值后才是 `Uniform(-LSB/2, +LSB/2)`
的随机分量。所以代码里算 PDF 前会先减均值。

**thermal vs quantization：为什么形状差别这么大**

| | thermal noise | quantization noise |
|---|---|---|
| 来源 | 海量独立小事件相加 | 一次舍入操作 |
| 物理机制 | CLT（中心极限定理） | 位置均匀 |
| PDF 形状 | `exp(-e²/2σ²)` 中间高两头低 | `1/LSB` 水平线 |
| 尾巴 | 长尾（4σ 概率 0.006%）| 硬截断（超过 ±LSB/2 概率为 0）|
| 关键机制 | "求和"导致中心倾向 | "舍入"没有中心倾向 |

**harmonic distortion → 有结构的 PDF**

如果 error 含有 `cos(2π·k·f·n)` 成分（k 次谐波），error 的瞬时值会在谐波波峰
附近停留更久，PDF 会呈现**双峰**或**马鞍形**。阶数越高、幅度越大，结构越明显。

直觉推导：对纯余弦 `cos(2πfn)`，瞬时值在 ±1 附近（峰附近）变化慢、停留时间长，
在 0 附近（过零）变化快、停留时间短。所以纯余弦的 PDF 是 `1/(π√(1-x²))`（U 形，
两头高中间低）——和 Gaussian 的"中间高两头低"完全相反。当 error 含谐波成分时，
PDF 会朝这种 U 形偏移。

**glitch / burst noise → heavy tail**

偶发的大幅误差（比如 0.1% 概率出现 10σ 的尖峰）会让 PDF 出现长尾。高斯分布的
4σ 概率是 0.006%，如果实测 4σ 以上的样本明显多，基本就是 glitch。

判据：把实测 PDF 的尾巴（比如 |e| > 3σ 部分）和拟合高斯比。如果实测明显高，
就是 heavy tail；如果实测有孤立尖峰（非连续），就是 deterministic glitch。


#### 4.2 KDE：从离散样本估连续 PDF

error 是一堆离散样本 `e[0], e[1], ..., e[N-1]`。要估连续 PDF，最简单的是直方图，
但直方图对 bin 宽度敏感、不光滑。`analyze_error_pdf` 用 **KDE（kernel density
estimation，核密度估计）**：

```text
对每个样本 e[i]，以它为中心放一个宽度 h 的高斯核
把所有 N 个高斯核叠加，再除以 N
得到连续的 PDF 估计
```

代码实现（`python/src/adctoolbox/aout/analyze_error_pdf.py`）：

```python
# Silverman bandwidth rule
h = 1.06 * np.std(err_lsb, ddof=1) * N**(-1/5)

for i in range(len(x)):
    u = (x[i] - err_lsb) / h
    fx[i] = np.mean(np.exp(-0.5 * u**2)) / (h * np.sqrt(2*np.pi))
```

`h` 是核宽度（bandwidth）。Silverman 规则是高斯分布下最优 h 的经验公式：h 和
样本标准差成正比、和 `N^(1/5)` 成反比。h 太小 PDF 毛刺多，h 太大过度平滑。

#### 4.3 KL divergence：PDF 有多像 Gaussian

光靠眼睛看 PDF 形状不够客观。`analyze_error_pdf` 计算一个数值指标 **KL
divergence（Kullback-Leibler divergence）**衡量实际 PDF 和拟合高斯有多远：

```text
KL(p || q) = Σ p(x) · log(p(x) / q(x)) · dx
```

其中 `p` 是实测 PDF（KDE 估计），`q` 是同均值/同方差的高斯分布。直观含义：

```text
KL = 0       p 和 q 完全相同
KL 小        p 接近高斯，random noise 主导
KL 大        p 明显偏离高斯，有 deterministic 结构或 heavy tail
```

代码：

```python
kl_divergence = np.sum(p * np.log(p / q)) * dx
```

ADC 测试的典型经验值：

```text
纯 thermal noise:              KL ≈ 0.001 ~ 0.01
thermal + 轻 harmonic:         KL ≈ 0.01 ~ 0.1
明显 harmonic 或 glitch:       KL > 0.1
```

但 KL 不能告诉你"为什么偏离高斯"——可能是 harmonic、可能是 heavy tail、可能是
multi-modal。所以 KL 是"亮红灯"的指标，具体原因要看 PDF 形状 + error spectrum。

#### 4.4 把 error 转成 LSB 单位

代码里有个关键步骤：

```python
lsb = full_scale / (2**resolution)
err_lsb = np.asarray(err_data).flatten() / lsb
```

把 error 从电压（V）转成 LSB 单位。为什么？因为不同 ADC 的 full-scale 和 bit 数
不同，直接比电压不公平。换算成 LSB 后，"error 是 0.5 LSB" 在 8 位和 16 位 ADC 上
都表示"半个量化步长"，可以直接比较。

Stage 01 已经建立了 LSB 的概念，这里只是把它用到 error 上：

```text
err_lsb = err_voltage / LSB
       = err_voltage · 2^N / full_scale
```

`resolution` 默认是 12 位，`full_scale` 默认从数据范围推断（max − min）。
分析真实 ADC 数据时要显式传正确的 `resolution` 和 `full_scale`，否则 sigma、KL
都会算错。

#### 4.5 PDF 看图判据（更新版）

| error PDF 形状 | 可能含义 | 对应 KL |
|---|---|---|
| Gaussian（零均值、对称、单峰）| thermal noise 主导 | 小 |
| Uniform（平顶、有界）| 理想量化噪声主导 | 中等 |
| 双峰 / 马鞍形 | 含低阶 harmonic | 大 |
| Heavy tail（4σ 以上异常多）| glitch / burst noise | 大 |
| 不对称（skewed）| offset / 奇偶不对称 | 中等 |
| Multi-modal（多峰）| code missing / deterministic | 大 |

重要提醒：**PDF 单独看不够**。PDF 只告诉幅度分布，看不出"误差是不是按某种时间
模式重复出现"。一个含固定频率 spur 的 error，它的 PDF 可能看起来仍然接近高斯
（如果 spur 幅度小），但 ACF 和 error spectrum 会立刻暴露。所以 PDF/ACF/spectrum
要一起看——这是前面"几类 residual 图分别看什么"一节强调过的点。

### 5. Autocorrelation：误差样本之间有没有 memory

ACF（autocorrelation function，自相关函数）回答：

```text
error 在 n 时刻的值，和 n+k 时刻的值，有没有关系？
```

它衡量 error 的时间结构。PDF 看幅度分布、ACF 看时间依赖——两者互补。

#### 5.1 ACF 的数学定义

理论定义：

```text
R[k] = E[e[n] · e[n+k]]
```

`E[]` 是数学期望（总体平均），要求无限长序列或无限次重复。对一段有限观测
`e[0], e[1], ..., e[N-1]`，只能用**有限样本估计**。

##### 5.1.1 从理论到代码：有限样本估计的两个细节

把 `E[]` 换成有限样本求和时，有两个细节必须说清楚，否则代码会和直觉对不上。

**细节 1：求和上限**

`E[e[n]·e[n+k]]` 理论上对所有 n 求和。但有限序列里，当 `n > N-k-1` 时
`e[n+k]` 越界（不存在），这些项必须砍掉。所以实际求和是：

```text
Σ_{n=0}^{N-k-1} e[n]·e[n+k]
```

对 N=5, k=2：`e[0]·e[2] + e[1]·e[3] + e[2]·e[4]`，只剩 N-k=3 项。

**细节 2：分母——biased 还是 unbiased**

求和之后除以什么？这里有两种合法选择，统计性质不同：

```text
biased（有偏）:
    R̂[k] = (1/N) · Σ_{n=0}^{N-k-1} e[n]·e[n+k]
    分母固定为 N（不管 lag 多大）
    -> E[R̂[k]] = (N-k)/N · R[k]    ← 期望偏小，大 lag 偏差大
    -> 但方差小（除以大数）
    -> numpy.correlate / plt.acorr 默认用这个

unbiased（无偏）:
    R̂[k] = (1/(N-k)) · Σ_{n=0}^{N-k-1} e[n]·e[n+k]
    分母是实际重叠项数 N-k（随 lag 减小）
    -> E[R̂[k]] = R[k]              ← 期望无偏
    -> 但方差大（大 lag 时分母小，少数项主导）
    -> 本库 analyze_error_autocorr 用这个
```

**两者数学上都没错**，都是 `R[k] = E[...]` 的合法估计器。差别在 tradeoff：

```text
biased:   偏差大，方差小（大 lag 看起来偏小但稳定）
unbiased: 无偏，方差大（大 lag 看起来波动大）
```

##### 5.1.2 本库代码用 unbiased（np.mean 实现）

代码实现（`analyze_error_autocorr.py`）：

```python
for k in range(len(lags)):
    lag = lags[k]
    if lag >= 0:
        x1 = e[:N-lag]   # e[0], e[1], ..., e[N-lag-1]   长度 N-lag
        x2 = e[lag:N]    # e[lag], ..., e[N-1]            长度 N-lag
    acf[k] = np.mean(x1 * x2)
```

`np.mean(x1 * x2)` = `sum(x1·x2) / len(x1)` = `sum / (N-lag)`，这正是 unbiased
估计。逐元素追踪（N=5, lag=2）：

```text
x1 = e[:3]  = [e0, e1, e2]
x2 = e[2:5] = [e2, e3, e4]
x1 * x2 = [e0·e2, e1·e3, e2·e4]      ← 长度都是 N-lag = 3，能逐元素相乘
acf[2] = (e0·e2 + e1·e3 + e2·e4) / 3  ← 分母是 N-k
```

注意一个容易看错的点：`x1` 和 `x2` 的**长度相同**（都是 N-lag），只是切片的起点
不同。两个切片逐元素相乘时，配对的是 `e[n]` 和 `e[n+k]`——这正好是 `R[k] = E[e[n]·e[n+k]]`
里的项。直觉上可以理解成"把序列左半段和右半段错位 k 后对齐相乘"。

逐 lag 计算。先减均值 `e = e - np.mean(e)`，保证 R[k] 对常数 offset 不敏感
（否则常数项会让所有 lag 的 R[k] 都偏大）。


#### 5.2 归一化：R[0] = 1 的含义，以及 unbiased 估计的副作用

代码默认 `normalize=True`：

```python
acf = acf / acf[lags == 0]
```

理论 `R[0] = E[e[n]²]` 是 error 的功率（方差）。归一化后：

```text
R_norm[0] = 1            <- error 的能量基准
R_norm[k] ∈ [-1, +1]    <- 相对 R[0] 的相关性
```

归一化让不同幅度 error 的 ACF 可以直接比较——一个 σ=1mV 和 σ=1V 的 error，如果
都是白噪声，归一化 ACF 都应该是 `R[0]=1, R[k≠0]≈0`。

##### 5.2.1 unbiased + 归一化的副作用：大 lag 噪声地板偏高

这是看 ACF 图时最容易踩的坑。本库用 unbiased 估计，归一化后会出现一个数学上
必然的现象：**大 lag 的归一化 ACF 方差被人为放大**。

推导。设 unbiased 估计：

```text
R̂[k]   = sum_k / (N-k)      (sum_k = Σ e[n]·e[n+k])
R̂[0]   = sum_0 / N          (sum_0 = Σ e[n]²)
```

归一化：

```text
R_norm[k] = R̂[k] / R̂[0]
          = [sum_k / (N-k)] / [sum_0 / N]
          = (N / (N-k)) · (sum_k / sum_0)
                ↑
            这个因子随 lag 增大而增大
```

对 lag = N/2，放大因子 = 2；对 lag = 4N/5，放大因子 = 5。

**对白噪声的影响**（白噪声理论 `R[k≠0] = 0`）：

```text
理论：  R[k] = 0 for k ≠ 0
实测：  sum_k 是 N-k 个零均值独立乘积之和，本身有方差
        归一化后被 N/(N-k) 放大
        -> lag 越大，方差越大
        -> 白噪声 ACF 在大 lag 看起来不是平的 0，而是"散开的噪声"
```

这**不是真实的相关**，是估计噪声。如果不理解这一点，看 ACF 图会发现"大 lag 有
非零值"，误判为 long-range correlation 或 memory effect。

对比 biased 估计：分母固定 N，没有这个放大因子，大 lag 噪声地板更平。但 biased
会让 `E[R̂[k]] = (N-k)/N · R[k]`，大 lag 看起来**整体偏低**（即使有真实相关也
会被压小）。两种估计各有缺陷：

```text
                biased (/N)              unbiased (/N-k)
期望            (N-k)/N · R[k]           R[k]  ← 无偏
大 lag 行为     整体偏低（真实相关被压）  方差大（噪声地板抬高）
适用场景        看谱形（Wiener-Khinchin） 看小 lag 数值
本库选择                                 ✓ 用这个
```

##### 5.2.2 看图建议：只关注 lag < N/10

基于 § 5.2.1 的副作用，正确的看图姿势是：

```text
1. 只关注小 lag 区域，通常 lag < N/10
   -> 这区域 unbiased 的放大因子 < 1.11，几乎无影响
   -> 真实的 memory effect / 短期相关都在这里

2. 大 lag 的非零值默认当成估计噪声
   -> 不要看到 lag=N/2 处有"峰"就以为是周期干扰
   -> 除非这个峰在多次独立测量中都稳定出现

3. max_lag 的设置影响能看到的最大周期
   -> max_lag 默认 50，能检测周期 < 50 的干扰
   -> 怀疑低频干扰时增大 max_lag（但要意识到大 lag 的噪声也变大）

4. 区分"周期峰"和"噪声峰"
   -> 周期峰：在 lag = T, 2T, 3T, ... 等整数倍处规律出现
   -> 噪声峰：随机位置出现，多次测量不一致
```

##### 5.2.3 为什么本库选 unbiased 而不是 biased

```text
1. 小 lag 数值更准
   -> ADC 诊断主要关心短期 memory（lag < 10），不关心大 lag
   -> 这区域 unbiased 无偏，biased 有 (N-k)/N 偏差（虽然小）

2. 和 MATLAB 的 xcorr 默认一致
   -> 代码注释明确写 "consistent with MATLAB implementation"
   -> 便于和 MATLAB 工具链对照

3. 大 lag 副作用可以用"看图指南"规避（§ 5.2.2）
   -> 不是数学错误，是使用时的注意事项
```

总结：**unbiased 估计不是原理性问题**（数学上合法、无偏），但有实际副作用（大 lag
方差大）。看图时只关注 lag < N/10 就能规避这个副作用。如果要做严格的功率谱估计
（Wiener-Khinchin），biased 估计更合适——但那是 Stage 02 的频谱分析范畴，不是
Stage 03 的 ACF 诊断用途。

#### 5.3 三种典型 error 的 ACF 形状

**white noise（理想随机噪声）→ R[k] = δ[k]**

零均值白噪声的定义就是"不同样本不相关"：

```text
R[k] = E[e[n]·e[n+k]] = σ²·δ[k]
     = σ²,  k=0
     = 0,   k≠0
```

归一化后就是 `R[0]=1, R[k≠0]=0`。看图是一根孤立的尖峰，其它 lag 全是 0 附近的
随机噪声。**这是 thermal noise 主导的标志特征**。

**memory effect → 小 lag 上 R[k] 明显非零**

如果 error 有"惯性"——当前样本受前一状态影响（比如 reference settling 没完成、
sampling capacitor 残留电荷），相邻样本会相关：

```text
R[1], R[2], R[3] ... 在小 lag 上明显 > 0
随 lag 增大缓慢衰减（exponential decay）
```

一阶 AR 模型 `e[n] = α·e[n-1] + w[n]` 的 ACF 是 `R[k] = σ²·α^|k|`，指数衰减。
α 越大衰减越慢，memory 越强。

**periodic interference → ACF 周期性峰**

如果 error 含有固定频率成分（比如时钟馈通、电源耦合），ACF 也会周期性出现峰：

```text
R[k] 在 k = period, 2·period, 3·period, ... 处出现峰
```

这和 error spectrum 的关系是**Wiener-Khinchin 定理**：

```text
ACF 的 FFT = power spectrum（功率谱）
```

所以 ACF 上的周期峰 ⟺ spectrum 上的固定频率 spur。它们是同一现象的两种看法。
区别是 ACF 直接看时间结构，spectrum 直接看频率结构。

#### 5.4 ACF 看图判据

| ACF 形状 | 可能含义 |
|---|---|
| R[0]=1, 其它 lag 全 ≈ 0 | 白噪声主导（理想）|
| 小 lag 上明显 > 0，指数衰减 | memory effect（settling / reference droop）|
| 某个固定 lag 周期出现峰 | 周期性干扰（clock feedthrough / 电源耦合）|
| 负值明显（R[k]<0）| 交替结构（比如奇偶不对称、over-correction）|
| 噪声水平高、看不出结构 | 数据太短或随机噪声过大，需要更多样本 |

代码里 `max_lag` 默认 50。如果怀疑低频干扰（周期很长），要增大 `max_lag`；
如果只关心局部 memory，`max_lag=20` 就够。

### 6. Error spectrum：误差里有没有确定性频率成分

error spectrum 是对 `error[n]` 再做一次 FFT。它回答：

```text
error 里有哪些频率成分？它们的幅度多大？
```

#### 6.0 error spectrum 和 ACF 的关系：为什么两者都需要

读完 § 5 ACF 再读这一节，自然会问：ACF 已经衡量了"时间结构"，error spectrum 又
衡量"频率结构"，**两者是不是重合？** 答案是：数学上对偶，工程上互补，不可互相
替代。这个关系背后的核心是 **Wiener-Khinchin 定理**。

##### 6.0.1 数学等价：ACF 和功率谱是同一信息的两种表示

对零均值广义平稳随机过程 `e[n]`，Wiener-Khinchin 定理：

```text
S_e(ω) = Σ_k R[k] · exp(-jωk)              (ACF 的 DTFT = 功率谱)
R[k]   = (1/2π) ∫ S_e(ω) · exp(jωk) dω     (功率谱的逆 DTFT = ACF)

其中:
    R[k]   = 自相关函数（§ 5）
    S_e(ω) = 功率谱密度（PSD）
```

所以从**信息含量**看，ACF 和 PSD 完全等价——知道一个就能算出另一个，没有信息
丢失。这正是初学者直觉感到"两者重合"的根源。

##### 6.0.2 但工程用途完全互补

虽然信息等价，**人类眼睛和工程判断对两种表示的敏感度完全不同**。这是两者都存在
的原因。具体看四层分工：

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

关键对比：**一个 10 MHz 的时钟馈通 spur**。
- ACF：在 `lag = Fs/10MHz` 的整数倍处出现峰。看图要先数峰间距，再算 `1/间距`
  才知道频率。
- spectrum：在 10 MHz 处直接看到一根尖峰，频率读出来就是 10 MHz。

反过来：**一个一阶 AR memory effect**（`e[n] = α·e[n-1] + w[n]`）。
- ACF：`R[k] = σ²·α^|k|`，指数衰减，**α 直接从衰减速率读出**。
- spectrum：`S(ω) = σ²/(1-2αcos(ω)+α²)`，是平滑形状，没有尖峰，**α 不容易直接读**。

**分工 2：spectrum 频率分辨率远高于 ACF**

spectrum 是 N/2 个 bin，每个 bin 是一个独立频率点。ACF 通常只算 `max_lag` 个 lag
（代码默认 50）。所以 spectrum 的频率分辨率远高于 ACF：

```text
N = 8192, Fs = 100 MHz:
    spectrum: 4096 个 bin，每个 bin 宽 12.2 kHz
        -> 能分辨相隔 12.2 kHz 的两个 spur
    ACF (max_lag=50): 只有 51 个 lag
        -> 能分辨的最低频率是 Fs/50 = 2 MHz
        -> 相隔 100 kHz 的两个 spur 在 ACF 里分不开
```

所以看**密集谐波系列、密集 spur、jitter 裙边**必须用 spectrum，ACF 分不开。

**分工 3：ACF 大 lag 不可靠（§ 5.2 讲过）**

§ 5.2 推导过：unbiased ACF 估计让大 lag 方差大（归一化后被 `N/(N-k)` 放大）。
所以 ACF 只能看小 lag（lag < N/10），看不了低频细节。

spectrum 的低频 bin 是独立测量，没有这个"大 lag 不可靠"问题。所以看**低频 drift、
1/f noise**用 spectrum 更可靠。

**分工 4：spectrum 对非平稳信号敏感，ACF 对瞬态更鲁棒**

error spectrum 是对 `error[n]` 做 FFT 幅度谱，假设信号平稳（整个 N 点统计性质
不变）。如果 error 含**瞬态事件**（glitch、突发干扰），FFT 会把它散到所有 bin，
形状误导：

```text
单个 glitch (脉冲):
    spectrum: 整个频谱被拉高（白噪声形状），看不出是瞬态
    ACF:      R[k] 在所有 lag 上都有泄漏，但 R[0] 特别突出
              -> 能看出是脉冲性质
```

ACF 对瞬态更鲁棒，因为它本质是时间平均，瞬态在 ACF 里的表现是可识别的。

##### 6.0.3 一个精确的差别：FFT 幅度谱 vs PSD

Wiener-Khinchin 连的是 ACF 和 **PSD（功率谱密度）**。但 `analyze_error_spectrum`
做的是 **FFT 幅度谱**（带 window、归一化），不是严格的 PSD。差别：

```text
PSD (power spectral density):
    定义: S(ω) = lim_{T→∞} E[|X_T(ω)|²] / T
    -> 理论量，无限长平均
    -> 和 ACF 严格 Wiener-Khinchin 对偶

FFT 幅度谱 (analyze_error_spectrum 实际做的):
    -> 有限 N，乘 window，一次 FFT
    -> 是 PSD 的一个有限样本估计
    -> 含 phase 信息（如果保留的话），不只是功率
    -> 对非平稳信号敏感
```

所以 `analyze_error_spectrum` 和 `analyze_error_autocorr` 之间不是严格的
Wiener-Khinchin 对偶，而是"两种从同一组数据提取不同诊断信息的工具"。信息有重叠
（都基于 R[k] 和 S(ω) 的对偶），但实现和侧重点不同。

##### 6.0.4 实际工作流

```text
先看 spectrum 提出频率假设
    -> 发现某个频率的 spur / 裙边 / 低频抬升
-> 再看 ACF 验证时间结构
    -> 这个频率成分是不是稳定的周期（ACF 周期峰）
    -> 还是只是统计噪声（ACF 没有对应结构）
-> 两者一致才下结论
```

一句话总结：

```text
ACF 和 spectrum 数学等价（Wiener-Khinchin），
但工程用途互补（时间结构 vs 频率结构）。
信息有重叠，但任何一方都不能单独替代另一方。
```

#### 6.1 error spectrum 和原始 signal spectrum 的区别

这是 Stage 03 最容易混淆的点。两个 spectrum 看的都是频域，但对象完全不同：

```text
原始 signal spectrum (Stage 02):
    对 y[n] 做 FFT
    -> 看到 fundamental + harmonic + noise + spur + DC
    -> fundamental 占绝大部分能量，淹没了小误差

error spectrum (Stage 03):
    对 error[n] = y[n] - fitted_sine[n] 做 FFT
    -> fundamental 已经被减掉
    -> 看到的是 error 内部的频率结构
    -> 小 spur / harmonic / memory pattern 更清楚
```

打个比方：原始 spectrum 像在摇滚演唱会里找蚊子的声音——主唱（fundamental）太响，
蚊子（小 error）听不见。error spectrum 是先把主唱歌声滤掉，剩下的蚊子和背景噪声
就清楚了。

#### 6.2 error spectrum 看什么

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

#### 6.3 对应到 analyze_error_spectrum 代码

`python/src/adctoolbox/aout/analyze_error_spectrum.py` 的核心：

```python
# 1. 拟合 ideal sine
fit_result = fit_sine_4param(signal)
sig_ideal = fit_result['fitted_signal']

# 2. 减掉主信号
error_signal = signal - sig_ideal

# 3. 对 error 做 FFT 分析
result = analyze_spectrum(error_signal, fs=fs, max_harmonic=5)
```

注意第 3 步直接复用了 Stage 02 学过的 `analyze_spectrum`。所以 error spectrum 的
所有概念（window、leakage、bin、side_bin、dBFS）都和 Stage 02 一致，区别只是输入
从 signal 换成了 error。

返回字段也和 Stage 02 一致（enob, sndr_db, sfdr_db, snr_db, thd_db, ...），但
**含义变了**：这里的 SNDR 是"error 相对于什么"，不是原信号的 SNDR。实际使用时要
注意——error spectrum 主要看**形状**（有没有尖峰、哪里抬升），指标数字是次要的。

#### 6.4 一个陷阱：fit 频率不准时的假结构

如果 `fit_sine_4param` 的频率估计和真实主频有偏差，减掉 fitted sine 后会留下一个
"准主频"残差——它的幅度小，但在 error spectrum 里表现为 fundamental 附近的尖峰。
这个尖峰不是真实 ADC 问题，而是 fit 不够好。

判断方法：

```text
真实 harmonic:
    在 2f, 3f, 4f, ... 整数倍处
    幅度和 fit 质量无关

fit 残差（假结构）:
    只在 fundamental 附近
    改变 fit 的 max_iterations 后会消失或移动
```

所以看 error spectrum 时，fundamental 附近的尖峰要先怀疑 fit 质量；远离 fundamental
的尖峰才更可能是真实 ADC 问题。`fit_sine_4param` 默认 `max_iterations=1`，对噪声
大的数据可能不够，可以增大到 3-5。

## 电路需要理解什么

这一节把实验 2（exp_a21）的 15 种非理想按**物理机制**分成 4 类，逐类讲清"这个噪声/
失真是什么、从哪个电路来、为什么在 PDF/ACF/spectrum 上是这个样子"。这是 Stage 03
从"看图形态"到"归因到电路"的关键一步。

具体的电路建模（CDAC 权重怎么算、comparator noise 怎么进 bit decision、SAR bit trial
的细节）属于 Stage 04 的范畴；这里只要求建立"residual 形态 → 电路问题类别"的直觉。

### 0. 快速索引：15 种非理想的 residual 指纹

按实验 2 的实测结果（KL 从小到大排序）：

| 类别 | 非理想 | sigma (LSB) | KL | PDF 形状 | 最敏感工具 |
|---|---|---|---|---|---|
| 随机噪声 | Thermal Noise | 0.75 | 0.0002 | 完美 Gaussian | PDF（基准）|
| 随机噪声 | Quantization | 1.17 | 0.12 | 平顶 | PDF |
| 随机噪声 | Jitter | 1.77 | 0.05 | 近 Gaussian | spectrum 裙边 |
| 静态非线性 | Static HD2 (-80dBc) | 0.15 | 0.13 | 不对称 | spectrum / by_value |
| 静态非线性 | Static HD3 (-70dBc) | 0.46 | 0.26 | 结构明显 | spectrum / by_value |
| 静态非线性 | Clipping | 0.11 | 0.72 | 边缘堆积 | PDF |
| 动态/记忆 | Memory Effect | 0.71 | 0.03 | 近 Gaussian | **ACF** |
| 动态/记忆 | Incomplete Settling | 0.09 | 0.04 | 近 Gaussian | **ACF / by_value** |
| 动态/记忆 | Reference Error | 0.68 | 0.23 | 不对称 | ACF / by_value |
| 调制/干扰 | AM Noise | 0.72 | 0.05 | 近 Gaussian | **by_phase** |
| 调制/干扰 | AM Tone (5%) | 48.8 | 0.06 | 近 Gaussian | **spectrum spur** |
| 调制/干扰 | RA Gain Error | 4.76 | 0.09 | 轻双峰 | by_value |
| 调制/干扰 | RA Dynamic Gain | 14.1 | 0.08 | 近 Gaussian | spectrum / by_value |
| 调制/干扰 | Drift | 9.87 | 0.21 | 宽峰 | 时域图 / spectrum 低频 |
| 调制/干扰 | Glitch | 17.1 | 1.69 | 长尾 | **PDF** |

这张表最右边一列是关键——**每种非理想都有一个"最敏感工具"**，对应它在哪个分析图
上最容易被识别。PDF 不是万能的，后面会看到很多非理想在 PDF 上是盲点。

### 1. 随机噪声类（stochastic，不可校准）

这一类的共同特征：**误差是真正随机的，每次测量不同，只能用统计量（RMS、PDF、
PSD）描述**。它们决定了 ADC 的 noise floor，是 SNR 的根本限制。

#### 1.1 Thermal Noise（热噪声）

**来源**：电阻、开关、采样电容里电子的热运动。本库 `apply_thermal_noise(noise_rms)`
直接加零均值高斯白噪声。

**电路图像**：任何导体里的电子都在做布朗运动（温度 > 0K），瞬时形成随机电压。
这个随机电压在采样瞬间被"冻结"进采样电容，叠加到信号上。

**代码建模**（`siggen/nonidealities.py` 第 56-60 行）：

```python
noise = np.random.randn(self.N) * noise_rms
return signal + noise
```

转成数学公式：

```text
e[n] = w[n],   w[n] ~ N(0, noise_rms²)    独立同分布高斯
y[n] = x[n] + e[n]                          加性噪声
```

**关键**：每个 `e[n]` 独立抽取——`e[n]` 和 `e[n-1]` 无关。这是**真随机**。

**为什么是 Gaussian**：每一时刻的总热噪声是海量独立小扰动（每个电子的贡献）相加。
中心极限定理保证：N 个独立同分布随机变量之和趋向高斯，不论每个小扰动是什么分布。

**residual 特征**：

```text
PDF:    完美 Gaussian（KL ≈ 0）
ACF:    白噪声 δ[k]（除 lag=0 外全为 0，因为 e[n] 独立）
spectrum: 平坦 noise floor
```

实验 2 的 Thermal Noise case KL=0.0002，是所有 case 里最小的——这就是 Gaussian 拟合
的"基准线"。其它 case 的 KL 都要和这个比。

**诊断意义**：如果 ADC 测出来 KL < 0.01 且 ACF 是白噪声，基本可以判断"随机噪声主导"。

#### 1.2 Quantization Noise（量化噪声）

**来源**：有限 bit 数导致的舍入误差。本库 `apply_quantization_noise(n_bits)`
模拟 floor-based 量化（lower-edge reconstruction，见 Stage 01）。

**电路图像**：ADC 的 N-bit 比较器只能分辨 2^N 个离散电平。连续输入被"归到"最近的
code，产生不超过 1 LSB 的误差。

**代码建模**（`siggen/nonidealities.py` 第 62-77 行）：

```python
lsb = (v_max - v_min) / (2 ** n_bits)              # LSB 步长
codes = np.floor((signal - v_min) / lsb)           # 连续值 → code（floor）
codes = np.clip(codes, 0, 2**n_bits - 1)           # 饱和保护
return codes * lsb + v_min                         # code → 重建电压（lower-edge）
```

转成数学公式：

```text
code[n]  = floor((x[n] - v_min) / LSB)
y[n]     = code[n] · LSB + v_min                  ← lower-edge 重建

e[n]     = x[n] - y[n]
         = x[n] - (floor((x[n]-v_min)/LSB)·LSB + v_min)
         ∈ [-LSB, 0]                               ← 注意是 [-LSB, 0]，不是 [-LSB/2, +LSB/2]
```

去均值后（`e[n] + LSB/2`）才是对称的 `Uniform(-LSB/2, +LSB/2)`。

**关键**：`e[n]` 只取决于 `x[n]` 落在哪个 LSB 区间，**不依赖历史**——所以量化
噪声样本间独立（前提是输入跨过足够多 code，见 Stage 01 的 dither 讨论）。

**为什么是 Uniform**（Stage 01 + § 4.1 详细推导）：量化误差 = 输入相对于 LSB 区间
中心的偏移。只要输入跨过足够多 code、不超量程，输入在每个区间内的位置均匀，误差
就在 [-LSB/2, +LSB/2] 上均匀分布。

**residual 特征**：

```text
PDF:    平顶（Uniform），不是 Gaussian
        KL 中等（~0.12），明显大于 thermal
ACF:    近似白噪声（量化误差和输入近似不相关时）
spectrum: 平坦，但和 thermal 的"连续平坦"略有差别（量化可能有弱谐波）
```

**实验 2 的陷阱**：Quantization case 的 sigma=1.17 LSB，看起来比理论 `1/√12≈0.29`
大 4 倍。原因是信号用 10-bit 量化，但 PDF 分析用 12-bit resolution——LSB 定义不一致。
这印证了 § 4.4：**resolution 必须传对，否则 sigma 会误导**。

#### 1.3 Jitter Noise（时钟抖动噪声）

**来源**：采样时刻的随机抖动。本库 `apply_jitter(jitter_rms)` 模拟 aperture jitter。

**电路图像**：采样开关的时钟沿不是无限陡的，实际采样时刻在理想时刻附近抖动
`δt[n]`。这个抖动来自时钟源的 phase noise、电源噪声耦合到时钟链。

**代码建模**（`siggen/nonidealities.py` 第 79-100 行）：

```python
t_jitter = np.random.randn(self.N) * jitter_rms       # 采样时刻偏移
# Case 1（input_signal=None）: 完美数学重生成
total_phase = 2π · Fin · (t + t_jitter)
return A · sin(total_phase) + DC
```

转成数学公式：

```text
δt[n] ~ N(0, jitter_rms²)                            独立同分布
y[n] = A · sin(2π·Fin·(t[n] + δt[n])) + DC

线性化（Stage 02 § 4.1 推导，当 2π·Fin·δt 很小时）:
y[n] ≈ A·sin(2π·Fin·t[n]) + A·cos(2π·Fin·t[n])·2π·Fin·δt[n]
       = x[n] + (dx/dt)|_{t[n]} · δt[n]
              ↑ 信号斜率 × 时间抖动

e[n] = (dx/dt)|_{t[n]} · δt[n] = 2π·Fin·A·cos(2π·Fin·t[n]) · δt[n]
```

**关键**：`e[n]` = 确定性斜率（cos 包络）× 随机时间抖动。斜率 ∝ Fin，所以高频
输入对 jitter 更敏感（Stage 02 § 4.1）。δt[n] 独立 → e[n] 样本间独立（白噪声）。

**为什么 PDF 接近 Gaussian**：δt 是高斯的，乘上确定性的 cos(ωt) 后，边际分布仍接近
高斯（高斯 × 确定性 = 高斯，只是方差被 cos²(ωt) 的平均 1/2 调制）。

**residual 特征**：

```text
PDF:    近 Gaussian（KL ≈ 0.05，略大于 thermal）
        -> PDF 几乎看不出 jitter
ACF:    近白噪声（jitter 是样本独立的）
spectrum: fundamental 两侧"裙边"抬起（Stage 02 § 4.2 推导）
          -> 这是 jitter 的标志特征
```

**诊断意义**：jitter 是 PDF 的盲点——KL 才 0.05，和 thermal 几乎一样。要诊断 jitter
必须看 spectrum 的裙边形状，或扫输入频率（jitter 随 Fin 变化，thermal 不变）。


### 2. 静态非线性类（deterministic，可校准）

这一类的共同特征：**误差是输入信号的确定性函数，e = f(vin)**。同一输入永远产生
同一误差，重复测量不变。它们产生 harmonic distortion，是 THD/SFDR 的主要来源。

#### 2.1 Static HD2 / HD3（静态谐波失真）

**来源**：ADC 前端（input buffer、sampling switch）或 CDAC 的非线性传递特性。本库
`apply_static_nonlinearity(k2, k3)` 模拟多项式非线性。

**电路图像**：输入 buffer 的增益不是严格常数，而是随输入幅度变化（MOS 管的非线性
跨导、结电容的非线性）。这种"增益随输入变"用多项式拟合：

**代码建模**（`siggen/nonidealities.py` 第 102-120 行）：

```python
signal_ac = signal - self.DC                            # 去 DC
distortion = np.zeros_like(signal_ac)
if k2 != 0: distortion += k2 * (signal_ac ** 2)         # 二阶项
if k3 != 0: distortion += k3 * (signal_ac ** 3)         # 三阶项
signal_distorted = signal_ac + distortion
return signal_distorted + self.DC
```

转成数学公式：

```text
y[n] = x[n] + k2·(x[n]-DC)² + k3·(x[n]-DC)³ + ...

对正弦输入 x[n] - DC = A·sin(ωt):
(A·sin(ωt))² = A²/2 - (A²/2)·cos(2ωt)                   → DC 偏移 + HD2
(A·sin(ωt))³ = (3A³/4)·sin(ωt) - (A³/4)·sin(3ωt)        → fundamental 增强 + HD3

所以:
  k2 产生: DC 偏移 + HD2 (在 2ω 处)
  k3 产生: fundamental 失真 + HD3 (在 3ω 处)
```

**误差表达式**：

```text
e[n] = y[n] - x[n] = k2·(x[n]-DC)² + k3·(x[n]-DC)³ + ...
```

e[n] 是输入的**确定性函数**——同一输入永远产生同一误差，重复测量不变。

**为什么 PDF 有结构**：误差是 cos(2ωt) 或 sin(3ωt) 的确定性函数。对纯余弦，瞬时值
在 ±1 附近停留久、在 0 附近停留短（§ 4.1 推导），PDF 呈 U 形 `1/(π√(1-x²))`。
实验 2 HD2/HD3 的 PDF 就是从 Gaussian 朝 U 形偏移。

**为什么 HD3 的 KL > HD2**：奇阶非线性（x³）在 fundamental 频率上有分量（影响 fit），
偶阶（x²）只有 DC + HD2（正交于 fundamental）。所以 HD3 对 PDF 形状的扰动更强。

**residual 特征**：

```text
PDF:    不对称（HD2）或结构明显（HD3）
        KL: HD2 ≈ 0.13, HD3 ≈ 0.26
ACF:    有周期性结构（harmonic 是确定性周期信号）
spectrum: 在 2f, 3f 处有明显 spur（最直接）
```

**诊断意义**：spectrum 是诊断 harmonic 最直接的工具（直接看 2f/3f 的 spur）。PDF 能
检测到"有结构"，但分不清是几阶。KL 对弱 harmonic 极其灵敏——-80dBc 的 HD2 让 KL
从 0.0002 涨到 0.13，放大了 650 倍。

#### 2.2 Clipping（削顶/饱和）

**来源**：输入幅度超过 ADC 量程，被硬截断。本库 `apply_clipping(percentile_clip)`
模拟硬限幅。

**电路图像**：ADC 的 input range 是 [v_min, v_max]，超过这个范围比较器饱和，输出
被钳位在边界。这是**强非线性**——输入/输出曲线在饱和区是平的。

**代码建模**（`siggen/nonidealities.py` 第 258-270 行）：

```python
lower_threshold = np.percentile(signal, percentile_clip)        # 动态阈值
upper_threshold = np.percentile(signal, 100.0 - percentile_clip)
signal_clipped = np.clip(signal, lower_threshold, upper_threshold)  # 硬钳位
```

转成数学公式：

```text
y[n] = clip(x[n], lower, upper)
     = lower,        if x[n] < lower
       x[n],         if lower ≤ x[n] ≤ upper     ← 线性区，无失真
       upper,        if x[n] > upper              ← 饱和区

e[n] = x[n] - y[n]
     = x[n] - lower,  if x[n] < lower             ← 正误差（被压低）
       0,             if 线性区                   ← 无误差
       x[n] - upper,  if x[n] > upper             ← 负误差（被压高）
```

**关键**：clipping 只影响"超出阈值"的少量样本（实验 2 是上下各 1%）。但被截断的
样本本来分布在 [lower, -∞] 和 [upper, +∞]，现在全部"堆积"在 lower / upper 边界。

**为什么 PDF 有"边缘堆积"**：所有超过边界的样本被压到边界值，形成 Gaussian 没有
的尖峰。中心部分仍像 Gaussian（95% 样本在线性区），但两头有明显的堆积尖峰。

**residual 特征**：

```text
PDF:    边缘堆积（在 ±max 处出现尖峰）
        KL 极大（≈0.72），sigma 反而小（只影响截断的少量样本）
ACF:    有周期性结构（clipping 发生在波峰/波谷，和 fundamental 同步）
spectrum: 出现大量奇阶谐波（clipping 类似方波化，rich in odd harmonics）
```

**诊断意义**：clipping 是"sigma 小但 KL 极大"的典型。只看 sigma 会漏诊，只看 PDF
（边缘堆积）或 spectrum（奇阶谐波系列）能立刻发现。

**关键对比**：
```text
Static HD2/HD3: 弱非线性，sigma 小 KL 中等，spectrum 有单根 spur
Clipping:        强非线性，sigma 小 KL 极大，spectrum 有奇阶谐波系列
```

### 3. 动态/记忆效应类（error 和前一状态相关）

这一类的共同特征：**误差不是当前输入的函数，而是当前输入 + 历史状态的函数**，
`e[n] = f(vin[n], vin[n-1], ...)`。它们让相邻样本相关，是 ACF 的主要诊断对象。

#### 3.1 Memory Effect（记忆效应）

**来源**：采样电容残留电荷、前端放大器的有限带宽、switch charge injection 的历史
依赖。本库 `apply_memory_effect(memory_strength)` 模拟。

**电路图像**：两-stage pipelined ADC 里，上一拍的 MSB decision（粗量化结果）通过
寄生电容或 charge injection 泄漏回输入端，污染下一拍的采样。下一拍采到的电压 =
真实输入 + 上一拍 MSB 的残留。

**代码建模**（`siggen/nonidealities.py` 第 138-149 行）：

```python
msb = np.floor(signal * 2**4) / 2**4         # 当前 signal 的 4-bit 粗量化
lsb = np.floor((signal - msb) * 2**12) / 2**12  # 剩余部分 12-bit 细量化
msb_shifted = np.roll(msb, shift=1)          # 上一拍的 MSB
return msb + lsb + memory_strength * msb_shifted
```

转成数学公式：

```text
msb[n]   = floor(signal[n] · 2^4) / 2^4                    ← 当前粗量化
lsb[n]   = floor((signal[n] - msb[n]) · 2^12) / 2^12       ← 当前细量化
y[n]     = msb[n] + lsb[n] + α · msb[n-1]
                                      ↑
                            memory_strength · 上一拍 MSB
```

所以误差是：

```text
e[n] = y[n] - signal[n]
     = msb[n] + lsb[n] + α·msb[n-1] - signal[n]
     = (msb[n] + lsb[n] - signal[n])   +   α·msb[n-1]
       ↑ 这部分是量化误差（小）          ↑ memory 残留（和上一拍相关）
```

**关键**：误差显式依赖 `msb[n-1]`（前一个样本的 MSB）。给定相同的输入序列，
`msb[n-1]` 完全确定 → **memory effect 不是真随机，是确定性状态依赖**。

**为什么 PDF 看不出来**：memory effect 改变的是**样本间的时间相关性**，不是瞬时
幅度分布。`msb[n-1]` 在大量样本上覆盖多个 code，边际分布接近均匀/高斯混合，所以
PDF 的 KL 很小（≈0.03）。但 ACF 能检测出"e[n] 和 e[n-1] 通过 msb[n-1] 相关"。

**residual 特征**：

```text
PDF:    近 Gaussian（KL ≈ 0.03）→ 盲点
ACF:    小 lag 上 R[k] > 0
        R[1] 明显非零（因为 e[n] 直接依赖 msb[n-1]）
        R[2], R[3] 也有结构（msb[n-1] 本身有相关性）
        不是严格的指数衰减（因为 msb 是离散量化值）
spectrum: 低频抬升 + 弱谐波（memory 引入了输入相关的残留）
```

**诊断意义**：memory effect 是 ACF 的"招牌 case"。实验 3（ACF）会清楚看到它的
R[k] 在小 lag 上明显非零。这是 PDF 的典型盲点。

**和 AR(1) 模型的区别**：教科书常把 memory effect 简化成一阶 IIR `e[n] = α·e[n-1] + w[n]`，
它的 ACF 是严格指数衰减。但本库代码模型是"上一拍 MSB 泄漏"——msb 是离散量化值，
所以 ACF 不是光滑指数衰减，而是有量化痕迹的结构。这是代码和简化模型的差别。

#### 3.2 Incomplete Settling（建立不完整）

**来源**：采样开关的 on-resistance + 采样电容组成 RC 电路，采样时间不够时电压
没充到最终值。本库 `apply_incomplete_sampling(T_track, coeff_k)` 模拟有限建立时间。

**电路图像**：采样开关闭合瞬间，信号通过开关电阻 R 给电容 C 充电。RC 时间常数
τ = RC。如果采样时间 T_track 不够大，电容电压没充到输入值就断开了——而且输入
幅度大时 slew rate 限制让建立更慢，所以误差**和输入幅度相关**。

**代码建模**（`siggen/nonidealities.py` 第 151-169 行）：

```python
v_prev = 0
for n in range(self.N):
    v_target = signal_ac[n]
    tau_dynamic = tau_nom * (1 + coeff_k * v_target ** 2)    # 信号依赖的时间常数
    vout[n] = v_target + (v_prev - v_target) * np.exp(-T_track / tau_dynamic)
    v_prev = vout[n]
```

转成数学公式：

```text
τ_dynamic[n] = τ_nom · (1 + coeff_k · v_target²)            ← 信号依赖的 τ
y[n] = v_target[n] + (y[n-1] - v_target[n]) · exp(-T_track / τ_dynamic[n])
                           ↑
                    前一拍的输出（建立起点）

误差:
e[n] = y[n] - x[n]
     = (y[n-1] - x[n]) · exp(-T_track / τ_dynamic[n])
       ↑                    ↑
       前一状态              建立不足的比例
```

**关键**：误差同时依赖 `y[n-1]`（前一拍输出）和 `v_target[n]`（当前输入）。而且
`τ_dynamic` 随 `v_target²` 变化——大信号时 τ 更大，建立更不足。这让误差既**有时间
相关性**（依赖 y[n-1]），又**有幅度依赖**（依赖 v_target）。

**和 memory effect 的区别**：
```text
memory effect:        残留来自上一拍的 MSB decision（量化值泄漏）
incomplete settling:  残留来自前一拍的输出电压（RC 充电未完成）
两者都让 e[n] 和历史相关，但物理来源不同
settling 还额外有"幅度依赖"（coeff_k · v² 让 τ 动态变化）
```

**residual 特征**：

```text
PDF:    近 Gaussian（KL ≈ 0.04）→ 盲点
        sigma 很小（0.09 LSB，建立误差本身幅度小）
ACF:    有结构（建立不足让相邻样本相关）
spectrum: 可能有和输入幅度相关的 HD3（tau_dynamic 的 v² 项产生奇阶非线性）
by_value: 能看到 error 随输入幅度变化（大跳变后建立更不足）← 标志特征
```

**诊断意义**：incomplete settling 的 sigma 最小（0.09 LSB），单看 PDF/sigma 会漏诊。
必须看 ACF（时间相关）或 by_value（幅度依赖）。

#### 3.3 Reference Error（基准误差）

**来源**：ADC 的电压基准（reference driver）在转换期间不稳定——settling 不足 +
droop（电容被消耗导致基准电压下垂）。本库 `apply_reference_error(settling_tau,
droop_strength)` 模拟。

**电路图像**：ADC 内部的电压基准 Vref 通过一个大电容稳定。但 CDAC 每次切换都从
Vref 抽取/注入电荷，如果 reference driver 带不动（带宽不够），Vref 会暂时下垂。
这个下垂在记录期间累积（IIR 衰减），影响后续所有 bit trial 的判断基准。

**代码建模**（`siggen/nonidealities.py` 第 208-230 行）：

```python
current_kick = droop_strength * np.abs(signal_ac)          # 每个样本的 kick（和 |signal| 成正比）
decay = np.exp(-1.0 / settling_tau)                        # IIR 衰减系数
vref_droop = lfilter([1], [1, -decay], current_kick)       # 一阶 IIR 滤波
signal_settled = signal * (1.0 - vref_droop)               # 信号被 Vref droop 调制
```

转成数学公式：

```text
kick[n]    = droop_strength · |x[n]|                       每拍的电荷抽取
decay      = exp(-1/settling_tau)                          IIR 衰减

vref_droop[n] = kick[n] + decay · vref_droop[n-1]          ← 一阶 IIR（累积）
              = Σ_{k=0}^{n} decay^k · kick[n-k]            ← 累积和

y[n] = x[n] · (1 - vref_droop[n])

误差:
e[n] = x[n] - y[n] = x[n] · vref_droop[n]
                      ↑
              信号 × 累积的基准下垂（乘性！）
```

**关键**：误差是**乘性**的（`x[n] · vref_droop[n]`），不是加性。而且 vref_droop 是
kick 序列的 IIR 累积——**长记忆**（settling_tau 大时记忆更长）。这让误差既依赖当前
信号幅度，又依赖历史信号的累积。

**为什么 KL 较大（0.23）**：reference error 让 ADC 的"有效满量程"在记录期间漂移，
这种慢漂移让 PDF 出现宽峰或不对称（不同时段的"局部增益"不同）。而且乘性结构
（x · droop）让 PDF 形状偏离 Gaussian 更明显。

**residual 特征**：

```text
PDF:    不对称或宽峰（KL ≈ 0.23，比 memory/settling 大）
ACF:    有结构，长程相关（IIR 累积，settling_tau 大时 R[k] 衰减慢）
spectrum: 低频成分（droop 是慢变化，IIR 的低通特性）
by_value: 误差随输入累积幅度变化（乘性）
```

**诊断意义**：reference error 是 memory 类里 PDF 最敏感的（KL=0.23）。但要和
"真正的 harmonic"区分，需要看 ACF（memory 有小 lag 相关 + 长程衰减，harmonic 有周期峰）。


### 4. 调制/外部干扰类（乘性或周期性）

这一类的共同特征：**误差不是简单的加性噪声，而是信号被某种调制或外部干扰污染**。
它们让误差和信号的幅度/相位/频率耦合，是 fit 和 PDF 的盲点重灾区。

#### 4.1 AM Noise / AM Tone（幅度调制）

**来源**：
- AM Noise：电源纹波、温度波动让 ADC 增益随机波动（本库 `apply_am_noise`）
- AM Tone：某个固定频率（如电源 50Hz/60Hz、开关频率）对信号做确定性调幅
  （本库 `apply_am_tone`）

**电路图像**：ADC 的增益（input buffer 跨导、reference 电压）不是严格恒定，而是
被某个低频信号调制。这个调制信号来自电源纹波、温度波动（AM Noise）或某个固定
干扰源（AM Tone）。

**代码建模 AM Noise**（`siggen/nonidealities.py` 第 232-248 行）：

```python
am_envelope = 1 + strength * np.random.normal(0, 1, len(self.t))   # 随机增益波动
signal_am = signal_ac * am_envelope                                 # 乘性调制
```

**代码建模 AM Tone**（第 250-256 行）：

```python
am_tone_env = 1 + am_tone_depth * np.sin(2π · am_tone_freq · t)   # 确定性调幅
signal_am = signal_ac * am_tone_env
```

两者形式统一，转成数学公式：

```text
AM Noise:    m[n] = 1 + strength·w[n],        w[n] ~ N(0,1)        随机调制
AM Tone:     m[n] = 1 + depth·sin(2π·fm·t[n])                      确定性调制

y[n] = m[n] · (x[n] - DC)

误差:
e[n] = y[n] - x[n] = (m[n] - 1)·(x[n] - DC)
                     ↑              ↑
                  调制分量         信号 AC 部分
```

**关键**：误差是**乘性**的（调制 × 信号），不是加性。这是 AM 和 thermal/jitter 的
本质区别——thermal 是 `x + w`，AM 是 `x · (1 + m)`。

**用积化和差展开 AM Tone**：

```text
e[n] = depth·sin(2π·fm·t) · A·sin(2π·f·t)
     = (depth·A/2) · [cos(2π(f-fm)t) - cos(2π(f+fm)t)]
                      ↑                    ↑
                  下边带 (f-fm)        上边带 (f+fm)
```

所以 AM Tone 的误差是**两个边带**（在 f±fm 处），不是加性噪声。

**为什么 PDF 看不出来**（§ 3.5.5 实验 Case B 的直接体现）：
```text
AM 误差 = m(t)·sin(ωt)

如果 ωm 小（AM Noise 的调制是宽带低频）：
   边带接近 fundamental，部分被 fit 吸收（§ 3.5.5）
   -> residual 丢失 envelope 信息
   -> PDF 看起来近 Gaussian（KL ≈ 0.05）

如果 ωm 是固定频率（AM Tone）：
   边带在 (ω±ωm) 是明确的频率点
   -> residual 仍然保留这些边带
   -> 但 PDF 对"频率结构"不敏感，只看幅度分布
   -> sigma 巨大（48 LSB）但 KL 小（0.065）
```

**residual 特征**：

```text
PDF:    近 Gaussian（KL 小）→ 盲点
        AM Tone 的 sigma 巨大但 PDF 形状正常
ACF:    AM Tone 有周期峰（调制频率）；AM Noise 近白噪声
spectrum: AM Tone 在 (ω±ωm) 有明确 spur ← 标志特征
          AM Noise 有低频抬升
by_phase: AM 失真的标志性工具（误差随相位变化）
```

**诊断意义**：AM 是 fit + PDF 的双重盲点。实验 2 里 AM Tone sigma=48.8 LSB（最大）
但 KL=0.065（很小），完美诠释了"sigma 大 ≠ PDF 异常"。诊断 AM 必须用 by_phase 或
spectrum。

#### 4.2 RA Gain Error / RA Dynamic Gain（residue amplifier 增益问题）

**来源**：流水线/pipelined ADC 里 residue amplifier（RA）的增益不准。本库
`apply_ra_gain_error` 模拟静态增益误差，`apply_ra_gain_error_dynamic` 模拟增益随
输入动态变化。

**电路图像**：两-stage pipelined ADC 把信号分成 MSB（粗）和 LSB（细）。RA 把
LSB 子 ADC 的残差放大到 full-scale，供第二 stage 处理。如果 RA 增益 G ≠ 理想值，
第二 stage 的量化结果会被错误缩放，产生"MSB 和 LSB 尺度不匹配"的误差。

**代码建模 RA Gain Error**（`siggen/nonidealities.py` 第 171-181 行）：

```python
msb = np.floor(signal_ac * 2**msb_bits) / 2**msb_bits            # MSB 粗量化
lsb = np.floor((signal_ac - msb) * 2**lsb_bits) / 2**lsb_bits    # LSB 细量化
return msb * relative_gain + lsb + self.DC                        # MSB 增益错误
```

**代码建模 RA Dynamic Gain**（第 183-206 行）：

```python
for n in range(self.N):
    G_dynamic = relative_gain + coeff_3 * (v_residue_out_prev_ac ** 2)   # 增益随历史变化
    v_output_ac[n] = v_msb_code * G_dynamic + v_lsb_code
    v_residue_out_prev_ac = v_output_ac[n]                                # 更新记忆
```

转成数学公式：

```text
静态:
  G_static = relative_gain                                固定增益误差
  y[n] = msb[n]·G_static + lsb[n]
  e[n] = msb[n]·(G_static - 1)                            ← MSB 的线性函数

动态:
  G_dynamic[n] = G_static + coeff_3 · y[n-1]²             增益随上一拍输出² 变化
  y[n] = msb[n]·G_dynamic[n] + lsb[n]
  e[n] = msb[n]·(G_dynamic[n] - 1) = msb[n]·(G_static-1) + coeff_3·msb[n]·y[n-1]²
                                                            ↑ 静态项          ↑ 动态记忆项
```

**关键**：
- 静态：误差是 `msb[n]` 的线性函数 → by_value 上是清晰斜坡
- 动态：误差多了一项 `msb[n]·y[n-1]²` → 既依赖当前 MSB，又依赖历史输出（memory-like）

**为什么 sigma 大但 KL 小**：RA 增益误差和 MSB 信号值成比例，MSB 信号值在样本间
变化大（覆盖多个 code），所以 sigma 大。但瞬时分布在大量样本平均后接近高斯
（中心极限），所以 PDF 看起来正常。

**residual 特征**：

```text
PDF:    轻双峰（RA Gain Error，KL ≈ 0.09）或近 Gaussian（Dynamic，KL ≈ 0.08）
ACF:    有结构（误差和输入信号相关，输入信号是周期的；Dynamic 还有 memory 项）
spectrum: 在 LSB 子 ADC 对应的频率有谐波
by_value: 明显的斜坡或分段结构 ← 标志特征
```

**诊断意义**：RA 增益误差是 by_value 的招牌 case——误差随输入值线性变化，在
by_value 图上是清晰的直线/曲线。PDF 会低估它的严重性。

#### 4.2.5 概念补充：因果性、滤波与 DSP 串讲

在讲 Drift（§ 4.3）之前，需要补一个 DSP 基础概念——**因果性（causality）**。它直接
解释了 Drift 代码里 `filtfilt` 的选择，也是理解本库很多滤波操作的前提。

##### 4.2.5.1 DSP 的全景：信号、系统、滤波

先把 Stage 02/03 用到的 DSP 概念串成一张图，避免它们看起来零散：

```text
DSP 处理对象: 离散信号 x[n], n = 0, 1, ..., N-1

三大分析工具（Stage 02/03 都用过）:
  时域:   看波形 y[n] vs n           -> fit_sine, residual, drift 包络
  频域:   看频谱 X(k) vs f           -> FFT, spectrum, harmonic/spur
  统计域: 看 PDF/ACF                  -> analyze_error_pdf/autocorr

两大操作:
  分析:   从信号提取信息             -> FFT, ACF, fit（不改信号）
  滤波:   改造信号                   -> lfilter, filtfilt, window
          滤波器 = 一个系统 H
          输入 x -> H -> 输出 y

系统的核心性质:
  线性:   H(a·x1 + b·x2) = a·H(x1) + b·H(x2)
          -> 本库所有滤波器都是线性的
  时不变: H(x[n-n0]) = y[n-n0]
          -> 系统参数不随时间变
  因果:   y[n] 只依赖 x[n], x[n-1], ...（不依赖未来）
          -> 本节重点
```

ADC 本身就是一个系统：输入连续电压 x(t)，输出离散 code。Stage 02 的 window、
Stage 03 的 fit 都是"分析"（不改信号）；drift 模型里的低通滤波是"滤波"（改信号）。

##### 4.2.5.2 什么是因果性

**因果系统的定义**：输出 y[n] 只依赖现在和过去的输入 x[n], x[n-1], x[n-2], ...，
**不依赖未来**的输入 x[n+1], x[n+2], ...。

```text
因果:   y[n] = 0.5·x[n] + 0.5·x[n-1]            ✓ 只用现在和过去
非因果: y[n] = 0.5·x[n] + 0.5·x[n+1]            ✗ 用了 x[n+1]（未来）
```

**为什么物理世界必然因果**：时间单向流逝，n 时刻不可能知道 n+1 时刻的输入。所有
真实硬件（ADC、放大器、滤波器电路）都是因果的。

**非因果只在离线处理中可能**：如果整个信号 x[0..N-1] 已经全部采集完（存在内存里），
算法可以"访问未来"——比如 y[n] 用 x[n+1]。这在物理上不存在，但在数据分析中合法。

##### 4.2.5.3 滤波器的相位延迟问题

因果滤波器（`scipy.signal.lfilter`）有一个副作用：**引入相位延迟**，而且不同频率
延迟不同。

```text
对低通滤波器:
  低频成分（接近 DC）:  相位延迟小
  高频成分（接近截止）: 相位延迟大
  -> 不同频率延迟不同 -> "相位失真"

后果:
  输入是多频率叠加（比如正弦 + 谐波）
  -> 各频率被延迟不同时间
  -> 输出的时域波形和输入形状不同（即使幅度谱对了）
  -> 这对"看波形"的应用（比如 drift 包络）不友好
```

**例子**：一个含 fundamental + HD3 的信号，经因果低通后，fundamental 和 HD3 延迟
不同，叠加后的波形会变形——这叫"相位失真"。

##### 4.2.5.4 filtfilt：用"翻转再滤一次"抵消相位

`scipy.signal.filtfilt` 的核心技巧：**做两次滤波，让相位延迟互相抵消**。

```text
步骤 1: 正向滤波（因果 lfilter）
  y1[n] = lfilter(b, a, x)[n]
  -> y1 比 x 多了相位 +φ(f)（每个频率 f 延迟不同）

步骤 2: 时间反转
  y2[n] = y1[N-1-n]    （把 y1 倒过来，"从后往前"）

步骤 3: 反向滤波（对反转序列再做 lfilter）
  y3[n] = lfilter(b, a, y2)[n]
  -> 在反转时间轴上又加了 +φ(f)
  -> 但 y2 是反转的，换算回原始时间轴，这次相当于 -φ(f)

步骤 4: 再反转回来
  drift[n] = y3[N-1-n]

总相位: +φ(f) + (-φ(f)) = 0    ← 零相位！
```

**相位抵消的代价是必然非因果**——反向滤波处理的是时间反转序列，等于用了原始信号
的"未来"。这不是设计目的（目的就是相位抵消），而是这个技巧的必然副作用。

##### 4.2.5.5 最小例子：为什么"翻转再滤"导致非因果

用 3 个样本 `x = [1, 2, 3]`，最简单的因果滤波器 `y[n] = x[n] + x[n-1]`：

```text
正向 lfilter（补 x[-1]=0）:
  y1 = [1, 3, 5]            (y1[0]=1, y1[1]=2+1, y1[2]=3+2)

反转:
  y2 = [5, 3, 1]

反向 lfilter（补 y2[-1]=0）:
  y3 = [5, 8, 4]            (y3[0]=5, y3[1]=3+5, y3[2]=1+3)

再反转:
  drift = [4, 8, 5]
```

追踪 `drift[0] = 4` 依赖原始 `x` 的哪些样本：

```text
drift[0] = y3[2]
         = y2[2] + y2[1]
         = y1[0] + y1[1]
         = x[0] + (x[0] + x[1])
         = 2·x[0] + x[1]
                    ↑
              drift[0]（n=0 时刻的输出）依赖了 x[1]（n=1 时刻的输入）！
              这就是非因果——n=0 的输出"知道"了 n=1 的输入
```

**结论**：filtfilt 的非因果性来自"反转序列"这一步——反转后，原始信号的"未来"
变成了反转序列的"过去"，lfilter 处理反转序列时就用到了这些"未来"样本。

##### 4.2.5.6 lfilter vs filtfilt：什么时候用哪个

```text
                    lfilter (因果)           filtfilt (非因果)
-----------------------------------------------------------------
依赖未来?           否                       是
能实时?             能                       不能（必须等全部数据）
相位延迟?           有（相位失真）           无（零相位）
滤波效果            幅度滤波一次             幅度滤波两次（更陡，等效阶数 ×2）
物理对应            真实系统                 离线后处理
适用场景            实时处理、硬件实现        离线数据分析、信号生成
```

**经验法则**：

```text
实时（边来边处理）:    必须用 lfilter
  - ADC 数字校准（实时输出）
  - 通信均衡器
  - 音频实时效果

离线（数据已采集完）:   可以用 filtfilt，享受零相位
  - 实验数据后处理
  - 信号生成（drift 模型）
  - 频谱分析的预滤波
```

##### 4.2.5.7 回到 drift 代码：filtfilt 的选择是否合理

```python
def apply_drift(self, input_signal=None, drift_scale=5e-5):
    drift_steps = np.random.randn(self.N) * drift_scale
    drift_walk = np.cumsum(drift_steps)                    # 随机游走
    b, a = scipy_signal.butter(2, 0.001)                   # 极低通
    drift = scipy_signal.filtfilt(b, a, drift_walk)        # ← filtfilt
    return signal + drift
```

**用 filtfilt 的动机**：让 drift 信号零相位，和 signal 在时域上干净对齐（drift 的
"特征事件"不滞后于游走）。这对教学和分析直观。

**代价**：drift 是非因果的——drift[n] 依赖了游走的未来。这违反真实 drift 的物理
（真实温度/电源漂移是因果的）。

**对实验结论的影响**：
```text
1. 对 ACF 分析几乎没影响
   filtfilt 和 lfilter 都让 drift 平滑（低频准常数）
   -> ACF 都接近 1.0
   -> "ACF 填满"是 butter 截止低导致的，不是 filtfilt 导致的

2. 对物理保真度影响小
   drift 变化极慢（特征时间 τ ≈ 320 samples）
   非因果的"提前响应"效应几乎看不出来
   -> 对教学够用

3. 严格物理仿真应该改用 lfilter
   但 lfilter 有相位延迟，drift 和游走会错位
   -> 视觉/分析不直观
```

**综合判断**：filtfilt 在这里是一个合理的工程简化——为了时域对齐干净而牺牲了因果性。
对 drift 的 residual 形态（慢变化准常数）和 ACF 行为（≈1）没有实质影响。下一节
（§ 4.3）分析 drift 时会用到这个概念。

#### 4.3 Drift（慢漂移）

**来源**：温度漂移、电源慢变化、1/f noise。本库 `apply_drift(drift_scale)` 模拟。

**电路图像**：ADC 的 DC offset 或 gain 在记录期间缓慢变化——温度漂移让 reference
电压慢慢移动，电源慢波动让 gain 慢慢变。这是**非平稳**过程。

**代码建模**（`siggen/nonidealities.py` 第 272-279 行）：

```python
drift_steps = np.random.randn(self.N) * drift_scale              # 每步随机扰动
drift_walk = np.cumsum(drift_steps)                              # 随机游走（累积）
b, a = scipy_signal.butter(2, 0.001)                             # 低通滤波器
drift = scipy_signal.filtfilt(b, a, drift_walk)                  # 只保留极低频
return signal + drift
```

转成数学公式：

```text
step[n]    = drift_scale · w[n],    w[n] ~ N(0,1)               每步随机扰动
walk[n]    = Σ_{k=0}^{n} step[k]                                随机游走（cumsum）
drift[n]   = LPF(walk[n])                                        低通滤波，只保留极低频

y[n]       = x[n] + drift[n]

e[n]       = drift[n]                                            ← 加性慢漂移
```

**关键**：drift 是**累积随机游走再低通滤波**。随机游走让漂移"有记忆"（当前值依赖
历史所有扰动），低通滤波让漂移只包含极低频成分（变化慢）。

**关于 filtfilt 的非因果性**：代码用 `filtfilt`（零相位）而不是 `lfilter`（因果），
是为了让 drift 在时域上和 signal 干净对齐（不滞后）。代价是 drift 非因果（依赖了
游走的"未来"）。详细原理见 § 4.2.5。对 drift 这种慢变化信号，非因果性的影响
可忽略——ACF≈1 是 butter 截止频率低（变化慢）导致的，不是 filtfilt 导致的。

**为什么是非平稳**：drift 的统计特性随时间变——记录开始时 drift ≈ 0，记录结束时
drift 可能累积到几个 LSB。这违反了 fit 和 PDF 的"平稳"假设（假设整个记录的统计
性质不变）。

**为什么 KL 较大（0.21）**：drift 让不同时段的"局部均值"不同，整体 PDF 是多个
Gaussian（不同时段的）的混合 → 比 Gaussian 宽，KL 偏离。

**residual 特征**：

```text
PDF:    宽峰或轻微双峰（KL ≈ 0.21）
        drift 让不同时段的"局部均值"不同，整体 PDF 被展宽
ACF:    所有 lag 上 R[k] ≈ 1.0（平的水平线）← drift 的标志特征！
        原因: drift 变化极慢（特征时间 ~320 samples）
              在 max_lag=100 范围内 e[n] ≈ e[n+k]（准常数）
              -> ACF[k] = mean(e[n]·e[n+k]) ≈ c² -> 归一化 ≈ 1
        实验 3 实测: ACF[1]=1.000, ACF[10]=1.000, ACF[100]=0.999
        视觉上 "ACF 图被填满"，因为所有值贴在 +1.0 上沿
spectrum: 极低频抬升（drift 的能量在 DC 附近）
时域图:  包络明显变化 ← 最直接
```

**为什么 ACF≈1 是 drift 的指纹**：和其它非理想的 ACF 形态对比——

```text
白噪声:        ACF = δ[k]     （只有 lag=0 是 1，其它是 0）
memory (AR1):  ACF 指数衰减   （lag=0 是 1，快速降到 0）
周期信号:      ACF 周期振荡   （lag=0 是 1，周期性回到 ±1）
drift:         ACF ≈ 1 平的   （所有 lag 都是 1，不衰减）  ← drift 的指纹
```

看到 ACF 在所有 lag 都接近 1，几乎就是 drift（或类似的非平稳过程）。这比 PDF
（KL=0.21，弱信号）和 spectrum（低频抬升，需要看图判断）都更直接。

**"ACF 填满"不是 bug**：ACF 算法对"准常数信号"的正确响应就是全 1。这正好揭示了
drift 违反了"样本独立"的假设——如果 ACF 平到 1，说明信号完全没有独立性，
是强非平稳的标志。

**诊断意义**：drift 的诊断最直接的是**时域 error vs sample 图**（看包络慢变化）
或 **ACF**（看是否全 ≈1）。PDF 的 KL=0.21 能检测到"有结构"，但分不清是 drift 还是
其它；ACF≈1 则是 drift 独有的指纹。


#### 4.4 Glitch（毛刺）

**来源**：数字耦合、电源瞬变、metastability。本库 `apply_glitch(glitch_prob,
glitch_amplitude)` 模拟偶发大幅尖峰。

**电路图像**：数字信号（时钟、控制位）通过寄生电容耦合到模拟通路，或比较器
metastability（接近阈值时延迟决策），偶尔让某个样本产生大幅错误。这是**瞬态事件**
——大部分样本正常，少数样本严重错误。

**代码建模**（`siggen/nonidealities.py` 第 281-286 行）：

```python
glitch_mask = np.random.rand(self.N) < glitch_prob               # 伯努利试验（是否 glitch）
glitch = glitch_mask * glitch_amplitude                          # 触发时加固定幅度
return signal + glitch
```

转成数学公式：

```text
mask[n] ~ Bernoulli(glitch_prob)                                  以 glitch_prob 的概率为 1
g[n]    = mask[n] · glitch_amplitude                              触发时 = amplitude，否则 = 0

y[n]    = x[n] + g[n]

e[n]    = g[n]
       = glitch_amplitude,   with prob = glitch_prob
         0,                   with prob = 1 - glitch_prob
```

**关键**：误差是**混合分布**——99.8% 的样本误差为 0，0.2% 的样本误差为固定幅度
（0.1 = 410 LSB）。这是一个"双点分布"的 PDF（一个在 0，一个在 glitch_amplitude）。

**为什么 PDF 的 KL 极大（1.69）**：0.2% 的异常样本让 PDF 出现极长的尾巴。Gaussian
拟合完全无法描述这个长尾（Gaussian 的 4σ 概率是 0.006%，但 glitch 让 0.2% 的样本
出现在 10σ+ 处）。**KL 对 heavy tail 极其敏感**。

**为什么 ACF 的 R[0] 突出**：glitch 是瞬态（单个样本），能量集中在 lag=0。相邻
样本不相关（glitch 触发是伯努利独立试验），所以 R[k≠0] 接近 0，只有 R[0] 有大值。

**residual 特征**：

```text
PDF:    长尾（KL ≈ 1.69，所有 case 里最大）← 标志特征
ACF:    R[0] 特别突出（瞬态的能量集中在 lag=0）
spectrum: 整个频谱被拉高（瞬态是宽带的，能量散到所有 bin）
时域图:  可见的尖峰 ← 最直接
```

**诊断意义**：glitch 是 PDF 的"招牌 case"——KL 远超其它所有 case。如果测出来
KL > 1，几乎可以确定有 glitch 或类似的瞬态事件。


### 5. 综合诊断流程：从 residual 形态到电路问题

把上面 4 类合起来，Stage 03 的诊断流程是：

```text
第 1 步：看 PDF 的 KL
    KL < 0.01  → 随机噪声主导（类别 1）
                 -> 看 spectrum 区分 thermal/jitter/quant
    KL 0.01-0.1 → 可能有弱结构（memory/AM/RA）
                 -> PDF 是盲点，必须看 ACF / by_value / by_phase
    KL > 0.1   → 明显非高斯
                 -> 看 PDF 形状: 双峰=harmonic, 长尾=glitch, 边缘堆积=clipping

第 2 步：看 ACF
    白噪声 (R[k≠0]≈0) → 确认随机噪声
    小 lag 相关       → memory/settling/reference（类别 3）
    周期峰           → harmonic 或 AM Tone

第 3 步：看 error spectrum
    平坦             → 随机噪声
    fundamental 裙边 → jitter
    整数倍 spur      → harmonic
    非 harmonic spur → AM Tone / 外部干扰
    低频抬升         → drift / memory
    全频段抬升       → glitch（瞬态）

第 4 步：看 by_value / by_phase（fit 盲点的补救）
    by_value 斜坡    → RA gain error / settling
    by_phase 结构    → AM / PM 失真
```

**核心规律**：

```text
没有任何单一工具能诊断所有问题。
PDF 强于: heavy tail (glitch)、边缘堆积 (clipping)、明显 harmonic
ACF  强于: memory effect、settling、短程相关
spectrum 强于: 频率定位 (spur/jitter裙边/AM边带)
by_value/by_phase 强于: AM/PM、幅度相关失真

三件套 + by_value/by_phase = 完整诊断工具链
```

这也是为什么本库 `aout/` 模块同时提供这么多分析函数——它们各有盲点，合起来才能
覆盖所有 ADC 非理想行为。

## 本库对应代码

正弦拟合：

```text
python/src/adctoolbox/fundamentals/fit_sine_4param.py
```

误差分析：

```text
python/src/adctoolbox/aout/analyze_error_pdf.py
python/src/adctoolbox/aout/analyze_error_autocorr.py
python/src/adctoolbox/aout/analyze_error_spectrum.py
python/src/adctoolbox/aout/analyze_error_by_value.py
python/src/adctoolbox/aout/analyze_error_by_phase.py
python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py
```

相关文档：

```text
python/docs/source/algorithms/fit_sine_4param.md
python/docs/source/algorithms/analyze_error_pdf.md
python/docs/source/algorithms/analyze_error_autocorr.md
```

## 对应 API

```python
from adctoolbox import fit_sine_4param
from adctoolbox import analyze_error_pdf
from adctoolbox import analyze_error_autocorr
from adctoolbox import analyze_error_spectrum
from adctoolbox import analyze_error_by_value
from adctoolbox import analyze_error_by_phase
```

## 实验 1：正弦拟合

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a01_fit_sine_4param.py
```

观察：

- fitted sine 是否贴合原始数据。
- residual RMS 是否合理。
- 频率估计是否稳定。

## 实验 2：error PDF

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a21_analyze_error_pdf.py
```

观察：

- `sigma` 是多少 LSB。
- KL divergence 是否接近 0。
- PDF 是否 Gaussian-like。

## 实验 3：error autocorrelation

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a23_analyze_error_autocorrelation.py
```

观察：

- lag=0 以外是否接近 0。
- 是否有周期性峰。

## 实验 4：本地完整 demo

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

看：

```text
E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\02_analog_error_debug.png
```

## 本阶段代码阅读

建议读：

```text
python/src/adctoolbox/fundamentals/fit_sine_4param.py
python/src/adctoolbox/aout/analyze_error_pdf.py
python/src/adctoolbox/aout/analyze_error_autocorr.py
```

阅读重点：

- fitted signal 怎么生成。
- residual 怎么计算。
- error 如何转成 LSB。
- autocorrelation 怎么归一化。

读代码时先追踪这些变量：

```text
data
frequency_estimate
fitted_signal
residuals
rmse
```

你暂时不需要完全理解所有迭代细节。先确认：

```text
fit_sine_4param(data) 不是“滤波”
它是在找一个最能解释 data 的理想正弦
```

## 容易混淆的点

- residual 小，不代表 ADC 完美；它只表示在当前输入和当前模型下剩余误差小。
- residual 有周期结构，通常比 residual RMS 更值得警惕。
- error PDF 像 Gaussian，通常说明随机噪声占主导，但不能单独证明没有 spur。
- sine fitting 频率不准时，residual 会出现假的低频结构或拍频。

## 阶段检查问题

1. 为什么 residual 比原始 waveform 更适合诊断 ADC 问题？
2. PDF 接近 Gaussian 说明什么？
3. ACF 在非零 lag 有明显峰说明什么？
4. error spectrum 和原始 signal spectrum 的区别是什么？
5. 为什么 sine fitting 是很多 ADC 测试算法的前置步骤？

