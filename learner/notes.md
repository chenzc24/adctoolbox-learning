# ADC Toolbox Notes
## 1. Modeling ADC 的输入/输出数据流

### I/O 数据流及物理意义

```text
最简数据流：理想正弦波参数
    -> 在 t[n] = n / Fs 上逐点取样，得到 vin
    -> sar_convert 得到 raw bit decisions / codes
    -> sar_reconstruct 得到 aout
```

Evidence:

```python
n = np.arange(N)
vin = DC + A * np.sin(2 * np.pi * Fin * n / Fs)  # shape == (N,)

weights = sar_ideal_weights(n_bits)       # shape == (n_bits,), MSB first
bits = sar_convert(vin, weights)          # shape == (N, n_bits), raw bit decisions
aout = sar_reconstruct(bits, weights)     # shape == (N,)
```

### Question: coherent sampling

逻辑链条：

```text
N 点 DFT 会把有限长度数据看成 N 点周期延拓
    -> 时间窗口长度 T = N / Fs
    -> 周期延拓的基频 f0 = 1 / T = Fs / N
    -> 第 k 个 DFT bin 对应 f_k = k * Fs / N
    -> DFT 系数 = 信号和第 k 个复指数基底取内积
    -> 如果 Fin = k * Fs / N，能量集中在第 k 个 bin
    -> 如果 Fin 不是 Fs/N 的整数倍，能量泄漏到多个 bin
```

所以 coherent sampling 是让采样窗口里刚好包含整数个输入周期：

```text
Fin / Fs = fin_bin / N
Fin = fin_bin * Fs / N
```

其中 `fin_bin` 就是 DFT 的 bin index，也是 N 点窗口里的正弦周期数。

如果 `Fin` 已定，就要选合适的 `Fs` 和 `N`，让：

```text
fin_bin = Fin * N / Fs
```

是整数。若 `Fs` 和 `N` 已定，则通常调整 `Fin` 到最近的 coherent frequency。

本库用 `find_coherent_frequency(fs, fin_target, n_fft)` 在目标频率附近找合适的 `fin_bin`，减少 FFT leakage。

连续傅里叶 vs DFT：

```text
CTFT：连续时间、无限长度/非周期信号 -> 连续频率
傅里叶级数：连续时间、周期 T 信号 -> k/T 离散频率
DFT：N 点离散数据，默认 N 点周期延拓 -> k*Fs/N 离散 bin
```

### Question: ADCToolbox 的系统闭环是什么？非理想 ADC 行为在哪些步骤加入？

ADCToolbox 的核心能力：

```text
造数据：ADC 建模
看数据：数据分析
修数据：校准方法
```

最终目的：

```text
把 ADC 的非理想问题变成可复现、可诊断、可校准、可反馈到电路设计和测试验证的工程流程。
```

核心闭环：

```text
1. 程序建模 / 数字校准闭环
   理想模型 -> 加非理想 -> 生成 bits/aout -> 分析 -> 校准 -> 比较校准前后
   目的：验证非理想的数据表现，以及数字校准是否有效。

2. 电路设计 / 仿真验证闭环
   电路设计 -> Spectre/SPICE/Verilog-A 仿真 -> 导入 ADCToolbox 分析
   -> 和行为模型比对 -> 判断误差来源 -> 改电路或交给数字校准 -> 再仿真
   目的：判断性能问题来自哪块电路，以及该改电路还是用数字校准。

3. 芯片测试 / 数据诊断闭环
   测试数据 -> ADCToolbox 分析 -> 和非理想模型对照 -> 尝试校准
   -> 改测试条件 / 反馈电路 / 修改算法
   目的：从真实数据中诊断问题来源。

4. 架构探索 / 规格权衡闭环
   架构假设 -> 行为级仿真 -> 加噪声/失配/非线性预算
   -> 分析指标 -> 评估校准需求 -> 调整架构
   目的：在电路细节完成前判断规格是否可达。

5. 算法开发 / 回归验证闭环
   新算法 -> 可控模型数据 -> 跑算法 -> 和 truth 对比 -> 加测试
   目的：保证分析和校准算法可靠、可复现。
```

非理想 ADC 行为加入的位置：

```text
1. 输入波形阶段：vin -> vin_nonideal
   例：thermal noise, jitter, static nonlinearity, clipping, drift

2. SAR 权重阶段：nominal_weights -> actual_weights
   例：sar_apply_cap_mismatch(...)

3. SAR 转换阶段：vin -> bits
   例：sampling_noise_rms, comparator_noise_rms

4. 数字重构阶段：bits -> aout
   例：nominal_weights / actual_weights / calibrated_weights
```

关键判断：

```text
这个 ADC 性能问题是什么造成的？
它能不能在数字域校准？
如果不能，应该回到哪一块电路或测试条件去修改？
```

- 随机噪声及其他非线性的加入

通过随机数 seed 控制随机噪声，保证可复现性。

本库推荐：

```python
rng = np.random.default_rng(42)
noise = noise_std * rng.standard_normal(N)
vin_noisy = vin + noise
```

旧写法也能用，但会影响全局随机状态：

```python
np.random.seed(42)
noise = np.random.normal(0, noise_std, N)
vin_noisy = vin + noise
```

SAR 模型中通常把 `rng` 显式传进去：

```python
bits = sar_convert(
    vin,
    actual_weights,
    sampling_noise_rms=40e-6,
    comparator_noise_rms=40e-6,
    rng=rng,
)
```
