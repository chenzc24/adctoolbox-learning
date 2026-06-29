# Stage 10：Oversampling 与 Noise Shaping（过采样和噪声整形）

## 本阶段如何承接 Stage 09

Stage 09 讲的是：

```text
无滤波 subsample debug output
```

它故意不滤波，因为目标是把 raw ADC 行为送出来离线调试。

Stage 10 讲的是另一个方向：

```text
oversampling + noise shaping + signal-band analysis
```

这里的目标不是保留所有带外 spur，而是把信号带宽限定在 `0..fB`，然后利用更高采样率和
NTF 把带内噪声压低。它对应的是 Sigma-Delta ADC 和 oversampled data converter 的核心直觉。

## 本阶段目标

学完本阶段，你应该能解释：

- OSR 为什么定义为 `fs/(2*fB)`。
- 只靠 oversampling 时，带内白噪声为什么改善 `10*log10(OSR)`。
- NTF 是什么，为什么低频 notch 能压低带内量化噪声。
- 一阶、二阶、高阶 noise shaping 在频谱斜率上有什么差异。
- 为什么高阶不等于无条件更好。
- `ntf_analyzer` 返回的 dB 值代表什么。
- `apply_noise_shaping` 的教学模型和真实 Sigma-Delta loop 有什么边界。
- 怎么用 `10_oversampling` examples 连接理论、频谱图和 API。

## 初学者先抓住的主线

Nyquist ADC 通常把信号带宽铺满到接近 `fs/2`。Oversampling ADC 则让：

```text
fs >> 2*fB
```

其中 `fB` 是你真正关心的信号带宽。OSR 定义为：

```text
OSR = fs / (2*fB)
```

如果量化噪声近似白噪声，总噪声铺在 `0..fs/2`。你只关心 `0..fB`，所以带内只吃到
总噪声的 `1/OSR`：

```text
P_noise,in-band = P_noise,total / OSR
SNR gain = 10*log10(OSR)
```

这就是“只靠过采样”的收益：每 OSR 翻倍约 3 dB，等效 0.5 bit。

Noise shaping 进一步改变噪声形状：

```text
低频带内噪声压低；
高频带外噪声抬高；
后续数字滤波/带宽限制把高频噪声丢掉。
```

所以 noise shaping 不是让噪声凭空消失，而是：

```text
把量化噪声从有用信号带搬到不用的带外区域。
```

这也是 Stage 10 和 Stage 09 的根本差异：

```text
Stage 09:
  debug output 故意保留 raw 带外 artifact，即使它们会 alias。

Stage 10:
  oversampled converter 明确知道 signal band，然后用滤波/decimation 丢掉带外噪声。
```

## NTF 的直觉

Sigma-Delta 系统常把输出写成：

```text
Y(z) = STF(z) * X(z) + NTF(z) * E(z)
```

其中：

```text
STF: signal transfer function，希望在信号带内接近 1
NTF: noise transfer function，希望在信号带内很小
E:   量化误差
```

理想目标是：

```text
STF ≈ 1 in signal band
NTF ≈ 0 in signal band
```

也就是：

```text
输入信号尽量原样通过；
量化误差尽量不要进入信号带；
被推到带外的量化噪声再由数字低通 / decimation filter 去掉。
```

最常见的教学 NTF 是：

```text
1st order: NTF(z) = 1 - z^-1
2nd order: NTF(z) = (1 - z^-1)^2
```

它们在 DC 处有零点：

```text
z = 1 -> low-frequency noise notch
```

所以低频噪声被压下，高频噪声被推高。

### NTF 作用到误差上，就是对误差做滤波

当我们写：

```text
Y_noise(z) = NTF(z) * E(z)
```

这里的乘法是在 z 域 / 频域里做乘法。对应到时域，就是用 `NTF` 的 impulse response
去卷积量化误差序列：

```text
y_noise[n] = h_ntf[n] * e[n]
```

所以 `NTF(z)=1-z^-1` 对应的 FIR impulse response 是：

```text
h_ntf[n] = δ[n] - δ[n-1]
```

回到时域：

```text
e_shaped[n] = e[n] - e[n-1]
```

二阶同理：

```text
NTF(z) = (1 - z^-1)^2
       = 1 - 2z^-1 + z^-2
```

对应：

```text
h_ntf[n] = δ[n] - 2δ[n-1] + δ[n-2]
e_shaped[n] = e[n] - 2e[n-1] + e[n-2]
```

这就是代码里用 `[1, -1]`、`[1, -2, 1]` 这些系数滤波量化误差的数学来源。

### NTF 对量化误差是高通

为什么 `1 - z^-1` 能压低低频？它在时域上是一个差分器：

```text
e_shaped[n] = e[n] - e[n-1]
```

如果噪声成分变化很慢，也就是低频成分：

```text
e[n] ≈ e[n-1]
```

那么：

```text
e[n] - e[n-1] ≈ 0
```

所以低频被抵消。

从频域看，令：

```text
z = exp(jω)
```

则：

```text
NTF(exp(jω)) = 1 - exp(-jω)
|NTF(exp(jω))| = 2 * |sin(ω/2)|
```

当 `ω` 很小时：

```text
sin(ω/2) ≈ ω/2
|NTF| ≈ ω
```

所以 DC 附近有一个零点：

```text
ω = 0 -> |NTF| = 0
```

而在 Nyquist 附近：

```text
ω = π -> |1 - exp(-jπ)| = 2
```

所以 `NTF(z)=1-z^-1` 对量化误差来说就是一个高通滤波器：

```text
低频 / DC 量化噪声被压低；
高频量化噪声被抬高。
```

要注意：高通的是**量化误差**，不是输入信号。输入信号走的是 `STF`，理想情况下
在 signal band 内接近 1；量化误差走的是 `NTF`，理想情况下在 signal band 内接近 0。

二阶 NTF 相当于做两次差分：

```text
NTF(z) = (1 - z^-1)^2
e_shaped[n] = e[n] - 2e[n-1] + e[n-2]
```

低频近似：

```text
|NTF| ≈ ω^2
```

所以二阶比一阶在低频压噪更强。

## 斜率和阶数

对于 `NTF(z) = (1 - z^-1)^L`：

```text
低频近似: |NTF| ≈ ω^L
```

换成 dB：

```text
20*log10(|NTF|)
≈ 20*L*log10(ω)
```

因此每十倍频率变化：

```text
L = 1 -> 约 20 dB/decade
L = 2 -> 约 40 dB/decade
L = 3 -> 约 60 dB/decade
```

阶数越高，低频 notch 越陡，带内量化噪声越低。但真实电路中还要考虑：

```text
loop stability
quantizer overload
opamp/integrator finite gain
coefficient mismatch
multi-bit feedback DAC mismatch
idle tone
digital filter delay and area
```

所以 Stage 10 的结论不是“阶数越高越好”，而是：

```text
NTF 越激进，带内噪声可以越低，但稳定性和实现代价更高。
```

## Sigma-Delta ADC 的拓展理解

是的，NTF / noise shaping 正是 Sigma-Delta ADC 的核心知识。为了避免把 Stage 10
的教学模型误解成完整电路，这里把 Sigma-Delta ADC 的定义、结构、工作原理和最终目标
放在一起说明。

### 定义：过采样反馈型 ADC

Sigma-Delta ADC，也常写作 Delta-Sigma ADC，是一种**过采样反馈型 ADC**。它不追求
在一次 Nyquist-rate 转换里直接得到很高精度，而是用：

```text
高采样率 oversampling
低到中等分辨率 quantizer
闭环反馈 loop feedback
noise shaping
digital low-pass / decimation filter
```

共同换取较高的信号带内精度。

它的核心目标可以概括为：

```text
把输入信号在目标带宽内尽量保真；
把量化噪声从目标带宽内推到带外；
再用数字滤波和降采样把带外噪声丢掉。
```

所以 Sigma-Delta ADC 特别适合音频、传感器、仪表、低到中等带宽高分辨率场景。它牺牲的是
较高的内部采样率、环路稳定性设计难度、数字滤波延迟和带宽。

### 基本结构

真实 Sigma-Delta ADC 不是“先凭空生成白量化误差，再拿 FIR 滤一下”。更典型的结构是：

```text
analog input x(t)
  -> summing node: input - DAC feedback
  -> loop filter / integrator
  -> coarse quantizer
  -> digital output bitstream / code stream
  -> feedback DAC
  -> 回到 summing node

digital output bitstream / code stream
  -> digital low-pass filter
  -> decimation
  -> lower-rate high-resolution output
```

几个模块的角色是：

```text
summing node:
  比较输入和反馈 DAC 重建值，形成误差信号。

loop filter / integrator:
  放大并累积低频误差，让环路强烈修正带内误差。

quantizer:
  把 loop filter 输出量化成数字码。它可以是 1-bit，也可以是 multi-bit。

feedback DAC:
  把数字输出转换回模拟反馈量，闭合环路。

digital low-pass / decimation filter:
  去掉被推到带外的噪声，并把高采样率码流降到目标输出采样率。
```

### 基本工作原理

先分清两层：

```text
Stage 10 讲的 NTF / noise shaping:
  Sigma-Delta ADC 的线性化频域解释。

真实 Sigma-Delta ADC:
  通过 oversampling、loop filter / integrator、quantizer、feedback DAC
  组成闭环系统，在电路运行中实现 noise shaping。
```

过采样本身先带来一个基本好处：同样的量化噪声被摊到更宽的 Nyquist 频带里。如果信号只占
其中一小段带宽，那么只看信号带内时，带内噪声会降低。

```text
oversampling:
  spread quantization noise over a wider frequency range

band-limited analysis / filtering:
  keep only the signal band
```

Sigma-Delta 的关键进一步在于闭环噪声整形。直觉上，环路会不断观察输入和反馈之间的误差。
低频误差会被积分器强烈累积并反馈修正，所以低频量化噪声被压下；高频误差不容易被环路
完全修正，于是噪声被推到高频。

线性化后，工程上常把这个闭环写成：

```text
Y(z) = STF(z) * X(z) + NTF(z) * E(z)
```

这里的“信号”和“噪声”分开，不是说真实电路里有两条物理通路。真实输出只有一条，
信号和噪声在同一个节点上混在一起。分开写是线性化模型下的数学等效：

```text
quantizer output ≈ quantizer input + quantization error
Q(v) ≈ v + e
```

把量化器替换成一个“理想增益 1 + 加性误差源”后，闭环就变成一个线性系统加一个
从量化器位置注入的误差源。线性系统满足叠加原理，所以可以分别看：

```text
X 到 Y 的传递函数 -> STF
E 到 Y 的传递函数 -> NTF
```

最后再相加：

```text
Y = STF * X + NTF * E
```

关键是：`X` 和 `E` 注入的位置不同，所以即使经过同一个闭环系统，到输出的传递函数也
不同。用一阶 Sigma-Delta 的线性模型可以直观看到这一点。假设 loop filter 是：

```text
H(z) = z^-1 / (1 - z^-1)
```

若线性化闭环满足：

```text
Y = H * (X - Y) + E
```

则：

```text
Y * (1 + H) = H * X + E
STF = H / (1 + H)
NTF = 1 / (1 + H)
```

代入这个积分器型 `H(z)`：

```text
STF(z) = z^-1
NTF(z) = 1 - z^-1
```

这说明：

```text
输入信号 X 到输出 Y:
  主要只是延迟一拍，基本保留。

量化误差 E 到输出 Y:
  经过 1 - z^-1，高通整形。
```

所以 STF/NTF 分开分析的本质是：

```text
不是物理分线；
而是两个不同注入源在同一个线性化反馈系统中的不同传递函数。
```

最后，数字低通 / decimation filter 会把带外高频噪声滤掉，并把高采样率输出降到系统真正
需要的输出采样率。这一步很关键：Sigma-Delta 不是只把噪声推到高频就结束，而是要依靠
后续数字滤波把这些带外噪声从最终输出里去掉。

### 最终达成的成果

理想情况下，Sigma-Delta ADC 最终换来的是：

```text
目标信号带内:
  更低的量化噪声；
  更高的 SNR / SNDR / ENOB；
  更高的有效分辨率。

带外:
  量化噪声被抬高；
  需要数字低通滤波和 decimation 去除。

系统层面:
  用较简单的模拟量化器和较高采样率，换取高分辨率低带宽输出；
  把一部分精度压力从模拟电路转移到反馈环路和数字滤波。
```

所以它不是“量化噪声消失了”，而是：

```text
noise shaping 把噪声重新分布；
digital filtering 把不需要的带外噪声丢掉；
最终在目标带宽内看到更干净的输出。
```

但真实 Sigma-Delta 还要处理：

```text
loop stability
integrator saturation
quantizer overload
excess loop delay
idle tone / limit cycle
multi-bit feedback DAC mismatch
out-of-band noise peaking
digital decimation filter design
```

所以 Stage 10 的 `NTF=(1-z^-1)^L` 是帮助理解 noise shaping 的教学入口，不是完整
Sigma-Delta ADC 设计签核。

## 本库对应代码

核心 API：

```python
from adctoolbox import analyze_spectrum, ntf_analyzer, sweep_performance_vs_osr
from adctoolbox.siggen import ADC_Signal_Generator
```

对应源码：

```text
python/src/adctoolbox/oversampling/ntf_analyzer.py
python/src/adctoolbox/siggen/nonidealities.py        # apply_noise_shaping
python/src/adctoolbox/spectrum/sweep_performance_vs_osr.py
```

官方示例（**注意：以下实验脚本尚未创建，API 已就绪**）：

```text
python/src/adctoolbox/examples/10_oversampling/README.md
python/src/adctoolbox/examples/10_oversampling/exp_o01_noise_shaping_spectrum.py
python/src/adctoolbox/examples/10_oversampling/exp_o02_ntf_band_analysis.py
python/src/adctoolbox/examples/10_oversampling/exp_o03_snr_vs_osr.py
```

截至本课程版本，`examples/10_oversampling/` 目录尚未生成。但核心 API
（`apply_noise_shaping`、`ntf_analyzer`、`sweep_performance_vs_osr`）已经实现并可调用。
可以用这些 API 直接写学习脚本，不依赖官方 example。

### `apply_noise_shaping` 对应哪一部分

源码位置：

```text
python/src/adctoolbox/siggen/nonidealities.py
```

`ADC_Signal_Generator.apply_noise_shaping(...)` 的流程是：

```text
1. 先调用 apply_quantization_noise 生成普通量化输出。
2. 计算白量化误差:
     quant_error_white = signal_quantized - signal
3. 根据 order 选择 (1 - z^-1)^order 的 FIR 系数。
4. 用这些系数滤波 quant_error_white。
5. 返回:
     signal + quant_error_shaped
```

代码中的系数直接来自二项式展开：

```text
order 1: [1, -1]
order 2: [1, -2, 1]
order 3: [1, -3, 3, -1]
order 4: [1, -4, 6, -4, 1]
order 5: [1, -5, 10, -10, 5, -1]
```

它对应的是：

```text
NTF(z) = (1 - z^-1)^order
```

因此这个函数演示的是：

```text
量化误差通过 NTF 后，频谱形状如何改变。
```

它不是完整 Sigma-Delta loop，因为它没有真实闭环状态、积分器 swing、反馈 DAC、
稳定性和 overload 行为。

## `ntf_analyzer` 返回什么

`ntf_analyzer(ntf, flow, fhigh)` 做的是：

```text
在 normalized frequency band [flow, fhigh] 内积分 |NTF(f)|^2
再和 NTF=1 的白噪声基准比较
```

返回值可以理解为：

```text
这个 NTF 在该信号带内带来多少 dB 的量化噪声抑制。
```

例如低通一阶 NTF，在 OSR=16 时：

```text
flow = 0
fhigh = 0.5 / 16
ntf_analyzer(1 - z^-1, flow, fhigh) ≈ 30 dB
```

它不是测某一条 waveform 的 SNDR，而是对 NTF 形状本身做频带积分。

另一个工程边界也要记住：当前 `ntf_analyzer.py` 源码顶部仍标注为尚未同时经过 MATLAB
和 Python testbench 双重验证。学习时可以用它理解 NTF 频带积分和 suppression 的量级；
写严肃报告时，不要把它单独当成完整 Sigma-Delta 设计签核工具。

## `sweep_performance_vs_osr` 对应哪一部分

源码位置：

```text
python/src/adctoolbox/spectrum/sweep_performance_vs_osr.py
```

这个函数不是改变 ADC 输出，也不是做 decimation filter。它是在同一条 waveform 上改变
“分析带宽”，看带内 residual power 如何随 OSR 变化。

核心流程是：

```text
1. 用 fit_sine_4param 拟合 fundamental。
2. err = data - fitted_signal。
3. 对 err 做 FFT，得到 error spectrum。
4. 对每个 OSR，把 in-band bin 数量缩小到 fs/(2*OSR)。
5. 积分这个带宽内的 error power。
6. 计算 SNDR / SFDR / ENOB vs OSR。
```

所以它回答的是：

```text
如果我的 signal band 只到 fs/(2*OSR)，
这条输出在该带宽内的动态指标是多少？
```

这和 Stage 09 的 debug subsampling 不同。Stage 09 改变实际输出采样序列；
`sweep_performance_vs_osr` 只是改变分析带宽。

## `apply_noise_shaping` 的边界

`ADC_Signal_Generator.apply_noise_shaping` 是教学用的行为模型：

```text
先生成量化误差；
再用 (1 - z^-1)^order 形状处理量化误差；
最后把 shaped error 加回 signal。
```

它适合学习：

```text
noise floor slope
order vs in-band SNR
OSR 带宽选择
```

但它不是完整 Sigma-Delta loop 仿真。它不完整建模：

```text
loop filter state evolution
STF/NTF closed-loop stability
quantizer overload recovery
idle tone / limit cycle
multi-bit feedback DAC mismatch
decimation filter implementation
```

所以报告时应说：

```text
这是 noise-shaped quantization 的行为级教学模型。
```

不要说：

```text
这是某个真实 Sigma-Delta modulator 的晶体管级或环路级仿真。
```

## 实验 1：Noise shaping 频谱斜率

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\10_oversampling\exp_o01_noise_shaping_spectrum.py
```

观察：

```text
Order 0: 普通量化，噪声较平
Order 1/2/3: 低频噪声逐渐被压低，高频噪声被推高
OSR band 内 SNR 随阶数提高
```

输出图：

```text
python/src/adctoolbox/examples/10_oversampling/output/exp_o01_noise_shaping_spectrum.png
```

## 实验 2：NTF band analysis

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\10_oversampling\exp_o02_ntf_band_analysis.py
```

观察：

```text
一阶低通 NTF 在低频有 notch
二阶低通 NTF notch 更深
bandpass NTF 只在目标中心频率附近压噪
同一个 NTF 换 signal band 后，suppression 可能完全不同
```

输出图：

```text
python/src/adctoolbox/examples/10_oversampling/output/exp_o02_ntf_band_analysis.png
```

## 实验 3：Performance vs OSR

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\10_oversampling\exp_o03_snr_vs_osr.py
```

观察：

```text
white quantization noise: OSR 提升主要给出约 10*log10(OSR) 的趋势
noise-shaped quantization: OSR 提升更快，因为带内噪声被 NTF 额外压低
sweep_performance_vs_osr: 类似 MATLAB perfosr 的学习入口
```

输出图：

```text
python/src/adctoolbox/examples/10_oversampling/output/exp_o03_snr_vs_osr.png
```

## 和 07/08/09 的边界

| 阶段 | 负责的问题 | 不重复讲什么 |
|---|---|---|
| Stage 07 | 校准结论如何验证，测试条件如何报告 | 不讲 NTF 数学细节 |
| Stage 08 | TI-ADC 通道间失配和校准 | 不讲 OSR 带内噪声积分 |
| Stage 09 | 无滤波 debug output 的 alias 和 N 选择 | 不讲 Sigma-Delta noise shaping |
| Stage 10 | oversampling、NTF、noise shaping | 不讲 raw debug port spur 保真 |

一个简单判断：

```text
如果你在保留 raw spur 给 debug，读 Stage 09。
如果你在缩小 signal band 来压低带内噪声，读 Stage 10。
```

## 容易混淆的点

- OSR 的带宽是信号带宽 `fB`，不是随便把 FFT 画窄。
- 只靠 oversampling 的白噪声收益是 `10*log10(OSR)`，不是任意大。
- noise shaping 降低带内噪声，同时抬高带外噪声。
- `ntf_analyzer` 分析 NTF 形状，不直接测某条 capture 的 SNDR。
- `apply_noise_shaping` 是教学模型，不是完整 Sigma-Delta 环路仿真。
- 高阶 NTF 可能带来更好带内 SNR，也可能带来稳定性和实现风险。
- Stage 09 的 subsample-only 和 Stage 10 的 oversampling/decimation 目的相反。

## 阶段检查问题

1. 为什么 OSR 定义为 `fs/(2*fB)`？
2. 只靠过采样时，白噪声带内 SNR 为什么改善 `10*log10(OSR)`？
3. `NTF(z)=1-z^-1` 为什么能压低低频量化噪声？
4. 一阶和二阶 noise shaping 的频谱斜率有什么区别？
5. 为什么高阶 NTF 不是无条件越高越好？
6. `ntf_analyzer` 的返回值和 `analyze_spectrum()["snr_dbc"]` 有什么区别？
7. `apply_noise_shaping` 没有建模哪些真实 Sigma-Delta 现象？
8. Stage 09 的下采样和 Stage 10 的带宽限制为什么不能混为一谈？

完成这些问题后，你就能把 “OSR/NTF/noise shaping” 和前面 SAR、TI、debug-port
三个主题分开，不会把所有频谱变化都归因到同一种下采样机制。
