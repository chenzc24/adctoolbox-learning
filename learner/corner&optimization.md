# Corner & Optimization Notes

这个文件记录 ADCToolbox 学习过程中发现的 corner cases、边界条件、文档修正点和后续优化方向。

维护规则：

- 每一条必须标明日期、代码位置、问题陈述、原理推导。
- 只有维护者明确提出“加入/记录到本文件”时，Agent 才能新增条目。
- Agent 可以建议新增条目，但不能自行把普通讨论自动写入本文件。
- 条目应保留问题出现的上下文，避免改写成脱离代码的泛泛结论。
- 如果后续代码或文档已经修正，应在原条目下追加“处理状态”，不要删除历史记录。

## 2026-06-22: `fit_sine_4param` 的正交性条件和 residual 解释边界

### 代码位置

- `python/src/adctoolbox/fundamentals/fit_sine_4param.py`
  - `fit_sine_4param(...)`
  - `_fit_core(...)`
  - `design_matrix = [cos_vec, sin_vec, ones]`
  - `residuals = y - fitted_sig`
- `python/src/adctoolbox/aout/rearrange_error_by_phase.py`
  - 内部调用 `fit_sine_4param(...)`
  - `error = signal - fitted_signal`
- `python/src/adctoolbox/aout/rearrange_error_by_value.py`
  - 内部调用 `fit_sine_4param(...)`
  - `error = signal - fitted_signal`
- `learning/adctoolbox-learning/staged_course/stage_03_error_analysis/stage_03_error_analysis.md`
  - Stage 03 关于 sine fitting、residual、by value/by phase 的解释需要同步这个边界。
- `learning/adctoolbox-learning/learner/notes.md`
  - 短笔记中关于 fit 盲点、by value/by phase 的说法需要保持准确。

### 问题陈述

`fit_sine_4param` 的目的不是保留 ADC 的全部非理想信息，而是从 measured signal 中估计一个 best-fit single-tone reference：

```text
y_fit[n] = A*cos(omega*n) + B*sin(omega*n) + C
residual[n] = y[n] - y_fit[n]
```

因此 residual 的准确解释应为：

```text
residual = measured signal 中 best-fit single-tone 解释不了的部分
```

不能简单写成：

```text
residual = ADC 的全部非理想
```

原因是：任何与 `cos(omega*n)`、`sin(omega*n)`、`DC` 以及频率迭代导数方向不正交的误差，都会被 fit 部分吸收到 `A/B/C/frequency` 中。被吸收的部分不会完整出现在 residual、error PDF、error ACF、error spectrum 中。

特别需要修正的表达：

```text
by_value / by_phase 不依赖 fit，专门看 AM/PM 失真
```

当前代码并不支持这个说法。`analyze_error_by_value` 和 `analyze_error_by_phase` 都会先调用 `fit_sine_4param`，再对 `signal - fitted_signal` 做 value/phase 条件化分析。更准确的说法是：

```text
by_value / by_phase 是 residual 的条件化重排和建模。
它们能揭示 residual 中随 value/phase 变化的结构，
但不能恢复已经被 fundamental projection 吸收的同频或近同频误差。
```

### 原理推导

频率固定时，fit 的线性模型为：

```text
y = X*beta + e
X = [cos(omega*n), sin(omega*n), 1]
beta = [A, B, C]^T
```

最小二乘解满足 normal equation：

```text
X^T X beta = X^T y
```

如果真实信号为：

```text
y = X*beta_true + h + noise
```

则：

```text
X^T y = X^T X beta_true + X^T h + X^T noise
```

当 `h` 是 coherent harmonic，例如 HD2/HD3，并且与 fundamental basis 正交：

```text
X^T h = 0
```

那么 harmonic 不改变 `beta`，会完整留在 residual 中。这是 coherent sine fitting 能干净去掉 fundamental、保留 harmonic/noise 的数学基础。

反过来，如果某个误差项 `u` 与 fundamental basis 不正交：

```text
X^T u != 0
```

它就会改变 `beta`，被 fit 部分吸收。典型情况：

```text
1. AM / amplitude drift:
   y[n] = A*sin(omega*n) * [1 + m*cos(omega_m*n)]
        = A*sin(omega*n)
        + A*m/2 * sin((omega + omega_m)n)
        + A*m/2 * sin((omega - omega_m)n)

   sidebands 靠近 fundamental 时，有限 N 下与 fundamental basis 弱不正交，
   fit amplitude 可能偏高或偏低，residual 会低估 envelope 相关信息。

2. PM / timing-like modulation:
   小相位扰动会产生接近 slope sensitivity 的误差项。
   与 fundamental 相关的分量可能进入 fitted phase/frequency。

3. frequency estimate 未收敛:
   fitted frequency 与 true frequency 不一致时，
   residual 会留下准 fundamental 结构，在 error spectrum 的 fundamental 附近形成假尖峰。

4. 与 fundamental 同频的 gain/phase/DC 分量:
   按定义会被解释为主信号参数，而不是 residual error。
```

### 当前判断

- `fit_sine_4param` 的功能和目的没有错；它本来就是 best-fit single-tone estimator。
- 需要修正的是 Stage 03 和 notes 对 residual 的解释边界。
- `residual` 应被描述为 `unexplained error after best-fit sine`，而不是 `all ADC non-idealities`。
- `by_value / by_phase` 当前实现仍依赖 fit residual；文档应避免暗示它们能完全绕开 fit 盲点。

### 后续优化方向

- 在 Stage 03 增加 “fit 的正交性条件和盲点” 小节。
- 在 notes 中保留紧凑版逻辑链。
- 如果后续需要真正分析被 fit 吸收的 AM/PM/drift，可考虑增加 raw-signal demodulation、cycle-by-cycle amplitude/phase tracking，或明确区分：

```text
fit-residual diagnostics
raw-signal modulation diagnostics
```

### 处理状态

- 2026-06-22：已记录 corner。尚未修改 Stage 03 正文和 learner notes。

## 2026-06-22: auto frequency initialization 的收敛边界和选错峰风险

### 代码位置

- `python/src/adctoolbox/fundamentals/fit_sine_4param.py`
  - `_estimate_frequency_fft(y)`
  - `_fit_core(y, freq_init, max_iter, tol, verbose=0)`
  - `freq = freq_init if freq_init is not None else _estimate_frequency_fft(y)`
  - `freq_corr = t * (-a * sin_vec + b * cos_vec)`
  - `delta_freq = coeffs[3] / (2 * np.pi)`
- 下游自动 fit 调用路径：
  - `python/src/adctoolbox/aout/analyze_error_pdf.py`
  - `python/src/adctoolbox/aout/analyze_error_spectrum.py`
  - `python/src/adctoolbox/aout/analyze_error_autocorr.py`
  - `python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py`
  - `python/src/adctoolbox/aout/rearrange_error_by_phase.py`
  - `python/src/adctoolbox/aout/rearrange_error_by_value.py`
- 相关建模来源：
  - `python/src/adctoolbox/siggen/nonidealities.py`
  - `apply_am_tone`
  - `apply_drift`
  - `apply_clipping`
  - `apply_reference_error`
  - `apply_memory_effect`
  - `apply_ra_gain_error_dynamic`
  - `apply_glitch`

### 问题陈述

`fit_sine_4param(data)` 在没有传入 `frequency_estimate` 时，会先用 FFT 幅度最大峰估计初始频率：

```text
spec = abs(fft(y))
spec[0] = 0
k = argmax(spec[:N/2])
```

然后用简化的两点幅度比估计 sub-bin offset：

```text
r = +1 or -1, depending on which neighbor is larger
delta = r * spec[k+r] / (spec[k] + spec[k+r])
freq_init = (k + delta) / N
```

这个初始频率随后进入一阶 Taylor / least-squares 频率修正。关键边界是：

```text
Taylor/Gauss-Newton frequency refinement 是局部迭代。
它需要初始频率已经落在真实 fundamental 附近的收敛盆内。
如果 FFT 初值选到了错误峰，后续迭代通常不会全局跳回真实 fundamental。
```

因此，auto fit 在以下场景可能失效或产生 misleading residual：

```text
1. fundamental 不是 FFT 最大峰
   例如强 harmonic、强独立 spur、严重 clipping、低频 drift/interference。

2. 初始频率离真实频率太远
   例如手动传错 frequency_estimate，或者 near DC / near Nyquist 条件下 FFT 初值偏差较大。

3. 默认 max_iterations=1 不足以达到 tolerance
   结果可能已经足够准确，但仍触发 did-not-converge warning；
   或者 residual 中保留准 fundamental 假结构。
```

这不是 sine fitting 的原理错误，而是自动初始频率估计和局部迭代方法的工程边界。

### 原理推导

`fit_sine_4param` 要最小化：

```text
min_{a,b,c,f} sum_n [y[n] - a*cos(2*pi*f*n) - b*sin(2*pi*f*n) - c]^2
```

当频率 `f` 固定时，`a,b,c` 是线性最小二乘问题。但 `f` 在 `cos/sin` 内部，因此对 `f` 是非线性的。

代码的做法是在当前频率 `f0` 附近做一阶 Taylor 展开。设：

```text
omega = 2*pi*f0
y_fit[n] = a*cos(omega*n) + b*sin(omega*n) + c
```

频率移动 `delta_f`，即 `delta_omega = 2*pi*delta_f`：

```text
cos((omega + delta_omega)n)
    ~= cos(omega*n) - delta_omega*n*sin(omega*n)

sin((omega + delta_omega)n)
    ~= sin(omega*n) + delta_omega*n*cos(omega*n)
```

代回模型：

```text
y_fit_new[n]
    ~= a*cos(omega*n) + b*sin(omega*n) + c
     + delta_omega * n * [-a*sin(omega*n) + b*cos(omega*n)]
```

因此代码添加一列 frequency correction basis：

```text
freq_corr[n] = n * [-a*sin(omega*n) + b*cos(omega*n)]
```

再解线性最小二乘：

```text
[cos, sin, 1, freq_corr] * [a, b, c, delta_omega] ~= y
```

解出的第 4 个系数换算为：

```text
delta_freq = delta_omega / (2*pi)
freq <- freq + delta_freq
```

这个推导说明：

```text
delta_freq 只是在当前 f0 附近的一阶局部修正。
如果 f0 靠近真实 fundamental，迭代会快速收敛。
如果 f0 靠近错误 spur/harmonic，迭代会优化错误局部解。
```

### 工程环境中是否会出现

在标准 ADC 单音测试中，这些 corner 通常被流程刻意避开：

```text
coherent frequency
known Fin/Fs
fundamental 明显最大
record length 足够
输入源干净
```

但在 debug、bring-up、故障数据、复杂行为建模中会真实出现：

```text
clipping / saturation
    -> harmonic 暴涨，可能干扰最大峰选择

reference droop / supply spur / digital coupling
    -> 固定 spur 或低频调制进入输出

drift / baseline wander
    -> 长记录中低频成分可能很大

AM / PM / jitter-like modulation
    -> fundamental 两侧 sideband 或裙边

near DC / near Nyquist / undersampling
    -> FFT 初值和 Taylor 迭代都更敏感

仿真参数过猛或故障芯片
    -> spur/harmonic 可能接近甚至超过 fundamental
```

本库的建模环境主动支持这些非理想，因此这不是纯理论 corner。

### 当前判断

- 对干净单音、主频峰明显、已知 `Fin/Fs` 的标准测试，当前实现通常足够。
- 对自动 fit 路径，`_estimate_frequency_fft` 默认选择最大峰；如果最大峰不是 fundamental，就可能选错初值。
- `max_iterations=1` 在很多普通 non-coherent 单音下已经能给出很准结果，但未必满足 `tolerance=1e-9`，可能产生 warning。
- 当 residual 中出现 fundamental 附近假尖峰，或 fit frequency 明显偏离预期 bin，应优先怀疑 fit 初值/收敛质量。

### 后续优化方向

文档建议：

```text
1. 已知频率时，优先传入 frequency_estimate / frequency。
2. 复杂信号先看 raw spectrum，确认最大峰是否为真实 fundamental。
3. 做严肃 residual 诊断时，建议 max_iterations=3-5。
4. 对 near DC / near Nyquist / short record，增加 N 或避开边界频率。
```

代码优化候选：

```text
1. 将默认 max_iterations 从 1 调整为 3-5，或在高级分析函数中显式设置。
2. 提供可选的 expected frequency / search band，避免强 spur 抢占最大峰。
3. 将 `_estimate_frequency_fft` 改为三点 parabolic/log-parabolic 初值估计。
4. 对自动 fit 返回 diagnostic 字段，例如 init_frequency、delta_freq、converged、n_iterations。
5. 对明显异常的 `rmse` 或 `fit_freq` 偏离预期 bin 给出更具体 warning。
```

### 处理状态

- 2026-06-22：已记录 corner。尚未修改代码或 Stage 03 正文。

## 2026-06-23: ACF estimator 的大 lag 方差和 `max_lag` 非自适应边界

### 代码位置

- `python/src/adctoolbox/aout/analyze_error_autocorr.py`
  - `analyze_error_autocorr(..., max_lag=50, normalize=True, ...)`
  - `lags = np.arange(-max_lag, max_lag + 1)`
  - `acf[k] = np.mean(x1 * x2)`
  - `acf = acf / acf[lags == 0]`
- `matlab/src/dumped/errac.m`
  - `addParameter(p, "MaxLag", 100)`
  - `lags = -maxLag:maxLag`
  - `acf(k) = mean(x1 .* x2)`
  - `acf = acf / acf(lags==0)`
- Typical callers:
  - `python/src/adctoolbox/toolset/generate_aout_dashboard.py`
  - `python/src/adctoolbox/toolset/generate_aout_dashboard_3x4.py`
  - `python/src/adctoolbox/examples/04_debug_analog/exp_a23_analyze_error_autocorrelation.py`
  - `learning/adctoolbox-learning/demos/whole_workflow_demo.py`

### 问题陈述

当前 ACF 实现对 lag `k` 使用重叠样本的平均值：

```text
R_hat[k] = mean(e[n] * e[n+k])
```

由于 lag `k` 时可用的重叠样本数是 `N - |k|`，因此代码等价于：

```text
R_hat[k] = (1 / (N - |k|)) * sum_overlap e[n] * e[n+k]
```

这是 adjusted / unbiased-style sample ACF。它是合法 estimator，不是数学错误。

但代码默认 `normalize=True`，会用 lag 0 归一化：

```text
rho_hat[k] = R_hat[k] / R_hat[0]
```

归一化后，相比 biased 形式 `/N`，非零 lag 会多出一个尺度因子：

```text
rho_unbiased[k]
    = (N / (N - |k|)) * (sum_overlap / sum_all_energy)
```

因此当 `|k|` 接近 `N` 时，白噪声的 ACF 估计方差会被人为放大。初学者可能把大 lag 上的非零 ACF 误判为 long-range memory。

当前 `max_lag` 选择不是自适应的：

```text
Python default: max_lag = 50
MATLAB default: MaxLag = 100
Python example: max_lag = 100
MATLAB toolset: MaxLag = 200
```

这些默认值对本库常见的 `N=8192` 或 `N=16384` 是合理的，因为 `max_lag << N`。但如果用户传入较大的 `max_lag`，例如 `N/2` 或更大，代码没有 warning 或 guard。

### 原理推导

理论 ACF 定义：

```text
R[k] = E[e[n] * e[n+k]]
```

有限长度估计常见两种：

```text
adjusted / unbiased-style:
    R_hat_u[k] = (1 / (N - |k|)) * sum_overlap e[n] * e[n+k]

biased:
    R_hat_b[k] = (1 / N) * sum_overlap e[n] * e[n+k]
```

代码使用的是 `mean(x1 * x2)`，所以是 adjusted / unbiased-style。

归一化时：

```text
R_hat_u[0] = (1 / N) * sum_all e[n]^2

rho_hat_u[k] = R_hat_u[k] / R_hat_u[0]
             = [sum_overlap / (N - |k|)] / [sum_all / N]
             = N / (N - |k|) * sum_overlap / sum_all
```

当 `|k|` 很小：

```text
N / (N - |k|) ~= 1
```

影响可以忽略。

当 `|k| = N/2`：

```text
N / (N - |k|) = 2
```

大 lag 的随机抖动明显增大。对白噪声，理论 `R[k != 0] = 0`，但有限样本估计仍有随机波动；adjusted estimator 在大 lag 处的方差更高。

### 工程影响

默认设置下影响通常很小：

```text
N = 8192, max_lag = 50  -> max_lag/N ~= 0.006
N = 8192, max_lag = 100 -> max_lag/N ~= 0.012
N = 8192, max_lag = 200 -> max_lag/N ~= 0.024
```

这些范围主要用于观察局部 memory：

```text
settling memory
reference droop 的短期相关
pipeline/SAR 相邻样本相关
clock/feedthrough 的短周期结构
```

风险主要出现在：

```text
1. 用户手动设置 max_lag 接近 N/2 或更大。
2. 数据记录很短，而 max_lag 没有随 N 缩小。
3. 初学者把大 lag 处的非零 ACF 直接解释为真实 long-range correlation。
```

### 当前判断

- 这不是原理性问题。`/(N-|k|)` 是合法 ACF estimator。
- 当前默认 `max_lag=50` 对常见 ADCToolbox 示例数据是合理的。
- 代码没有根据 `N` 自动限制 `max_lag`，也没有提示大 lag 方差问题。
- Stage 03 中 “白噪声 lag=0 以外接近 0” 的表述应加上 “小 lag / max_lag << N” 的条件。

### 后续优化方向

文档建议：

```text
1. 说明当前代码使用 adjusted/unbiased-style ACF，分母是 N-|lag|。
2. 说明归一化后大 lag 方差会增加。
3. 看图时优先关注小 lag，建议 max_lag << N，经验上 max_lag < N/10。
4. 如果要看长周期结构，更适合结合 error spectrum，而不是单靠大 lag ACF。
```

代码优化候选：

```text
1. 对 max_lag >= N 抛出 ValueError，避免空 overlap。
2. 对 max_lag > N/10 给出 warning，提示 large-lag ACF variance。
3. 增加 estimator 参数：
   estimator="adjusted"  -> current mean over overlap, / (N-|lag|)
   estimator="biased"    -> sum over overlap / N
4. 在返回结果中加入 metadata：
   estimator, effective_counts_per_lag, normalized
```

### 处理状态

- 2026-06-23：已记录 corner/optimization。尚未修改代码或 Stage 03 正文。

## 2026-06-23: `fit_sine_4param` 默认 `max_iterations=1` 的 warning 语义和优化边界

### 代码位置

- `python/src/adctoolbox/fundamentals/fit_sine_4param.py`
  - `def fit_sine_4param(..., max_iterations=1, tolerance=1e-9, ...)`
  - `for i in range(max_iter + 1)`
  - `if i == 0: design_matrix = [cos, sin, ones]`
  - `else: design_matrix = [cos, sin, ones, freq_corr]`
  - `if abs(delta_freq) < tol: converged = True`
  - `if max_iter > 0 and not converged: RuntimeWarning`
- Downstream callers mostly use defaults:
  - `python/src/adctoolbox/aout/analyze_error_spectrum.py`
  - `python/src/adctoolbox/aout/analyze_error_pdf.py`
  - `python/src/adctoolbox/aout/analyze_error_autocorr.py`
  - `python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py`
  - `python/src/adctoolbox/aout/rearrange_error_by_value.py`
  - `python/src/adctoolbox/fundamentals/frequency.py`

### 问题陈述

当前默认参数为：

```text
max_iterations = 1
tolerance = 1e-9
```

这意味着默认流程不是“持续迭代直到满足 tolerance”，而是：

```text
i=0: 只做 3-parameter fit，求 A/B/C
i=1: 做一次 4-parameter Taylor frequency correction，求 delta_freq
```

如果这一唯一一次 `delta_freq` 小于 `tolerance`，就认为收敛；否则触发：

```text
RuntimeWarning: fit_sine_4param did not converge in 1 iterations.
```

因此，`tolerance` 在默认配置下主要是 warning 判据，而不是充分的“自动迭代到收敛”机制。

实验观察显示：

```text
普通 non-coherent / noisy single-tone:
    max_iterations=1 经常 warning
    但频率误差已经很小
    max_iterations=5 可以消除 warning
    但频率误差几乎不再改善，因为已经受噪声极限限制

near DC / near Nyquist / clean high-precision residual:
    max_iterations=1 可能留下明显假 residual
    max_iterations=5 显著改善
```

所以当前 warning 语义容易让用户误解：

```text
did not converge
```

看起来像“fit 失败”，但在普通噪声场景下更准确的含义是：

```text
没有在 1 次频率修正内达到非常严格的 tolerance；
结果可能仍然足够好。
```

### 原理推导

`fit_sine_4param` 的频率迭代是局部一阶 Taylor / Gauss-Newton correction。

固定当前频率 `f` 后，先解：

```text
y[n] ~= a*cos(2*pi*f*n) + b*sin(2*pi*f*n) + c
```

下一轮在当前 `f` 附近增加 frequency correction basis：

```text
freq_corr[n] = n * [-a*sin(2*pi*f*n) + b*cos(2*pi*f*n)]
```

然后解：

```text
y[n] ~= a*cos(...) + b*sin(...) + c + delta_omega * freq_corr[n]
```

并更新：

```text
delta_freq = delta_omega / (2*pi)
f <- f + delta_freq
```

`tolerance` 判断的是最后一次频率修正量：

```text
abs(delta_freq) < tolerance
```

在有噪声时，`delta_freq` 不可能无限接近 0；它会受到噪声、记录长度、SNR 和模型误差限制。因此，用极严的 `tolerance=1e-9` 搭配 `max_iterations=1`，会造成 warning 过敏。

### 实验结果摘要

Monte Carlo 条件：

```text
N = 8192
true bin = 82.33
single-tone + white noise
compare max_iterations=1 vs 5
```

结果：

```text
SNR=60 dB:
  iter=1: warn 99.4%, median |freq error| ~= 4.107e-6 bin
  iter=5: warn 0.0%,  median |freq error| ~= 4.102e-6 bin

SNR=40 dB:
  iter=1: warn 99.4%, median |freq error| ~= 4.273e-5 bin
  iter=5: warn 0.0%,  median |freq error| ~= 4.277e-5 bin

SNR=20 dB:
  iter=1: warn 99.6%, median |freq error| ~= 3.968e-4 bin
  iter=5: warn 0.0%,  median |freq error| ~= 3.972e-4 bin

SNR=10 dB:
  iter=1: warn 99.4%, median |freq error| ~= 1.299e-3 bin
  iter=5: warn 0.0%,  median |freq error| ~= 1.296e-3 bin
```

Clean random bin sweep:

```text
normal frequency region:
  iter=1: warning common, but bad error > 1e-3 bin = 0%
  iter=5: warning removed, numerical precision result

near DC:
  iter=1: bad error > 1e-3 bin ~= 36%
  iter=5: bad error > 1e-3 bin ~= 0.2%

near Nyquist:
  iter=1: bad error > 1e-3 bin ~= 20%
  iter=5: bad error > 1e-3 bin ~= 0.2%
```

### 当前判断

- 这不是 sine fitting 的原理性错误。
- 默认 `max_iterations=1` 是速度优先、普通单音够用的选择。
- 当前 warning 对普通 noisy single-tone 过于敏感，不能直接解释为 fit 失败。
- 对精密 residual / error spectrum，尤其 near DC / near Nyquist，默认一次修正可能不足。
- 下游 error analysis API 不暴露 `max_iterations` 和 fit diagnostics，使用户难以判断 warning 是否重要。

### 后续优化方向

文档建议：

```text
1. 明确说明默认策略是 “FFT initial estimate + one Taylor correction”。
2. 说明 tolerance 只在 max_iterations 允许的次数内判断收敛。
3. 说明 warning 常见，不等于 fit 失败；需要结合 rmse、fit_freq、residual spectrum 判断。
4. 建议精密 residual / error spectrum 使用 max_iterations=3-5。
```

代码优化候选：

```text
1. `fit_sine_4param` 返回 diagnostics:
   converged
   n_iterations
   initial_frequency
   last_delta_freq
   warning_reason

2. 下游 API 暴露 fit options:
   analyze_error_spectrum(..., max_iterations=3, tolerance=1e-9, return_fit=True)
   analyze_error_pdf(..., max_iterations=...)
   analyze_error_autocorr(..., max_iterations=...)

3. warning 文案更精确:
   "frequency refinement did not reach tolerance within max_iterations;
    returned fit may still be usable. Inspect rmse/fit frequency/residual."

4. 对 near DC / near Nyquist 自动提高 max_iterations 或提示用户。
```

### Issue 状态

- 2026-06-23：`ISSUE-CANDIDATE / P2`
  - 建议给作者提交 issue。
  - 建议标题：`Clarify or relax fit_sine_4param convergence warning semantics`
  - 主要范围：`fit_sine_4param(..., max_iterations=1, tolerance=1e-9, ...)` 的 warning 文案、默认迭代次数和 diagnostics。
  - 提交理由：当前 warning 在普通 noisy/non-coherent single-tone 下非常常见，但频率误差往往已经很小；用户容易把 “did not converge” 误解为 fit 失败。更精确的 warning 文案或 diagnostics 能显著降低误判。

### 处理状态

- 2026-06-23：已记录 corner/optimization。尚未修改代码或 Stage 03 正文。

## 2026-06-23: error analysis API 的 fit quality 暴露与 known-frequency 入口

### 代码位置

- `python/src/adctoolbox/aout/analyze_error_spectrum.py`
  - `analyze_error_spectrum(...)`
  - 内部调用 `fit_sine_4param(signal)` 或 `fit_sine_4param(signal, frequency_estimate=frequency)`
  - 当前不暴露 `max_iterations`、`tolerance`、`return_fit` 或 fit diagnostics
- `python/src/adctoolbox/fundamentals/fit_sine_4param.py`
  - `fit_sine_4param(..., max_iterations=1, tolerance=1e-9, ...)`
  - `_fit_core(...)`
  - 当前返回 `fit_params, sig_ideal, error_signal`，但不返回 `converged`、`initial_frequency`、`last_delta_freq` 等诊断信息
- `python/src/adctoolbox/aout/decompose_harmonic_error.py`
  - `decompose_harmonic_error(signal, n_harmonics=5)`
  - 当前 public API 先自动检测 fundamental，再做 harmonic fit
  - 没有 `frequency` / `frequency_estimate` 参数让用户传入已知 fundamental
- `python/src/adctoolbox/aout/_fit_sine_harmonics.py`
  - `_fit_sine_harmonics(signal, freq, order=5, include_dc=True)`
  - private kernel 已支持指定 `freq`，但 public API 没有把这个能力暴露出来

### 问题陈述

`analyze_error_spectrum` 的设计目标是：

```text
measured signal
  -> single-tone sine fit
  -> residual = signal - fitted fundamental
  -> FFT(residual)
```

这个目标本身没有问题。error spectrum 本来就应该显示 residual 中的 harmonic、spur、noise 和其他未被 single-tone fit 解释的结构。因此，不能把 `analyze_error_spectrum` 默认改成 multi-harmonic fit；否则 HD2/HD3 会被拟合掉，反而隐藏了 ADC distortion。

真正的工程边界在于：当前 API 把 fit 过程藏在内部，只返回 residual spectrum，没有充分暴露 fit quality。

```text
当前风险：
1. fit 频率未充分收敛时，residual 中会留下 fundamental 附近的假尖峰。
2. auto frequency detection 选错峰时，residual spectrum 可能把真实 fundamental 当成 error spur。
3. RuntimeWarning 只说明没有在 max_iterations 内达到 tolerance，
   但用户看不到 last_delta_freq、initial_frequency、converged 等上下文。
4. 用户想提高 max_iterations 或检查 fit 质量时，需要绕开高级 API，手动调用底层函数。
```

`decompose_harmonic_error` 也有类似边界。它确实能做 multi-harmonic decomposition，但 public API 仍然依赖自动 fundamental detection：

```text
signal
  -> fit_sine_4param(..., frequency_estimate=None, max_iterations=1)
  -> fundamental_freq
  -> _fit_sine_harmonics(signal, freq=fundamental_freq, ...)
```

如果强 harmonic、强 spur、drift、clipping 让自动检测选错峰，后续 harmonic decomposition 会围绕错误的 fundamental 展开。private `_fit_sine_harmonics` 已经能接受指定频率，但 public `decompose_harmonic_error` 没有暴露这个入口。

### 原理推导

single-tone residual spectrum 的数学形式是：

```text
y[n] = fundamental[n] + h[n] + noise[n] + u[n]

fit:
  y_fit[n] = projection of y[n] onto single-tone model

residual:
  e[n] = y[n] - y_fit[n]
```

当 `h[n]` 是与 fundamental 正交的 coherent harmonic 时：

```text
<h, sin(omega n)> = 0
<h, cos(omega n)> = 0
```

它应该完整留在 residual 中。这正是 error spectrum 的用途之一：

```text
residual spectrum 显示 harmonic distortion / spur / noise
```

所以 `analyze_error_spectrum` 不使用 `_fit_sine_harmonics` 并不是原理性错误，也不应默认自动拟合掉 harmonic。

但如果 fit 频率不准，设真实信号为：

```text
y[n] = A sin((omega + Delta omega)n + phi)
```

而 fitted signal 使用 `omega`，一阶展开：

```text
sin((omega + Delta omega)n + phi)
  ~= sin(omega n + phi)
   + Delta omega * n * cos(omega n + phi)
```

因此 residual 中会留下：

```text
e[n] ~= A * Delta omega * n * cos(omega n + phi)
```

这不是 ADC 真实 spur，而是 fit mismatch 造成的 near-fundamental structure。它在 error spectrum 中可能表现为 fundamental 附近的尖峰或主瓣形状。

如果 auto detection 选错峰，例如 HD2 或独立 spur 比 fundamental 更大：

```text
f_init = f_spur 或 2*f0
```

后续 Taylor / Gauss-Newton refinement 是局部迭代，只会在错误峰附近优化：

```text
wrong initial peak -> wrong local fit -> true fundamental remains in residual
```

这时 `analyze_error_spectrum` 输出仍然是数学上一致的 residual spectrum，但用户可能把 fit artifact 误判为真实 ADC error。

### 当前判断

- `analyze_error_spectrum` 的单音 residual spectrum 设计目标是合理的。
- 不建议默认改成 multi-harmonic fit，因为那会隐藏 harmonic distortion。
- 但对于精密 residual diagnosis，当前 API 缺少 fit quality / fit options，属于有实际工程意义的优化点。
- `fit_sine_4param` 的 warning 语义应配合 diagnostics 使用，而不应让用户只看到一个笼统的 did-not-converge warning。
- `decompose_harmonic_error` 的 public API 应允许传入 known fundamental frequency；这不是改变算法，而是把 private kernel 已有能力暴露出来。

### 后续优化方向

优先级建议：

```text
P1. analyze_error_spectrum 暴露 fit options:
    max_iterations
    tolerance
    frequency_estimate / frequency

P1. analyze_error_spectrum 可选返回 fit diagnostics:
    return_fit=True
    fit_frequency
    fit_amplitude
    fit_phase
    fit_offset
    rmse
    converged
    n_iterations
    initial_frequency
    last_delta_freq

P2. fit_sine_4param 提供 diagnostics 返回模式：
    保持原返回值兼容
    增加可选 return_diagnostics=True

P2. decompose_harmonic_error 增加 known-frequency 入口：
    decompose_harmonic_error(signal, n_harmonics=5, frequency=None, ...)
    frequency=None 时保持当前 auto detection 行为
    frequency 给定时直接传给 _fit_sine_harmonics

P3. 文档中明确区分：
    error spectrum = single-tone residual diagnostics
    harmonic decomposition = fundamental + harmonics model decomposition
```

### Issue 状态

- 2026-06-23：`ISSUE-CANDIDATE / P1`
  - 建议给作者提交 issue。
  - 建议标题：`Expose sine-fit options and diagnostics in analyze_error_* APIs`
  - 主要范围：
    - `analyze_error_spectrum` 暴露 `max_iterations`、`tolerance`、`frequency_estimate / frequency`。
    - 可选返回 fit diagnostics，例如 `fit_frequency`、`rmse`、`converged`、`initial_frequency`、`last_delta_freq`。
    - `decompose_harmonic_error` 支持传入 known fundamental frequency。
  - 提交理由：当前 API 隐藏内部 sine fit 质量，用户容易把 fit artifact 误判为真实 residual spur；这是精密 residual 诊断中最有工程价值的 API 优化之一。

### 处理状态

- 2026-06-23：已记录 optimization。尚未修改代码、测试或 Stage 03 正文。

## 2026-06-23: `siggen/nonidealities.py` 非理想模型保真度和实现边界审计

### 代码位置

- `python/src/adctoolbox/siggen/nonidealities.py`
  - `apply_memory_effect(...)`
  - `apply_incomplete_sampling(...)`
  - `apply_ra_gain_error(...)`
  - `apply_ra_gain_error_dynamic(...)`
  - `apply_reference_error(...)`
  - `apply_am_noise(...)`
  - `apply_drift(...)`
  - 其他相对稳健模型：`apply_thermal_noise(...)`、`apply_quantization_noise(...)`、`apply_jitter(...)`、`apply_static_nonlinearity(...)`、`apply_static_nonlinearity_hd(...)`、`apply_am_tone(...)`、`apply_clipping(...)`、`apply_glitch(...)`
- 主要调用位置：
  - `python/src/adctoolbox/examples/04_debug_analog/nonideality_cases.py`
  - `python/src/adctoolbox/examples/03_generate_signals/exp_g06_sweep_dynamic_nonlin.py`
  - `python/src/adctoolbox/examples/03_generate_signals/exp_g07_sweep_interferences.py`
- 课程关联位置：
  - `learning/adctoolbox-learning/staged_course/stage_03_error_analysis/stage_03_error_analysis.md`
  - Stage 03 中 memory、settling、reference、AM、RA gain、drift 等 case 的解释需要明确模型保真度边界。

### 问题陈述

这轮审计的核心问题不是“这些 nonideality case 是否能产生可诊断的 residual 特征”，而是：

```text
这些模型是否能被解释为真实 ADC 物理机制的合理近似？
哪些只是教学信号生成器？
哪些存在实现层面的方向错误或非因果边界？
```

当前判断分三类。

第一类：代码级或结构性问题，后续应优先修正或明确标注：

```text
1. apply_reference_error:
   当前实现可能重复加 DC，导致输出均值被整体推高。

2. apply_ra_gain_error / apply_ra_gain_error_dynamic:
   docstring 声称模拟 two-stage pipeline ADC 的 residue amplifier gain error，
   但代码把 gain error 乘在 MSB path 上，物理方向可疑。

3. apply_memory_effect:
   使用 np.roll(msb, shift=1)，让第一个样本继承最后一个样本的 MSB，
   存在非因果 wrap-around。

4. apply_drift:
   使用 filtfilt 做零相位滤波，离线造数据可以，但不是因果 drift。
   默认 drift_scale 配长记录时随机游走尺度偏大。
```

第二类：模型简化，不一定是 bug，但需要文档说清楚：

```text
1. apply_am_noise:
   使用逐样本 white Gaussian envelope。
   这能说明 AM 是乘性调制，但不等同于真实电源纹波、温漂、1/f 主导的低频 AM。

2. apply_reference_error:
   除 DC double-add 外，kick = droop_strength * abs(signal_ac) 也是简化。
   真实 CDAC reference kick 更接近 bit-pattern dependent，而不是纯 |signal| 函数。

3. apply_incomplete_sampling:
   v_prev = 0 是 AC 初始状态。
   对默认 sine 从零相位开始时影响很小；对任意相位或链式输入会造成记录开头伪影。
```

第三类：作为教学/一阶行为模型基本稳健：

```text
thermal noise
quantization noise
jitter
static HD2/HD3
AM tone
clipping
glitch
```

但“高保真”应理解为“机制和量级适合教学与一阶仿真”，不应解释成晶体管级或 signoff 级行为模型。

### 原理推导

#### 1. `apply_reference_error` 的 DC double-add 风险

当前代码：

```python
signal = self._resolve_signal(input_signal)
signal_ac = signal - self.DC
current_kick = droop_strength * np.abs(signal_ac)
vref_droop = lfilter([1], [1, -decay], current_kick)
signal_settled = signal * (1.0 - vref_droop)
return signal_settled + self.DC
```

设：

```text
signal[n] = x_ac[n] + DC
d[n] = vref_droop[n]
```

当前输出为：

```text
y[n] = signal[n] * (1 - d[n]) + DC
     = (x_ac[n] + DC) * (1 - d[n]) + DC
     = x_ac[n]*(1-d[n]) + DC*(1-d[n]) + DC
     = x_ac[n]*(1-d[n]) + 2*DC - DC*d[n]
```

当 `d[n]` 很小时：

```text
y[n] ~= x_ac[n] + 2*DC
```

这意味着若 `DC=0.5`，输出会被推到以 `1.0` 为中心，而不是仍以 `0.5` 为中心。这和 reference droop 的物理图像不一致。

更合理的乘性 reference/gain 模型应围绕 AC 分量或统一电压定义二选一：

```text
方案 A：只调制 AC 分量
    y[n] = DC + x_ac[n] * (1 - d[n])

方案 B：如果确实要调制绝对 signal
    y[n] = signal[n] * (1 - d[n])
    不应再额外 + DC
```

本轮 sanity check 观察到：

```text
clean mean ~= 0.5
apply_reference_error 后 mean ~= 0.9997
min/max ~= 0.51 / 1.49
```

这表明当前实现不仅是“reference kick 简化”，还存在明显 DC 偏置问题。

#### 2. `apply_ra_gain_error` 的 MSB/LSB 缩放方向

当前代码：

```python
msb = floor(signal_ac * 2**msb_bits) / 2**msb_bits
lsb = floor((signal_ac - msb) * 2**lsb_bits) / 2**lsb_bits
return msb * relative_gain + lsb + DC
```

因此相对于 `relative_gain=1` 的误差是：

```text
e_code[n] = msb[n] * (relative_gain - 1)
```

sanity check 证实：

```text
relative_gain = 0.99 时，
err == -0.01 * msb，最大残差约 7e-17
```

如果函数语义是“MSB path gain error”，这个公式自洽；但 docstring 写的是：

```text
interstage gain error (2-stage pipeline ADC)
residue amplifier gain error
```

在 two-stage pipeline ADC 中，更典型的流程是：

```text
1. coarse ADC 得到 q1
2. DAC 重构 q1
3. residue r = vin - q1
4. residue amplifier 输出 G * r
5. second stage 对 G*r 量化
```

因此 RA gain error 首先影响的是 residue/LSB path，而不是直接缩放 MSB path。小误差近似下：

```text
G_actual = G_ideal * (1 + epsilon)
e_RA[n] roughly proportional to residue[n] * epsilon
```

而当前代码是：

```text
e_current[n] = msb[n] * epsilon
```

由于 `msb[n]` 是信号主体，`residue[n]` 只是 coarse bin 内的剩余量，当前误差幅度会显著大于典型 residue-gain mismatch 的一阶量级。

sanity check 量级：

```text
current RA error RMS       ~= 2.85e-3
1% residue-only error RMS  ~= 3.60e-4
```

两者相差约 8 倍。这说明当前模型可以产生“by_value 斜坡”教学特征，但如果称为真实 pipeline RA gain error，物理方向和量级都需要谨慎。

`apply_ra_gain_error_dynamic` 同样把动态 gain 乘在 `v_msb_code` 上：

```python
G_dynamic = relative_gain + coeff_3 * (v_residue_out_prev_ac ** 2)
v_output_ac[n] = v_msb_code * G_dynamic + v_lsb_code
```

因此它继承了相同的建模边界。

#### 3. `apply_memory_effect` 的 `np.roll` 非因果边界

当前代码：

```python
msb_shifted = np.roll(msb, shift=1)
return msb + lsb + memory_strength * msb_shifted
```

数学上等价于：

```text
msb_shifted[n] = msb[n-1]       for n > 0
msb_shifted[0] = msb[N-1]       because np.roll wraps around
```

这让第一个样本继承记录最后一个样本的 MSB：

```text
y[0] contains memory_strength * msb[N-1]
```

真实 ADC 的第一个样本应该继承记录开始前的状态，而不是记录末尾的状态。更合理的边界处理包括：

```text
1. cold start:
   msb_shifted[0] = 0

2. steady-state warm-up:
   在正式记录前生成若干 pre-samples，用最后一个 pre-sample 状态初始化。

3. edge replicate:
   msb_shifted[0] = msb[0]
```

当前 `np.roll` 对长记录整体统计影响通常很小，但对短记录、ACF、小 lag 诊断、或严格因果教学会造成边界伪影。

另一个边界是：该函数内部把 `signal` 分成 4-bit `msb` 和 12-bit `lsb`，相当于在 memory 模型中嵌入了一次分段量化。如果调用者后续又叠加 quantization noise，需要文档说明这是“模型内部的 two-stage quantized state”，不是纯模拟 memory kernel。

#### 4. `apply_drift` 的非因果滤波和尺度问题

当前代码：

```python
drift_steps = np.random.randn(self.N) * drift_scale
drift_walk = np.cumsum(drift_steps)
b, a = scipy_signal.butter(2, 0.001)
drift = scipy_signal.filtfilt(b, a, drift_walk)
return signal + drift
```

`filtfilt` 是前向 + 后向滤波：

```text
当前样本的 drift 依赖未来样本
```

这适合离线生成平滑波形，但不适合解释成真实 ADC 的因果温漂/电源漂移。若强调物理因果性，应使用：

```text
lfilter
state-space/IIR causal filter
或显式 low-frequency colored noise 生成器
```

尺度上，随机游走末端标准差近似为：

```text
std(walk[N-1]) = drift_scale * sqrt(N)
```

对示例常用：

```text
N = 65536
drift_scale = 5e-5
sqrt(N) = 256
std_end ~= 0.0128
```

在 1 V full-scale、12-bit ADC 下：

```text
1 LSB ~= 1/4096 ~= 2.44e-4
0.0128 ~= 52 LSB
```

这对“单次记录内温漂”可能偏大。作为 stress case 可以，但作为默认真实量级要谨慎。

#### 5. `apply_am_noise` 的 white envelope 简化

当前代码：

```python
am_envelope = 1 + strength * np.random.normal(0, 1, size=N)
signal_am = signal_ac * am_envelope
```

这表达了正确的乘性结构：

```text
y[n] = x_ac[n] * (1 + m[n]) + DC
e[n] = x_ac[n] * m[n]
```

但当前 `m[n]` 是白噪声。真实 AM 来源往往是：

```text
reference ripple
supply coupling
temperature drift
1/f noise
bias noise
```

这些通常不是逐样本独立白噪声，而是低频 colored noise 或窄带 tone。结果差别是：

```text
white AM:
    sideband/noise broadly spread around signal

low-frequency AM:
    sidebands concentrated near fundamental or specific ripple offsets

AM tone:
    deterministic spurs at f_in +/- f_m
```

因此 `apply_am_noise` 适合教学“AM 是乘性噪声”，但不应直接解释成真实电源纹波模型。真实电源纹波更适合 `apply_am_tone` 或 colored AM envelope。

#### 6. `apply_incomplete_sampling` 的初始化边界

当前代码：

```python
signal_ac = signal - DC
v_prev = 0
for n in range(N):
    v_target = signal_ac[n]
    tau_dynamic = tau_nom * (1 + coeff_k * v_target**2)
    vout[n] = v_target + (v_prev - v_target) * exp(-T_track / tau_dynamic)
    v_prev = vout[n]
return vout + DC
```

核心机制是合理的：

```text
y[n] = x[n] + (y[n-1] - x[n]) * exp(-T_track/tau[n])
tau[n] = tau_nom * (1 + coeff_k*x[n]^2)
```

它能同时产生：

```text
memory-like adjacent-sample dependence
large-signal dependent settling
HD3-like distortion from x^2-dependent tau
```

边界在于 `v_prev=0`。对本库默认 base sine：

```text
x_ac[0] = A*sin(0) = 0
```

所以第一点并不严重。但如果：

```text
1. 输入不是零相位 sine
2. input_signal 来自前面链式处理
3. 记录从任意相位截取
```

那么 `v_prev=0` 就相当于强行假设记录开始前采样电容处于 0 V AC 状态，会造成开头若干样本的 settling 伪影。可选优化是加入 warm-up 或允许传入 initial_state。

### 当前判断

这轮审计后，建议把模型分为下面几档。

代码级优先修正：

```text
P0/P1. apply_reference_error:
       修正 DC double-add。
       同时明确 droop 应调制 signal_ac 还是绝对 signal。

P1. apply_ra_gain_error / apply_ra_gain_error_dynamic:
    如果函数语义保持 "residue amplifier gain error"，
    应改为影响 residue/LSB path。
    如果保留当前公式，应改名或改 docstring 为 MSB-path gain mismatch / coarse-path gain error。

P1. apply_memory_effect:
    替换 np.roll wrap-around，增加 causal boundary handling。
```

文档必须标注的教学简化：

```text
P2. apply_drift:
    filtfilt 非因果，drift_scale 对长记录可能很大。

P2. apply_am_noise:
    white multiplicative noise，不是低频 supply/temperature AM 的完整模型。

P2. apply_reference_error:
    kick = abs(signal_ac) 是简化，真实 CDAC kick 更 bit-pattern dependent。

P3. apply_incomplete_sampling:
    v_prev=0 是初始化假设，对默认零相位 sine 影响小，对任意相位有边界伪影。
```

相对稳健、只需避免过度声称的模型：

```text
thermal noise:
    加性白高斯噪声，合理。

quantization noise:
    floor + lower-edge reconstruction，符合本库 Stage 01 约定。

jitter:
    数学重生成与 CubicSpline 链式模式都合理。

static HD2/HD3:
    polynomial / Volterra 低阶近似，合理。

AM tone:
    标准乘性调制，合理。

clipping:
    percentile-based stress model，适合教学。

glitch:
    Bernoulli impulse model，抓住 heavy-tail 和 rare-event 特征。
```

### 后续优化方向

代码建议：

```text
1. 修正 apply_reference_error:
   推荐实现：
       signal_ac = signal - DC
       signal_settled = signal_ac * (1 - vref_droop) + DC
   或者若要调制绝对 signal，则删除最后的 + DC。

2. 重构 RA gain error:
   提供两个清晰模型：
       apply_coarse_path_gain_error(...)
       apply_residue_gain_error(...)
   或保留旧 API，但增加 mode="coarse_path" / "residue_path"。

3. 修正 memory boundary:
   用显式数组替代 np.roll：
       msb_shifted = np.empty_like(msb)
       msb_shifted[0] = initial_msb_state
       msb_shifted[1:] = msb[:-1]
   可选增加 warmup。

4. drift 增加 causal 参数：
       causal=True 使用 lfilter
       causal=False 保留 filtfilt 作为 offline smooth generator

5. AM noise 增加 colored envelope：
       envelope_type="white" / "lowpass" / "1/f-like" / "tone"
```

课程建议：

```text
1. Stage 03/04 对每个 nonideality case 增加 “model fidelity note”。
2. 明确区分：
       diagnostic teaching model
       physically faithful ADC behavioral model
       stress-test signal generator
3. 对 RA/reference/memory/drift 四个 case 不要用过强的真实物理措辞。
4. 如果代码未修，正文必须说明当前代码行为以代码为准。
```

测试建议：

```text
1. reference_error:
   clean sine with DC=0.5 should remain centered near 0.5 for small droop.

2. memory_effect:
   first sample should not depend on last sample unless explicitly cyclic=True.

3. RA gain:
   residue mode 的 error 应与 residue 相关，而不是与 MSB 主体相关。

4. drift:
   causal=True 输出不应依赖未来样本。
```

### Issue 状态

- 2026-06-23：`ISSUE-CANDIDATE / P0`
  - 建议给作者提交 issue。
  - 建议标题：`Bug: apply_reference_error appears to add DC offset twice`
  - 主要范围：`apply_reference_error(...)` 当前对已含 `DC` 的 `signal` 做乘性 droop 后又 `+ self.DC`。
  - 提交理由：这会把 `DC=0.5` 的 clean sine 输出中心推到接近 `1.0`，属于直接影响示例结果和诊断解释的代码级问题。

- 2026-06-24：`ISSUE-RESOLVED / P0`
  - GitHub issue：`#52 Bug: apply_reference_error adds DC offset when droop_strength=0`
  - 解决 PR：`#55 Fix signal-generator nonideality semantics`
  - 主线提交：`45d5b74 Fix signal-generator nonideality semantics`
  - 处理结果：`apply_reference_error(...)` 已改为对 `signal_ac` 做 droop 调制，再加回 `self.DC`：
    ```python
    signal_settled = signal_ac * (1.0 - vref_droop)
    return signal_settled + self.DC
    ```
  - 当前判断：该 P0 代码级问题已在 upstream/main 解决。

- 2026-06-23：`ISSUE-CANDIDATE / P1`
  - 建议给作者提交 issue。
  - 建议标题：`Model semantics: apply_ra_gain_error scales MSB path while docstring says residue amplifier gain error`
  - 主要范围：`apply_ra_gain_error(...)` 和 `apply_ra_gain_error_dynamic(...)`。
  - 提交理由：函数说明指向 two-stage pipeline ADC 的 residue amplifier gain error，但代码把 gain error 乘在 MSB/coarse path 上；如果作者本意是 coarse-path gain mismatch，应改 docstring/命名，如果本意是 RA gain error，应考虑让误差作用在 residue/LSB path。

- 2026-06-24：`ISSUE-RESOLVED / P1`
  - GitHub issue：`#53 Model semantics: apply_ra_gain_error scales MSB path while docstring says residue amplifier gain error`
  - 解决 PR：`#55 Fix signal-generator nonideality semantics`
  - 主线提交：`45d5b74 Fix signal-generator nonideality semantics`
  - 处理结果：`apply_ra_gain_error(...)` 和 `apply_ra_gain_error_dynamic(...)` 增加 `mode` 参数：
    ```text
    mode="coarse_path"   -> 保留 legacy MSB/coarse-path 行为
    mode="residue_path"  -> 提供 residue/LSB-path gain error 行为
    ```
  - 当前判断：原 issue 的“语义不清 / RA path 与实现不一致”已通过 mode 和 docstring 澄清解决；后续课程说明仍应区分 coarse-path 与 residue-path。

### 处理状态

- 2026-06-23：已记录 optimization。尚未修改 `siggen/nonidealities.py`、examples、测试或 Stage 03 正文。
- 2026-06-24：已核对 GitHub issue 动态；`#52` 和 `#53` 已由 PR `#55` 解决并进入 upstream/main。未在本学习仓库正文中同步修改说明。

## 2026-06-24: MATLAB test runner 在 Windows 上的 executable 校验失效

### 代码位置

- 分支/上下文：
  - `origin/codex/fix-25-matlab-test-env`
  - 当前 `learning/course-notes` 工作树中没有 `matlab/tests/run_matlab_tests.py`，该问题是在上述 runner 分支中验证的。
- `matlab/tests/run_matlab_tests.py`
  - `_is_executable_file(path: Path) -> bool`
  - `_resolve_matlab_candidate(candidate: str) -> Path | None`
  - `find_matlab_executable(explicit: str | None = None) -> Path | None`
  - `main(...)`
  - `subprocess.run(command, cwd=_repo_root(), check=False)`
- `python/tests/unit/test_matlab_test_runner.py`
  - `test_explicit_non_executable_matlab_path_is_rejected(...)`
  - 该测试期望显式传入不可执行 MATLAB 路径时返回 `INVALID_MATLAB_EXECUTABLE_EXIT_CODE = 2`。

### 问题陈述

MATLAB test runner 需要支持：

```text
python matlab/tests/run_matlab_tests.py common --matlab-executable <path>
```

当用户显式传入的 `<path>` 不存在或不是合法 executable 时，runner 的设计意图是：

```text
1. 在执行 MATLAB 前完成校验。
2. 打印友好的 invalid executable 错误。
3. 返回 INVALID_MATLAB_EXECUTABLE_EXIT_CODE = 2。
4. 不再 fallback 到 PATH 或标准安装路径。
```

但 runner 分支中当前校验逻辑为：

```python
def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)
```

这个写法在 Unix-like 系统上通常可用，因为文件系统有 executable bit。但在 Windows 上，`os.access(path, os.X_OK)` 不能可靠表示“这个文件可被操作系统作为程序加载执行”。实测在 Windows 上，普通文本文件、空文件、损坏的 `.exe` 只要是存在的普通文件，都可能返回 `True`。

因此，显式传入一个存在但非可执行的文件时，runner 会误判为合法 MATLAB executable，跳过 invalid-executable 分支，进入命令构造和实际执行阶段。非 dry-run 时，最后由 Windows loader 抛出底层异常，例如：

```text
OSError [WinError 216]
```

而不是 runner 自己返回预期的 exit code 2。

### 复现证据

在 Windows 环境下，从 `origin/codex/fix-25-matlab-test-env:matlab/tests/run_matlab_tests.py` 读取 runner 源码后做最小复现：

```text
os.name = nt
INVALID_MATLAB_EXECUTABLE_EXIT_CODE = 2

candidate matlab      is_file=True  X_OK=True  runner_is_exec=True
candidate notes.txt   is_file=True  X_OK=True  runner_is_exec=True
candidate matlab.exe  is_file=True  X_OK=True  runner_is_exec=True
missing-matlab.exe    is_file=False X_OK=False runner_is_exec=False
```

随后将一个普通文本文件命名为 `matlab.exe`，内容类似：

```text
I am definitely not MATLAB
```

并传入：

```text
runner.main(["common", "--matlab-executable", "<temp>/matlab.exe", "--dry-run"])
```

实际结果：

```text
dry_run_exit = 0
```

说明 runner 已经接受了这个文本文件，并打印 MATLAB 命令。

非 dry-run 时：

```text
runner.main(["common", "--matlab-executable", "<temp>/matlab.exe"])
```

实际结果：

```text
先打印命令：
<temp>/matlab.exe -batch cd('.../matlab'); ...; run_common

随后抛出：
OSError [WinError 216]
```

这说明失败不是 runner 的前置校验触发，而是 Windows 在加载文件时兜底报错。

### 原理推导

runner 的执行链是：

```text
main(argv)
  -> parse_args(argv)
  -> find_matlab_executable(args.matlab_executable)
  -> _resolve_matlab_candidate(explicit_path)
  -> _is_executable_file(candidate_path)
```

在 Windows 上，如果 `candidate_path` 是存在的普通文件：

```text
candidate_path.is_file()       -> True
os.access(path, os.X_OK)       -> True  （Windows 上退化/不可靠）
_is_executable_file(path)      -> True
```

于是：

```text
find_matlab_executable(...) -> Path(...)
```

`main()` 中的拒绝分支不会触发：

```python
if executable is None and args.matlab_executable:
    print(_invalid_matlab_executable_message(...), file=sys.stderr)
    return INVALID_MATLAB_EXECUTABLE_EXIT_CODE
```

因为 `executable` 已经不是 `None`。随后：

```text
build_matlab_command(...)
print(" ".join(command), flush=True)
subprocess.run(command, ...)
```

因此，预期的控制流：

```text
invalid explicit executable
  -> return 2
```

实际变为：

```text
invalid explicit executable
  -> accepted as executable
  -> attempted execution
  -> OSError / WinError 216
```

这违反了 runner 对显式 MATLAB executable 输入的健壮性契约。

### 当前判断

- 这是一个真实的 Windows 平台兼容性 bug。
- 根因是把 Unix-like executable permission 模型错误套用到 Windows 上。
- 问题与 MATLAB 测试本身、AOUT/Python pytest assertion、fit/error analysis 等主线问题无关，是独立的 runner robustness issue。
- 正常用户传真实 `matlab.exe` 时通常不触发，因此实际危害有限。
- 但作为命令行工具，显式用户输入校验不应依赖 OS loader 兜底；测试 `test_explicit_non_executable_matlab_path_is_rejected` 的期望是合理的。

### 后续优化方向

建议修法：

```python
def _is_executable_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if os.name == "nt":
        return path.suffix.lower() in {".exe", ".bat", ".cmd", ".ps1"}
    return os.access(path, os.X_OK)
```

如果 runner 只允许 MATLAB executable，Windows 上可以更保守：

```text
1. 显式路径只接受 .exe。
2. 或至少要求文件名为 matlab.exe。
3. 对 .bat/.cmd/.ps1 是否允许，需要根据 runner 设计决定。
```

也可以补充防御式异常处理：

```text
try:
    completed = subprocess.run(...)
except OSError as exc:
    print(f"Failed to execute MATLAB executable: {exc}", file=sys.stderr)
    return INVALID_MATLAB_EXECUTABLE_EXIT_CODE
```

但异常捕获不应替代前置校验。核心修复仍应是 Windows 上不要使用 `os.access(X_OK)` 作为 executable 判据。

测试建议：

```text
1. Windows 上，显式传入普通文本文件应返回 exit code 2。
2. Windows 上，显式传入空文件或损坏 .exe 不应在 dry-run 中被当作合法 MATLAB。
3. Unix-like 上，保留 chmod executable 的测试。
4. 测试应避免假设 chmod 在 Windows 上能设置 Unix execute bit。
```

### 跟踪状态

- 2026-06-24：`NOT-FILED / P2`
  - 尚未向作者提交 issue，不标记为 `ISSUE-CANDIDATE`。
  - 当前仅作为本地 optimization/corner 记录保留。
  - 若后续决定提交，可使用建议标题：`Windows: run_matlab_tests.py accepts non-executable files because os.access(X_OK) is unreliable`
  - 主要范围：`matlab/tests/run_matlab_tests.py` 的 `_is_executable_file(...)` 与显式 `--matlab-executable` 校验。
- 2026-06-25：`PR-SUBMITTED / P2`
  - GitHub PR：`#57 Fix Windows MATLAB runner executable validation`
  - 分支：`chenzc24:codex/fix-windows-matlab-runner` -> `Arcadia-1/ADCToolbox:main`
  - 主要修复：Windows 上不再依赖 `os.access(path, os.X_OK)` 判断 MATLAB runner executable；对 `.exe` 做 PE 签名校验，并对 `shutil.which(...)` 结果复用同一校验。
  - 额外防御：`subprocess.run(...)` 抛出的 `OSError` 会转换为 `INVALID_MATLAB_EXECUTABLE_EXIT_CODE = 2`，避免把底层 Windows loader 异常直接暴露给用户。
  - 验证命令：`cd python && uv run --with pytest pytest tests/unit/test_matlab_test_runner.py -q`，结果 `10 passed`。

### 处理状态

- 2026-06-24：已记录 optimization。尚未修改 MATLAB runner 分支代码或测试。
- 2026-06-25：已基于当前 `main` 提交修复 PR `#57`；尚未合并 upstream/main。
