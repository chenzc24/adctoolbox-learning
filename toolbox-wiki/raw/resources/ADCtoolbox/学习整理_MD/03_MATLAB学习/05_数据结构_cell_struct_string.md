# 数据结构：cell、struct、string

## 为什么不只用矩阵

矩阵适合存同类型、规则大小的数据。但实际代码中，参数、文件名、不同长度数组、配置项需要更灵活的数据结构。

## cell

cell 可以存不同类型和不同大小的数据。用花括号访问内容。

C{1} 表示第一个 cell 里的内容。

C(1) 表示第一个 cell 本身，仍是 cell。

这个区别是 MATLAB 初学者常见坑。

## struct

struct 用字段名组织数据：

cfg.fs = 1e6
cfg.N = 4096
cfg.window = 'hann'

读 ADC 代码时，struct 常用于保存配置、测试结果、指标集合。

## char 和 string

老 MATLAB 常用 char，例如 'abc'。新 MATLAB 支持 string，例如 "abc"。两者相似但不完全相同。

文件路径、图例、字段名经常涉及字符串。

## table

table 适合存带列名的数据。学习阶段不必深挖，但看到 table 要知道它像带标题的表格。

## 学习重点

如果变量代表数学向量或矩阵，用普通数组；如果变量代表一组配置或结果，用 struct；如果每个元素大小不同，用 cell。读代码时先判断数据结构，再判断操作含义。
