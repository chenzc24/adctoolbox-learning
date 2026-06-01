# Stage 05：Digital Output 与 bit matrix 诊断

## 本阶段目标

学完本阶段，你应该能解释：

- ADC raw digital output 为什么可以表示成 bit matrix。
- bit activity、weight radix、overflow、ENOB sweep 各自检查什么。
- 为什么校准前必须理解 raw bits。
- 为什么不要只把 ADC 输出看成一条 analog waveform。

## 数学需要补什么

### 1. bit matrix

SAR ADC 每个样本输出一个 bit vector：

```text
[b0, b1, ..., bN-1]
```

对 `M` 个样本，形成矩阵：

```text
B shape = (M, N)
```

在代码中：

```python
bits.shape == (n_samples, n_bits)
```

约定：

```text
MSB at column 0
LSB at last column
```

### 2. 数字重构

给定权重：

```text
w = [w0, w1, ..., wN-1]
```

重构：

```text
y = B @ w
```

这是矩阵乘法：

```text
(M, N) @ (N,) -> (M,)
```

### 3. bit activity

第 `i` 位的 activity：

```text
activity_i = mean(B[:, i]) * 100%
```

理想情况下，对居中且覆盖良好的 sine，很多 bit 的 activity 应接近 50%。

明显偏离可能表示：

- DC offset
- clipping
- input range 不合适
- bit decision 异常

### 4. radix

相邻权重比：

```text
radix_i = |w[i-1]| / |w[i]|
```

纯二进制接近：

```text
radix = 2
```

sub-radix 或冗余结构：

```text
radix < 2
```

### 5. ENOB sweep

ENOB sweep 观察使用不同 bit 子集重构时性能如何变化。

它可以帮助判断：

- 哪些低位主要是噪声。
- 增加 bit 是否真的带来有效性能。
- 校准后哪些 bit 对性能贡献最大。

## 电路需要理解什么

### 1. raw bits 是电路行为的直接证据

waveform 是 bits 加权后的结果，已经混合了很多信息。

raw bits 更接近电路内部：

- MSB decision 是否均衡
- LSB 是否随机
- redundancy 是否足够
- 某些 bit 是否 stuck

### 2. overflow/redundancy margin

对冗余 SAR，某些 bit 权重不是严格二进制。

这样做的目的：

- 容忍 comparator offset
- 容忍 DAC settling error
- 容忍前面 bit decision 小错误

但冗余不足时，某些输入区域无法被后续 bit 修正，表现为 overflow 或残差分布异常。

## 本库对应代码

Digital output 分析：

```text
python/src/adctoolbox/dout/analyze_bit_activity.py
python/src/adctoolbox/dout/analyze_weight_radix.py
python/src/adctoolbox/dout/analyze_overflow.py
python/src/adctoolbox/dout/analyze_enob_sweep.py
python/src/adctoolbox/dout/plot_residual_scatter.py
```

官方示例：

```text
python/src/adctoolbox/examples/05_debug_digital/
```

本地完整 demo 输出：

```text
agent_playground/adctoolbox_learning/outputs/whole_workflow/04_digital_debug_bits_and_weights.png
```

## 对应 API

```python
from adctoolbox.dout import analyze_bit_activity
from adctoolbox.dout import analyze_weight_radix
from adctoolbox.dout import analyze_overflow
from adctoolbox.dout import analyze_enob_sweep
```

## 实验 1：bit activity

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d11_bit_activity.py
```

观察：

- 哪些 bit 偏离 50%。
- 偏离最大的是 MSB 还是 LSB。

思考：

- 如果输入 DC 从 0.5 改成 0.55，会发生什么？
- 如果输入 amplitude 太大导致 clipping，会发生什么？

## 实验 2：ENOB sweep

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d12_sweep_bit_enob.py
```

观察：

- 使用更多 bit 时 ENOB 是否持续提升。
- 是否出现平台区。

## 实验 3：weight radix

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d13_weight_scaling.py
```

观察：

- radix 是否接近 2。
- 是否有异常跳变。

## 实验 4：overflow check

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d14_overflow_check.py
```

观察：

- 残差分布是否接近边界。
- 是否有明显 overflow 风险。

## 本阶段代码阅读

建议读：

```text
python/src/adctoolbox/dout/analyze_bit_activity.py
python/src/adctoolbox/dout/analyze_weight_radix.py
```

阅读重点：

- bit activity 如何计算。
- radix 如何由 weights 得到。
- effective resolution 是怎样的启发式估计。

## 阶段检查问题

1. 为什么 bit matrix 比 reconstructed waveform 更接近 ADC 内部状态？
2. bit activity 偏离 50% 可能意味着什么？
3. radix=2 和 radix<2 分别对应什么 ADC 结构？
4. ENOB sweep 为什么能判断低位是否有用？
5. 为什么校准前要先检查 bits 是否合理？

