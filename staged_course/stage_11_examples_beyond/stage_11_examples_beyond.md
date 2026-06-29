# Stage 11：ADCToolbox Examples 全量专题

## 本阶段定位：example atlas，不是零散补遗

Stage 00–10 走完了主线：

```text
numerics -> ADC basics -> FFT metrics -> error analysis -> SAR model
        -> digital bits -> calibration -> validation -> TI-ADC
        -> subsample debug -> oversampling / noise shaping
```

学到这里，知识主线已经完整。Stage 11 的定位要换一下：它不是再开一个新的 ADC
理论主题，而是把本库现存 examples 做成一个**可运行、可解释、可索引**的专题总章。

换句话说，前面 stage 是：

```text
按知识主线学习 ADC toolbox
```

Stage 11 是：

```text
按 examples 反向总览 ADCToolbox
```

根据源库 `python/src/adctoolbox/examples/README.md`，当前 examples 目录下有 **59 个
runnable example**。另外还有少量 helper 文件，例如：

```text
04_debug_analog/nonideality_cases.py
08_time_interleave/variable_delay_line.py
```

它们是支撑脚本，不按 runnable example 计数。

### 为什么需要一个 example 专题

examples 的意义不只是“展示 API 怎么调用”。它们承担了三层教学功能：

1. **验证主线知识**：例如 coherent sampling、windowing、NSD/SNR 换算、SAR weight calibration。
2. **展示诊断工具**：例如 error PDF、phase-plane、polar spectrum、harmonic decomposition。
3. **演示工程 workflow**：例如 dashboard batch、TI foreground/background、debug subsample output。

所以 Stage 11 不再把没跑过的脚本称为“遗留”，而是把它们按知识背景组织起来：

```text
每个 example 回答什么问题；
它依赖前面哪个 stage 的知识；
运行后应该看什么结果；
它是新概念、验证脚本，还是工程 workflow。
```

## 本阶段目标

学完本阶段，你应该能解释：

- 如何按目录完整跑完 59 个 runnable examples。
- 每个 example 属于哪条知识线：基础、频谱、信号生成、analog debug、digital/SAR、dashboard、
  conversions、TI、downsample。
- 哪些 example 是前面 stage 的验证脚本，哪些需要在 Stage 11 单独补背景。
- polar 频谱为什么能同时显示谐波的幅度和相位，笛卡尔频谱为什么不能。
- 相平面 / lag plot 怎么识别 sparkle code、磁滞、亚稳态。
- 谐波分解比纯 FFT 多给出什么（每个 HD 分量的独立幅度+相位）。
- INL/DNL 为什么是静态 transfer curve 指标，和动态 SNDR/SFDR 不等价。
- power averaging、coherent averaging、polar coherent averaging 各自保留/丢失什么信息。

也就是说，本阶段的完成标准不是“背完一个新公式”，而是：

```text
看到任意一个 ADCToolbox example，知道它为什么存在、该怎么跑、输出图该怎么解释。
```

---

## 如何跑完整 example 库

推荐先按目录逐组跑，因为每组对应一个知识主题：

```powershell
cd E:\ADCToolbox\python

uv run python src\adctoolbox\examples\01_basic\exp_b01_environment_check.py
uv run python src\adctoolbox\examples\02_spectrum\exp_s01_analyze_spectrum_simplest.py
uv run python src\adctoolbox\examples\05_debug_digital\exp_d02_cal_weight_sine.py
```

如果要机械地跑完整个 runnable example 库，可以用 PowerShell：

```powershell
cd E:\ADCToolbox\python

$examples = Get-ChildItem src\adctoolbox\examples -Recurse -Filter "exp_*.py" |
  Sort-Object FullName

foreach ($ex in $examples) {
  Write-Host "=== running $($ex.FullName) ==="
  uv run python $ex.FullName
}
```

注意三点：

```text
1. 大多数 example 会把图保存到各自 output/ 目录。
2. dashboard / Monte Carlo / sweep 类脚本可能比单图脚本慢。
3. nonideality_cases.py 和 variable_delay_line.py 是 helper，不按 exp_*.py 直接跑。
```

更适合学习的顺序不是字母序，而是知识顺序：

```text
01_basic
  -> 02_spectrum
  -> 03_generate_signals
  -> 04_debug_analog
  -> 05_debug_digital
  -> 06_use_toolsets
  -> 07_conversions
  -> 08_time_interleave
  -> 09_downsample
```

## 每个实验必须先交代数据建模信息

Stage 11 以后解释 example，先不要急着看图。每个实验都应该先问：

```text
数据来源:
  是真实 ADC capture、完整 ADC 行为模型，还是手工合成 waveform？

理想基线:
  Fs、Fin、N、A、DC、full-scale、bit 数是多少？

非理想性:
  加了 thermal noise、quantization、jitter、static nonlinearity、memory、mismatch、
  glitch、clipping 还是 TI skew？

注入位置:
  非理想性是在 analog waveform 上加的？
  在 quantization 前加的？
  在 SAR CDAC 权重里加的？
  在 digital reconstruction 时故意用错权重？
  还是在多 run 平均前改变相位？

分析步骤:
  是直接 FFT？
  先 fit sine 再看 residual？
  先 decompose harmonic？
  还是先 deinterleave / calibrate / decimate？
```

这不是形式主义。很多 demo 的结论只在它的建模假设下成立。如果不写清楚“数据怎么造出来”，
读者很容易把教学合成数据误读成真实芯片数据，把人为插入的 memory effect 误读成 skew，
或把理想权重/失配权重混用的 SAR demo 误读成完整校准流程。

---

## 全量目录地图：先知道每组 example 在讲什么

| 目录 | runnable 数 | 知识背景 | 运行后主要看什么 |
|---|---:|---|---|
| `01_basic/` | 2 | 环境、自检、相干采样 | 是否装好、coherent/non-coherent 的频谱差异 |
| `02_spectrum/` | 13 | FFT、window、spur、OSR、polar | 频谱指标、泄漏、平均、极坐标相位 |
| `03_generate_signals/` | 6 | 理想/非理想 ADC 信号生成 | bit 数、jitter、非线性、干扰如何改变性能 |
| `04_debug_analog/` | 15 | analog output error diagnosis | error vs value/phase、PDF、ACF、相平面、INL/DNL |
| `05_debug_digital/` | 11 | SAR bit matrix 与权重校准 | weight、radix、overflow、calibration、mismatch MC |
| `06_use_toolsets/` | 4 | dashboard workflow | 单文件/批量 aout/dout 报告 |
| `07_conversions/` | 5 | 单位与指标换算 | aliasing zone、dB/dBFS/dBm、FoM、NSD/SNR |
| `08_time_interleave/` | 2 | TI-ADC mismatch calibration | offset/gain/skew、foreground/background、VDL |
| `09_downsample/` | 1 | debug subsample output | 无滤波抽样 alias、spur 高度和频率解释 |

这一张表是 Stage 11 的主索引。下面五个深挖点，是前面 stage 没完全展开、但 examples
里确实有独立诊断价值的部分。

---

## 缺口 1：polar 频谱（极坐标频谱）

### 这个工具解决什么问题

stage_02 和 stage_03 一直用**笛卡尔频谱**：横轴频率，纵轴幅度(dB)。它能告诉你
"在 H2、H3 频率上有多少能量"，但丢失了一个维度——**相位**。

笛卡尔频谱画的是 `|X(f)|`（幅度），phase 信息被丢掉了。但很多诊断场景里相位是关键：

```text
静态非线性产生的 HD2/HD3 有固定相位（它和输入同步）
记忆效应产生的失真相位会随输入散开（它依赖历史）
```

stage_03 讲记忆效应时，是用 ACF（自相关）的"小 lag 上 R[k] 非零"来识别的。
那是一个**间接**指标。polar 频谱是**直接**指标：把 HD2/HD3 的幅度和相位同时画出来。

### polar 频谱怎么画

`plot_spectrum_polar` 用的是**复数谱**（不只是幅度谱）：

```text
笛卡尔频谱 : 只画 |X(f)|，扔掉 angle(X(f))
polar 频谱 :
   径向（半径） = 谐波幅度 (dB)
   角度（方位） = 谐波相位
```

基波放在角度 0°，HD2、HD3 按它们的相位落在不同方位。于是：

```text
一个纯净的静态 HD3 -> 稳稳地落在某个固定角度（一个点）
有记忆效应的失真  -> 相位散开（不是一个点，是一团云）
```

这样"固定相位 vs 散开相位"的差别就肉眼可辨了——这是笛卡尔频谱做不到的。

### 实验 1：跑 exp_s11_polar_memory_effect

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s11_polar_memory_effect.py
```

数据建模信息：

```text
数据来源:
  手工合成 waveform，不是真实 ADC capture，也不是完整 ADC 仿真。

公共参数:
  Fs = 800 MHz
  N = 2^13 = 8192
  A = 0.49 Vpeak
  DC = 0.5
  base_noise = 50 uVrms

上排 static nonlinearity:
  Fin target = 80 MHz，实际取 coherent frequency，bin = 819 / 8192
  理想基线: sig_ideal = A * sin(2πFin t)
  HD2 target = -80 dBc
  HD3 target = -66 dBc
  k2、k3 由目标 HD2/HD3 反推
  非理想注入: sig + k2*sig^2 或 k3*sig^3
  注入顺序: sine -> static polynomial -> DC -> thermal noise

下排 memory effect:
  Fin targets = 40 / 80 / 160 MHz
  先生成 sine + DC + thermal noise
  再按 4-bit MSB + 18-bit LSB 人工拆分
  非理想注入: signal_me = msb + lsb + 0.02 * previous_msb
  注入位置: 当前输出里混入上一拍 MSB，模拟历史依赖
```

所以这个实验不是在看 skew，也不是在看 TI-ADC。它是在比较：

```text
memoryless static nonlinearity:
  HD2/HD3 相位主要由 k2/k3 符号决定，随 Fin/Fs 不应明显漂移。

memory effect:
  谐波相位会随 Fin/Fs 改变，因为上一拍信息被混入当前输出。
```

#### 上排的静态非线性到底是什么模型

静态非线性产生哪些谐波，取决于输入输出函数里有哪些幂次项。常见行为模型写成：

```text
y = x + k2*x^2 + k3*x^3 + k4*x^4 + ...
```

如果输入是单音：

```text
x = A * sin(ωt)
```

那么这些幂次项会展开成不同谐波：

```text
x^2 -> DC + HD2
x^3 -> fundamental + HD3
x^4 -> DC + HD2 + HD4
x^5 -> fundamental + HD3 + HD5
```

所以可以先粗略记住：

```text
偶次非线性 -> 主要产生偶次谐波，比如 HD2、HD4
奇次非线性 -> 主要产生奇次谐波，比如 HD3、HD5
```

这个模型不是说真实 ADC 的物理机制一定就是多项式，而是把 memoryless、平滑的静态
transfer curve 做低阶行为近似。它特别适合教学：

```text
k2 的正负怎么影响 HD2 相位；
k3 的正负怎么影响 HD3 相位；
幅度频谱看不出的符号/相位信息，polar 图能不能看出来。
```

SAR 的 CDAC 电容失配也会让单音输出出现 harmonic/spur，但机制不同。更准确地说：

```text
k2/k3 polynomial:
  连续、光滑的静态非线性模型。

CDAC mismatch:
  分段的、code-dependent 静态非线性模型。
```

CDAC mismatch 不是简单的 `k2*x^2 + k3*x^3`，它来自 bit weight 偏离理想二进制权重。
spur 位置和强度会受 bit weight error、输入幅度、码覆盖、SAR 决策路径影响。它可以在
频谱上表现为谐波/杂散，但不能把它直接等同于本实验上排的多项式模型。

因此，`exp_s11` 上排不是“三阶正弦输入”。输入仍然是普通单音正弦：

```text
sig_ideal = A * sin(2πFin t)
```

然后 demo 在输出上加入静态多项式非理想：

```python
signal_1 = sig_ideal + k3 * sig_ideal**3 + DC + noise
signal_2 = sig_ideal - k3 * sig_ideal**3 + DC + noise
signal_3 = sig_ideal + k2 * sig_ideal**2 - k3 * sig_ideal**3 + DC + noise
```

所以更准确的描述是：

```text
输入：单音正弦
非理想模型：二阶/三阶静态多项式非线性
结果：输出中出现 HD2 / HD3
```

`k3` 不是“三阶正弦输入”，而是“输出静态非线性里的三次项系数”。

这个实验对照两类失真：

```text
ROW 1 静态非线性：
  HD3=-66dBc, k3>0  -> SNDR=65.70 dB
  HD3=-66dBc, k3<0  -> SNDR=65.61 dB
  HD2+HD3           -> SNDR=65.50 dB

ROW 2 记忆效应（ME=0.02）：
  fin=40MHz  -> sndr=60.13, snr=72.61, thd=-72.47
  fin=80MHz  -> sndr=60.07, snr=72.64, thd=-72.30
  fin=160MHz -> sndr=59.99, snr=72.50, thd=-72.27
```

注意记忆效应那一行的 **SNDR(60) 远低于 SNR(72)**，差了 12 dB——说明有一大块能量
**不在随机噪声里，而在确定性失真里**，但 THD 又只有 -72 dB（谐波解释不了全部）。
这部分"既不是噪声也不是整数谐波"的能量，就是记忆效应的签名。

polar 图上：静态 HD3 是一个清晰的相位点；记忆效应是一片相位散开的云。两种失真
**SNDR 可能差不多，但 polar 图样完全不同**——这正是 polar 的诊断价值。

### 与 stage_03 的衔接

stage_03 §3.1 讲了"记忆效应是什么、为什么 PDF 看不见、ACF 怎么识别"。
本节补的是**第三种可视化手段**：polar 频谱直接看相位散开。三者互补：

```text
PDF     : 看误差分布形状（记忆效应看不出来）
ACF     : 看时间相关性（记忆效应在 lag=1 非零）
polar   : 看谐波相位散开（记忆效应是一团云，静态是点）
```

---

## 缺口 2：相平面 / lag plot

### 这个工具解决什么问题

相平面是另一种和频谱完全不同的视角：不看频域，看**时序结构**。
做法很简单——把信号和它延迟 `k` 个样本的版本画成散点：

```text
x 轴 : x[n]
y 轴 : x[n+k]
```

在单音测试里，它本质上就是一个 **lagged Lissajous 图形**。普通 Lissajous 是：

```text
x = A sin(ωt)
y = B sin(ωt + φ)
```

相平面只是把第二个信号换成同一条记录的延迟版本：

```text
x[n]   = A sin(ωn + φ0)
x[n+k] = A sin(ωn + φ0 + Ω)
Ω      = ωk
```

令：

```text
u = x[n] / A
v = x[n+k] / A
θ = ωn + φ0
```

则：

```text
u = sinθ
v = sin(θ + Ω) = sinθ cosΩ + cosθ sinΩ
```

消去 `θ` 后得到：

```text
u^2 - 2uv cosΩ + v^2 = sin^2Ω
```

这就是一条椭圆。特殊情况下：

```text
Ω ≈ 0°    -> 接近正斜率直线
Ω ≈ 90°   -> 接近圆
Ω ≈ 180°  -> 接近反斜率直线
```

所以 phase-plane 的诊断逻辑可以写成：

```text
理想单音 -> 稳定 Lissajous 椭圆
ADC 非理想 -> 以不同方式破坏这条椭圆
```

频谱把所有时间结构投影成频率能量；相平面保留了局部状态转移：

```text
x[n+k] = F(x[n])
```

是否仍然是单值、平滑、低噪声的关系。这个差别正是它能诊断时序异常的原因。

### auto-lag 怎么选 k

`analyze_phase_plane` 在 `lag='auto'` 时自动选 k，逻辑是（源码 line 43-84）：

```text
1. 去直流，FFT 找主频 -> 得到归一化频率 f_norm
2. 估计周期 = 1/f_norm
3. 搜索 k 使相位偏移 2π·f_norm·k 接近 90°（sin 接近 ±1）
4. 这样散点接近正圆，异常最显眼
```

为什么要 ~90°？因为 k 太小（接近 0°）散点退化成对角线，k 接近 180° 退化成反对角线，
都看不出异常。90°（1/4 周期）让环最"圆"，任何偏离环的点最容易被发现。

实验实测（exp_a41），15 种非理想性 auto-lag 都选了 k=2（因为这个实验的 fin 让
1/4 周期正好约等于 2 个样本）。

### 异常怎样破坏 Lissajous 椭圆

理想 sine 是一条薄椭圆。白噪声只是让椭圆均匀变厚：

```text
x[n]   = s[n]   + e[n]
x[n+k] = s[n+k] + e[n+k]
```

如果 `e[n]` 是小的白噪声，散点围绕椭圆均匀扩散，没有明显方向结构。

不同异常的数学结构不同，所以破坏方式也不同。

**1. sparkle / glitch：稀疏脉冲误差**

可以写成：

```text
x[n] = s[n] + g[n]

g[n] = large error,  only for rare n
g[n] = 0,            most of the time
```

相平面点变成：

```text
(x[n], x[n+k]) = (s[n] + g[n], s[n+k] + g[n+k])
```

大多数点仍在椭圆附近；只要 `g[n]` 或 `g[n+k]` 非零，点就会横向或纵向跳离主环。
所以 glitch/sparkle 是少量孤立离群点。在频域里，稀疏脉冲会扩散成宽带能量，
很容易只被看成噪声底抬高。

**2. hysteresis：同一输入值有两条历史路径**

hysteresis 的核心不是：

```text
x_out = f(x_in)
```

而是：

```text
x_out = f(x_in, state)
```

最简单可以写成：

```text
x_out[n] = f_up(x_in[n])    if dx/dt > 0
x_out[n] = f_down(x_in[n])  if dx/dt < 0
```

同一个 `x_in`，上升沿和下降沿输出不同。因此在 lagged Lissajous 图上，同一个
`x[n]` 附近可能对应两条不同的 `x[n+k]` 路径：

```text
上升路径: (x[n], x[n+k]) follows one curve
下降路径: (x[n], x[n+k]) follows another curve
```

于是会出现双轨、回环或 8 字形。频谱可能只把它显示成 HD2/HD3 能量，无法告诉你
“同一输入值有两条历史路径”。

**3. settling / memory：隐藏状态参与**

memory/settling 可以写成带历史项的模型：

```text
x[n] = f(s[n], s[n-1], s[n-2], ...)
```

一阶近似可以是：

```text
x[n] = s[n] + α * s[n-1]
```

或者误差状态模型：

```text
e[n] = β * e[n-1] + η[n]
```

这时 `x[n+k]` 不再只由当前相位决定，还受隐藏状态影响。相平面不再是一条薄椭圆，
而会变厚、拖尾、扭曲，甚至出现条纹或多轨。频谱可能只看到 harmonic/spur 或噪声底变化，
但相平面会暴露“误差有状态记忆”。

**4. metastability：阈值附近条件性错误**

metastability 可以抽象成：

```text
if s[n] near threshold:
    decision delay / wrong decision probability rises
```

也就是：

```text
P(error | s[n]) 在阈值附近变大
```

因此异常点不会均匀分布在整条椭圆上，而会集中在某些轨迹位置，表现为局部点云变厚、
局部断裂、阈值附近聚集或局部离群。频谱会把这些条件性错误平均到全频域里，
常常只表现为噪声底或杂散。

**5. AM / gain modulation：椭圆半径变化**

如果信号幅度被慢变化调制：

```text
x[n] = A[n] * sin(ωn)
```

那么 Lissajous 椭圆的半径会随时间变化，图上会出现多层环或厚环。`exp_a41`
里的 AM Tone 就是这种图样：不是少数点飞出去，而是整条轨迹半径在变。

**6. jitter / phase modulation：相位关系抖动**

如果采样时刻抖动：

```text
x[n] = A sin(ω(nTs + δt[n]))
```

那么相当于局部相位有扰动。相平面里，点会沿轨迹切向扩散；频率越高，同样的
`δt[n]` 造成的幅度误差越大。

总结成一张表：

| 异常类型 | Lissajous 图样 | 频谱里的表现 |
|---|---|---|
| white noise | 椭圆均匀变厚 | 噪声底 |
| sparkle / glitch | 少量点远离椭圆 | 宽带噪声/杂散 |
| hysteresis | 双轨、回环、8 字形 | HD，但看不出路径依赖 |
| settling / memory | 拖尾、条纹、扭曲、多轨 | harmonic/spur/噪声底 |
| metastability | 阈值附近局部变厚或断裂 | 噪声底或局部 spur |
| AM / gain modulation | 多层环、厚环 | 调制边带 |
| jitter / phase modulation | 沿轨迹切向扩散 | jitter noise，随 Fin 恶化 |

### outlier 检测为什么用 MAD 不用 std

源码 line 110-117 的细节值得注意：outlier 检测用 **MAD（中位数绝对偏差）**而不是 std：

```python
r_median = np.median(radius)
mad = np.median(np.abs(radius - r_median))
r_sigma_robust = mad * 1.4826
outlier_mask = np.abs(radius - r_median) > threshold * r_sigma_robust
```

这里的 `radius` 可以理解为每个点离 Lissajous 主环中心的半径。检测逻辑是：

```text
正常点:
  radius 接近主环半径

glitch / sparkle:
  radius 远离主环半径
```

如果用标准差：

```text
std = sqrt(mean((r - mean(r))^2))
```

极端点会被平方项强烈放大。少数 sparkle 点会把 `std` 撑大，阈值也随之变大：

```text
threshold * std 变大
```

结果是 outlier 自己把尺子拉长，反而让自己“不够异常”。

MAD 是中位数型统计：

```text
median = median(r)
MAD    = median(abs(r - median))
```

只要 outlier 数量不是多数，中位数几乎不被它们拉偏。源码里的：

```text
r_sigma_robust = MAD * 1.4826
```

是把正态分布下的 MAD 换算到和标准差同量纲，因为对高斯噪声：

```text
std ≈ 1.4826 * MAD
```

所以这个 outlier detector 的含义是：

```text
先用中位数估计主环半径；
再用 MAD 估计正常环厚度；
离主环超过若干个 robust sigma 的点，标成 outlier。
```

这也解释了 `exp_a41` 的结果：HD2/HD3、drift、memory 多数是连续变形，不一定产生
离群点；Glitch 是稀疏跳点，所以被红叉抓出来。

### 实验 2：跑 exp_a41 + exp_a42

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a41_analyze_phase_plane.py
uv run python src\adctoolbox\examples\04_debug_analog\exp_a42_analyze_error_phase_plane.py
```

数据建模信息：

```text
数据来源:
  ADC_Signal_Generator 合成的 analog-output waveform。
  不是真实 ADC capture。

公共参数来自 nonideality_cases.get_batch_test_setup():
  Fs = 800 MHz
  Fin target = 97 MHz，实际取 coherent frequency
  N = 2^16 = 65536
  A = 0.49 Vpeak
  DC = 0.5
  resolution label = 12 bit
  adc_range = [0, 1]

15 类 case:
  Thermal Noise:
    直接加 180 uVrms thermal noise。

  其余 case:
    先在理想 sine 上注入某类非理想；
    最后再统一加 10 uVrms thermal noise。

非理想类型:
  quantization:          10-bit quantization
  jitter:                jitter_rms = 2 ps
  AM noise:              strength = 0.0005
  static HD2:            target = -80 dBc
  static HD3:            target = -70 dBc
  memory effect:         memory_strength = 0.009
  incomplete settling:   T_track = 0.2/Fs, coeff_k = 0.09
  RA gain error:         msb_bits=4, lsb_bits=8, relative_gain=0.99
  RA dynamic gain:       coeff_3 = 0.15
  AM tone:               500 kHz, depth=0.05
  clipping:              percentile_clip = 1%
  drift:                 drift_scale = 5e-5
  reference error:       settling_tau=0.1, droop_strength=0.002
  glitch:                prob=0.002, amplitude=0.1

分析差异:
  exp_a41: 直接画 raw signal 的 x[n] vs x[n+k]
  exp_a42: 先 fit sine 去掉基波，再画 residual/error phase-plane
```

这些面板里的 "noise" 不是同一种东西，含义要分开：

```text
Thermal Noise:
  加性白噪声。模型是 x[n] = s[n] + e[n]。
  phase-plane 上表现为理想 Lissajous 椭圆均匀变厚。

Quantization Noise:
  把连续电压量化到有限 code，再重构为电压。
  phase-plane 上常见细密的格点/带状纹理，因为输出只能落在有限 code 上。

Jitter Noise:
  采样时刻扰动。模型近似是 x[n] = s(t_n + δt[n])。
  它主要沿轨迹切向扩散，高 Fin 时更明显。

AM Noise:
  随机幅度调制。模型是 x[n] = (1 + m[n]) * s_ac[n] + DC。
  它主要改变 Lissajous 椭圆半径，所以表现为径向变厚或多层环。

AM Tone:
  确定性的慢幅度调制。模型是 x[n] = (1 + d*sin(ωm n)) * s_ac[n] + DC。
  因为包络在高/低幅度之间周期变化，phase-plane 会出现更清楚的多圈/双圈结构。

Glitch:
  稀疏脉冲误差。模型是 x[n] = s[n] + g[n]，其中 g[n] 大多数为 0，
  少数样本为 +0.1。phase-plane 上表现为远离主椭圆的红色离群点。
```

#### 为什么 AM noise / AM tone 会像双圈或厚环

理想单音的 lagged Lissajous 可以写成：

```text
x[n]   = A sinθ
x[n+k] = A sin(θ + Ω)
```

这是一条固定半径的椭圆。如果存在幅度调制：

```text
x[n] = A[n] sinθ
```

那么半径不再固定。对 phase-plane 来说，每一个瞬时幅度 `A[n]` 都对应一条不同大小的
Lissajous 椭圆：

```text
A[n] 小 -> 小椭圆
A[n] 大 -> 大椭圆
```

如果 `A[n]` 是随机的，就会把主环沿径向抹厚；如果 `A[n]` 是一个慢速 tone，采样点会在
几个相对稳定的幅度包络上停留更久，于是图上更容易看成双圈、多层环或厚环。

所以要区分：

```text
AM Noise 面板:
  随机包络，主要是环变厚。

AM Tone 面板:
  确定性包络，双圈/多圈更明显。
```

这不是新的频率轴信息，而是幅度包络在 Lissajous 空间里的几何投影。

#### Glitch 红点是否符合理论

符合。`apply_glitch` 的模型是：

```python
glitch_mask = np.random.rand(N) < glitch_prob
glitch = glitch_mask * glitch_amplitude
signal_glitch = signal + glitch
```

本实验里：

```text
glitch_prob = 0.002
glitch_amplitude = 0.1
lag k = 2
```

phase-plane 点是：

```text
(x[n], x[n+k])
```

如果 `n` 这一点 glitch：

```text
(s[n] + 0.1, s[n+k])
```

点会主要向 x 方向跳离主椭圆。

如果 `n+k` 这一点 glitch：

```text
(s[n], s[n+k] + 0.1)
```

点会主要向 y 方向跳离主椭圆。

如果两个点同时 glitch：

```text
(s[n] + 0.1, s[n+k] + 0.1)
```

点会沿对角方向跳离，但概率约为 `p^2`，很少。

源码的 outlier detector 不是直接读取 `glitch_mask`，而是看相平面半径是否远离主环：

```text
radius = sqrt((x - mean(x))^2 + (y - mean(y))^2)
outlier = |radius - median(radius)| > threshold * robust_sigma
```

因此红点数量不一定等于真实 glitch 样本数。理论上，一个 glitch 样本可能影响两个
phase-plane 点：一次作为 `x[n]`，一次作为 `x[n+k]`。但如果某些 glitch 发生在主环内侧、
径向偏移不够大，或者两个事件重叠，MAD 阈值可能不会全部标红。`exp_a41` 检出 174 个
红点，和“稀疏 +0.1 脉冲会产生离群点”的理论是一致的。

所以 a41/a42 的目的不是判断某一个单独参数，也不是 skew 专项实验。skew 是 Stage 08
的 TI-ADC 失配问题；这里的 phase-plane 主要用于看 sparkle、hysteresis、memory、
settling、clipping、glitch、静态/动态非线性。

**exp_a41**（15 种非理想的相平面）：实测结果很有说服力——

```text
14 种非理想性的 outlier 数都是 0
只有 Glitch 检出 199 个 outlier
```

也就是说相平面对 sparkle/glitch 类异常极其敏感（专抓时序离群），对连续失真
（HD、drift）反而不敏感（它们不产生离群点，只是让环变形）。

**exp_a42**（误差相平面，a42 的特殊价值）：它先 `fit_sine_4param` 去掉基波，
对**残差**做相平面。源码自己总结了：

```text
* HD2/HD3 cases show characteristic parabola/S-curve shapes even at -80/-70 dBc
* This method is 1000x more sensitive than regular phase planes for detecting harmonics
```

去基波后，-80 dBc 的 HD2（信号幅度的万分之一）在残差里变成了主要成分，
相平面能直接看到它的抛物线形状。**放大 1000 倍**就是从这里来的：
原本被基波淹没的微小 HD，去基波后凸显。

#### 深入读第二幅图：exp_a42 的 residual phase plane

这张图容易和 `exp_a41` 混淆，但二者不是同一个对象：

```text
exp_a41:
  x-axis = x[n]
  y-axis = x[n+k]
  看 raw signal 的 lagged Lissajous 轨迹。

exp_a42:
  x-axis = data[n]
  y-axis = data[n] - fitted_sine[n]
  看去掉最佳正弦后的 residual/error 是否随输入电平形成结构。
```

也就是说，`exp_a42` 的纵轴不是延迟样本，而是**残差**。它的完整数据链路是：

```text
1. nonideality_cases.py 生成 clean sine:
     data_clean[n] = 0.49 * sin(2π Fin n/Fs) + 0.5

2. 对每个 panel 注入一种非理想:
     thermal / quantization / jitter / AM / HD2 / HD3 / memory / settling / ...

3. 大多数 case 最后再加 10 uVrms thermal noise。

4. analyze_error_phase_plane(data) 拟合最佳正弦:
     data_fit[n] = a*cos(ωn) + b*sin(ωn) + c

5. 计算残差:
     residual[n] = data[n] - data_fit[n]

6. 作图:
     x = data[n]
     y = residual[n] * 1e6
```

所以图中灰色散点的数学含义是：

```text
(当前 ADC 输入电平, 相对于最佳正弦的误差)
```

这里的横轴标成 `Signal Amplitude (V)` 有歧义。按本 demo 的作者意图，它更准确应理解为：

```text
Signal sample value / ADC input level
```

因为基础信号是：

```text
A = 0.49
DC = 0.5
adc_range = [0, 1]
```

也就是归一化的单端 full-scale 模型：

```text
ADC 输入范围      : 0 ~ 1
common-mode / DC : 0.5
AC peak amplitude: 0.49
```

如果把 `1 full-scale` 解释成 `1 V`，纵轴显示成 `uV` 是可以自洽的；如果只是归一化仿真，
那更严谨的单位应写成 `uFS` 或 `ppm FS`。

##### 为什么去掉最佳正弦后更敏感

原始数据里，主正弦幅度约为：

```text
0.49 full-scale
```

而 -80 dBc 的 HD2 振幅只有主信号的：

```text
10^(-80/20) = 1e-4
```

直接画 raw signal 时，这个误差被大正弦轨迹淹没。`exp_a42` 先把最佳正弦拟合掉：

```text
data[n] = ideal_sine[n] + error[n]
residual[n] = data[n] - fitted_sine[n]
```

如果拟合足够好，基波、整体 DC、整体 gain、整体 phase 都被吸收，剩下的主要就是：

```text
非线性误差；
动态误差；
码相关误差；
随机噪声；
无法被一个纯正弦解释的部分。
```

这就是它比 raw phase-plane 更容易看见 HD2/HD3 的原因。它不是魔法放大器，而是把
`0.49` 量级的基波从图里拿掉，让 `uV` 级残差成为主角。

##### HD2 / HD3 为什么分别像 U 形和 S 形

设去 DC 后的理想输入为：

```text
x = A sinθ
```

二阶静态非线性可以写成：

```text
y = x + k2*x^2
```

当把最佳正弦部分去掉后，剩下的误差主要随 `x^2` 变化。`x^2` 是偶函数：

```text
x 和 -x 给出相同方向的误差
```

所以 residual-vs-value 图上表现为抛物线 / U 形。这就是 `Static HD2 (-80 dBc)` 面板的主图样。

三阶静态非线性可以写成：

```text
y = x + k3*x^3
```

`x^3` 是奇函数，正半周和负半周误差方向相反，因此 residual-vs-value 图上表现为 S 形。
注意，`x^3` 里有一部分会投影到 fundamental 上，被 `fit_sine_4param` 吸走；图上看到的是
**去掉最佳基波后的三阶残差形状**，不是裸的 `k3*x^3`。

##### 紫线、绿线和右上角统计框

`analyze_error_phase_plane.py` 不只画灰色 residual 点，还会尝试判断上升沿和下降沿是否不同：

```python
gradient = np.gradient(data)
mask_rise = gradient > 0
mask_fall = gradient < 0

coeff_rise = np.polyfit(data[valid_rise], residual[valid_rise], 3)
coeff_fall = np.polyfit(data[valid_fall], residual[valid_fall], 3)
```

然后画两条三阶趋势线：

```text
green / 绿线:
  Rising (Memory)，输入处在上升沿时的 residual trend。

magenta / 紫线:
  Falling (Memory)，输入处在下降沿时的 residual trend。
```

这两条线回答的问题是：

```text
同一个输入电平 x，误差是否只由 x 决定？
还是还取决于它是从低处升上来，还是从高处降下来？
```

如果误差是纯静态非线性：

```text
error[n] = f(x[n])
```

那么同一个 `x` 必须对应同一个 `error`，上升沿和下降沿趋势线应该重合。典型例子是
`Static HD2` / `Static HD3`：曲线形状明显，但绿线和紫线基本是一条线。

如果误差有 memory / settling / hysteresis：

```text
error[n] = f(x[n], state[n])
```

那么同一个 `x` 可能因为历史状态不同而给出不同误差。一个简单 settling 模型是：

```text
y[n] = x[n] + α * (x[n-1] - x[n])
```

因为：

```text
x[n-1] - x[n] ≈ -Ts * dx/dt
```

所以：

```text
error[n] ≈ -α Ts * dx/dt
```

上升沿 `dx/dt > 0` 和下降沿 `dx/dt < 0` 的误差符号会不同。于是同一个输入电平附近，
residual 会分成两条路径。这正是绿线和紫线分开的物理含义。

右上角的小框不是 legend，而是统计量：

```text
RMS:
  residual 的标准差，表示整体误差能量。

Peak:
  residual 的最大绝对值，容易被 clipping / glitch / drift 拉大。

Hyst:
  绿线和紫线之间的平均距离：
    mean(abs(trend_rise - trend_fall))
```

所以 `Hyst` 越大，说明上升/下降路径差异越明显。它不是严格证明“来源一定是 memory”，
而是证明：

```text
误差不是当前输入值的单值函数。
```

memory、settling、hysteresis、reference recovery、动态 gain、低频调制都可能造成这种现象。
因此它是很强的诊断线索，但不是最终归因证明。

还有一个作图细节：源码给趋势线设置了 label：

```python
label='Rising (Memory)'
label='Falling (Memory)'
```

但没有调用 `ax.legend()`，所以图上不会显示真正的 legend。并且紫线后画，如果两条线重合，
紫线会盖住绿线；这时看起来像“只有紫线”，并不代表没有上升沿趋势。

##### 逐类看第二幅图的图样

```text
Thermal Noise:
  residual 围绕 0 水平散开，没有明确随输入值变化的曲线。

Quantization Noise:
  residual 仍围绕 0，但可能出现更均匀的带状/格点纹理。

Jitter Noise:
  误差近似和斜率有关：error ≈ dx/dt * δt。
  因此过零附近更容易变厚，峰顶/谷底相对较小。

AM Noise:
  乘性幅度噪声：x_out = (1 + m[n]) * x_ac[n] + DC。
  residual 大小随 |x_ac| 增大，两端更厚，中间更窄。

Static HD2:
  U 形 / 抛物线，典型二阶静态非线性。

Static HD3:
  S 形，典型三阶静态非线性。

Memory Effect / Incomplete Settling:
  同一输入值可能对应不同历史状态，容易出现双轨、分叉或绿紫趋势线分离。

RA Gain Error:
  residue-amplifier / stage gain 相关误差，可能出现码段纹理或锯齿状结构。

RA Dynamic Gain:
  gain 随内部状态变化，既有强曲率，也有明显上升/下降路径差异。

AM Tone:
  确定性幅度调制，残差结构很大且规则，常呈扇形或交叉纹理。

Clipping:
  两端突然折断，peak 可能明显但 RMS 未必最大。

Drift:
  慢变化 offset 不能被单个固定正弦完全解释，残差会出现大范围竖向漂移。

Reference Error:
  Vref droop / recovery 会把幅度相关和历史相关混在一起，常表现为弯曲趋势。

Glitch:
  少数样本突然跳变，peak 极大；在 residual-vs-value 图里可能被压缩到少数极端点。
```

这张图的正确读法是：

```text
先看灰点形状判断 residual 是否有结构；
再看绿/紫趋势线是否分开判断是否存在历史依赖；
最后用 RMS / Peak / Hyst 量化误差大小、极端点和上升/下降路径差异。
```

##### Reference Error 为什么像奇函数

修复后的 reference error 模型应按 AC component 作用：

```text
x[n] = signal[n] - DC

kick[n]  = k * |x[n]|
droop[n] = IIR(kick[n])
output[n] = DC + x[n] * (1 - droop[n])
```

本实验参数是：

```text
settling_tau = 0.1
droop_strength = 0.002
```

因为：

```text
decay = exp(-1 / settling_tau) = exp(-10) ≈ 4.5e-5
```

所以 reference recovery 非常快，IIR 的历史记忆很弱。可以先近似成：

```text
droop[n] ≈ k * |x[n]|
```

于是输出误差近似为：

```text
error[n]
  = output[n] - ideal[n]
  ≈ -x[n] * droop[n]
  ≈ -k * x[n] * |x[n]|
```

这里：

```text
|x|      是偶函数
x       是奇函数
x * |x| 是奇函数
```

所以修复后的 Reference Error 面板自然会围绕 midscale 呈现 odd / S-like 的残差结构。
它不是 HD2 那种 U 形，因为虽然 reference stress 用了 `|x|`，但最后 droop 是乘到
`x` 上的：

```text
reference droop -> dynamic gain error
error            -> signal_ac * droop
```

`fit_sine_4param` 还会把最像 fundamental 的那部分吸收掉，所以图上看到的也不是裸的
`-k*x|x|`，而是去掉最佳正弦后的残差。结果常表现为：

```text
低端边缘偏正；
低中段偏负；
高中段偏正；
高端边缘偏负。
```

这就是它看起来像一种 odd high-order residual 的原因。

如果 reference load 对正负半周不对称，或者模型直接加入 `x^2` 型误差，那么图形才会更像
偶函数 / U 形。本 demo 的 reference error 不是那种模型。

还要注意旧实现和修复实现的差别。旧实现等效为：

```text
output_old = (DC + x) * (1 - droop) + DC
```

这会额外引入：

```text
-DC * droop ≈ -k * DC * |x|
```

并且把横轴整体抬到 `0.5 ~ 1.5` 附近。main 中修复后应是：

```text
output_fixed = DC + x * (1 - droop)
```

此时横轴回到 `0 ~ 1`，Reference Error 的 RMS/Peak 也会明显下降。重跑 `exp_a42` 后，
Reference Error 的典型结果是：

```text
RMS  ≈ 59 uV
Peak ≈ 124 uV
Hyst ≈ 0.1 uV
```

`Hyst` 很小正好说明：这组 `settling_tau=0.1` 参数下，reference recovery 的记忆性很弱；
图形主要来自幅度相关的乘性误差，而不是强 hysteresis。

##### Drift 为什么不像包络，而像发散网格

Drift 面板的模型不是幅度调制，而是慢变 additive offset：

```text
drift_steps = random
drift_walk  = cumsum(drift_steps)
drift       = low-pass(drift_walk)

output[n] = sine[n] + drift[n]
```

要和 AM 区分开：

```text
AM:
  output[n] = (1 + m[n]) * sine_ac[n] + DC
  误差随 |sine_ac| 变大，像包络/扇形/双圈。

Drift:
  output[n] = sine[n] + d[n]
  误差主要是慢变化 baseline，不随当前幅度成比例缩放。
```

`fit_sine_4param` 只能拟合一个固定的：

```text
a*cos(ωn) + b*sin(ωn) + c
```

其中 `c` 是固定 DC。它无法拟合：

```text
c[n] = slowly varying DC
```

所以 drift 会留在 residual 里：

```text
residual[n] ≈ drift[n] - best_constant_DC
```

为什么在 residual-vs-value 图里看起来像“发散”或交叉网格？因为这张图把时间轴折叠掉了：

```text
x-axis = data[n]
y-axis = residual[n]
```

同一个输入电平会在很多个时间点被扫到，但每次扫到时 drift 状态可能不同：

```text
same signal value, different time -> different drift offset
```

因此 residual 不是 `f(x)` 这种单值函数，而是很多条慢变时间轨迹叠在同一张
`residual vs signal value` 图上。时间信息被折叠后，就会出现密集交叉、多轨、像发散的结构。

如果改看：

```text
residual vs time
```

drift 会更像直观的慢变 baseline；如果看：

```text
residual vs phase
```

每个相位点会被慢漂上下拖动。只有在 `residual vs signal value` 这种图里，它才会变成
交叉网格。换句话说：

```text
Drift 不像包络，不是因为模型奇怪；
而是因为它是加性慢漂，且这张图丢掉了时间轴。
```

---

## 缺口 3：谐波分解（harmonic decomposition）

### 这个工具解决什么问题

stage_03 讲了 HD2/HD3 的成因（k2 → HD2，k3 → HD3），stage_02 的频谱能测出
HD2、HD3 各自的 dBc。但频谱给的是**功率**，丢掉了相位。

如果你想回答这些问题，频谱不够：

```text
这个 HD2 到底是偶次非线性还是别的？
HD2 和 HD3 的相对相位是什么？（决定它们在时域叠加后是相长还是相消）
能不能把 HD2 分量单独从波形里抽出来，看它单独长什么样？
```

谐波分解就是干这个的：用最小二乘把每个谐波分量**独立地**解出来，给出幅度**和**相位。

### 数学：最小二乘谐波分解

`decompose_harmonic_error` 的算法（源码 line 59-67）：

```text
1. fit_sine_4param 定基频 ω（和 stage_03 用的同一个拟合）
2. 构造谐波 basis：
     A = [1, cos(ωt), sin(ωt), cos(2ωt), sin(2ωt), ..., cos(nωt), sin(nωt)]
3. 最小二乘：W = (A^T A)^(-1) A^T · signal
4. 每个谐波 h 的幅度 = sqrt(W[cos_h]^2 + W[sin_h]^2)，相位 = atan2(...)
5. 相位都相对基波旋转（line 71）：
     phase_h_relative = phase_h - h * phase_fundamental
```

第 5 步"相对基波"是关键约定：这样不同测量的相位才有可比性。
（基波相位本身依赖时间零点，没意义；减掉 h 倍基波相位后，剩的是失真本身的特征相位。）

输出比频谱多两个维度：

```text
频谱   : 每个 HD 的功率（dBc）
分解   : 每个 HD 的幅度 + 相位 + 独立的时域波形（fundamental_signal / harmonic_signal / noise_residual）
```

特别地，`harmonic_signal` 是把基波去掉、只留所有谐波的波形——可以直接看"失真单独长什么样"。

### 实验 3：跑 exp_a11 + exp_a12

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a11_decompose_harmonics.py
uv run python src\adctoolbox\examples\04_debug_analog\exp_a12_decompose_harmonics_polar.py
```

数据建模信息：

```text
数据来源:
  手工合成 analog waveform，不是真实 ADC capture。

exp_a11:
  Fs = 800 MHz
  N = 2^13 = 8192
  Fin = 10.1234567 MHz
  A = 0.25 Vpeak
  DC = 0.5
  base_noise = 50 uVrms

exp_a12:
  Fs = 800 MHz
  N = 2^13 = 8192
  Fin target = 100 MHz，实际取 coherent frequency
  A = 0.5 Vpeak
  DC = 0.5
  base_noise = 50 uVrms
  adc_range = [0, 1]

三类 waveform:
  thermal noise only:
    sig = sine + DC + thermal noise

  static nonlinearity:
    sig = DC + sine_ac + k2*sine_ac^2 + k3*sine_ac^3 + thermal noise
    k2 = 0.001
    k3 = 0.005
    非线性只作用在 AC component 上，DC 后加回

  glitches:
    glitch_prob = 1%
    glitch_amplitude = 0.1
    sig = sine + DC + random glitch + thermal noise

分析步骤:
  exp_a11: harmonic decomposition 的时域视图
  exp_a12: 先画 spectrum，再画 polar decomposition
```

- **exp_a11**：把信号分解成 fundamental / harmonics / residual 三层，逐层画时域波形。
  能直接看到 HD3 的三次曲线形状、residual 的噪声形状。
- **exp_a12**：把分解结果画成 polar（和缺口 1 联动），用 fs=800MHz / Fin=100MHz 的
  相干采样，把每个谐波的幅度+相位标在极坐标上。

（注：这两个 example 的 fit_sine_4param 在 max_iterations=1 下会有一个收敛警告，
属于 example 脚本的有意设置——它故意只迭代一次拿频率估计，后续靠 LMS 精修。
不影响分解结果。）

#### 这两幅图到底在分什么

这两个 example 的核心不是“凭图直接判断物理来源”，而是做一个数学投影：

```text
signal ≈ DC + H1 + H2 + H3 + H4 + H5

harmonic_signal = H2 + H3 + H4 + H5
noise_residual  = signal - (DC + H1 + H2 + H3 + H4 + H5)
```

所以它区分的是：

```text
coherent harmonic component:
  能被固定频率、固定相位的整数倍谐波 basis 解释。

residual / other errors:
  不能被这些低阶 harmonic basis 解释。
```

这不是自动物理归因。更严谨的说法是：

```text
它能判断误差是否“像稳定的 H2/H3/H4/H5”；
不能单凭这一张图证明误差一定来自某个电路模块。
```

例如：

```text
静态 k2/k3 非线性:
  单音输入下会稳定产生 HD2/HD3，所以会被分到 harmonics。

thermal noise:
  和 harmonic basis 不相干，主要留在 residual。

glitch:
  稀疏脉冲在频域是宽带扩散，不是少数固定谐波，所以主要留在 residual。

外部 spur 恰好落在 3fin:
  即使不是 ADC 静态非线性，也会被这个算法投影成 HD3。
```

所以读图时要把“数学分解”和“物理归因”分开。

#### exp_a11：时域图怎么读

`exp_a11_decompose_harmonics.png` 每列对应一类数据：

```text
左列 : Thermal Noise Only
中列 : Nonlinearity (k2=0.001, k3=0.005)
右列 : Glitches (prob=1%, amp=0.1)
```

上排是：

```text
蓝色 x:
  原始 signal。

灰线:
  拟合出来的 fundamental sine。
```

下排是：

```text
红线:
  harmonic_signal，也就是 H2~H5 重构出来的谐波误差。

蓝线:
  noise_residual / other errors，也就是去掉 H1~H5 后剩下的部分。
```

三列图的含义是：

```text
Thermal Noise:
  红线接近 0，说明没有稳定低阶谐波；
  蓝线随机跳动，说明误差主要是随机噪声。

Static Nonlinearity:
  红线变成平滑周期波，说明 k2/k3 产生了稳定谐波；
  蓝线仍是小随机噪声，说明去掉谐波后剩余主要是 thermal noise。

Glitches:
  蓝线出现巨大尖峰，说明少数样本的 impulsive error 不能被 H2~H5 解释；
  红线较小，不代表 glitch 没有频谱能量，而是说明它不是少数低阶相干谐波。
```

还有一个容易误读的细节：`plot_decomposition_time` 会围绕最大误差位置截取显示窗口。
因此三列的 sample 范围不一样。glitch 列看起来特别突兀，是因为窗口自动选到了有大尖峰的地方。

#### exp_a12：频谱 + polar 图怎么读

`exp_a12_decompose_harmonics_polar.png` 上排是普通频谱，下排是 polar harmonic decomposition。

上排读法：

```text
Thermal Noise:
  噪底低，SFDR/SNDR 高。

Static Nonlinearity:
  H2/H3 spur 清楚，SFDR/SNDR 被确定性谐波拉低。

Glitches:
  噪底/宽带误差大幅抬高，SNDR 很差；
  不应过度解读某一个 harmonic marker。
```

下排 polar 图读法：

```text
蓝色实心圆:
  fundamental，按约定放在 0°。

蓝色空心方块:
  H2~H5 的相量。

半径:
  幅度 dB。

角度:
  相对 fundamental 的相位。

黑色虚线圆:
  residual / other errors 的 RMS 参考圈。
```

黑色虚线圆不是一个“有相位的噪声相量”，它只是把 residual 总能量画成一个参考半径。
判断规则是：

```text
某个 harmonic 点明显在 residual circle 外:
  这个谐波显著，说明存在稳定确定性谐波分量。

某个 harmonic 点在 residual circle 附近或里面:
  它可能只是噪声/随机误差投影出来的，不要过度解释相位。
```

因此：

```text
Thermal Noise polar:
  H2~H5 都接近噪声圈，角度基本没有物理意义。

Static Nonlinearity polar:
  H2/H3 明显突出 residual circle，幅度和相位都值得解释。

Glitch polar:
  residual circle 很大，说明主要误差是 broadband / impulsive residual；
  H2~H5 方块更多是 glitch 对 harmonic basis 的随机投影。
```

#### 数学和电路上是否合理

数学上，这个方法合理。它本质是最小二乘 / 正交投影：

```text
把信号投影到 [1, cos(kωt), sin(kωt)] 组成的谐波子空间；
投影上的部分叫 harmonic；
投影之外的部分叫 residual。
```

这正适合单音 ADC 动态测试，因为很多静态非线性在单音下确实表现为整数倍谐波：

```text
x^2 -> DC + HD2
x^3 -> fundamental + HD3
```

但它不是万能物理分类器。它只能说明：

```text
某部分误差和 harmonic basis 高度相干。
```

不能单独证明：

```text
它物理上一定来自静态非线性。
```

电路建模上，三类 case 的合理性不同：

```text
Thermal Noise:
  signal = ideal sine + white noise
  这是 ADC/前端热噪声的最小行为模型，合理。

Static Nonlinearity:
  signal = DC + x + k2*x^2 + k3*x^3 + noise
  这是 memoryless transfer curve 的低阶多项式近似，作为行为模型合理。
  真实来源可能是采样开关 Ron 非线性、输入 buffer 非线性、前端压缩、
  reference modulation、CDAC mismatch 等，但不一定真的等于低阶多项式。

Glitches:
  少数样本加 +0.1 impulse
  这是 sparkle code / transient glitch 的教学模型，合理但简化。
  真实 glitch 可能有正负极性、幅度分布、码相关性、时钟相关性或 burst 结构。
```

所以这两个 example 的定位应是：

```text
作为教学 demo:
  合理。它训练你区分“稳定相干谐波”和“随机/脉冲 residual”。

作为数学工具:
  合理，但应称为 harmonic projection / least-squares decomposition。

作为电路模型:
  简化较重。它不是某颗 ADC 的签核级电路仿真。
```

还要注意两个 demo 参数并不一致：

```text
exp_a11:
  Fin = 10.1234567 MHz
  A = 0.25

exp_a12:
  Fin ≈ 99.902344 MHz
  A = 0.5
```

因此不能把两张图当作同一份数据的两个视图；它们是同一分解思想的两个演示脚本。

### 与 stage_03 的衔接

stage_03 回答了"HD2/HD3 从哪来（k2/k3 系数）"。
本节回答"怎么把 HD2/HD3 单独测出来（幅度+相位+独立波形）"。
两者是"成因 → 测量"的完整闭环。

---

## 衔接实验：exp_d15（未校准 mismatch spur）

stage_04 把 `exp_d15` 列为官方示例，但全程没跑过。它值得专门跑一次，因为它是
理解 stage_06 校准**为什么有效**的最佳前置实验：先看"不校准会差成什么样"。

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
```

数据建模信息：

```text
数据来源:
  SAR 行为模型合成数据，不是真实芯片 capture。

SAR 参数:
  NUM_BITS = 16
  N_SAMPLES = 16384
  FS = 16384
  FIN_BIN = 1777
  input = 0.5 + 0.5 * sin(2π * FIN_BIN * n / N_SAMPLES)
  quant_range = [0, 1]

权重模型:
  nominal_weights = ideal 16-bit binary SAR weights
  actual_weights = nominal_weights + unit-cap mismatch

mismatch sweep:
  sigma_Cu = 0 / 0.1% / 1% / 10%
  random seed = BASE_SEED + case_index

关键注入位置:
  sar_convert 用 actual_weights 编码，也就是 analog CDAC 是失配的；
  sar_reconstruct 却故意用 nominal_weights 重构，也就是 digital backend 未校准。

这不是校准实验:
  它故意不调用 calibrate_weight_sine；
  目的是建立“未校准 mismatch 会产生多大 spur penalty”的基线。
```

实测（unit cap mismatch sigma 扫 4 档）：

```text
sigma_Cu    SNDR_dB   ENOB    SFDR_dB   THD_dB
0%          98.10     16.00   122.66    -126.53
0.1%        97.88     15.97   116.63    -116.58
1%          91.71     14.94    98.16    -97.08
10%         78.18     12.69    86.10    -84.87
```

读这张表的方式：

```text
sigma=0%   : 理想 SAR，SNDR=98 dB（16 bit 满量程），SFDR 123 dB
sigma=1%   : 1% 电容失配，SNDR 掉到 91.7（掉 6 dB，相当于丢了 1 bit）
             SFDR 从 123 掉到 98（掉 25 dB！）—— 这就是 mismatch 的杀伤力
sigma=10%  : SNDR 78（接近 12.7 bit），SFDR 只剩 86
```

**SFDR 掉 25 dB**（sigma=1% 时）正是 stage_06 校准要修的东西。
回忆 stage_06 d16/d18 的结果：同样的 1% mismatch，校准后 SFDR 能回到 110+ dB。
d15 给出了"修之前"的基线，让 d16/d18 的"修之后"有对照。

这和 stage_07 §4 讲的"对比才能证明校准有效"是完全一致的逻辑——
**没有 uncalibrated 基线，就无法声称校准带来了改善**。

---

## 补充 4：INL/DNL from sine（静态线性指标）

### 为什么 INL/DNL 不能只放在“可选脚本”里

Stage 02 的 SNDR/SFDR/THD 是动态单音指标，回答的是：

```text
这个 ADC 对某个 sine 的频域表现如何？
```

INL/DNL 是静态 transfer curve 指标，回答的是：

```text
每个 code 的宽度是否正确？
累计转移曲线相对理想直线偏了多少？
```

两者相关但不等价。一个 ADC 可以有不错的 SNDR，但局部 code width 异常；也可以有可见
INL，但在某个输入频点和幅度下动态指标仍然可接受。因此看到 `analyze_inl_from_sine`
时，不要把它当成另一个频谱函数。

### sine histogram 的直觉

`analyze_inl_from_sine` 用的是 sine histogram 思路：

```text
1. 给 ADC 输入接近满幅的 sine。
2. 统计每个 output code 出现了多少次。
3. 理想 sine 的 PDF/CDF 是已知的，越靠近峰值停留时间越长。
4. 如果某个 code 出现次数比理论多，说明这个 code bin 更宽；反之更窄。
5. code width 偏差积分起来，就是 INL。
```

所以它依赖足够长的记录。样本太少时，histogram 抖动会直接变成 DNL/INL 噪声。

### 实验 4：跑 exp_a32

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a32_inl_from_sine_sweep_length.py
```

数据建模信息：

```text
数据来源:
  手工合成 sine waveform，不是真实 ADC capture。

公共参数:
  n_bits = 16
  full_scale = 1.0
  fs = 800 MHz
  fin_target = 80 MHz
  A = 0.49 Vpeak
  DC = 0.5
  base_noise = 50 uVrms

非理想性:
  HD2 = -80 dBc
  HD3 = -66 dBc
  k2、k3 由目标 HD2/HD3 反推

记录长度 sweep:
  N = 2^10, 2^14, 2^18, 2^22
  每个 N 都重新找 coherent frequency

注入顺序:
  sine_ac -> k2*sine_ac^2 + k3*sine_ac^3 -> DC -> thermal noise

分析步骤:
  先 analyze_spectrum 看动态指标；
  再 analyze_inl_from_sine 用 sine histogram 估计 DNL/INL。
```

这个实验扫记录长度，但它的定位要说得更谨慎。它**不是一个严谨的真实 ADC
DNL/INL 测量示范**，而更像是：

```text
sine-histogram estimator 在不同记录长度、输入失真、code 覆盖条件下会输出什么 apparent DNL/INL。
```

原因是：这个 demo 不是构造一个已知 transition-level DNL/INL 的 ADC，再用理想正弦去测；
它是在输入 waveform 里直接加入：

```text
sine_ac + k2*sine_ac^2 + k3*sine_ac^3
```

然后 `analyze_inl_from_sine` 又按“输入应是理想正弦”的假设从 histogram 反推 DNL/INL。
于是算法会把输入源 HD2/HD3 造成的 PDF 偏差，解释成 ADC code transition 的偏差。

所以这里更准确应叫：

```text
apparent DNL / apparent INL under ideal-sine assumption
```

而不是：

```text
真实 ADC transition DNL/INL。
```

#### 这里的 DNL/INL 到底怎么算

理想 LSB 本身是已知的：

```text
num_bits = 16
full_scale = 1.0
LSB_ideal = full_scale / 2^16
```

短记录的问题不是“不知道 LSB”，而是无法可靠估计每个 code 的实际 transition width。
`compute_inl_from_sine.py` 的核心流程是：

```python
counts, _ = np.histogram(codes_clipped, bins=bins)

cumulative_distribution = -np.cos(
    np.pi * np.cumsum(counts) / np.sum(counts)
)

dnl = np.diff(cumulative_distribution[0:-1])

dnl = dnl / np.sum(dnl)
dnl = dnl * code_range - 1
dnl = dnl - np.mean(dnl)
dnl = np.maximum(dnl, -1)

inl = np.cumsum(dnl)
```

翻成概念就是：

```text
1. 把 waveform 量化成 codes。
2. 对 codes 做 histogram，得到每个 code 的 hit count。
3. 用 sine CDF 的反函数，把累计 hit count 映射成 transition 位置。
4. 相邻 transition 的差值就是估计 code width。
5. code width / ideal_width - 1 得到 DNL。
6. INL = cumulative sum of DNL。
```

DNL 的下界通常是：

```text
DNL = -1  -> missing code / zero width
```

但上界不是 `+1`。如果某个 code 被估计为很宽：

```text
DNL = actual_width / ideal_width - 1
```

可以远大于 `+1`。因此图里 `+196 LSB` 不是定义上不可能，而是说明：

```text
在严重欠采样/覆盖不足时，histogram estimator 把少数 hit 误解释成超宽 code。
```

#### 为什么短记录会出现巨大 DNL/INL

`N=2^10` 时只有 1024 个样本，却要估计接近 65536 个 code：

```text
average samples/code ≈ 1024 / 65536 = 0.016
```

大量 code 没 hit，少数 code 只有 1 次 hit。算法不知道“这是样本太少”，只能按统计概率解释：

```text
zero count:
  可能被解释成 missing / narrow code。

single count:
  可能被解释成比理想概率大很多的 wide code。
```

粗略用 ramp 直觉看：

```text
ideal count/code = 0.016
one hit -> 1 / 0.016 - 1 ≈ 61.5 LSB
```

sine histogram 还要经过 `-cos(pi*C)` 的非线性 CDF 反变换，所以局部峰值可以更大。
INL 又是：

```text
inl = cumsum(dnl)
```

于是 DNL 的巨大统计伪影会累计成看起来很夸张的 INL。

#### 记录长度只是必要条件，不是充分条件

这个问题不只取决于样本总数 `N`。真正需要的是：

```text
输入幅度覆盖目标 code 区间；
唯一采样相位点足够多；
每个 code 的期望 hit count 足够大；
采样相位不能和 code transition 形成坏的周期性锁定；
输入源要足够纯，否则 source distortion 会被误解释成 ADC INL；
噪声/dither 不能过大，否则 transition 被 smear。
```

如果：

```text
Fin/Fs = p/q
```

且 `p/q` 是小分母有理数，那么离散正弦最多只有 `q` 个唯一相位点。即使采很多周期，也只是在
重复同一批幅度点，很多 code 永远不会被覆盖。

本 demo 每个 `N` 都调用：

```python
fin, J = find_coherent_frequency(fs, fin_target, N)
```

实际离散正弦是：

```text
x[n] = A sin(2π J n / N)
```

当 `gcd(J, N)=1` 时，`J*n mod N` 会遍历 `0...N-1` 的相位格点，所以唯一相位点数随
`N` 增加。这解释了为什么这里 `N` 变大后图会逐渐稳定。但这不是说“只要采得久就一定可以”，
而是因为这个 demo 同时让 coherent 相位网格随 `N` 变密。

#### 为什么 INL 呈奇函数 / 正弦形

这不是所有 ADC INL 的必然形状，而是本实验注入模型决定的。脚本目标是：

```text
HD2 = -80 dBc
HD3 = -66 dBc
```

三阶项明显强于二阶项。换成函数直觉：

```text
error(x) ≈ k3*x^3 + smaller k2*x^2
```

三阶项是奇函数。再考虑 INL/DNL 计算会去掉 offset / gain-like 成分，三阶残差更像：

```text
x^3 - α*x
```

这仍然是奇函数，而且端点受约束后看起来像平滑的 S 形 / 正弦形。二阶项会贡献偶函数 /
U 形成分，但本实验里 HD2 比 HD3 小 14 dB 左右，因此被三阶形状压住。

还要再次强调：这里得到的不是“某颗 ADC 的真实 INL 必然是奇函数”，而是：

```text
带 HD3 主导的失真正弦，在 ideal-sine histogram 假设下，被投影成了 odd/S-like apparent INL。
```

#### 这张图的正确结论

不应写成：

```text
N 越大，越接近真实静态非线性。
```

更准确是：

```text
N 越大，apparent DNL/INL estimator 越稳定；
但它稳定收敛到的，不一定是真实 ADC INL。
```

在本 demo 里，它更可能收敛到：

```text
输入源 HD2/HD3 + 量化 + 噪声，在“理想正弦输入”假设下形成的等效曲线。
```

如果要做严谨 INL/DNL demo，应该改成两类之一：

```text
版本 A：真实静态 ADC INL/DNL 验证
  构造已知 transition-level DNL/INL 的 ADC；
  用理想正弦激励；
  sine histogram 反推；
  和 ground truth 对比。

版本 B：输入源污染警示
  明确说明输入正弦含 HD2/HD3；
  输出叫 apparent INL/DNL；
  目的就是展示 source distortion 会污染 sine-histogram INL。
```

当前 example 混在两者中间。作为“记录长度影响 histogram 稳定性”的教学图有价值；
作为“正确测量 ADC INL/DNL”的示范则不够严谨。

和 Stage 07 的验证思想连接起来，INL/DNL 结果必须同时报告：

```text
输入幅度；
源纯度；
clip_percent；
记录长度；
唯一相位点/相位网格；
code 覆盖范围；
平均 samples/code；
是否存在动态误差或 dither。
```

---

## 补充 5：多记录频谱平均与 polar coherent averaging

### power averaging 只让图更稳，不给 processing gain

Stage 02 已经讲了单条记录的 FFT、window、ENBW。多记录平均是另一个问题：

```text
power averaging:
  对 |FFT|^2 或功率谱平均
  丢掉相位
  noise floor 视觉上更平滑
  SNR 通常不按 10log10(Nrun) 提升
```

这适合做稳定的噪声底估计，但不能把多个记录当成一个相干积分器。

### coherent averaging 保留相位，能给 processing gain

```text
coherent averaging:
  先对齐相位，再平均 complex FFT
  随机噪声相互抵消
  相干的 fundamental / harmonic 被保留
  理想 processing gain 约为 10log10(Nrun)
```

代价是条件更苛刻：频率、采样、相位参考都要可对齐。真实测试里，如果触发相位漂移、
输入源相位不稳或记录不是同一个 coherent grid，coherent averaging 会失败。

### 实验 5：跑 exp_s07 + exp_s12

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s07_spectrum_averaging.py
uv run python src\adctoolbox\examples\02_spectrum\exp_s12_polar_coherent_averaging.py
```

数据建模信息：

```text
数据来源:
  多条手工合成 waveform，不是真实 ADC capture。

exp_s07:
  Fs = 100 MHz
  N_fft = 2^13 = 8192
  Fin target = 5 MHz，实际取 coherent frequency
  A = 0.499 Vpeak
  noise_rms = 100 uVrms
  HD2 = -100 dBc
  HD3 = -90 dBc
  N_runs = 1 / 10 / 100

exp_s12:
  Fs = 100 MHz
  N_fft = 2^10 = 1024
  Fin target = 5 MHz，实际取 coherent frequency
  A = 0.499 Vpeak
  noise_rms = 100 uVrms
  HD2 = -80 dBc
  HD3 = -73 dBc
  N_runs = 1 / 10 / 100

每条 run 的生成顺序:
  先随机 fundamental phase；
  生成 sine；
  加 static nonlinearity: y = x + k2*x^2 + k3*x^3；
  最后加 thermal noise。

分析步骤:
  power averaging:
    丢弃相位，只平均功率谱。

  coherent averaging:
    对齐相位后平均 complex FFT。

  polar coherent averaging:
    在 polar 图上保留 harmonic phase relationship。
```

`exp_s07` 对比 power averaging 和 coherent averaging：

```text
power averaging:    噪声底更光滑，但 SNR 基本不变
coherent averaging: 相位对齐后，SNR 随 run 数显著提升
```

`exp_s12` 把这个思想放到 polar spectrum：

```text
coherent averaging 后，随机噪声被压低；
HD2/HD3 的相位关系仍然留在 polar 图上；
所以它同时服务于“看得更干净”和“保留相位诊断信息”。
```

实测上，`exp_s12` 的趋势非常清楚：

```text
N_run = 1:
  ENOB = 11.10, SNDR = 68.58 dB, SNR = 70.90 dB

N_run = 10:
  ENOB = 11.61, SNDR = 71.67 dB, SNR = 81.41 dB

N_run = 100:
  ENOB = 11.70, SNDR = 72.17 dB, SNR = 91.51 dB
```

这里 SNR 随 run 数明显改善，是因为随机噪声在 complex average 中被抵消。SNDR / ENOB
没有按同样幅度继续提升，是因为 demo 里还故意加入了稳定的 HD2 / HD3；这些谐波和输入相干，
不会被相干平均消掉。

修复 polar 注释后的图上，HD2 / HD3 也回到和注入模型一致的位置：

```text
N_run = 1:
  HD2 ~= -79.9 dB, angle ~=  1.5 deg
  HD3 ~= -73.6 dB, angle ~= -3.2 deg

N_run = 10:
  HD2 ~= -79.8 dB, angle ~= -0.3 deg
  HD3 ~= -73.1 dB, angle ~= -0.0 deg

N_run = 100:
  HD2 ~= -80.0 dB, angle ~= -0.4 deg
  HD3 ~= -73.0 dB, angle ~= -0.0 deg
```

如果旧图里 HD2 / HD3 被标成接近 `-150 dB`，那不是这个实验的理论结论，而是 polar
annotation 的实现问题：谱线本身存在，图中文字读错了要标注的幅度。修复后，标注与注入的
`HD2=-80 dBc`、`HD3=-73 dBc` 对齐。

### exp_s12 到底怎么平均

`exp_s12` 不是把多条 time waveform 直接相加，而是走 complex spectrum averaging：

```text
1. 为每条 run 随机取一个 fundamental phase:
     s_r[n] = A * sin(2*pi*fin*n/fs + phi_r)

2. 在这个 sine 上加入静态非线性:
     y_r[n] = s_r[n] + k2*s_r[n]^2 + k3*s_r[n]^3 + noise_r[n]

3. 对每条 run 做 FFT，得到复数谱:
     Y_r[k]

4. 找到 fundamental bin 的相位，作为这一条 run 的相位参考。

5. 把每条 run 的复数谱旋转到同一个输入相位参考下。

6. 对旋转后的复数谱做 complex average。

7. 用平均后的复数谱画 spectrum 和 polar 图。
```

这里最容易误解的是第 5 步。它不是“把整张频谱所有 bin 统一乘同一个相位因子”，也不是只把
fundamental 的相位调成 0 就结束。对由同一个输入相位 `phi` 派生出来的静态谐波，谐波相位会按阶数变化：

```text
x = A * sin(wt + phi)

x^2 里出现 2nd harmonic:
  phase contains 2*phi

x^3 里出现 3rd harmonic:
  phase contains 3*phi
```

所以如果一条 run 的 fundamental phase 多了 `phi`，同一条 run 的 HD2 / HD3 相位会分别多出
`2*phi` / `3*phi`。为了把不同 run 放到同一个相位参考下，正确的相对相位应该近似看成：

```text
HD2 relative phase = angle(H2) - 2 * angle(H1)
HD3 relative phase = angle(H3) - 3 * angle(H1)
HDh relative phase = angle(Hh) - h * angle(H1)
```

这背后的数学不是“任意给谐波多转几倍”，而是 DFT 的时间平移 / 输入相位性质：同一个时间原点偏移，
在频率 bin `k` 上表现为和 `k` 成正比的相位斜坡。若第 `h` 次谐波位于 fundamental bin 的
`h` 倍位置，它对同一个输入相位参考的响应也自然是 `h` 倍。

但这个逻辑有一个重要边界：

```text
它只适用于和输入相位锁定的成分：
  fundamental、静态 HD2、静态 HD3、由同一输入非线性产生的相干谐波。

它不应该被解释为：
  任意 spur 都会按 harmonic order 跟着 fundamental 相位走。
```

如果某个 spur 来自独立时钟串扰、随机 glitch、异步干扰或非相位锁定噪声，它不会满足
`angle(Hh) - h*angle(H1)` 这种关系。相干平均会倾向于把这类不相干成分平均掉，或者让它们在
polar 图上变成散开的云，而不是稳定的谐波点。

这就是为什么 `exp_s12` 不该只留在 docs expected output 里：它补上了 Stage 11 的最后一块，
也把 Stage 02 的平均、Stage 03 的谐波、Stage 11 的 polar 视角连起来。

---

## 全量 example 索引：每个脚本该怎么看

这一节把 59 个 runnable examples 全部收齐。每个条目后面的说明不是复述源码，而是告诉你：

```text
它对应哪个知识背景；
跑完主要看哪个现象；
如果结果异常，应优先回到哪个 stage 查概念。
```

### `01_basic/`：环境与采样基本功

```text
exp_b01_environment_check
  背景：环境、自检、matplotlib 输出。
  看点：能否正常 import adctoolbox、生成信号并保存图。

exp_b02_coherent_vs_non_coherent
  背景：stage_02 的 coherent sampling / leakage。
  看点：非相干采样时能量泄漏到邻近 bin，window 会改变泄漏形态。
```

### `02_spectrum/`：频谱分析方法论

```text
exp_s00_fft_fundamentals
  背景：FFT bin、频率轴、幅度归一。
  看点：离散频率 bin 怎么对应真实频率。

exp_s01_analyze_spectrum_simplest
  背景：stage_02 的最小 analyze_spectrum 调用。
  看点：SNDR/SFDR/SNR/THD/ENOB 的基本输出。

exp_s02_analyze_spectrum_interactive
  背景：同一频谱分析的交互式查看。
  看点：交互图用于人工检查 spur，而不是新数学。

exp_s03_analyze_spectrum_savefig
  背景：报告/自动化出图。
  看点：如何把频谱结果固定成文件。

exp_s04_sweep_dynamic_range
  背景：输入幅度 sweep 与动态范围。
  看点：输入太小受噪声主导，太大可能受 clipping/distortion 主导。

exp_s05_annotating_spur
  背景：spur 标注。
  看点：MaxSpur、harmonic marker、噪声底线如何辅助读图。

exp_s06_sweeping_fft_and_osr
  背景：FFT length、OSR、分析带宽。
  看点：点数和带宽定义会影响噪声积分与 NSD 解释。

exp_s07_spectrum_averaging
  背景：power averaging vs coherent averaging。
  看点：非相干功率平均让谱线更稳；相干平均保留相位，可降低随机噪声。

exp_s08_windowing_deep_dive
  背景：window leakage、main lobe、side lobe。
  看点：window 不是“让频谱更真实”，而是在泄漏和分辨率之间折中。

exp_s09_sar_fft_length_near_nyquist
  背景：SAR 输出接近 Nyquist 时的频谱设置。
  看点：Fin 接近 Nyquist 时，bin、alias、window 更容易被误读。

exp_s10_cartesian_and_polar_plot
  背景：笛卡尔频谱 vs polar 频谱。
  看点：同一复数谱既有幅度，也有相位。

exp_s11_polar_memory_effect
  背景：stage_03 的 memory effect + 本阶段 polar 视角。
  看点：记忆效应会让谐波相位散开，不只是幅度变高。

exp_s12_polar_coherent_averaging
  背景：coherent averaging + polar spectrum。
  看点：相干平均保留相位结构，能把稳定谐波从随机噪声中提出来。
```

### `03_generate_signals/`：生成侧非理想性

```text
exp_g01_generate_signal_demo
  背景：stage_01/02 的热噪声、正弦生成、SNR/NSD。
  看点：thermal noise RMS 每翻倍一次，SNR 约下降 6 dB。

exp_g03_sweep_quant_bits
  背景：6.02N + 1.76 dB。
  看点：bit 数增加时，理想量化 SNDR 和 ENOB 如何变化。

exp_g04_sweep_jitter_fin
  背景：jitter-limited SNR 与 Fin 成反比恶化。
  看点：同样 jitter，在高输入频率下造成更大误差。

exp_g05_sweep_static_nonlin
  背景：stage_03 的 k2/k3 静态非线性。
  看点：HD2/HD3 如何随非线性系数增长。

exp_g06_sweep_dynamic_nonlin
  背景：动态非线性、memory、settling。
  看点：失真不只由瞬时输入值决定，也可能由历史状态决定。

exp_g07_sweep_interferences
  背景：干扰、clipping、外加 tone。
  看点：频谱中的 spur 不一定来自 ADC 本体，也可能来自输入条件。
```

#### exp_g01 / exp_g03：已经跑过的两个生成侧基线

`exp_g01_generate_signal_demo` 是 thermal noise baseline，不是量化实验。它的建模信息是：

```text
Fs = 100 MHz
N = 2^13 = 8192
Fin ~= 12 MHz, coherent bin = 983 / 8192
A = 0.5 Vpeak
DC = 0.5
非理想性: 只加入 thermal noise
noise_rms = 0 / 50 uV / 100 uV / 200 uV
```

实测结果符合热噪声直觉：

```text
50 uV  -> SNR ~= 77.14 dB
100 uV -> SNR ~= 70.98 dB
200 uV -> SNR ~= 65.22 dB
```

噪声 RMS 每翻倍一次，噪声功率增加约 6 dB，所以 SNR/SNDR 约下降 6 dB。
`Clean Sinewave` 的 `ENOB=32.93`、`SNDR=200 dB` 不代表真实 ADC 性能，只是无噪声、
无量化、无非线性条件下的数值上限 / 保护值。噪声图里的 `MaxSpur` 也不是确定性 spur，
而是有限 FFT 中随机噪声最高的 bin。

`exp_g03_sweep_quant_bits` 是理想量化实验。建模信息是：

```text
Fs = 1 GHz
N = 2^16 = 65536
Fin ~= 80 MHz, coherent sampling
A = 0.5 Vpeak
DC = 0.5
输入范围 = 0 ~ 1
非理想性: 只加入理想量化
bit sweep = 2, 4, 6, 8, 10, 12, 14, 16 bit
```

这里要特别小心 `SNR`、`SNDR`、`ENOB` 的关系。ADCToolbox 里 ENOB 的源码定义是：

```python
sndr_dbc = 10 * np.log10(sig_linear / noi_sndr)
enob = (sndr_dbc - 1.76) / 6.02
```

也就是：

```text
ENOB = (SNDR - 1.76) / 6.02
```

这符合 ADC 动态测试习惯：ENOB 通常由 `SINAD/SNDR` 反推，而不是由只排除谐波后的
`SNR` 反推。区别是：

```text
SNR:
  Signal / Noise
  通常排除 harmonic distortion。

SNDR / SINAD:
  Signal / (Noise + Distortion)
  包含 harmonic、spur、量化失真。

ENOB:
  把测得的 SNDR 换算成“等效理想 bit 数”。
```

因此，`ENOB 接近配置 bit 数` 和 `SNDR 接近 6.02N+1.76` 不是两条独立证据。
它们是同一件事的两种单位：

```text
SNDR measured -> ENOB_from_SNDR
```

这个实验真正独立验证的是：

```text
配置的 bit 数 N
  -> 生成理想量化 waveform
  -> 频谱测得 SNDR
  -> SNDR 是否接近理想量化公式 6.02N + 1.76 dB
```

低 bit 时尤其能看出 `SNR` 和 `SNDR` 的差异。2-bit 情况下：

```text
SNR  = 38.76 dB
SNDR = 13.30 dB
理论 = 13.80 dB
ENOB = (13.30 - 1.76) / 6.02 = 1.92 bit
```

为什么 `SNR` 会虚高？因为低 bit 量化误差不是理想白噪声，会有很强的确定性 spur /
harmonic。`SNR` 把这些谐波失真排除后，只剩随机噪声，所以看起来很高；`SNDR` 把它们都算进
非信号功率，因此才和理想量化公式一致。

所以这个 example 的结论应写成：

```text
ENOB 用 SNDR 算: 符合定义。
console 把 SNR measured 和 6.02N+1.76 并列比较: 不严谨。
更好的表头:
  Bits | Measured SNDR | Ideal SNDR/SQNR | ENOB_from_SNDR
```

还有一个可视化小问题：`exp_g03` 第一幅 2-bit 图里，`MaxSpur` 文字容易跑到 panel 外面。
这不是数据问题，而是通用 `plot_spectrum.py` 的标注策略不够鲁棒：

```python
ax.text(spur_bin_idx / N * fs, spur_db + 10, 'MaxSpur', ...)
```

当 spur 本身很高时，`spur_db + 10` 会贴近甚至超过 y 轴上边界。这个问题应该在通用
`plot_spectrum.py` / `plot_spectrum_virtuoso.py` 中做 label clamp 或自动改放到 marker 下方，
不应只在 `exp_g03` 局部修。

#### exp_g06：8 类非理想性的频谱对照

`exp_g06_sweep_dynamic_nonlin.py` 的名字里有 `sweep_dynamic_nonlin`，但它更准确是一个
**nonideality case comparison**：把 8 种非理想性放在同一套 FFT 条件下比较。

统一输入条件是：

```text
Fs = 1 GHz
N = 2^13 = 8192
Fin ~= 80 MHz
A = 0.5
DC = 0
base_noise = 10 uVrms
```

实测结果：

```text
Static HD3 Only          SFDR 80.01 dB, THD -80.01 dB
Incomplete Settling      SFDR 80.25 dB, THD -80.25 dB
Memory Effect +          SFDR 81.29 dB, THD -79.93 dB
Memory Effect -          SFDR 81.10 dB, THD -78.97 dB
RA Static Gain +         SFDR 81.10 dB, THD -78.62 dB
RA Static Gain -         SFDR 81.22 dB, THD -80.53 dB
RA Dynamic Gain +        SFDR 70.43 dB, THD -70.31 dB
RA Dynamic Gain -        SFDR 70.23 dB, THD -70.17 dB
```

**1. Static HD3 Only**

源码模型：

```python
y = x + k3 * x**3
```

这是 memoryless static nonlinearity：输出只依赖当前输入值，不依赖上一拍。因为：

```text
sin^3(theta) = (3sin(theta) - sin(3theta)) / 4
```

所以三次项会带来：

```text
fundamental gain shift + HD3
```

图里主要就是一个稳定的 HD3，约 `-80 dBc`。这是最干净的“静态三阶非线性基准”。

**2. Incomplete Settling**

源码模型：

```python
tau_dynamic = tau_nom * (1 + coeff_k * v_target**2)
vout[n] = v_target + (v_prev - v_target) * exp(-T_track / tau_dynamic)
```

它模拟采样/保持或前端 buffer 没有在有限 tracking 时间内完全跟上输入。若 `tau` 是常数，
它更像线性低通，只改变幅度和相位，不一定产生谐波；但这里 `tau` 随 `v_target^2` 变化：

```text
输入幅度越大，settling 时间常数越变；
当前输出还依赖上一拍 v_prev。
```

所以它是：

```text
动态误差 + 幅度相关误差
```

单音下也会产生 HD3。图里它和 Static HD3 很像，是因为 demo 参数把三阶失真强度调到
约 `-80 dBc`。

注意一个文案问题：panel 标题写 `Incomplete Settling (+0.005)`，但源码实际参数是：

```python
coeff_k = +0.09
```

因此这张图的数据可以看，但标题中的数值不严谨。

**3. Memory Effect (+0.005)**

源码模型：

```python
msb = floor(signal * 2**4) / 2**4
lsb = floor((signal - msb) * 2**12) / 2**12
msb_shifted = roll(msb, 1)

y[n] = msb[n] + lsb[n] + memory_strength * msb[n-1]
```

也就是说，当前输出里混入了上一拍的 MSB 粗码。电路直觉是：

```text
上一拍 CDAC/MSB switching 残留；
charge injection；
reference / residue memory；
前一拍粗量化状态影响当前转换。
```

它不是简单的：

```text
y = f(x)
```

而是：

```text
y[n] = f(x[n], state[n-1])
```

所以频谱不只一个干净 HD3，周围会出现更多 code/path 相关 spur，噪声底也更毛。

**4. Memory Effect (-0.005)**

和第 3 个模型相同，只是记忆项符号反过来：

```text
y[n] = current_code - 0.005 * previous_msb
```

负号主要改变记忆误差相位。普通幅度频谱里，正负号不一定让 HD 幅度发生巨大变化，
但会改变 harmonic phase / spur pattern。所以图上 `+0.005` 和 `-0.005` 看起来相近，
不代表物理完全一样，只是 Cartesian magnitude spectrum 对符号/相位不敏感。

**5. RA Static Gain (+0.5%)**

源码默认是 `mode="coarse_path"`：

```python
msb = floor(signal_ac * 2**msb_bits) / 2**msb_bits
lsb = floor((signal_ac - msb) * 2**lsb_bits) / 2**lsb_bits

y = msb * relative_gain + lsb
```

这里 `relative_gain=1.005`。名字叫 RA gain error，但按当前默认实现，它更准确是：

```text
two-stage reconstructed coarse/MSB path gain mismatch
```

也就是粗段 MSB 路径被多放大 0.5%，LSB residue 正常加回。因为 MSB 是分段阶梯函数，
所以这不是普通全局 gain error，而是 code-dependent piecewise error，会产生 spur/harmonic。

**6. RA Static Gain (-0.5%)**

同上，只是：

```text
relative_gain = 0.995
```

粗段 MSB 路径偏小 0.5%。它主要改变误差符号/相位，幅度谱上和 `+0.5%` 不会完全对称，
但会比较接近。

一个重要边界：源码也提供 `mode="residue_path"`，更接近“residue amplifier gain error”
的解释；但这个 example 没用它，用的是默认 `coarse_path`。因此讲电路含义时不能把它直接
等同于真实 residue amplifier 路径误差。

**7. RA Dynamic Gain (+0.5%)**

源码核心：

```python
G_dynamic = relative_gain + coeff_3 * (v_dynamic_state_prev_ac ** 2)
y[n] = v_msb_code[n] * G_dynamic + v_lsb_code[n]
```

这里 `coeff_3=+0.005`。它比 RA Static Gain 更严重，因为 gain 不再是常数，而是依赖上一状态的平方：

```text
gain[n] = 1 + coeff * state[n-1]^2
```

所以它同时具备：

```text
code-dependent；
history-dependent；
amplitude-dependent；
nonlinear gain modulation。
```

这很容易产生强 HD3 和其他 spur。图里它的 SFDR/THD 恶化到约 `70 dB`，明显比前几个
`80 dB` 级别更差。

**8. RA Dynamic Gain (-0.5%)**

同第 7 个，只是：

```text
coeff_3 = -0.005
```

动态增益随上一状态平方反方向变化。因为平方项本身是偶函数，变号主要改变失真相位和某些
harmonic/spur 组合，但幅度上仍然很严重。所以图里 `+0.5%` 和 `-0.5%` 都在约 `70 dB`
SFDR 附近。

这个实验的真正价值不是“哪个参数扫了多少”，而是训练你区分：

```text
memoryless static distortion
  当前值非线性，最干净。

dynamic / history-dependent distortion
  当前输出还受上一状态影响。

piecewise code-path distortion
  MSB/LSB 分段路径或残留状态造成 code-dependent spur。
```

#### exp_g07：干扰类型的频域指纹

`exp_g07_sweep_interferences.py` 是 `03_generate_signals` 这一组的最后一个实验。它不再只看
ADC 本体非理想，而是把多种输入/系统干扰分别加到同一个 coherent sine 上：

```text
Fs = 1 GHz
N = 2^13 = 8192
Fin ~= 80 MHz
A = 0.5
DC = 0
base_noise = 10 uVrms
```

每个 panel 独立加入一种干扰：

```text
1. Clean
2. Glitch
3. AM Tone
4. AM Noise
5. Clipping 1%
6. Clipping 2%
7. Drift
8. Reference Error
```

实测结果：

```text
Clean              SFDR 114.85 dB, THD -118.94 dB, SNR 91.10 dB
Glitch             SFDR  74.22 dB, THD  -74.96 dB, SNR 43.05 dB
AM Tone            SFDR  72.07 dB, THD -121.26 dB, SNR 91.00 dB
AM Noise           SFDR  85.62 dB, THD  -85.47 dB, SNR 60.32 dB
Clipping 1%        SFDR  97.37 dB, THD  -95.04 dB, SNR 90.44 dB
Clipping 2%        SFDR  79.54 dB, THD  -76.58 dB, SNR 90.07 dB
Drift              SFDR  61.97 dB, THD -121.20 dB, SNR 91.16 dB
Reference Error    SFDR  59.08 dB, THD  -59.04 dB, SNR 90.90 dB
```

先记住频率参考：

```text
Fin  ~= 80 MHz
HD2  ~= 160 MHz
HD3  ~= 240 MHz
Nyquist = 500 MHz
```

**1. Clean Signal**

只有基波和 `10 uVrms` 底噪：

```text
基波在 80 MHz；
噪声底很低；
HD2 / HD3 基本在噪声底；
MaxSpur 是随机噪声里的最高 bin。
```

所以它的 SFDR 高、THD 很低、SNR 约 `91 dB`。这是后面所有 case 的参考基线。

**2. Glitch**

代码模型是稀疏脉冲：

```python
glitch_mask = rand(N) < 0.0005
glitch = glitch_mask * 0.1
y = signal + glitch
```

时域里是少数样本突然跳一下。频域里，窄脉冲会扩散成宽带能量，所以图上表现为：

```text
整片噪声底显著抬高；
没有特别干净的 HD2/HD3 结构；
MaxSpur 是某个随机突出的频点；
SNR 掉得很惨。
```

这类错误在频谱里不像“某个谐波坏了”，更像宽带污染。

**3. AM Tone**

代码模型是确定性幅度调制：

```python
y = x * (1 + m * sin(2*pi*fm*t))
fm = 500 kHz
m = 0.0005
```

数学上：

```text
sin(2*pi*Fin*t) * sin(2*pi*fm*t)
  -> tones at Fin + fm and Fin - fm
```

所以频域特征是：

```text
基波左右出现一对调制边带；
边带不是 HD2/HD3；
THD 很低；
SNR 仍然很好；
但 SFDR 变差。
```

这解释了为什么它的结果是：

```text
SFDR ~= 72 dB
THD  ~= -121 dB
SNR  ~= 91 dB
```

它不是 ADC 非线性谐波，而是调制 spur。

**4. AM Noise**

代码模型是随机幅度调制：

```python
y = x * (1 + random_noise)
```

这相当于：

```text
carrier * white/noisy envelope
```

频域上可以理解成：包络噪声的频谱被搬移到基波附近，并扩散到更宽频带。因此图里：

```text
噪声底明显变厚；
基波附近和全带都有随机调制噪声；
可能出现看似 HD3 的局部峰，但本质是随机 AM 污染；
SNR 明显下降。
```

它和 AM Tone 的区别是：

```text
AM Tone  -> 离散边带
AM Noise -> 宽带噪声底抬高
```

**5. Clipping 1%**

代码模型是按上下 percentile 削顶：

```python
lower = percentile(signal, 1)
upper = percentile(signal, 99)
y = clip(signal, lower, upper)
```

削顶是强非线性，但 1% 比较轻。频域特征是：

```text
出现谐波；
主要是奇次谐波，尤其 HD3；
也会有更高阶谐波；
噪声底本身没有像 glitch 那样整体暴涨。
```

为什么主要奇次？因为输入是零 DC 的对称正弦，正负两端一起削顶，近似奇对称失真，偶次项相对弱。

**6. Clipping 2%**

同样是削顶，但更严重。频域特征是：

```text
HD3 明显抬高；
高阶谐波更多；
SFDR 和 THD 明显恶化；
SNR 仍然接近 90 dB，因为它主要不是随机噪声，而是确定性失真。
```

所以 clipping 的典型模式是：

```text
THD/SFDR 坏；
SNR 不一定坏。
```

这点和 glitch 正好相反。

**7. Drift**

代码模型是低频随机游走：

```python
drift_steps = randn(N) * drift_scale
drift_walk = cumsum(drift_steps)
drift = lowpass(drift_walk)
y = signal + drift
```

它是慢变化基线漂移。频域上慢变化就是低频能量，所以图上：

```text
频谱左侧/低频处有很强 spur；
HD2/HD3 仍然很低；
THD 很好；
SNR 也很好；
但 SFDR 很差。
```

这说明：

```text
SFDR 差不一定是谐波差。
```

Drift 的最大 spur 是低频漂移，不是输入的二三次谐波。

**8. Reference Error**

这个 case 最容易误解，需要从电路、数学和代码三层对齐。

电路上，ADC reference 不是理想电压源。以 SAR/CDAC 为例，转换过程中电容阵列不断切到
`Vref`、`GND` 或 common-mode。每次切换都会从 reference buffer / reference decap 抽取电荷：

```text
Q = C * ΔV
```

如果 reference buffer 输出阻抗不是 0、decap 不够大、或者采样速度太快，那么：

```text
reference node 会被拉低；
恢复不是瞬时的；
当前转换会受前几次转换的 reference 状态影响。
```

而且这个负载通常和输入/code 有关：

```text
输入越大 -> CDAC switching 活动越大 -> reference kick 越大
```

所以 reference error 不是纯随机噪声，而是：

```text
幅度相关 + 历史相关 + 非线性
```

理想 ADC 的数字码本质上表示：

```text
code ~= Vin / Vref * 2^N
```

如果把 code 重构回电压：

```text
V_recon = code * LSB
LSB = Vref / 2^N
```

对 SAR/CDAC 来说更直观：

```text
Vdac = Σ bit_i * C_i/Ctot * Vref
```

也就是说，reference 决定了每一位的真实模拟权重和比较阈值。采样电容先采的是输入电压；
reference 主要在转换阶段提供比较尺度。最终数字结果表达的是：

```text
Vin 相对于 Vref 的量化结果
```

因此 `Vref` droop 会导致：

```text
bit weight / threshold 改变；
同一 code 对应的模拟电压改变；
输出出现幅度相关、历史相关失真。
```

源码模型是：

```python
signal_ac = signal - self.DC

current_kick = droop_strength * abs(signal_ac)
decay = exp(-1.0 / settling_tau)
vref_droop = lfilter([1], [1, -decay], current_kick)

y = signal_ac * (1.0 - vref_droop) + self.DC
```

逐项解释：

```text
current_kick = droop_strength * abs(signal_ac)
  |signal_ac| 越大，reference load 越大。
  用 abs() 表示正半周和负半周都会消耗 reference 能量。
  这不是严格 CDAC switching 方程，而是行为级近似。

vref_droop = IIR(current_kick)
  用一阶 IIR 模拟 reference recovery。

decay = exp(-1 / settling_tau)
  settling_tau 越大 -> decay 越接近 1 -> 恢复越慢 -> memory 越强。

y = signal_ac * (1 - vref_droop)
  把 reference droop 等效成动态 gain error。
```

IIR 对应差分方程：

```text
d[n] = current_kick[n] + decay * d[n-1]
```

所以当前 reference droop 既依赖当前输入幅度，也依赖之前样本的 droop 状态。

为什么图里 Reference Error 主要变成强 HD3？设输入：

```text
x[n] = A sin(ωn)
```

droop 大致和 `|x[n]|` 有关：

```text
d[n] ~= k * |sin(ωn)|
```

而 `|sin|` 不是正弦，它含有 DC 和偶次谐波：

```text
|sin(ωt)| -> DC + 2ω + 4ω + ...
```

输出是：

```text
y[n] = x[n] * (1 - d[n])
```

也就是把 `sin(ωt)` 和 `DC + 2ω + 4ω + ...` 相乘。频域相乘会产生和差频：

```text
sin(ω) * cos(2ω) -> sin(3ω) 和 sin(ω)
sin(ω) * cos(4ω) -> sin(5ω) 和 sin(3ω)
```

所以 Reference Error 很容易产生：

```text
HD3、HD5 等奇次谐波
```

图里就是这样：HD3 成为 MaxSpur，`THD ~= -59 dB`，`SFDR ~= 59 dB`，但 `SNR`
仍然接近 clean case。这说明它主要不是随机噪声问题，而是 reference droop 造成的确定性
非线性 / memory distortion。

总结这 8 个 panel：

```text
Glitch:
  宽带污染，SNR 大幅下降。

AM Tone:
  Fin ± fm 边带，SFDR 差但 THD 好。

AM Noise:
  调制噪声底变厚，SNR 下降。

Clipping:
  硬非线性，奇次谐波和高阶谐波增加。

Drift:
  低频 spur，SFDR 差但 THD/SNR 可能很好。

Reference Error:
  幅度相关 reference droop，强 HD3/奇次谐波。
```

### `04_debug_analog/`：analog output 诊断工具箱

```text
exp_a01_fit_sine_4param
  背景：stage_03 的 sine fitting。
  看点：先拟合基波，才能定义 error/residual。

exp_a02_analyze_error_by_value
  背景：error vs input value。
  看点：静态非线性常随输入幅值呈结构化变化。

exp_a03_analyze_error_by_phase
  背景：error vs sine phase。
  看点：相位视角能分辨周期性误差和瞬态误差。

exp_a04_jitter_calculation
  背景：jitter-limited SNR。
  看点：Fin 越高，同样时间抖动带来的幅度误差越大。

exp_a11_decompose_harmonics
  背景：本阶段谐波分解。
  看点：把 waveform 拆成 fundamental、HD2/HD3、residual。

exp_a12_decompose_harmonics_polar
  背景：谐波分解 + polar 视角。
  看点：谐波的幅度和相位能一起读。

exp_a21_analyze_error_pdf
  背景：误差分布。
  看点：随机噪声近似 PDF，非线性/异常点会改变分布形状。

exp_a22_analyze_error_spectrum
  背景：误差频谱。
  看点：从 residual 里看 harmonic、spur、noise，而不是从原始信号里看。

exp_a23_analyze_error_autocorrelation
  背景：error ACF。
  看点：白噪声相关性低，memory/settling 会留下短 lag 相关。

exp_a24_analyze_error_envelope_spectrum
  背景：误差包络谱。
  看点：误差幅度是否被某个慢变化机制调制。

exp_a25_spectra
  背景：stage_03 的 15 种非理想频谱对照。
  看点：不同非理想性在频谱上的“指纹”。

exp_a31_fit_static_nonlin
  背景：静态非线性拟合。
  看点：用低阶多项式解释 HD2/HD3，但不要把所有动态误差硬塞进去。

exp_a32_inl_from_sine_sweep_length
  背景：本阶段 INL/DNL from sine。
  看点：记录长度影响 histogram 统计稳定性。

exp_a41_analyze_phase_plane
  背景：本阶段 phase-plane / lag plot。
  看点：sparkle、hysteresis、memory 在相平面上有不同形态。

exp_a42_analyze_error_phase_plane
  背景：error phase-plane。
  看点：先去掉基波后，小异常会比在原始相平面里更突出。
```

`nonideality_cases.py` 是这组 example 共享的非理想性 case 定义，不单独作为 runnable example。

### `05_debug_digital/`：digital code 与 SAR 校准

```text
exp_d01_cal_weight_sine_lite
  背景：stage_06 的最小 sine-weight calibration。
  看点：固定一个 fundamental basis 后，用最小二乘求 bit weights。

exp_d02_cal_weight_sine
  背景：stage_06 的完整 calibration。
  看点：dual basis、harmonic_order、rank patch、column conditioning。

exp_d03_redundancy_comparison
  背景：冗余结构 vs 严格二进制。
  看点：redundancy 给后续 bit 留 correction margin。

exp_d11_bit_activity
  背景：stage_05 的 bit matrix 可观测性。
  看点：每一列是否翻转，输入是否覆盖到足够 code range。

exp_d12_sweep_bit_enob
  背景：stage_05 的 ENOB sweep。
  看点：逐步加入 bit 后，动态性能是否上升、平台或恶化。

exp_d13_weight_scaling
  背景：stage_05/06 的 weight radix 与 column scaling。
  看点：权重结构是否像预期架构；scaling 主要是数值防御，不治相关性。

exp_d14_overflow_check
  背景：stage_05 的 suffix distribution / overflow。
  看点：剩余 bit 段是否经常贴边，correction margin 是否吃紧。

exp_d15_sar_unit_cap_mismatch_uncal_spectra
  背景：本阶段衔接实验，未校准 mismatch 基线。
  看点：unit-cap mismatch 会把 SFDR 拉低，给 stage_06 校准提供反例基准。

exp_d16_sar_unit_cap_mismatch_mc
  背景：Monte Carlo mismatch + calibration。
  看点：before/after calibration 的 ENOB 分布，不只看单颗样本。

exp_d17_sar_msb_error_binary_vs_repeat_calibration
  背景：MSB error、binary vs redundant SAR。
  看点：冗余结构能否让校准吸收 MSB 权重错误。

exp_d18_sar_redundant_mismatch_training_length_sweep
  背景：training length 与校准稳定性。
  看点：样本数不足时，权重估计和动态性能会不稳定。
```

### `06_use_toolsets/`：dashboard workflow

```text
exp_t01_aout_dashboard_single
  背景：analog output 单文件报告。
  看点：把常用图和指标打包成一个 dashboard。

exp_t02_aout_dashboard_batch
  背景：analog output 批量报告。
  看点：工程上如何批处理多条 capture。

exp_t03_dout_dashboard_single
  背景：digital output 单文件报告。
  看点：面向 code stream 的 dashboard。

exp_t04_dout_dashboard_batch
  背景：digital output 批量报告。
  看点：批量 dout 数据如何统一生成诊断输出。
```

这组更像 workflow，不是新理论。whole-workflow 和前面 stages 已经展示过核心图形，
这里重点是“如何批量化”。

### `07_conversions/`：单位、指标、datasheet 语言

```text
exp_c01_aliasing_nyquist_zones
  背景：stage_02 的 aliasing / Nyquist zones。
  看点：输入频率超过 Nyquist 后如何折叠。

exp_c02_unit_conversions
  背景：dB、dBFS、LSB、dBm 等单位。
  看点：相对满量程和绝对功率单位不要混用。

exp_c03_calculate_fom
  背景：stage_07 的 Walden / Schreier FoM。
  看点：FoM 是跨 ADC 比较指标，不是单次动态测试结果。

exp_c04_amplitudes_to_snr
  背景：幅度、噪声、SNR 换算。
  看点：幅度标尺变化会直接改变 dB 解释。

exp_c05_convert_nsd_snr
  背景：stage_02/09 的 NSD 与带宽。
  看点：NSD 是每 Hz 噪声密度，SNR 是带内总功率比。
```

### `08_time_interleave/`：TI-ADC mismatch

```text
exp_ti01_compare_skew_methods
  背景：stage_08 foreground TI 校准。
  看点：FFT fractional delay 和 Farrow fractional delay 的差别。

exp_ti02_autocorr_background_skew_calibration
  背景：stage_08 background skew calibration。
  看点：盲搜索 skew trim code，主要校准 timing，不等价于 offset/gain 全校准。
```

`variable_delay_line.py` 是 `exp_ti02` 用到的 VDL 支撑模型，不单独算 runnable example。

### `09_downsample/`：低速 debug output

```text
exp_d00_subsample_aliasing
  背景：stage_09 的无滤波 subsample debug output。
  看点：spur 高度基本守恒，但频率按新采样率折叠；N 选不好会发生 alias 污染。
```

---

## 阶段检查问题

1. polar 频谱的径向和角度分别代表谐波的什么？为什么笛卡尔频谱看不到记忆效应？
2. 相平面的 auto-lag 为什么选 ~90° 相移的 k？k=0 或 k=半周期会怎样？
3. 相平面的 outlier 检测为什么用 MAD 而不是 std？
4. exp_a42（误差相平面）为什么比 exp_a41 灵敏 1000 倍？它多做了一步什么？
5. 谐波分解比纯 FFT 频谱多给出什么？为什么相位要"相对基波"旋转？
6. exp_d15 的 sigma=1% 那行，SFDR 从 123 掉到 98，这 25 dB 是什么造成的？stage_06 怎么修它？
7. INL/DNL 和 SNDR/SFDR 分别在回答什么问题？为什么不能互相替代？
8. power averaging、coherent averaging、polar coherent averaging 分别保留和丢失什么？

---

## 收尾：全课程 example 视角

Stage 11 不是说前面没讲的 example 才重要，而是把完整例库变成一张地图：

```text
前面 stages:
  用代表性 examples 学知识主线。

Stage 11:
  反过来按 examples 检查整个工具箱。

完整 examples 目录:
  59 个 runnable examples。

helper 文件:
  nonideality_cases.py、variable_delay_line.py 等，不按 runnable example 统计。
```

真正的完成标准是：

```text
能跑完；
能知道每张图在诊断什么；
能把每个 example 放回对应 ADC 概念；
能区分教学 demo、诊断工具、工程 workflow 和完整设计签核。
```

最后保留两个明确边界，避免把学习库说过头：

```text
1. TI-ADC bandwidth mismatch / multi-tone swept diagnosis 尚未系统覆盖。
   当前 Stage 08 聚焦 offset/gain/skew。
2. Stage 10 是 OSR/NTF/noise shaping 的行为级学习入口，
   不是完整 Sigma-Delta loop 稳定性设计教程。
```

整个 staged course 的主线到这里完整闭合：

```text
ADC 是什么 -> 怎么测它 -> 怎么建它的模型 -> 怎么校准它 -> 怎么验证校准
          -> 多通道(TI)怎么处理 -> 调试口/过采样进阶 -> 可视化与诊断工具箱补全
```
