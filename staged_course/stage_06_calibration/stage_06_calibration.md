# Stage 06：Sine-based ADC 位权重校准

## 本阶段如何承接 Stage 05

Stage 05 已经把 SAR ADC 的 raw digital output 看成矩阵：

```text
B = bits
B.shape == (n_samples, n_bits)
```

并且已经知道数字重构是：

```text
aout = B @ weights
```

Stage 06 从这里继续，问一个更工程化的问题：

```text
如果 weights 不准，能不能从一段已知输入形式的数据里估计出更好的 weights？
```

对 SAR ADC 来说，最常见的答案是：

```text
用一段 sine input 做 foreground calibration。
```

也就是：

```text
已知输入应该是一条正弦；
已知 ADC 输出的 raw bits；
未知的是每个 bit column 应该乘多大的数字权重。
```

一句话承接：

```text
Stage 05 检查 B 是否可信；
Stage 06 用 B 去估计 w。
```

## 本阶段目标

学完本阶段，你应该能解释：

- ADC 位权重校准要解决什么问题。
- 为什么 sine input 可以用于估计 bit weights。
- `calibrate_weight_sine` 的输入、输出和整体数学逻辑。
- 为什么 `freq` 必须是 normalized `Fin/Fs`，而不是 Hz。
- `harmonic_order` 在校准模型里扮演什么角色。
- 为什么 rank deficiency 会让某些权重不可独立估计。
- 为什么校准通常改善 SFDR/THD，但不一定显著改善随机噪声导致的 SNR。
- 如何用 spectrum、residual 和独立测试数据验证校准效果。

## 对应孙老师课件主线

本阶段对应孙老师课件中的几条关键观点：

```text
ch4  DAC 权重：
     ADC 内部 DAC 的实际权重不可能完全理想；校准是在估计真实权重。

ch12 SAR ADC：
     SAR 的主要可校准误差之一是 CDAC capacitor mismatch。

ch3  性能指标：
     校准效果不能只说“图变好了”，要看 SNDR / SFDR / THD / ENOB。

ch17 测试：
     校准需要观测误差，测试提供观测手段；测试条件会影响指标。

数学补充：最小二乘、矩阵秩、可观测性：
     B @ w ≈ target 是一个带噪声、可能秩亏的参数估计问题。
```

## 初学者先抓住的主线

校准不是重新做一次 ADC 转换。

ADC 转换已经发生了：

```text
bits = SAR(vin, actual_analog_weights)
```

校准做的是数字域后处理：

```text
校准前：aout_before = bits @ nominal_weights
校准后：aout_after  = bits @ calibrated_weights
```

也就是说：

```text
bits 没变；
变的是数字重构 weights。
```

从初学者角度，`calibrate_weight_sine` 可以先理解成：

```text
我知道输入应该是一条正弦；
我也知道每个采样点的 bit pattern；
那我能不能求一组 weights，让 bits @ weights 尽量像一条正弦？
```

这就是最小二乘的工程含义。

## 一个极简类比

假设 ADC 只有三列 bit：

```text
y[n] = b0[n] * w0 + b1[n] * w1 + b2[n] * w2
```

真实 ADC 的 `w0, w1, w2` 因为电容失配不等于理想值。你采了很多点，于是有很多方程：

```text
sample0: b00*w0 + b01*w1 + b02*w2 ≈ sine0
sample1: b10*w0 + b11*w1 + b12*w2 ≈ sine1
sample2: b20*w0 + b21*w1 + b22*w2 ≈ sine2
...
```

如果样本足够多、bit pattern 足够丰富，这就是一个过定方程：

```text
B @ w ≈ sine
```

最小二乘选择一组 `w`，让所有样本的总体误差最小：

```text
min ||B @ w - sine||^2
```

实际代码比这个式子更复杂，因为：

```text
sine 的幅度、相位、DC offset 也未知；
输入频率可能也需要估计；
输出里可能有 harmonic；
bit matrix 可能 rank deficient；
数值条件可能不好。
```

但主线始终是：

```text
用 raw bits 解释一个正弦目标，从而估计 bit weights。
```

## 数学需要补什么

### 1. 从重构模型开始

对 bit matrix：

```text
B.shape == (N, M)
```

数字重构：

```text
y = B @ w + c
```

其中：

```text
B -> 已知，来自 ADC raw bits
w -> 未知或不准，是待估计 bit weights
c -> DC offset
```

如果输入是单音正弦，理想输出可以写成：

```text
s[n] = A*cos(2πf n) + D*sin(2πf n) + C
```

这里用 `cos` 和 `sin` 两个 basis 的原因是：

```text
任意相位的正弦都可以写成 cos 和 sin 的线性组合。
```

例如：

```text
R*sin(2πf n + φ)
  = A*cos(2πf n) + D*sin(2πf n)
```

其中 `A` 和 `D` 吸收了幅度和相位。

### 2. 为什么不是直接 `B @ w = vin`

仿真里我们有时知道 `vin`，但真实 ADC 测试中通常不知道每个采样点的精确模拟输入电压。我们更可靠地知道的是：

```text
输入是一条频率可控的 sine。
```

所以校准目标不是：

```text
B @ w = 某个逐点精确已知的 vin
```

而是：

```text
B @ w 应该能被一组 sine basis 解释。
```

这非常符合 ADC 动态测试习惯：

```text
输入低失真正弦；
采集输出码流；
用频域或拟合方法估计性能。
```

孙老师 ch17 讲的动态测试，就是这条思路的测试侧表达。

### 3. `calibrate_weight_sine_lite` 的最小模型

最小版本 `calibrate_weight_sine_lite.py` 假设频率已知，构造：

```python
t = np.arange(n_samples)
phase = 2.0 * np.pi * freq * t
cos_basis = np.cos(phase)
sin_basis = np.sin(phase)

offset_col = np.ones((n_samples, 1))
A = np.column_stack([bits, offset_col, sin_basis])
b = -cos_basis
coeffs, _, _, _ = lstsq(A, b)
```

这等价于求：

```text
bits @ w_raw + offset + sin_coeff * sin(2πf n) ≈ -cos(2πf n)
```

为什么把 `cos` 放到右边？

因为 sine 的整体幅度未知。如果把 `cos` 和 `sin` 两个 fundamental 系数都放进未知量，同时又让 `w` 也自由缩放，就会出现尺度不唯一：

```text
把 w、cos coefficient、sin coefficient 同时乘一个常数，
相对误差形式可能仍然难以唯一固定。
```

lite 版本用一个约定固定尺度：

```text
假设 cos fundamental coefficient = 1
```

然后求出其他系数。最后用 fundamental 幅度归一化：

```python
norm_factor = np.sqrt(1.0 + sin_coeff**2)
weights = weights_raw / norm_factor
```

直觉是：

```text
cos coefficient 固定为 1，sin coefficient 由最小二乘求出；
fundamental 的真实幅度是 sqrt(1^2 + sin_coeff^2)；
weights 要除以这个幅度，回到归一化后的物理权重尺度。
```

最后还有 polarity correction：

```python
if np.sum(weights) < 0:
    weights = -weights
```

因为最小二乘本身可能给出整体符号相反的等价解。对 SAR 权重来说，我们通常希望权重总和为正。

### 4. 完整版本为什么尝试 dual basis

完整的 `_lstsq_solver.py` 不只固定 `cos=1`，还会尝试：

```text
Assumption 1: Cosine fundamental is unity
Assumption 2: Sine fundamental is unity
```

也就是：

```python
A1 = column_stack([bits, offsets, cos_basis[:, 1:], sin_basis])
b1 = -cos_basis[:, 0]

A2 = column_stack([bits, offsets, sin_basis[:, 1:], cos_basis])
b2 = -sin_basis[:, 0]
```

然后比较 residual：

```python
err1 = norm(A1 @ coeffs1 - b1)
err2 = norm(A2 @ coeffs2 - b2)
```

选择误差更小的一边。

为什么要这样？

因为实际输入相位可能让某个 basis 更适合固定为 unity。dual basis 可以避免单一相位约定导致数值条件不好。

### 5. harmonic_order 的意义

真实 ADC 输出不一定只有 fundamental。CDAC mismatch、静态非线性、参考动态误差等会产生 harmonic：

```text
2Fin, 3Fin, 4Fin, ...
```

如果校准模型只允许 fundamental，而真实数据里有明显 harmonic，那么最小二乘可能会试图用 `weights` 去解释这些 harmonic。这样会污染权重估计。

完整版本构造 harmonic basis：

```python
harmonics = np.arange(1, harmonic_order + 1)
phase = 2.0 * np.pi * freq * outer(t, harmonics)
cos_basis = cos(phase)
sin_basis = sin(phase)
```

当：

```python
harmonic_order=3
```

模型里会包含：

```text
1Fin, 2Fin, 3Fin
```

其中 fundamental 用来固定尺度，额外 harmonic 作为 nuisance basis，帮助把谐波成分从权重估计里分离出去。

所以 `harmonic_order` 不是“把谐波校准掉几次”的意思，而是：

```text
在拟合模型里显式允许若干 harmonic，让它们不要错误污染 bit weights。
```

常见理解：

```text
harmonic_order = 1:
  只建 fundamental，不额外吸收高次谐波。

harmonic_order = 3:
  允许 2nd/3rd harmonic 进入拟合模型，降低它们对 weight estimation 的污染。
```

### 6. freq 必须是 normalized `Fin/Fs`

`calibrate_weight_sine` 的 `freq` 参数不是 Hz，而是：

```text
freq = Fin / Fs
```

Nyquist 范围是：

```text
0 <= freq <= 0.5
```

代码里有明确保护：

```python
if np.any(_freq_check > 0.5):
    raise ValueError("freq must be normalized Fin/Fs ...")
```

如果你有：

```text
Fin = 6.1 MHz
Fs  = 100 MHz
```

应该传：

```python
freq = 6.1e6 / 100e6
```

如果是 coherent sampling：

```text
Fin / Fs = fin_bin / n_samples
```

所以常见调用是：

```python
cal = calibrate_weight_sine(
    bits,
    freq=fin_bin / n_samples,
)
```

把 Hz 直接传进去是非常常见、也非常危险的错误。现在代码会直接报错，避免 silent failure。

### 7. 频率估计和 frequency search

如果 `freq=None`，完整版本会尝试估计频率：

```python
freq_array = _estimate_frequencies(bits_stacked, segment_lengths, freq, verbose)
```

估计时会先用一部分 bit 按二进制假设重构出一个粗略信号：

```python
assumed_weights = 2 ** np.arange(n_use - 1, -1, -1)
sig = current_segment[:, indices] @ assumed_weights
f_est = estimate_frequency(sig)
```

然后如果需要，会进入 frequency refinement：

```python
_solve_weights_searching_freq(...)
```

这个过程迭代做：

```text
1. 用当前频率求最小二乘权重。
2. 计算 residual 对频率的导数。
3. 更新频率。
4. 重复直到 relerr 足够小或达到 max_iter。
```

学习时不必一开始读懂每个导数细节，但要理解：

```text
频率估计不准会直接污染校准；
如果你知道 coherent bin，优先传准确的 freq。
```

### 8. rank deficiency：为什么有些权重无法独立估计

最小二乘能稳定工作，需要观测矩阵有足够独立信息。

如果：

```text
B[:, i] == B[:, j]
```

那么数据无法区分：

```text
w_i 增大
```

和：

```text
w_j 增大
```

这就是 rank deficiency。

ADCToolbox 在 `_patch_rank_deficiency.py` 里先检查：

```python
matrix_to_check = np.column_stack([bits_stacked, np.ones(n_samples_total)])
np.linalg.matrix_rank(matrix_to_check)
```

注意它把 DC offset 列也放进去，因为校准模型包含 offset。

如果 rank 不够，就逐列修补：

```text
Case A: constant column -> dead bit, drop
Case B: independent column -> keep
Case C: dependent column -> merge into existing effective column
```

对 dependent column，代码用 nominal weights 的比例来分配：

```python
bit_weight_ratios[bit_idx] = nominal_weights[bit_idx] / nominal_weights[founding_bit_idx]
bits_effective[:, col_idx] += col * bit_weight_ratios[bit_idx]
```

求解完成后，再恢复回原 bit 空间：

```python
weights_recovered = w_effective[bit_to_col_map] * bit_weight_ratios
weights_recovered[bit_to_col_map < 0] = 0.0
```

物理意义是：

```text
如果数据只能看见两个 bit 的组合，就先估计组合总权重；
再按 nominal ratio 分回每个 bit。
```

这不是凭空创造信息，而是在信息不足时做一个有工程先验的分配。

### 9. column scaling：数值条件不是小事

bit columns 的尺度可能差很多，尤其经过 rank patch 后，某些 effective columns 可能不是简单 0/1。

`_scale_columns_for_conditioning.py` 会按数量级缩放列：

```python
max_vals = np.max(np.abs(col_extremes), axis=0)
bit_scales = np.floor(np.log10(max_vals + 1e-15))
bits_effective = bits * (10.0 ** (-bit_scales))
```

求解后再恢复：

```python
w_physical_eff = w_normalized * (10.0 ** (-bit_scales))
```

这属于数值线性代数里的 conditioning。物理直觉是：

```text
不要让某些列因为数值尺度太大或太小，在最小二乘中造成病态求解。
```

### 10. 输出结果应该如何理解

`calibrate_weight_sine` 返回 dictionary，常见字段：

```text
weight
offset
calibrated_signal
ideal
error
refined_frequency
snr_db
enob
```

其中：

```text
weight:
  校准得到的 digital reconstruction weights。

offset:
  拟合出的 DC offset。

calibrated_signal:
  用校准权重对 bits 重构出的信号。
  它不是 ADC 重新采样得到的信号。

ideal:
  拟合模型重构出来的 reference sine / harmonic model。

error:
  calibrated_signal 去掉 offset 后与 ideal 的差。

refined_frequency:
  最终使用或估计出的 normalized frequency。

snr_db / enob:
  基于内部拟合误差计算的性能摘要。
```

实际验证时，不要只看返回的 `enob`。更稳的做法是：

```python
calibrated = cal["calibrated_signal"]
metrics = analyze_spectrum(calibrated, ...)
```

然后和校准前比较：

```text
SNDR
SNR
SFDR
THD
ENOB
harmonics
noise floor
```

## 电路需要理解什么

### 1. 校准针对 deterministic mismatch

孙老师 ch4 和 ch12 都强调：SAR 内部 CDAC 权重不准会导致比较阈值不准。

这类误差通常是 deterministic：

```text
同一颗芯片上，某个电容偏大或偏小；
每次转换都用同一套偏差权重；
误差在输出中形成稳定结构。
```

这正适合数字校准：

```text
估计实际权重；
在数字重构时使用 calibrated_weights。
```

典型可校准误差：

```text
capacitor mismatch
stable bit weight error
stable offset / gain error
interstage gain error
某些稳定通道 mismatch
```

### 2. 随机噪声不能被逐次权重校准消掉

采样 kT/C 噪声、比较器随机噪声、热噪声、随机 jitter 等，每次采样或每次比较都会变化。

数学上可以写成：

```text
y[n] = B[n, :] @ w_true + noise[n]
```

校准可以估计 `w_true`，但不能知道每一个 `noise[n]` 的真实 realization。

所以常见现象是：

```text
SFDR / THD 明显改善；
SNR 几乎不变；
ENOB 有改善但不会无限接近 nominal bit。
```

这不是校准失败，而是说明：

```text
deterministic spur 被修正了；
random noise floor 仍然存在。
```

这正对应孙老师 ch5/ch6/ch7 的物理边界：

```text
kT/C 噪声、比较器噪声、建立动态错误不是同一种东西；
固定误差可估计，随机噪声不能逐次消除。
```

### 3. actual analog weights 与 digital weights 必须分清

仿真中我们可以写：

```python
actual_weights = sar_apply_cap_mismatch(nominal_weights, sigma=0.004, rng=rng)
bits = sar_convert(vin, actual_weights)
```

这里的 `actual_weights` 是模拟转换时 CDAC 的真实权重。

数字重构时：

```python
aout_before = sar_reconstruct(bits, nominal_weights)
aout_after  = bits @ calibrated_weights
```

这里的 `nominal_weights` / `calibrated_weights` 是数字后端使用的重构权重。

校准改变的是：

```text
digital reconstruction weights
```

不是：

```text
已经发生的 analog conversion。
```

如果模拟转换阶段已经发生不可恢复的错误，例如：

```text
比较器随机翻转太多；
严重 clipping；
redundancy 不足导致前位错误无法被后位修正；
reference 瞬态错误随时间强烈变化；
```

单纯改数字权重无法完全修复。

### 4. 为什么 sine input 适合 foreground calibration

sine input 的优点：

```text
容易由低失真信号源产生；
频谱结构简单；
幅度、相位、DC 都可以用少量参数表示；
频率可以通过 FFT 或拟合估计；
覆盖大量 code 时能激励多个 bit pattern；
适合和 SNDR / SFDR / THD 指标直接连接。
```

但 sine calibration 也有条件：

```text
输入幅度不能太小，否则低位不充分翻转；
输入不能严重 clipping；
频率估计要可靠；
训练长度要足够；
bit matrix 条件要好；
测试源失真不能比 ADC 还糟。
```

这就是 Stage 07 要继续强调的验证问题。

## 本库对应代码

主入口：

```text
python/src/adctoolbox/calibration/calibrate_weight_sine.py
python/src/adctoolbox/calibration/calibrate_weight_sine_lite.py
```

内部步骤：

```text
python/src/adctoolbox/calibration/_prepare_input.py
python/src/adctoolbox/calibration/_patch_rank_deficiency.py
python/src/adctoolbox/calibration/_scale_columns_for_conditioning.py
python/src/adctoolbox/calibration/_estimate_frequencies.py
python/src/adctoolbox/calibration/_lstsq_solver.py
python/src/adctoolbox/calibration/_post_process.py
```

相关 SAR 模型：

```text
python/src/adctoolbox/models/sar.py
```

相关 spectrum 验证：

```text
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/spectrum/quick_sndr.py
```

官方示例：

```text
python/src/adctoolbox/examples/05_debug_digital/exp_d01_cal_weight_sine_lite.py
python/src/adctoolbox/examples/05_debug_digital/exp_d02_cal_weight_sine.py
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

本地完整 demo：

```text
learning/adctoolbox-learning/demos/whole_workflow_demo.py
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

## 对应 API

```python
from adctoolbox import calibrate_weight_sine
from adctoolbox.calibration import calibrate_weight_sine_lite
```

典型调用：

```python
cal = calibrate_weight_sine(
    bits,
    freq=fin_bin / n_samples,
    nominal_weights=nominal_weights,
    harmonic_order=3,
)

weights_calibrated = cal["weight"]
signal_calibrated = cal["calibrated_signal"]
```

如果只有最小实验：

```python
weights = calibrate_weight_sine_lite(bits, freq=fin_bin / n_samples)
```

## `calibrate_weight_sine` 代码流程总览

完整函数可以按 7 步读：

```text
1. 检查 freq 是否在 normalized Nyquist 范围内。
2. _prepare_input：把 bits 整理成统一格式，建立 nominal_weights。
3. _patch_rank_deficiency：处理恒定列和线性相关列。
4. _scale_columns_for_conditioning：改善最小二乘数值条件。
5. _estimate_frequencies：如果需要，估计输入频率。
6. _lstsq_solver：在已知或搜索频率下求最小二乘解。
7. _post_process：恢复权重、重构信号、计算 error / ENOB。
```

对应源码骨架：

```python
clean_input = _prepare_input(bits, nominal_weights, verbose)
patched_input = _patch_rank_deficiency(bits_stacked, nominal_weights, verbose)
bits_scaled, bit_scales = _scale_columns_for_conditioning(bits_effective, verbose)
freq_array = _estimate_frequencies(bits_stacked, segment_lengths, freq, verbose)

if run_frequency_search:
    freq_array, coeffs, basis_choice, cos_basis, sin_basis = _solve_weights_searching_freq(...)
else:
    coeffs, basis_choice, cos_basis, sin_basis = _solve_weights_with_known_freq(...)

w_phys_effective = _recover_columns_for_conditioning(...)
weights_final = _recover_rank_deficiency(...)
results = _post_process(...)
```

读代码时不要一上来陷入所有细节。先追三件事：

```text
bits 怎么变成最小二乘矩阵；
weights 在哪里被解出来；
calibrated_signal 最后怎么生成。
```

## 实验 1：最小校准示例

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d01_cal_weight_sine_lite.py
```

重点看：

```text
bits 如何进入 calibrate_weight_sine_lite；
freq 如何传入；
recovered_weights 和原始权重的差异。
```

这个例子适合理解最小数学模型。

## 实验 2：完整 sine weight calibration

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d02_cal_weight_sine.py
```

观察：

```text
before calibration 的 ENOB / spectrum；
after calibration 的 ENOB / spectrum；
nominal weights、real weights、calibrated weights 的差异。
```

注意示例里有一条非常有用的注释：

```text
calibrate_weight_sine returns weights that sum to ~2.0 (differential signal)
```

这提醒你：

```text
权重尺度和输入/输出归一化约定有关；
不要只凭“数值看起来是不是 1/2,1/4...”判断对错。
```

## 实验 3：SAR mismatch Monte Carlo

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d16_sar_unit_cap_mismatch_mc.py
```

这个例子比较：

```text
Strict binary
Radix ~1.8 redundant SAR
```

并对 unit-cap mismatch sigma 做 sweep。每个 sigma 下跑 32 次 Monte Carlo。

观察重点：

```text
before calibration: mismatch 越大，ENOB 分布越差；
after calibration: deterministic weight error 被补偿；
redundant SAR 在高 mismatch 下更稳；
结果要看分布，不要只看某一个 seed。
```

## 实验 4：MSB error 与 redundancy

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
```

这个例子比较：

```text
Strict binary:
  [32768, 16384, 8192, 4096, ..., 1]

3rd-weight repeat:
  [32768, 16384, 8192, 8192, 4096, ..., 1]
```

同样给 MSB 加 1% actual weight error，然后：

```text
用一段 coherent sine 训练；
用另一段 coherent sine 测试；
比较 before / after / ideal actual weight。
```

它要说明：

```text
冗余结构不是为了让权重“更复杂”，而是为了给错误决策留下 correction margin。
```

## 实验 5：训练长度 sweep 与 overfitting

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

这个例子问：

```text
foreground sine calibration 需要多少训练样本，才能泛化到独立测试 capture？
```

它会生成三类图：

```text
1. 在独立 test capture 上的 ENOB 分布。
2. 在 calibration capture 自身上的 ENOB 分布。
3. 两者 overlay，用来暴露短训练记录的 overfitting。
```

这个实验非常适合 Stage 07，但 Stage 06 也要先知道结论：

```text
训练数据上变好，不等于校准真的可信。
```

## 实验 6：本地完整闭环

运行：

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

看：

```text
E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\03_sar_model_and_calibration.png
E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\spectrum_metrics.csv
```

重点比较：

```text
sar_mismatch_nominal_weights
sar_after_sine_calibration
```

你应该看到典型模式：

```text
SFDR / THD 改善；
SNR 不会因为权重校准而奇迹般消失噪声底；
ENOB 的改善取决于原先性能是被 deterministic spur 还是 random noise 限制。
```

## 校准前后应该怎么看

不要只看 ENOB。

至少看：

```text
SNDR
SNR
SFDR
THD
ENOB
noise floor
harmonic levels
residual structure
bit activity / radix / overflow
```

常见解释：

| 现象 | 可能解释 |
|---|---|
| SFDR 明显改善，SNR 几乎不变 | 校准修正了 deterministic spur，但噪声底没变 |
| THD 改善，ENOB 小幅改善 | 原本同时受失真和随机噪声限制 |
| 校准后训练集很好，测试集不好 | 样本不足、过拟合、频率估计偏差、输入覆盖不足 |
| 校准后变差 | 模型不匹配、`freq` 错、bit order 错、rank/conditioning 问题 |
| 权重看起来很怪但指标改善 | 可能有尺度/极性/冗余分配约定，需要结合架构解释 |
| 权重接近 actual 但指标没改善 | 可能随机噪声或不可恢复 bit decision 主导 |

## 容易混淆的点

- `calibrated_signal` 是用校准权重重构出的信号，不是 ADC 重新采样得到的信号。
- `freq` 必须是 normalized `Fin/Fs`，不是 Hz。
- `harmonic_order` 不是“校准几次谐波”，而是在拟合模型里显式允许若干 harmonic basis。
- 校准结果接近 `actual_weights` 是仿真里的好现象；真实芯片上通常不知道 `actual_weights`。
- 如果输入幅度太小，某些 bit 没有充分翻转，对应权重很难估。
- 如果 bit matrix rank deficient，样本再多也不一定能独立估计所有权重。
- 如果随机噪声已经主导，权重校准不会让 SNR 大幅提升。
- 如果只在训练 capture 上验证，很容易把 overfitting 当成校准成功。
- `nominal_weights` 在 rank deficiency 修补时会影响权重分配，不只是装饰参数。
- `calibrate_weight_sine` 的内部 `snr_db/enob` 是拟合摘要；最终工程结论仍应靠独立 spectrum/residual 验证。

## 进入 Stage 07 前要带走什么

Stage 06 的核心不是“记住函数参数”，而是建立参数估计模型：

```text
观测数据 = 已知 bit matrix 结构 + 未知 weights + sine basis + 噪声/残差
```

最重要的判断是：

```text
这个误差是不是稳定、可参数化、可观测？
```

如果答案是“是”，校准可能有效。

如果答案是：

```text
随机噪声主导；
bit 决策已经不可恢复；
模型没有覆盖真实动态误差；
训练数据不充分；
```

那么校准效果会有限，甚至可能在独立测试上变差。

一句话总结：

```text
Sine-based calibration 是用最小二乘从 raw bits 中估计 digital weights；
它能修稳定权重错误，但不能突破噪声、可观测性和模型边界。
```

## 阶段检查问题

1. 为什么校准可以写成 `B @ w ≈ sine`？
2. `bits`、`weights`、`calibrated_signal` 分别是什么？
3. `actual_analog_weights` 和 `digital_reconstruction_weights` 有什么区别？
4. 为什么 `freq=Fin/Fs`，而不是 `freq=Fin`？
5. `calibrate_weight_sine_lite` 为什么要固定一个 fundamental basis coefficient 为 1？
6. `harmonic_order` 的意义是什么？
7. 为什么 capacitor mismatch 适合校准，而 thermal noise 不适合逐次校准？
8. 什么情况下 bit matrix 会 rank deficient？
9. `_patch_rank_deficiency` 为什么要用 nominal weight ratio 把 dependent bit 分回去？
10. 为什么训练数据上 ENOB 变好不等于校准结论可信？

这些问题如果能讲清楚，就可以进入 Stage 07：从“会校准”进入“会判断校准是否可信”。
