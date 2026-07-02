# 争议问题与边界问题记录

这个文件用于记录学习过程中出现的“值得反复讨论的问题”。它不是结论库，也不是
`notes.md` 的替代品，而是专门保存那些：

- 看起来和常见教材说法有张力的问题。
- 关系到测试方法是否严谨的问题。
- 需要区分“数学真实值”和“工程估计值”的问题。
- 当前已经有阶段性理解，但还需要后续验证、标准对照或代码实验的问题。

推荐每个条目都保留：

```text
问题
触发讨论
当前共识
仍然开放的边界
对课程/代码的影响
后续验证方向
```

## 2026-06-30：Window correction 是否能还原真实频谱？

### 问题

在 Stage 02 学习 window、CG、ENBW、`side_bin` 和动态指标计算时，出现一个核心疑问：

```text
有限 FFT 中，每个 bin 本身已经是多个频率成分经 window 频谱泄漏后的叠加。
那么对每个 bin 乘一个统一的 window correction，
是否真的能还原原始真实频谱？
如果不能，SNR / SNDR / THD / SFDR 是否还能算准？
```

更具体地说：

```text
Y[k]
= 目标频率贡献
 + fundamental leakage
 + harmonic leakage
 + spur leakage
 + noise realization
```

所以某个 bin 通常不是“原始第 k 个频率点乘了一个常数”，而是频域卷积后的混合结果。

### 触发讨论

最初的疑问来自 CG：

```text
CG = (1 / N) * sum_n w[n]
```

它可以解释 coherent 单音落在某个 bin 时，中心 bin 幅度为什么被 window 缩放：

```text
Y[m] = A * sum_n w[n]
Y[m] / N = A * CG
```

但这只严格对应：

```text
coherent single tone
```

并不能推出：

```text
任意频谱中的每个 bin 都只是被 CG 缩放。
```

因为一般情况下：

```text
时域乘窗
-> 频域卷积
-> 频率成分互相泄漏和耦合
```

### 当前共识

当前阶段形成的共识是：

```text
window correction 不是 inverse windowing；
window correction 不是 deconvolution；
window correction 不能从有限 FFT 中恢复真实无限长频谱。
```

ADCToolbox 中的：

```text
power_correction = 4 / (window_gain^2 * ENBW)
```

由于：

```text
window_gain = sum(w) / N
ENBW = N * sum(w^2) / (sum(w))^2

window_gain^2 * ENBW
= sum(w^2) / N
= mean(w^2)
```

所以更准确地说，它是在做：

```text
window RMS power normalization
```

也就是对 windowed power spectrum 做一次功率尺度标定，而不是把 leakage 卷积撤销。

因此：

```text
CG / ENBW correction:
    负责功率尺度标定

side_bin:
    负责把 fundamental 主瓣附近的 bin 合并为 signal power

window choice:
    负责改变 leakage 的主瓣/旁瓣分布

coherent sampling:
    负责让已知 tone 尽量落在 FFT bin 上
```

这些方法合起来可以改善有限记录频谱估计，但不能真正还原真实频谱。

### 对 SNR / SNDR 的影响

`SNR`、`SNDR`、`THD`、`SFDR` 在 FFT 动态测试中应理解为：

```text
在指定采样条件、指定 window、指定分析带宽、指定 bin 分类规则下得到的性能估计。
```

它们不是：

```text
先严格恢复真实频谱，再从真实频谱积分出来的绝对物理真值。
```

这意味着：

- 如果 fundamental coherent，主信号功率估计会更干净。
- 如果 harmonic 也由 coherent fundamental 产生，harmonic 通常也更容易落在可预测 bin。
- 但外部 spur、reference ripple、clock spur、colored noise、测试源污染不一定 coherent。
- 非相干 deterministic spur 如果没有被正确合并或排除，可能被误算成 noise。
- 强 fundamental 的 leakage 也可能盖住小 spur，影响 `SFDR` 和 `SNDR`。
- 白噪声近似平坦时，ENBW 对 noise density / total noise 的标定更有意义。
- 对非白噪声或确定性 spur，单个 scalar correction 不足以完成真实分离。

所以更严谨的表达是：

```text
FFT 指标的可信度来自：
    测试条件设计
    coherent sampling
    合适 window
    足够记录长度 N
    合理 side_bin / bin mask
    输入源和时钟质量控制
    多次测量或 sweep 验证
    residual analysis 交叉检查

而不是来自 window correction 能恢复真实频谱。
```

### 2026-07-01 数值验证：不反演也能证明指标有效

更准确的问题不是：

```text
能不能从 windowed FFT 反演真实连续频谱？
```

而是：

```text
在不反演真实频谱的情况下，
FFT-based SNR / SNDR / THD / SFDR 是否仍能正确反映 ADC 输出误差能量？
```

可以。证明对象应限定为：

```text
在固定测试 protocol、固定 window、固定 N、固定带宽、固定 bin mask 下，
FFT 指标等价于有限记录中目标信号能量与非目标误差能量的比值。
```

它的数学基础是 Parseval 定理：

```text
时域有限记录中的能量
等价于
频域 FFT bin 功率之和
```

window 会改变能量在频率 bin 之间的分布，但不会让有限记录中的能量凭空消失或产生。只要目标 tone、
harmonic、spur、noise 的 bin 分类规则固定，并且分类足够覆盖对应主瓣，指标就不需要 true-spectrum
recovery 也能成立。

我们做了一个确定性数值实验：

```text
N = 16384
fundamental bin = 997
signal peak = 0.7 FS
noise/spur = 多个已知非谐波整数 bin 的正交 tone
harmonics = 已知 HD2 / HD3
window = rectangular
side_bin = 0
```

在 ADCToolbox 的 dBFS convention 下，peak 为 `A` 的 full-scale-normalized sine 对应功率尺度为
`A^2`。因此可直接构造真值：

```text
P_signal = A^2
P_noise = sum(noise_amp_i^2)
P_distortion = sum(harmonic_amp_i^2)

SNR_truth  = 10log10(P_signal / P_noise)
SNDR_truth = 10log10(P_signal / (P_noise + P_distortion))
```

实验 A：只改变 noise，其他条件固定。

```text
noise_amp_rss  truth_SNR   FFT_SNR   error       truth_SNDR  FFT_SNDR   error
0.0002         70.881361   70.881361  -1.4e-11   70.881361   70.881361  -1.5e-11
0.0005         62.922561   62.922561  -5.6e-12   62.922561   62.922561  -5.8e-12
0.0010         56.901961   56.901961  -2.8e-12   56.901961   56.901961  -2.8e-12
0.0020         50.881361   50.881361  -1.4e-12   50.881361   50.881361  -1.4e-12
0.0050         42.922561   42.922561  -5.6e-13   42.922561   42.922561  -5.7e-13
```

这说明在 coherent rectangular 的理想可分离条件下，FFT 指标与有限记录真值能量比相差只有浮点舍入误差。
noise 放大 2 倍时，SNR / SNDR 严格下降约 `6.02 dB`。

实验 B：noise 固定，只增加 harmonic distortion。

```text
dist_scale  truth_SNR   FFT_SNR   truth_SNDR  FFT_SNDR   THD
0           62.922561   62.922561  62.922561   62.922561  -146.902
0.5         62.922561   62.922561  60.845995   60.845995   -65.047
1           62.922561   62.922561  57.541438   57.541438   -59.027
2           62.922561   62.922561  52.584577   52.584577   -53.006
4           62.922561   62.922561  46.876275   46.876275   -46.986
8           62.922561   62.922561  40.937389   40.937389   -40.965
```

这个结果说明：

```text
SNR 只跟 noise energy 有关，不应随 harmonic distortion 增加而改变；
SNDR 跟 noise + distortion energy 有关，会随 harmonic distortion 增加而下降；
THD 跟 harmonic energy 有关，会随 distortion scale 增加而上升。
```

因此，在固定测试条件下，`SNR` / `SNDR` 越大，确实表示 ADC 输出中的非目标误差能量越小。这个结论来自
有限记录能量分解，而不是来自真实频谱反演。

同时，这个实验也验证了边界：

```text
无 harmonic distortion 时：
    Hann / Blackman-Harris 等 window 只要使用合适 side_bin，也能与真值能量比一致。

有 harmonic distortion 时：
    SNDR 仍可与真值一致，因为它把非 fundamental 能量整体放入 denominator。
    SNR 若只排除 harmonic center bin，而没有排除 harmonic main-lobe，
    会把 harmonic side-lobe 误算入 noise，得到保守偏低的 SNR。
    使用 harmonic lobe exclusion 后，SNR 恢复与真值一致。
```

2026-07-01 追加判断：

```text
这不是小的显示误差，而是动态指标体系的 energy classification consistency 问题。
```

当前 upstream 已经把：

```text
THD / harmonics_dbc:
    harmonic power = harmonic main-lobe integrated power

SNDR:
    denominator = noise + distortion
    因此 harmonic center 和 harmonic side-lobe 都应留在 denominator 中
```

但 `SNR` 的 noise estimator 仍可能出现 method-dependent 不一致：

```text
nf_method=3:
    只排除 harmonic center bin
    harmonic side-lobe 仍进入 noise

nf_method=4:
    通过 _exclude_bins_from_spectrum 排除 harmonic ± side_bin
```

因此，在 windowed harmonic distortion case 中，同一段 harmonic lobe 可能被：

```text
THD 视为 distortion；
SNDR 视为 distortion/noise+distortion denominator；
SNR(nf_method=3) 的 noise estimator 却把 harmonic side-lobe 视为 noise。
```

这会让 `SNR` 偏低，并且让 `snr_dbc`、`noise_floor_dbfs`、`nsd_dbfs_hz` 的含义依赖
noise-estimation method。严格来说，既然默认动态指标已经切到 integrated-lobe convention，
SNR 的 harmonic exclusion 也应该采用同一套 harmonic-lobe mask，或者明确标记 center-bin-only
noise exclusion 是 legacy / plotspec-style 口径。

所以严格结论是：

```text
FFT 指标不需要 true-spectrum recovery 才有意义。

它们测量的是：
    在指定测试 protocol 下，
    ADC 输出有限记录中目标正弦能量与非目标误差能量的比值。

正确性依赖：
    固定测试条件
    足够记录长度
    合理 window / side_bin
    正确 bin mask / energy classification
    输入源和时钟误差受控

不依赖：
    从 windowed FFT 反演真实连续频谱。
```

### 和标准测试方法的关系

后续需要对照 ADC / digitizer 动态测试标准和厂商应用笔记继续核对，例如：

```text
IEEE 1241
IEEE 1057
coherent sampling / window sampling application notes
```

当前理解是：

```text
标准测试方法通常也不是宣称 FFT + window correction 可以恢复真实频谱；
而是规定采样条件、输入源质量、记录长度、窗口、带宽、bin 分类和报告方式，
使动态指标成为可重复、可比较的工程估计。
```

### 对课程内容的影响

Stage 02 中关于 window correction 的表述应避免写成：

```text
校正后得到真实频谱
```

更合适的说法是：

```text
window correction 只做功率尺度标定；
leakage 造成的频率混合无法通过 scalar correction 消除；
SNR / SNDR / THD / SFDR 是有限记录和指定分析规则下的动态性能估计。
```

Stage 03 的 residual analysis 因此很重要。它不是 Stage 02 的重复，而是用另一个视角检查：

```text
被频谱指标归类为 noise / harmonic / spur 的误差，
在时域、输入相位、输入值和误差频谱里是否真的呈现对应结构。
```

### 后续验证方向

可以设计几个实验继续验证：

1. coherent fundamental + rectangular window，观察理想单音指标。
2. coherent fundamental + 非相干外部 spur，观察 spur leakage 如何影响 noise / SFDR。
3. 同一数据分别用 rectangular、Hann、Blackman-Harris，比较主瓣合并和 noise 估计差异。
4. 增大 `N`，观察频率分辨率提升后指标是否趋于稳定。
5. 改变 `side_bin`，观察 `sig_pwr_dbfs`、`snr_dbc`、`sfdr_dbc` 的敏感性。
6. 用 `fit_sine_4param` 去除主信号，再用 residual spectrum 检查剩余结构。

### 当前状态

```text
状态：阶段性共识，已完成基础数值验证，仍需结合标准和更多 corner 实验继续验证。
影响：Stage 02 / Stage 03 均应保留“有限记录估计”这个边界。
```

## 2026-06-30：FFT 动态指标是否应该统一使用 integrated-lobe power？

### 问题

在继续检查 `SNR`、`SNDR`、`THD`、`SFDR` 的计算口径时，发现当前实现混用了两种
tone power 定义：

```text
integrated-lobe power:
    对 tone 的 main-lobe bins 求和

peak-bin power:
    只取 tone center bin 或最大 bin
```

这带来一个定义层面的争议：

```text
同一组动态指标里，signal power 是否应该始终表示同一个物理量？
```

当前 ADCToolbox 的实际情况是：

```text
SNR / SNDR / ENOB / NSD:
    使用 integrated fundamental power

THD / harmonics_dbc / SFDR:
    使用 peak-bin fundamental power
```

也就是说，同一个 fundamental 在不同指标中被当成了两个不同的 reference。

### 代码定位

核心代码在：

```text
python/src/adctoolbox/spectrum/compute_spectrum.py
python/src/adctoolbox/spectrum/_harmonics.py
```

`compute_spectrum.py` 中先计算两个 signal power：

```python
sig_bin_start = max(fundamental_bin - side_bin, 0)
sig_bin_end = min(fundamental_bin + side_bin + 1, n_inband)

sig_linear = float(np.sum(power_spectrum[sig_bin_start:sig_bin_end]))
sig_pwr_linear = sig_linear
sig_pwr_dbfs = 10 * np.log10(max(sig_pwr_linear, 1e-30))
sig_peak = float(power_spectrum[fundamental_bin])
```

其中：

```text
sig_linear:
    fundamental_bin ± side_bin 的积分功率

sig_peak:
    fundamental center bin 的单 bin 功率
```

随后：

```python
sndr_dbc = 10 * np.log10(sig_linear / (noi_sndr + 1e-20))
snr_dbc = 10 * np.log10(sig_linear / noise_power)
```

但：

```python
harmonics_dbc = 10 * np.log10(harmonic_powers / sig_peak)
thd_dbc = 10 * np.log10(thd_power / sig_peak)
sfdr_dbc = np.inf if spur_power <= 0 else 10 * np.log10(sig_peak / spur_power)
```

`_harmonics.py` 中当前 harmonic 使用 plotspec-style single-bin power：

```python
p = float(power_spectrum[h_bin])
harmonic_powers[harmonic_index] = max(p, 1e-15)
thd_power += p
```

`SFDR` 也使用最大非信号 single-bin power：

```python
spur_bin_idx = int(np.argmax(spectrum_copy))
spur_power = float(spectrum_copy[spur_bin_idx])
```

因此当前实现不是单纯的 integrated convention，也不是单纯的 peak-bin convention，而是：

```text
SNR / SNDR:
    integrated convention

THD / SFDR:
    peak-bin convention
```

### 触发讨论

问题最初来自 window 的影响：

```text
非矩形 window 会把一个 tone 的能量分布到多个 bins。
```

即使 tone 是 coherent，Hann、Blackman-Harris、flattop 等 window 下，center bin 也不等于
tone total power。一次数值检查显示：

```text
rectangular:
    sig_integrated - sig_peak = 0.000 dB

hann:
    sig_integrated - sig_peak = 1.761 dB

blackmanharris:
    sig_integrated - sig_peak = 3.020 dB

flattop:
    sig_integrated - sig_peak = 5.764 dB
```

因此如果某个指标用 `sig_linear`，另一个指标用 `sig_peak`，用户很容易误以为它们都在
引用同一个 signal power，但实际并不是。

### 当前共识

当前阶段形成的共识是：

```text
mixed convention 不适合作为不加说明的通用 API 语义。
```

更一般、更一致的有限 FFT 功率估计口径应是 integrated-lobe convention：

```text
P_signal:
    sum fundamental main-lobe bins

P_harmonic:
    sum each harmonic main-lobe bins

P_spur:
    find highest spur region, then sum spur main-lobe bins

P_noise:
    exclude signal / harmonic / identified spur regions, then estimate or sum remaining noise
```

然后统一计算：

```text
SNR  = P_signal / P_noise
SNDR = P_signal / (P_noise + distortion)
THD  = sum(P_harmonics) / P_signal
SFDR = P_signal / max(P_spur)
```

`peak-bin` 方法仍有合理使用场景，例如：

```text
coherent sampling
rectangular window
所有重要 tones 都 bin-centered
快速读图 / plotspec-style convention
legacy comparison
```

但它应被明确标注为：

```text
peak-bin / plotspec-style metric
```

而不应和 integrated signal power 混在同一组指标中却不说明。

### 仍然开放的边界

integrated-lobe convention 更一致，但仍不是 true-spectrum recovery。它仍依赖：

```text
side_bin 选择
window type
tone separation
spur 是否靠近 fundamental 或 harmonic
noise floor
record length N
```

因此后续真正需要定义的是：

```text
1. 如何为 harmonic / spur 选择 integration region？
2. close-in spur 是否应合并，还是应单独标记 collision？
3. integrated spur 是否应从 noise / SNDR denominator 中排除？
4. legacy plotspec-style 字段如何兼容？
5. 默认 API 应该保持 legacy，还是切到 integrated？
```

### 对课程/代码的影响

课程里应明确区分：

```text
peak-bin tone ratio
integrated-lobe tone power ratio
```

不要把当前 `thd_dbc` / `sfdr_dbc` 解释成无条件的 tone total power ratio。

代码层面，后续建议至少：

```text
1. 暴露 sig_peak_dbfs 和 sig_integrated_dbfs。
2. 修正 _extract_highest_spur 的 docstring，当前写的 summed over center ± side_bin 与实现不符。
3. 新增 integrated THD / SFDR / harmonics metrics，或新增 metric_mode。
4. 将 plotspec-style peak-bin 指标标记为 legacy / peak-bin convention。
```

### 当前状态

```text
状态：阶段性共识，建议进入 optimization 任务跟踪。
影响：当前 Stage 02 应把 THD/SFDR 的当前实现口径讲清楚；后续代码应考虑统一 metric convention。

2026-07-01 更新：
  upstream 已通过 issue #64 和 PR #65 / #67 采纳 integrated-lobe convention。
  Python `compute_spectrum` 已改为：
    signal / harmonics / THD / SFDR 使用 integrated-lobe power；
    MaxSpur power 对 detected spur lobe 求和，而不是只取 center bin。
  MATLAB `plotspec.m` 也已在 PR #67 中改为 integrated-lobe THD/SFDR。
  中间 PR #66 曾短暂保留 MATLAB legacy 口径，但已被 #67 覆盖。

  处理结论：
    本条争议中的“默认 API 是否应混用 peak-bin 与 integrated-lobe power”已经解决；
    当前 upstream/main 的默认方向是统一 integrated-lobe metric convention。
    仍需在课程中保留的边界是：integrated-lobe 仍不是 true-spectrum recovery，
    它仍依赖 window、side_bin、tone separation、record length 和 bin mask。
```
