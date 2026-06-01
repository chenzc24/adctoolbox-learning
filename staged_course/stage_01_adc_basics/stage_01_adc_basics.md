# Stage 01：ADC 基础、采样、量化、LSB

## 本阶段目标

学完本阶段，你应该能解释：

- ADC 的输入和输出分别是什么。
- 什么是 sampling、quantization、code、LSB、full-scale。
- 为什么理想 N-bit ADC 的 SNR 约为 `6.02N + 1.76 dB`。
- 为什么本库中的信号经常被归一化到 `0.0 ~ 1.0`。
- 为什么 SAR 模型的输入 `vin`、输出 `bits`、重构 `aout` 是三种不同对象。

## 数学需要补什么

### 1. 离散序列

连续信号：

```text
x(t)
```

采样后：

```text
x[n] = x(n / Fs)
```

其中：

- `Fs` 是采样率。
- `n` 是样本编号。
- `N` 是总样本数。

在代码里通常是：

```python
n = np.arange(N)
t = n / Fs
signal = A * np.sin(2*np.pi*Fin*t) + DC
```

### 2. 量化

理想 ADC 把连续电压映射成有限 code。

如果输入范围是：

```text
[Vmin, Vmax]
```

bit 数为 `Nbit`，那么 code 数：

```text
2^Nbit
```

LSB 大小：

```text
LSB = (Vmax - Vmin) / 2^Nbit
```

理想量化 code：

```text
code = floor((vin - Vmin) / LSB)
```

并限制在：

```text
0 <= code <= 2^Nbit - 1
```

### 3. 量化误差

理想量化误差：

```text
e = quantized_value - input_value
```

在经典近似中，量化误差被看作均匀分布：

```text
e ~ Uniform(-LSB/2, +LSB/2)
```

均方根：

```text
e_rms = LSB / sqrt(12)
```

这是推导理想 ADC SNR 的基础。

### 4. 理想 SNR 和 ENOB

满幅正弦 RMS：

```text
signal_rms = A / sqrt(2)
```

对理想 N-bit ADC，常用结果：

```text
SNR_ideal = 6.02N + 1.76 dB
```

反过来：

```text
ENOB = (SNDR - 1.76) / 6.02
```

注意这里用的是 `SNDR`，因为真实 ADC 的有效位数受到噪声和失真共同影响。

## 电路需要理解什么

### 1. ADC 是一个混合信号系统

ADC 前端是模拟电路：

- 采样开关
- 采样电容
- comparator
- reference
- DAC/CDAC

ADC 后端是数字结果：

- binary code
- SAR bit decisions
- calibration weights
- digital reconstruction

### 2. Full-scale range

如果本库使用：

```text
quant_range = (0.0, 1.0)
```

可以理解为归一化单端 ADC：

```text
0 V -> code 0
1 V -> max code
```

如果是差分 ADC，可以用：

```text
quant_range = (-Vref, +Vref)
```

但本学习路径先使用归一化单端模型，降低复杂度。

### 3. ADC 噪声来源

最基本的噪声和误差：

| 来源 | 电路含义 | 表现 |
|---|---|---|
| 量化误差 | 有限 bit 数 | 理想噪声底 |
| 热噪声 | 电阻、开关、电容采样噪声 | SNR 降低 |
| comparator noise | 比较器输入等效噪声 | code decision 抖动 |
| reference noise | 参考电压不稳 | 增益和噪声问题 |
| offset | 比较器/前端偏置 | code 偏移 |

## 本库对应代码

基础信号生成：

```text
python/src/adctoolbox/siggen/nonidealities.py
```

SAR 行为模型：

```text
python/src/adctoolbox/models/sar.py
```

基础单位和指标：

```text
python/src/adctoolbox/fundamentals/units.py
python/src/adctoolbox/fundamentals/snr_nsd.py
python/src/adctoolbox/fundamentals/metrics.py
```

官方示例：

```text
python/src/adctoolbox/examples/01_basic/
python/src/adctoolbox/examples/03_generate_signals/
```

本地学习脚本：

```text
agent_playground/adctoolbox_learning/demos/sar_adc_model_study.py
agent_playground/adctoolbox_learning/demos/whole_workflow_demo.py
```

## 对应 API

```python
from adctoolbox.siggen import ADC_Signal_Generator
from adctoolbox.models import sar_ideal_weights, sar_convert, sar_reconstruct
from adctoolbox import snr_to_enob, enob_to_snr, amplitudes_to_snr
```

## 实验 1：生成一个归一化正弦

运行完整 workflow：

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\whole_workflow_demo.py
```

看输出：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\whole_workflow\01_spectrum_clean_vs_nonideal.png
```

观察：

- clean sine 是数学理想信号。
- generated ADC output 加了失真、噪声、量化。

## 实验 2：查看 SAR bit trial

运行：

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\sar_adc_model_study.py
```

观察控制台中的：

```text
SAR bit-trial trace for one sample
```

每一行代表：

```text
当前 bit 尝试加一个 DAC weight
如果 vin >= v_test，则 bit = 1
否则 bit = 0
```

这就是 SAR ADC 的逐次逼近过程。

## 你应该修改的参数

打开：

```text
agent_playground/adctoolbox_learning/demos/sar_adc_model_study.py
```

修改：

```python
num_bits = 8
```

再改成：

```python
num_bits = 12
num_bits = 16
```

观察：

- 理想情况下 bit 数越高，ENOB 越高。
- 但加入噪声后，ENOB 不一定随 bit 数无限提高。

## 阶段检查问题

如果你能回答这些问题，就可以进入 Stage 02：

1. `LSB = full_scale / 2^N` 里的 full_scale 是什么？
2. 为什么 ideal ADC 也有量化噪声？
3. 为什么 ENOB 不一定等于 ADC nominal bit 数？
4. `vin`、`bits`、`aout` 分别是什么？
5. 为什么本库常用 `0.0 ~ 1.0` 的归一化输入？

