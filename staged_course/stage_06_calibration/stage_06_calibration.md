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

### 5. `harmonic_order` 的意义和边界

真实 ADC 输出不一定只有 fundamental。CDAC mismatch、静态非线性、参考动态误差、输入源失真等
都可能产生 harmonic：

```text
2Fin, 3Fin, 4Fin, ...
```

这里最容易误解的一点是：频谱里看到 H2/H3，并不能只凭单个 sine capture 判断它来自哪里。
它可能来自：

```text
输入源 / 测试链路 harmonic；
ADC analog nonlinearity；
CDAC mismatch / bit-weight error；
settling / comparator / code-dependent error。
```

所以 `harmonic_order` 不是“校准几次谐波”，也不是“越高越好”。它是在选择一个建模假设：

```text
这些 harmonic 更像 source/test-chain nuisance，
还是更应该由 bit weights 去解释？
```

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

其中 fundamental 用来固定尺度；额外 H2/H3 作为 nuisance basis 进入最小二乘。最终输出仍然是：

```text
calibrated_signal = bits @ calibrated_weights
```

而不是：

```text
bits @ calibrated_weights + fitted_harmonics
```

也就是说，harmonic 不会直接叠加到校准输出中；但它会改变求出来的 `weights`。

从线性代数角度看，加入 harmonic nuisance 近似等价于把 H2/H3/... 子空间从误差里投影掉：

```text
min_w || P_perp(Z) · (B @ w + reference) ||^2

Z = offset + companion fundamental basis + harmonic nuisance basis
```

这样有两面性。

如果 harmonic 主要来自输入源 / 测试链路：

```text
harmonic_order=1:
  可能把源 harmonic 错误吸收到 weights。

harmonic_order=3:
  可以把 H2/H3 当作 nuisance，保护 weight estimate。
```

如果 harmonic 主要来自 ADC / CDAC mismatch：

```text
harmonic_order = 1:
  更适合作为纯 mismatch 仿真、干净测试源、或敏感性 baseline。

harmonic_order = 3:
  可能把一部分本该约束 weights 的 mismatch harmonic 当作 nuisance 投影掉。
```

所以更准确的使用建议是：

```text
H=1:
  用于纯 mismatch 研究、仿真 demo、source 已知干净的情况，
  或作为 harmonic sensitivity 的 control/baseline。

H>=3:
  用于训练源可能含 harmonic 污染时的 robust weight estimation，
  但必须承认它带有 source/test-chain nuisance 假设。
```

实际工程里不要指望库从单个 sine capture 自动判断 H3 到底来自源还是 ADC。更诚实的目标是：

```text
当 harmonic attribution 歧义大到会影响 weights 时，把风险量化出来。
```

一个直接的诊断思路是分别跑：

```python
cal_h1 = calibrate_weight_sine(bits, freq=freq, harmonic_order=1)
cal_h3 = calibrate_weight_sine(bits, freq=freq, harmonic_order=3)
```

然后比较归一化后的权重差异：

```text
normalized_weight_delta = ||normalize(w_H1) - normalize(w_H3)|| / ||normalize(w_H1)||
```

这里的 `normalize` 应先处理整体尺度和 polarity；对带 trim / 负权重的结构，最好使用
best-fit scale 或 `sum(abs(w))` 类的归一化，而不是机械地按 `sum(w)`。

如果 `H=1` 与 `H=3` 的权重差异很大，结论不是“某个 harmonic 一定来自源”，而是：

```text
这个 capture 的 harmonic attribution 已经会影响 weight estimate。
```

更严谨的训练方式是 multi-capture + per-capture harmonic nuisance：

```python
cal = calibrate_weight_sine(
    [bits_f1, bits_f2, bits_f3, bits_f4],
    freq=[f1, f2, f3, f4],
    harmonic_order=3,
)
```

这里 `weights` 在多个 capture 间共享，而每个 capture 有自己的 harmonic basis。这样比“只做
multi-capture 但仍然 `harmonic_order=1`”更干净：

```text
multi-capture + H=1:
  可以缓解源 harmonic 污染，因为不同 frequency 下污染方向不完全一致；
  但模型仍缺少 harmonic 自由度，污染不会自动消失。

multi-capture + H>=3:
  shared weights 解释跨 capture 稳定的 bit-weight 结构；
  per-capture harmonic nuisance 吸收每条记录自己的 source/test-chain harmonic。
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

---

#### 第 8 节补充：恢复公式的真实写法、merge 顺序、以及两个实现隐患

上面的主线是对的：Case A/B/C + nominal ratio 分配，在可辨识性意义上合理。
但有几个实现细节和隐患，光读主线容易漏掉。这一节把它们补全。

**1. 恢复公式的真实写法（上面简化了）**

第 620 行写的是简化版：

```python
weights_recovered = w_effective[bit_to_col_map] * bit_weight_ratios
```

源码实际是（`_patch_rank_deficiency.py` 的 `_recover_rank_deficiency`）：

```python
weights_recovered = w_effective[np.maximum(bit_to_col_map, 0)]
weights_recovered = weights_recovered * bit_weight_ratios
weights_recovered[bit_to_col_map < 0] = 0.0
```

那个 `np.maximum(bit_to_col_map, 0)` 不是装饰：被 drop 的 bit 在 `bit_to_col_map`
里是 `-1`，直接拿去索引会触发 `IndexError`。`np.maximum(..., 0)` 把 -1 钳到 0，
先取到一个占位值，再由 `bit_weight_ratios`（被 drop 的 bit ratio=0）和最后一行的
强制清零把它归零。照着简化版写代码会踩坑。

**2. Case C 的 merge 依赖 bit 列顺序**

patch 是按 bit 顺序逐列处理的：第一个被 keep 的列成为 "founding bit"，
后面所有和它相关的列都并到它身上，ratio 按
`nominal_weights[bit_idx] / nominal_weights[founding_bit_idx]` 算。

这意味着 founding bit 选谁、分母是谁，取决于列的输入顺序。对二进制 SAR 影响不大，
但对 radix≠2 冗余 SAR，同一组相关列如果排列不同，分配结果会不同。这是一个隐含假设：
调用方需要保证 bit 列顺序（MSB 在前）的一致性。

**3. 隐患 A（静默错误）：部分 bit 不翻 → weight 被强制设 0**

当输入幅度太小，某些低位从不翻转，这些列在 Case A 被判为 constant、drop，
恢复时被强制 `weight=0`：

```python
weights_recovered[bit_to_col_map < 0] = 0.0
```

实测：4-bit SAR，幅度只够激励高位，低位信息不足被 merge：

```text
calibrated weights = [0.5333, 0.2667, 0.1333, 0.0667]
```

数学上可辩护（静默 bit 对动态信号贡献 0），但工程上危险：用户拿到一组看似
"校准成功"的权重，没有任何告警，重建却是错的。这比崩溃更糟，因为崩溃至少让人
知道有问题。

**4. 隐患 B（确定 bug）：全秩亏 → IndexError 崩溃**

当输入导致所有 bit 列都 constant（比如平 DC 输入，或幅度太小一个 bit 都不翻），
所有列被 drop，`bits_effective` 变成 0 列。然后 `_recover_rank_deficiency`
在空数组上索引：

```text
IndexError: index 0 is out of bounds for axis 0 with size 0
```

实测：平 DC 输入（toggle counts `[4096, 0, 0, 0]`）直接崩溃，没有有意义的错误
提示。建议在 `_patch_rank_deficiency` 末尾加 guard：

```python
if bits_effective.shape[1] == 0:
    raise ValueError(
        "No independent bit columns found; input has insufficient bit activity. "
        "Increase input amplitude so all bits toggle."
    )
```

**5. 实测：真正的 rank deficiency 能被正确处理**

主线逻辑是对的。构造一个确定的 rank deficiency（复制一列，`col8 == col4`），
Case C 正确识别并合并：

```text
[DEBUG] Bit [8] is dependent. Merging into effective column [4] with weight ratio 1.0000.
w[4]=0.03132  w[8]=0.03132  ratio=1.0000  (joint sum 恢复正确)
```

所以问题不在主线算法，而在边界 case 的健壮性：静默 weight=0 应该 warning，
全秩亏应该 raise 有意义的错误。

### 9. column scaling：给最小二乘换一个更舒服的坐标系

先不要从 ADC 想起。先看一个最普通的最小二乘问题：

```text
y ≈ A @ w
```

如果 `A` 的某些列数值很大，另一些列数值很小，例如：

```text
col1 ≈ 1,000,000
col2 ≈ 0.001
```

数学上，精确实数运算仍然能解。但计算机用的是有限精度浮点数，列尺度差太大时，
最小二乘求解会更容易受舍入误差影响。column scaling 的直觉就是：

```text
先把每一列缩放到差不多的数量级；
让求解器在更好的数值坐标系里解问题；
解完以后，再把缩放补回原来的权重尺度。
```

#### 9.1 最小数学模型

假设只看 bit matrix 部分：

```text
y ≈ B @ w
```

对每一列做缩放：

```text
B_scaled[:, j] = B[:, j] * scale[j]
```

写成矩阵就是：

```text
B_scaled = B @ D
D = diag(scale[j])
```

求解器实际解的是：

```text
y ≈ B_scaled @ alpha
  = B @ D @ alpha
```

而原始模型是：

```text
y ≈ B @ w
```

所以两者对应关系是：

```text
w = D @ alpha
```

也就是：

```text
列乘了多少，最后权重要按同样关系补回去。
```

这一步不是改变 ADC 物理模型，而是换一个数值坐标系来求同一个线性问题。

#### 9.2 ADCToolbox 的实际代码

`_scale_columns_for_conditioning.py` 做的是 10 进制数量级缩放：

```python
col_extremes = np.vstack([np.max(bits, axis=0), np.min(bits, axis=0)])
max_vals = np.max(np.abs(col_extremes), axis=0)

bit_scales = np.floor(np.log10(max_vals + 1e-15))

near_zero_bits = (max_vals <= 1e-15)
bit_scales[near_zero_bits] = 0

bits_effective = bits * (10.0 ** (-bit_scales))
```

含义是：

```text
看每一列最大绝对值大约是 10 的几次方；
把这一列乘 10^(-bit_scale)，拉回到 O(1) 附近。
```

例子：

```text
max = 1000  -> bit_scale = 3   -> 这一列乘 10^-3
max = 0.01  -> bit_scale = -2  -> 这一列乘 10^2
max = 1     -> bit_scale = 0   -> 不动
max = 0     -> near-zero guard -> bit_scale 设回 0
```

求解后，`_recover_columns_for_conditioning.py` 再恢复：

```python
w_raw = coeffs[:bit_width_effective]
w_normalized = w_raw / norm_factor
w_physical_eff = w_normalized * (10.0 ** (-bit_scales))
```

为什么恢复也是乘 `10^(-bit_scales)`？因为前面列已经乘过：

```text
scale = 10^(-bit_scales)
```

求解器得到的是 scaled 坐标下的 `alpha`，原始权重是：

```text
w = scale * alpha
```

所以代码乘回同一个 `10^(-bit_scales)`。

#### 9.3 放到 SAR ADC 里怎么理解

SAR 的 raw output 是 bit decisions。bit matrix 长这样：

```text
sample   bit0  bit1  bit2  bit3
0        1     0     1     1
1        0     1     1     0
2        1     1     0     0
...
```

数字重构是：

```text
aout[n] = bit0[n] * w0 + bit1[n] * w1 + bit2[n] * w2 + ...
```

这里要特别小心一个常见误解：

```text
MSB 大、LSB 小，体现在 weights 里；
不体现在 bit columns 的数值大小里。
```

无论 MSB 还是 LSB，普通 SAR bit column 本身都只是：

```text
0 或 1
```

所以对纯 0/1 的 SAR bit matrix：

```text
max(abs(B[:, j])) = 1
bit_scales[j] = floor(log10(1)) = 0
B_scaled = B
```

也就是说，在普通 SAR 校准里，column scaling 通常是 no-op：

```text
它不会解决 16-bit SAR 的权重跨度问题；
因为 1/2, 1/4, ..., 1/32768 的跨度在 weights 里，
不在 bits 的列值里。
```

#### 9.4 它什么时候会真的动手

它主要是给 rank patch 之后的 effective columns 做防御。

上一节讲过，Case C 会把 dependent column 合并到已有 effective column：

```python
bits_effective[:, col_idx] += col * bit_weight_ratios[bit_idx]
```

合并后，effective column 不一定还是简单 0/1。它可能变成：

```text
0 或 2
0 或 3
0 或 12
```

如果最大值跨过 10 的数量级，比如 `max=12`：

```text
bit_scale = floor(log10(12)) = 1
这一列乘 10^-1
```

这样可以避免某个合并列比其他列大一个数量级以上。

但要注意，这个实现是 coarse decade scaling：

```text
max = 3.9 -> bit_scale = 0 -> 不缩放
max = 9.9 -> bit_scale = 0 -> 不缩放
max = 10  -> bit_scale = 1 -> 缩放
```

所以它不是精细归一化，也不是每次 rank patch 后都一定明显生效。

#### 9.5 它解决什么，不解决什么

column scaling 能缓解的是：

```text
列尺度悬殊
```

也就是某些列的长度比其他列大很多或小很多。

但它不能解决：

```text
列之间高度相关；
bit column 不翻转；
bit matrix rank deficient；
输入没有充分激励低位；
冗余 SAR 因 sub-radix / repeated weight 造成的近相关性。
```

原因是：scaling 只改变列的长度，不改变列的方向。如果两列几乎平行：

```text
B[:, i] ≈ B[:, j]
```

把其中一列乘 10，也不会让它产生新的独立信息。

可以这样记：

```text
列太大/太小       -> scaling 可能有用
列太像/不可区分    -> scaling 治不了
列不翻            -> scaling 治不了
```

所以对 radix≠2 的冗余 SAR，如果条件数爆炸主要来自列相关性，column scaling
不会让这个病态消失。真正要看的仍然是：

```text
rank / singular values；
bit activity；
输入幅度和覆盖范围；
冗余结构；
训练 capture 和验证 capture 是否独立。
```

#### 9.6 最终意义

在本库里，column scaling 的准确定位是：

```text
低成本的数值防御；
对普通 0/1 SAR bit matrix 基本是 no-op；
对 rank-patch 后出现明显数量级差异的 effective columns 可能有帮助；
不负责解决 SAR 校准的主要可辨识性问题。
```

因此不要把它理解成：

```text
解决 SAR 条件数问题的关键技巧
```

更应该理解成：

```text
如果 patched design matrix 某些列真的大很多或小很多，
它帮最小二乘求解器把列尺度拉回可控范围；
如果主要问题是 rank / correlation / excitation，
它不会创造新信息。
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
  返回值是 list；单个 capture 时使用 cal["calibrated_signal"][0]。

ideal:
  拟合模型重构出来的 reference sine / harmonic model。
  返回值同样是 list。

error:
  calibrated_signal 去掉 offset 后与 ideal 的差。
  返回值同样是 list。

refined_frequency:
  最终使用或估计出的 normalized frequency。

snr_db / enob:
  基于内部拟合误差计算的性能摘要。
```

实际验证时，不要只看返回的 `enob`。更稳的做法是：

```python
calibrated = cal["calibrated_signal"][0]
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

这里的 `actual_weights` 是行为仿真里用于模拟转换的 actual analog weights；它是仿真真值，
不等于真实芯片上可直接观测到的物理电容答案。

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

典型调用要先明确你要验证什么。

如果是纯 mismatch 仿真、测试源已知干净，或想做 harmonic sensitivity baseline：

```python
cal_h1 = calibrate_weight_sine(
    bits,
    freq=fin_bin / n_samples,
    nominal_weights=nominal_weights,
    harmonic_order=1,
)

weights_calibrated = cal_h1["weight"]
signal_calibrated = cal_h1["calibrated_signal"][0]  # single capture
```

如果训练源可能带 H2/H3，且你希望把这些看作 source/test-chain nuisance：

```python
cal_h3 = calibrate_weight_sine(
    bits,
    freq=fin_bin / n_samples,
    nominal_weights=nominal_weights,
    harmonic_order=3,
)
```

如果有多条 capture，更推荐共享 weights、每条 capture 使用独立 harmonic nuisance：

```python
cal_multi = calibrate_weight_sine(
    [bits_f1, bits_f2, bits_f3],
    freq=[f1, f2, f3],
    nominal_weights=nominal_weights,
    harmonic_order=3,
)
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
3. _patch_rank_deficiency：处理恒定列和线性相关列（注意全秩亏崩溃、静默 weight=0 两个隐患）。
4. _scale_columns_for_conditioning：对 rank-patch 后的非 0/1 列做防御性尺度归一化（对纯 0/1 bits 是 no-op）。
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

并对 unit-cap-scaled mismatch sigma 做 sweep。每个 sigma 下跑 32 次 Monte Carlo。

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
- `harmonic_order>1` 带有 source/test-chain nuisance 假设；它可以保护权重不被源谐波污染，
  也可能削弱 mismatch harmonic 对权重的约束。
- 单个 sine capture 不能自动分辨 H2/H3 来自源还是 ADC；更实际的做法是比较 `H=1`
  和 `H=3` 的权重差异，判断 harmonic attribution 歧义是否已经影响 weights。
- multi-capture 本身只能缓解来源混淆；更干净的是 multi-capture + 每个 capture 独立
  harmonic nuisance + shared weights。
- 校准结果和 `actual_weights` 同尺度接近是仿真里的好现象；真实芯片上通常不知道
  `actual_weights`，而且校准权重的绝对尺度还取决于输入/输出归一化约定。
- 如果输入幅度太小，某些 bit 没有充分翻转，对应权重很难估。
- 如果 bit matrix rank deficient，样本再多也不一定能独立估计所有权重。
- **bit 不充分翻转时，`_patch_rank_deficiency` 会把静默列 drop 并把对应权重设 0（静默错误，无告警）；如果所有列都静默（如平 DC 输入），会直接 IndexError 崩溃。** 见第 8 节隐患 A/B。
- 如果随机噪声已经主导，权重校准不会让 SNR 大幅提升。
- 如果只在训练 capture 上验证，很容易把 overfitting 当成校准成功。
- `nominal_weights` 在 rank deficiency 修补时会影响权重分配，不只是装饰参数。
- `column scaling` 对纯 bits 矩阵是 no-op（bits 恒为 0/1）；它治不了 radix 冗余 SAR 的相关性病态，只是 rank-patch 重 merge 后的防御性处理。见第 9 节补充。
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
6. `harmonic_order` 的意义是什么？为什么它不是“越高越好”？
7. 为什么 capacitor mismatch 适合校准，而 thermal noise 不适合逐次校准？
8. 什么情况下 bit matrix 会 rank deficient？
9. `_patch_rank_deficiency` 为什么要用 nominal weight ratio 把 dependent bit 分回去？全秩亏或部分 bit 静默时分别会发生什么？
10. 为什么训练数据上 ENOB 变好不等于校准结论可信？
11. 为什么 multi-capture + per-capture harmonic nuisance 比单纯 multi-capture 更干净？
12. `_scale_columns_for_conditioning` 对纯 bits 矩阵为什么是 no-op？它治得了 radix 冗余 SAR 的条件数爆炸吗，为什么？

这些问题如果能讲清楚，就可以进入 Stage 07：从“会校准”进入“会判断校准是否可信”。
