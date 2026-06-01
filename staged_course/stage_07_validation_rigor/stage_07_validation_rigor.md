# Stage 07: 校准验证、模型边界与工程严谨性

## 本阶段目标

Stage 06 会让你理解 `calibrate_weight_sine` 如何估计 bit 权重。本阶段回答更工程化的问题：

- 校准结果为什么不能只看训练数据。
- 为什么 ENOB 变好不等于模型完全正确。
- 如何区分 deterministic mismatch 和 random noise。
- 如何设计 train/test 分离的验证。
- ADCToolbox 的行为级 SAR 模型有哪些边界。
- 什么时候可以相信结果，什么时候只能把它当学习或算法原型。

## 初学者先抓住的主线

Stage 07 的核心不是再学一个新函数，而是学会问：

```text
这个校准结论可信吗？
```

一个更专业的回答通常不是：

```text
ENOB 变好了，所以可信。
```

而是：

```text
训练数据和验证数据分开了吗？
换频率、换幅度、换相位后还有效吗？
改善的是 SFDR/THD，还是 SNR？
误差来源是 deterministic 还是 random？
模型有没有覆盖真实电路里的关键效应？
```

这一步会把你从“能跑 demo”推进到“能评价 demo 结论”。

## 一个判断模板

看到任何校准结果时，先按这个模板检查：

| 问题 | 为什么重要 |
|---|---|
| 校准用的数据和验证用的数据是否不同 | 防止只在训练集上变好 |
| 输入频率是否变化过 | 防止只对某个 bin 偶然有效 |
| 输入幅度是否变化过 | 防止只覆盖部分 code/bit pattern |
| SNR、SNDR、SFDR、THD 是否一起报告 | 判断改善来自噪声还是失真 |
| residual 或 error spectrum 是否检查 | 防止指标好看但误差有结构 |
| noise/mismatch seed 是否说明 | 保证仿真可复现 |
| 模型假设是否写清楚 | 防止把行为模型误当成真实芯片结论 |

## 关键结论

ADCToolbox 很适合：

```text
学习 ADC 行为建模
理解 SAR bit decision
验证 bit weight calibration 思想
做算法原型和可视化 debug
```

但它不能直接替代：

```text
晶体管级仿真
版图后寄生验证
生产测试校准流程
严格计量级 ADC characterization
```

换句话说，它是学习和算法验证工具，不是最终工程签核工具。

## 数学需要补什么

### 1. 训练集和验证集必须分离

校准时用一段训练正弦：

```text
bits_train -> estimate calibrated_weights
```

验证时应该换另一段数据：

```text
bits_test @ calibrated_weights -> analyze_spectrum
```

更严谨的验证会改变：

- 输入频率
- 输入相位
- 输入幅度
- 噪声 realization
- mismatch realization
- FFT 长度

如果只在训练数据上看 ENOB 变好，可能存在过拟合或频率估计偶然匹配。

### 2. 校准主要修正 deterministic error

可校准误差通常具有稳定结构：

```text
capacitor mismatch
bit weight error
interstage gain error
stable offset/gain mismatch
```

不适合被“消除”的随机误差：

```text
thermal noise
comparator random noise
sampling noise
clock jitter random component
```

所以常见现象是：

```text
SFDR / THD 明显改善
SNR 几乎不变
ENOB 有限改善
```

这不是校准失败，而是说明噪声底由随机噪声限制。

### 3. 频谱指标依赖测试设置

同一个波形，不同设置会影响结果：

- coherent 或 non-coherent sampling
- window 类型
- side-bin 选择
- harmonic exclusion
- noise-floor estimation method
- max_scale_range
- 是否去 DC

因此报告结果时必须同时报告测试条件。

## 电路需要理解什么

### 1. SAR 行为模型的边界

`python/src/adctoolbox/models/sar.py` 是行为级模型。它包含：

- ideal/sub-radix weights
- unit-cap mismatch
- sampling noise
- comparator noise
- bit trial logic

它没有完整建模：

- CDAC 动态 settling
- reference transient / droop 的真实网络响应
- comparator metastability timing
- kickback 对输入采样节点的反馈
- switch charge injection 的细粒度波形
- PVT、温漂、老化
- 版图寄生造成的频率相关效应

所以它适合先建立算法直觉，不适合直接替代电路仿真。

### 2. 校准改变的是数字重构，不是已经发生的模拟转换

SAR 转换已经由真实模拟权重完成：

```text
bits = SAR(vin, actual_analog_weights)
```

校准后改变的是数字端：

```text
aout_cal = bits @ calibrated_digital_weights
```

如果某个模拟错误已经导致 bit decision 不可恢复，例如 redundancy 不足、比较器随机翻转太多、前级严重饱和，单纯改数字权重无法完全修复。

## 本库对应代码

校准：

```text
python/src/adctoolbox/calibration/calibrate_weight_sine.py
python/src/adctoolbox/calibration/_lstsq_solver.py
python/src/adctoolbox/calibration/_post_process.py
```

验证：

```text
python/src/adctoolbox/spectrum/compute_spectrum.py
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/aout/analyze_error_spectrum.py
python/src/adctoolbox/aout/analyze_error_pdf.py
python/src/adctoolbox/dout/analyze_overflow.py
python/src/adctoolbox/dout/analyze_weight_radix.py
```

推荐示例：

```text
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

## 推荐验证流程

### Step 1: 生成训练输入

```text
vin_train: coherent sine, bin k1
```

用 actual weights 得到：

```text
bits_train = sar_convert(vin_train, actual_weights)
```

### Step 2: 校准权重

```python
cal = calibrate_weight_sine(
    bits_train,
    freq=train_bin / n_samples,
    nominal_weights=nominal_weights,
)
weights_cal = cal["weight"]
```

### Step 3: 生成独立验证输入

```text
vin_test: different coherent sine, bin k2, phase changed
```

得到：

```text
bits_test = sar_convert(vin_test, actual_weights)
```

### Step 4: 比较三种重构

```text
before = bits_test @ nominal_weights
after  = bits_test @ weights_cal
ideal  = bits_test @ actual_weights
```

### Step 5: 多指标判断

至少比较：

```text
SNDR
SNR
SFDR
THD
ENOB
harmonics_dbc
residual spectrum
```

## 最小可执行验证实验

如果你想把 Stage 07 变成一个具体实验，可以这样设计：

```text
训练：
Fin bin = 499
phase = 0
amplitude = 0.45 full-scale

验证 1：
Fin bin = 587
phase = 0.3 rad
amplitude = 0.45 full-scale

验证 2：
Fin bin = 587
phase = 1.1 rad
amplitude = 0.35 full-scale
```

每组都比较：

```text
nominal reconstruction
calibrated reconstruction
actual-weight oracle, 如果是仿真模型
```

如果训练集提升明显、验证集也稳定提升，结论才更可信。

如果只有训练集提升，而验证集不提升甚至变差，就要怀疑：

```text
训练样本不足
频率估计偏差
过拟合
输入覆盖不够
模型假设不成立
```

## 如何解释常见结果

| 现象 | 可能解释 |
|---|---|
| SFDR 明显改善，SNR 几乎不变 | 权重 mismatch 被修正，但随机噪声底没变 |
| THD 改善，ENOB 只小幅提升 | 原本性能同时受失真和噪声限制 |
| 校准后训练集变好，测试集不变差也不变好 | 训练数据不足或 mismatch 本来很小 |
| 校准后测试集变差 | 频率估计错误、训练幅度不足、过拟合、输入不符合单音假设 |
| 低 mismatch 时二进制 SAR 和冗余 SAR 差距小 | error 仍在可校正范围内 |
| 高 mismatch 时冗余结构更稳 | redundancy 给错误决策留下修正空间 |

## 容易混淆的点

- train/test 分离不是机器学习专属概念，任何校准算法都需要独立验证。
- 行为级模型中 `actual_weights` 可见，是因为仿真知道真值；真实芯片上你通常不知道真值。
- Monte Carlo 结果要看分布，不要只看某一次 seed 的漂亮结果。
- 一个模型“有用”不等于“完整”。有用表示它能解释目标问题，完整表示它覆盖所有重要物理效应，后者要求高得多。
- 校准改善 SFDR 但不改善 SNR，通常是合理现象，不要立刻判断算法失败。

## 阶段检查问题

1. 为什么不能只用训练数据判断校准是否有效？
2. 为什么校准通常更容易改善 SFDR/THD，而不是随机噪声造成的 SNR？
3. `actual_weights`、`nominal_weights`、`calibrated_weights` 应该如何分别用于转换和重构？
4. 哪些 SAR 真实电路效应没有被 `sar.py` 完整建模？
5. 一个严谨的校准实验至少应该报告哪些测试条件？

完成这些问题后，你才真正从“会调用校准函数”进入“能判断校准结论是否可信”的阶段。
