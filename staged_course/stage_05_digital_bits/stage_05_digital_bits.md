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

#### 这个量的意义

`effres` 的主要价值是做 **weight-list sanity check**。它不看输出波形、不看噪声、不看 harmonic，
只问一件事：

```text
这组显著数字权重的幅度跨度，大概像几 bit 的权重集合？
```

如果一个 12-bit SAR 的校准结果只给出 `effres ~= 9 bit`，这通常说明权重列表本身已经不健康，可能包括：

```text
后几位 bit 没有充分翻转；
训练输入覆盖不足；
bit column 高度相关，最小二乘病态；
某些低位权重被当成 trim/noise tail 排除了；
bit mapping、极性或归一化尺度可能有问题。
```

反过来，如果 `effres` 接近 nominal bit 数，只能说明：

```text
权重幅度 span 大致合理；
显著权重没有明显丢失；
校准出来的 weight list 在数量级上像预期架构。
```

它不能保证：

```text
真实 ADC ENOB 等于这个数；
DNL/INL 合格；
没有 missing code；
SAR decision 对所有输入都可达；
noise、jitter、comparator error 足够小。
```

所以它适合放在调试流程的前面：

```text
先用 effres / radix 检查权重列表有没有离谱；
再用 overflow / bit activity 检查 bit decision 覆盖和剩余修正余量；
最后用 spectrum / quick_sndr 看真实动态有效位数。
```

可以把它和 ENOB 区分成一句话：

```text
effres = 权重列表理论上覆盖了多少 levels；
ENOB   = ADC 动态输出实际还能分辨多少有效 bits。
```

### 6. residue / overflow：看剩余低位是否有修正余量

先区分两个容易混淆的对象：

```text
真实 analog / reconstruction residue:
  r_k[n] = input[n] - sum(first k accepted bit weights)

suffix-code distribution:
  z_i[n] = sum(bits from bit i to LSB) / sum(weights from bit i to LSB)
```

第一个需要 `input` 或 `signal`，第二个只需要 `raw_code` 和 `weight`。
`analyze_overflow.py` 做的是第二个：**剩余 bit 段的归一化 code distribution**，
不是直接计算真实 analog residue。

为什么这个量和 redundancy 有关？对 SAR 来说，前面某一位 trial 做错后，后续低位只能靠剩余权重补偿。
严格二进制权重几乎没有正的 overrange margin：

```text
w[i] ~= sum(w[i+1:]) + 1 LSB
```

如果第 `i` 位错过了太多，后面低位的所有组合也可能补不回来。
冗余 / sub-radix SAR 刻意让某些权重比例小于 2：

```text
sum(w[i+1:]) > w[i]
```

这样后续低位有额外 correction margin，可以吸收 comparator noise、settling error、
early decision error 等造成的偏差。

`analyze_overflow.py` 对每个 bit 位置 `ii` 计算：

```python
tmp = raw_code[:, ii:] @ weight[ii:]
sum_weight = np.sum(weight[ii:])
data_decom[:, ii] = tmp / sum_weight
```

数学上写成：

```text
B[n, j] = raw_code[n, j]
w[j]    = weight[j]

suffix_i[n] = Σ_{j=i}^{M-1} B[n, j] * w[j]
W_i         = Σ_{j=i}^{M-1} w[j]
z_i[n]      = suffix_i[n] / W_i
```

如果 `weight[ii:]` 全为正，且 bits 是 0/1，那么 `suffix_i[n]` 的理论范围就是：

```text
0 <= suffix_i[n] <= W_i
```

归一化以后：

```text
0 <= z_i[n] <= 1
```

也就是说，在这个标准正权重 SAR 情形下，`z_i[n]` **不会真正越过边界**，
只可能等于边界。图里的边界含义是：

```text
z_i[n] ~= 0  -> 剩余 bit 段贴到下边界，几乎没有向下修正余量
z_i[n] ~= 1  -> 剩余 bit 段贴到上边界，几乎没有向上修正余量
```

那为什么代码里还会检查：

```text
z_i[n] <= 0
z_i[n] >= 1
```

原因是 `analyze_overflow` 并没有强制输入一定满足“正权重 + 0/1 bit”的理想条件。
一旦权重里有负数、bit 不是 0/1 编码、或 suffix 权重和接近 0，`0` 和 `W_i`
就不再是实际可达范围的上下界。

例如：

```text
w = [1.0, -0.2]
W = sum(w) = 0.8

B = [1, 0] -> suffix = 1.0  -> z = 1.0 / 0.8  = 1.25
B = [0, 1] -> suffix = -0.2 -> z = -0.2 / 0.8 = -0.25
```

这里不是物理电容权重真的超过了自己的和，而是因为 `W = sum(weight)` 已经不是
“所有 bit 为 1 时的最大正边界”。对带符号权重来说，真实组合范围应该更接近：

```text
lower_bound = sum(min(w[j], 0))
upper_bound = sum(max(w[j], 0))
```

而不是简单的 `[0, sum(w)]`。所以对标准正权重 SAR，要把 `analyze_overflow`
主要理解成“贴边检查”；只有在带符号/异常输入下，才可能出现真正的越界数值。

用一个 3-bit 的例子看会更直观。假设列顺序是 MSB -> LSB：

```text
B[n, :] = [b2, b1, b0]
w       = [4,  2,  1]
```

那么三个 suffix distribution 分别是：

```text
i = 0: z_0[n] = (4*b2 + 2*b1 + 1*b0) / 7
i = 1: z_1[n] = (       2*b1 + 1*b0) / 3
i = 2: z_2[n] = (              1*b0) / 1
```

这里有一个容易混淆的点：**suffix 的单调性**和**suffix distribution 是否贴边**
不是同一个问题。

如果固定某一个样本 `n`，并且权重全为正，那么未归一化的 suffix sum 随着 `i`
从 MSB 往 LSB 走，确实是单调不增的：

```text
suffix_i[n] = B[n, i] * w[i] + suffix_{i+1}[n]
suffix_i[n] >= suffix_{i+1}[n]
```

因为往 LSB 走时只是把前面的非负项拿掉。
但 `analyze_overflow` 看的不是这条单样本轨迹是否单调，而是对每一个固定的 bit 位置 `i`，
看所有样本形成的一列分布：

```text
z_i[0], z_i[1], ..., z_i[N-1]
```

所谓“贴边”，指的是这列分布里有多少样本刚好落在该 suffix 段的可表达端点：

```text
z_i[n] = 0  -> 当前 bit 到 LSB 这一整段全为 0
z_i[n] = 1  -> 当前 bit 到 LSB 这一整段全为 1
```

还是用上面的 3-bit 例子：

```text
i = 1: z_1[n] = (2*b1 + b0) / 3

[b1, b0] = [0, 0] -> z_1 = 0
[b1, b0] = [1, 1] -> z_1 = 1
```

这和单调性不矛盾。单调性说的是同一个样本在不同 suffix 位置之间怎么变；
贴边说的是某一个 suffix 位置上，很多样本是否已经用到了这段剩余 code range
的最下端或最上端。

还有一个细节：归一化后的 `z_i` 本身不一定随着 `i` 单调，因为分母也在变：

```text
z_i[n]     = suffix_i[n] / W_i
z_{i+1}[n] = suffix_{i+1}[n] / W_{i+1}
```

`suffix_i` 和 `W_i` 都随 `i` 改变，所以不能把 `z_i` 当作一条必然单调的 residue 曲线。
最后一位尤其特殊：如果 bit 是 0/1，`z_{M-1}` 只能是 0 或 1，
所以 LSB suffix 的“贴边”是天然的，不应单独解读成故障。

`analyze_overflow` 不是把这三列完整返回，而是把每一列压缩成几个摘要统计量。

函数返回：

```text
range_min
range_max
ovf_percent_zero
ovf_percent_one
```

在正权重、且 `W_i > 0` 的常见 SAR 情形下，这些量不是额外的新概念，
而是直接从每一列 `z_i[n]` 的分布统计出来：

```text
range_min[i] = min_n z_i[n]
range_max[i] = max_n z_i[n]

ovf_percent_zero[i] = count(z_i[n] <= 0) / N * 100%
ovf_percent_one[i]  = count(z_i[n] >= 1) / N * 100%
```

也就是说，对每一个 bit 位置 `i`，函数先得到一条 suffix distribution：

```text
z_i[0], z_i[1], ..., z_i[N-1]
```

然后问四个问题：

```text
这条分布最低到哪里？        -> range_min[i]
这条分布最高到哪里？        -> range_max[i]
有多少样本贴到下边界 0？    -> ovf_percent_zero[i]
有多少样本贴到上边界 1？    -> ovf_percent_one[i]
```

这里的 `ovf_percent_zero/one` 名字有一点历史包袱。代码用的是：

```text
z_i[n] <= 0
z_i[n] >= 1
```

所以在标准正权重 SAR 情形下，它统计的是：

```text
贴到下边界或上边界的样本比例
```

在带符号/异常权重情形下，它也会把真正越界的样本算进去：

```text
z_i[n] < 0 或 z_i[n] > 1
```

这也是为什么在很低位的 suffix 上，特别是最后一位，很多样本天然会等于 0 或 1。
这本身不一定说明 ADC 已经坏了；它说明这个 suffix 段已经没有进一步的内部余量。
越靠前的 bit 位置如果也大量贴边，才更值得警惕，因为那意味着后续 bit 段很早就用满了可表达范围。

因此这些返回量回答的问题是：

```text
在每一个 bit 位置，从当前 bit 到 LSB 的 suffix code 是否经常贴到边界？
后续 bit 是否还有足够 margin 来吸收前面 decision 的误差？
```

如果某些 bit 位置出现大量贴边样本，或在非标准权重下出现越界样本，通常说明：

```text
输入范围太激进；
权重设计没有足够 redundancy；
校准权重异常；
前面 bit decision 的错误已经超过后续可修正范围。
```

#### `analyze_overflow.py` 代码流程展开

函数入口：

```python
def analyze_overflow(raw_code, weight, ofb=None, create_plot=True, ax=None, title=None):
```

输入约定是：

```text
raw_code.shape == (N, M)    # N 个样本，M 个 bit，列顺序默认 MSB -> LSB
weight.shape   == (M,)      # 每一列 bit 对应一个重构权重
```

代码先做基本整理：

```python
raw_code = np.asarray(raw_code)
weight = np.asarray(weight)

if raw_code.ndim == 1:
    raw_code = raw_code.reshape(-1, 1)

N, M = raw_code.shape

if len(weight) != M:
    raise ValueError(...)
```

这一步保证：

```text
每一列 bit 都有一个对应 weight；
后面可以做 raw_code[:, ii:] @ weight[ii:]。
```

接着分配中间矩阵和返回数组：

```python
data_decom = np.zeros((N, M))
range_min = np.zeros(M)
range_max = np.zeros(M)
ovf_percent_zero = np.zeros(M)
ovf_percent_one = np.zeros(M)
```

其中：

```text
data_decom[:, i] 保存 z_i[n]，也就是第 i 个 suffix 的归一化分布；
range_min/max 和 ovf_percent_* 是对 data_decom 每一列做统计。
```

核心循环是：

```python
for ii in range(M):
    tmp = raw_code[:, ii:] @ weight[ii:]
    sum_weight = np.sum(weight[ii:])
    data_decom[:, ii] = tmp / sum_weight
    range_min[ii] = np.min(tmp) / sum_weight
    range_max[ii] = np.max(tmp) / sum_weight
    ovf_percent_zero[ii] = np.sum(data_decom[:, ii] <= 0) / N * 100
    ovf_percent_one[ii] = np.sum(data_decom[:, ii] >= 1) / N * 100
```

逐行解释：

```text
raw_code[:, ii:]
  取从当前 bit 到 LSB 的所有列。

weight[ii:]
  取同一段剩余权重。

tmp
  每个样本的 suffix weighted sum。

sum_weight
  这个 suffix 段所有权重全为 1 时的最大可表示和。

tmp / sum_weight
  把 suffix weighted sum 归一化到 0..1 区间附近。

range_min/range_max
  只记录这个 suffix 分布的包络线。

ovf_percent_zero/one
  记录落到下/上边界的样本比例。
```

这段代码里 `range_min[ii] = np.min(tmp) / sum_weight` 的写法隐含了一个前提：

```text
sum_weight > 0
```

也就是常见 SAR 权重都是正的、剩余权重总和也是正的。此时：

```text
min(tmp) / sum_weight == min(tmp / sum_weight)
max(tmp) / sum_weight == max(tmp / sum_weight)
```

如果某个 suffix 的权重和为负，`min/max` 的方向会翻转；如果权重和接近 0，
归一化会被数值放大。这类情况下，`analyze_overflow` 仍会按代码执行，
但 `0..1 margin` 的物理解释就不再稳固。

所以 plot 里的红色包络线不是某个单样本轨迹，而是：

```text
每个 bit suffix distribution 的 min/max envelope。
```

`ofb` 参数只用于**选择哪一个 bit 位置的边界样本在图中高亮**：

```python
if ofb is None:
    ofb = M

ovf_zero = data_decom[:, M - ofb] <= 0
ovf_one = data_decom[:, M - ofb] >= 1
non_ovf = ~(ovf_zero | ovf_one)
```

这里沿用了 MATLAB 的 bit 编号习惯：

```text
ofb = M -> Python index 0，通常对应最左边/MSB suffix；
ofb = 1 -> Python index M-1，通常对应最右边/LSB suffix。
```

注意一个容易误读的点：

```text
ovf_percent_zero/one 是每个 bit 位置独立统计的返回值；
但图中蓝/红/黄散点的颜色，是根据指定 ofb 那一列的 boundary mask 来给所有列着色。
```

也就是说，返回数组回答的是：

```text
每个 bit 位置各自有多少边界样本？
```

而图中颜色还额外回答：

```text
在指定 ofb 位置贴到边界的那些样本，
或者在非标准权重下越过边界的那些样本，
它们在其它 suffix 位置上的分布轨迹长什么样？
```

这就是为什么 `ofb` 不改变 `range_min/range_max/ovf_percent_*` 的计算逻辑，
但会改变图里哪些点被标成红色或黄色。

边界条件也要记住：

```text
1. `analyze_overflow` 没有输入 `signal`，所以不是 vin - partial_sum 的真实 residue。
2. 如果权重有负数，或 `sum(weight[ii:])` 接近 0，`0..1` 的 margin 解释会变弱。
3. 它最适合 MSB-to-LSB、正权重、SAR / redundant SAR 风格的 bit matrix。
4. 它是 redundancy margin diagnostic，不是 DNL/INL 或 missing-code 证明。
```

### 7. residual scatter：看不同 bit stage 的残差结构

`plot_residual_scatter.py` 才是真正用 `signal` 做 partial-sum residual 的工具。
它的问题是：

```text
减掉前 k 个 bit 的重构贡献后，还剩下什么误差？
这个中间误差和最终误差之间有没有结构关系？
```

数学定义：

```text
r_k[n] = signal[n] - Σ_{j=0}^{k-1} bits[n, j] * weights[j]
```

当 `k=0`：

```text
res_0 = signal
```

当 `k=M`：

```text
res_M = signal - full reconstruction
```

代码对应：

```python
if x_bit == 0:
    res_x = signal.copy()
else:
    res_x = signal - bits[:, :x_bit] @ weights[:x_bit]

if y_bit == 0:
    res_y = signal.copy()
else:
    res_y = signal - bits[:, :y_bit] @ weights[:y_bit]
```

然后它把不同阶段的 residual 互相画 scatter，例如：

```text
res after bit 1 vs res after all bits
res after bit 2 vs res after all bits
```

这类图可以看出：

```text
某个 bit stage 之后的残差是否仍然带有结构；
最终误差是否和早期 partial residual 强相关；
某些 stage 是否出现分叉、条纹、弯曲等非线性模式；
冗余结构是否把早期残差压回较小范围。
```

它和 Stage 03 的 sine residual 不同：

```text
Stage 03 residual:
  measured waveform - best-fit sine
  重点是 analog error 相对单音参考的结构。

Stage 05 partial residual:
  signal - partial bit reconstruction
  重点是 bit-stage decision / weight 对误差演化的影响。
```

使用时要满足一个重要条件：

```text
signal 和 weights 必须在同一尺度。
```

如果 `signal` 是 ADC 电压尺度，而 `weights` 是 `calibrate_weight_sine` 的 solver/unit-sine 尺度，
scatter 的 residual 轴就没有直接物理意义。需要先确认或重缩放权重。

### 8. ENOB sweep：逐步增加 bit 子集看贡献

`analyze_enob_sweep.py` 看的是：**在同一组全量校准权重下，只使用前 n 个 bit 时，动态性能如何变化**。
它不是每个 bit 数都重新校准一次。

核心流程：

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
freq = result["refined_frequency"]

for n_bits in range(1, m_bits + 1):
    bits_subset = bits[:, :n_bits]
    weights_subset = weights_all[:n_bits]
    calibrated_signal = bits_subset @ weights_subset
    spectrum_result = analyze_spectrum(calibrated_signal, ...)
```

数学上：

```text
w_all = Calibrate(B[:, :M])
y_n[n] = Σ_{j=0}^{n-1} B[n, j] * w_all[j]
ENOB_n = SpectrumENOB(y_n)
```

所以 ENOB sweep 的正确解释不是“第 n 位单独有多少 ENOB”，而是：

```text
在当前 bit 顺序和当前全量校准权重下，prefix bit subset 对动态性能的贡献如何。
```

常见形态：

| sweep 形状 | 可能解释 |
|---|---|
| ENOB 随 bit 数上升 | 低位确实带来更多有效信息 |
| 后面进入平台 | 随机噪声、失真或测试条件已经主导 |
| 增加低位反而下降 | 低位主要是噪声、权重估计差、或输入未充分激励 |
| 某一位加入后突变 | 该 bit 权重/活动/决策可能异常 |

读图时要注意三个边界：

```text
1. bit 顺序必须有意义。
   代码用的是 `bits[:, :n_bits]`，默认列顺序是 MSB -> LSB。
   如果 bit matrix 被重排，prefix sweep 就不再等价于“逐步增加低位”。

2. 它默认用 `analyze_spectrum(calibrated_signal, ...)`，没有传 `max_scale_range`。
   因此更适合比较 ENOB/SNDR 这类比值指标；
   绝对 dBFS signal power / noise floor 不应直接和固定满量程测试混用。

3. 对强 redundancy、负权重、trim bit、乱序校准权重，
   “前 n 个 bit”不一定就是“最高 n 个有效贡献”。
   这时需要结合 radix、activity、overflow 和 bit mapping 一起看。
```

### 9. bit matrix 和可观测性

Stage 06 的校准可以看成一个线性回归问题。简化形式是：

```text
B @ w + c ≈ sine
```

其中：

```text
B: bit matrix, shape = (N samples, M bits)
w: bit weights, shape = (M,)
c: DC offset
```

真实 `calibrate_weight_sine` 还会加入 sine basis、harmonic basis、rank-deficiency patch、
column conditioning 等处理，但核心仍然是：**用 bit matrix 的列去解释一个已知或估计频率的正弦**。

这时 `B` 的列是否“可观测”非常关键。
用线性代数语言说，这就是最小二乘设计矩阵的 **rank deficiency / ill-conditioning** 问题。
严格一点，真正求解时看的不是裸的 `B`，而是包含 bit columns、DC offset、harmonic basis
等列的完整设计矩阵：

```text
A x ≈ b
```

在 `calibrate_weight_sine` 里，`A` 大致由这些列拼起来：

```text
A = [effective bit columns, offset columns, harmonic basis columns, ...]
```

如果 `A` 的列线性相关，就出现 rank deficiency：

```text
rank(A) < number_of_columns(A)
```

如果列没有完全相关、但接近相关，就不是严格奇异，而是病态：

```text
condition_number(A) 很大
```

对应到正规方程视角就是：

```text
A.T @ A
```

会奇异或接近奇异。实际代码用 `lstsq`，不需要显式求逆 `A.T @ A`，
但不可辨识和数值敏感的问题仍然存在。

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
数学上，这意味着设计矩阵有线性相关列：

```text
rank(B) < M
```

如果考虑 DC offset 和 harmonic basis，更严格的说法是：

```text
rank(A) < number_of_columns(A)
```

最小二乘只能识别组合：

```text
B[:, i] * (w_i + w_j)
```

不能唯一分配给 `w_i` 和 `w_j`。

如果某一列恒定：

```text
B[:, i] 全是 0 或全是 1
```

那这一位没有提供 AC 信息。由于模型里还有 DC offset，这一列等价于或接近等价于 offset column，
所以在完整设计矩阵 `A` 里也是线性相关或近似线性相关。它可能是：

```text
dead bit；
输入没有覆盖到；
测试幅度太小；
数据预处理错了；
或该 bit 本身被架构约束住。
```

如果两列不完全相同但高度相关：

```text
corr(B[:, i], B[:, j]) ~= 1
```

校准也会变得病态。此时不是完全不可解，而是权重估计对噪声、输入窗口、harmonic basis
和数值误差非常敏感。表现可能是：

```text
权重正负乱跳；
某些低位权重异常大或异常小；
ENOB sweep 某一位加入后突变；
radix 图出现随机跳变；
calibrated_signal 比值指标看似改善，但权重本身不稳定。
```

因此要把“可观测性”分成两类看。

严格的矩阵可解性检查是线性代数问题，应该直接看设计矩阵：

```text
rank(A)
singular values of A
condition_number(A)
column correlation / near dependency
```

其中 `A` 至少要包括：

```text
bit columns + DC offset column
```

如果要完全对应 `calibrate_weight_sine`，还要包括当前频率下的 harmonic basis。
只有这些量才能严格回答：

```text
这个 least-squares 问题是否满秩？
参数是否唯一可辨识？
数值条件是否足够好？
```

ADCToolbox 的校准代码本身也体现了这个判断：`_patch_rank_deficiency`
会对 `[bits, ones]` 做 `matrix_rank` 检查，并把恒定列或线性相关列合并/丢弃。
这比看图更接近真正的“可解性”判断。

Stage 05 里的这些工具不能严格证明矩阵可解，它们更像是围绕 bit matrix 的
**症状检查 / sanity check**：

```text
bit activity:
  直接相关。
  能发现恒定列、几乎不翻转的列、输入覆盖不足。
  但它不能发现所有列相关问题。

weight radix / effres:
  后验诊断。
  它看的是校准/给定权重是否像预期架构，不证明原始矩阵满秩。
  如果权重异常，可能提示病态拟合或 bit mapping 问题。

overflow:
  架构/输入范围诊断。
  它看 suffix code 是否经常贴边，说明 correction margin 是否吃紧。
  它基本不直接回答矩阵 rank。

residual scatter:
  后验结构诊断。
  它看 partial residual 和 final residual 是否存在 stage-wise 结构。
  它能提示某些 bit stage 没被模型解释好，但不是 rank test。

ENOB sweep:
  后验性能诊断。
  它看使用前 n 个 bit 后动态性能如何变化。
  它能提示某些 bit 加入后有异常贡献，但也不是可解性证明。
```

所以更准确的说法是：

```text
rank / SVD / condition number:
  回答 Stage 06 的 least-squares 是否数学上可辨识、数值上稳定。

Stage 05 的 activity/radix/overflow/residual/ENOB sweep:
  帮助解释为什么它可能不可辨识、为什么会病态、或者结果为什么不符合架构直觉。
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

本次运行的典型输出是：

```text
sar_ideal                      ENOB = 11.98 bits
sar_mismatch_nominal_weights   ENOB = 11.60 bits
sar_after_sine_calibration     ENOB = 11.62 bits

calibrated weight-list effective resolution = 12.01 bits
first four bit activities = [50.0, 49.99, 50.01, 49.96]
```

读法是：

```text
bit activity 接近 50%，说明前几位在当前正弦输入下翻转均衡；
effres 接近 12 bit，说明校准权重 span 没有明显丢 bit；
校准后 ENOB 只小幅提升，说明这个 case 的主要收益不是 SNDR 大幅恢复；
如果 SFDR 提升更明显，通常表示 deterministic spur 被校准压低了。
```

这个实验的作用是把 Stage 05 放回完整链路里看，不是单独证明 bit matrix 可解。

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

本次运行结果：

```text
ideal                   activity = 50.0% - 50.0%
+1% DC Offset           activity = 50.3% - 53.3%
-1% DC Offset           activity = 46.7% - 49.7%
Poor contact in Bit-11  activity = 45.0% - 50.0%
```

这个实验说明：

```text
bit activity 是单列边缘统计；
它能发现恒定列、弱翻转列、输入 DC 偏置、某位活动异常；
它不能发现所有列相关问题，也不能证明 least-squares 满秩。
```

所以 activity 是便宜的体检项。它和可解性有关，但不是完整的 rank / SVD / condition number 检查。

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

本次运行结果：

```text
Binary ADC with Thermal Noise:
  Max_ENOB = 11.20 bit @ 12 bits
  Final_ENOB = 11.20 bit

Binary ADC with Thermal Noise + LSB random:
  Max_ENOB = 10.69 bit @ 11 bits
  Final_ENOB = 10.69 bit
```

解释：

```text
第一组继续用到 12 bits，说明低位仍提供有效信息；
第二组最佳点停在 11 bits，说明最后一位主要进入随机扰动/噪声主导；
这不是“第 n 位单独的 ENOB”，而是 prefix bit subset 的重构性能。
```

ENOB sweep 是后验性能曲线。它能提示某些低位贡献很小或有负贡献，但不能证明矩阵可解。

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

本次运行结果：

```text
Strict Binary Weights:
  EffRes = 12.00 bit
  Average Radix = 2.0000

Sub-Radix-2 Weights:
  EffRes = 12.34 bit
  Average Radix = 1.8196
```

读法：

```text
radix ~= 2 表示权重比例接近严格二进制；
radix < 2 表示 sub-radix / redundancy，后续低位相对更有修正空间；
effres 只说明显著权重 span，不等价于真实 ENOB。
```

如果 radix 或 effres 已经明显离谱，后面校准/频谱结果就要更谨慎地读。

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

先注意一个重要边界：这张图画的是 `analyze_overflow` 的 suffix-code distribution，
不是直接的 analog residue。

```text
z_i[n] = (raw_code[:, i:] @ weight[i:]) / sum(weight[i:])
```

在正权重、0/1 bit 的标准 SAR 情形下，`z_i[n]` 理论上不会真正越过 `[0, 1]`，
所以图里的百分比主要应理解为：

```text
贴到下边界 0 的样本比例；
贴到上边界 1 的样本比例。
```

本次运行的关键数值：

```text
Binary ADC, Normal Range:
  MSB_range = [0.010, 0.990]

Binary ADC, Large Signal:
  MSB_range = [0.000, 1.000]
  MSB 贴下边界约 13.7%
  MSB 贴上边界约 13.7%

Sub-Radix with Redundancy:
  MSB_range = [0.010, 0.990]
  前几个高位 suffix 没有明显贴边

Sub-Radix, Insufficient Redundancy:
  MSB_range = [0.010, 0.990]
  当前参数下没有形成非常强的贴边反例
```

读图规律：

```text
第一幅 vs 第二幅：
  对照成立。large signal 把 MSB suffix 推到 [0, 1] 两端，边界占用明显增加。

第三幅 vs 第四幅：
  对照不够清晰。两者输入幅度相同，只改了一个 cap，当前 suffix 图没有强烈显示
  “redundancy 足够”和“redundancy 不足”的差异。
```

因此实验 5 的谨慎结论是：

```text
analyze_overflow 能显示 suffix code 是否贴边；
第一/第二幅能说明输入范围变大后边界占用增加；
第三/第四幅目前更像 demo 设计不够锋利，而不是核心函数计算错误。
```

如果要让第三/第四幅更适合教学，应当：

```text
标注目标 redundancy bit 附近的 range_min / range_max；
设置 ofb 到目标 bit，而不是只看默认 MSB mask；
增大输入幅度，或加入 comparator offset / decision error；
必要时改画真实 partial analog residue，而不是 suffix-code distribution。
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
unit-cap-scaled mismatch sigma sweep
32 次 Monte Carlo
before / after foreground sine calibration
```

重点不是某一条漂亮曲线，而是：

```text
看 ENOB 分布；
看 redundancy 在 mismatch 下是否更稳；
看校准前后差异是否符合 deterministic mismatch 的预期。
```

图的读法：

```text
横轴：unit-cap mismatch sigma，从 0% 到 10%。
纵轴：quick_sndr 得到的 ENOB。
每个 sigma 点跑 32 次 Monte Carlo。
曲线：32 次结果的 median ENOB。
深色阴影：p10 到 p90。
浅色阴影：min 到 max。
```

四条曲线分别是：

```text
蓝色虚线：Strict binary, before cal
蓝色实线：Strict binary, after cal
红色虚线：Radix ~1.8, before cal
红色实线：Radix ~1.8, after cal
```

核心规律：

```text
before cal:
  两条虚线都随 mismatch sigma 快速下降。
  原因是转换由 actual mismatched weights 决定，但重构仍用 nominal weights。

after cal:
  两条实线都明显高于虚线，说明 foreground sine calibration 学到了实际权重。

strict binary after cal:
  大 mismatch 下仍逐渐下降，阴影变宽。
  说明权重校准能救很多 deterministic mismatch，但严格二进制缺少 correction margin。

radix ~1.8 after cal:
  基本贴近 16 bit，分布也窄。
  说明 redundancy + calibration 对 unit-cap mismatch 更稳。
```

这张图不是说 sub-radix 未校准就天然高 ENOB。它真正说明的是：

```text
unit-cap mismatch 会严重破坏未校准 SAR；
foreground sine calibration 能恢复大部分 deterministic weight error；
sub-radix redundancy 让校准后的性能对 mismatch 更稳健。
```

阴影带来自 Monte Carlo 随机 realization。阴影越宽，说明不同随机 mismatch 芯片之间的性能差异越大。

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
