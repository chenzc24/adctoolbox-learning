# Stage 02：FFT 与 ADC 动态性能指标

## 本阶段目标

学完本阶段，你应该能解释：

- 为什么 ADC 测试常用单音 sine。
- 什么是 coherent sampling。
- FFT bin、spectral leakage、window 是什么。
- SNR、SNDR、SFDR、THD、ENOB、NSD 分别衡量什么。
- 为什么频谱分析必须排除 DC、fundamental、harmonics。

## 初学者先抓住的主线

FFT 阶段不是为了“画一张漂亮频谱图”，而是为了把 ADC 输出拆成几类能量：

```text
DC                  -> 偏置
fundamental          -> 你真正输入的正弦
harmonics            -> 非线性失真
other spurs          -> 杂散、失配、干扰
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
到底是噪声坏了，还是 spur/harmonic 坏了？
```

## 数学需要补什么

### 1. 正弦信号

单音测试信号：

```text
x[n] = A sin(2π Fin n / Fs) + DC
```

用 normalized frequency 表示：

```text
f = Fin / Fs
x[n] = A sin(2π f n) + DC
```

本库很多函数使用 normalized frequency，比如：

```text
freq = Fin / Fs
```

### 2. FFT bin

采样点数为 `N`，采样率为 `Fs`，频率分辨率：

```text
df = Fs / N
```

第 `k` 个 FFT bin 对应频率：

```text
Fk = k * Fs / N
```

如果输入频率刚好满足：

```text
Fin = k * Fs / N
```

则输入频率落在第 `k` 个 bin。

### 3. 相干采样

相干采样要求：

```text
Fin / Fs = k / N
```

这表示采样窗口里刚好有 `k` 个完整周期。

优点：

- 主频能量集中在一个 bin。
- rectangular window 可用。
- SNR/SFDR/THD 解释更干净。

不相干时：

- 主频能量泄漏到周围很多 bin。
- 需要 window。
- spur 和 noise floor 可能被误判。

### 4. 功率和 dB

功率比转 dB：

```text
dB = 10 log10(P1 / P2)
```

幅度比转 dB：

```text
dB = 20 log10(A1 / A2)
```

ADC 频谱指标通常基于功率。

### 5. 动态指标

设：

```text
P_signal = fundamental power
P_noise = noise power excluding DC, fundamental, harmonics
P_harm = harmonic distortion power
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

### 6. NSD

NSD 是 noise spectral density：

```text
dBFS/Hz
```

它把总噪声归一化到带宽上，更适合比较不同采样率或带宽下的噪声。

## 电路需要理解什么

### 1. SNR 差通常意味着随机噪声

可能来源：

- thermal noise
- comparator noise
- sampling capacitor kT/C noise
- reference noise
- clock jitter

### 2. SFDR/THD 差通常意味着确定性非线性

可能来源：

- capacitor mismatch
- amplifier nonlinear
- reference settling
- switch charge injection
- comparator kickback

### 3. jitter 与输入频率相关

jitter-limited SNR 近似：

```text
SNR_jitter = -20 log10(2π Fin σt)
```

所以同样的 clock jitter，在高输入频率下更差。

## 本库对应代码

核心频谱分析：

```text
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/spectrum/compute_spectrum.py
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
python/src/adctoolbox/examples/02_spectrum/
python/src/adctoolbox/examples/07_conversions/
```

## 对应 API

```python
from adctoolbox import analyze_spectrum
from adctoolbox import find_coherent_frequency
from adctoolbox import snr_to_nsd, nsd_to_snr
from adctoolbox import calculate_jitter_limit
```

## 实验 1：最小频谱分析

```powershell
cd C:\Users\90590\adctoolbox_examples
python 02_spectrum\exp_s01_analyze_spectrum_simplest.py
```

观察控制台输出：

```text
ENOB
SNDR
SFDR
SNR
NSD
```

问自己：

- SNDR 和 SNR 为什么不完全一样？
- SFDR 是看最大 spur，不是看总噪声。

## 实验 2：窗口函数和 leakage

```powershell
cd C:\Users\90590\adctoolbox_examples
python 02_spectrum\exp_s08_windowing_deep_dive.py
```

观察：

- rectangular window 对 coherent signal 很好。
- non-coherent 时 rectangular leakage 严重。
- window 牺牲主瓣宽度，换取旁瓣抑制。

## 实验 3：动态范围 sweep

```powershell
cd C:\Users\90590\adctoolbox_examples
python 02_spectrum\exp_s04_sweep_dynamic_range.py
```

观察：

- 输入幅度过小，SNR 下降。
- 输入幅度过大，可能 clipping，THD/SFDR 变差。

## 本阶段代码阅读

建议先读：

```text
python/src/adctoolbox/fundamentals/frequency.py
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/spectrum/compute_spectrum.py
python/src/adctoolbox/spectrum/_harmonics.py
python/src/adctoolbox/spectrum/_estimate_noise_power.py
```

阅读重点：

- fundamental bin 怎么找。
- harmonic bin 怎么折叠。
- noise bin 怎么排除。
- `enob` 是用哪个指标计算的。

读 `analyze_spectrum` 时，可以只追踪这条逻辑：

```text
输入 waveform
-> 计算 FFT
-> 找 fundamental
-> 找 harmonics
-> 剩下的 bins 估计 noise
-> 汇总 SNR / SNDR / SFDR / THD / ENOB
```

如果你读不懂所有参数，先抓住这些参数：

```text
fs              -> 采样率
win_type        -> 窗口类型
side_bin        -> 主频附近合并多少 bin
max_scale_range -> full-scale 归一化参考
```

## 容易混淆的点

- `SNR` 不包含 harmonic distortion；`SNDR` 包含。
- `SFDR` 只看最大的单个 spur，不代表总噪声。
- `ENOB` 是由 `SNDR` 换算来的，所以失真也会拉低 ENOB。
- coherent sampling 不是玄学，它只是让信号能量刚好落在 FFT bin 上。
- window 不是“让结果更好”，而是在 non-coherent 时减少 leakage 带来的误判。

## 阶段检查问题

1. 为什么非相干采样会导致 spectral leakage？
2. 为什么 THD 高会让 SNDR 变差，但不一定让 SNR 变差？
3. SNR、SNDR、SFDR 三者分别对什么问题敏感？
4. 为什么 jitter 对高频输入更致命？
5. 为什么理想 N-bit ADC 的 ENOB 接近 N，但真实 ADC 往往低于 N？

