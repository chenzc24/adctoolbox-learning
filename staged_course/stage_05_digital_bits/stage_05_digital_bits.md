# Stage 05：Digital Output 与 bit matrix 诊断

## 本阶段如何承接 Stage 04

Stage 04 已经把 SAR ADC 的行为模型讲成了这条链：

```text
vin
  -> sar_convert(vin, actual_analog_weights)
  -> bits
  -> sar_reconstruct(bits, digital_weights)
  -> aout
```

Stage 02 和 Stage 03 主要看的是 `aout`：

```text
aout -> spectrum / residual / PDF / ACF / error by value / error by phase
```

Stage 05 则故意停在中间的 `bits` 上：

```text
bits.shape == (n_samples, n_bits)
```

原因很简单：

```text
aout 是 bits 加权求和后的结果；
bits 才更接近 ADC 内部逐位比较器决策的原始记录。
```

如果只看 `aout`，很多问题已经被权重求和混在一起；如果看 `bits`，你能直接问：

```text
哪一位在翻转？
哪一位几乎不动？
权重比例是不是符合架构预期？
冗余位是否给了足够 correction margin？
低位增加后是否真的带来有效性能？
```

这就是 Stage 05 的位置：它不是替代频谱和 residual，而是把诊断视角下沉到 raw digital output。

## 本阶段目标

学完本阶段，你应该能解释：

- 为什么 ADC raw digital output 可以表示成 bit matrix。
- `bit activity`、`weight radix`、`overflow`、`ENOB sweep` 各自检查什么。
- 为什么 bit matrix 诊断比只看 reconstructed waveform 更接近 SAR 内部状态。
- 为什么 `analyze_weight_radix` 不是 DNL/INL 证明，只是权重列表诊断。
- 为什么 `analyze_enob_sweep` 观察的是 bit 子集对频谱性能的贡献，不是重新发明校准。
- 为什么校准前必须检查 raw bits 是否提供了足够可观测性。

如果 Stage 05 不稳，Stage 06 的 `calibrate_weight_sine` 很容易被误解成“万能拟合器”。实际上，校准只能利用 `bits` 里已经存在的信息；如果某些 bit 没有翻转、bit 列高度相关、输入覆盖不足，后面的最小二乘就会不稳定。

## 对应孙老师课件主线

本阶段主要承接孙老师课件中的几条线：

```text
ch3  ADC 性能指标：
     DNL / INL / SNR / SNDR / ENOB / SFDR / THD 都是观察真实 ADC 的语言。

ch4  Nyquist DAC 基础：
     SAR 内部 CDAC 的 bit weight 不准，会变成 ADC 的阈值错误和线性度问题。

ch12 SAR ADC：
     SAR 的每一位都是一次 DAC trial + comparator decision。

ch17 数据转换器测试：
     性能测试不只是“拿到一个数字”，还要知道测试条件、输入覆盖和数据质量。
```

Stage 05 把这些观点翻译成 ADCToolbox 里的数据结构：

```text
孙老师课件里的 code、transition、bit weight、testing
  -> 本库里的 bits、weights、activity、radix、overflow、ENOB sweep
```

## 初学者先抓住的主线

先记住一句话：

```text
bit matrix 是 ADC 对输入电压做出的一串离散判断。
```

每一行是一帧转换结果：

```text
bits[n, :] -> 第 n 个采样点的完整 bit decision vector
```

每一列是一位 ADC 决策在整个采样窗口里的历史：

```text
bits[:, i] -> 第 i 位在所有样本上的 0/1 变化
```

所以 Stage 05 的阅读方式是“按列看”：

```text
看一列的平均值       -> bit activity
看相邻列权重比例     -> radix
看剩余低位能否覆盖   -> overflow / residue distribution
看逐步增加列后的指标 -> ENOB sweep
```

和 Stage 02/03 的区别：

```text
Stage 02/03:
  aout[n] 是时间序列，主要问频谱和 residual 长什么样。

Stage 05:
  bits[n, i] 是二维矩阵，主要问每一位是否在合理工作。
```

## 一个 bit matrix 小例子

假设 4 个采样点、3-bit SAR：

```text
B =
sample0: [0, 0, 1]
sample1: [0, 1, 0]
sample2: [1, 0, 0]
sample3: [1, 1, 0]
```

如果权重是：

```text
w = [4, 2, 1]
```

重构结果是：

```text
y = B @ w
  = [1, 2, 4, 6]
```

逐列看 activity：

```text
MSB:  [0, 0, 1, 1] -> 2/4 = 50%
bit1: [0, 1, 0, 1] -> 2/4 = 50%
LSB:  [1, 0, 0, 0] -> 1/4 = 25%
```

这说明：

```text
activity 是按列统计的，不是按样本统计的。
```

如果只看 `y = [1, 2, 4, 6]`，你能看到输出大小；但看 `B`，你还能知道：

```text
LSB 在这段数据里很少为 1；
MSB 和 bit1 翻转比较均衡；
这个输入窗口可能没有充分激励所有 code。
```

这就是 raw bits 的价值。

## 数学需要补什么

### 1. bit matrix 的维度和物理含义

SAR ADC 每个样本输出一个 bit vector：

```text
b[n] = [b0[n], b1[n], ..., bM-1[n]]
```

对 `N` 个样本，堆成矩阵：

```text
B =
[
  b[0]
  b[1]
  ...
  b[N-1]
]
```

shape 是：

```text
B.shape == (N, M)
```

在 ADCToolbox 中通常写作：

```python
bits.shape == (n_samples, n_bits)
```

约定：

```text
bits[:, 0]  -> MSB
bits[:, -1] -> LSB
```

对 SAR 来说，bit matrix 不只是普通二进制编码，它记录了每个采样点在每个 bit trial 中的比较器决策。它更接近 Stage 04 的 `sar_convert` 内部循环：

```text
for each bit j:
    v_test = v_dac + weights[j]
    bit = vin >= v_test
```

所以读 `bits` 时要一直带着电路画面：

```text
一列 bit = 某一个 CDAC trial weight 在整个输入窗口上的比较结果。
```

### 2. 数字重构：bit matrix 被压成 waveform

给定权重：

```text
w.shape == (M,)
```

数字重构是：

```text
y = B @ w
```

逐样本写：

```text
y[n] = b0[n] * w0 + b1[n] * w1 + ... + bM-1[n] * wM-1
```

shape 变化：

```text
(N, M) @ (M,) -> (N,)
```

这一步有两个后果：

```text
1. 好处：二维 bit decision 被变成一维 waveform，可以做 FFT / residual。
2. 代价：每一位的问题被加权混合，单独 bit 的异常不再直观。
```

Stage 05 做的事，就是在重构之前或重构旁边看原始矩阵。

### 3. bit activity：按列求 1 的比例

第 `i` 位的 activity 定义为：

```text
activity_i = mean(B[:, i]) * 100%
```

因为 `B[:, i]` 只有 0 和 1，所以均值就是“这一位为 1 的比例”。

对应 ADCToolbox 代码 `analyze_bit_activity.py`：

```python
bit_usage = np.mean(bits, axis=0) * 100
```

这里的 `axis=0` 很重要：

```text
axis=0 -> 沿样本方向求平均，得到每一列 bit 的 activity。
```

#### 为什么很多时候期待接近 50%

如果输入是一条以 mid-scale 为中心、幅度合适、覆盖范围良好的正弦，那么很多 bit 会在观察窗口里接近一半时间为 0、一半时间为 1。

直觉上：

```text
输入在某个阈值两侧都充分出现
-> 这一位既有 0，也有 1
-> activity 接近 50%
```

但这不是数学定理，更不是“好 ADC 的充分条件”。

activity 受输入分布影响很大。例如：

```text
输入 DC 偏高:
  高位更容易为 1，activity 可能整体偏高。

输入幅度太小:
  某些高位或低位可能很少翻转。

输入 clipping:
  高位 activity 可能异常，且端点 code 过度集中。

输入不是正弦而是 ramp:
  activity 模式又会不同。
```

所以 activity 的正确用法是：

```text
先检查“这段数据有没有充分激励 bit”，不要直接把 50% 当作好坏判据。
```

### 4. weight radix：看权重比例是否符合架构预期

纯二进制 SAR 的权重近似：

```text
[1/2, 1/4, 1/8, 1/16, ...]
```

相邻权重比例是：

```text
radix_i = |w[i-1]| / |w[i]|
```

理想二进制：

```text
radix ≈ 2
```

sub-radix 或冗余结构：

```text
radix < 2
```

ADCToolbox 的 `analyze_weight_radix.py` 直接按这个公式算：

```python
radix[i] = abs_weights[i-1] / abs_weights[i]
```

注意它用的是绝对值：

```text
abs(weight)
```

所以即使某些 trim weight 是负的，也会按幅度参与 radix / effective span 分析。

#### radix 诊断能说明什么

它能说明：

```text
权重列表是不是接近二进制；
是否存在 sub-radix / redundancy；
某一位权重是否异常跳变；
校准后权重形状是否符合架构直觉。
```

它不能单独证明：

```text
DNL 合格；
INL 合格；
没有 missing code；
SAR decision 一定可达；
比较器和采样噪声足够小。
```

这是代码 docstring 已经明确提醒的边界：

```text
effres is a theoretical resolution estimate from the supplied weight
dynamic range, not a missing-code/DNL proof.
```

所以 Stage 05 要建立一个谨慎习惯：

```text
radix 是权重列表诊断，不是完整 ADC 线性度签核。
```

### 5. effective resolution：只看权重跨度的估计

`analyze_weight_radix` 还返回：

```text
effres = log2(sum(abs_w_sig) / min(abs_w_sig) + 1)
```

直觉是：

```text
把显著权重按最小显著权重归一化成 LSB 单位；
看这些权重一共能覆盖多少个 LSB；
再换算成 bits。
```

代码里还有一个“显著权重集合”的筛选：

```text
把 abs(weights) 从大到小排序；
如果相邻权重比值第一次 >= 3，就认为后面的很小权重可能是 trim/noise tail；
只用前面的 significant weights 算 effres。
```

这对包含小 trim 权重或负权重的校准结果有用，但它仍然只是：

```text
weight-list span
```

不是：

```text
真实 ADC 有效位数
```

真实有效位数仍要靠动态测试，比如 `analyze_spectrum` 或 `quick_sndr`。

### 6. residue / overflow：看剩余低位是否有修正余量

对 SAR 来说，每一个 bit decision 都会留下一个剩余误差：

```text
residue after k bits
  = input - sum(first k accepted bit weights)
```

如果结构是严格二进制，前面某一位做错，后面的低位总权重可能不够修回来。

冗余 SAR 的核心思想是：

```text
让某些权重比例小于 2，给后续低位留下 correction margin。
```

ADCToolbox 的 `analyze_overflow.py` 用一种“剩余 bit 段”的方式看风险。对每个 bit 位置 `ii`：

```python
tmp = raw_code[:, ii:] @ weight[ii:]
sum_weight = np.sum(weight[ii:])
data_decom[:, ii] = tmp / sum_weight
```

也就是：

```text
从当前 bit 到 LSB 的加权和
再除以这段剩余权重总和
```

于是得到归一化 residue distribution：

```text
data_decom[:, ii] <= 0  -> underflow side
data_decom[:, ii] >= 1  -> overflow side
```

函数返回：

```text
range_min
range_max
ovf_percent_zero
ovf_percent_one
```

这些量回答的问题是：

```text
在每一个 bit 位置，剩余 bit 的组合有没有贴到或越过边界？
```

如果某些 bit 位置出现大量 overflow / underflow，通常说明：

```text
输入范围太激进；
权重设计没有足够 redundancy；
校准权重异常；
前面 bit decision 的错误已经超过后续可修正范围。
```

### 7. residual scatter：看不同 bit stage 的残差结构

`plot_residual_scatter.py` 做的是 partial-sum residual：

```text
res_k[n] = signal[n] - bits[n, :k] @ weights[:k]
```

当 `k=0`：

```text
res_0 = signal
```

当 `k=M`：

```text
res_M = signal - full reconstruction
```

它把不同阶段的残差互相画 scatter，例如：

```text
res after bit 1 vs res after all bits
res after bit 2 vs res after all bits
```

这类图可以看：

```text
残差是否随某一阶段形成结构；
某些 bit stage 是否出现非线性模式；
冗余结构是否把前面残差压回可修正范围。
```

它不是 Stage 03 的 sine residual 图，而是更贴近 bit-stage 的 residual。

### 8. ENOB sweep：逐步增加 bit 子集看贡献

`analyze_enob_sweep.py` 的核心流程是：

```text
1. 先用所有 bits 跑一次 calibrate_weight_sine，得到 weights_all。
2. 对 n_bits = 1, 2, ..., M：
   bits_subset = bits[:, :n_bits]
   weights_subset = weights_all[:n_bits]
   calibrated_signal = bits_subset @ weights_subset
   用 analyze_spectrum 算 ENOB。
```

代码对应：

```python
result = calibrate_weight_sine(bits, freq=freq, harmonic_order=harmonic_order)
weights_all = result["weight"]

for n_bits in range(1, m_bits + 1):
    bits_subset = bits[:, :n_bits]
    weights_subset = weights_all[:n_bits]
    calibrated_signal = bits_subset @ weights_subset
    spectrum_result = analyze_spectrum(calibrated_signal, ...)
```

注意：

```text
它不是每个 bit 数都重新校准一次；
它是先全量校准，再看使用前 n 个 bit 重构时性能如何变化。
```

所以 ENOB sweep 的正确解释是：

```text
这些 bit 在当前校准权重下，对最终动态性能的边际贡献如何。
```

常见形态：

| sweep 形状 | 可能解释 |
|---|---|
| ENOB 随 bit 数上升 | 低位确实带来更多有效信息 |
| 后面进入平台 | 随机噪声、失真或测试条件已经主导 |
| 增加低位反而下降 | 低位主要是噪声、权重估计差、或输入未充分激励 |
| 某一位加入后突变 | 该 bit 权重/活动/决策可能异常 |

### 9. bit matrix 和可观测性

Stage 06 会把校准写成最小二乘：

```text
B @ w ≈ sine
```

这里的 `B` 就是 Stage 05 的 bit matrix。

如果某两列总是相同：

```text
B[:, i] == B[:, j]
```

那么仅凭这段数据无法区分：

```text
w_i 变大
```

和：

```text
w_j 变大
```

因为它们在所有样本里总是一起出现。

如果某一列恒定：

```text
B[:, i] 全是 0 或全是 1
```

那这一位没有提供 AC 信息。它可能是：

```text
dead bit；
输入没有覆盖到；
测试幅度太小；
数据预处理错了；
或该 bit 本身被架构约束住。
```

所以 Stage 05 的根本意义是：

```text
在做校准之前，检查 bit matrix 是否真的含有足够独立信息。
```

## 电路需要理解什么

### 1. raw bits 是比较器决策的直接证据

孙老师 ch12 讲 SAR 的基本过程：每一位都是一次“DAC 生成假设电压，再比较”的过程。

在代码中：

```text
bit = (vin_norm + noise >= v_test)
```

在电路中：

```text
comparator 判断 vin_sampled 是否大于 CDAC trial voltage
```

所以 raw bits 比 `aout` 更接近电路状态：

```text
bits[:, 0] 反映 MSB trial 是否经常被接受；
bits[:, 1] 反映第二位 trial 是否经常被接受；
bits[:, -1] 反映 LSB 附近的小决策是否有足够活动。
```

如果一个 bit 长期不翻转，不要急着把原因归咎于算法。先问：

```text
输入有没有覆盖对应阈值？
该 bit 的 CDAC weight 是否异常？
比较器是否有 offset？
输入是否 clipping 或 DC 偏置？
数据读取 bit order 是否反了？
```

### 2. bit activity 连接输入分布和阈值位置

从电路角度看，某一位的 activity 由两件事决定：

```text
1. 输入信号在时间上如何分布。
2. 该 bit trial threshold 在输入轴上落在哪里。
```

如果输入正弦以 mid-scale 为中心，且没有 clipping，MSB 往往接近 50%。

如果 MSB activity 明显偏高：

```text
可能是输入 DC 偏高；
可能是 comparator offset；
可能是 full-scale / quant_range 设置不一致；
也可能是数据已经被截断。
```

如果低位 activity 异常低：

```text
可能是输入幅度不足；
可能是低位被噪声淹没；
可能是数据长度太短，没有充分覆盖 code；
也可能是 bit extraction 错误。
```

### 3. weight radix 连接 CDAC 架构

孙老师 ch4 强调：SAR 内部 CDAC 本质上是 DAC，DAC 的权重不准会变成 ADC 的阈值错误。

所以权重列表不是抽象数字，而是：

```text
CDAC capacitor ratio
```

或：

```text
数字后端用于重构的 bit weight
```

严格二进制权重：

```text
8C, 4C, 2C, 1C
```

对应 radix：

```text
2, 2, 2
```

冗余或 sub-radix：

```text
8C, 4C, 4C, 2C, 1C
```

或更平滑的 radix ~1.8 权重列表，目的不是“让权重更漂亮”，而是：

```text
给错误决策留下后续可修正空间。
```

### 4. overflow 是 redundancy margin 的症状

严格二进制 SAR 的每一步很紧：

```text
前面 bit 一旦错得太大，后面低位总和可能不够补。
```

冗余 SAR 放松这个约束：

```text
前面 trial 不再刚好吃掉半个范围；
后面剩余权重有一点“余量”。
```

所以 overflow 检查背后的物理问题是：

```text
剩余低位是否还能覆盖前面决策留下的 residue？
```

如果不能，数字校准也很难完全修复，因为 bit decision 已经把输入映射到了不可恢复的码区。

### 5. raw bits 不能替代完整测试

bit matrix 很有价值，但它也有边界：

```text
它能告诉你 bit 如何翻转；
不能单独告诉你输入源是否纯净；
不能单独证明 DNL/INL 合格；
不能单独区分所有模拟非理想；
不能替代 spectrum / residual / static test。
```

孙老师 ch17 的测试观点在这里非常重要：

```text
测试条件就是指标的一部分。
```

同一段 raw bits，在不同输入幅度、频率、窗口和重构权重下，可能得到不同结论。

## 本库对应代码

Digital output 分析：

```text
python/src/adctoolbox/dout/analyze_bit_activity.py
python/src/adctoolbox/dout/analyze_weight_radix.py
python/src/adctoolbox/dout/analyze_overflow.py
python/src/adctoolbox/dout/analyze_enob_sweep.py
python/src/adctoolbox/dout/plot_residual_scatter.py
```

SAR 行为模型：

```text
python/src/adctoolbox/models/sar.py
```

校准函数：

```text
python/src/adctoolbox/calibration/calibrate_weight_sine.py
```

官方示例：

```text
python/src/adctoolbox/examples/05_debug_digital/exp_d11_bit_activity.py
python/src/adctoolbox/examples/05_debug_digital/exp_d12_sweep_bit_enob.py
python/src/adctoolbox/examples/05_debug_digital/exp_d13_weight_scaling.py
python/src/adctoolbox/examples/05_debug_digital/exp_d14_overflow_check.py
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

本地完整 demo 输出：

```text
learning/adctoolbox-learning/outputs/whole_workflow/04_digital_debug_bits_and_weights.png
```

## 对应 API

```python
from adctoolbox.dout import analyze_bit_activity
from adctoolbox.dout import analyze_weight_radix
from adctoolbox.dout import analyze_overflow
from adctoolbox.dout import analyze_enob_sweep
from adctoolbox.dout import plot_residual_scatter
```

常见输入：

```python
bit_usage = analyze_bit_activity(bits)
radix_info = analyze_weight_radix(weights)
range_min, range_max, ovf0, ovf1 = analyze_overflow(bits, weights)
enob_sweep, n_bits_vec = analyze_enob_sweep(bits, freq=fin_bin / n_samples)
```

## 读代码时具体看什么

### 1. `analyze_bit_activity.py`

核心只有一行：

```python
bit_usage = np.mean(bits, axis=0) * 100
```

读它时确认：

```text
axis=0 是按列统计；
返回值长度等于 bit 数；
plot 里高亮的是偏离 50% 最大的 bit；
plot 默认 y 轴是 40% 到 60%，非常大的偏离可能需要自己调整图。
```

### 2. `analyze_weight_radix.py`

重点追：

```text
abs_weights
radix
abs_w_sorted
sig_break
wgtsca
effres
```

你要能说清：

```text
radix = 相邻输入顺序权重的绝对值比；
effres = 显著权重集合的 span；
negative weights 只影响符号，radix/effres 看幅度；
effres 不证明真实 ADC 没有 missing code。
```

### 3. `analyze_overflow.py`

重点追：

```text
tmp = raw_code[:, ii:] @ weight[ii:]
sum_weight = np.sum(weight[ii:])
data_decom[:, ii] = tmp / sum_weight
```

这里 `raw_code[:, ii:]` 表示：

```text
从当前 bit 到 LSB 的剩余 bit 段。
```

返回的两个百分比：

```text
ovf_percent_zero -> data_decom <= 0 的比例
ovf_percent_one  -> data_decom >= 1 的比例
```

读代码时还要注意 `ofb` 的约定：

```text
MATLAB convention: 1=LSB, M=MSB
Python index uses M - ofb
```

### 4. `analyze_enob_sweep.py`

重点追：

```text
result = calibrate_weight_sine(bits, ...)
weights_all = result["weight"]

bits_subset = bits[:, :n_bits]
weights_subset = weights_all[:n_bits]
calibrated_signal = bits_subset @ weights_subset
```

它的含义是：

```text
用同一组全量校准权重，观察前 n 个 bit 的重构性能。
```

不要误读成：

```text
每个 n_bits 都重新做了一次完整校准。
```

### 5. `plot_residual_scatter.py`

重点追：

```text
res_x = signal - bits[:, :x_bit] @ weights[:x_bit]
res_y = signal - bits[:, :y_bit] @ weights[:y_bit]
```

这说明它看的是：

```text
partial-sum residual between bit stages
```

不是 Stage 03 那种从 waveform 中拟合正弦再求 residual。

## 实验 1：运行本地完整 workflow

先从完整闭环看 Stage 05 的位置：

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

看输出图：

```text
E:\ADCToolbox\learning\adctoolbox-learning\outputs\whole_workflow\04_digital_debug_bits_and_weights.png
```

重点观察：

```text
左图 bit activity 哪一位偏离最大；
右图 calibrated weight radix 是否接近预期；
控制台 first four bit activities 和 weight_effres_bits。
```

## 实验 2：bit activity

运行官方示例：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d11_bit_activity.py
```

观察：

```text
哪些 bit 偏离 50%；
偏离最大的是 MSB 还是 LSB；
输入 DC 或 amplitude 改变时，activity 如何变化。
```

思考：

```text
如果输入 DC 从 0.5 改成 0.55，会发生什么？
如果输入 amplitude 太小，低位 activity 会如何？
如果输入 clipping，高位 activity 会如何？
```

## 实验 3：ENOB sweep

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d12_sweep_bit_enob.py
```

观察：

```text
使用更多 bit 时 ENOB 是否持续提升；
是否出现平台区；
最后几位是否带来负贡献。
```

如果出现平台，不要马上说“低位坏了”。先判断：

```text
是不是随机噪声底已经限制；
是不是输入没有充分激励低位；
是不是校准权重估计不稳定；
是不是 spectrum 设置导致指标不敏感。
```

## 实验 4：weight radix

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d13_weight_scaling.py
```

观察：

```text
radix 是否接近 2；
是否有 sub-radix；
是否有异常跳变；
effres 和 nominal bit 数是否接近。
```

记住：

```text
radix 图是权重形状图，不是频谱图。
```

## 实验 5：overflow check

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d14_overflow_check.py
```

观察：

```text
residue distribution 是否贴近 0 或 1；
某些 bit stage 是否出现高比例 overflow；
冗余结构是否比严格二进制更有余量。
```

## 实验 6：SAR mismatch Monte Carlo

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d16_sar_unit_cap_mismatch_mc.py
```

这个实验把 Stage 05 和 Stage 06/07 接起来：

```text
strict binary vs radix ~1.8 redundancy
unit-cap mismatch sigma sweep
32 次 Monte Carlo
before / after foreground sine calibration
```

重点不是某一条漂亮曲线，而是：

```text
看 ENOB 分布；
看 redundancy 在 mismatch 下是否更稳；
看校准前后差异是否符合 deterministic mismatch 的预期。
```

## 容易混淆的点

- `bits` 不是最终模拟波形，它是 raw digital decision matrix。
- bit activity 接近 50% 不代表 ADC 一定好，只代表这一位在当前输入下翻转比较均衡。
- bit activity 偏离 50% 不一定是坏事；也可能是输入 DC、幅度或测试信号分布导致。
- `radix=2` 只说明权重比例接近二进制，不说明 DNL/INL 一定合格。
- `effres` 是权重列表 span，不是动态 ENOB。
- `analyze_enob_sweep` 先全量校准，再截取前 n 个 bit 重构；不是每个 n 都重新校准。
- raw bits 如果已经缺少独立信息，后面校准很可能只是在拟合坏数据。
- 真实芯片上你通常不知道 `actual_weights`，只能通过 raw bits、测试输入和指标反推。

## 进入 Stage 06 前要带走什么

Stage 06 会把校准写成：

```text
B @ w ≈ sine
```

进入 Stage 06 前，你要先确认自己知道：

```text
B 是什么；
w 是什么；
B 的每一列是否提供了独立信息；
为什么某些 bit 不翻转会让权重不可观测；
为什么 radix / overflow / activity 是校准前的体检。
```

一句话总结：

```text
Stage 05 不是多学几个画图函数，而是学会在校准前检查 raw bits 是否值得信任。
```

## 阶段检查问题

1. 为什么 bit matrix 比 reconstructed waveform 更接近 ADC 内部状态？
2. `bits.shape == (N, M)` 中，行和列分别代表什么？
3. `analyze_bit_activity` 为什么用 `np.mean(bits, axis=0)`？
4. bit activity 偏离 50% 可能意味着哪些不同原因？
5. `radix=2` 和 `radix<2` 分别对应什么 ADC 权重结构？
6. 为什么 `analyze_weight_radix` 不能证明没有 missing code？
7. `analyze_overflow` 中 `raw_code[:, ii:] @ weight[ii:]` 的物理含义是什么？
8. ENOB sweep 出现平台时，可能有哪些解释？
9. 如果两个 bit 列完全相同，为什么无法独立估计它们的权重？
10. 为什么校准前要先检查 bits 是否合理？

如果这些问题答不稳，建议先不要进入 Stage 06。否则你会看到最小二乘矩阵，却不知道矩阵里的信息来自哪里。
