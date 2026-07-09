# MATLAB / Python 版本不一致记录

本文记录当前学习过程中发现的 MATLAB 版与 Python 版 ADCToolbox 的不一致点。它不是简单的 bug list，而是把每个差异分成：

```text
代码位置；
MATLAB 做法；
Python 做法；
原理差异；
实测现象；
建议处理方式。
```

这里的判断基于当前工作区代码和已运行的 parity 实验。本文最初是后续对齐、回归测试、PR 设计时的索引；
截至 2026-07-09，它也作为一次 MATLAB/Python alignment close-out 归档。

## 2026-07-09 最终状态

```text
Open PRs:    none
Open issues: none
```

本文记录的 notable MATLAB/Python 数值、contract、compare fixture 差异已在 upstream 中闭环：

```text
Spectrum / plotspec:          #76
Calibration scale/frequency:  #79, #80, #84, #85, #86, #87
Overflow fixture:             #88
ENOB sweep:                   #89, #97
Error envelope spectrum:      #90
Sine fit compare fixture:     #91
NTF grid:                     #92
plotphase LMS fixture:        #93
errsin compatibility:         #94
CDAC cap-to-weight order:     #95
```

后文各条保留了当时发现问题时的描述；若某段仍使用“当前差异 / 建议处理”措辞，应按本最终状态理解为历史记录。
剩余未强制一比一的部分主要是 workflow / UI 组织，例如 `adcpanel` 与 Python dashboards，不再视为核心 parity bug。

---

## 0. 总体结论

当前 Python 版不是 MATLAB 版的逐行翻译，而是做了不少重新组织：

```text
有些地方是核心算法一致，只是 API / 输入顺序不同；
有些地方是测试配置不同，导致看似不一致；
有些地方是 Python 版主动改了语义；
有些地方是 MATLAB 与 Python 都合理，但默认策略不同；
也有少数地方应当视为真实对齐问题。
```

最终结论是：

```text
1. sinfit / ifilter / tomdec / inlsin / errac / errspec / noiseshape 等核心计算基本对齐。
2. wcalsin 的求解、频率、harmonic residual、scale/radix contract 已通过显式 policy / metadata 对齐。
3. bitsweep、errsin、errevspec、plotphase 等已通过默认语义修正、compat wrapper 或 compare fixture 对齐。
4. cdacwgt / convert_cap_to_weight 已通过显式 input_order / output_order 处理顺序 contract。
5. findbin 的候选 bin policy 属于 API/默认策略差异；当前未作为 active parity blocker 跟踪。
6. adcpanel/dashboard 是 workflow/UI 组织差异，不作为核心算法对齐缺陷。
```

---

## 1. `findbin` / `find_coherent_frequency`：coherent bin 选择规则不同

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/findbin.m:1
  E:/ADCToolbox/matlab/src/findbin.m:92
  E:/ADCToolbox/matlab/src/findbin.m:101

Python:
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/frequency.py:12
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/frequency.py:65
```

### MATLAB 做法

MATLAB `findbin` 的核心约束是：

```text
gcd(bin, n) == 1
```

也就是保证输入周期和采样长度互质，从而得到 coherent sampling。它会先检查 target bin 附近的 upper candidate，再检查 lower candidate。

### Python 做法

Python `find_coherent_frequency` 默认多了一个约束：

```python
force_odd=True
```

因此它不仅要求 coherent，还倾向于选择 odd bin。并且在上下候选距离相近时，Python 的候选排序可能和 MATLAB 不同。

### 原理差异

coherent sampling 的基本要求是：

```text
Fin / Fs = k / N
gcd(k, N) = 1
```

其中 `k` 是 FFT bin，`N` 是采样点数。`k` 是否必须为奇数不是数学上的必要条件，而是某些 ADC 动态测试习惯中常用的额外约束。odd bin 可以避免部分镜像、谐波、周期对称性带来的特殊退化，但它不是 MATLAB `findbin` 的原始规则。

### 实测现象

已复核的典型例子：

```text
Fs = 10000, target = 2500, N = 1024
MATLAB-like: bin = 257
Python:      bin = 255

N = 999
MATLAB-like:          bin = 250
Python force_odd=True bin = 251
Python force_odd=False bin = 250
```

### 影响

这个差异会影响所有依赖自动 coherent frequency 的例子。频点略有变化后，spur 位置、fit 结果、频谱标注都可能产生小差异。

### 建议

应在文档中明确：

```text
MATLAB findbin: coherent first
Python find_coherent_frequency: coherent + optional odd-bin policy
```

如果目标是 parity test，Python 应显式设置 `force_odd=False`，并匹配 MATLAB 的上下候选优先级。

---

## 2. `wcalsin` / `calibrate_weight_sine`：求解核心一致，自动频率估计不一致

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/wcalsin.m:1
  E:/ADCToolbox/matlab/src/wcalsin.m:421
  E:/ADCToolbox/matlab/src/wcalsin.m:426

Python:
  E:/ADCToolbox/python/src/adctoolbox/calibration/calibrate_weight_sine.py:28
  E:/ADCToolbox/python/src/adctoolbox/calibration/calibrate_weight_sine.py:124
  E:/ADCToolbox/python/src/adctoolbox/calibration/_estimate_frequencies.py:16
  E:/ADCToolbox/python/src/adctoolbox/calibration/_estimate_frequencies.py:53
  E:/ADCToolbox/python/src/adctoolbox/calibration/_estimate_frequencies.py:63
  E:/ADCToolbox/python/src/adctoolbox/calibration/_estimate_frequencies.py:66
  E:/ADCToolbox/python/src/adctoolbox/calibration/_estimate_frequencies.py:69
  E:/ADCToolbox/python/src/adctoolbox/calibration/_estimate_frequencies.py:90
```

### MATLAB 做法

MATLAB `wcalsin` 会从若干 bit 子集重构信号中估计频率，最后取多个估计值的 median：

```matlab
freq = median(freq)
```

### Python 做法

Python `_estimate_frequencies` 按 bit toggles 选择两组 bit：

```text
toggle 少的一组；
toggle 多的一组；
```

分别构造候选信号，跑 spectrum / frequency estimate，再选择 winner。

### 原理差异

bit-weight sine calibration 的核心是：

```text
B @ w + harmonic/offset basis ≈ sine
```

如果频率已知，MATLAB 与 Python 的线性最小二乘核心可以高度一致。真正的差异出现在：

```text
频率未知时，先用什么 surrogate signal 估计频率。
```

频率估计只要偏一点，后续正弦基函数就会偏一点，最终权重和 ENOB 都可能出现可见差异。

### 实测现象

已验证：

```text
Python auto freq  = 0.2999298926993089
MATLAB freqCal    = 0.29992675804455
差异约            = 3.13e-6

Python auto weights vs MATLAB:
  max diff ≈ 0.001762
  RMS diff ≈ 0.000681

如果 Python 直接使用 MATLAB freq:
  force_search=False -> weight max diff ≈ 1.04e-9
  force_search=True  -> weight max diff ≈ 1.07e-11
```

这说明：

```text
最小二乘求解核心基本对齐；
不一致主要来自 auto frequency estimation。
```

### 影响

这不是“校准公式不一致”，而是“默认自动估频策略不一致”。在高精度 weight calibration 中，这个差异会放大到 ENOB / SFDR 结果上。

### 建议

后续可增加 parity mode：

```text
frequency_policy="matlab"
frequency_policy="python"
```

或者在 compare tests 中固定 `freq`，把“求解器对齐”和“自动估频策略对齐”拆开验证。

---

## 3. `bitsweep` / `analyze_enob_sweep`：语义不同，不是同一个实验

处理状态：`RESOLVED / #89 + #97`

最终结论：

```text
`prefix_of_full_calibration` 是 canonical/default ENOB sweep：
先对 full ADC 校准一次，再评估 full-weight prefix。

`recalibrate_each_subset` 保留为 diagnostic：
每个 n-bit prefix 作为独立 ADC 重新校准。

#97 修正了 #89 对“当前 MATLAB 行为”的过度跟随：MATLAB bitsweep 也改为 full-bit calibration semantics。
```

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/legacy/bitsweep.m:1
  E:/ADCToolbox/matlab/src/legacy/bitsweep.m:30
  E:/ADCToolbox/matlab/src/legacy/bitsweep.m:33

Python:
  E:/ADCToolbox/python/src/adctoolbox/dout/analyze_enob_sweep.py:65
  E:/ADCToolbox/python/src/adctoolbox/dout/analyze_enob_sweep.py:67
  E:/ADCToolbox/python/src/adctoolbox/dout/analyze_enob_sweep.py:76
  E:/ADCToolbox/python/src/adctoolbox/dout/analyze_enob_sweep.py:80
```

### MATLAB 做法

MATLAB 对每一个 bit 数重新校准：

```text
for nBits = 1..M:
  bits_subset = bits(:, 1:nBits)
  weights_subset = wcalsin(bits_subset)
  analyze reconstructed signal
```

### Python 做法

Python 先用全 bit 校准一次：

```text
weights_all = calibrate_weight_sine(bits)
```

然后每次只取前缀：

```text
bits_subset = bits[:, :n_bits]
weights_subset = weights_all[:n_bits]
```

### 原理差异

这两个实验回答的问题不同。

MATLAB 版本问的是：

```text
如果 ADC 只有前 n 个 bit，并且只用这 n 个 bit 重新校准，能达到什么性能？
```

Python 版本问的是：

```text
在全量校准权重已经确定的情况下，只使用前 n 个 bit 重构，边际贡献如何？
```

前者是“重新定义一个 n-bit 校准问题”，后者是“全模型权重下的 prefix ablation”。

### 影响

两者曲线不能直接比较。Python 版本更适合解释“低位是否继续贡献信息”；MATLAB 版本更接近“不同 bit 数 ADC 的独立校准性能”。

### 建议

Python 应显式提供两个模式：

```text
mode="recalibrate_each_subset"
mode="prefix_of_full_calibration"
```

文档中也应避免把二者都称为同一个 ENOB sweep。

---

## 4. `errsin` / Python phase-value error tools：Python 是重写后的诊断模型

处理状态：`RESOLVED / #94`

最终结论：

```text
`plot_error_hist_phase/code` 作为 legacy wrappers 已对齐 MATLAB `errsin` contract。
`analyze_error_by_phase/value` 保留 redesigned diagnostic 语义。
因此不再把 redesigned API 与 MATLAB `errsin` 直接硬比。
```

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/errsin.m:1
  E:/ADCToolbox/matlab/src/errsin.m:132
  E:/ADCToolbox/matlab/src/errsin.m:172
  E:/ADCToolbox/matlab/src/errsin.m:273
  E:/ADCToolbox/matlab/src/errsin.m:293

Python:
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_phase.py:15
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_phase.py:84
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_phase.py:89
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_phase.py:108
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_phase.py:160
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_value.py:9
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_value.py:60
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_value.py:73
  E:/ADCToolbox/python/src/adctoolbox/aout/rearrange_error_by_value.py:76
```

### MATLAB 做法

MATLAB `errsin` 是一个综合工具：拟合理想正弦，计算误差，然后按 phase / value 重排，并拟合 error energy 的 phase 结构。

其误差符号是：

```matlab
err = sig_fit - sig
```

### Python 做法

Python 拆成了多个函数，并引入了更明确的 phase/value bin、clip margin、base-noise/cos2phi 模型等。误差符号通常是：

```python
error = signal - fitted_signal
```

### 原理差异

errsin 类工具不是一个唯一数学定义，而是“把 sine fit residual 换坐标观察”的诊断方法。只要以下细节不同，输出就会明显不同：

```text
误差符号；
phase 单位和 bin center；
bin rounding / clipping；
是否显式建模 base noise；
是否拟合 cos(2phi) 结构；
value bin 的边界处理。
```

### 实测现象

compare CSV 中该项差异很大，不是浮点误差级别。

### 影响

这应视为语义不一致，不宜写成“Python 完全复刻 MATLAB errsin”。Python 版更像是重新设计过的 AOUT residual diagnostic。

### 建议

保留 Python 版新诊断，同时将 legacy wrapper 与 MATLAB `errsin` 分开描述：

```text
plot_error_hist_phase/code -> MATLAB errsin-compatible legacy contract；
analyze_error_by_phase/value -> Python redesigned residual diagnostics。
```

2026-07-09 更新：#94 已新增并接入 `errsin_compat`，本条不再是 active parity TODO。

---

## 5. `errevspec` / `plot_envelope_spectrum`：是否再次拟合 residual，语义不同

处理状态：`RESOLVED / #90`

最终结论：

```text
已通过 `input_kind="signal" | "error"` 拆开 contract。
MATLAB parity 使用 error/residual input path；
signal-input convenience path 保留 Python 原有行为。
```

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/dumped/errevspec.m:1
  E:/ADCToolbox/matlab/src/dumped/errevspec.m:9
  E:/ADCToolbox/matlab/src/dumped/errevspec.m:11

Python:
  E:/ADCToolbox/python/src/adctoolbox/aout/__init__.py:124
  E:/ADCToolbox/python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py:17
  E:/ADCToolbox/python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py:72
  E:/ADCToolbox/python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py:79
  E:/ADCToolbox/python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py:85
```

### MATLAB 做法

MATLAB `errevspec` 假设输入已经是 error：

```matlab
env = abs(hilbert(e))
specPlot(env)
```

也就是直接对 error 的 Hilbert envelope 做频谱。

### Python 做法

Python `plot_envelope_spectrum` / `analyze_error_envelope_spectrum` 会先把输入当成 signal，再 fit sine：

```python
sig_ideal = fitted sine
error_signal = signal - sig_ideal
env = abs(hilbert(error_signal))
```

如果用户传入的本来就是 residual，那么 Python 会对 residual 再拟合一次正弦，相当于分析“residual of residual”的 envelope。

### 原理差异

envelope spectrum 的对象应该明确：

```text
对象 A: residual e[n]
对象 B: signal x[n]，先减掉 fitted sine 得到 residual
```

MATLAB 是对象 A；Python 当前 wrapper 是对象 B。

### 实测现象

直接用 Python 做：

```text
abs(hilbert(err_data)) -> analyze_spectrum
```

可以和 MATLAB 高度一致。已验证关键指标：

```text
MATLAB vs current Python wrapper vs direct_env

ENoB: -4.237748, -4.269587, -4.237573
SNDR: -23.751241, -23.942912, -23.750188
SFDR: 0.323042, -0.024902, 0.323067
SNR:  -23.021998, -23.216781, -23.021805
THD:  -1.699380, -1.248789, -1.699398
```

### 影响

这是一个真实语义差异。当前 Python 名字容易让用户以为它等价于 MATLAB `errevspec(err)`。

### 建议

拆成两个入口：

```text
analyze_envelope_spectrum(error)
analyze_error_envelope_spectrum(signal, fit sine first)
```

并把 wrapper 名字改得更明确。

---

## 6. `plotwgt` / `analyze_weight_radix`：radix 数组长度和索引约定不同

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/plotwgt.m:1
  E:/ADCToolbox/matlab/src/plotwgt.m:84

Python:
  E:/ADCToolbox/python/src/adctoolbox/dout/analyze_weight_radix.py:10
  E:/ADCToolbox/python/src/adctoolbox/dout/analyze_weight_radix.py:72
  E:/ADCToolbox/python/src/adctoolbox/dout/analyze_weight_radix.py:73
  E:/ADCToolbox/python/src/adctoolbox/dout/__init__.py:23
  E:/ADCToolbox/python/src/adctoolbox/dout/__init__.py:25
```

### MATLAB 做法

MATLAB 返回：

```text
radix length = nBits - 1
```

因为 radix 是相邻权重之比，天然只有 `M-1` 个。

### Python 做法

Python 返回：

```text
radix length = nBits
radix[0] = NaN
radix[1:] = adjacent ratios
```

### 原理差异

数学上，radix 定义为：

```text
radix[i] = abs(w[i-1]) / abs(w[i])
```

它对应两个相邻 bit 之间的关系，不对应第一个 bit 自身。因此 MATLAB 的 `M-1` 长度更贴近数学定义；Python 的 `M` 长度更方便和 bit index 对齐，但需要第一个位置填 `NaN`。

### 实测现象

源码层面，如果使用相同 weights，并把 Python 的首位 `NaN` 去掉后再与 MATLAB `plotwgt` 的 radix 定义比较：

```text
Python radix[1:] vs MATLAB radix
max diff ≈ 1e-14
```

核心公式一致。

但需要注意当前 `reference_output/dout_SAR_12b_weight_2/test_wscaling/radix_matlab.csv` 的状态：

```text
reference radix length = nBits
reference radix[0] = NaN
Python radix[1:] vs reference radix[1:] max diff ≈ 8.44e-15
```

也就是说，当前 reference CSV 已经是“bit-aligned radix”形状，和当前源码 `plotwgt.m` 中 `nBits-1` 的直接返回定义不完全一致。这里应分清：

```text
源码接口定义：MATLAB plotwgt 返回 M-1 个 interval-indexed radix。
现有 reference 输出：已经带首位 NaN，形状更像 Python 的 bit-aligned radix。
```

### 影响

这是 API shape / reference 状态不一致，不是算法错误。风险在于 downstream 代码如果不知道 Python 或当前 reference 的第一个 radix 是 NaN，可能误用统计量；而如果只看当前 reference，又可能误以为 MATLAB 源码接口本身也是 `M` 长度。

### 建议

文档里明确：

```text
MATLAB: interval-indexed radix
Python: bit-aligned radix, radix[0]=NaN
```

必要时提供 `matlab_compatible=True` 返回 `radix[1:]`。

---

## 7. `cdacwgt` / `convert_cap_to_weight`：递推一致，但输入顺序相反

处理状态：`RESOLVED / #95`

最终结论：

```text
Python 默认保留 legacy `cap2weight` 的 LSB-to-MSB convention。
通过 `input_order="msb_to_lsb"` / `output_order="msb_to_lsb"` 支持 MATLAB `cdacwgt` convention。
递推算法不需要改，差异已显式化为 order contract。
```

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/cdacwgt.m:1
  E:/ADCToolbox/matlab/src/cdacwgt.m:17
  E:/ADCToolbox/matlab/src/cdacwgt.m:20
  E:/ADCToolbox/matlab/src/cdacwgt.m:24
  E:/ADCToolbox/matlab/src/cdacwgt.m:30
  E:/ADCToolbox/matlab/src/cdacwgt.m:109
  E:/ADCToolbox/matlab/src/cdacwgt.m:145

Python:
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/convert_cap_to_weight.py:13
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/convert_cap_to_weight.py:26
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/convert_cap_to_weight.py:36
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/convert_cap_to_weight.py:55
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/convert_cap_to_weight.py:87
```

### MATLAB 做法

MATLAB 新接口 `cdacwgt` 文档约定输入为：

```text
[MSB ... LSB]
```

内部为了递推，会反转成 LSB 到 MSB 处理，最后再反转输出。

补充：MATLAB 旧接口 `cap2weight` 本身是 LSB-to-MSB 约定，并在内部转接到 `cdacwgt`。因此这里的“顺序相反”主要是指 Python `convert_cap_to_weight` 与 MATLAB 新接口 `cdacwgt` 相比，而不是与 legacy `cap2weight` 相比。

### Python 做法

Python 文档约定输入为：

```text
[LSB ... MSB]
```

并按这个顺序直接递推和返回。

### 原理差异

CDAC weight 递推本质上从 LSB 往 MSB 累积 bottom plate / top plate 等效贡献，因此 LSB-first 是自然计算顺序。MATLAB 把用户接口做成 MSB-first，更符合 ADC bit vector 的常见阅读方式；Python 把用户接口做成 LSB-first，更贴近递推实现。

### 实测现象

如果把输入顺序对齐，两边结果一致：

```text
weight max diff ≈ 3.33e-16
ctot diff       = 0
```

### 影响

这是非常容易误用的 API 差异。用户如果把 MATLAB 的 `[MSB ... LSB]` 数据直接传给 Python，会得到反向解释的权重。

### 建议

Python 文档应在函数开头显眼标注：

```text
Python expects LSB-to-MSB order.
MATLAB cdacwgt expects MSB-to-LSB order.
```

也可以增加参数：

```python
order="lsb_to_msb" | "msb_to_lsb"
```

---

## 8. `plotphase` / polar analysis：不是完整一对一移植

处理状态：`RESOLVED FOR COMPARE FIXTURE / #93`

最终结论：

```text
LMS compare fixture 已对齐。
MATLAB `plotphase` 仍是综合入口，Python 保持拆分 API；这是 workflow / API 组织差异，
不是当前 active 数值 parity bug。
```

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/plotphase.m:1
  E:/ADCToolbox/matlab/src/plotphase.m:80
  E:/ADCToolbox/matlab/src/plotphase.m:141
  E:/ADCToolbox/matlab/src/plotphase.m:287
  E:/ADCToolbox/matlab/src/plotphase.m:386

Python:
  E:/ADCToolbox/python/src/adctoolbox/spectrum/analyze_spectrum_polar.py:16
  E:/ADCToolbox/python/src/adctoolbox/spectrum/analyze_spectrum_polar.py:56
  E:/ADCToolbox/python/src/adctoolbox/aout/analyze_decomposition_polar.py:8
  E:/ADCToolbox/python/src/adctoolbox/aout/decompose_harmonic_error.py:13
```

### MATLAB 做法

MATLAB `plotphase` 是一个综合函数，支持：

```text
mode = "FFT"
mode = "LMS"
```

默认更偏向 LMS / sine decomposition 路线。

### Python 做法

Python 拆成了两条线：

```text
analyze_spectrum_polar:
  FFT / coherent averaging based polar spectrum

analyze_decomposition_polar + decompose_harmonic_error:
  类似 LMS 的 harmonic decomposition
```

### 原理差异

polar plot 可以来自两种不同估计：

```text
FFT bin phasor:
  从频谱 bin 直接读复数相量。

LMS / basis decomposition:
  用 cos/sin basis 对每个 harmonic 做最小二乘拟合。
```

这两种在 coherent、无窗、长采样条件下会接近，但在 window、leakage、非 coherent、noise、phase reference 不一致时不完全等价。

### 影响

不能简单说 Python `analyze_spectrum_polar` 等价 MATLAB `plotphase`。它们服务的诊断目的接近，但默认方法、相位参考、归一化和输出对象不同。

### 建议

文档中应写成：

```text
MATLAB plotphase contains both FFT and LMS style paths.
Python currently exposes them as separate APIs.
```

若要做 parity test，必须固定同一 mode、同一 window、同一 phase reference。

---

## 9. `adcpanel` / dashboard：MATLAB 是统一面板，Python 是拆分 dashboard

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/adcpanel.m:1
  E:/ADCToolbox/matlab/src/adcpanel.m:68
  E:/ADCToolbox/matlab/src/adcpanel.m:81
  E:/ADCToolbox/matlab/src/adcpanel.m:406
  E:/ADCToolbox/matlab/src/adcpanel.m:477
  E:/ADCToolbox/matlab/src/adcpanel.m:486

Python:
  E:/ADCToolbox/python/src/adctoolbox/toolset/generate_aout_dashboard.py:16
  E:/ADCToolbox/python/src/adctoolbox/toolset/generate_aout_dashboard.py:48
  E:/ADCToolbox/python/src/adctoolbox/toolset/generate_dout_dashboard.py:14
  E:/ADCToolbox/python/src/adctoolbox/toolset/generate_dout_dashboard.py:53
  E:/ADCToolbox/python/src/adctoolbox/toolset/generate_dout_dashboard.py:57
```

### MATLAB 做法

MATLAB `adcpanel` 是一个大一统面板入口，内部根据数据类型和参数走不同 pipeline：

```text
analog output pipeline；
digital bit pipeline；
value pipeline；
full sine diagnostic pipeline。
```

### Python 做法

Python 把 dashboard 拆开：

```text
generate_aout_dashboard: 2x4 analog-output dashboard
generate_dout_dashboard: 2x3 digital-output dashboard
```

而且 digital dashboard 内部会自行做一次校准。

### 原理差异

这是工具组织方式不同，不是单一算法差异。MATLAB 倾向“一键总控”；Python 倾向“按数据类型拆工具”。

### 影响

如果用户期待 Python dashboard 和 MATLAB adcpanel 图数、图序、指标完全一致，会产生误解。

### 建议

Python 可以保留拆分 API，但应增加：

```text
adcpanel-compatible dashboard
```

或者在文档中明确两者不是一对一。

---

## 10. `ovfchk` / `check_overflow`：核心一致，测试配置曾不一致

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/tests/dout/run_ovfchk.m:14

Python:
  E:/ADCToolbox/python/tests/integration/test_overflow_chk.py:21
  E:/ADCToolbox/python/tests/integration/test_overflow_chk.py:24
  E:/ADCToolbox/python/tests/integration/test_overflow_chk.py:28
```

### 差异

MATLAB 测试里使用：

```text
wcalsin(read_data)
```

默认 harmonic order 为 1。

Python 测试里曾使用：

```text
calibrate_weight_sine(..., order=5)
```

然后把这个权重送入 overflow check。

### 原理差异

overflow / suffix-code distribution 对 weight 很敏感。只要校准权重不同，后续：

```text
range_min
range_max
ovf_percent_zero
ovf_percent_one
```

都可能不同。

### 实测现象

复核当前 reference 时，如果把同一套 MATLAB reference weights 直接送入 Python `check_overflow` / `analyze_overflow`：

```text
range_min diff ≈ 6.57e-7
range_max diff ≈ 6.57e-7
ovf_zero diff = 0
ovf_one diff  = 0
```

而当前 Python integration test 仍用上游 `calibrate_weight_sine(..., order=5)` 权重，与 MATLAB `wcalsin(read_data)` 默认 H=1 的 reference 比较时：

```text
ovf_one diff ≈ 0.732421875
```

### 影响

这不是 overflow 算法不一致，而是 test fixture 的 upstream weight 不一致。

### 建议

对齐测试应固定同一套 weights，或明确分成：

```text
check_overflow core parity；
calibrate_weight_sine + check_overflow integration behavior。
```

---

## 11. `sinfit` / `fit_sine_4param`：默认迭代次数不同

处理状态：`RESOLVED FOR COMPARE FIXTURE / #91`

最终结论：

```text
compare fixture 显式使用 MATLAB-compatible refinement policy。
Python 默认 lightweight iteration policy 保留；warning/default 差异不再作为 parity blocker。
```

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/sinfit.m:101
  E:/ADCToolbox/matlab/src/sinfit.m:180

Python:
  E:/ADCToolbox/python/src/adctoolbox/fundamentals/fit_sine_4param.py:10
```

### MATLAB 做法

MATLAB 默认：

```text
niter = 100
```

如果 100 次仍未收敛，MATLAB 也会 warning；只是默认迭代次数更高，所以常规数据中不容易触发。

### Python 做法

Python 默认：

```python
max_iterations=1
tolerance=1e-9
```

因此很多 integration test 中会出现：

```text
fit_sine_4param did not converge in 1 iterations
```

### 原理差异

四参数 sine fit 通常需要迭代估计：

```text
amplitude
frequency
phase
DC
```

如果只迭代一次，它更像是“一步修正”，不是完整收敛。

### 实测现象

在常规 sinfit parity 中，最终参数仍可高度一致：

```text
freq diff     ≈ 2.30e-13
mag diff      ≈ 4.28e-10
dc diff       ≈ 1.92e-14
phi diff      ≈ 2.93e-10
data_fit diff ≈ 4.76e-10
```

但默认 warning 容易污染用户体验。

### 影响

这更像默认参数和 warning policy 问题，而不是算法核心错误。

### 建议

要么提高默认 `max_iterations`，要么让上层示例显式传入合理迭代次数。

---

## 12. `ntfperf` / NTF analyzer：频率积分网格不同

处理状态：`RESOLVED / #92`

最终结论：

```text
已暴露 MATLAB grid policy，compare 固定同一 integration grid。
Python 默认 grid 可作为原有快速路径保留。
```

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/ntfperf.m:1
  E:/ADCToolbox/matlab/src/ntfperf.m:63
  E:/ADCToolbox/matlab/src/ntfperf.m:64

Python:
  E:/ADCToolbox/python/src/adctoolbox/oversampling/ntfperf.py:8
  E:/ADCToolbox/python/src/adctoolbox/oversampling/ntf_analyzer.py:6
  E:/ADCToolbox/python/src/adctoolbox/oversampling/ntf_analyzer.py:19
```

### MATLAB 做法

MATLAB 使用：

```text
N = 1e6
w = (1:N) / N / 2
```

### Python 做法

Python 使用：

```python
np.linspace(0, 0.5, 2**16)
```

### 原理差异

NTF performance 需要对频率上的噪声传递函数做积分或近似积分。频率网格越密，数值积分越接近连续结果。

### 实测现象

观测到约：

```text
0.001352 dB
```

级别差异。

### 影响

这是小的数值积分差异，不是物理模型差异。

### 建议

如果要 parity，应提供 `n_grid` 参数并在 compare test 中固定相同网格。

---

## 13. `plotspec` / `analyze_spectrum`：源码已有对齐迹象，但 reference/compare 状态未同步

### 代码位置

```text
MATLAB:
  E:/ADCToolbox/matlab/src/plotspec.m

Python:
  E:/ADCToolbox/python/src/adctoolbox/spectrum/analyze_spectrum.py
  E:/ADCToolbox/python/tests/compare/test_compare_analyze_spectrum.py
```

### 当前源码状态

当前 MATLAB `plotspec.m` 源码已经在多处把 `sideBin` 纳入 harmonic / spur / THD 相关计算。例如：

```text
THD:      h_start = max(b-sideBin,1), h_end = min(b+sideBin,inbandEnd)
NFMethod: spec_noise(h_start:h_end) = 0
SFDR:     spur_start/spur_end also use sideBin
```

因此，“MATLAB 当前源码完全没有对 harmonic 使用 sideBin”这个说法已经不适合作为当前源码事实。

### 历史注意点

但是 compare test 中仍保留 known inconsistency skip 注释，大意是：

```text
MATLAB harmonic power 没有使用 sideBin；
Python harmonic power 使用 sideBin。
```

并且使用当前仓库已有 `reference_output` 手动比较时，`run_plotspec` 仍未达到 strict parity：

```text
sigpwr diff ≈ 1.93e-15  （基本完全一致）
ENOB diff   ≈ 3.08e-4
SNDR diff   ≈ 1.85e-3 dB
SNR/NSD diff≈ 0.199 dB
SFDR diff   ≈ 1.79 dB
THD diff    ≈ 2.84 dB
```

这说明当前状态更可能是：

```text
源码曾经或正在修正 sideBin/harmonic 策略；
但 reference CSV、skip reason、compare test 尚未同步到同一套定义。
```

### 原理差异

频谱分析中的 sideBin 决定了：

```text
tone power 是否只取中心 bin；
还是把中心 bin 周围泄漏/窗函数主瓣一起计入。
```

这会影响：

```text
signal power；
harmonic power；
noise power；
SNDR / THD / SFDR。
```

### 建议

保留对 `sideBin` 的显式说明。重新判定 parity 前应先：

```text
1. 确认当前 MATLAB plotspec 源码定义；
2. 重新生成 MATLAB reference_output；
3. 更新或取消 test_compare_analyze_spectrum.py 中的旧 skip reason；
4. 再比较 Python 输出。
```

parity test 中应固定：

```text
window；
sideBin；
harmonic sideBin policy；
coherent / non-coherent 条件。
```

---

## 14. 已确认核心基本对齐的项目

以下项目在相同输入、相同关键参数下，MATLAB 与 Python 结果基本一致：

```text
sinfit / fit_sine_4param:
  标量参数和 fitted data 高度一致。

ifilter:
  max diff ≈ 4.66e-15。

noiseshape / apply_noise_shaping:
  shaped error RMS diff ≈ 1e-18。

tomdec / decompose_harmonics:
  sine/error diff ≈ 1.28e-9；
  harmic/others diff ≈ 3.49e-6，仍是小数值差异，但不是原先记录的 3e-9 量级。

inlsin / compute_inl_from_sine:
  diff ≈ 2.2e-13。

errac:
  residual autocorrelation 路线基本一致。

errspec:
  residual spectrum 路线基本一致。

plotres / plot_residual_scatter:
  partial residual 公式一致。

errpdf:
  KDE 核心一致，x/fx 小差异约 1e-6，主要来自 fit/default/wrapper 细节。

perfosr:
  原理一致，少量 dB 差异更像默认 fit / FFT / 网格细节。
```

这些项目后续不应优先视为算法缺陷，而应先检查：

```text
输入是否完全相同；
默认参数是否一致；
频率 / 相位 / window / sideBin 是否一致；
是否经过上游不同校准权重。
```

---

## 15. 最终解决状态

原 P0 / P1 / P2 队列已闭环：

```text
cdacwgt / convert_cap_to_weight order contract        -> #95
bitsweep / analyze_enob_sweep mode + default contract -> #89, #97
errevspec / envelope spectrum input contract          -> #90
wcalsin frequency / radix / scale contracts           -> #79, #84, #85, #86, #87
overflow compare fixture                              -> #88
ntfperf grid contract                                 -> #92
plotphase LMS compare fixture                         -> #93
errsin legacy compatibility wrappers                  -> #94
sinfit compare refinement policy                      -> #91
plotspec integrated-lobe parity                       -> #76
```

仍可保留的后续增强不再是 active parity blocker：

```text
1. `adcpanel` / dashboard migration note：workflow/UI 映射说明。
2. `plotspec` / spectrum 更多 corner regression：hardening，不是已知 mismatch。
3. `findbin` / coherent-frequency candidate policy：API/default policy 差异，若未来需要可单独设计。
4. learning 文档和 release note 的最终整理。
```

---

## 16. 学习上的核心判断

从学习角度看，这些不一致提醒我们一件事：

```text
“函数名字相同”不等于“实验问题相同”；
“图像类似”不等于“数学对象相同”；
“核心公式一致”不等于“默认入口一致”。
```

ADC 工具箱里很多函数都不是孤立算法，而是一个完整实验流程的一部分。真正对齐时必须同时对齐：

```text
输入数据；
预处理；
频率估计；
拟合模型；
归一化；
bin / window / sideBin；
输出指标定义；
作图语义。
```

因此后续看 MATLAB 与 Python 差异时，第一步不应直接问“谁错了”，而应先问：

```text
它们是否在回答同一个问题？
```

如果回答的是同一个问题，再进入公式、数值和代码级别的 bug 判断。
