# Stage 04：SAR ADC 行为建模

## 本阶段目标

学完本阶段，你应该能解释：

- SAR ADC 的逐次逼近过程。
- CDAC weights 如何决定 bit decision。
- nominal weights 和 actual weights 的区别。
- capacitor mismatch 如何造成非线性和 spur。
- sampling noise 和 comparator noise 在模型中如何进入。
- 本库 `sar_convert` 和 `sar_reconstruct` 的数据流。

## 初学者先抓住的主线

SAR ADC 的行为可以先想成一个“二分试探”过程：

```text
先试 MSB：输入有没有超过 1/2 full-scale？
再试下一位：在已有判断基础上，再加 1/4 full-scale 试一下。
继续往下，直到 LSB。
```

每一位只做一件事：

```text
临时把当前 weight 加到 DAC 输出上
比较 vin 和 v_test
如果 vin 更大，这一位保留为 1
否则这一位为 0
```

所以 SAR 模型里最重要的三个对象是：

```text
vin       -> 要转换的输入
weights   -> CDAC 每一位能产生多大的 DAC step
bits      -> 每一步比较器留下的 0/1 决策
```

先把这个过程看懂，再看 mismatch、noise、redundancy。

## 手算一个 4-bit 例子

理想 4-bit 权重：

```text
[0.5, 0.25, 0.125, 0.0625]
```

假设：

```text
vin = 0.70
```

逐次逼近：

| bit | weight | v_test | decision | v_dac |
|---|---:|---:|---:|---:|
| MSB | 0.5 | 0.5 | 1 | 0.5 |
| bit1 | 0.25 | 0.75 | 0 | 0.5 |
| bit2 | 0.125 | 0.625 | 1 | 0.625 |
| bit3 | 0.0625 | 0.6875 | 1 | 0.6875 |

得到：

```text
bits = [1, 0, 1, 1]
aout = 0.6875
residue = vin - aout = 0.0125
```

这个表就是 `sar_convert` 的核心逻辑。

## 数学需要补什么

### 1. 逐次逼近是贪心搜索

SAR ADC 想用一组二进制权重近似输入：

```text
vin ≈ b0*w0 + b1*w1 + ... + bN-1*wN-1
```

其中：

```text
bi ∈ {0, 1}
```

理想权重：

```text
w = [1/2, 1/4, 1/8, ..., 1/2^N]
```

逐次逼近过程：

```text
v_dac = 0
for each bit:
    v_test = v_dac + current_weight
    if vin >= v_test:
        bit = 1
        v_dac = v_test
    else:
        bit = 0
```

### 2. 权重向量

本库的理想权重生成方式：

```text
raw = [2^(N-1), ..., 1]
weights = raw / (sum(raw) + 1 LSB)
```

例如 4-bit：

```text
raw = [8, 4, 2, 1]
weights = [8, 4, 2, 1] / 16
```

这不是除以 15，而是除以 16。这样对应完整 4-bit 量化格点。

### 3. mismatch

实际电容不是理想值：

```text
w_actual = w_nominal * (1 + error)
```

对于单位电容 mismatch，较大电容由更多单位电容并联而成，相对误差更小：

```text
sigma_relative ∝ 1 / sqrt(C)
```

本库 `sar_apply_cap_mismatch` 使用这个思想。

### 4. 两套权重

必须区分：

```text
actual analog weights
digital reconstruction weights
```

转换时：

```text
bits = sar_convert(vin, actual_weights)
```

重构时：

```text
aout = sar_reconstruct(bits, digital_weights)
```

未校准 ADC：

```text
actual_weights != nominal_weights
digital_weights = nominal_weights
```

校准后：

```text
digital_weights = calibrated_weights
```

## 电路需要理解什么

### 1. SAR ADC 电路块

典型 SAR ADC 包含：

- sample-and-hold
- CDAC
- comparator
- SAR logic
- reference driver

每一位 trial 实际上是：

```text
切换 CDAC
等待建立
比较 vin 与 v_dac
锁存 bit
```

### 2. CDAC mismatch

CDAC capacitor mismatch 会导致：

- bit weight 偏离理想值
- transfer curve 非线性
- harmonic distortion
- SFDR 下降

这种误差是 deterministic，所以适合校准。

### 3. Comparator noise

Comparator noise 会导致 bit decision 随机翻转，尤其在输入接近 threshold 时。

这种误差是 stochastic，校准不能完全消除，只能通过 averaging、设计改进或降低噪声。

### 4. Sampling noise

采样电容上的 kT/C 噪声进入 sampled input：

```text
vin_sampled = vin + noise
```

它主要影响 SNR/ENOB。

## 本库对应代码

SAR 模型：

```text
python/src/adctoolbox/models/sar.py
```

官方示例：

```text
python/src/adctoolbox/examples/02_spectrum/exp_s09_sar_fft_length_near_nyquist.py
python/src/adctoolbox/examples/05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

本地学习脚本：

```text
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

## 对应 API

```python
from adctoolbox.models import sar_ideal_weights
from adctoolbox.models import sar_apply_cap_mismatch
from adctoolbox.models import sar_convert
from adctoolbox.models import sar_reconstruct
```

## 实验 1：运行 SAR bit trial 学习脚本

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\sar_adc_model_study.py
```

重点看控制台：

```text
SAR bit-trial trace for one sample
```

每一行对应一次 comparator decision。

## 实验 2：改变 capacitor mismatch

打开：

```text
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

修改：

```python
cap_mismatch_sigma: float = 0.0
```

然后改成：

```python
cap_mismatch_sigma: float = 0.002
cap_mismatch_sigma: float = 0.01
```

观察：

- SFDR 是否变差。
- calibration 是否能恢复一部分性能。

## 实验 3：改变 comparator noise

修改：

```python
comparator_noise_rms: float = 0.0
```

再改成：

```python
comparator_noise_rms: float = 100e-6
```

观察：

- SNR/ENOB 下降。
- calibration 对随机噪声改善有限。

## 本阶段代码阅读

读：

```text
python/src/adctoolbox/models/sar.py
```

重点看：

- `sar_ideal_weights`
- `sar_apply_cap_mismatch`
- `sar_convert`
- `sar_reconstruct`

尤其是 `sar_convert` 中这段逻辑：

```text
v_test = v_dac + weights[j]
bit = vin_norm + noise >= v_test
v_dac = where(bit, v_test, v_dac)
```

建议你按这个顺序给自己讲出来：

```text
1. sar_ideal_weights 生成 nominal_weights
2. sar_apply_cap_mismatch 生成 actual_weights
3. sar_convert 用 actual_weights 产生 bits
4. sar_reconstruct 用 digital_weights 重构 aout
```

关键问题是第 3 步和第 4 步可以使用不同权重：

```text
转换时用 actual analog weights
重构时用 nominal/calibrated digital weights
```

这正是后面校准能发挥作用的地方。

## 容易混淆的点

- `actual_weights` 不是“真实答案输出”，它是模拟 CDAC 的实际权重。
- `nominal_weights` 是数字端以为 ADC 应该有的理想权重。
- mismatch 会先影响 bit decision，再影响数字重构；校准只能修正可由数字权重补偿的部分。
- comparator noise 是每次比较时的随机扰动，不是一个固定权重误差。
- `cap_mismatch_sigma=0.002` 表示相对失配量级，不是 ENOB 直接下降 0.002 bit。

## 阶段检查问题

1. SAR ADC 为什么从 MSB 开始 trial？
2. 为什么 actual weights 和 nominal weights 不一致会产生失真？
3. capacitor mismatch 和 comparator noise 哪个更适合校准？
4. `sar_convert` 输出的 bits 是什么 shape？
5. `sar_reconstruct(bits, weights)` 中的 weights 是模拟权重还是数字重构权重？

