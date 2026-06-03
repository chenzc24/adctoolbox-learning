# Source Note: MATLAB Fundamentals Bridge

```yaml
stage_link:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/01_MATLAB基本观念_脚本_命令窗口.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/02_数组_矩阵_索引_冒号.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/03_运算符_点运算_线性代数运算.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/04_流程控制_函数_匿名函数.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/05_数据结构_cell_struct_string.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/06_绘图_文件读写_调试.md
source_links:
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/01_MATLAB基本观念_脚本_命令窗口.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/02_数组_矩阵_索引_冒号.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/03_运算符_点运算_线性代数运算.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/04_流程控制_函数_匿名函数.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/05_数据结构_cell_struct_string.md
  - ../../raw/resources/ADCtoolbox/学习整理_MD/03_MATLAB学习/06_绘图_文件读写_调试.md
rigor:
  - source-confirmed
  - engineering-heuristic
status: draft
last_updated: 2026-06-03
confidence: medium
```

## One-Sentence Takeaway

The MATLAB bridge teaches enough syntax and data-flow reading to understand ADC
reference code, then map it back to ADCToolbox Python concepts.

## Key Extracted Ideas

- MATLAB is matrix-first; always inspect `size`, `class`, and orientation.
- Scripts share workspace state, while functions have explicit inputs and
  outputs.
- Indexing starts at 1, and `:` selects ranges, rows, or columns.
- `*` is matrix multiplication; `.*` is elementwise multiplication.
- `^` is matrix power; `.^` is elementwise power.
- Backslash solves linear systems or least-squares problems and is preferred
  over explicit inverse for solving.
- `pinv`, `rank`, and `cond` are important clues in calibration code.
- `cell`, `struct`, `string`, and `table` usually represent configuration,
  mixed-size data, result bundles, or labels.
- Plots are diagnostic tools: waveform, spectrum, histogram, DNL/INL, and
  before/after calibration comparisons.
- Debugging should start with dimensions, NaN/Inf, index bounds, and whether a
  matrix operation was confused with an elementwise operation.

## Integration Into The Wiki

This source supports:

- [Reading ADC MATLAB code](matlab_code_reading_note.md)
- [Least-squares ADC calibration](../concepts/least_squares_adc_calibration.md)
- [FFT metrics](../concepts/fft_metrics.md)
- [Full calibration source](../source_code/calibrate_weight_sine_py.md)

## Rigor Notes

This page is a translation bridge, not an ADC theory source. It should help the
learner identify FFT, statistics, least-squares, loops, fitting, and plotting
patterns in MATLAB ADC material.

## Open Follow-Up

Add a MATLAB-to-Python comparison table if the learner begins translating
MATLAB snippets into ADCToolbox or NumPy code.
