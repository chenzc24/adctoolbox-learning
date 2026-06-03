# Raw Distillation Audit 2026-06-03

```yaml
scope: toolbox-wiki
status: in-progress
last_updated: 2026-06-03
```

## Verdict

Raw source distillation is now meaningfully underway, but not complete.

The wiki has absorbed the highest-value Markdown notes for ADC metrics,
testing, FFT, rank, least squares, noise, quantization, SAR, sampling circuits,
comparators, switched-capacitor settling, Pipeline ADCs, time interleaving,
oversampling, dither, filtering, and MATLAB code reading.

## Current Source Note Count

Current generated source notes: 21.

## Distilled Raw Markdown Notes

- `01_ADC学习_孙老师课件主线/03_ch3_ADC性能指标.md`
- `01_ADC学习_孙老师课件主线/05_ch5_采样电路.md`
- `01_ADC学习_孙老师课件主线/06_ch6_开关电容建立与噪声.md`
- `01_ADC学习_孙老师课件主线/07_ch7_电压比较器.md`
- `01_ADC学习_孙老师课件主线/10_ch10_Pipeline_ADC概念.md`
- `01_ADC学习_孙老师课件主线/11_ch11_Pipeline_ADC实现.md`
- `01_ADC学习_孙老师课件主线/12a_ch12_低功耗SAR_ADC.md`
- `01_ADC学习_孙老师课件主线/12b_ch12_高速SAR_ADC.md`
- `01_ADC学习_孙老师课件主线/13_ch13_Time_Interleaving.md`
- `01_ADC学习_孙老师课件主线/14_ch14_过采样ADC.md`
- `01_ADC学习_孙老师课件主线/16_ch16_ADC_FOM.md`
- `01_ADC学习_孙老师课件主线/17_ch17_数据转换器测试.md`
- `02_数学学习_ADC校准所需/01_向量矩阵与线性组合.md`
- `02_数学学习_ADC校准所需/02_线性方程组_矩阵秩_可观测性.md`
- `02_数学学习_ADC校准所需/03_最小二乘_从过定方程到校准.md`
- `02_数学学习_ADC校准所需/04_概率噪声_RMS_功率_方差.md`
- `02_数学学习_ADC校准所需/05_量化误差与白噪声模型.md`
- `02_数学学习_ADC校准所需/06_采样定理_傅里叶_DFT_FFT.md`
- `02_数学学习_ADC校准所需/07_卷积_滤波_频域乘法.md`
- `02_数学学习_ADC校准所需/08_Dither_为什么噪声有时有帮助.md`
- `03_MATLAB学习/07_读懂ADC资料中的MATLAB代码.md`

## Remaining Markdown Notes

High priority:

- `01_ADC学习_孙老师课件主线/08_ch8_Flash_ADC.md`
- `01_ADC学习_孙老师课件主线/09_ch9_Folding_Interpolating_ADC.md`
- `02_数学学习_ADC校准所需/09_复数_相位_拉普拉斯和系统观点.md`
- `03_MATLAB学习/01_MATLAB基本观念_脚本_命令窗口.md`
- `03_MATLAB学习/02_数组_矩阵_索引_冒号.md`
- `03_MATLAB学习/03_运算符_点运算_线性代数运算.md`
- `03_MATLAB学习/04_流程控制_函数_匿名函数.md`
- `03_MATLAB学习/05_数据结构_cell_struct_string.md`
- `03_MATLAB学习/06_绘图_文件读写_调试.md`

Lower priority or index/meta notes:

- Course index and README files.
- DAC, Flash, Folding/Interpolating, oversampling DAC, and other architecture
  notes that are less central to the immediate ADCToolbox calibration path.

## PDF And DOCX Gap

PDF and DOCX sources are imported but not yet systematically distilled. Highest
priority:

- `ADC测试分析与校准.pdf`
- `Data Conversion Handbook.pdf`
- `ADC关键metric及concept.docx`
- `ADC核心概念详细解析.pdf`
- `ADC工作物理系统结构.docx`
- `MATLAB.docx`

## Current Content Meaning

The raw Markdown layer now supports the core learning chain:

```text
sampling / comparator / CDAC / MDAC nonidealities
  -> bit or stage weight errors
  -> linear algebra and least squares
  -> rank, observability, dither, and conditioning
  -> FFT testing, noise metrics, FOM, and validation
  -> ADCToolbox source-code pages
```

## Next Distillation Pass

Recommended next pass:

1. Flash ADC and folding/interpolating ADC architecture notes.
2. Remaining MATLAB fundamentals notes.
3. Complex numbers, phase, Laplace, and systems viewpoint.
4. First PDF/DOCX distillation pass for `ADC测试分析与校准.pdf` and
   `Data Conversion Handbook.pdf`.
5. Example evidence notes from `wiki/workflows/example_ingest_map.md`.

## Verification

Automated lint should be run after each distillation pass:

```bash
python tools/lint_wiki.py
```
