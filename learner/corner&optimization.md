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
- `python/src/adctoolbox/aout/analyze_error_by_phase.py` / `analyze_error_by_value.py`
  - public wrapper，内部调用上面的 `rearrange_error_*`

### 问题陈述

`fit_sine_4param` 的目的不是保留 ADC 的全部非理想信息，而是从 measured signal 中估计一个 best-fit single-tone reference：

```text
y_fit[n] = A*cos(omega*n) + B*sin(omega*n) + C
residual[n] = y[n] - y_fit[n]
```

源码侧的事实边界（中性、无歧义）：

```text
residual = measured signal 中 best-fit single-tone 解释不了的部分
```

`analyze_error_by_value` / `analyze_error_by_phase` 都是先调用 `fit_sine_4param`，
再对 `signal - fitted_signal` 做 value/phase 条件化分析。因此它们分析的是 residual，
不是 raw signal；它们不能恢复已经被 fundamental projection 吸收的同频或近同频误差，
但能揭示 residual 中随 value/phase 变化的结构。源码 docstring 对这一点的描述是中性的，
没有做出过强声称。

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

### 处理状态

- 2026-06-22：已记录 corner。源码侧无 bug，`fit_sine_4param` 与 `analyze_error_*` 的实现与上述边界一致。
- 2026-06-28：本条早先版本还包含"Stage 03 / learner notes 措辞需修正"的内容。按本文件定义（只记录源码库 bug），课程笔记侧的措辞订正不在此跟踪；相关订正已在 `staged_course/stage_03_error_analysis.md`（§3.5、by_value/by_phase 段）和 `learner/notes.md` 落地。

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
- 复现确认：`max_lag >= N` 时代码不报错，而是**静默返回 NaN**（只在 numpy 层
  打印 “Mean of empty slice” warning）；`max_lag > N` 时抛晦涩的
  `ValueError: operands could not be broadcast together`。两者都不是有意义的用户错误提示。

### 后续优化方向

代码优化候选：

```text
1. 对 max_lag >= N 抛出明确 ValueError（当前是静默 NaN），对 max_lag > N 也给出
   有意义的错误（当前是晦涩的 broadcast ValueError）。
2. 对 max_lag > N/10 给出 warning，提示 large-lag ACF variance。
3. 增加 estimator 参数：
   estimator=”adjusted”  -> current mean over overlap, / (N-|lag|)
   estimator=”biased”    -> sum over overlap / N
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
- 2026-06-23：已并入上游 issue `#54 Expose sine-fit diagnostics and fit options in residual error-analysis APIs`（OPEN）。该 issue 同时覆盖本条和下一条（error analysis API）的 fit diagnostics / max_iterations 暴露诉求。

### 处理状态

- 2026-06-23：已记录 corner/optimization。尚未修改代码或 Stage 03 正文。
- 2026-06-28：复核确认 upstream/main 仍未合并相关修复——`fit_sine_4param` 仍 `max_iterations=1` 默认、无 diagnostics、warning 文案未改。修复 PR `#56`（OPEN）已在 fork 分支实现，等待 upstream review。Monte Carlo 结论（warning 在 99%+ noisy 单音下触发，但频率误差已 < 1e-7 bin）仍然成立。

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
- 2026-06-23：已作为上游 issue `#54 Expose sine-fit diagnostics and fit options in residual error-analysis APIs`（OPEN）提交，与上一条（fit warning）合并到同一 issue。

### 处理状态

- 2026-06-23：已记录 optimization。尚未修改代码、测试或 Stage 03 正文。
- 2026-06-28：复核确认 upstream/main 仍未合并——`analyze_error_spectrum` 只暴露 `frequency`，无 `max_iterations`/`tolerance`/`return_fit`/diagnostics；`decompose_harmonic_error` 仍无 known-frequency 入口；`fit_sine_4param` 仍无 diagnostics。修复 PR `#56`（OPEN，`codex/issue-54-harmonic-frequency-options`）已在 fork 分支实现，等待 upstream review。

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
- 2026-06-28：复核确认 PR `#57` 仍 OPEN 未合并；upstream/main 的 `_is_executable_file` 仍是 `path.is_file() and os.access(path, os.X_OK)`，Windows 上不可靠的问题仍在。

## 2026-06-25: `calibrate_weight_sine` 输出尺度与 dBFS 满量程尺度混用风险

### 代码位置

- `python/src/adctoolbox/calibration/calibrate_weight_sine.py`
  - `calibrate_weight_sine(...)`
  - `norm_factor = sqrt(1 + coeffs[idx_quadrature]**2)`
  - `_recover_columns_for_conditioning(..., norm_factor=norm_factor, ...)`
- `python/src/adctoolbox/calibration/_post_process.py`
  - `sig_k = weights @ bit_segments[k].T`
  - 返回字段：`weight`, `offset`, `calibrated_signal`, `ideal`, `error`
- `python/src/adctoolbox/spectrum/_prepare_fft_input.py`
  - `max_scale_range`
  - `peak_amplitude = (range_max - range_min) / 2`
  - `data_normalized = data_dc_removed / peak_amplitude`
- 相关官方示例：
  - `python/src/adctoolbox/examples/05_debug_digital/exp_d02_cal_weight_sine.py`
  - `python/src/adctoolbox/examples/05_debug_digital/exp_d03_redundancy_comparison.py`
  - `python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py`
  - `python/src/adctoolbox/toolset/generate_dout_dashboard.py`
- 本地触发上下文：
  - `learning/adctoolbox-learning/demos/sar_adc_model_study.py`
  - Stage 04 SAR modeling demo 中，将 `calibrate_weight_sine()["calibrated_signal"]`
    直接传给 `analyze_spectrum(..., max_scale_range=(-0.5, 0.5))`。

### 问题陈述

在 Stage 04 SAR demo 中，校准前后频谱指标出现了一个看似矛盾的现象：

```text
校准后图上的 noise floor 明显抬高约 6 dB
但 SNR / SNDR / ENOB 几乎不变
并且 calibrated 分支显示 Sig = +6.02 dBFS
```

对 ADC 满量程语义来说，`Sig > 0 dBFS` 是强烈异常信号。若输入数据被明确声明为
`max_scale_range=(-0.5, 0.5)`，那么满量程正弦应接近 `0 dBFS`，低于满量程的正弦应为负 dBFS。
校准输出出现 `+6.02 dBFS`，说明传入 spectrum analyzer 的波形不在同一 full-scale 尺度上。

实测保存数据：

```text
ideal / nonideal / oracle aout RMS ~= 0.3465
calibrated_aout RMS              ~= 0.7071
scale                            ~= 2.0408 = +6.20 dB
```

其中 `2.0408 ~= 1 / 0.49`，对应 demo 的输入正弦幅度 `input_amplitude=0.49`。
因此根本现象是：

```text
calibrated_signal 在单位正弦 / calibration solver 尺度上
而 SAR 输出和 dBFS 分析使用的是 ADC voltage/full-scale 尺度
```

当 `calibrated_signal` 被直接传给：

```python
analyze_spectrum(calibrated_signal, max_scale_range=(-0.5, 0.5))
```

spectrum analyzer 会把其解释成超过满量程的 ADC voltage waveform，于是得到：

```text
Sig = +6.02 dBFS
Noise Floor 同步上移约 6 dB
SNR/SNDR 基本不变，因为信号和噪声被同一比例整体缩放
```

这不是 SAR 模型或频谱公式本身错误，而是 `calibrate_weight_sine` 输出尺度与
`analyze_spectrum` dBFS 参考尺度之间缺少显式桥接。

### 作者意图判断

从现有官方示例可以反推出作者并非完全忽略该尺度问题。例如：

```python
# calibrate_weight_sine returns weights that sum to ~2.0 (differential signal)
# Normalize to match the single-ended weights (sum ~1.0)
weights_calibrated_norm = weights_calibrated / 2.0
```

以及：

```python
# calibrate_weight_sine returns differential-scale weights for this
# single-ended normalized SAR setup.
return np.asarray(result["weight"], dtype=float) / 2.0
```

这说明作者意图大概率是：

```text
calibrate_weight_sine 返回相对权重 / 差分尺度 / 校准求解器尺度的结果；
调用者需要根据自己的 ADC 架构、single-ended/differential 约定和 full-scale 定义再做归一化。
```

因此不能简单判定为“校准算法错”。更准确的判断是：

```text
作者意图：合理
核心算法：无明显错误
API 契约：不够显式
返回字段命名：容易让用户误以为 calibrated_signal 已经是 ADC voltage/full-scale 尺度
示例一致性：部分示例知道要归一化权重，但仍有直接分析 calibrated_signal 的用法
防误用能力：偏弱
```

### 原理推导

`calibrate_weight_sine(bits, freq=...)` 只接收：

```text
bits: raw bit columns
freq: normalized Fin/Fs
nominal_weights: optional, mainly for rank-deficiency patch
```

它没有接收：

```text
input amplitude
ADC full-scale range
single-ended / differential voltage convention
SAR quant_range
```

因此该函数从数学上无法唯一知道“真实 ADC voltage 尺度”。
它能求的是一组让 bit columns 拟合单位正弦基函数的权重尺度。

简化看，校准问题形如：

```text
bits @ w + offset ~= unit_sine + harmonic terms
```

如果真实训练信号是：

```text
vin = A * sin(...) + DC
```

而 solver 内部参考是单位正弦，那么求出来的 `w` 和 `calibrated_signal=bits@w`
天然会包含一个约 `1/A` 的尺度因子。对 `A=0.49`，该因子约为：

```text
1 / 0.49 = 2.0408
20*log10(2.0408) = 6.20 dB
```

这解释了为什么校准后 dBFS signal power 会从约 `-0.18 dBFS` 变成 `+6.02 dBFS`。

另一方面，`analyze_spectrum` 的 `max_scale_range` 行为是：

```text
给定 max_scale_range=(-0.5, 0.5)
peak_amplitude = 0.5
data_normalized = data / 0.5
```

它不会 clamp，也不会默认判断“ADC 不应超过满量程”。因此若用户传入峰值接近 `1.0` 的
`calibrated_signal`，analyzer 报 `+6 dBFS` 在数学上是自洽的：

```text
20*log10(1.0 / 0.5) = +6.02 dB
```

### 当前判断

这是真实问题，但不是 P0/P1 级别的核心算法错误。

建议定性为：

```text
ISSUE-CANDIDATE / P2
类型：API robustness / documentation / example consistency
影响：容易造成 dBFS 绝对尺度、noise floor、NSD 误读
不影响：校准相对权重趋势、SFDR/SNDR 比值类指标的基本结论
```

严重性来源：

```text
1. `calibrated_signal` 名称暗示它是校准后的信号，但没有说明其尺度不是 ADC voltage scale。
2. 比值指标 SNR/SNDR/SFDR 可能仍然“看起来对”，掩盖了绝对 dBFS 尺度错误。
3. 一旦用户关注 noise floor / NSD / signal power，结果会产生误导。
4. 官方示例中已有注释承认 differential-scale 归一化问题，说明这不是纯理论担忧。
```

非严重性来源：

```text
1. `calibrate_weight_sine` 没有 full-scale / amplitude 输入，从数学上不可能自动恢复唯一电压尺度。
2. `analyze_spectrum` 报 `+dBFS` 可以被解释为合法 overrange diagnostic。
3. 熟悉 calibration scale 的用户可以手动归一化权重或信号。
4. 不建议为了防止误用而破坏现有 API 返回值行为。
```

### 后续优化方向

文档 / docstring 优先：

```text
1. 在 `calibrate_weight_sine` docstring 的 Returns 中明确：
   `weight` 和 `calibrated_signal` are returned in calibration/solver scale.
   They are not guaranteed to be in ADC voltage or dBFS full-scale units.

2. 明确说明：
   如果要与 `analyze_spectrum(..., max_scale_range=...)` 一起使用，
   调用者必须先把权重或信号缩放到同一 full-scale convention。

3. 在 user guide / api quickref 中加入：
   calibration scale vs ADC full-scale scale
```

代码层面保持向后兼容：

```text
1. 增加 helper：
   scale_calibrated_weights(weights, target_weights=...)
   或 normalize_calibration_to_nominal(result, nominal_weights, mode=...)

2. `calibrate_weight_sine` 返回 metadata：
   scale_convention = "solver_unit_sine"
   norm_factor
   maybe effective_fundamental_amplitude

3. 新增可选参数，而不是改变默认返回行为：
   output_scale="solver" | "nominal_sum" | "full_scale"
   其中默认保留 "solver" 以避免破坏已有用户。

4. `analyze_spectrum` 在显式 `max_scale_range` 下检测到：
   max(abs(data - mean(data))) > peak_amplitude * (1 + tol)
   时给出 `UserWarning`：
   input exceeds declared full-scale; dBFS signal power may be positive.
   不建议直接抛错，因为 overrange 本身可能是用户想观察的 clipping / stress case。
```

示例修复：

```text
1. 所有使用 `calibrate_weight_sine()["calibrated_signal"]` 后接 spectrum 的示例，
   应显式说明是否在 auto-scale 模式下分析，还是已经缩放到 ADC full-scale。

2. 如果示例要展示 dBFS / noise floor / NSD，必须使用一致的 `max_scale_range`。

3. 如果示例只展示相对 SNDR/SFDR 改善，可以使用 auto-scale，但应避免解读绝对 dBFS。
```

测试建议：

```text
1. 增加 `calibrate_weight_sine` 文档行为测试：
   对半满量程 sine，返回的 calibrated_signal 可与单位正弦尺度一致；
   测试中明确这是 solver scale，而不是 ADC voltage scale。

2. 增加 example-level regression：
   如果示例声称使用固定 full-scale dBFS，则 assert sig_pwr_dbfs <= 0 + tolerance。

3. 增加 `analyze_spectrum` warning 测试：
   显式 max_scale_range 下传入超 full-scale 正弦，应产生 warning 且 sig_pwr_dbfs > 0。
```

### 处理状态

- 2026-06-25：本地 Stage 04 学习 demo 已修正展示尺度：

```python
calibrated_weights = np.asarray(cal["weight"], dtype=float) * cfg.input_amplitude
calibrated_aout = np.asarray(cal["calibrated_signal"][0], dtype=float) * cfg.input_amplitude
```

修正后：

```text
calibrated_aout Sig = -0.18 dBFS
Noise Floor ~= -72.68 dBFS
SNR/SNDR/SFDR 与 actual-weight oracle 对齐
```

- 2026-06-25：尚未修改 ADCToolbox 主代码库的 `calibrate_weight_sine` docstring、helper、
  官方 examples 或 `analyze_spectrum` warning 行为。
- 2026-06-25：尚未向作者提交 GitHub issue。若后续提交，建议标题：

```text
Clarify calibrate_weight_sine output scale and warn on dBFS full-scale mismatch
```

- 2026-06-28：复核确认上游状态未变——`calibrate_weight_sine` 的 Returns docstring 仍未说明 `weight`/`calibrated_signal` 是 solver-unit-sine 尺度而非 ADC voltage 尺度；`_prepare_fft_input` 仍按 `peak_amplitude` 归一化且不 clamp / 不对 over-range warn。核心机制（半量程输入 A=0.49 → calibrated_signal peak ≈ 2.0 ≈ 1/A，analyze_spectrum 报 +6.02 dBFS）经实验复现仍然成立。

## 2026-06-27: `calibrate_weight_sine` dual-basis 分支选择的严谨性与可审计性

### 问题级别

```text
TYPE: NUMERICAL-METHOD / ESTIMATOR-RIGOR / DIAGNOSTICS
SEVERITY: P3 by current evidence
STATUS: document and instrument first; do not replace default solver yet
```

这不是一个当前已经证明会严重影响性能的 bug，而是一个数学表述和可审计性问题。

### 背景

`calibrate_weight_sine_lite.py` 用一个最小模型固定 fundamental 的一个 basis coefficient：

```text
bits @ w + offset + sin_coeff * sin(2πfn) ≈ -cos(2πfn)
```

也就是隐含：

```text
cos fundamental coefficient = 1
```

完整版本 `_lstsq_solver.py` 做得更稳一些，会尝试两个分支：

```text
Assumption 1:
  cosine fundamental is unity

Assumption 2:
  sine fundamental is unity
```

代码结构是：

```python
A1 = np.column_stack([A_common, *extra_cols, cos_basis[:, 1:], sin_basis])
b1 = -cos_basis[:, 0]
coeffs1, _, _, _ = lstsq(A1, b1)
err1 = np.linalg.norm(A1 @ coeffs1 - b1)

A2 = np.column_stack([A_common, *extra_cols, sin_basis[:, 1:], cos_basis])
b2 = -sin_basis[:, 0]
coeffs2, _, _, _ = lstsq(A2, b2)
err2 = np.linalg.norm(A2 @ coeffs2 - b2)
```

然后选择：

```text
err1 < err2 -> use branch 1
else        -> use branch 2
```

### 严谨性问题

这个做法工程上能跑，但它没有严格对应一个清楚的全局约束最小二乘问题。

更自然的数学问题应该是：

```text
minimize || M x + F f ||
subject to ||f|| = 1

M = [bit columns, offset columns, higher-harmonic basis, ...]
F = [cos_fundamental, sin_fundamental]
f = [a, b]
```

也就是说：

```text
fundamental phase is free;
fundamental amplitude is fixed to 1;
weights / offsets / harmonic coefficients are solved consistently.
```

当前 dual-basis 则是两个 gauge-fixed 子问题：

```text
branch 1: fix a = 1, solve b and x
branch 2: fix b = 1, solve a and x
```

问题在于：

```text
err1 和 err2 是两个不同 gauge 下的 raw residual；
直接比较 raw residual 不等价于求解 ||f||=1 约束下的全局最优；
branch choice 也没有暴露 rank、singular values、condition number 或 normalized residual。
```

因此它更准确地说是：

```text
pragmatic gauge-fixing heuristic
```

而不是：

```text
strict constrained least-squares estimator
```

### polarity correction 的相关观察

`calibrate_weight_sine_lite.py` 只返回 weights，并做：

```python
if np.sum(weights) < 0:
    weights = -weights
```

这不是把每个权重取绝对值，而是整体 polarity convention。
数学上，负权重本身可以是合法最小二乘结果；整体负号更多反映参考正弦方向和
SAR 重构方向的约定不一致。

但从正交投影视角看，如果只翻 `weights` 而不同时翻完整 coefficient vector / reference，
它就不再是原始 `A @ coeffs ≈ b` 的同一个最小二乘解。

完整版本 `_post_process.py` 更自洽，会一起翻：

```text
weights
dc_offset
calibrated_signals
reference_sines
residual_errors
```

所以 lite 版本应被理解为：

```text
return normalized physical weights with positive overall SAR polarity
```

而不是：

```text
return the exact coefficient vector of the original LS projection
```

### 小型数值审计

为判断这是否值得立即改算法，做了一个本地审计：

```text
12-bit SAR
N = 4096
coherent sine training / testing
unit-cap mismatch sigma: 0% -> 10%
phase sweep
branch comparison:
  current raw-residual dual-basis selection
  err / norm_factor branch selection
  constrained phase solve:
    min ||M x + F f||, subject to ||f|| = 1
```

典型结果：

```text
raw residual choice vs err/norm_factor choice:
  某些理想场景下会有约 12% branch-choice difference；
  但归一化后的 weights / ENOB 基本相同，差异接近数值零。

current dual-basis vs constrained phase solve:
  在常规 mismatch sweep 下，ENOB 差异通常 ~1e-12 到 1e-6 bit 量级。

加入少量人工 bit flip 后:
  典型最大 ENOB 差异约 1e-3 到 2e-3 bit。
```

因此当前证据显示：

```text
这个严谨性问题真实存在；
但在典型 SAR sine calibration 场景下，它不是主要误差来源。
```

更大的误差来源更可能是：

```text
bit matrix rank / conditioning；
训练长度不足；
频率估计误差；
harmonic_order 设置；
输入没有充分激励；
随机噪声 / comparator noise；
calibration 输出尺度被误用。
```

### 为什么暂不建议直接替换默认算法

```text
1. 当前 dual-basis 行为对已有 examples 和用户代码是稳定依赖。
2. 审计结果显示典型 ENOB 差异极小，不足以支持破坏兼容性的默认替换。
3. 更严格的 constrained-phase solver 需要补 API、测试和性能验证。
4. 当前最大问题是不可审计，而不是已知严重性能错误。
```

### 建议优化路径

优先级 1：增加 diagnostics，不改默认结果。

```text
Return or optionally expose:
  basis_choice
  err1, err2
  norm_factor1, norm_factor2
  normalized_err1 = err1 / norm_factor1
  normalized_err2 = err2 / norm_factor2
  rank(A1), rank(A2)
  condition_number(A1), condition_number(A2)
  singular_values(A1), singular_values(A2) when requested
  polarity
```

优先级 2：文档说明方法边界。

```text
dual basis is a pragmatic gauge-fixing heuristic;
it tries cos=1 and sin=1 charts and picks the smaller residual;
it is not a formal global constrained least-squares derivation.
```

优先级 3：增加可选严格模式。

```text
method="dual_basis"         # default, backward compatible
method="constrained_phase"  # solve min ||M x + F f||, ||f||=1
```

可选严格模式的核心：

```text
For fixed f:
  x*(f) = argmin_x ||M x + F f||

Eliminate x:
  minimize ||P_perp_M F f||
  subject to ||f|| = 1

This is a small eigen/SVD problem in the 2-D fundamental subspace.
```

### 建议测试

```text
1. Branch-selection stability test:
   verify raw residual choice, normalized residual choice, and constrained_phase
   produce nearly identical weights on clean coherent SAR cases.

2. Stress tests:
   phase sweep, low amplitude, bit flip, comparator noise, high harmonic_order,
   near-rank-deficient bit matrices.

3. Diagnostics tests:
   ensure err/norm/rank/condition metadata is returned and finite.

4. Regression tolerance:
   current dual-basis vs constrained_phase ENOB difference should normally be < 1e-3 bit
   on documented examples, unless the example is intentionally pathological.
```

### 处理状态

```text
2026-06-27:
  记录问题和本地数值审计结论。
  暂不建议直接替换默认 solver。
  建议先补 diagnostics 和文档边界。
2026-06-28:
  课程侧的解释已在 stage_06 §4 (dual basis) 落地，本条只保留源码侧的
  算法严谨性结论和数值审计证据。
```

## 2026-06-27: `calibrate_weight_sine` harmonic nuisance 的物理归因与可辨识性风险

### 问题一句话

`calibrate_weight_sine(harmonic_order > 1)` 会把 H2/H3/... 作为 nuisance basis
加入 sine-based weight calibration。这个设计有合理用途：它可以避免输入源 / 测试链路
harmonic 污染 bit weights；但它也可能把 ADC / CDAC mismatch 产生的 harmonic
误当成 nuisance 投影掉。

因此 `harmonic_order` 不是“越高越高级”的校准精度旋钮，而是一个带有物理假设的建模选项。

### 当前实现的真实行为

当前求解器在 `_lstsq_solver.py` 中构造 dual-basis least-squares：

```python
A1 = np.column_stack([A_common, *extra_cols, cos_basis[:, 1:], sin_basis])
b1 = -cos_basis[:, 0]

A2 = np.column_stack([A_common, *extra_cols, sin_basis[:, 1:], cos_basis])
b2 = -sin_basis[:, 0]
```

当 `harmonic_order > 1` 时，H2/H3/... 的 cosine/sine basis 会进入设计矩阵，
并参与权重估计。

但最终输出不是：

```text
bits @ weight + fitted_harmonics
```

而仍然是：

```text
calibrated_signal = bits @ weight
```

对应 `_post_process.py`：

```python
sig_k = weights @ bit_segments[k].T
```

所以当前实现没有把 harmonic 直接叠加到校准输出里；真正的问题在于：

```text
harmonic basis 会改变 weight 的估计。
```

数学上，它近似等价于把某些 harmonic 子空间从误差里投影掉：

```text
min_w || P_perp(Z) · (B @ w + reference) ||^2
```

其中：

```text
B: bit matrix
w: bit weights
Z: offset + companion fundamental basis + H2/H3/... harmonic nuisance basis
P_perp(Z): 对 nuisance 子空间的正交补投影
```

### 根本限制：单个 sine capture 无法唯一归因

只看一条单音数据时，频谱中的 H2/H3 不能唯一判断来自：

```text
输入源 / 测试链路 harmonic；
ADC analog nonlinearity；
CDAC mismatch / bit-weight error；
settling / comparator / code-dependent error。
```

这些成分在单个 capture 里可以同频、同相、同窗口位置出现。
所以算法无法仅凭一条记录自动知道某个 harmonic 应该：

```text
由 bit weight 修正；
还是作为 source/test-chain nuisance 排除。
```

这不是简单换一个 least-squares 分支就能彻底解决的问题，而是观测模型的可辨识性问题。

更精确地说，即使使用 multi-capture，也不能从纯数据中完全证明 harmonic 的物理来源。
multi-capture 能增加约束、缓解混淆，但除非加入额外先验，例如 source 已知纯净、
ADC mismatch 模型已知、或每个 capture 显式建 source harmonic nuisance，否则算法仍不能直接输出：

```text
这个 H3 来自 source；
那个 H3 来自 ADC mismatch。
```

更可落地的目标是：

```text
当 harmonic attribution 的歧义已经影响 weights 时，把风险量化出来并报警。
```

### 风险两面性

如果 harmonic 主要来自输入源：

```text
harmonic_order=1 可能把源 harmonic 错误吸收到 weights；
harmonic_order=3 可以保护 weight estimate。
```

如果 harmonic 主要来自 ADC / CDAC mismatch：

```text
harmonic_order=3 可能削弱 mismatch error 对 weights 的约束；
过高 harmonic_order 会进一步增加过拟合和病态风险。
```

所以不能把 `harmonic_order > 1` 简单描述为普遍更优；它是在选择一种归因假设：

```text
observed harmonic is more like nuisance than weight error.
```

### 本地实验依据

新增可复现实验脚本：

```text
demos/harmonic_nuisance_calibration_study.py
```

运行方式：

```bash
cd E:/ADCToolbox/python
uv run python ../learning/adctoolbox-learning/demos/harmonic_nuisance_calibration_study.py
```

输出：

```text
outputs/harmonic_nuisance_calibration_study/results.csv
outputs/harmonic_nuisance_calibration_study/summary.json
```

实验分三类：

```text
1. 普通随机 unit-cap mismatch Monte Carlo。
2. 构造 harmonic-subspace 权重误差方向。
3. 训练输入源带外部 H3 污染，验证输入保持 clean sine。
```

主要观察：

```text
普通随机 unit-cap mismatch：
  H=1 与 H=3 在验证 tone 上几乎相同；
  H=31 开始出现可观测性 / 过拟合风险。

构造 harmonic-subspace 权重误差：
  H=3 会使 THD 和 weight error 变差；
  高阶 harmonic_order 风险更明显。

训练输入带外部 H3：
  H=1 会严重污染权重；
  H=3 能恢复接近 clean-source 的验证性能。
```

补充多 capture 观察：

```text
single capture, -60 dBc source H3:
  H=1  -> ENOB 约 10.3, weight error 约 5.9e-4
  H=3  -> ENOB 约 16.0, weight error 约 3.2e-7

multi-capture, 4 个不同 bin, 每条 capture 都带 -60 dBc source H3:
  H=1  -> ENOB 约 14.3, weight error 约 2.4e-5
  H=3  -> ENOB 约 16.0, weight error 约 3.1e-7
```

这个结果说明：

```text
multi-capture + H=1 可以缓解 source harmonic 污染；
multi-capture + H=1 不能消除模型缺失造成的系统性偏差；
multi-capture + per-capture harmonic nuisance 才是更干净的建模。
```

典型外部 H3 结果：

```text
训练源含 -60 dBc H3，验证源为 clean sine，sigma=1% cap mismatch：

H=1:
  validation SFDR ~= 67.8 dB
  weight_shape_error ~= 9e-4

H=3:
  validation SFDR ~= 98.2 dB
  weight_shape_error ~= 1.4e-5
```

这说明 `harmonic_order=3` 的合理用途很强：它可以防止不纯净训练源污染权重。
但也说明它必须被解释为 source/test-chain nuisance 假设，而不是无条件的 mismatch calibration 增强。

### 对现有 demo / 文档的影响

如果 demo 目标是证明：

```text
数字权重校准修复 CDAC mismatch 导致的 SFDR degradation
```

更干净的设置应优先使用：

```text
harmonic_order=1
```

如果 demo 目标是证明：

```text
校准器在输入源含 harmonic 污染时仍能稳健估计 weights
```

则可以使用：

```text
harmonic_order=3
```

但需要明确说明 harmonic basis 的物理假设：

```text
这些 harmonic 被视作 source/test-chain nuisance，而不是待校准的 ADC mismatch error。
```

不建议用 `harmonic_order=3` 的单图直接强宣称：

```text
数字校准修复了 mismatch harmonic。
```

因为这会混淆：

```text
weight calibration
source harmonic rejection
ADC harmonic attribution
```

### 建议优化路径

#### 1. 文档和 demo 分流

明确两类使用场景：

```text
harmonic_order=1:
  用于纯 mismatch 仿真、source 已知干净的测试、
  或作为 harmonic sensitivity 的 control/baseline。

harmonic_order>1:
  用于存在输入源 harmonic 污染时的 robust calibration。
  但必须明确它带有 source/test-chain nuisance 假设。
```

#### 2. 增加诊断输出

建议 `calibrate_weight_sine` 返回或可选返回：

```text
basis_choice
solver residual
rank / condition number
estimated harmonic coefficients
harmonic projection ratio
H=1 vs H=3 normalized weight delta
H=1 vs H=3 validation metric delta
```

其中 `harmonic projection ratio` 可以定义为：

```text
在去掉 DC / fundamental 后，
B 的列空间或 nominal mismatch error 有多少能量落进 H2/H3/... nuisance 子空间。
```

这个量不能证明真实来源，但可以提示：

```text
weight estimate may be sensitive to harmonic nuisance assumptions.
```

`H=1 vs H=3 normalized weight delta` 是更直接的歧义报警器。计算前应先处理整体尺度
和 polarity，例如使用 best-fit scale、`sum(abs(w))` 归一化，或架构相关的归一化规则：

```text
delta_w = || normalize(w_H1) - normalize(w_H3) || / || normalize(w_H1) ||
```

这个量的含义不是：

```text
判断 H3 到底来自 source 还是 mismatch。
```

而是：

```text
判断 harmonic nuisance 假设是否已经显著改变 weight estimate。
```

#### 3. 增加 warning

当出现以下情况时建议提示用户：

```text
H=1 和 H=3 权重差异过大；
H=1 和 H=3 validation SFDR / THD 差异过大；
bit matrix 与 harmonic subspace 高度重合；
condition number 过高；
harmonic_order 过高且样本数 / bit excitation 不足。
```

warning 文案不应说“算法失败”，而应说：

```text
harmonic attribution ambiguity may be affecting the weight estimate.
```

#### 4. 推荐 multi-capture + per-capture harmonic nuisance

更严谨的路径不是指望单个 sine capture 自动分辨 harmonic 来源，而是使用多数据集，
并给每条 capture 独立 harmonic nuisance：

```text
多个 frequency；
多个 amplitude；
多个 phase；
shared weights；
每个 capture 独立 source harmonic nuisance。
```

直觉：

```text
真实 bit weights 应跨 capture 共享；
输入源 harmonic / 测试链路误差可能随频率、幅度、相位或设备状态变化；
每条 capture 的 harmonic nuisance 吸收本条记录自己的源/测试链路 harmonic。
```

需要明确区分：

```text
multi-capture + H=1:
  可以缓解污染，因为不同 frequency 下 source harmonic 对 shared weights 的拉扯方向不同；
  但模型仍缺少 harmonic 自由度，系统性偏差不会自动消失。

multi-capture + H>=3:
  shared weights 解释跨 capture 稳定的 bit-weight structure；
  per-capture harmonic nuisance 解释每条记录自己的 H2/H3/...；
  这是更干净的建模。
```

当前 `_solve_weights_with_known_freq` 已经为 list-of-captures 构造 per-dataset harmonic basis，
所以这条优化首先是文档和推荐路径问题，不一定需要先改 solver。

#### 5. API 层面显式化 policy

未来可以考虑把 `harmonic_order` 包在更明确的 policy 之下：

```python
harmonic_policy="none"              # 不加入高阶 harmonic
harmonic_policy="source_nuisance"   # 假设 harmonic 多来自输入源 / 测试链路
harmonic_policy="diagnostic_compare"# 同时跑 H=1 / H=3 并报告差异
```

保留原参数以兼容旧代码，但文档上避免暗示：

```text
larger harmonic_order is generally better.
```

### 建议优先级

```text
P2: 文档 / demo correctness。
P2: 如果用于严肃 ADC 校准结论或论文级实验，需要 validation / diagnostics。
P3: solver API enhancement。
P3: warning diagnostics。
P3: harmonic_policy 可以作为 v2 API 方向，先不要破坏现有 `harmonic_order`。
```

这不是立刻破坏默认功能的 bug；它是一个真实的可辨识性和可解释性问题。
当前实现工程上有用，但应暴露假设、补诊断，并在 docstring / example 中分清用途。

### 非目标

```text
不要声称算法能从单个 sine capture 自动分辨 harmonic 来源。
不要声称 multi-capture 本身能完全分辨 harmonic 来源。
不要简单删除 harmonic basis。
不要把 harmonic_order>1 描述成普遍更优。
不要用 harmonic_order=3 的 mismatch demo 图单独证明 mismatch harmonic 已被权重校准修复。
```

### 处理状态

```text
2026-06-27:
  记录 harmonic nuisance 的物理归因风险。
  已新增可复现实验脚本 harmonic_nuisance_calibration_study.py。
  已修正 multi-capture 表述：单纯 multi-capture 只能缓解，multi-capture + per-capture harmonic nuisance 才更干净。
  暂不建议直接删除 harmonic basis 或替换默认 solver。
  建议优先补 docstring / example 分流、diagnostics、warning 和 multi-capture 推荐路径。
2026-06-28:
  课程侧的解释（H=1 作为 baseline、H>=3 作为 source-nuisance 假设、multi-capture 边界）
  已在 stage_06 §5 (harmonic_order) 落地，本条只保留源码侧的可辨识性结论、
  实验证据（multi-capture 表、外部 H3 数据）和 API 优化建议。
```

## 2026-06-27: rank-deficiency patch 的全秩亏崩溃与静默不可观测 bit 风险

### 问题一句话

`calibrate_weight_sine` 的 rank-deficiency patch 主体思路是合理的：

```text
Case A: constant column -> no AC information, drop
Case B: independent column -> keep
Case C: dependent column -> merge into existing effective column by nominal ratio
```

但当前实现有两个用户可见问题：

```text
1. 所有 bit columns 都不可观测时，会抛底层 IndexError，而不是明确说明校准不可辨识。
2. 部分 bit columns 不翻转时，恢复权重会静默置 0，缺少 warning / metadata。
```

第一个是确定 bug；第二个数学上可解释，但工程上危险。

### 相关源码

主流程：

```text
python/src/adctoolbox/calibration/calibrate_weight_sine.py
```

调用顺序：

```python
patched_input = _patch_rank_deficiency(bits_stacked, nominal_weights, verbose)
bits_stacked_effective = patched_input["bits_effective"]
bit_to_col_map = patched_input["bit_to_col_map"]
bit_weight_ratios = patched_input["bit_weight_ratios"]
bit_width_effective = patched_input["bit_width_effective"]

bits_stacked_effective_scaled, bit_scales = _scale_columns_for_conditioning(...)
...
weights_final = _recover_rank_deficiency(...)
```

rank patch 源码：

```text
python/src/adctoolbox/calibration/_patch_rank_deficiency.py
```

核心逻辑：

```python
bits_effective = np.empty((n_samples_total, 0))
bit_to_col_map = np.full(bit_width, -1, dtype=int)
bit_weight_ratios = np.zeros(bit_width)

for bit_idx in range(bit_width):
    col = bits_stacked[:, bit_idx]

    if np.ptp(col) < 1e-15:
        continue

    ...
```

恢复逻辑：

```python
weights_recovered = w_effective[np.maximum(bit_to_col_map, 0)]
weights_recovered = weights_recovered * bit_weight_ratios
weights_recovered[bit_to_col_map < 0] = 0.0
```

这里的 `np.maximum(bit_to_col_map, 0)` 本意是避免 `-1` 索引造成误用；
但当 `w_effective` 为空时，`0` 本身也不是合法索引。

### Bug 1：全秩亏时触发底层 IndexError

复现条件：

```text
输入 bit matrix 的所有列都是常数；
例如平 DC 输入、输入幅度太小、或预处理后没有任何 bit 翻转。
```

最小复现：

```python
import numpy as np
from adctoolbox import calibrate_weight_sine

bits = np.ones((64, 5), dtype=int)
nominal = 2.0 ** np.arange(4, -1, -1)

calibrate_weight_sine(
    bits,
    freq=1 / 64,
    nominal_weights=nominal,
)
```

当前行为：

```text
bits_effective.shape == (64, 0)
bit_to_col_map == [-1, -1, -1, -1, -1]
bit_weight_ratios == [0, 0, 0, 0, 0]

IndexError: index 0 is out of bounds for axis 0 with size 0
```

traceback 位置：

```text
calibrate_weight_sine.py
  -> _recover_rank_deficiency(...)

_patch_rank_deficiency.py
  weights_recovered = w_effective[np.maximum(bit_to_col_map, 0)]
```

这不是一个合理的用户错误提示。真正的问题应该表达为：

```text
No effective bit columns remain after rank-deficiency patching.
The calibration problem is not identifiable because no bit column has AC activity.
```

### Bug 2 / 风险：部分静默 bit 被静默恢复为 0

复现条件：

```text
只有部分 bit columns 有翻转；
其他 bit columns 在当前 capture 内恒定。
```

当前恢复行为：

```text
bit_to_col_map:      [0, -1, -1, -1, -1]
bit_weight_ratios:   [1,  0,  0,  0,  0]
w_effective:         [123]
weights_recovered:   [123, 0, 0, 0, 0]
```

从当前 capture 的 AC 拟合角度，这可以解释：

```text
constant bit 没有 AC 信息；
它对当前动态残差没有可估计贡献。
```

但从工程使用角度，这很危险：

```text
用户可能把 0 理解成真实 physical bit weight 为 0；
用户可能把这些 weights 用到另一个输入范围更大的 test capture；
低位或静默位的错误会被静默带入后续重构。
```

所以这里至少需要 warning 或 metadata，而不应该只悄悄返回 0。

> 说明：本条早先还包含 "当前数学逻辑仍然合理的部分"、"merge 顺序依赖"、
> "rank patch 与 column scaling 的耦合" 三节。这些内容（nominal ratio 分配的
> 可辨识性解释、Case C merge 对 bit 顺序的依赖、rank patch 与 column scaling 的
> 耦合关系）已在 `staged_course/stage_06_calibration.md` 第 8 节及补充、第 9 节
> 完整覆盖，故从本文件移除以避免重复。本文件只保留与源码 bug 直接相关的最小
> 复现脚本、traceback 定位、以及针对性的修复/测试建议。

### 建议修复

#### 1. 对全秩亏加明确 guard

位置：

```text
_patch_rank_deficiency(...) 末尾
或 calibrate_weight_sine(...) 取到 bit_width_effective 后
```

建议行为：

```python
if bits_effective.shape[1] == 0:
    raise ValueError(
        "No effective bit columns remain after rank-deficiency patching. "
        "All bit columns are constant in this capture, so sine-based weight "
        "calibration is not identifiable. Increase input amplitude, check bit "
        "ordering/preprocessing, or provide a capture with sufficient bit activity."
    )
```

这应作为 P1/P2 修复，因为它把底层 `IndexError` 改成可理解的用户错误。

#### 2. 暴露 rank patch metadata

建议返回或可选返回：

```text
rank_patch_applied
bit_width_effective
bit_to_col_map
bit_weight_ratios
constant_bits
merged_bits
founding_bits
rank_before
rank_after
```

这些信息能让用户知道：

```text
哪些 bit 没有 AC 信息；
哪些 bit 被合并；
哪些组合权重是按 nominal ratio 分配的；
最终权重是否可以泛化到其他 capture。
```

#### 3. 对静默 bit 置零加 warning 或 result flag

当存在：

```text
np.any(bit_to_col_map < 0)
```

应提示：

```text
Some bit columns were constant in this capture and had no AC information.
Returned weights for these bits are set to 0 for this fitted model; this does
not imply their physical ADC weights are zero.
```

如果不想默认 print warning，也至少应该在 result 里加：

```text
rank_patch_warnings
dropped_constant_bits
```

### 建议测试

```text
1. all_constant_bits_raise_value_error:
   bits = all zeros or all ones;
   calibrate_weight_sine should raise ValueError with "not identifiable" message.

2. partially_constant_bits_metadata:
   one active bit column, remaining constant columns;
   result should expose dropped_constant_bits or warnings.

3. duplicate_columns_merge_ratio:
   create B[:, j] == B[:, i];
   verify merged joint weight is stable and recovered weights follow nominal ratio.

4. rank_patch_then_scaling:
   create dependent columns with non-unit nominal ratio;
   verify effective columns are scaled and recovered weights are finite.
```

### 建议优先级

```text
P1/P2:
  全秩亏 IndexError -> 明确 ValueError。

P2:
  部分静默 bit 置零 -> warning / metadata。

P3:
  merge 顺序依赖、rank patch + scaling 耦合 -> 文档和 diagnostics。
```

### 处理状态

```text
2026-06-27:
  已复现 all-constant bit matrix 导致 IndexError。
  已确认部分 constant bit 会被恢复为 weight=0。
  暂未修改源代码。
  建议优先修 guard + test，再补 metadata/warning。
2026-06-28:
  本条的算法解释（nominal ratio 分配、merge 顺序、rank patch + scaling 耦合）
  已在 stage_06 第 8 节及补充、第 9 节完整覆盖，故从本文件移除这些重复内容。
  本文件只保留源码 bug 的最小复现脚本、traceback 定位和针对性修复/测试建议。
```

## 2026-06-28: Stage 09 subsample debug output 的 multi-N alias 反推缺口

### 问题背景

Stage 09 讨论的是芯片 debug / monitor 口常见的低速输出方式：

```text
ADC 内部高速采样: fs_in
debug 输出带宽有限
每 N 个样本只送出 1 个
fs_out = fs_in / N
```

这类 `subsample-only debug output` 没有 anti-alias low-pass。它的目标不是生成
一个干净的低带宽 DSP 信号，而是保留 raw ADC 行为供离线 debug：

```text
harmonic;
spur;
TI channel pattern;
code histogram;
clock / reference / settling artifact.
```

代价是所有原始频率都会按 `fs_out` 折叠到 debug Nyquist 带内：

```text
f_debug = fold(f_original, fs_out)
```

反过来：

```text
f_original = ±f_debug + k * fs_out
```

这是 many-to-one 映射。单个 `N` 的低速 debug 频谱无法唯一反推出原始频率。

### 为什么这是严肃问题

当前 Stage 09 已经解释了一个孤立 coherent spur 的高度在无滤波抽点前后基本守恒。
但这个结论依赖很强：

```text
只有一个 spur 折到该输出 bin;
没有其他 harmonic / TI spur / clock spur collision;
FFT coherent;
窗口和分析口径一致。
```

真实电路里，debug 输出之前我们往往并不知道：

```text
HD2 / HD3 的真实位置和幅度;
TI offset spur / gain-skew spur 是否存在;
clock / PLL / reference spur 在哪里;
某个高频 artifact 是否会折到目标带内 spur 位置。
```

因此单个 `N` 的 debug FFT 存在两个风险：

```text
1. 来源误判:
   把高频 HD3 / TI spur / clock spur 的 alias 当成真实低频 spur。

2. 幅度污染:
   多个原始频率折到同一个 debug bin 后，复数相量相加。
   该 bin 的幅度可能变高、变低，甚至相互抵消。
```

所以 raw subsample debug output 不能被当成完整频谱测量工具。它更像是：

```text
有限 IO 条件下的折叠观察口。
```

可信解释需要额外信息：

```text
多个 N;
多个输入 fin;
设计先验;
或短时间高带宽 raw capture / on-chip SRAM。
```

### 当前代码位置与现状

当前相关代码主要在 example 层，不是核心库 API。

#### 1. 当前唯一 Stage 09 示例

```text
python/src/adctoolbox/examples/09_downsample/exp_d00_subsample_aliasing.py
```

关键位置：

```text
line 31:
  def subsample(signal, n):
      return signal[n - 1 :: n]

line 37:
  def alias_freq(f, fs):
      ...

line 51:
  n_factor = 3

line 66-69:
  cases = [
      fin = 50 / 70 / 100 / 140 MHz
  ]

line 96-100:
  a_hd2 = alias_freq(2 * fin, fs_out)
  a_hd3 = alias_freq(3 * fin, fs_out)

line 157-171:
  图和打印表强调 harmonic aliasing + spur-height conservation。
```

这个脚本做的是正向演示：

```text
已知 fin / HD2 / HD3;
固定 N = 3;
计算它们会 alias 到哪里;
验证 SFDR_in 和 SFDR_out 接近。
```

它没有做：

```text
multi-N sweep;
debug spur -> original frequency candidates;
alias collision check;
N selection / recommendation;
unknown-source disambiguation.
```

#### 2. 当前 README 表述

```text
python/src/adctoolbox/examples/09_downsample/README.md
```

关键位置：

```text
line 12:
  说明 exp_d00 是 fin = 50 / 70 / 100 / 140 MHz, N = 3 的单示例。

line 18-34:
  说明 subsample-only、无 anti-alias filter、harmonic alias、spur height conservation。

line 36:
  Choosing the downsample ratio N
```

README 已经提醒选择 `N` 的问题，但没有提供自动化 multi-N 诊断或反推工具。

#### 3. Stage 文档位置

```text
learning/adctoolbox-learning/staged_course/stage_09_downsample_debug/stage_09_downsample_debug.md
```

关键位置：

```text
line 42-153:
  DSP decimation vs debug subsampling 的定义和目的差异。

line 155-186:
  alias 到输出 Nyquist 的公式和例子。

line 193-211:
  spur 高度基本守恒的教学说明。

line 304-327:
  实验：3x subsample aliasing。

line 353-389 (§4 它适合看什么，不适合看什么):
  已有 caveat：不适合判断"某个低频 debug spur 的唯一原始频率"、
  "完整未混叠频谱"、"collision 后单个 spur 的真实幅度"；
  并给出正确用法"换 N、换 fin、扫参数来减少歧义"。

line 391-426 (和 TI-ADC 的连接):
  已有 gcd(N, M) = 1 规则和 N = 31 / 15 / 7 推荐。
```

也就是说，Stage 09 文档**已经覆盖**了 "单个 N 不可唯一反演"、"alias collision"、
"换 N 换 fin 减少歧义"、"gcd(N,M)=1 / N 选择" 这些 caveat。本条早先版本认为
Stage 09 "需要明确补充" 这些内容的判断已经过时。

当前 Stage 09 文本上唯一的缺口是：collision 的机制（多个原始频率折到同一 debug bin
时是**复数相量相加**，幅度可能升高、降低甚至相互抵消）只在 §4 用一句话带过
（"collision 后单个 spur 的真实幅度"），没有展开。这一点已在 2026-06-28 的文本
订正中补上（stage_09 §4 collision 段）。

因此 Stage 09 文档侧不再有缺口；本条剩余内容纯属源码侧的 example / 工具缺口
（见下面"建议优化方向"）。

### 建议优化方向

#### 1. 增加候选频率反推工具

建议新增 utility，例如：

```text
adctoolbox.downsample.alias_candidates(...)
```

或先作为 example helper：

```text
python/src/adctoolbox/examples/09_downsample/exp_d01_multi_n_alias_disambiguation.py
```

输入：

```text
fs_in
N
observed_debug_freqs
f_max_original
tolerance_hz
```

输出：

```text
f_candidate = ±f_debug + k * fs_out
```

并折回 `[0, fs_in/2]` 或用户指定的可观测频带。

#### 2. 增加 multi-N 联立反推 demo

建议新增 example：

```text
exp_d01_multi_n_alias_disambiguation.py
```

流程：

```text
1. 构造 unknown original spur set，例如:
   fin, HD2, HD3, TI spur, clock spur。

2. 对多个 N 生成 debug observations:
   N_list = [3, 5, 7, 11, 31]

3. 对每个 N 只给出 folded debug spur。

4. 反推每个 debug spur 的 original frequency candidates。

5. 跨多个 N 匹配候选:
   找出能同时解释多个观测的原始频率。
```

这不是 Monte Carlo，而是：

```text
deterministic multi-projection / alias tomography。
```

#### 3. 增加 alias collision / N selection 工具

建议新增 helper：

```text
score_debug_downsample_factor(
    fs_in,
    n_list,
    expected_freqs,
    tolerance_hz,
)
```

用途：

```text
给定可能的 fin / HD2 / HD3 / TI spur / clock spur;
遍历候选 N;
计算哪些频率会折到同一 debug bin;
给每个 N 一个 collision score;
推荐 collision 最少且和 TI 通道数 M 互质的 N。
```

TI-ADC 场景还应检查：

```text
gcd(N, M) == 1
```

避免 debug output 总是抽到固定通道子集，隐藏 channel mismatch。

#### 4. 文档中明确边界

`09_downsample/README.md`（上游 example README）应明确写：

```text
当前 exp_d00 只是正向 alias 演示;
它不能从单个 N 的 debug 频谱唯一反推原始 spur;
真实 debug 诊断应使用 multi-N、multi-fin、设计先验或高带宽 capture 辅助。
```

（Stage 09 课程文档侧的相关 caveat 已齐备，无需再改；见上面 "3. Stage 文档位置"。）

### 建议测试

```text
1. alias_candidates_roundtrip:
   给定 fs_in、N、known f_original;
   fold 到 f_debug 后，candidate list 应包含 f_original。

2. multi_n_disambiguation_unique:
   构造两个不同 original spur，它们在 N=3 下 collision;
   加入 N=5 后应能分开候选。

3. collision_score_detects_overlap:
   expected_freqs 中两个频率在某个 N 下 fold 到同一 bin;
   score 应报告 collision。

4. ti_gcd_warning:
   M=4, N=4 或 N=8 时应提示 channel coverage risk;
   N=3,5,7,31 不应触发该 warning。
```

### 建议优先级

```text
P2:
  增加文档边界声明 + multi-N demo。

P2/P3:
  增加 alias candidate / collision score helper。

P3:
  将 helper 从 example 提升为 public API，视用户需求和真实项目使用频率决定。
```

### 处理状态

```text
2026-06-28:
  已确认当前 09_downsample 只有固定 N=3 的正向 alias example。
  已确认没有 multi-N 反推、collision check、N selection 自动化。
  暂未修改源代码。
  课程文档侧（stage_09）的相关 caveat 已齐备，并在 §4 补上了 collision 相量相加
  机制的展开；剩余缺口纯粹是源码侧的 example / 工具（alias_candidates、
  exp_d01 multi-N、score_debug_downsample_factor），仍在此跟踪。
```
