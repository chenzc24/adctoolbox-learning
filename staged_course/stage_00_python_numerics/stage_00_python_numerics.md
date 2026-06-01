# Stage 00: Python 数值仿真基础

## 本阶段目标

这一阶段不是学习普通 Python 语法，而是补齐 ADCToolbox 建模所需的数值计算直觉。学完后，你应该能解释：

- `np.ndarray` 的 shape 为什么比变量名更重要。
- `bits.shape == (n_samples, n_bits)` 为什么是后续校准的基础。
- `@` 矩阵乘法在 ADC 重构中代表什么。
- 为什么仿真脚本要固定随机种子。
- 为什么工程建模里要反复区分单位、归一化范围和 full-scale。

如果这一阶段不稳，后面读 `sar_convert`、`sar_reconstruct`、`calibrate_weight_sine` 时会很容易把物理含义和数组维度混在一起。

## 初学者先抓住的主线

先不要急着背 NumPy 语法。你只需要先建立一个习惯：

```text
每看到一个变量，先问三件事：
1. 它是一维还是二维？
2. 每一维代表什么物理含义？
3. 它的单位是什么，或者它是不是归一化量？
```

例如：

```python
bits.shape == (8192, 12)
```

这句话比变量名更重要。它表示：

```text
8192 个采样点
每个采样点有 12 个 SAR bit decision
```

再例如：

```python
weights.shape == (12,)
```

它表示：

```text
每一列 bit 对应一个重构权重
```

所以：

```python
aout = bits @ weights
```

才会得到：

```text
8192 个重构输出点
```

这就是后面所有 SAR 建模和位权重校准的最小骨架。

## 数学需要补什么

### 1. 向量和矩阵不是抽象符号

在本项目里，一个采样序列通常写成一维数组：

```python
aout.shape == (n_samples,)
```

而 SAR ADC 的 raw bits 是二维矩阵：

```python
bits.shape == (n_samples, n_bits)
```

第 0 维是时间样本，第 1 维是 bit 位置。约定是：

```text
bits[:, 0]      -> MSB
bits[:, -1]     -> LSB
bits[n, :]      -> 第 n 个样本的完整 bit decision vector
```

### 2. ADC 数字重构就是矩阵乘法

给定 bit matrix 和权重：

```text
B shape = (N, M)
w shape = (M,)
```

重构输出是：

```text
y = B @ w
```

shape 变成：

```text
(N, M) @ (M,) -> (N,)
```

这不是单纯的编程技巧，而是 ADC 数字重构的核心模型：

```text
y[n] = b0[n]*w0 + b1[n]*w1 + ... + bM-1[n]*wM-1
```

后续校准就是估计这个 `w`。

### 3. 随机数 seed 是实验可复现性的基础

ADC 建模中会出现：

- capacitor mismatch
- thermal noise
- comparator noise
- sampling noise
- Monte Carlo sweep

如果不固定 seed，每次结果都会变。学习阶段建议显式写：

```python
rng = np.random.default_rng(20260601)
```

这样你改一个参数时，结果变化更容易归因。

### 4. 归一化和单位必须分清

本项目常见两类频率：

```text
Fin, fs      -> Hz
freq         -> Fin / fs, normalized frequency
```

常见电压范围：

```text
quant_range = (0.0, 1.0)       # normalized single-ended
quant_range = (-Vref, +Vref)   # differential-style range
```

建模时先用归一化范围是合理的，因为它降低了无关复杂度；但学习时要始终知道“这个数是归一化量，还是物理单位”。

## 电路需要理解什么

数值数组只是物理系统的投影：

| 代码对象 | 电路/系统含义 |
|---|---|
| `vin` | ADC 输入电压 |
| `aout` | 重构后的模拟输出波形 |
| `bits` | SAR 每一位比较器决策 |
| `weights` | CDAC 或数字重构权重 |
| `noise_rms` | 输入等效 RMS 噪声 |
| `quant_range` | ADC 满量程范围 |
| `rng` | 某次芯片/噪声 realization |

学习时建议先读代码变量，再强迫自己说出它对应的物理对象。

## 本库对应代码

建议先读：

```text
python/src/adctoolbox/models/sar.py
python/src/adctoolbox/siggen/nonidealities.py
python/src/adctoolbox/fundamentals/validate.py
python/src/adctoolbox/fundamentals/frequency.py
```

重点 API：

```python
import numpy as np
from adctoolbox.models import sar_ideal_weights, sar_convert, sar_reconstruct
```

## 读代码时具体看什么

打开：

```text
python/src/adctoolbox/models/sar.py
```

先找这几个函数，不需要一次读完整文件：

```text
sar_ideal_weights    -> 权重向量怎么生成
sar_convert          -> vin 怎么变成 bits
sar_reconstruct      -> bits 怎么乘 weights 变成 aout
```

读 `sar_convert` 时，只追踪这几个变量：

```text
vin_norm
weights
v_dac
v_test
bits
```

读 `sar_reconstruct` 时，只追踪：

```text
bits @ weights
```

这一阶段不要被更复杂的参数吓到。先把“数组形状 + 物理含义 + 单位”对应起来。

## 实验 1: 手写一次数字重构

在 Python 交互环境或临时脚本里运行：

```python
import numpy as np

bits = np.array([
    [0, 0, 0],
    [0, 0, 1],
    [0, 1, 0],
    [0, 1, 1],
    [1, 0, 0],
])

weights = np.array([4, 2, 1])
aout = bits @ weights

print(bits.shape)
print(weights.shape)
print(aout)
```

你应该看到：

```text
bits 是 5 个样本、3 个 bit
weights 是 3 个 bit 的权重
aout 是每个样本的重构值
```

## 实验 2: 修改权重观察重构变化

把权重改成：

```python
weights_bad = np.array([4.2, 1.9, 1.0])
```

比较：

```python
print(bits @ weights)
print(bits @ weights_bad)
```

这个小实验就是 SAR mismatch 的最小雏形：同一组 `bits`，不同的重构权重，会得到不同的输出。

## 阶段检查问题

1. `bits.shape == (N, M)` 中 `N` 和 `M` 分别代表什么？
2. 为什么 `bits @ weights` 是 ADC 数字重构，而不只是矩阵运算？
3. `Fin` 和 `freq = Fin / fs` 有什么区别？
4. 为什么 Monte Carlo 仿真要固定 random seed？
5. `actual_weights` 和 `digital_weights` 是同一个东西吗？

如果这些问题还答不稳，不建议进入 Stage 01。
