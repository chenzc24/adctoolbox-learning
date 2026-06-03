# 如何读懂 ADC 资料中的 MATLAB 代码

## 先找输入输出

读任何 ADC MATLAB 函数，第一步看函数头：输入参数是什么，输出结果是什么。输入可能是 raw code、采样率、输入频率、FFT 长度、OSR、窗口参数；输出可能是 SNR、SNDR、ENOB、DNL、INL、校准权重。

## 判断代码属于哪类数学

常见类型包括：

- FFT/频谱分析：出现 fft、abs、log10、bin、harmonic。
- 统计分析：出现 mean、std、var、histogram、rms。
- 线性方程求解：出现反斜杠、pinv、rank、A'*A。
- 搜索和拟合：出现 min、max、polyfit、优化循环。
- 数据整理：出现 reshape、sort、find、logical indexing。

## 不要逐行硬啃

先画出流程：

原始数据 -> 预处理 -> 变换 -> 提取指标 -> 输出/绘图

然后再把每一段对应到数学概念。

## 读 FFT 代码时看什么

- N_fft 是多少。
- 是否去掉 DC。
- 是否加窗。
- 频率 bin 如何定义。
- 基波和谐波如何定位。
- 噪声 bin 如何排除信号和谐波。
- dBFS 或 dBc 如何归一化。

## 读校准代码时看什么

- 未知量是什么：bit weight、stage weight、gain 还是 offset？
- 矩阵 A 怎么构造？
- 目标 y 是什么？
- 用 Ay、pinv 还是迭代？
- 是否加入 dither？
- 是否检查 rank 或条件数？

## 读函数名的线索

函数名常透露任务：

- FindBin：找频率 bin。
- FindFin：估计输入频率。
- INLsine：用正弦直方图估计 INL。
- overflowChk：检查余差是否越界。
- FGCalSine：可能是 foreground calibration with sine。
- NTF Analyzer：分析噪声传递函数。

## 学习重点

MATLAB 是表达数学流程的语言。你不必先成为 MATLAB 熟练工程师，也能通过“输入输出 + 数学类型 + 数据流”读懂大部分 ADC 学习代码。
