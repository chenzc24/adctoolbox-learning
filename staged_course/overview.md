# ADC 八阶段学习总览

本课程面向“代码能力较强，但 ADC 和相关数学还在入门阶段”的学习者。

目标不是把 ADCToolbox 当黑盒调用，而是逐步建立下面这条链路：

```text
Python 数值仿真基础
  -> ADC 基础
  -> FFT 动态指标
  -> residual 误差分析
  -> SAR ADC 行为建模
  -> bit matrix 数字诊断
  -> sine-based 位权重校准
  -> 校准验证、模型边界与工程严谨性
```

每个阶段都包含三条线：

```text
数学线：为了理解算法，需要补哪些数学
电路线：为了理解 ADC，需要补哪些电路直觉
代码线：本仓库哪些代码对应这些概念
```

现在每个阶段还增加了更适合初学者的学习锚点：

```text
初学者先抓住的主线
最小例子或手算例子
读代码时具体追踪哪些变量
容易混淆的点
阶段检查问题
```

## 目录结构

```text
staged_course/
├── overview.md
├── stage_00_python_numerics/
│   └── stage_00_python_numerics.md
├── stage_01_adc_basics/
│   └── stage_01_adc_basics.md
├── stage_02_fft_metrics/
│   └── stage_02_fft_metrics.md
├── stage_03_error_analysis/
│   └── stage_03_error_analysis.md
├── stage_04_sar_modeling/
│   └── stage_04_sar_modeling.md
├── stage_05_digital_bits/
│   └── stage_05_digital_bits.md
├── stage_06_calibration/
│   └── stage_06_calibration.md
└── stage_07_validation_rigor/
    └── stage_07_validation_rigor.md
```

## 八个阶段

| 阶段 | 主题 | 你应该获得的能力 |
|---|---|---|
| Stage 00 | Python 数值仿真基础 | 看懂 array shape、矩阵乘法、随机种子、归一化单位 |
| Stage 01 | ADC 基础、采样、量化、LSB | 看懂 ADC 输入、输出 code、量化噪声和 ideal ENOB |
| Stage 02 | FFT 和动态性能指标 | 能解释 SNR/SNDR/SFDR/THD/ENOB/NSD |
| Stage 03 | 正弦拟合和 residual 分析 | 能从 waveform 中分离 ideal sine 与 error |
| Stage 04 | SAR ADC 行为建模 | 能理解 bit trial、CDAC weight、mismatch、noise |
| Stage 05 | bit matrix 数字诊断 | 能直接分析 ADC raw bits，而不只看 waveform |
| Stage 06 | sine-based calibration | 能理解 `calibrate_weight_sine` 的整体数学逻辑 |
| Stage 07 | 验证与严谨性 | 能判断校准结果是否可信，并知道模型边界 |

## 推荐学习节奏

不要一口气读完八个阶段。建议每个阶段按这个顺序：

1. 先读“初学者先抓住的主线”，把本阶段的大图抓住。
2. 看最小例子或手算例子，确认自己知道变量在做什么。
3. 再读数学部分，只要求理解概念，不要求严格推导。
4. 再读电路部分，把数学变量对应到 ADC 物理含义。
5. 然后看本仓库代码位置，先追踪指定变量，不要通读全部实现。
6. 跑推荐实验。
7. 回答阶段检查问题。

初学阶段最有效的读码方式是：

```text
带着一个变量去读代码
例如 bits、weights、aout、residual、freq
```

每次只追踪一个变量如何产生、如何变形、如何被用于指标计算。

如果检查问题答不上来，不要进入下一阶段。

## 统一运行环境

从 ADCToolbox 的 Python 子项目运行：

```powershell
cd E:\ADCToolbox\python
```

确认环境：

```powershell
uv run python -c "import adctoolbox; print(adctoolbox.__version__)"
```

复制官方示例：

```powershell
uv run adctoolbox-get-examples C:\Users\90590\adctoolbox_examples
```

运行本学习仓库的完整 demo：

```powershell
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

运行本学习仓库的 SAR demo：

```powershell
uv run python ..\learning\adctoolbox-learning\demos\sar_adc_model_study.py
```

## 代码库主线

ADCToolbox 的 Python 主线可以简化成：

```text
siggen/        生成输入和非理想信号
models/        ADC 行为模型，重点是 SAR
spectrum/      FFT 动态指标
aout/          analog output residual debug
dout/          digital output bit matrix debug
calibration/   bit weight calibration
toolset/       dashboard workflow
```

对应完整 ADC 校准闭环：

```text
input sine
  -> ADC model or real ADC capture
  -> raw waveform or raw bits
  -> nominal reconstruction
  -> spectrum and residual analysis
  -> diagnose mismatch/noise/distortion
  -> estimate calibrated weights
  -> reconstruct calibrated output
  -> verify on independent data
  -> report model assumptions and test conditions
```

## 最重要的心智模型

ADC 校准不是“让图变好看”，而是参数估计问题：

```text
观测数据 = 已知结构的模型 + 未知参数 + 噪声
```

在 SAR 位权重校准中：

```text
bits @ weights ≈ ideal sine
```

其中：

- `bits` 是 ADC 输出的 bit matrix。
- `weights` 是未知或不准确的数字重构权重。
- `ideal sine` 是已知输入形式，频率可已知或估计。
- 校准就是估计 `weights`。

Stage 07 会提醒你：一个校准结论是否可信，不只取决于训练数据上的 ENOB，而取决于独立验证、误差来源、模型边界和测试条件是否讲清楚。
