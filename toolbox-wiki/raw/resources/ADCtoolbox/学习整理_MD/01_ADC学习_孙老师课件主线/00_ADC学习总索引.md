# ADC 学习主线总索引

本目录以孙老师课件为主线整理。源文件全部保留在原目录，本目录只新增学习用 Markdown。目标不是复刻课件，而是把每一章扩展成更适合自学的笔记：概念先行，公式服务直觉，电路细节服务 ADC 和校准理解。

## 推荐顺序

1. ch2：先理解模拟世界、数字世界和数据转换器的高层图景。
2. ch3：建立性能指标语言，知道 Offset、Gain、DNL、INL、SNR、SNDR、ENOB 在说什么。
3. ch5、ch6、ch7：采样保持、开关电容、比较器，是理解真实 ADC 的物理基础。
4. ch8、ch9、ch10、ch11、ch12：学习 Nyquist ADC 架构，重点关注 Pipeline 和 SAR。
5. ch14：过采样和噪声整形，是 Sigma-Delta 的入口。
6. ch13、ch16、ch17：作为进阶补充，分别对应时间交织、FOM、测试。

## 文件对应关系

- ch1 -> 01_ch1_课程介绍与学习方法.md
- ch2 -> 02_ch2_数据转换器高层图景.md
- ch3 -> 03_ch3_ADC性能指标.md
- ch4 -> 04_ch4_Nyquist_DAC基础.md
- ch5 -> 05_ch5_采样电路.md
- ch6 -> 06_ch6_开关电容建立与噪声.md
- ch7 -> 07_ch7_电压比较器.md
- ch8 -> 08_ch8_Flash_ADC.md
- ch9 -> 09_ch9_Folding_Interpolating_ADC.md
- ch10 -> 10_ch10_Pipeline_ADC概念.md
- ch11 -> 11_ch11_Pipeline_ADC实现.md
- ch12 low power -> 12a_ch12_低功耗SAR_ADC.md
- ch12 high speed -> 12b_ch12_高速SAR_ADC.md
- ch13 -> 13_ch13_Time_Interleaving.md
- ch14 -> 14_ch14_过采样ADC.md
- ch15 -> 15_ch15_过采样DAC.md
- ch16 -> 16_ch16_ADC_FOM.md
- ch17 -> 17_ch17_数据转换器测试.md

## 关于备份文件

（备份）ch10.pdf 保留为源文件，不重复生成学习笔记；本目录用 ch10.pdf 生成 Pipeline ADC 概念章节。
