# Stage 11：遗留 example 与知识缺口补充

## 本阶段定位：不是新主题，是收尾

Stage 00–10 走完了主线：

```text
numerics -> ADC basics -> FFT metrics -> error analysis -> SAR model
        -> digital bits -> calibration -> validation -> TI-ADC
        -> subsample debug -> oversampling / noise shaping
```

学到这里，**知识主线已经完整**。本阶段不引入新主题，而是做两件事：

```text
1. 补 stage 00-10 没系统展开的诊断工具（polar / 相平面 / 谐波分解 / INL-DNL / 频谱平均）
2. 清点「已学知识、但对应 example 没跑」的遗留脚本，给清单不展开
```

### 为什么要这样组织

做过一次核查：ADCToolbox 共 62 个 runnable example，主线索引的 example 只跑了约 19 个。
看起来漏了一大半，但逐个核对背后的知识后发现——**绝大多数"没跑的 example"对应的
概念其实已经在某个 stage 教过了**。比如：

```text
FoM 公式 (Walden/Schreier)   -> stage_07 §3 已推
NSD <-> SNR 换算             -> stage_02 §8 已推
jitter / kT/C 物理极限 SNR   -> stage_01/02 已讲
静态非线性 k2/k3             -> stage_03 §2.1 已讲
aliasing / Nyquist           -> stage_02 §4.4 已讲
量化噪声 vs bit 数           -> stage_01 § 已推 (6.02N+1.76)
记忆效应                     -> stage_03 §3.1 已讲
降采样 / spur 守恒           -> stage_09 已讲（exp_d00）
```

所以"example 跑过率"和"知识覆盖率"是两回事。真正需要在 staged course 里补成学习
锚点的缺口集中在**频谱/误差的可视化、分解和静态指标工具**上：

```text
缺口 1 : polar 频谱（极坐标频谱）—— stage_03 讲了记忆效应，但没用 polar 可视化
缺口 2 : 相平面 / lag plot        —— 完全没讲
缺口 3 : 谐波分解                 —— stage_03 讲了 HD2/HD3 成因，但没讲怎么单独测
缺口 4 : INL/DNL from sine         —— guides 讲过，staged course 需要入口
缺口 5 : 多记录频谱平均            —— stage_02 讲单谱和 window，没讲跨记录平均
```

这些内容构不成独立大主题，不值得各建新 stage，集中在本阶段补。

## 本阶段目标

学完本阶段，你应该能解释：

- polar 频谱为什么能同时显示谐波的幅度和相位，笛卡尔频谱为什么不能。
- 相平面 / lag plot 怎么识别 sparkle code、磁滞、亚稳态。
- 谐波分解比纯 FFT 多给出什么（每个 HD 分量的独立幅度+相位）。
- INL/DNL 为什么是静态 transfer curve 指标，和动态 SNDR/SFDR 不等价。
- power averaging、coherent averaging、polar coherent averaging 各自保留/丢失什么信息。

补完这些点，学习主线就闭合了。剩下的 example 多数是已学知识的验证性脚本，按需跑即可。

---

## 缺口 1：polar 频谱（极坐标频谱）

### 这个工具解决什么问题

stage_02 和 stage_03 一直用**笛卡尔频谱**：横轴频率，纵轴幅度(dB)。它能告诉你
"在 H2、H3 频率上有多少能量"，但丢失了一个维度——**相位**。

笛卡尔频谱画的是 `|X(f)|`（幅度），phase 信息被丢掉了。但很多诊断场景里相位是关键：

```text
静态非线性产生的 HD2/HD3 有固定相位（它和输入同步）
记忆效应产生的失真相位会随输入散开（它依赖历史）
```

stage_03 讲记忆效应时，是用 ACF（自相关）的"小 lag 上 R[k] 非零"来识别的。
那是一个**间接**指标。polar 频谱是**直接**指标：把 HD2/HD3 的幅度和相位同时画出来。

### polar 频谱怎么画

`plot_spectrum_polar` 用的是**复数谱**（不只是幅度谱）：

```text
笛卡尔频谱 : 只画 |X(f)|，扔掉 angle(X(f))
polar 频谱 :
   径向（半径） = 谐波幅度 (dB)
   角度（方位） = 谐波相位
```

基波放在角度 0°，HD2、HD3 按它们的相位落在不同方位。于是：

```text
一个纯净的静态 HD3 -> 稳稳地落在某个固定角度（一个点）
有记忆效应的失真  -> 相位散开（不是一个点，是一团云）
```

这样"固定相位 vs 散开相位"的差别就肉眼可辨了——这是笛卡尔频谱做不到的。

### 实验 1：跑 exp_s11_polar_memory_effect

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s11_polar_memory_effect.py
```

这个实验对照两类失真：

```text
ROW 1 静态非线性：
  HD3=-66dBc, k3>0  -> SNDR=65.70 dB
  HD3=-66dBc, k3<0  -> SNDR=65.61 dB
  HD2+HD3           -> SNDR=65.50 dB

ROW 2 记忆效应（ME=0.02）：
  fin=40MHz  -> sndr=60.13, snr=72.61, thd=-72.47
  fin=80MHz  -> sndr=60.07, snr=72.64, thd=-72.30
  fin=160MHz -> sndr=59.99, snr=72.50, thd=-72.27
```

注意记忆效应那一行的 **SNDR(60) 远低于 SNR(72)**，差了 12 dB——说明有一大块能量
**不在随机噪声里，而在确定性失真里**，但 THD 又只有 -72 dB（谐波解释不了全部）。
这部分"既不是噪声也不是整数谐波"的能量，就是记忆效应的签名。

polar 图上：静态 HD3 是一个清晰的相位点；记忆效应是一片相位散开的云。两种失真
**SNDR 可能差不多，但 polar 图样完全不同**——这正是 polar 的诊断价值。

### 与 stage_03 的衔接

stage_03 §3.1 讲了"记忆效应是什么、为什么 PDF 看不见、ACF 怎么识别"。
本节补的是**第三种可视化手段**：polar 频谱直接看相位散开。三者互补：

```text
PDF     : 看误差分布形状（记忆效应看不出来）
ACF     : 看时间相关性（记忆效应在 lag=1 非零）
polar   : 看谐波相位散开（记忆效应是一团云，静态是点）
```

---

## 缺口 2：相平面 / lag plot

### 这个工具解决什么问题

相平面是另一种和频谱完全不同的视角：不看频域，看**时序结构**。
做法很简单——把信号和它延迟 k 个样本的版本画成散点：

```text
x 轴 : x[n]
y 轴 : x[n+k]
```

对一个纯正弦，这个散点是一个**椭圆环**（因为 x[n] 和 x[n+k] 是同频正弦，相差一个相位）。
环的形状由 k 决定。各种非理想性会在环上留下不同的"伤痕"，这就是诊断依据。

### auto-lag 怎么选 k

`analyze_phase_plane` 在 `lag='auto'` 时自动选 k，逻辑是（源码 line 43-84）：

```text
1. 去直流，FFT 找主频 -> 得到归一化频率 f_norm
2. 估计周期 = 1/f_norm
3. 搜索 k 使相位偏移 2π·f_norm·k 接近 90°（sin 接近 ±1）
4. 这样散点接近正圆，异常最显眼
```

为什么要 ~90°？因为 k 太小（接近 0°）散点退化成对角线，k 接近 180° 退化成反对角线，
都看不出异常。90°（1/4 周期）让环最"圆"，任何偏离环的点最容易被发现。

实验实测（exp_a41），15 种非理想性 auto-lag 都选了 k=2（因为这个实验的 fin 让
1/4 周期正好约等于 2 个样本）。

### 三类异常的图样

相平面专抓频谱看不出来的**时序异常**：

| 异常类型 | 相平面图样 | 频谱能不能看 |
|---|---|---|
| sparkle code | 散点里离群的点（红 × 标记） | 频谱看成一个噪声底，看不出来 |
| 磁滞 / settling | 环出现回环或 8 字形 | 频谱看成 HD，但看不出时序结构 |
| 亚稳态 | 阈值附近点聚集 | 频谱看成噪声 |

### outlier 检测为什么用 MAD 不用 std

源码 line 110-117 的细节值得注意：outlier 检测用 **MAD（中位数绝对偏差）**而不是 std：

```python
r_median = np.median(radius)
mad = np.median(np.abs(radius - r_median))
r_sigma_robust = mad * 1.4826
outlier_mask = np.abs(radius - r_median) > threshold * r_sigma_robust
```

因为 **std 会被 outlier 本身拉偏**——如果用 std，sparkle code 会把 std 撑大，
反而让自己"看起来没那么异常"。MAD 对 outlier 免疫，所以能稳定地把它们揪出来。
这是一个很实用的鲁棒统计技巧。

### 实验 2：跑 exp_a41 + exp_a42

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a41_analyze_phase_plane.py
uv run python src\adctoolbox\examples\04_debug_analog\exp_a42_analyze_error_phase_plane.py
```

**exp_a41**（15 种非理想的相平面）：实测结果很有说服力——

```text
14 种非理想性的 outlier 数都是 0
只有 Glitch 检出 199 个 outlier
```

也就是说相平面对 sparkle/glitch 类异常极其敏感（专抓时序离群），对连续失真
（HD、drift）反而不敏感（它们不产生离群点，只是让环变形）。

**exp_a42**（误差相平面，a42 的特殊价值）：它先 `fit_sine_4param` 去掉基波，
对**残差**做相平面。源码自己总结了：

```text
* HD2/HD3 cases show characteristic parabola/S-curve shapes even at -80/-70 dBc
* This method is 1000x more sensitive than regular phase planes for detecting harmonics
```

去基波后，-80 dBc 的 HD2（信号幅度的万分之一）在残差里变成了主要成分，
相平面能直接看到它的抛物线形状。**放大 1000 倍**就是从这里来的：
原本被基波淹没的微小 HD，去基波后凸显。

---

## 缺口 3：谐波分解（harmonic decomposition）

### 这个工具解决什么问题

stage_03 讲了 HD2/HD3 的成因（k2 → HD2，k3 → HD3），stage_02 的频谱能测出
HD2、HD3 各自的 dBc。但频谱给的是**功率**，丢掉了相位。

如果你想回答这些问题，频谱不够：

```text
这个 HD2 到底是偶次非线性还是别的？
HD2 和 HD3 的相对相位是什么？（决定它们在时域叠加后是相长还是相消）
能不能把 HD2 分量单独从波形里抽出来，看它单独长什么样？
```

谐波分解就是干这个的：用最小二乘把每个谐波分量**独立地**解出来，给出幅度**和**相位。

### 数学：最小二乘谐波分解

`decompose_harmonic_error` 的算法（源码 line 59-67）：

```text
1. fit_sine_4param 定基频 ω（和 stage_03 用的同一个拟合）
2. 构造谐波 basis：
     A = [1, cos(ωt), sin(ωt), cos(2ωt), sin(2ωt), ..., cos(nωt), sin(nωt)]
3. 最小二乘：W = (A^T A)^(-1) A^T · signal
4. 每个谐波 h 的幅度 = sqrt(W[cos_h]^2 + W[sin_h]^2)，相位 = atan2(...)
5. 相位都相对基波旋转（line 71）：
     phase_h_relative = phase_h - h * phase_fundamental
```

第 5 步"相对基波"是关键约定：这样不同测量的相位才有可比性。
（基波相位本身依赖时间零点，没意义；减掉 h 倍基波相位后，剩的是失真本身的特征相位。）

输出比频谱多两个维度：

```text
频谱   : 每个 HD 的功率（dBc）
分解   : 每个 HD 的幅度 + 相位 + 独立的时域波形（fundamental_signal / harmonic_signal / noise_residual）
```

特别地，`harmonic_signal` 是把基波去掉、只留所有谐波的波形——可以直接看"失真单独长什么样"。

### 实验 3：跑 exp_a11 + exp_a12

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a11_decompose_harmonics.py
uv run python src\adctoolbox\examples\04_debug_analog\exp_a12_decompose_harmonics_polar.py
```

- **exp_a11**：把信号分解成 fundamental / harmonics / residual 三层，逐层画时域波形。
  能直接看到 HD3 的三次曲线形状、residual 的噪声形状。
- **exp_a12**：把分解结果画成 polar（和缺口 1 联动），用 fs=800MHz / Fin=100MHz 的
  相干采样，把每个谐波的幅度+相位标在极坐标上。

（注：这两个 example 的 fit_sine_4param 在 max_iterations=1 下会有一个收敛警告，
属于 example 脚本的有意设置——它故意只迭代一次拿频率估计，后续靠 LMS 精修。
不影响分解结果。）

### 与 stage_03 的衔接

stage_03 回答了"HD2/HD3 从哪来（k2/k3 系数）"。
本节回答"怎么把 HD2/HD3 单独测出来（幅度+相位+独立波形）"。
两者是"成因 → 测量"的完整闭环。

---

## 衔接实验：exp_d15（未校准 mismatch spur）

stage_04 把 `exp_d15` 列为官方示例，但全程没跑过。它值得专门跑一次，因为它是
理解 stage_06 校准**为什么有效**的最佳前置实验：先看"不校准会差成什么样"。

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\05_debug_digital\exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
```

实测（unit cap mismatch sigma 扫 4 档）：

```text
sigma_Cu    SNDR_dB   ENOB    SFDR_dB   THD_dB
0%          98.10     16.00   122.66    -126.53
0.1%        97.88     15.97   116.63    -116.58
1%          91.71     14.94    98.16    -97.08
10%         78.18     12.69    86.10    -84.87
```

读这张表的方式：

```text
sigma=0%   : 理想 SAR，SNDR=98 dB（16 bit 满量程），SFDR 123 dB
sigma=1%   : 1% 电容失配，SNDR 掉到 91.7（掉 6 dB，相当于丢了 1 bit）
             SFDR 从 123 掉到 98（掉 25 dB！）—— 这就是 mismatch 的杀伤力
sigma=10%  : SNDR 78（接近 12.7 bit），SFDR 只剩 86
```

**SFDR 掉 25 dB**（sigma=1% 时）正是 stage_06 校准要修的东西。
回忆 stage_06 d16/d18 的结果：同样的 1% mismatch，校准后 SFDR 能回到 110+ dB。
d15 给出了"修之前"的基线，让 d16/d18 的"修之后"有对照。

这和 stage_07 §4 讲的"对比才能证明校准有效"是完全一致的逻辑——
**没有 uncalibrated 基线，就无法声称校准带来了改善**。

---

## 补充 4：INL/DNL from sine（静态线性指标）

### 为什么 INL/DNL 不能只放在“可选脚本”里

Stage 02 的 SNDR/SFDR/THD 是动态单音指标，回答的是：

```text
这个 ADC 对某个 sine 的频域表现如何？
```

INL/DNL 是静态 transfer curve 指标，回答的是：

```text
每个 code 的宽度是否正确？
累计转移曲线相对理想直线偏了多少？
```

两者相关但不等价。一个 ADC 可以有不错的 SNDR，但局部 code width 异常；也可以有可见
INL，但在某个输入频点和幅度下动态指标仍然可接受。因此看到 `analyze_inl_from_sine`
时，不要把它当成另一个频谱函数。

### sine histogram 的直觉

`analyze_inl_from_sine` 用的是 sine histogram 思路：

```text
1. 给 ADC 输入接近满幅的 sine。
2. 统计每个 output code 出现了多少次。
3. 理想 sine 的 PDF/CDF 是已知的，越靠近峰值停留时间越长。
4. 如果某个 code 出现次数比理论多，说明这个 code bin 更宽；反之更窄。
5. code width 偏差积分起来，就是 INL。
```

所以它依赖足够长的记录。样本太少时，histogram 抖动会直接变成 DNL/INL 噪声。

### 实验 4：跑 exp_a32

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\04_debug_analog\exp_a32_inl_from_sine_sweep_length.py
```

这个实验扫记录长度。读图时重点看：

```text
N 越小：DNL/INL 曲线越 noisy，局部 code width 判断不稳。
N 越大：曲线更平滑，更接近真实静态非线性。
```

和 Stage 07 的验证思想连接起来：

```text
INL/DNL 结果必须同时报告输入幅度、clip_percent、记录长度和 code 覆盖范围。
```

---

## 补充 5：多记录频谱平均与 polar coherent averaging

### power averaging 只让图更稳，不给 processing gain

Stage 02 已经讲了单条记录的 FFT、window、ENBW。多记录平均是另一个问题：

```text
power averaging:
  对 |FFT|^2 或功率谱平均
  丢掉相位
  noise floor 视觉上更平滑
  SNR 通常不按 10log10(Nrun) 提升
```

这适合做稳定的噪声底估计，但不能把多个记录当成一个相干积分器。

### coherent averaging 保留相位，能给 processing gain

```text
coherent averaging:
  先对齐相位，再平均 complex FFT
  随机噪声相互抵消
  相干的 fundamental / harmonic 被保留
  理想 processing gain 约为 10log10(Nrun)
```

代价是条件更苛刻：频率、采样、相位参考都要可对齐。真实测试里，如果触发相位漂移、
输入源相位不稳或记录不是同一个 coherent grid，coherent averaging 会失败。

### 实验 5：跑 exp_s07 + exp_s12

```powershell
cd E:\ADCToolbox\python
uv run python src\adctoolbox\examples\02_spectrum\exp_s07_spectrum_averaging.py
uv run python src\adctoolbox\examples\02_spectrum\exp_s12_polar_coherent_averaging.py
```

`exp_s07` 对比 power averaging 和 coherent averaging：

```text
power averaging:    噪声底更光滑，但 SNR 基本不变
coherent averaging: 相位对齐后，SNR 随 run 数显著提升
```

`exp_s12` 把这个思想放到 polar spectrum：

```text
coherent averaging 后，随机噪声被压低；
HD2/HD3 的相位关系仍然留在 polar 图上；
所以它同时服务于“看得更干净”和“保留相位诊断信息”。
```

这就是为什么 `exp_s12` 不该只留在 docs expected output 里：它补上了 Stage 11 的最后一块，
也把 Stage 02 的平均、Stage 03 的谐波、Stage 11 的 polar 视角连起来。

---

## 已学知识的遗留 example 清单

以下 example 对应的概念都已经在某个 stage 学过了，列在这里供你按需验证。
**不需要全跑**，每个板块跑一个代表就够。每个后面的括号标了"验证了 stage_X 的什么"。

### Conversions / 性能指标换算（07_conversions/）

```text
exp_c01_aliasing_nyquist_zones       (验证 stage_02 §4.4 aliasing / Nyquist)
exp_c02_unit_conversions             (验证 stage_01/02 的 dB/dBFS/LSB/NSD 单位)
exp_c03_calculate_fom                (验证 stage_07 §3 的 Walden/Schreier FOM)
exp_c04_amplitudes_to_snr            (验证 stage_02 的幅度↔SNR)
exp_c05_convert_nsd_snr              (验证 stage_02 §8 的 NSD↔SNR)
```

注：唯一的新东西是 c02 里的 **dBm**（绝对功率单位，相对 1mW），staged course 没专门讲。
如果你要读带 dBm 的 datasheet，看一眼 c02 的换算即可（dBm = dBFS + 满量程功率的 dBm 值）。

### 信号生成 sweep（03_generate_signals/）

```text
exp_g01_generate_signal_demo         (验证 stage_01 的量化 + 热噪声)
exp_g03_sweep_quant_bits             (验证 stage_01 的 6.02N+1.76)
exp_g05_sweep_static_nonlin          (验证 stage_03 §2.1 的 k2/k3 静态非线性)
exp_g06_sweep_dynamic_nonlin         (验证 stage_03 的动态非线性/settling)
exp_g07_sweep_interferences          (验证 stage_03 的 clipping/干扰)
```

这批是生成侧的 sweep，和 04_debug_analog 的 a 系列是同一批非理想性的不同视角。
stage_03 已经用 a 系列更完整地讲过了，这里可选。

### debug_analog 其余（04_debug_analog/）

```text
exp_a02_analyze_error_by_value       (验证 stage_03 的 error vs code)
exp_a03_analyze_error_by_phase       (验证 stage_03 的 error vs phase)
exp_a04_jitter_calculation           (验证 stage_02 §4 的 jitter 极限 SNR)
exp_a22_analyze_error_spectrum       (验证 stage_03 的误差频谱)
exp_a24_analyze_error_envelope_spectrum  (验证 stage_03 的误差包络谱)
exp_a25_spectra                      (验证 stage_03 的 15 种非理想频谱对照)
exp_a31_fit_static_nonlin            (验证 stage_03 的静态非线性拟合)
exp_a32_inl_from_sine_sweep_length   (补充 4 已讲，静态 INL/DNL 与记录长度)
```

### spectrum 方法论变体（02_spectrum/）

```text
exp_s02_analyze_spectrum_interactive (交互式频谱，画图方式变体)
exp_s03_analyze_spectrum_savefig      (存图方式变体)
exp_s05_annotating_spur              (spur 标注方式变体)
exp_s06_sweeping_fft_and_osr         (FFT 长度/OSR sweep，验证 stage_02 §8)
exp_s07_spectrum_averaging           (补充 5 已讲，power vs coherent averaging)
exp_s10_cartesian_and_polar_plot     (笛卡尔 vs polar，和本阶段缺口 1 联动)
exp_s12_polar_coherent_averaging     (补充 5 已讲，polar + coherent averaging)
```

### toolsets dashboard（06_use_toolsets/）

```text
exp_t01_aout_dashboard_single        (单文件 aout dashboard)
exp_t02_aout_dashboard_batch         (批量 aout dashboard)
exp_t03_dout_dashboard_single        (单文件 dout dashboard)
exp_t04_dout_dashboard_batch         (批量 dout dashboard)
```

whole_workflow_demo（stage_01/05/06/07 都跑过）已经展示了 dashboard 的效果。
这 4 个是它的分文件化/批量化版本，工程上用于批量出图，不是新知识。

### 其他

```text
exp_b01_environment_check            (安装自检，装好就过)
exp_b02_coherent_vs_non_coherent     (验证 stage_02 §4 的相干采样概念)
exp_d03_redundancy_comparison        (验证 stage_06 d17 的冗余 vs 二进制，d17 更完整)
exp_s09_sar_fft_length_near_nyquist  (SAR 频谱在 Nyquist 附近，小众)
```

注：**降采样 / spur 守恒**（exp_d00）已由 **stage_09_downsample_debug** 完整覆盖，
本阶段不再重复，如需回顾看那一篇。

---

## 阶段检查问题

1. polar 频谱的径向和角度分别代表谐波的什么？为什么笛卡尔频谱看不到记忆效应？
2. 相平面的 auto-lag 为什么选 ~90° 相移的 k？k=0 或 k=半周期会怎样？
3. 相平面的 outlier 检测为什么用 MAD 而不是 std？
4. exp_a42（误差相平面）为什么比 exp_a41 灵敏 1000 倍？它多做了一步什么？
5. 谐波分解比纯 FFT 频谱多给出什么？为什么相位要"相对基波"旋转？
6. exp_d15 的 sigma=1% 那行，SFDR 从 123 掉到 98，这 25 dB 是什么造成的？stage_06 怎么修它？
7. INL/DNL 和 SNDR/SFDR 分别在回答什么问题？为什么不能互相替代？
8. power averaging、coherent averaging、polar coherent averaging 分别保留和丢失什么？

---

## 收尾：全课程 example 覆盖率

补完本阶段后，主要遗留诊断工具都已进入 staged course。stage_11 共纳入这些之前没
系统学习的 example：

```text
a11, a12: 谐波分解
a32:      INL/DNL from sine
a41, a42: 相平面 / error phase-plane
s07, s12: 多记录频谱平均 / polar coherent averaging
s11:      polar memory effect
d15:      未校准 mismatch spur 基线
```

全课程 example 状态：

```text
stage 00-08 主线已跑 : 约 19 个
stage 09 (downsample) : exp_d00
stage 10 (oversampling) : 3 个相关 example
stage 11 (本阶段新补)  : 9 个相关 example
已学知识遗留           : 约 25 个 (可选验证，清单见上)
```

至此，**学习主线闭合**。剩余的约 25 个 example 大多是"已学概念的可选验证脚本"，
跑与不跑不影响主线完整性，按需选用。

最后保留两个明确边界，避免把学习库说过头：

```text
1. TI-ADC bandwidth mismatch / multi-tone swept diagnosis 尚未系统覆盖。
   当前 Stage 08 聚焦 offset/gain/skew。
2. Stage 10 是 OSR/NTF/noise shaping 的行为级学习入口，
   不是完整 Sigma-Delta loop 稳定性设计教程。
```

整个 staged course 的主线到这里完整闭合：

```text
ADC 是什么 -> 怎么测它 -> 怎么建它的模型 -> 怎么校准它 -> 怎么验证校准
          -> 多通道(TI)怎么处理 -> 调试口/过采样进阶 -> 可视化与诊断工具箱补全
```
