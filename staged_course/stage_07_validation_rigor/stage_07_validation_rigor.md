# Stage 07：校准验证、模型边界与工程严谨性

## 本阶段如何承接 Stage 06

Stage 06 已经让你理解：

```text
bits -> calibrate_weight_sine -> calibrated_weights
bits @ calibrated_weights -> calibrated_signal
```

也就是说，你已经会把 SAR bit weight error 变成一个最小二乘估计问题：

```text
B @ w ≈ sine
```

Stage 07 不再主要学习一个新函数，而是学习如何判断：

```text
这个校准结论可信吗？
```

一个初学者常见回答是：

```text
ENOB 变好了，所以可信。
```

更工程化的回答应该是：

```text
训练数据和验证数据分开了吗？
换频率、换幅度、换相位后还有效吗？
改善的是 SFDR/THD，还是 SNR？
误差来源是 deterministic 还是 random？
模型有没有覆盖真实电路里的关键效应？
测试条件是否足够干净且写清楚？
```

这一步会把你从“会跑校准 demo”推进到“能评价校准结论”。

### Stage 06 交给 Stage 07 的检查清单

Stage 06 已经把校准模型讲清楚了，但每一个模型假设都要在 Stage 07 变成验证项：

| Stage 06 学到的点 | Stage 07 要验证什么 |
|---|---|
| `calibrated_signal = bits @ calibrated_weights` | 这组 weights 是否能泛化到独立 capture |
| `harmonic_order>1` 带有 source/test-chain nuisance 假设 | 比较 `H=1` 与 `H=3` 的 normalized weight delta 和验证指标 |
| bit matrix 可能 rank deficient | 校准前检查 bit activity、constant columns、merged columns、rank patch metadata |
| 静默 bit 会被恢复为 0，当前实现还缺 warning | 不把静默位的 0 权重解释成真实物理权重为 0 |
| column scaling 对纯 0/1 SAR bits 基本是 no-op | 不把 scaling 当作解决列相关性或冗余 SAR 病态的手段 |
| `calibrate_weight_sine` 有尺度/极性约定 | 比较频谱时保持 dBFS/full-scale 标尺一致 |
| 训练集 residual 变小 | 必须在不同频率、幅度、相位或噪声 realization 上复测 |

所以 Stage 07 的核心不是多跑几张图，而是把 Stage 06 的结论拆成：

```text
哪些是训练目标；
哪些是验证指标；
哪些是假设；
哪些是风险报警。
```

## 本阶段目标

学完本阶段，你应该能解释：

- 为什么校准结果不能只看训练数据。
- 为什么 ENOB 变好不等于模型完全正确。
- 如何区分 deterministic mismatch 和 random noise。
- 如何设计 train/test 分离的验证。
- 为什么 Monte Carlo 要看分布，而不是只看一个 seed。
- ADCToolbox 的行为级 SAR 模型有哪些边界。
- 测试条件为什么是指标的一部分。
- 校准如何影响 FOM，以及为什么校准本身也有代价。
- 如何把 `harmonic_order`、rank patch、bit activity 和尺度约定纳入校准可信度检查。
- 什么时候可以相信结果，什么时候只能把它当学习或算法原型。

## 对应孙老师课件主线

Stage 07 对应孙老师课件中最工程化的几条线：

```text
ch17 数据转换器测试：
     测试平台、输入源、时钟源、电源、采集和分析都会限制测量结果。
     同一个 ADC 在不同测试条件下可以得到不同 SNR/SNDR/SFDR。

ch16 ADC FOM：
     FOM 适合趋势比较，但不能替代完整规格表。
     校准能改善指标，也会带来功耗、面积、时间和复杂度代价。

ch12 高速/低功耗 SAR：
     行为模型能解释 SAR bit trial 和权重失配，但真实高速电路还受
     DAC settling、reference droop、comparator metastability、kickback 等影响。

ch5/ch6/ch7：
     采样、开关电容和比较器带来的噪声/动态误差，决定哪些误差可校准、哪些只能降低或平均。
```

一句话：

```text
Stage 07 把“算法结果”放回测试、电路和系统约束里审查。
```

## 本阶段边界：只讲验证，不重复后续频谱专题

Stage 07 是一个横向检查阶段。它教你如何判断结论是否可信，但不展开每一种高速或带宽相关机制：

| 后续阶段 | 机制 | Stage 07 只保留的检查角度 |
|---|---|---|
| Stage 08 | TI-ADC offset/gain/skew spur | 验证校准前后 spur 是否真实改善、是否跨输入条件稳定 |
| Stage 09 | subsample debug output alias | 报告 debug 输出采样率、N、alias 解释和通道覆盖 |
| Stage 10 | oversampling / NTF / noise shaping | 报告 OSR、信号带宽、NTF 假设和带内指标 |

所以本阶段不重复推导 `k*fs/M`、subsample alias 公式或 NTF 积分；它只提醒你：

```text
任何这些结论都要写清测试条件、模型边界和可泛化范围。
```

## 初学者先抓住的主线

看到任何校准结果时，先按这个模板检查：

| 问题 | 为什么重要 |
|---|---|
| 校准用的数据和验证用的数据是否不同 | 防止只在训练集上变好 |
| 输入频率是否变化过 | 防止只对某个 bin 偶然有效 |
| 输入幅度是否变化过 | 防止只覆盖部分 code/bit pattern |
| 输入相位是否变化过 | 防止采样点位置偶然匹配 |
| SNR、SNDR、SFDR、THD 是否一起报告 | 判断改善来自噪声还是失真 |
| residual 或 error spectrum 是否检查 | 防止指标好看但误差有结构 |
| bit activity / radix / overflow 是否检查 | 防止 raw bits 或权重本身不合理 |
| `H=1` 与 `H=3` 权重是否差很多 | 判断 harmonic nuisance 假设是否显著影响 weights |
| rank patch 是否发生，是否有静默 bit | 防止把不可观测 bit 的返回值误当成物理权重 |
| dBFS/full-scale 标尺是否一致 | 防止把尺度错误误判成校准改善或恶化 |
| noise/mismatch seed 是否说明 | 保证仿真可复现 |
| 测试源和时钟是否足够干净 | 防止测到的是 test bench 限制 |
| 模型假设是否写清楚 | 防止把行为模型误当成真实芯片结论 |

这个模板比单个 ENOB 数字重要得多。

## 核心判断

ADCToolbox 很适合：

```text
学习 ADC 行为建模
理解 SAR bit decision
验证 bit weight calibration 思想
做算法原型和可视化 debug
建立“误差 -> 数据表现 -> 校准效果”的因果链
```

但它不能直接替代：

```text
晶体管级仿真
版图后寄生验证
真实测试板 characterization
生产测试校准流程
严格计量级 ADC characterization
```

换句话说：

```text
它是学习和算法验证工具，不是最终工程签核工具。
```

## 证据等级：从“能跑”到“可信”

Stage 07 最容易变成一句空话：

```text
要严谨验证。
```

为了避免空话，可以把校准证据分成几个等级。等级越高，能支持的结论越强。

| 等级 | 你做了什么 | 可以声称什么 | 还不能声称什么 |
|---|---|---|---|
| Level 0 | 只看 training capture | 代码能跑，训练目标下降 | 校准能泛化 |
| Level 1 | 独立 test capture，同一颗 chip / mismatch realization | 权重对同一颗芯片的另一个输入有效 | 对频率、幅度、相位普遍有效 |
| Level 2 | 扫 frequency / amplitude / phase / noise seed | 在这个输入范围内较稳定 | 对所有 PVT、架构和测试链路有效 |
| Level 3 | 多 mismatch seed / Monte Carlo 分布 | 对一组随机芯片有统计稳定性 | 对真实硅片生产分布有效 |
| Level 4 | 写清模型边界、测试源限制、校准代价和失效案例 | 可以作为严肃工程/论文级论证的一部分 | 仍不能替代晶体管级仿真和实测 |

如果只有 Level 0，报告里最多说：

```text
这个校准器能拟合这条训练记录。
```

如果做到 Level 1/2，才可以说：

```text
这组 calibrated weights 在独立输入上仍然改善了指标。
```

如果做到 Level 3/4，才更接近工程判断：

```text
在这个 mismatch model 和测试范围内，校准收益有统计稳定性，并且已说明模型边界。
```

这张表的目的不是制造形式主义，而是防止把一个漂亮 demo 说成完整工程结论。

## 数学需要补什么

### 1. 校准是参数估计，不是魔法修复

Stage 06 的校准目标可以写成：

```text
min_w ||B_train @ w - sine_model_train||^2
```

这只是让训练数据上的误差最小。

真正关心的是：

```text
B_test @ w_cal
```

在独立测试数据上是否也表现好。

所以要分清：

```text
training objective:
  用来估计参数。

validation objective:
  用来判断参数是否泛化。
```

如果只看训练数据，就可能出现：

```text
训练集 residual 很小；
测试集 spectrum 没改善，甚至变差。
```

这就是 overfitting 或模型不匹配。

### 2. train/test 分离不是机器学习专属

任何校准算法都需要独立验证，因为校准本质是：

```text
从一组观测估计参数；
希望这些参数对未来数据仍然有效。
```

一个最小 SAR 校准验证流程是：

```text
训练：
  vin_train -> bits_train -> estimate calibrated_weights

验证：
  vin_test -> bits_test -> bits_test @ calibrated_weights -> analyze_spectrum
```

训练和验证至少应该在某些维度上不同：

```text
different frequency
different phase
different amplitude
different noise realization
different capture length
```

仿真中还可以区分：

```text
same mismatch realization:
  表示同一颗芯片，只换测试输入。

different mismatch realization:
  表示不同芯片，用来做 Monte Carlo 分布。
```

这两个问题不要混在一起。

### 3. 误差分解：deterministic、random、model error

校准后的 residual 可以粗略分成：

```text
e[n] = e_det_remaining[n] + e_random[n] + e_model[n]
```

其中：

```text
e_det_remaining:
  尚未修掉的确定性误差，如残余权重误差、谐波、稳定 spur。

e_random:
  热噪声、采样噪声、比较器随机噪声、随机 jitter。

e_model:
  模型没有覆盖的误差，如 reference droop、动态 settling、kickback、温漂。
```

如果校准有效且主要问题是 CDAC mismatch，常见变化是：

```text
e_det_remaining 下降
-> harmonic / spur 下降
-> SFDR / THD 改善

e_random 基本不变
-> SNR 或 noise floor 基本不变
```

如果你看到：

```text
SNR 大幅改善，但 SFDR/THD 变化不大
```

就要非常小心。权重校准通常不应该“消灭随机噪声”。这种结果可能意味着：

```text
分析设置变化；
信号幅度/归一化变化；
训练和测试不独立；
噪声估计方法变化；
或代码使用方式有误。
```

### 4. ENOB 是折算结果，不是事实本身

孙老师 ch3 强调：

```text
ENOB = (SNDR - 1.76) / 6.02
```

它是用 SNDR 反推的等效理想 ADC 位数。

所以 ENOB 包含：

```text
输入幅度
频率
采样率
窗口
带宽
谐波排除规则
噪声估计方法
测试源质量
ADC 本身误差
```

一个 ENOB 数字不能单独回答：

```text
误差来自哪里？
校准是否真的修了权重？
测试是否可信？
模型是否完整？
```

所以 Stage 07 的习惯是：

```text
ENOB 用来摘要；
SNDR/SNR/SFDR/THD/residual/bit diagnostics 用来解释。
```

### 5. Monte Carlo 看分布，不看单次漂亮 seed

如果误差来自随机 mismatch，例如 unit-cap-scaled mismatch，那么单次 seed 只代表一颗“随机芯片”。

工程上更关心：

```text
median
p10 / p90
min / max
std
yield-like behavior
```

比如 `exp_d16_sar_unit_cap_mismatch_mc.py` 对每个 mismatch sigma 运行：

```text
N_MC = 32
```

并统计：

```text
min / p10 / median / p90 / max / mean / std
```

这比单次结果更接近工程判断：

```text
校准是否稳定？
高 mismatch 下是否有长尾失败？
冗余结构是否提高最差情况？
```

不要用一个 seed 的漂亮图替代分布。

### 6. validation matrix：验证不是只换一次输入

更完整的验证可以设计成矩阵：

| 维度 | 为什么要扫 |
|---|---|
| input frequency | jitter、settling、动态非线性可能随频率变化 |
| input amplitude | bit coverage、clipping、非线性强度随幅度变化 |
| input phase | coherent capture 的采样点位置可能偶然有利 |
| capture length | 短记录可能 rank/conditioning 差或 overfit |
| noise seed | 随机噪声 realization 不能只看一次 |
| mismatch seed | 不同芯片的权重误差不同 |
| temperature / supply | 真实芯片上权重、offset、noise 可能漂移 |
| window / side_bin / nf_method | 频谱指标依赖分析设置 |

在学习阶段，不必一次扫所有维度；但你要知道：

```text
没有扫过的维度，就是结论没有覆盖的范围。
```

### 7. 行为模型边界

`python/src/adctoolbox/models/sar.py` 是行为级 SAR 模型。

它建模了：

```text
ideal / redundant bit weights
unit-cap-scaled gaussian mismatch
sampling_noise_rms
comparator_noise_rms
MSB-to-LSB bit trial logic
quant_range normalization
actual weights vs digital reconstruction weights
```

它没有完整建模：

```text
CDAC 动态 settling waveform
reference transient / droop 的真实网络响应
comparator metastability timing
kickback 对采样节点或 CDAC 节点的反馈
switch charge injection 的细粒度波形
bootstrapped switch 的非线性
PVT、温漂、老化
版图寄生造成的频率相关效应
输入驱动器和采样网络相互作用
真实测试板信号源/时钟/电源限制
```

所以当模型能解释某个现象时，可以说：

```text
在这些假设下，CDAC mismatch + sine calibration 能解释并改善这个 spur。
```

不要直接说：

```text
真实芯片一定就是 CDAC mismatch。
```

真实芯片还需要更多证据。

### 8. 校准改变的是数字重构，不是模拟历史

Stage 04/06 已经讲过：

```text
bits = sar_convert(vin, actual_analog_weights)
aout_cal = bits @ calibrated_digital_weights
```

如果 analog conversion 阶段已经损失信息，数字权重无法完全恢复。

典型不可完全恢复情况：

```text
比较器随机翻转太多；
前面 bit 决策错误超过 redundancy margin；
输入 clipping；
采样保持已经严重失真；
reference droop 依赖历史状态；
time-interleaving timing skew 没有被模型覆盖；
```

所以一个重要判断是：

```text
这个错误是“重构权重用错了”，还是“bit decision 本身已经错得不可逆”？
```

前者适合 Stage 06 的权重校准；后者需要电路设计、冗余、时序、参考、采样或更复杂校准。

## 电路需要理解什么

### 1. 测试平台可能限制测量结果

孙老师 ch17 强调：测试不是单纯测数字，而是搭建一个系统。

一个 ADC test bench 通常包括：

```text
signal source
clock source
power / bias
DUT
data capture
data analysis
```

每一部分都可能成为瓶颈：

```text
信号源失真比 ADC 大 -> 测到的 THD 可能是信号源的。
时钟 jitter 太大       -> 测到的 SNR 可能是时钟限制。
电源噪声大             -> 频谱里可能出现 supply-related spur。
采集接口出错           -> raw bits 可能已有数字错误。
窗口/频率设置不当      -> leakage 影响 SNR/SFDR。
```

仿真里这些限制可能不存在；真实测试里必须说明。

### 2. coherent sampling 和 window 是测试条件

如果输入频率和采样频率满足整数周期关系：

```text
Fin / Fs = k / N
```

则：

```text
coherent sampling
```

能量集中在 FFT bin 上，leakage 小。

如果不相干，就需要 window：

```text
hann
hamming
blackman
...
```

但 window 会改变：

```text
amplitude correction
noise bandwidth
side-bin 选择
noise floor 估计
```

所以报告 spectrum 指标时，至少要写清：

```text
N
Fs
Fin 或 bin
win_type
side_bin
max_harmonic
nf_method
是否去 DC
输入幅度 / max_scale_range
```

### 3. FOM 不能替代完整规格

孙老师 ch16 讲 FOM 的价值和局限。

Walden FOM：

```text
FOM_W = Power / (2^ENOB * fs)
```

Schreier FOM：

```text
FOM_S = SNDR + 10*log10(BW/Power)
```

校准可能提升 ENOB 或允许更小电容、更低模拟精度，从而改善 FOM。

但校准也有代价：

```text
训练时间
数字计算功耗
存储校准参数
后台 dither 或校准信号
测试复杂度
生产测试时间
温度/电压漂移下重校准需求
```

所以正确说法不是：

```text
加校准一定更好。
```

而是：

```text
校准是否以可接受的系统代价换来了足够的性能、功耗或面积收益？
```

## 本库对应代码

校准：

```text
python/src/adctoolbox/calibration/calibrate_weight_sine.py
python/src/adctoolbox/calibration/_lstsq_solver.py
python/src/adctoolbox/calibration/_post_process.py
```

SAR 行为模型：

```text
python/src/adctoolbox/models/sar.py
```

频谱验证：

```text
python/src/adctoolbox/spectrum/analyze_spectrum.py
python/src/adctoolbox/spectrum/quick_sndr.py
python/src/adctoolbox/spectrum/compute_spectrum.py
```

analog residual 验证：

```text
python/src/adctoolbox/aout/analyze_error_spectrum.py
python/src/adctoolbox/aout/analyze_error_pdf.py
python/src/adctoolbox/aout/analyze_error_autocorr.py
python/src/adctoolbox/aout/analyze_error_by_value.py
python/src/adctoolbox/aout/analyze_error_by_phase.py
```

digital raw bit 验证：

```text
python/src/adctoolbox/dout/analyze_bit_activity.py
python/src/adctoolbox/dout/analyze_weight_radix.py
python/src/adctoolbox/dout/analyze_overflow.py
python/src/adctoolbox/dout/analyze_enob_sweep.py
```

推荐示例：

```text
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

本地学习闭环：

```text
learning/adctoolbox-learning/demos/whole_workflow_demo.py
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

## 推荐验证流程

### Step 0：校准前 preflight

在调用 `calibrate_weight_sine` 前，先做最低限度的输入健康检查：

```text
1. freq 是否是 normalized Fin/Fs，而不是 Hz。
2. bits shape 是否正确，bit order 是否符合 MSB -> LSB 约定。
3. bit activity 是否合理，是否有大量 constant columns。
4. 输入幅度是否覆盖足够 code，低位是否被激励。
5. 是否预期会发生 rank patch，是否能接受 nominal-ratio 分配。
6. 是否需要比较 H=1 和 H=3，检查 harmonic nuisance 假设是否影响 weights。
7. max_scale_range / dBFS 标尺是否在 before/after/oracle 间一致。
```

如果 preflight 已经发现：

```text
bit 几乎不翻；
所有列常数；
freq 单位不对；
输入严重 clipping；
```

就不要急着解释校准结果。先修测试条件，否则后面的 ENOB / SFDR 都只是症状。

### Step 1：固定“芯片”

仿真中先抽一组 actual weights：

```python
rng = np.random.default_rng(seed)
actual_weights = sar_apply_cap_mismatch(nominal_weights, sigma=sigma, rng=rng)
```

这代表同一颗行为模型里的随机芯片。这里的 `actual_weights` 是仿真真值；真实芯片上
通常只能通过校准或测试间接估计数字重构权重。

### Step 2：生成训练输入

例如：

```text
train_bin = 997
phase = 0
amplitude = 0.45 full-scale
```

得到：

```python
bits_train = sar_convert(vin_train, actual_weights)
```

### Step 3：估计校准权重

```python
cal = calibrate_weight_sine(
    bits_train,
    freq=train_bin / n_train,
    nominal_weights=nominal_weights,
    harmonic_order=3,
)

weights_cal = cal["weight"]
```

### Step 4：生成独立验证输入

至少换一个频率或相位：

```text
test_bin = 1231
phase = 0.37 rad
same actual_weights
```

得到：

```python
bits_test = sar_convert(vin_test, actual_weights)
```

### Step 5：比较三种重构

```python
before = sar_reconstruct(bits_test, nominal_weights)
after  = bits_test.astype(float) @ weights_cal
oracle = sar_reconstruct(bits_test, actual_weights)
```

解释：

```text
before:
  未校准数字重构。

after:
  校准权重重构。
  注意校准权重的绝对尺度由拟合归一化决定；比较频谱指标通常没问题，
  但若要和 oracle waveform 逐点比较，应先确认或统一权重尺度。

oracle:
  仿真里知道 actual_weights 时的“上限参考”。
  真实芯片上通常没有这个。
```

### Step 6：多指标判断

至少比较：

```text
SNDR
SNR
SFDR
THD
ENOB
harmonic levels
noise floor
residual spectrum
bit activity
weight radix
overflow
```

如果只比较 `ENOB`，信息太少。

## 最小可执行验证实验

可以按这个组合练习：

```text
训练：
  N = 8192
  Fin bin = 997
  phase = 0
  amplitude = 0.45 full-scale

验证 1：
  N = 8192
  Fin bin = 1231
  phase = 0.37 rad
  amplitude = 0.45 full-scale

验证 2：
  N = 8192
  Fin bin = 1231
  phase = 1.10 rad
  amplitude = 0.35 full-scale
```

每组都比较：

```text
nominal reconstruction
calibrated reconstruction
actual-weight oracle（仅仿真）
```

判断方式：

```text
训练集提升明显、验证集也稳定提升 -> 结论较可信。
训练集提升明显、验证集不提升或变差 -> 怀疑 overfit / 频率估计 / 输入覆盖 / 模型不匹配。
训练和验证都不提升 -> 可能 mismatch 小、随机噪声主导、或校准输入信息不足。
```

## 实验 1：Monte Carlo mismatch 分布

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d16_sar_unit_cap_mismatch_mc.py
```

这个例子体现 Stage 07 的两个重点：

```text
1. 不同 mismatch sigma 下，校准前后 ENOB 分布如何变化。
2. strict binary 与 radix ~1.8 redundant SAR 哪个在随机 mismatch 下更稳。
```

读图时不要只看中位数，还要看：

```text
min / max envelope
p10 / p90
高 sigma 下是否出现长尾失败
after calibration 是否稳定接近目标
```

## 实验 2：同一错误下比较架构

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
```

这个例子固定：

```text
MSB actual weight +1%
```

比较：

```text
Strict binary
3rd-weight repeat redundancy
```

重点看：

```text
first_decision_margin_lsb
before ENOB
after ENOB
ideal actual-weight ENOB
```

它说明：

```text
同样的权重错误，在不同架构下可恢复程度不同。
```

## 实验 3：训练长度与 overfitting

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

这个例子非常重要，因为它会同时画：

```text
校准 capture 上的 ENOB
独立 test capture 上的 ENOB
两者 overlay
```

你应该重点观察：

```text
短训练记录可能在训练集上看起来很好；
但在独立测试集上泛化差；
训练样本增加后，测试集 ENOB 分布才稳定。
```

这就是“训练集变好不等于结论可信”的直接证据。

## 实验 4：本地完整 workflow

运行：

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

重点看：

```text
03_sar_model_and_calibration.png
04_digital_debug_bits_and_weights.png
spectrum_metrics.csv
workflow_summary.json
```

建议你按这个顺序读结果：

```text
1. mismatch_nominal_weights 的 SFDR/THD 是否变差。
2. after_sine_calibration 的 SFDR/THD 是否改善。
3. SNR 是否基本不变。
4. bit activity 是否合理。
5. calibrated weight radix 是否合理。
```

如果这些互相一致，说明：

```text
CDAC mismatch -> deterministic spur -> sine calibration 修正权重
```

这条因果链比较可信。

## 如何解释常见结果

| 现象 | 可能解释 |
|---|---|
| SFDR 明显改善，SNR 几乎不变 | 权重 mismatch 被修正，但随机噪声底没变 |
| THD 改善，ENOB 只小幅提升 | 原本性能同时受失真和噪声限制 |
| 校准后训练集很好，测试集差 | 过拟合、训练样本不足、输入覆盖不足、频率估计偏差 |
| 校准后测试集变差 | 模型不匹配、`freq` 错、bit order 错、rank/conditioning 差 |
| 低 mismatch 下二进制和冗余差距小 | error 仍在严格二进制可处理范围内 |
| 高 mismatch 下冗余结构更稳 | redundancy 给错误决策留下修正空间 |
| `actual_weights` oracle 也不理想 | 随机噪声、比较器误差或不可恢复决策已经主导 |
| 权重校准后 SNR 大幅改善 | 需要检查分析设置，权重校准通常不该消除随机噪声 |
| ENOB 很高但 SFDR 有突出 spur | 单个大 spur 可能被总功率指标掩盖，必须看 SFDR/频谱图 |

## 失败归因：先查什么，后查什么

当校准结果不好，或者结果好得不合理时，按这个顺序排查：

1. **复现性**

```text
同一 seed、同一输入、同一分析设置能不能复现？
```

如果不能复现，先不要讨论物理原因。

2. **分析设置**

```text
freq 是否 normalized；
window / side_bin / nf_method 是否一致；
max_scale_range 是否一致；
是否去 DC；
训练和验证是不是混用了不同标尺。
```

很多“校准改善/恶化”其实是分析口径变了。

3. **raw bit 健康度**

```text
bit activity 是否合理；
是否有 constant columns；
是否 rank deficient；
是否出现静默 bit 被恢复为 0；
是否存在 bit order 错误。
```

如果 raw bits 本身不可观测，后面的 weight 拟合没有神通。

4. **训练/验证分离**

```text
训练集是否和测试集独立；
是否只在同一个 frequency / phase / amplitude 上验证；
是否换过 noise realization。
```

训练集好、测试集差，优先怀疑 overfit、频率估计、输入覆盖或模型不匹配。

5. **harmonic 假设**

```text
H=1 与 H=3 的 normalized weight delta 是否很大；
H=3 是否把 source harmonic 当 nuisance；
H=3 是否也可能投影掉 mismatch harmonic。
```

诊断目的不是判断 harmonic 到底来自哪里，而是判断这个归因假设是否已经影响 weights。

6. **仿真 oracle**

如果是行为仿真，检查：

```text
actual-weight oracle 是否已经接近理想；
如果 oracle 也不理想，说明随机噪声或不可恢复 bit decision 已经主导。
```

7. **模型边界**

最后再问：

```text
这个现象是不是 sar.py 根本没建模？
例如 reference droop、settling waveform、metastability、kickback、PVT drift。
```

这个顺序很重要：先排除使用错误和分析错误，再谈物理解释。

## 报告一个校准实验时至少写什么

一个严谨的校准报告至少包含：

```text
ADC / model:
  bit 数、架构、nominal weights、是否 redundancy、quant_range

nonideality:
  mismatch model、sigma、sampling noise、comparator noise、seed

training:
  N、Fin/bin、Fs、amplitude、phase、freq 是否已知、harmonic_order

validation:
  N、Fin/bin、Fs、amplitude、phase、是否独立 capture

analysis:
  window、side_bin、max_harmonic、nf_method、max_scale_range、是否去 DC

results:
  before/after 的 SNDR、SNR、SFDR、THD、ENOB
  residual/error spectrum
  bit activity、radix、overflow
  H=1 vs H=3 normalized weight delta（如果 harmonic_order 是关键假设）
  rank patch / constant bits / merged bits（如果发生）

scope:
  模型包含什么、不包含什么
  结论适用在哪些输入范围和条件下
```

这比单独说：

```text
ENOB improved from X to Y
```

有价值得多。

## 结论应该怎么写

弱证据的写法：

```text
在这条训练记录上，calibrated_signal 的拟合误差下降。
```

中等证据的写法：

```text
在同一 mismatch realization 的独立 test capture 上，SFDR/THD 仍然改善，
且 SNR 基本不变，符合 deterministic weight error 被修正的预期。
```

更强证据的写法：

```text
在多个 frequency / amplitude / phase 和多个 mismatch seed 下，
校准后 SFDR/THD 分布稳定改善；报告同时给出 bit activity、rank patch、
H=1/H=3 sensitivity、模型边界和测试条件。
```

不建议的写法：

```text
ENOB 变高，所以校准正确。
数字校准消除了噪声。
这个行为模型证明真实芯片一定由 CDAC mismatch 主导。
H=3 结果更好，所以 harmonic_order 越高越好。
```

Stage 07 的语言要和证据等级匹配。证据只覆盖哪里，结论就只能写到哪里。

## 容易混淆的点

- train/test 分离不是机器学习专属概念，任何校准算法都需要独立验证。
- 行为级模型中 `actual_weights` 可见，是因为仿真知道真值；真实芯片上通常不知道。
- Monte Carlo 结果要看分布，不要只看某一次 seed 的漂亮结果。
- Level 0 的训练集改善只能证明拟合成功，不能证明校准可信。
- 一个模型“有用”不等于“完整”。有用表示它能解释目标问题，完整表示它覆盖所有重要物理效应。
- 校准改善 SFDR 但不改善 SNR，通常是合理现象，不要立刻判断算法失败。
- `analyze_spectrum` 的设置变化会影响结果；比较 before/after 时设置必须一致。
- `H=1` 和 `H=3` 的权重差异是风险报警，不是 harmonic 来源判决器。
- rank patch 发生时，要报告哪些列被 drop / merge；否则权重解释不完整。
- FOM 改善不代表系统一定更好；校准本身也消耗资源。
- 真实测试中，信号源、时钟、电源和采集链路可能比 ADC 本身更差。
- 如果 bit decision 本身不可恢复，数字权重校准无法完全修复。
- 如果验证只覆盖一个频率和一个幅度，结论就只在那个小范围内较可信。

## 完成 Stage 07 后要形成的习惯

以后看到任何 ADC 校准结果，先问四组问题：

```text
数据问题：
  训练和测试分开了吗？
  输入覆盖够吗？
  bit matrix 条件好吗？

指标问题：
  SNDR/SNR/SFDR/THD/ENOB 是否一起看？
  residual 和 error spectrum 是否支持同一个结论？

物理问题：
  误差是 deterministic 还是 random？
  这个模型包含了主要物理效应吗？

工程问题：
  测试条件写清了吗？
  校准代价值得吗？
  结论能泛化到哪些频率、幅度、温度和芯片样本？
```

一句话总结：

```text
Stage 07 的目标不是让你更会跑代码，而是让你不被漂亮指标骗到。
```

## 阶段检查问题

1. 为什么不能只用训练数据判断校准是否有效？
2. 为什么校准通常更容易改善 SFDR/THD，而不是随机噪声造成的 SNR？
3. `actual_weights`、`nominal_weights`、`calibrated_weights` 应该如何分别用于转换和重构？
4. 哪些 SAR 真实电路效应没有被 `sar.py` 完整建模？
5. 一个严谨的校准实验至少应该报告哪些测试条件？
6. 为什么 Monte Carlo 要看 median / p10 / p90，而不是只看一个 seed？
7. 如果训练集 ENOB 很高、测试集 ENOB 很低，可能是什么原因？
8. 为什么 FOM 不能替代完整规格表？
9. 为什么测试源和时钟质量会影响 ADC 指标判断？
10. 如果校准后 SNR 大幅改善，你应该先检查什么？

完成这些问题后，你才真正从“会调用校准函数”进入“能判断校准结论是否可信”的阶段。
