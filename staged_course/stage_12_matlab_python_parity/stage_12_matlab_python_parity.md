# Stage 12：MATLAB / Python 版本对齐与 corner case 审计

## 本阶段定位：parity audit，不是新理论课

Stage 00-11 已经把 Python 版 ADCToolbox 的学习主线跑通：

```text
ADC 基础 -> FFT 指标 -> residual 诊断 -> SAR 建模 -> bit matrix
         -> calibration -> validation -> TI -> downsample -> oversampling
         -> examples atlas
```

Stage 12 不是再开一个新的 ADC 理论主题，而是回到仓库本身，回答一个工程问题：

```text
MATLAB 版本和 Python 版本到底对齐到什么程度？
哪里只是 API 名字不同？
哪里是默认参数、单位、数值细节或边界条件不同？
哪些差异会变成真实 corner case？
```

所以本阶段的角色是：

```text
Stage 11:
  跑完并解释 Python examples。

Stage 12:
  用 MATLAB 原版 / legacy / tests 反查 Python 实现，建立 parity map，
  并系统挖 corner case。
```

这不是为了“学 MATLAB 语法”。MATLAB 在这里的价值是：

```text
1. 原始算法语义参考；
2. 历史 API 行为参考；
3. Python port 的 parity 目标；
4. corner case 的对照来源。
```

---

## 本阶段目标

学完本阶段，你应该能回答：

- MATLAB `src/` 中哪些函数已经有 Python 对应实现。
- 哪些函数只是命名不同，哪些函数语义也变了。
- MATLAB 默认参数、返回顺序、单位约定、图形行为和 Python 是否一致。
- MATLAB tests / reference output 在 Python 版验证里扮演什么角色。
- legacy / dumped 函数哪些只是历史包袱，哪些可能藏着未移植功能。
- 如何为一个函数写 parity checklist，而不是只看“跑不跑得通”。
- 如何从 parity mismatch 中提炼 corner case / optimization item。

本阶段完成标准不是：

```text
把 MATLAB 代码逐行翻译一遍。
```

而是：

```text
对每个核心功能，知道 MATLAB 语义、Python 语义、已知差异、测试覆盖和 corner 风险。
```

---

## 仓库对象地图

本阶段主要看根仓库的这些路径：

```text
matlab/src/
  MATLAB 当前核心函数。

matlab/src/legacy/
  旧函数名 / 旧 API / 原始实现参考。

matlab/src/dumped/
  暂时未纳入当前主 API 的旧工具或转储实现。

matlab/src/shortcut/
  MATLAB 快捷封装。

matlab/data_generation/
  MATLAB 测试数据生成脚本。

matlab/tests/
  MATLAB 端测试入口和验证脚本。

reference_dataset/
  跨语言测试输入数据。

reference_output/
  MATLAB golden output 或参考输出。

python/src/adctoolbox/
  Python 版实现。

python/tests/
  Python 测试，包括 MATLAB parity 相关验证。

python/docs/source/python_matlab_parity.rst
  Python 文档里的 MATLAB parity 说明。
```

当前 MATLAB 核心 `matlab/src/*.m` 包括：

```text
adcpanel
alias
bitchk
cdacwgt
errsin
findbin
findfreq
ifilter
inlsin
noiseshape
ntfperf
perfosr
plotphase
plotres
plotspec
plotwgt
sinfit
tomdec
wcalsin
```

这 19 个函数是 Stage12 第一轮 parity audit 的主对象。

---

## MATLAB -> Python 初始映射表

这张表是起点，不是最终结论。后续每完成一个函数的 audit，都应补充：

```text
parity 状态；
默认参数差异；
返回值差异；
单位/归一化差异；
已跑测试；
corner case。
```

| MATLAB | Python 对应 | 初始判断 | 重点风险 |
|---|---|---|---|
| `plotspec` | `adctoolbox.spectrum.analyze_spectrum` | 强对应 | window、side bins、harmonic mask、OSR、SNR/SNDR/NSD 口径 |
| `plotphase` | `analyze_spectrum_polar` / `plot_spectrum_polar` | 强对应但图形语义需核对 | 相位对齐、harmonic phase、polar averaging |
| `sinfit` | `fit_sine_4param` | 强对应 | 迭代次数、初值、频率单位、收敛失败行为 |
| `findfreq` | `fit_sine_4param` / frequency estimation helpers | 部分对应 | 返回频率单位、低 SNR、非相干输入 |
| `findbin` | `find_coherent_frequency` / bin helpers | 部分对应 | 1-index vs 0-index、Hz vs normalized frequency |
| `tomdec` | `analyze_decomposition_time` / `decompose_harmonic_error` | 部分对应 | harmonic basis、相位参考、known frequency 入口 |
| `wcalsin` | `calibrate_weight_sine` | 强对应但高风险 | rank patch、harmonic nuisance、column scaling、polarity、multi-dataset |
| `cdacwgt` | `convert_cap_to_weight` / SAR helpers | 部分对应 | cap segmentation、normalization denominator、redundancy |
| `plotwgt` | `analyze_weight_radix` + plotting helpers | 部分对应 | radix、effres、significant weights、负权重 |
| `plotres` | `plot_residual_scatter` | 部分对应 | residual 定义、partial sum、输入 signal 约定 |
| `inlsin` | `analyze_inl_from_sine` / `compute_inl_from_sine` | 强对应但高风险 | sparse histogram、clip percent、code axis、INL/DNL 口径 |
| `errsin` | `analyze_error_by_phase` / `analyze_error_by_value` | 部分对应 | phase/value binning、AM/PM/base 分解、fit sine 前处理 |
| `ntfperf` | `oversampling.ntfperf` | 强对应 | frequency normalization、积分区间、TransferFunction 表达 |
| `noiseshape` | `ADC_Signal_Generator.apply_noise_shaping` | 部分对应 | 是否真实量化、FIR NTF、随机误差模型、稳定性边界 |
| `perfosr` | `oversampling.perfosr` | 强对应 | OSR 是分析带宽还是物理带宽、plot axis、harmonic 默认值 |
| `ifilter` | `oversampling.ifilter` | 强对应 | ideal brickwall、非因果、矩阵方向、不要误用于物理权重校准 |
| `alias` | alias / fold-frequency helpers | 部分对应 | Nyquist folding convention、负频率、边界点 |
| `bitchk` | `analyze_overflow` | 强对应但需核对 | suffix distribution、overflow 定义、负权重/零权重 |
| `adcpanel` | `generate_aout_dashboard` / `generate_dout_dashboard` | workflow 对应 | 2x4 vs 3x4/12-tool dashboard、自动数据类型、返回 report |

---

## 本阶段审计方法

### 1. 先写 parity spec，不急着跑代码

每个函数先写清楚：

```text
输入:
  shape、dtype、单位、是否列向量优先、是否接受矩阵。

默认参数:
  MATLAB 默认值是什么？
  Python 默认值是什么？

输出:
  返回顺序、dict key、单位、是否包含 figure handle。

图形行为:
  默认是否画图？
  是否保存图？
  是否返回 axes / figure？

数值口径:
  full-scale、dBFS、dBc、OSR、frequency normalization。

异常行为:
  空输入、NaN、常数输入、rank deficient、非相干输入。
```

这一步的目标是避免只比较最后一个数字：

```text
最后数字相近
  不代表 API 语义一致。

最后数字不同
  也不一定代表谁错，可能是默认窗口/单位/带宽不同。
```

### 2. 再跑最小 parity case

每个函数至少准备三类 case：

```text
happy path:
  标准 coherent sine，参数温和，确认主结果一致。

edge path:
  接近边界的输入，比如 near-Nyquist、small amplitude、OSR>1、rank deficient。

failure path:
  故意触发错误或不可辨识条件，确认错误信息是否清楚。
```

对频谱类函数，至少覆盖：

```text
coherent sine；
non-coherent sine + window；
harmonic near band edge；
OSR in-band mask；
near Nyquist fundamental；
DC / constant input；
very low amplitude。
```

对校准类函数，至少覆盖：

```text
full-rank bit matrix；
duplicate columns；
constant columns；
small amplitude insufficient bit activity；
multi-capture same weights；
H=1 vs H=3 harmonic nuisance；
known freq vs search freq。
```

### 3. 再看是否已有 tests 覆盖

MATLAB 端测试入口：

```powershell
cd E:\ADCToolbox
python matlab/tests/run_matlab_tests.py all --matlab-executable D:\MATLAB_2025b\bin\matlab.exe
```

可用 suite：

```text
common
aout
dout
all
jitter
```

当前环境已经能通过命令行调用 MATLAB：

```text
D:\MATLAB_2025b\bin\matlab.exe
R2025b Update 1
```

如果本机没有 MATLAB，`--missing-ok` 可以把缺失 MATLAB 当作可接受跳过；但这只能说明
环境缺失，不代表 parity 已验证。

Python 端要看：

```text
python/tests/
reference_dataset/
reference_output/
```

其中 `reference_output/` 很关键：它常常代表 MATLAB golden output，是 Python parity
测试的锚点。

### 3.1 MATLAB suite 分组运行顺序

MATLAB 测试可以按官方 wrapper 分成五个 suite：

```powershell
cd E:\ADCToolbox

python matlab/tests/run_matlab_tests.py common --matlab-executable D:\MATLAB_2025b\bin\matlab.exe
python matlab/tests/run_matlab_tests.py aout   --matlab-executable D:\MATLAB_2025b\bin\matlab.exe
python matlab/tests/run_matlab_tests.py dout   --matlab-executable D:\MATLAB_2025b\bin\matlab.exe
python matlab/tests/run_matlab_tests.py jitter --matlab-executable D:\MATLAB_2025b\bin\matlab.exe
python matlab/tests/run_matlab_tests.py all    --matlab-executable D:\MATLAB_2025b\bin\matlab.exe
```

各 suite 对应内容：

| suite | 覆盖脚本 | 对应课程主题 |
|---|---|---|
| `common` | `test_alias`, `test_noiseshape`, `run_basic`, `run_sinfit` | Stage 00/02/03/10 |
| `aout` | `run_tomdec`, `run_plotspec`, `run_plotphase_*`, `run_errsin_*`, `run_errpdf`, `run_errac`, `run_errspec`, `run_errevspec`, `run_inlsine` | Stage 02/03/11 |
| `dout` | `run_bitact`, `run_wscaling`, `run_wcalsin`, `run_bitsweep`, `run_ovfchk` | Stage 05/06 |
| `jitter` | `run_jitter_load` | Stage 03/04 |
| `all` | `common + aout + dout`，若 jitter 数据存在则也跑 `jitter` | 总 smoke |

更细的脚本清单：

```text
common:
  test_alias
  test_noiseshape
  run_basic
  run_sinfit

aout:
  run_tomdec
  run_plotspec
  run_plotspec_dynamic_metric_masks
  run_plotphase_fft
  run_plotphase_lms
  run_errsin_code
  run_errsin_phase
  run_errpdf
  run_errac
  run_errspec
  run_errevspec
  run_inlsine

dout:
  run_bitact
  run_wscaling
  run_wcalsin
  run_bitsweep
  run_ovfchk
```

还有一些脚本不完全在 `all` 默认 suite 中，需要后续单独补跑或静态审计：

```text
aout/run_fitstaticnl.m
aout/run_toolset_aout.m
dout/run_toolset_dout.m
dout/run_weightScaling.m
```

`matlab/data_generation/` 还有 24 个数据生成脚本，例如：

```text
gen_sinewave_jitter.m
gen_sinewave_glitch.m
gen_sinewave_drift.m
gen_sar_dout.m
gen_pipeline*_dout.m
gen_jitter_sweep_data.m
```

它们不应一开始就全部跑。更好的顺序是：

```text
1. common
   先确认 MATLAB 环境、基础函数、alias/noiseshape/sinfit。

2. aout
   对齐频谱、相位、误差分析、INL。

3. dout
   对齐 bit matrix、权重校准、overflow。

4. 单独补跑 toolset / fitstaticnl / weightScaling
   因为它们不完全在 all 默认 suite 里。

5. jitter / data_generation
   最后跑，因为依赖生成数据，且更像扩展验证。
```

这个顺序和 Stage12 的审计目标一致：先小后大，先基础后校准，先 deterministic fixture
后 generated-data。

### 4. 最后把差异分级

建议分四类：

```text
P0 / blocking:
  Python 结果明显错误，或函数在正常输入下崩溃。

P1 / correctness:
  指标口径错误、单位错、默认值导致误判。

P2 / workflow risk:
  单个函数没错，但组合用法会诱导错误结论。

P3 / docs/demo:
  主要是教学说明、图形标注、console 输出或示例设计问题。
```

只有当问题具备代码位置、可复现条件、原则推导和影响范围时，才进入
`learner/corner-cases-and-optimization.md`。

---

## 第一轮优先审计清单

### A. Spectrum parity：`plotspec` vs `analyze_spectrum`

优先级最高，因为很多后续工具依赖动态指标。

重点检查：

```text
window 默认值；
window coherent gain；
ENBW / noise power correction；
signal bin 和 side_bin；
harmonic bins mask；
OSR in-band mask；
SNR / SNDR / THD / SFDR / NSD 定义；
near-Nyquist harmonic folding；
max spur 标注。
```

已知高风险方向：

```text
动态指标 mask 不一致；
harmonic side bins 与 noise bins 重叠；
OSR 下 quick metric 和 full analyze metric 口径不一致；
console 输出把 SNR 和 SNDR 理论公式混比。
```

### B. Calibration parity：`wcalsin` vs `calibrate_weight_sine`

这是最容易出现“数学上能解、物理上不可信”的区域。

重点检查：

```text
dual basis 选择；
harmonic_order 的含义；
rank-deficiency patch；
constant bit columns；
column scaling；
polarity convention；
multi-capture shared weights；
nominal weights 在 rank patch 中的角色。
```

已知高风险方向：

```text
单 capture 无法区分源谐波和 ADC mismatch；
H=1 vs H=3 权重差异可作为 ambiguity warning；
全秩亏时应给清楚错误，而不是底层 IndexError；
部分静默 bit 被置 0 时需要 warning/metadata；
ifilter 后的 thermometer/unit code matrix 不应直接做无约束物理权重校准。
```

### C. AOUT debug parity：`errsin` / `tomdec` / `inlsin`

重点检查：

```text
fit sine 是否一致；
error by phase/value 的 binning 是否一致；
AM/PM/base 分解是否同口径；
INL/DNL 的 histogram 反推是否同口径；
code axis、clip percent、full-scale 解释是否一致。
```

已知高风险方向：

```text
sine histogram INL/DNL 在样本不足时会给 apparent INL/DNL；
value bins 与 code bins 混用会让图看起来更平滑但更乐观；
phase-binned AM/PM 分解有不可辨识平坦项；
fit_static_nonlin 图形若缺少 RMS，难判断拟合误差量级。
```

### D. DOUT debug parity：`bitchk` / `plotwgt` / `plotres`

重点检查：

```text
suffix overflow 定义；
range_min/range_max 与 ovf_percent 的语义；
radix / effres / significant weight 筛选；
residual scatter 的 partial-sum residual 定义；
负权重和小 trim weights 如何处理。
```

已知高风险方向：

```text
overflow 图容易被误读成真实 analog residue；
effres 容易被误读成 ADC 有效位数；
weight scaling 容易被误读成能解决 SAR 相关性病态。
```

### E. Oversampling parity：`ntfperf` / `perfosr` / `ifilter`

重点检查：

```text
frequency normalization；
NTF transfer function 表达；
积分区间；
OSR 是分析带宽还是物理采样率变化；
ifilter 的 matrix orientation；
brickwall mask 的边界 bin。
```

已知高风险方向：

```text
log frequency axis 让低频 bin 看起来很稀；
N=2^13 对 OSR=32 的带内 PSD 展示偏少；
ifilter 是离线非因果 brickwall，不是硬件 decimation filter；
ifilter + unregularized unit-weight LS 是病态 workflow。
```

### F. Dashboard parity：`adcpanel` vs Python dashboards

重点检查：

```text
自动判断 values/bits；
Pipeline A/B/C 是否对应；
AOUT dashboard 2x4 / 3x4 / 12-tool 版本；
DOUT dashboard 是否传 fs 和 freq；
batch report 是否和 single report 一致；
返回结构是否足够支持自动测试。
```

已知高风险方向：

```text
图形 dashboard 很容易“看起来对”，但底层 freq/fs/OSR 参数未传递完整；
batch 和 single 入口可能默认值不一致；
图形验证需要同时看像素/axis/annotation，不只看函数不报错。
```

---

## MATLAB / Python 常见差异清单

后续 audit 时每个函数都先过这张 checklist。

```text
1. 索引:
   MATLAB 1-index，Python 0-index。
   bin index、harmonic index、bit index 都可能偏 1。

2. 向量方向:
   MATLAB 默认 column vector。
   Python 常用 1D array 或 (N, M) matrix。
   ifilter / matrix functions 是否自动转置要重点看。

3. 频率单位:
   Hz、normalized cycles/sample、FFT bin 三种单位不能混。

4. Full-scale:
   Vpp、Vpeak、[-0.5,0.5]、[0,1]、dBFS convention 必须写清。

5. Plot 默认:
   MATLAB 常默认画图；
   Python 常用 create_plot / ax / show。

6. 返回值:
   MATLAB 多输出按位置；
   Python 多用 dict。
   legacy wrapper 可能同时保留旧 key。

7. 随机性:
   MATLAB rng 和 numpy rng 不同；
   只能比统计分布或固定数据，不应盲比逐点。

8. 窗函数:
   hann/hanning、periodic/symmetric、gain correction 可能不同。

9. 浮点容差:
   频谱指标用 dB，误差容差应按指标物理意义设，不要只用 allclose。

10. 错误处理:
   MATLAB 可能 warning 或返回 NaN；
   Python 应尽量给明确 ValueError / metadata。
```

---

## 本阶段输出物

建议最终形成三类产物：

```text
1. parity table:
   每个 MATLAB 核心函数对应 Python 函数、parity 状态、测试覆盖。

2. corner list:
   只有真实可复现、有代码位置和原则推导的问题，才进入 optimization log。

3. migration notes:
   给 MATLAB 用户迁移到 Python 时看的简短说明：
   函数名怎么换、默认值哪里不同、哪些结果不能直接比。
```

如果后续要贡献到主仓库文档，可以落到：

```text
python/docs/source/python_matlab_parity.rst
python/docs/source/api/*.rst
python/src/adctoolbox/_bundled_skills/skills/adctoolbox-user-guide/references/
```

但在学习阶段，先在本 Stage12 记录，不急着改主库文档。

---

## 阶段检查问题

1. MATLAB `plotspec` 和 Python `analyze_spectrum` 对齐时，为什么不能只比较 ENOB 一个数？
2. MATLAB 1-index 和 Python 0-index 会在哪些 ADC 指标里造成 off-by-one？
3. 为什么 `ifilter` 作为频带提取是合理的，但作为物理权重校准预处理很危险？
4. `wcalsin` / `calibrate_weight_sine` 的 parity 为什么比 `alias` / `ifilter` 更难？
5. 对一个 Python port，什么情况下应该追求 MATLAB bit-exact，什么情况下只应追求 semantic parity？
6. 如果 MATLAB 返回 warning 而 Python 返回 ValueError，这算不算 parity mismatch？
7. 为什么 reference output 只能证明某些 fixture 上一致，不能证明所有 corner case 都覆盖？
8. 如果 MATLAB legacy 函数和当前 MATLAB `src/` 语义不同，Python 应该对齐哪一个？

---

## 本阶段第一步建议

建议先按 suite 跑，再按函数深挖。

第一轮运行顺序：

```text
1. MATLAB common suite
2. MATLAB aout suite
3. MATLAB dout suite
4. 单独补跑 toolset / fitstaticnl / weightScaling
5. jitter / data_generation generated-data suite
```

第二轮函数审计顺序：

```text
1. plotspec -> analyze_spectrum
2. wcalsin -> calibrate_weight_sine
3. inlsin / errsin / tomdec -> aout debug tools
4. bitchk / plotwgt / plotres -> dout debug tools
5. ntfperf / perfosr / ifilter -> oversampling tools
6. adcpanel -> dashboard workflow
```

这样安排的原因是：

```text
suite 先跑:
  快速确认环境、已知 fixture 和 MATLAB 自身测试状态。

函数再审:
  对具体 mismatch 做语义拆解，找 corner case。
```

每完成一个函数，就补一段：

```text
MATLAB behavior:
Python behavior:
Matched:
Different:
Corner cases:
Tests / evidence:
Next action:
```

这样 Stage12 会自然变成一份可执行的 parity 审计日志，而不是静态函数列表。
