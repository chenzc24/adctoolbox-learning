# Stage 06：Sine-based ADC 位权重校准

## 本阶段目标

学完本阶段，你应该能解释：

- ADC 位权重校准要解决什么问题。
- 为什么 sine input 可以用于估计 bit weights。
- `calibrate_weight_sine` 的输入、输出和整体数学逻辑。
- 为什么校准通常改善 SFDR/THD，但不一定显著改善随机噪声导致的 SNR。
- 如何用 spectrum 验证校准效果。

## 数学需要补什么

### 1. 从重构开始

对 bit matrix：

```text
B shape = (N_samples, N_bits)
```

重构输出：

```text
y = B @ w + offset
```

其中：

- `B` 已知，来自 ADC raw bits。
- `w` 未知或不准，是待估计 bit weights。
- `offset` 是 DC 项。

### 2. 校准的核心假设

输入是 sine，所以理想输出应该接近：

```text
s[n] = A cos(2πfn) + B sin(2πfn) + C
```

校准寻找 `w`，使：

```text
B_bits @ w ≈ sine_basis
```

更完整地写：

```text
B_bits @ w + offset ≈ a1 cos(2πfn) + b1 sin(2πfn)
```

如果考虑 harmonic rejection：

```text
B_bits @ w + offset ≈ sum_k ak cos(2πkfn) + bk sin(2πkfn)
```

### 3. 这是最小二乘问题

本质：

```text
min ||X θ - target||^2
```

其中未知量包括：

- bit weights
- offset
- sine basis coefficients
- harmonic coefficients

代码中通过构造线性系统求解。

### 4. 为什么需要 harmonic rejection

如果 ADC 有非线性，输出中有 harmonic。

如果校准时把 harmonic 全部当成 weight error，可能把真实失真错误地吸收到权重里。

所以可以设置：

```python
harmonic_order=3
```

让模型显式包含 1、2、3 次谐波项，避免权重估计被谐波污染。

### 5. rank deficiency

如果两个 bit pattern 完全相同：

```text
B[:, i] == B[:, j]
```

那么仅凭数据无法唯一区分 `w_i` 和 `w_j`。

这叫 rank deficiency。

本库处理方法：

1. 找到冗余或相同列。
2. 先求组内总权重。
3. 再按 nominal weights 分配回每个 bit。

这对 redundant SAR 很重要。

## 电路需要理解什么

### 1. 校准针对 deterministic mismatch

典型可校准误差：

- capacitor mismatch
- bit weight error
- interstage gain error
- 某些稳定的 offset/gain mismatch

典型不可完全校准误差：

- thermal noise
- comparator random noise
- sampling noise
- jitter random component

所以：

```text
校准能改善 deterministic spur
校准不能消除随机噪声底
```

### 2. SAR 校准中的 analog/digital 分离

实际转换：

```text
bits = SAR(vin, actual_analog_weights)
```

数字重构：

```text
y = bits @ digital_weights
```

校准改变的是：

```text
digital_weights
```

不是已经发生的模拟转换过程。

### 3. 为什么用 sine

sine input 的优点：

- 易产生。
- 频谱结构简单。
- 可通过 FFT/拟合估计频率。
- 理想输出可以用少量 basis 表示。
- 适合 foreground calibration。

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

官方示例：

```text
python/src/adctoolbox/examples/05_debug_digital/exp_d01_cal_weight_sine_lite.py
python/src/adctoolbox/examples/05_debug_digital/exp_d02_cal_weight_sine.py
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

本地完整 demo：

```text
agent_playground/adctoolbox_learning/demos/whole_workflow_demo.py
```

## 对应 API

```python
from adctoolbox import calibrate_weight_sine
```

典型调用：

```python
cal = calibrate_weight_sine(
    bits,
    freq=fin_bin / n_samples,
    harmonic_order=3,
)

weights_calibrated = cal["weight"]
signal_calibrated = cal["calibrated_signal"]
```

## 实验 1：最小校准示例

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d02_cal_weight_sine.py
```

观察：

- before calibration 的 ENOB。
- after calibration 的 ENOB。
- nominal weights、real weights、calibrated weights 的差异。

## 实验 2：SAR mismatch Monte Carlo

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d16_sar_unit_cap_mismatch_mc.py
```

观察：

- 多次随机 mismatch 下 ENOB 分布。
- binary SAR 和 redundant SAR 的差异。

## 实验 3：训练长度 sweep

```powershell
cd C:\Users\90590\adctoolbox_examples
python 05_debug_digital\exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

观察：

- 训练样本越多，校准越稳定。
- 样本太少时可能 overfit。

## 实验 4：本地完整闭环

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\whole_workflow_demo.py
```

看：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\03_sar_model_and_calibration.png
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\spectrum_metrics.csv
```

重点比较：

```text
sar_mismatch_nominal_weights
sar_after_sine_calibration
```

## 本阶段代码阅读

建议顺序：

```text
python/src/adctoolbox/calibration/calibrate_weight_sine.py
python/src/adctoolbox/calibration/_prepare_input.py
python/src/adctoolbox/calibration/_estimate_frequencies.py
python/src/adctoolbox/calibration/_lstsq_solver.py
python/src/adctoolbox/calibration/_patch_rank_deficiency.py
python/src/adctoolbox/calibration/_post_process.py
```

阅读重点：

- 输入 bits 如何统一成内部格式。
- frequency 如何估计或使用。
- least-squares 系统如何构造。
- redundant/rank-deficient bit 如何处理。
- 输出 `calibrated_signal` 如何生成。

## 校准前后应该怎么看

不要只看 ENOB。

至少看：

```text
SNDR
SNR
SFDR
THD
ENOB
```

解释方式：

| 现象 | 可能解释 |
|---|---|
| SFDR 明显改善，SNR 几乎不变 | 校准修正了 deterministic spur，但噪声底没变 |
| ENOB 改善很小 | 原本主要受随机噪声限制 |
| THD 改善 | weight mismatch 导致的谐波被修正 |
| 校准后变差 | 频率估计不准、样本不足、overfit、输入不符合 sine 假设 |

## 阶段检查问题

1. 为什么校准可以写成 `B @ w ≈ sine`？
2. `bits`、`weights`、`calibrated_signal` 分别是什么？
3. 为什么 capacitor mismatch 适合校准，而 thermal noise 不适合校准？
4. harmonic_order 的意义是什么？
5. 为什么校准效果必须用校准后 spectrum 再验证？

