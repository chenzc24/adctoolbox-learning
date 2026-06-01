# ADC 六阶段学习总览

本课程面向“代码能力较强，但 ADC 和相关数学还在入门阶段”的学习者。

目标不是把 ADCToolbox 当黑盒调用，而是逐步建立下面这条链路：

```text
ADC 基础
  -> FFT 动态指标
  -> 误差 residual 分析
  -> SAR ADC 行为建模
  -> bit matrix 数字诊断
  -> sine-based 位权重校准
```

每个阶段都包含三条线：

```text
数学线：为了理解算法，需要补哪些数学
电路线：为了理解 ADC，需要补哪些电路直觉
代码线：本仓库哪些代码对应这些概念
```

## 目录结构

```text
staged_course/
├── overview.md
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
└── stage_06_calibration/
    └── stage_06_calibration.md
```

## 六个阶段

| 阶段 | 主题 | 你应该获得的能力 |
|---|---|---|
| Stage 01 | ADC 基础、采样、量化、LSB | 看懂 ADC 输入、输出 code、量化噪声和 ideal ENOB |
| Stage 02 | FFT 和动态性能指标 | 能解释 SNR/SNDR/SFDR/THD/ENOB/NSD |
| Stage 03 | 正弦拟合和 residual 分析 | 能从 waveform 中分离 ideal sine 与 error |
| Stage 04 | SAR ADC 行为建模 | 能理解 bit trial、CDAC weight、mismatch、noise |
| Stage 05 | bit matrix 数字诊断 | 能直接分析 ADC raw bits，而不只看 waveform |
| Stage 06 | sine-based calibration | 能理解 `calibrate_weight_sine` 的整体数学逻辑 |

## 推荐学习节奏

不要一口气读完六个阶段。建议每一阶段按这个顺序：

1. 先读数学部分，只要求理解概念，不要求严格推导。
2. 再读电路部分，把数学变量对应到 ADC 物理含义。
3. 然后看本仓库代码位置。
4. 跑推荐实验。
5. 回答“阶段检查问题”。

如果检查问题答不上来，不要进入下一阶段。

## 统一运行环境

从 Python 子项目运行：

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

运行本地完整 demo：

```powershell
uv run python ..\agent_playground\adctoolbox_learning\demos\whole_workflow_demo.py
```

运行本地 SAR demo：

```powershell
uv run python ..\agent_playground\adctoolbox_learning\demos\sar_adc_model_study.py
```

## 代码库主线

本仓库的 Python 主线可以简化成：

```text
siggen/        生成输入和非理想信号
models/        ADC 行为模型，重点 SAR
spectrum/      FFT 动态指标
aout/          analog output residual debug
dout/          digital output bit matrix debug
calibration/   bit weight calibration
toolset/       dashboard workflow
```

对应到完整 ADC 校准闭环：

```text
input sine
  -> ADC model or real ADC capture
  -> raw waveform or raw bits
  -> nominal reconstruction
  -> spectrum and residual analysis
  -> diagnose mismatch/noise/distortion
  -> estimate calibrated weights
  -> reconstruct calibrated output
  -> verify SNDR/SFDR/ENOB improvement
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

