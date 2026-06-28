# Stage 09：Subsample Debug Output（无滤波下采样调试口）

## 本阶段如何承接 Stage 08

Stage 08 讨论的是高速 ADC 内部的真实采样结构：

```text
多个子 ADC 交织 -> aggregate sample rate fs -> TI spur
```

Stage 09 讨论另一个工程问题：芯片内部 ADC 可以跑在 GS/s，但调试输出 pad、FPGA
采集口或低速监控链路常常不能把所有样本都送出来。常见做法不是做 DSP 意义上的
decimation filter，而是：

```text
每 N 个样本只送出 1 个，其他丢弃。
```

这叫 subsample-only debug output。它是一个 IO rate adapter，不是抗混叠下采样器。

所以本阶段只回答三个问题：

```text
丢样后频谱怎么看？
spur/谐波为什么会 alias？
如果前一级是 TI-ADC，N 应该怎么选？
```

## 本阶段目标

学完本阶段，你应该能解释：

- subsample-only 和带抗混叠滤波的 DSP downsample 有什么本质区别。
- 为什么 debug port 下采样会保留 spur 高度，但改变 spur 频率位置。
- alias 公式如何用于 fundamental、harmonic 和 TI spur。
- 为什么无滤波下采样后 NSD 会恶化 `10*log10(N)`。
- 为什么 TI-ADC 的 debug 下采样因子要和 interleave 通道数互质。
- 如何运行 `09_downsample/exp_d00_subsample_aliasing.py` 检查这些现象。

## 初学者先抓住的主线

先区分两个容易混淆的词：

```text
decimation:
  通常指 DSP 里的“先抗混叠滤波，再降低采样率”。

subsample-only debug output:
  只把原始 ADC 输出中每 N 个样本取 1 个送出来，不先滤波。
```

真正的 DSP decimation by `N` 通常是：

```text
low-pass / band-limit -> keep every N-th sample
```

也就是：

```text
x[n]
  -> anti-alias low-pass, cutoff <= fs_in/(2N)
  -> y[m] = filtered_x[m·N]
```

为什么要先低通？因为抽点后输出采样率变成：

```text
fs_out = fs_in / N
```

新的 Nyquist 频率也变成：

```text
fs_out / 2 = fs_in / (2N)
```

原来高于 `fs_out/2` 的频率，如果不先滤掉，就会折叠到新的 Nyquist 带内。
所以 DSP decimation 的目标是：

```text
保留目标低频带宽；
删除会 alias 的带外成分；
得到一个干净、低速、可继续处理的数字信号。
```

Stage 09 的 debug output 是：

```text
keep every N-th sample only
```

数学上就是：

```text
y[m] = x[m·N]
```

没有前面的低通滤波，所有频率成分都会按新的输出采样率 `fs_out = fs_in / N`
重新折叠到输出 Nyquist 带内。换句话说，在 debug 输出里：

```text
f, f ± fs_out, f ± 2fs_out, ...
```

这些频率会变成同一个离散时间频率。低速 debug 口看到的某个低频 spur，可能并不是
原始 ADC 真的在这个低频位置有 spur，而是高频 harmonic、TI spur 或其他带外 artifact
折叠下来的结果。

这不是 bug，而是 debug port 的目的不同：

```text
DSP decimation:
  想得到一个低带宽、已抗混叠的重建信号。

ADC monitor/debug output:
  想把 raw ADC 行为送出来离线看，包括 harmonic、spur、code histogram、TI channel pattern。
```

这两种链路的价值判断相反：

```text
DSP decimation:
  带外 spur 是污染源，应该在降采样前滤掉。

ADC debug output:
  带外 spur 可能正是证据，应该尽量保留下来让工程师离线分析。
```

如果你提前滤掉了带外 spur，就可能把最想调试的东西删掉。例如：

```text
CDAC mismatch 造成的 harmonic；
TI offset/gain/skew 造成的 fs/M 网格 spur；
reference settling 或 clock feedthrough 造成的高频 spur；
某些 code-dependent pattern；
通道轮转 pattern 或 code histogram 异常。
```

所以 Stage 09 的 debug 口不是为了生成“正确低带宽信号”，而是为了生成一个**低速但尽量
raw 的观察窗口**。它牺牲了频率位置的直读性，换来对原始 ADC 行为的保留。

使用这种 debug output 时，正确姿势是：

```text
1. 先记住原始采样率 fs_in 和抽点因子 N。
2. 计算 fs_out = fs_in / N。
3. 把 debug 频谱里的每个可疑 spur 按 fs_out 反折叠。
4. 再判断它可能来自 fundamental、harmonic、TI spur 还是其他 artifact。
```

如果你的目标真的是得到一个低带宽、已抗混叠的信号，那就不应该用 Stage 09 这种
subsample-only debug output，而应该进入真正的 DSP filtering / decimation 设计。

## 核心公式：alias 到输出 Nyquist

设输出采样率：

```text
fs_out = fs_in / N
```

任意真实频率 `f` 在 debug output 中会落到：

```text
f_alias = | ((f + fs_out/2) mod fs_out) - fs_out/2 |
```

这和 Stage 02 的 Nyquist folding 是同一件事，只是这里的采样率从 `fs_in`
变成了低速输出口的 `fs_out`。

举例：

```text
fs_in  = 1 GHz
N      = 3
fs_out = 333.33 MHz
Nyq    = 166.67 MHz
```

如果输入 fundamental 是 100 MHz：

```text
HD2 = 200 MHz -> alias 到 133.33 MHz
HD3 = 300 MHz -> alias 到 33.33 MHz
```

所以在低速口看到 33.33 MHz spur，不代表芯片内部真的有一个 33.33 MHz
模拟失真源；它可能是 300 MHz 的 HD3 折叠过来的。

## Spur 高度为什么基本守恒

无滤波 subsample 只是改变采样网格。对一个稳定的 coherent tone 来说：

```text
tone 的幅度不因为丢样而自动变小；
它只是换了一个离散时间频率。
```

所以在理想 coherent 设置下，输入频谱和输出频谱中同一个 spur 的 dBc 高度应接近一致。
官方 example 会打印输入/输出 SFDR 差值，目标是：

```text
|SFDR_in - SFDR_out| < 0.1 dB
```

这个检查很重要。它告诉你：

```text
debug port 没有“改善”spur；
它只是把 spur 搬到了另一个频率位置。
```

## NSD 为什么会恶化

总噪声功率没有因为简单丢样而神奇消失；但输出 Nyquist 带宽缩小成原来的 `1/N`。
如果同样的噪声功率挤进更窄的频带，单位 Hz 的噪声密度会上升：

```text
NSD_out ≈ NSD_in + 10*log10(N)
```

注意区分：

```text
SNR / SNDR:
  看带内总功率比，依赖你定义的带宽。

NSD:
  看每 Hz 噪声密度，输出采样率变小后很容易看起来变差。
```

所以 Stage 09 的重点不是“下采样提高 SNR”，而是“低速 debug 口如何解释频率轴和噪声密度”。

## Debug output 的意义：观测口，不是完整性能测量口

到这里你可能会有一个合理的质疑：

```text
频率位置会 alias；
多个 spur 可能叠到一起；
NSD 标尺也变了；
那这种 debug output 还有什么意义？
```

答案是：Stage 09 的 debug output 不应该被理解为一个低速精确频谱仪，也不应该替代
完整 ADC performance characterization。它更准确的定位是：

```text
observability port:
  在 IO / 测试链路受限时，提供一个低速但尽量 raw 的观察窗口。
```

它的意义不是“测得准”，而是“看得到”。

### 1. 完整码字不等于完整采样序列

ADC 最终当然要输出完整码字。但 debug subsampling 通常不是把一个 sample 的 bit
截掉，而是：

```text
每个送出来的 sample 仍然是完整码字；
但不是每个 sample 都送出来。
```

例如：

```text
原始高速码流:
  x[0], x[1], x[2], x[3], x[4], x[5], ...

N=4 debug output:
  x[3], x[7], x[11], x[15], ...
```

所以它保留了“每个被观察样本的幅度分辨率”，但牺牲了“完整时间序列”。

这两个概念要分开：

```text
完整码字:
  每个样本的电压 / code 信息完整。

完整采样序列:
  每个采样时刻都被保留下来，频率信息不因丢样而混叠。
```

Stage 09 的 debug output 通常保留前者，牺牲后者。

### 2. 为什么不直接输出全速 raw code

如果芯片和测试平台真的能持续输出全速、未处理、完整 raw code stream，那当然最好。
这时你应该优先抓全速 raw data，而不是依赖 subsample debug output。

但现实限制往往是数据率太高。比如：

```text
12-bit ADC, 1 GS/s:
  raw data rate = 12 Gb/s
```

如果还有多通道、framing、编码开销、JESD / FPGA / ATE 限制，成本会继续上升。
实际限制可能来自：

```text
pad / package IO 带宽不够；
FPGA / ATE capture 速率不够；
片上 debug bus 太窄；
高速持续输出功耗太大；
高速接口面积和验证成本太高；
片上 SRAM 只能短时间抓取，不能长时间 streaming。
```

所以 subsample debug output 的本质是：

```text
ADC 内部太快，外部观察太慢；
用时间完整性换 IO 可观测性。
```

### 3. 最终产品输出不一定是 raw ADC 输出

还有一个常见误区：最终产品输出能跑通，不代表你看到了 ADC core 的 raw 行为。
很多芯片最终输出前可能已经经过：

```text
digital calibration；
channel alignment；
decimation filter；
DDC；
averaging；
format packing；
error correction；
data compression；
JESD framing。
```

这些链路对系统功能验证很有用，但可能已经把 ADC core 的某些异常滤掉、平均掉、
校掉或重新编码。比如你想看：

```text
校准前的 TI spur；
某个子 ADC 是否异常；
raw code histogram；
reference settling artifact；
clock feedthrough；
内部 mux 后的数据。
```

最终输出链路未必保留这些信息。debug output 的价值就在于：它可以在最终 DSP 链路之前，
提供一个更靠近 ADC core 的低成本观察点。

### 4. 它适合看什么，不适合看什么

适合：

```text
有没有异常；
扫 trim / bias / supply / temperature 时异常是否变小；
某个 channel pattern 是否存在；
code histogram 是否卡死、缺码或周期性跳变；
校准前后某个 alias spur 是否随控制量变化；
长期监控趋势。
```

不适合单独用来判断：

```text
某个低频 debug spur 的唯一原始频率；
完整未混叠频谱；
collision 后单个 spur 的真实幅度；
最终 ADC 数据手册级性能。
```

所以正确用法是把 debug output 当成一组证据，而不是最终判决：

```text
固定 N、固定设置时看相对变化；
换 N、换 fin、扫参数来减少歧义；
结合设计先验解释候选来源；
必要时用片上 SRAM 或高带宽 capture 做确认。
```

一句话总结：

```text
Debug output 不是 performance characterization port；
它是 observability port。
```

## 和 TI-ADC 的连接：N 要和通道数互质

如果前一级是 M-way TI-ADC，原始样本通道序列是：

```text
ch0, ch1, ch2, ..., ch(M-1), ch0, ch1, ...
```

如果每 N 个样本取一个，取到的通道是：

```text
sample index: N-1, 2N-1, 3N-1, ...
channel:      (N-1) mod M, (2N-1) mod M, ...
```

如果 `gcd(N, M) != 1`，输出可能只访问部分通道。最坏情况：

```text
M = 4, N = 4
```

每次都取同一个通道，debug output 完全看不到 channel-to-channel mismatch。

所以经验规则是：

```text
gcd(N, M) = 1
```

常用选择：

```text
N = 31  适合很多 M，输出率低，覆盖通道均匀
N = 15  对 M = 2/4/8/16 互质
N = 7   对非 7 因子的 M 互质
```

避免在 binary-interleaved ADC 上用 `N = 2, 4, 8, 16` 这类因子。

## 本库对应代码

官方示例：

```text
python/src/adctoolbox/examples/09_downsample/README.md
python/src/adctoolbox/examples/09_downsample/exp_d00_subsample_aliasing.py
```

相关基础 API：

```python
from adctoolbox import analyze_spectrum, find_coherent_frequency
from adctoolbox.siggen import ADC_Signal_Generator
```

`exp_d00` 内部故意只实现一个很小的 helper：

```python
def subsample(signal, n):
    return signal[n - 1 :: n]
```

这和 RTL counter 常见行为一致：

```text
counter = 0, 1, ..., N-1
counter == N-1 时 capture
```

## 实验：3x subsample aliasing

运行：

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\09_downsample\exp_d00_subsample_aliasing.py
```

观察：

```text
四列输入频率：50 / 70 / 100 / 140 MHz
上排：1 GHz 输入采样率下的频谱
下排：N=3 debug output 后的频谱
红线：发生 alias 的 harmonic
绿线：未 alias 的 fundamental 或 harmonic
打印表：HD3 输入频率、HD3 输出 alias 频率、SFDR 差值
```

输出图：

```text
python/src/adctoolbox/examples/09_downsample/output/exp_d00_subsample_aliasing.png
```

读图时重点看两件事：

```text
1. frequency position 变化了；
2. spur height 基本没变。
```

## 和前后阶段的边界

| 阶段 | 负责的问题 | 不重复讲什么 |
|---|---|---|
| Stage 02 | FFT、window、alias 基础和动态指标 | 不讲 debug port 选 N |
| Stage 08 | TI 失配和校准 | 不讲低速输出口采样因子 |
| Stage 09 | 无滤波 subsample debug output | 不讲 NTF/抗混叠 decimation filter |
| Stage 10 | oversampling、noise shaping、NTF | 不讲 raw debug port alias 保真 |

这样分开后，看到“下采样”两个字先问：

```text
这是 DSP filtering/decimation，还是 chip debug port subsample？
```

这两个目的完全不同。

## 容易混淆的点

- subsample-only 不是抗混叠滤波器。它会保留并折叠带外 spur。
- 低速输出口看到的 spur 频率不一定是真实模拟频率，要按 `fs_out` 反折叠。
- spur dBc 高度基本守恒，不代表下采样改善了 ADC。
- NSD 变差不一定是设计坏了，可能只是带宽缩小后的每 Hz 噪声密度上升。
- TI-ADC debug 下采样时，N 和通道数 M 不互质会造成通道覆盖偏置。
- `09_downsample` 的例子和 Stage 10 的 oversampling/decimation 不是同一个问题。

## 阶段检查问题

1. subsample-only debug output 和 DSP decimation 的主要区别是什么？
2. `fs_in=1GHz, N=3, fin=100MHz` 时，HD2/HD3 在输出频谱落到哪里？
3. 为什么无滤波下采样后 spur 高度不会自动变小？
4. 为什么 NSD 会恶化约 `10*log10(N)`？
5. 如果一个 4-way TI-ADC 用 `N=4` 做 debug output，会发生什么问题？
6. 为什么 `N=31` 常被用作相对安全的 debug downsample ratio？
7. 在低速口看到 33 MHz spur，为什么不能直接说芯片内部有 33 MHz 失真源？
8. Stage 09 和 Stage 10 的“下采样/带宽变窄”有什么不同？

完成这些问题后，你就能把低速 debug output 里的频谱看成“折叠后的证据”，而不是把每个频点都误认为原始模拟频率。
