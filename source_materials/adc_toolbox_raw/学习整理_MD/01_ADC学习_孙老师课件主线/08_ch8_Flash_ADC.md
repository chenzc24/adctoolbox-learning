# ch8 Flash ADCs：全并行量化

## 学习目标

Flash ADC 是最直接的 ADC 架构：用 2^N - 1 个比较器同时比较输入和一组参考阈值，一拍得到结果。它速度极快，但硬件复杂度随位数指数增长。

## 基本结构

N 位 Flash ADC 需要 2^N 个量化区间，因此需要 2^N - 1 个 transition levels。通常用电阻串产生参考电压，再用一排比较器判断 Vin 大于哪些阈值。

比较器输出形成 thermometer code，例如低阈值比较器输出 1，高阈值比较器输出 0。随后编码器把 thermometer code 转成二进制码。

## 优点

- 延迟最低，适合极高速低分辨率应用。
- 没有逐次逼近或级间等待，一次并行完成量化。
- 结构概念清晰，是理解 threshold-based quantization 的最好例子。

## 缺点

比较器数量指数增长。8 位需要 255 个比较器，10 位需要 1023 个比较器。比较器本身还要匹配、低 offset、低噪声、高速，功耗和面积很快不可接受。

## Bubble Error

thermometer code 理想形式是连续的一串 1 后面接一串 0。如果某个比较器因为噪声或 offset 出错，可能出现 111011000 这类 bubble。需要 bubble correction，否则编码结果会跳变。

## DNL/INL 来源

Flash ADC 的 DNL/INL 主要来自参考电阻串误差和比较器 offset。若某些阈值间距过小或顺序错乱，就会产生 missing code 或非单调。

## 与校准的连接

Flash ADC 的阈值误差可以通过测量 transition levels 来校准。但比较器数量太多时，校准开销也大。Flash 的思想会出现在 Pipeline 的 sub-ADC 中：每一级用低位 Flash 做粗量化，再用 DAC 和余差放大修正。

## 学习重点

Flash ADC 不一定是你最终重点研究的架构，但它是理解“多阈值并行比较”和“复杂度爆炸”的基准。Pipeline、Folding、Interpolating 等架构很多都是在回答：如何避免 Flash 的指数复杂度？


## 自检问题

1. 本章最核心的物理问题是什么？
2. 哪些理想假设在真实 ADC 中最容易失效？
3. 这一章和采样、量化、噪声、校准四条线中的哪几条有关？

## 和后续学习的连接

读完本章后，不要求记住所有电路细节，但要能把“模拟量如何被采样、比较、编码”讲成自己的话。后面学习校准时，所有算法最终都要回到这些非理想来源：采样误差、增益误差、比较器误差、电容/电阻失配、时钟误差和数字拼接误差。

## 进一步展开：Flash ADC 的编码细节

Flash ADC 的比较器输出通常不是天然二进制，而是 thermometer code。理想情况下输入越大，越多低阈值比较器输出 1。编码器要把 thermometer code 转成 binary code，这一步可能需要 bubble correction 和 priority encoding。

Flash 的指数复杂度不仅是比较器数量，还包括参考电阻串负载、输入电容、时钟分布、编码器复杂度和功耗。位数每增加 1，比较器数大约翻倍，匹配要求还会提高。

Flash 仍然重要，因为它经常作为子模块出现。Pipeline 的 sub-ADC、Folding 的前端判决、高速辅助量化器都可能使用低位 Flash。因此理解 Flash 是理解复杂 ADC 的基础积木。