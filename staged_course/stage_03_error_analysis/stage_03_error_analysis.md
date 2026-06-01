# Stage 03：正弦拟合与 residual 误差分析

## 本阶段目标

学完本阶段，你应该能解释：

- 为什么 ADC 单音测试要拟合一个 ideal sine。
- residual/error 是什么。
- error PDF、error autocorrelation、error spectrum 分别回答什么问题。
- 如何根据 residual 判断噪声、失真、memory、glitch 等问题。

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

## 三张图分别看什么

如果 demo 给你三类 residual 图，按这个顺序看：

| 图 | 先问什么 |
|---|---|
| error vs sample/time | 有没有周期、突变、包络变化 |
| error PDF | 像 Gaussian、uniform，还是有长尾/多峰 |
| error autocorrelation | 相邻样本之间是否相关 |
| error spectrum | residual 里有没有固定频率 spur |

初学者最常见误区是只看 PDF。PDF 能看幅度分布，但看不出“这个误差是不是每隔固定周期出现”。所以 PDF、ACF、spectrum 要一起看。

## 数学需要补什么

### 1. 模型分解

单音 ADC 输出可以写成：

```text
y[n] = ideal_sine[n] + error[n]
```

其中：

```text
ideal_sine[n] = A cos(2πfn) + B sin(2πfn) + C
```

或者等价地：

```text
ideal_sine[n] = Amp * sin(2πfn + phase) + DC
```

残差：

```text
error[n] = y[n] - ideal_sine[n]
```

### 2. 最小二乘

如果频率 `f` 已知，拟合 `A, B, C` 是线性最小二乘：

```text
y ≈ X β
```

其中：

```text
X = [cos(2πfn), sin(2πfn), 1]
β = [A, B, C]^T
```

最小二乘求：

```text
min ||Xβ - y||^2
```

解析形式：

```text
β = (X^T X)^-1 X^T y
```

实际代码通常用数值稳定的 `lstsq`。

### 3. 频率也未知时

如果频率未知，就先用 FFT 找主峰，再迭代 refine。

本库的 `fit_sine_4param` 返回：

```text
frequency
amplitude
phase
dc_offset
fitted_signal
residuals
rmse
```

### 4. PDF

PDF 分析 error 的幅度分布。

常见判断：

| error PDF | 可能含义 |
|---|---|
| Gaussian | thermal noise 主导 |
| Uniform | 理想量化噪声近似 |
| heavy tail | glitch、干扰、突发噪声 |
| asymmetric | offset、奇偶不对称、系统性误差 |
| multi-modal | code 问题或 deterministic error |

### 5. Autocorrelation

自相关：

```text
R[k] = E[e[n] e[n+k]]
```

直觉：

- white noise：除 `k=0` 外接近 0。
- memory effect：小 lag 上有相关。
- periodic interference：周期性 lag 上有峰。

### 6. Error spectrum

error spectrum 是对 `error[n]` 再做 FFT。

它回答：

```text
误差里有哪些频率成分？
```

这比只看 PDF 更能发现确定性 spur。

## 电路需要理解什么

### 1. 不同电路问题有不同 residual 指纹

| 电路/系统问题 | residual 特征 |
|---|---|
| thermal noise | PDF Gaussian，ACF 近似 white |
| quantization | bounded error，可能接近 uniform |
| capacitor mismatch | deterministic harmonic/spur |
| incomplete settling | error 与前一状态相关，ACF 有结构 |
| reference droop | memory-like error，可能随输入幅度变化 |
| clock feedthrough | error spectrum 有固定 spur |
| clipping | PDF tail/edge 异常，harmonics 增强 |

### 2. residual 是诊断工具

频谱指标告诉你：

```text
坏了多少
```

residual 告诉你：

```text
坏的形态是什么
```

这一步是从“测量”进入“归因”的关键。

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
cd C:\Users\90590\adctoolbox_examples
python 04_debug_analog\exp_a01_fit_sine_4param.py
```

观察：

- fitted sine 是否贴合原始数据。
- residual RMS 是否合理。
- 频率估计是否稳定。

## 实验 2：error PDF

```powershell
cd C:\Users\90590\adctoolbox_examples
python 04_debug_analog\exp_a21_analyze_error_pdf.py
```

观察：

- `sigma` 是多少 LSB。
- KL divergence 是否接近 0。
- PDF 是否 Gaussian-like。

## 实验 3：error autocorrelation

```powershell
cd C:\Users\90590\adctoolbox_examples
python 04_debug_analog\exp_a23_analyze_error_autocorrelation.py
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

