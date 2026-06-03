# Stage 01：ADC 基础、采样、量化、LSB

## 本阶段如何承接 Stage 00

Stage 00 已经建立了本课程的共同语言：

```text
vin.shape     == (N,)
bits.shape    == (N, n_bits)
weights.shape == (n_bits,)
aout.shape    == (N,)
```

也就是说，你已经知道这些对象在代码里长什么样：

```text
vin  -> 一串输入采样点
bits -> 每个采样点对应的一组 bit decision
aout -> bits 乘 weights 后得到的一维重构波形
```

Stage 01 不再重点讲 array shape，也不提前展开 SAR 内部细节。它要回答的是更基础的问题：

```text
这些数组为什么会这样产生？
连续电压为什么会变成 code？
有限 bit 数为什么天然带来量化误差和理想 SNR 上限？
```

一句话承接：

```text
Stage 00 讲“数据在代码里是什么形状”；
Stage 01 讲“ADC 为什么会产生这些数据”。
```

## 本阶段目标

学完本阶段，你应该能解释：

- ADC 的输入、采样值、数字 code、重构输出分别是什么。
- sampling、quantization、code、LSB、full-scale 的含义。
- 为什么 `2^N` 个 code 只能表示有限精度。
- 为什么理想 N-bit ADC 的 SNR 约为 `6.02N + 1.76 dB`。
- 为什么本库常用 `quant_range = (0.0, 1.0)` 做归一化建模。
- 为什么 Stage 02 可以从 `aout` 继续做 FFT 和动态指标分析。

## 初学者先抓住的主线

ADC 最核心的事只有一句话：

```text
把连续电压，在离散时间点上，变成有限个数字 code。
```

拆成三步：

```text
连续电压      -> 采样 sampling      -> 一串时间样本 vin
时间样本 vin  -> 量化 quantization  -> 一串 code / bits
code / bits   -> 数字重构           -> 可分析的输出波形 aout
```

在 ADCToolbox 的 SAR 模型里，可以先这样记：

```text
vin   -> 采样后的输入电压
bits  -> ADC 内部比较后留下的 0/1 决策
aout  -> bits 乘数字权重后的重构输出
```

这里先不深究 SAR 每一位怎么比较。Stage 04 会专门讲 `sar_convert` 的 bit trial。
本阶段只需要确认：`vin`、`bits`、`aout` 不是同一个东西，它们处在 ADC 流程的不同位置。

## 一个 3-bit ADC 小例子

假设输入范围是：

```text
quant_range = (0.0, 1.0)
```

3-bit ADC 有：

```text
2^3 = 8 个 code
code = 0, 1, 2, ..., 7
LSB = (1.0 - 0.0) / 8 = 0.125
```

可以粗略理解为：

| 输入电压范围 | code |
|---|---|
| 0.000 到 0.125 | 0 |
| 0.125 到 0.250 | 1 |
| 0.250 到 0.375 | 2 |
| 0.375 到 0.500 | 3 |
| 0.500 到 0.625 | 4 |
| 0.625 到 0.750 | 5 |
| 0.750 到 0.875 | 6 |
| 0.875 到 1.000 | 7 |

注意两个点：

- `1.0` 是输入范围的上边界，不是第 8 个 code。
- 输入电压的微小变化不一定会改变 code，因为一个 code 覆盖一个 LSB 宽度的区间。

所以量化误差不是 bug，而是有限 bit 数天然带来的误差。

## 数学需要补什么

### 1. 采样

连续信号可以写成：

```text
x(t)
```

采样之后变成离散序列：

```text
x[n] = x(n / Fs)
```

其中：

- `Fs` 是采样率。
- `n` 是样本编号。
- `N` 是总样本数。

在代码里通常是：

```python
n = np.arange(N)
t = n / Fs
vin = DC + A * np.sin(2 * np.pi * Fin * t)
```

这一步得到的是 Stage 00 里的一维数组：

```text
vin.shape == (N,)
```

### 2. 量化

理想 ADC 把连续电压映射成有限 code。

如果输入范围是：

```text
[Vmin, Vmax]
```

bit 数为 `Nbit`，那么 code 数是：

```text
2^Nbit
```

LSB 大小是：

```text
LSB = (Vmax - Vmin) / 2^Nbit
```

理想量化 code 可以写成：

```text
code = floor((vin - Vmin) / LSB)
```

再限制到合法范围：

```text
0 <= code <= 2^Nbit - 1
```

如果输入超过 `[Vmin, Vmax]`，真实系统通常会出现 clipping 或 saturation。
这不是量化精度问题，而是输入范围问题。

### 3. code、bits 和 aout

对普通二进制 ADC，可以把一个整数 code 写成二进制 bits：

```text
code 5 -> bits [1, 0, 1]   # 3-bit 表示
```

在 SAR ADC 行为模型里，`bits` 更接近“每一位比较器决策”的记录：

```text
bits[n, :] -> 第 n 个采样点的一组 bit decision
```

然后重构输出可以理解成：

```text
aout[n] = bits[n, :] @ weights
```

这正好接回 Stage 00 的矩阵乘法：

```text
bits.shape    == (N, n_bits)
weights.shape == (n_bits,)
aout.shape    == (N,)
```

本阶段只需要知道这个关系成立；SAR 内部怎么一步步得到 `bits`，留到 Stage 04。

### 4. 量化误差

量化之后，一般会用某个重构值代表整个 LSB 区间。
理想量化误差可以写成：

```text
e = quantized_value - input_value
```

在经典近似中，量化误差被看作均匀分布：

```text
e ~ Uniform(-LSB/2, +LSB/2)
```

它的 RMS 是：

```text
e_rms = LSB / sqrt(12)
```

这就是理想 ADC 也有噪声底的原因：不是电路坏了，而是有限 bit 数不能表示无限精细的电压。

更严格一点说，量化误差本质上不是随机变量。给定输入 `input_value`
和量化器，`e` 是确定的。把它当成随机噪声，是为了推导和理解 ADC
的平均噪声功率。

设：

```text
Δ = LSB
e ~ Uniform(-Δ/2, +Δ/2)
```

均匀分布的概率密度是：

```text
p(e) = 1 / Δ,  -Δ/2 <= e <= +Δ/2
```

均值为：

```text
E[e] = ∫ e p(e) de
     = ∫_{-Δ/2}^{+Δ/2} e * (1/Δ) de
     = 0
```

方差为：

```text
Var(e) = E[(e - E[e])^2] = E[e^2]
```

因此：

```text
E[e^2]
= ∫_{-Δ/2}^{+Δ/2} e^2 * (1/Δ) de
= (1/Δ) * [e^3 / 3]_{-Δ/2}^{+Δ/2}
= Δ^2 / 12
```

所以零均值量化噪声的 RMS，也就是标准差，是：

```text
e_rms = sqrt(E[e^2]) = Δ / sqrt(12) = LSB / sqrt(12)
```

这套经典模型隐含了几个近似条件：

```text
输入跨过足够多的 code
输入不过载、不 clipping
输入在每个量化区间内的位置近似均匀
量化误差和输入近似不相关
```

如果这些条件不成立，量化误差可能不再像白噪声，而会和输入相关。
在频谱里，它可能表现为 harmonic、spur 或 noise modulation。

#### 当前库的量化模式

还要注意：经典公式默认讨论的是“中心化后的量化噪声”。当前库中有些量化实现更接近
`floor + lower-edge reconstruction`。

例如 `ADC_Signal_Generator.apply_quantization_noise(...)` 的核心逻辑是：

```text
code = floor((signal - Vmin) / LSB)
quantized_value = code * LSB + Vmin
```

也就是说，如果输入落在：

```text
[k*LSB, (k+1)*LSB)
```

输出会是：

```text
k*LSB
```

因此如果直接定义：

```text
e = quantized_value - input_value
```

且输入在每个量化区间内的位置近似均匀，则：

```text
e ~ Uniform(-LSB, 0)
E[e] = -LSB/2
```

这时直接二阶矩为：

```text
E[e^2] = ∫_{-Δ}^{0} e^2 * (1/Δ) de = Δ^2 / 3
```

直接 RMS 是：

```text
sqrt(E[e^2]) = Δ / sqrt(3)
```

但它包含了一个 DC bias。去掉均值后：

```text
e_noise = e - E[e]
```

仍然有：

```text
Var(e) = E[e^2] - E[e]^2
       = Δ^2/3 - (Δ/2)^2
       = Δ^2/12
```

所以影响频谱噪声底和 SNR 的随机分量仍然是：

```text
std(e) = LSB / sqrt(12)
```

这也是为什么频谱分析通常要排除 DC。DC bias 不应该算作随机噪声底。

SAR 模型也有类似 lower-edge 风格。例如 4-bit 理想权重是：

```text
[8, 4, 2, 1] / 16
```

输出 code 对应：

```text
0/16, 1/16, 2/16, ..., 15/16
```

而不是中心重构的：

```text
0.5/16, 1.5/16, ..., 15.5/16
```

因此对本库来说，学习时要区分：

```text
经典零均值噪声模型：
e_noise ~ Uniform(-LSB/2, +LSB/2)
E[e_noise] = 0
std = LSB / sqrt(12)

当前库 lower-edge reconstruction 的直接误差：
e = quantized_value - input
e ~ Uniform(-LSB, 0)
E[e] = -LSB/2
std = LSB / sqrt(12)
```

#### Dither 为什么有用

Dither 是在量化前故意加入小随机扰动：

```text
x_dithered[n] = x[n] + d[n]
q[n] = Q(x[n] + d[n])
```

它的目的不是降低噪声，而是降低量化误差和输入之间的相关性。

不加 dither 时：

```text
输入有规律
-> 落入量化区间的位置也可能有规律
-> 量化误差和输入相关
-> 频谱中出现 spur / harmonic
```

加入 dither 后：

```text
量化前加入随机扰动
-> 输入落入量化区间的位置被随机化
-> 量化误差更接近独立随机噪声
-> spur / harmonic 减少
-> noise floor 上升
```

常见 dither 类型：

```text
RPDF: d ~ Uniform(-LSB/2, +LSB/2)
TPDF: d = d1 + d2, d1/d2 ~ Uniform(-LSB/2, +LSB/2)
```

如果使用 subtractive dither，还会在量化后把 dither 减掉：

```text
y[n] = Q(x[n] + d[n]) - d[n]
```

这种方式在理论上可以更干净地让量化误差和输入解相关。

从物理上看，dither 对应的是“量化前存在一个随机扰动”。它可以是刻意加入的，
也可以来自系统本来就有的噪声：

```text
刻意加入：
模拟输入端注入小噪声
reference / DAC 中加入随机扰动
数字系统中加入伪随机序列

天然存在：
thermal noise
kT/C sampling noise
comparator noise
reference noise
前端输入等效噪声
```

所以 dither 不只是数学技巧，它可以有真实电路或系统对应。即使没有显式 dither
电路，系统中的天然噪声有时也会起到类似作用，让输入跨越量化边界时不那么确定。

工程上允许“故意加噪声”的原因，是确定性误差有时比随机噪声更糟：

```text
无 dither：
量化误差和输入相关
-> 可能形成确定性 spur / harmonic
-> SFDR / THD 变差

有 dither：
随机扰动打散相关性
-> spur / harmonic 降低
-> noise floor 上升
-> SNR 可能变差一点，但频谱更干净
```

也就是说，dither 是一个 tradeoff：

```text
牺牲一点 noise floor，换更少的确定性失真。
```

一句话总结：

```text
Dither 用可控随机噪声，换掉不可控的相关量化失真。
```

### 5. 理想 SNR 和 ENOB

设 full-scale 范围为：

```text
FS = Vmax - Vmin
```

则：

```text
LSB = FS / 2^N
```

满幅正弦的 peak amplitude 约为：

```text
A = FS / 2
```

所以信号 RMS 是：

```text
signal_rms = A / sqrt(2) = FS / (2 * sqrt(2))
```

这里的 `A / sqrt(2)` 来自正弦 RMS 的定义。对一个零均值正弦：

```text
x(t) = A sin(ωt)
```

RMS 定义为：

```text
x_rms = sqrt(mean(x(t)^2))
```

对一个周期 `T` 取平均：

```text
x_rms
= sqrt((1/T) * ∫_0^T A^2 sin^2(ωt) dt)
= A * sqrt((1/T) * ∫_0^T sin^2(ωt) dt)
```

而：

```text
mean(sin^2(ωt)) = 1/2
```

所以：

```text
x_rms = A * sqrt(1/2) = A / sqrt(2)
```

如果信号带 DC：

```text
x(t) = DC + A sin(ωt)
```

总 RMS 是：

```text
x_rms_total = sqrt(DC^2 + A^2/2)
```

但 ADC 动态指标中的 signal power 通常只看 AC fundamental，不把 DC 当作信号功率。
因此理想 SNR 推导里使用：

```text
signal_rms = A / sqrt(2)
```

量化噪声 RMS 是：

```text
noise_rms = LSB / sqrt(12) = FS / (2^N * sqrt(12))
```

两者相除并换成 dB，可得到常用结论：

```text
SNR_ideal = 6.02N + 1.76 dB
```

反过来，常用 SNDR 估算有效位数：

```text
ENOB = (SNDR - 1.76) / 6.02
```

这里用 `SNDR` 而不只用 `SNR`，是因为真实 ADC 的有效位数会同时受到随机噪声和失真的影响。

## 电路需要理解什么

### 1. SAR ADC 的基本电路框架

这一节先不重复前面已经建立的数据流，而是搭一个电路框架。对 SAR ADC 来说，
初学者先认识这些模块就够了：

| 模块 | 一句话作用 | 先记住的关键词 |
|---|---|---|
| sampling switch | 决定什么时候把输入接到采样节点 | on-resistance、charge injection |
| sampling capacitor | 存住采样瞬间的输入电压 | `Q = C * V`、`kT/C` noise |
| reference | 提供 ADC 判断电压大小的基准 | `Vref`、full-scale、settling |
| DAC / CDAC | 产生 SAR 每一位的试探电压 | bit weight、capacitor mismatch |
| comparator | 比较输入和试探电压，输出 0/1 判决 | noise、offset、metastability |
| SAR logic | 控制逐次逼近顺序并记录 bit | MSB-to-LSB、bit decision |

#### Sampling switch

采样开关负责在两个相位之间切换：

```text
采样相位：输入电压接到采样电容
转换相位：输入断开，电容保持采样值
```

SAR ADC 需要逐位比较，不是瞬间完成转换。因此在转换期间，输入最好保持不变。
采样开关和采样电容一起完成这个 sample-and-hold 动作。

常见非理想包括：

| 非理想 | 直觉影响 |
|---|---|
| on-resistance | 采样节点需要时间充到输入电压，可能 settling 不足 |
| charge injection | 开关断开瞬间注入电荷，造成采样误差 |
| clock feedthrough | 时钟边沿通过寄生电容耦合到采样节点 |
| thermal noise | 开关电阻带来采样热噪声 |

Stage 01 只需要知道这些误差会让“采到的电压”不再完全等于理想输入。
具体建模和指标影响后面再展开。

#### Sampling capacitor

采样电容负责存住采样瞬间的输入电压。最基本关系是：

```text
Q = C * V
```

电容越大，通常：

```text
优点：kT/C 噪声更小，匹配可能更好
缺点：面积更大，驱动更难，采样更慢，功耗更高
```

一个重要直觉是：

```text
采样热噪声功率约和 kT/C 有关
C 越大，采样噪声越小
```

所以采样电容不是任意选择的，它直接参与 SNR、速度、面积和功耗之间的权衡。

#### Reference

`reference` 是 ADC 的电压基准。常见符号包括：

```text
Vref
Vrefp / Vrefn
Vcm
```

它决定：

```text
ADC 的 full-scale range
CDAC 每次 trial voltage 的大小
比较器每一步判决所依赖的电压基准
```

在本学习路径中，常见归一化写法是：

```text
quant_range = (0.0, 1.0)
```

这可以先理解成把真实 `Vref` 归一化成 `1.0`。真实电路中可能是：

```text
single-ended: 0 到 Vref
differential: -Vref 到 +Vref，或围绕 Vcm 摆动
```

reference 不稳时，表现可能是：

```text
gain error
noise increase
spur / distortion
```

因此 reference 不是一个“背景常数”那么简单；它会影响量化范围、CDAC 切换和最终动态指标。

#### DAC 和 CDAC

DAC 全称是：

```text
Digital-to-Analog Converter
```

CDAC 全称是：

```text
Capacitive Digital-to-Analog Converter
```

也常说成：

```text
Capacitor DAC
```

在 SAR ADC 中，CDAC 是核心模拟模块。它用一组加权电容产生逐次逼近时的
trial voltage，让 comparator 判断当前 bit 应该保留为 1 还是清成 0。

理想二进制 CDAC 可以先这样理解：

```text
4-bit capacitor array: [8C, 4C, 2C, 1C]
normalized weights:   [1/2, 1/4, 1/8, 1/16]
```

CDAC 的作用不是输出最终分析波形，而是在转换过程中产生试探电压。常见非理想包括：

| 非理想 | 直觉影响 |
|---|---|
| capacitor mismatch | bit weight 不准，产生非线性和 spur |
| parasitic capacitance | 实际权重偏离理想 |
| reference settling | CDAC 切换后电压未稳定就比较 |
| switch error | CDAC 切换过程引入误差 |

这些内容在 Stage 04 的 SAR 建模和 Stage 06 的位权重校准中会变得非常重要。

#### Comparator

Comparator 的作用是回答一个二值问题：

```text
输入电压是否大于等于 CDAC 试探电压？
```

如果是：

```text
bit = 1
```

否则：

```text
bit = 0
```

它不是最终输出波形，也不是普通意义上的放大器；在 SAR ADC 中，它主要是
bit decision 的判决器。

常见非理想包括：

| 非理想 | 直觉影响 |
|---|---|
| input-referred noise | 输入和试探电压接近时，判决会抖动 |
| offset | 判决门槛整体偏移 |
| metastability | 比较时间不够时，输出可能不可靠 |
| kickback noise | 比较器反向扰动输入或 CDAC 节点 |

Stage 01 只需要知道 comparator 是“判 0/1 的器件”。后面再看
comparator noise 如何影响 `bits`。

#### SAR logic

SAR logic 是数字控制逻辑。它负责：

```text
控制 CDAC 从 MSB 到 LSB 逐位试探
读取 comparator 的 0/1 判决
决定当前 bit 保留 1 还是清成 0
记录最终 digital output bits
```

先记住这三个角色的分工：

```text
CDAC       -> 产生试探电压
comparator -> 判断大小
SAR logic  -> 安排试探顺序并记录 bits
```

Stage 01 的目标不是深入每个非理想的数学模型，而是建立下面这个框架：

```text
ADC 性能问题通常来自：
采样是否准、
电容权重是否准、
reference 是否稳、
comparator 判决是否准、
数字重构权重是否匹配。
```

### 2. Full-scale range

本库经常使用：

```text
quant_range = (0.0, 1.0)
```

可以理解为归一化单端 ADC：

```text
0.0 -> 输入下边界
1.0 -> 输入上边界
```

它不一定表示真实电路就是 `0 V` 到 `1 V`，而是先把 full-scale 归一化，
方便学习和比较。等理解稳定后，再换成真实单位：

```text
quant_range = (0.0, Vref)
quant_range = (-Vref, +Vref)
```

初学时要一直问自己：

```text
这个数是归一化量，还是带物理单位的电压？
```

### 3. ADC 噪声和误差来源

最基本的噪声和误差：

| 来源 | 电路含义 | 常见表现 |
|---|---|---|
| 量化误差 | 有限 bit 数 | 理想噪声底 |
| 热噪声 | 电阻、开关、电容采样噪声 | SNR 降低 |
| comparator noise | 比较器输入等效噪声 | code decision 抖动 |
| reference noise | 参考电压不稳 | 增益误差、噪声增加 |
| offset | 比较器或前端偏置 | code 偏移 |
| 非线性 | 开关、参考、DAC/CDAC 非理想 | harmonic、spur、SFDR 下降 |

Stage 01 只建立分类直觉。Stage 02 会用 FFT 指标区分噪声、谐波和 spur；
Stage 03 以后会继续看 residual、bit matrix 和校准。

## 本库对应代码

基础信号生成：

```text
python/src/adctoolbox/siggen/nonidealities.py
```

SAR 行为模型：

```text
python/src/adctoolbox/models/sar.py
```

基础单位和指标：

```text
python/src/adctoolbox/fundamentals/units.py
python/src/adctoolbox/fundamentals/snr_nsd.py
python/src/adctoolbox/fundamentals/metrics.py
```

官方示例：

```text
python/src/adctoolbox/examples/01_basic/
python/src/adctoolbox/examples/03_generate_signals/
```

本地学习脚本：

```text
learning/adctoolbox-learning/demos/whole_workflow_demo.py
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

## 对应 API

```python
from adctoolbox.siggen import ADC_Signal_Generator
from adctoolbox.models import sar_ideal_weights, sar_convert, sar_reconstruct
from adctoolbox import snr_to_enob, enob_to_snr
```

## 实验 1：手算一个 3-bit 量化器

先不用任何库，只做手算：

```text
quant_range = (0.0, 1.0)
Nbit = 3
LSB = 0.125
```

判断下面输入大约落在哪个 code：

| vin | code |
|---|---|
| 0.03 | ? |
| 0.20 | ? |
| 0.51 | ? |
| 0.88 | ? |
| 1.05 | ? |

重点不是算得快，而是说清楚：

- 为什么 `1.05` 已经超出 full-scale。
- 为什么 `0.20` 和 `0.24` 可能得到同一个 code。
- 为什么 code 是离散的，vin 是连续的。

## 实验 2：运行完整 workflow，看 vin 到 aout

运行：

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

看输出：

```text
E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\01_spectrum_clean_vs_nonideal.png
```

观察：

- clean sine 是理想输入/参考。
- generated ADC output 已经包含量化、噪声或失真。
- Stage 02 会继续解释这张频谱里的 SNR、SNDR、SFDR、THD、ENOB。

## 实验 3：修改 bit 数，观察理想上限

打开：

```text
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

找到：

```python
num_bits = 8
```

尝试改成：

```python
num_bits = 12
num_bits = 16
```

运行：

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\sar_adc_model_study.py
```

观察：

- 理想情况下 bit 数越高，量化误差越小。
- 如果其他噪声或失真已经主导，ENOB 不一定随 nominal bit 数无限提高。

如果控制台里出现 SAR bit-trial trace，本阶段只需要知道它是在展示
`vin -> bits` 的过程；具体每一位怎么比较，留到 Stage 04。

## 本阶段代码阅读

建议只读和本阶段概念直接相关的部分：

```text
python/src/adctoolbox/fundamentals/snr_nsd.py
python/src/adctoolbox/fundamentals/metrics.py
python/src/adctoolbox/models/sar.py
python/src/adctoolbox/siggen/nonidealities.py
```

阅读重点：

- `snr_to_enob` 和 `enob_to_snr` 只是公式转换，不是重新测量 ADC。
- `sar_convert` 的输入是 `vin`，输出是 `bits`。
- `sar_reconstruct` 把 `bits` 和 `weights` 变回 `aout`。
- `ADC_Signal_Generator` 负责生成输入信号和部分非理想效果。

读完后，能画出这条链就够了：

```text
vin -> quantization / SAR decision -> bits -> sar_reconstruct -> aout
```

## 容易混淆的点

- `Vmax` 是 full-scale 上边界，不是额外多出来的 code。
- `2^N` 是 code 数量，最大 code 是 `2^N - 1`。
- LSB 是一个电压间隔，不是最低 bit 本身。
- 理想 ADC 也有量化噪声。
- ENOB 是性能换算结果，不一定等于 nominal bit 数。
- `aout` 是后续 FFT 分析的 waveform；`bits` 是更底层的数字决策记录。

## 进入 Stage 02 前要带走什么

Stage 02 会从 `aout` 出发做频谱分析。进入下一阶段前，你只需要带走这条链：

```text
有限 bit 数
-> 量化误差
-> 理想噪声底
-> SNR_ideal = 6.02N + 1.76 dB
-> 真实 ADC 还会叠加噪声和失真
-> 需要 FFT 指标把它们分开看
```

这就是 Stage 01 到 Stage 02 的桥。

## 阶段检查问题

如果你能回答这些问题，就可以进入 Stage 02：

1. `LSB = full_scale / 2^N` 里的 full_scale 是什么？
2. 为什么最大 code 是 `2^N - 1`，不是 `2^N`？
3. 为什么 ideal ADC 也有量化噪声？
4. 为什么 ENOB 不一定等于 ADC nominal bit 数？
5. `vin`、`bits`、`aout` 分别是什么？
6. 为什么本库常用 `0.0 ~ 1.0` 的归一化输入？
7. Stage 02 为什么要从 `aout` 继续做 FFT？
