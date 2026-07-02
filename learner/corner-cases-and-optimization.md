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
- 2026-07-01：upstream 已合并 PR `#56 Expose sine-fit controls and diagnostics in AOUT analyses`，并关闭 issue `#54`。
  - 合并 commit：`e916c7292ab3d9d844c472b366acbdc71dac0a2c`
  - 已落地：`fit_sine_4param` 返回 `converged`、`n_iterations`、`initial_frequency`、`last_delta_freq`。
  - 已落地：下游 residual/error analysis API 暴露 `max_iterations`、`tolerance`、`return_fit`，可检查 fit 质量。
  - 当前判断：本条作为 upstream issue 的主要阻塞已解决。默认 `max_iterations=1` 仍保留，warning 语义仍需用户结合 diagnostics 解释；若未来要改 warning 文案或 near-DC 自动策略，应作为新增强项跟踪。

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
- 2026-07-01：upstream 已合并 PR `#56`，issue `#54` 已关闭。
  - 合并 commit：`e916c7292ab3d9d844c472b366acbdc71dac0a2c`
  - 已落地：`analyze_error_spectrum`、`analyze_error_pdf`、`analyze_error_autocorr`、`analyze_error_envelope_spectrum`、`rearrange_error_by_value`、`rearrange_error_by_phase` 等 API 支持 fit controls 和 `return_fit=True`。
  - 已落地：`decompose_harmonic_error` 及 decomposition wrappers 支持 `frequency`、`max_iterations`、`tolerance`，known fundamental 可绕过强 HD2 误检。
  - 已落地：新增 regression tests 覆盖 near-DC false residual 和 strong-HD2 fundamental mis-detection。
  - 当前判断：本条 optimization 已在 upstream/main 解决。

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
- 2026-07-01：upstream 已合并 PR `#57 Fix Windows MATLAB runner executable validation`。
  - 合并 commit：`59680024b79961188e8931715377e4be4f954f21`
  - 已落地：Windows 上不再只依赖 `os.access(path, os.X_OK)`；显式路径、`shutil.which(...)` 结果和 launch-time `OSError` 都进入统一 invalid executable 处理。
  - 当前判断：本条 Windows MATLAB runner executable 校验问题已解决。

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

## 2026-06-29: `analyze_error_by_value` 把 value-binned residual 标成 INL 的语义边界

### 上游 issue

```text
https://github.com/Arcadia-1/ADCToolbox/issues/62
```

### 代码位置

```text
python/src/adctoolbox/aout/analyze_error_by_value.py
python/src/adctoolbox/aout/rearrange_error_by_value.py
python/src/adctoolbox/aout/plot_rearranged_error_by_value.py
python/src/adctoolbox/examples/04_debug_analog/exp_a02_analyze_error_by_value.py
python/docs/source/algorithms/analyze_error_by_value.md
```

核心分 bin 逻辑在：

```text
python/src/adctoolbox/aout/rearrange_error_by_value.py
```

关键代码：

```python
scale = (n_bins - 1) / (v_max - v_min)
raw_indices = (signal - v_min) * scale
bin_indices = np.round(raw_indices).astype(int)
```

mean / RMS residual 统计也在该文件中完成。

图例误导点在：

```text
python/src/adctoolbox/aout/plot_rearranged_error_by_value.py
```

当前图例把 value-binned mean residual 标成：

```text
Mean Error (INL)
```

`exp_a02_analyze_error_by_value.py` 里还存在 example 文案和实际参数不一致的问题：注释/说明中提到较大的 bin 数，但实际演示使用的是较小的 bin 数。

### 问题陈述

`analyze_error_by_value` 的基本目标是合理的。它适合快速区分：

```text
thermal noise:
  mean residual 随 signal value 基本为 0

static k3 nonlinearity:
  mean residual 随 signal value 呈 S 型
```

它的实际处理流程是：

```text
1. fit sine
2. residual = signal - fitted_sine
3. 按 signal value 分 bins
4. 对每个 bin 求 residual mean / RMS
5. 画 value-binned residual profile
```

所以它观察的是：

```text
value-binned conditional residual statistics
```

而不是严格意义上的：

```text
code-domain transfer deviation
code width error
DNL / INL from transition levels
histogram INL/DNL
```

因此把 mean residual 曲线直接标成 `INL` 容易误导。更准确的表述应是：

```text
Mean Residual
Mean Error by Value
Value-Binned Mean Residual
INL-like residual profile  # 只能作为文档里的限定性说法
```

这不是说该工具无用，也不是说 `fit_sine_4param` 或 residual 计算错了。问题在于：当前命名、图例和文档表达会让用户把一个平滑的 value-binned residual diagnostic 误读成严格 code-domain INL。

### 实验验证

构造一个 code-level corner：

```text
8-bit code-like signal
256 codes
人为注入相邻 code 交替误差：
  even code = -0.20 LSB
  odd code  = +0.20 LSB
```

真实 code-domain 误差是：

```text
mean_abs = 0.2000 LSB
max_abs  = 0.2000 LSB
```

但如果只用 `16 value bins` 做 value-binned residual mean：

```text
mean_abs = 0.0291 LSB
max_abs  = 0.0640 LSB
```

误差几乎被相邻 code 的正负交替平均掉，看起来像 false healthy / false negative。

当 bins 提高到 `256 bins`，才基本恢复 code-scale 结构：

```text
mean_abs = 0.2007 LSB
max_abs  = 0.2820 LSB
```

本地验证图：

```text
E:/ADCToolbox/python/src/adctoolbox/examples/04_debug_analog/output/corner_value_bins_vs_codes_mismatch.png
```

这个实验说明：

```text
bins 少不是天然“更稳”；
如果 n_bins 和目标误差尺度不匹配，真实 code-level error 会被 bin averaging 平滑掉；
bins 多但每 bin 样本不足，又会让统计变 noisy。
```

### 原理推导

`analyze_error_by_value` 计算的不是 transition-level INL，而是条件均值：

```text
mean_residual[k] = mean(residual[n] | signal[n] falls into value bin k)
```

如果一个 bin 覆盖多个 code，并且这些 code 的误差符号交替：

```text
e_even = -0.20 LSB
e_odd  = +0.20 LSB
```

那么粗 bin 内部的均值会趋向：

```text
mean(e_even, e_odd) ≈ 0
```

这会把真实的 code-scale error 消掉。这个消掉不是噪声平均带来的好处，而是观测尺度选错造成的结构丢失。

严格 INL/DNL 的观测对象是 code-domain transfer curve：

```text
DNL: code width deviation
INL: transition/code boundary relative to ideal line 的累计偏差
```

它必须保留 code/transition 尺度的信息。value-binned residual profile 则是 residual 条件统计，更适合看：

```text
二阶/三阶静态非线性形状
clipping / edge distortion
value-dependent residual trend
```

但不能替代：

```text
analyze_inl_from_sine
analyze_inl_from_ramp
histogram / code-density INL-DNL
```

### 建议修改方向

#### 1. 图例改名

把：

```text
Mean Error (INL)
```

改为：

```text
Mean Residual
```

或：

```text
Mean Error by Value
Value-Binned Mean Residual
```

不要在主图例中直接叫 `INL`。

#### 2. 文档和 docstring 明确语义

文档应写清楚：

```text
This is a value-binned residual diagnostic.
It is not strict code-domain INL/DNL extraction.
```

并指向真正的静态线性工具：

```text
analyze_inl_from_sine
analyze_inl_from_ramp
```

#### 3. x 轴使用 actual value center

当前图如果只显示 bin index，很容易被误读成 code index / INL curve。

建议返回并绘制：

```text
value_centers[k]
```

而不是只画：

```text
bin index k
```

#### 4. 返回并显示 count_per_bin

建议在结果中返回：

```text
count_per_bin
```

并在图上提示 empty / low-count bins。因为每个 bin 的样本数直接决定 mean/RMS residual 的可信度。

#### 5. 输入校验

建议新增：

```text
n_bins 必须为正整数；
signal / residual 不得含 NaN / Inf；
clip_percent 不能裁到无有效样本；
v_min / v_max 在裁剪后必须有效；
low-count / empty bins 应有 warning 或显式统计。
```

#### 6. 修正 exp_a02 文案

`exp_a02_analyze_error_by_value.py` 的注释和实际参数应一致，避免教学文案说 `50 / 200 bins`，实际却用 `16 / 64 bins` 之类的不一致。

#### 7. 文档增加 bin 尺度 caveat

应明确写：

```text
bins 必须匹配目标误差尺度；
bins 太少会平均掉 code-level error，造成 false negative；
bins 太多但样本不足会导致 noisy estimate；
如果目标是 strict INL/DNL，请使用 code-density / sine/ramp histogram 工具。
```

### 优先级判断

```text
P2
```

原因：

```text
不破坏 residual 计算核心；
不影响 spectrum/SNDR/THD 等主指标；
但会误导教学和 debug workflow；
在 optimization/debug 场景里可能给出过度乐观的 false-negative 判断。
```

### 处理状态

```text
2026-06-29:
  已向 upstream 提 issue:
  https://github.com/Arcadia-1/ADCToolbox/issues/62

  当前仅记录问题和建议修复方向；
  尚未修改 analyze_error_by_value / rearrange_error_by_value /
  plot_rearranged_error_by_value / exp_a02。

2026-06-30:
  upstream 已合并修复 PR:
  https://github.com/Arcadia-1/ADCToolbox/pull/63

  issue #62 已关闭:
  https://github.com/Arcadia-1/ADCToolbox/issues/62

  合并 commit:
  5b53039de80e25f42f3744d9673aa2f7313ac27d

  已落地内容：
  - `analyze_error_by_value` / 文档改为 value-binned residual diagnostic 语义。
  - 图例从 INL-style 表述改为 value-binned residual 表述。
  - x 轴改用实际 signal value / value-bin centers。
  - 结果返回 `value_bin_centers` 和 `count_per_bin`。
  - 增加 `n_bins`、finite signal、`clip_percent`、`value_range` 输入校验。
  - 修正 `exp_a02_analyze_error_by_value.py` 的 bin 数说明。
  - 增加单测覆盖 residual diagnostic label、bin centers、count_per_bin 和输入校验。

  当前判断：
  该条目对应的 upstream 问题已解决。后续若继续优化，可关注低 count bin 的可视化提示
  是否需要更醒目；但这已属于增强项，不再是本条记录的阻塞问题。
```

## 2026-06-30: FFT dynamic metrics 的 peak-bin / integrated-lobe 口径混用

### 代码位置

- `python/src/adctoolbox/spectrum/compute_spectrum.py`
  - `sig_linear = sum(power_spectrum[fundamental_bin ± side_bin])`
  - `sig_peak = power_spectrum[fundamental_bin]`
  - `snr_dbc` / `sndr_dbc` 使用 `sig_linear`
  - `harmonics_dbc` / `thd_dbc` / `sfdr_dbc` 使用 `sig_peak`
- `python/src/adctoolbox/spectrum/_harmonics.py`
  - `_calculate_harmonic_power_plotspec(...)`
  - `_extract_highest_spur(...)`

### 问题陈述

当前 `compute_spectrum` 的动态指标混用了两种 tone power convention：

```text
SNR / SNDR / ENOB / NSD:
    使用 integrated fundamental power
    sig_linear = fundamental main-lobe bins 求和

THD / harmonics_dbc / SFDR:
    使用 peak-bin fundamental power
    sig_peak = fundamental center bin
```

同时，当前 harmonic 和 spur 也是 peak-bin 口径：

```text
harmonic_powers:
    harmonic center bin single-bin power

spur_power:
    largest remaining single-bin power
```

因此当前实现是 mixed convention，而不是统一的 integrated-lobe convention 或统一的
peak-bin convention。这对用户非常 confusing，尤其在 Hann / Blackman-Harris / flattop
等非矩形 window 下，center bin 不等于 tone total power。

另外 `_extract_highest_spur(...)` 的 docstring 当前描述 `spur_power` 为：

```text
summed over center ± side_bin
```

但实际实现是：

```python
spur_power = float(spectrum_copy[spur_bin_idx])
```

这是一个明确的文档/注释不一致。

### 原理推导

非矩形 window 会把一个 tone 的能量分布到多个 FFT bins：

```text
tone total power ≠ center-bin power
```

一次 coherent tone 数值检查显示：

```text
rectangular:
    sig_integrated - sig_peak = 0.000 dB

hann:
    sig_integrated - sig_peak = 1.761 dB

blackmanharris:
    sig_integrated - sig_peak = 3.020 dB

flattop:
    sig_integrated - sig_peak = 5.764 dB
```

因此如果一组动态指标中有的使用 `sig_linear`，有的使用 `sig_peak`，则用户不能把这些指标
理解为同一套功率定义下的结果。

更一般的 finite-record FFT tone-power estimator 应倾向于 integrated-lobe convention：

```text
P_signal   = sum fundamental main-lobe bins
P_harmonic = sum harmonic main-lobe bins
P_spur     = sum spur main-lobe bins
P_noise    = remaining in-band noise
```

然后：

```text
SNR  = P_signal / P_noise
SNDR = P_signal / (P_noise + distortion)
THD  = sum(P_harmonics) / P_signal
SFDR = P_signal / max(P_spur)
```

Peak-bin convention 可以作为 plotspec-style / legacy / quick plot-reading mode 保留，但不应
在默认 API 中与 integrated signal reference 混合而不说明。

### 建议优化方向

短期：

```text
1. 修正 `_extract_highest_spur(...)` docstring，使其明确当前返回 largest single-bin power。
2. 在文档中明确当前 `thd_dbc` / `sfdr_dbc` 是 peak-bin plotspec-style convention，
   而 `snr_dbc` / `sndr_dbc` 使用 integrated fundamental power。
3. 返回或暴露 `sig_peak_dbfs`，帮助用户看到它和 `sig_pwr_dbfs` 的差异。
```

中期：

```text
1. 新增 integrated metrics：
   - `harmonics_integrated_dbc`
   - `thd_integrated_dbc`
   - `sfdr_integrated_dbc`

2. 或新增 `metric_mode`：
   - `metric_mode="integrated"`
   - `metric_mode="peak_bin"` / `"plotspec"`

3. integrated mode 下，signal / harmonic / spur 均使用 main-lobe integrated power。
```

长期：

```text
1. 定义 close-in spur / harmonic collision 时的 integration 规则。
2. 明确 integrated spur 是否从 noise / SNDR denominator 中排除。
3. 建立 coherent / non-coherent / different-window 的回归测试矩阵。
4. 与 IEEE 1241 / IEEE 1057 或厂商 application note 的指标口径做对照说明。
```

### 优先级判断

```text
P1/P2
```

原因：

```text
不一定导致 coherent rectangular 场景下的数值错误；
但会让同一 API 输出的动态指标语义不统一；
在非矩形 window、non-coherent sampling、spur leakage 较明显时，THD/SFDR 的解释会明显依赖方法；
对教学、debug workflow 和后续标准化都有较大影响。
```

### 处理状态

```text
2026-06-30:
  已记录争议主条目：
  `learner/controversial-questions.md`
  "FFT 动态指标是否应该统一使用 integrated-lobe power？"

  当前仅记录问题和建议方向；尚未修改 `compute_spectrum.py` / `_harmonics.py`。

2026-07-01:
  upstream 已关闭 issue:
  https://github.com/Arcadia-1/ADCToolbox/issues/64

  已合并修复 PR:
  - #65 Use integrated lobe power for spectrum metrics
    https://github.com/Arcadia-1/ADCToolbox/pull/65
    commit: b633280714408ff8932dea5f076ab5d3970c1729

  - #67 Use integrated lobe power in MATLAB plotspec
    https://github.com/Arcadia-1/ADCToolbox/pull/67
    commit: 9a40fab3ca57b7e7566833b467d33e391dfa9f5e

  中间 PR #66 保留 Python integrated 修复、短暂回退 MATLAB metric change；
  随后 #67 又将 MATLAB plotspec.m 更新为 integrated-lobe THD/SFDR。

  已落地内容：
  - Python `compute_spectrum` 的 THD / harmonics_dbc / SFDR 改为 integrated-lobe power。
  - harmonic lobe 使用去重后的 main-lobe sum。
  - MaxSpur / SFDR 使用 detected spur lobe 的积分功率，而不是单 bin power。
  - MATLAB `plotspec.m` 同步为 integrated-lobe THD/SFDR。
  - 增加 coherent windowed、non-coherent HD2/THD、integrated metric power 等回归测试。

  当前判断：
  本条 peak-bin / integrated-lobe 口径混用问题已在 upstream/main 解决。
  课程侧仍需保留“integrated-lobe 不是真实频谱恢复”的边界说明。
```

## 2026-07-01: `SNR` harmonic-lobe exclusion 与 integrated-lobe 指标体系不一致

### 代码位置

- `python/src/adctoolbox/spectrum/compute_spectrum.py`
  - `THD` / `harmonics_dbc` 已通过 `_calculate_harmonic_power(...)` 使用 harmonic main-lobe power。
  - `SNDR` 只排除 DC 和 fundamental main-lobe，剩余 in-band power 全部进入 `noise + distortion` denominator。
  - `SNR` 调用 `_estimate_noise_power(...)` 得到 noise-only denominator。
- `python/src/adctoolbox/spectrum/_harmonics.py`
  - `_calculate_harmonic_power(...)` 对每个 harmonic 使用 `h_bin ± side_bin` 求和。
- `python/src/adctoolbox/spectrum/_estimate_noise_power.py`
  - `nf_method=3` 的 `_exclude_noise()` 当前只执行 `spec_noise[h_bin] = 0.0`。
  - 也就是说，只排除 harmonic center bin，没有排除 harmonic side-lobe。
- `python/src/adctoolbox/spectrum/_exclude_bins.py`
  - `nf_method=4` 走 `_exclude_bins_from_spectrum(...)`，会排除 harmonic `± side_bin`。

### 问题陈述

#65 / #67 之后，默认动态指标已经从 mixed peak-bin convention 转向 integrated-lobe convention：

```text
THD / harmonics_dbc:
    harmonic power = harmonic main-lobe integrated power

SFDR:
    spur power = detected spur lobe integrated power

SNDR:
    denominator = all non-fundamental in-band power
    harmonic center 和 harmonic side-lobe 都应该留在 noise + distortion 中
```

但 `SNR` 的 noise-only denominator 仍存在 method-dependent 不一致：

```text
nf_method=3:
    只排除 harmonic center bin
    harmonic side-lobe 会残留进 noise

nf_method=4:
    排除 harmonic center ± side_bin
```

因此在 windowed harmonic distortion case 中，同一段 harmonic lobe 可能被不同指标分类为不同物理量：

```text
THD:
    harmonic side-lobe 是 distortion power

SNDR:
    harmonic side-lobe 属于 noise + distortion denominator，合理

SNR(nf_method=3):
    harmonic center 被排除；
    harmonic side-lobe 被算作 noise
```

这不是单纯的标注问题，而是 dynamic metric energy classification consistency 问题。

### 实验现象

确定性实验设置：

```text
N = 16384
fundamental bin = 997
signal peak = 0.7 FS
noise = 多个整数 bin 正交 tone
distortion = HD2 / HD3
```

结果：

```text
rectangular + coherent:
    harmonic energy 只落在 center bin；
    nf_method=3 / nf_method=4 的 SNR 都与真值一致。

Hann / Blackman-Harris + harmonic distortion:
    harmonic energy 分布到 harmonic main-lobe；
    THD 与 SNDR 可与真值一致；
    nf_method=3 的 SNR 会偏低，因为 harmonic side-lobe 被误算为 noise；
    nf_method=4 排除 harmonic ± side_bin 后，SNR 恢复与真值一致。
```

这个结果说明：

```text
SNDR 没有问题：
    harmonic side-lobe 本来就应该进入 noise + distortion denominator。

THD 没有问题：
    harmonic side-lobe 已经通过 integrated-lobe power 计入 distortion。

问题集中在 SNR noise estimator：
    如果 SNR 定义为 signal / noise，
    那 harmonic distortion 的 main-lobe 应该整体从 noise denominator 中排除。
```

### 影响范围

```text
P1/P2: 系统一致性问题。
```

原因：

```text
不一定影响 rectangular coherent 的基本 demo；
但会影响 windowed harmonic distortion 场景下的 SNR、noise_floor_dbfs、nsd_dbfs_hz；
会让 `nf_method=3` 和 `nf_method=4` 的语义差异不只是 estimator 差异，而是 harmonic-lobe mask 差异；
会让同一 API 中 THD/SNDR/SNR 对同一段 harmonic side-lobe 给出不同物理分类；
对教学和工程 debug 都容易造成误解。
```

### 建议修复方向

优先建议：

```text
1. 统一 harmonic exclusion mask：
   将 `nf_method=3` 的 harmonic 排除从 center-bin-only 改为 `h_bin ± side_bin`。

2. 复用或抽取统一 helper：
   signal / harmonic / spur 的 lobe mask 应尽量由同一套逻辑生成，
   避免 THD、SNDR、SNR 各自维护不同的 bin classification。

3. 保留 legacy 口径时必须显式命名：
   如果需要 center-bin-only plotspec-style SNR，
   应作为 legacy / peak-bin / center-bin-only mode，而不是默认 “exclude harmonics” 语义。
```

测试建议：

```text
1. coherent rectangular + harmonic:
   修改前后 SNR 不应变化。

2. Hann / Blackman-Harris + coherent harmonic:
   nf_method=3 的 SNR 应与有限记录真值 noise-only ratio 一致。

3. 无 harmonic distortion:
   SNR / SNDR 不应因 harmonic-lobe exclusion 改变。

4. harmonic collision / alias to DC / alias to fundamental:
   exclusion mask 应沿用 `_calculate_harmonic_power(...)` 的 collision 规则或明确保持一致。
```

### 当前状态

```text
2026-07-01:
  已记录为独立 optimization item。
  这不是 #65/#67 的 integrated-lobe 主修复回退，而是其后暴露出的 SNR noise-estimator consistency 问题。
  尚未修改 upstream 代码，建议后续单独提 issue / PR。

2026-07-02:
  PR #71 已针对主问题提交修复：`nf_method=3` / `NFMethod='exclude'` 改为 harmonic-lobe exclusion，
  并补了 band-edge lobe clip。该 PR 解决 center-bin-only 与 OSR band-edge 问题。
  但 near-fundamental harmonic collision 的 Python/MATLAB policy 仍不一致，见下一条独立记录。
```

## 2026-07-02: `SNR`/`THD` near-fundamental harmonic collision 的 Python/MATLAB 口径不一致

### 代码位置

- `python/src/adctoolbox/spectrum/_estimate_noise_power.py`
  - `_estimate_noise_power(...)`
  - `nf_method=3` 的 `_exclude_noise()`
  - 当前有 fundamental-collision guard：

```python
if abs(h_bin - bin_idx) <= 2 * side_bin:
    continue
```

- `python/src/adctoolbox/spectrum/_harmonics.py`
  - `_calculate_harmonic_power(...)`
  - THD / `harmonics_dbc` 也有相同类型的 guard：

```python
is_fundamental_collision = abs(harmonic_bin_center - fundamental_bin) <= 2 * side_bin
if is_fundamental_collision:
    collided_harmonics.append(harmonic_order)
    continue
```

- `matlab/src/plotspec.m`
  - `NFMethod='exclude'` 的 harmonic exclusion：

```matlab
h_start = max(b-sideBin,1);
h_end = min(b+sideBin,inbandEnd);
spec_noise(h_start:h_end) = 0;
```

  - THD mask：

```matlab
h_start = max(b-sideBin,1);
h_end = min(b+sideBin,inbandEnd);
thd_mask(h_start:h_end) = true;
```

MATLAB 当前没有 Python 侧的 `abs(h_bin - fundamental_bin) <= 2*side_bin` guard。

### 问题陈述

当某个 harmonic alias 到 fundamental 附近时，Python 和 MATLAB 对同一段 bins 的物理分类不同。

以 0-based bin 表达：

```text
fundamental_bin = 100
side_bin = 2
fundamental lobe = 98..102

harmonic_bin = 104
harmonic lobe = 102..106
abs(104 - 100) = 4 = 2*side_bin
```

Python：

```text
认为 harmonic 与 fundamental collision；
SNR nf_method=3: 不额外清 harmonic lobe；
THD / harmonics_dbc: 不计入该 harmonic；
结果：103..106 仍可能被当成 noise，且不进入 THD。
```

MATLAB：

```text
先清掉 fundamental lobe；
随后仍对 harmonic lobe 做 clip / mask；
结果：103..106 会被 NFMethod='exclude' 从 noise 中排除；
THD 也会把 103..106 计入 harmonic distortion。
```

因此同一个 near-fundamental aliased harmonic：

```text
Python SNR: 更保守，可能偏低；
MATLAB SNR: 更乐观，可能偏高；

Python THD: 可能偏低，因为整条 collided harmonic 被跳过；
MATLAB THD: 可能偏高/更接近 clipped-lobe 口径，因为 fundamental lobe 外侧 annulus 被计入。
```

这不是 PR #71 的 band-edge clip 问题。#71 已解决：

```text
harmonic center 在 analysis band 边界外，但 lobe 仍部分在带内时，
Python 与 MATLAB 都应自然 clip。
```

本条是另一类问题：

```text
harmonic center 在 fundamental 附近时，
Python 选择 collision skip；
MATLAB 选择 unconditional lobe clip。
```

### 原理解释

从测量物理看，harmonic alias 到 fundamental 附近时确实存在不可分辨性：

```text
fundamental leakage
near-fundamental spur / AM sideband / phase-noise skirt
aliased harmonic lobe
```

这些能量可能落在相邻 bins，有限 FFT 和 window 下无法仅凭 bin index 完全区分。因此 Python 的 guard 有保守意义：

```text
避免把 fundamental 附近的真实 noise / sideband 误删；
避免把无法可靠分离的 harmonic 强行报告为 THD。
```

但 MATLAB 当前行为也有另一种一致性：

```text
只要 harmonic lobe 的一部分落在 analysis band 内，
就按 lobe mask 处理；
fundamental lobe 已经提前清零，重叠部分是 no-op，
非重叠 annulus 仍按 harmonic lobe 处理。
```

问题不在于哪一种一定物理错误，而在于 Python / MATLAB 当前选择了不同 policy，
导致 `SNR` / `THD` 在这个 corner 下不能 parity。

### 严重程度

```text
P1: 动态指标定义一致性问题。
```

原因：

```text
发生概率低于常规 harmonic-lobe / OSR band-edge 问题；
但一旦 harmonic alias 接近 fundamental，SNR 与 THD 的差异可能很大；
该差异会直接影响 Python↔MATLAB parity；
也会影响教学中“同一套 dynamic metric mask convention”的解释。
```

这不是显示层 bug，也不是单纯文档问题；它会改变 `snr_dbc`、`noise_floor_dbfs`、`nsd_dbfs_hz`、
`thd_dbc` 和 `harmonics_dbc` 的数值。

### 建议修复方向

需要先明确项目 policy，再同步 Python 和 MATLAB。不要只在一侧打补丁。

可选方向：

```text
Option A: 严格 MATLAB parity / unconditional clipped lobe
  - 去掉 Python NF / THD 的 fundamental-collision guard；
  - 统一用 clipped harmonic lobe mask；
  - fundamental lobe 已清零，重叠部分自然 no-op；
  - 优点：Python/MATLAB 对齐，mask 逻辑简单；
  - 风险：near-fundamental AM sideband / phase-noise skirt 可能被误排除，SNR 可能偏乐观。

Option B: 保守 collision policy
  - 保留 Python guard；
  - MATLAB NF / THD 增加同等 collision guard；
  - 优点：不把不可分辨的 near-fundamental 能量强行分类为 harmonic；
  - 风险：偏离 MATLAB 当前 legacy 行为，THD 可能低估 collided harmonic 的可见 annulus。

Option C: 显式 policy 参数
  - 例如 harmonic_collision_policy = "clip" / "skip" / "warn"；
  - 默认选择需谨慎，避免破坏 legacy 行为；
  - 实现和文档成本较高，不适合作为小修。
```

无论选择哪一项，都应增加 Python 与 MATLAB 的共同回归测试：

```text
1. harmonic center 距 fundamental <= side_bin:
   完全不可分辨，应按选定 policy 一致处理。

2. harmonic center 距 fundamental 在 (side_bin, 2*side_bin]：
   lobe 与 fundamental lobe 部分重叠，annulus 是关键差异区。

3. near-fundamental AM sideband / spur:
   验证 chosen policy 对 SNR 乐观/保守偏差的说明。
```

### 当前状态

```text
2026-07-02:
  已记录为未解决 high-priority optimization / parity issue。
  PR #71 未修改该 guard；#71 只修 harmonic-lobe exclusion、OSR in-band clip 和 band-edge lobe clip。
  建议后续单独开 issue / PR，先决定 Python/MATLAB near-fundamental collision policy。
```

## 2026-07-01: OSR 下 Python `THD` / `harmonics_dbc` 未受 in-band 限制

### 代码位置

- `python/src/adctoolbox/spectrum/compute_spectrum.py`
  - `n_inband = rfft_inband_bin_count(N, osr)`
  - `SNDR` / `SFDR` / `SNR` 都使用 `n_inband` 限制分析带宽。
  - `THD` / `harmonics_dbc` 调用 `_calculate_harmonic_power(...)` 时没有传入 `n_inband`。
- `python/src/adctoolbox/spectrum/_harmonics.py`
  - `_calculate_harmonic_power(...)`
  - harmonic lobe 终点当前是：

```python
harmonic_end_index = min(harmonic_bin_center + side_bin + 1, len(power_spectrum))
```

也就是说，Python `THD` / `harmonics_dbc` 当前最多只受 full rFFT spectrum 长度限制，不受
`osr` 对 in-band bandwidth 的限制。

- `matlab/src/plotspec.m`
  - MATLAB 侧 #67 后的 THD lobe 终点是：

```matlab
h_end = min(b+sideBin,inbandEnd);
```

因此 MATLAB `plotspec.m` 的 THD 已经受 in-band 限制。

### 问题陈述

在 OSR 分析中，动态指标应只评价：

```text
0 .. Fs/(2*OSR)
```

这个 signal band 内的信号、噪声、失真和 spur。当前 Python `compute_spectrum` 中：

```text
SNDR:
    denominator = sum(spec_sndr[:n_inband])

SFDR:
    spur search = spectrum[:n_inband]

SNR:
    noise estimate = spectrum[:n_inband]

THD / harmonics_dbc:
    harmonic lobe = h_bin ± side_bin, bounded by len(power_spectrum)
```

因此可能出现同一条带外 harmonic：

```text
SNDR / SFDR / SNR:
    不把它当作 in-band error

THD:
    仍然把它计入 distortion
```

这会让 OSR 下的 `THD` 与 `SNDR/SFDR/SNR` 使用不同的分析带宽。

### 实验现象

确定性实验：

```text
N = 8192
fundamental bin = 900
HD2 bin = 1800
HD2 amplitude = -60 dBc
window = rectangular
side_bin = 0
```

结果：

```text
OSR=1:
    n_inband = 4097
    HD2 bin  = 1800 in-band
    THD=-60 dB, SNDR=60 dB, SFDR=60 dB

OSR=2:
    n_inband = 2049
    HD2 bin  = 1800 in-band
    THD=-60 dB, SNDR=60 dB, SFDR=60 dB

OSR=4:
    n_inband = 1025
    HD2 bin  = 1800 out-of-band
    THD=-60 dB, SNDR=200 dB, SFDR=266 dB
```

`OSR=4` 时，HD2 已经在 signal band 外；`SNDR` / `SFDR` 已把它排除在分析带宽外，但 `THD`
仍然报告 `-60 dB`。这是 Python dynamic metric 的明确带宽不一致。

### 影响范围

```text
P1/P2: OSR 场景下的核心动态指标一致性问题。
```

原因：

```text
不影响 OSR=1 的常规全 Nyquist 分析；
不影响 harmonic 仍在 in-band 的情况；
但会影响 oversampling / narrow-band ADC / noise-shaping workflow；
会导致 Python 与 MATLAB plotspec.m 的 THD 口径不一致；
会让 THD 与 SNDR/SFDR/SNR 在同一次 OSR 分析中使用不同 bandwidth。
```

### 建议修复方向

```text
1. 给 `_calculate_harmonic_power(...)` 增加 `n_inband` 或 `max_bin` 参数。
2. harmonic lobe 终点使用 `min(h_bin + side_bin + 1, n_inband)`。
3. harmonic center 若不在 `0 < h_bin < n_inband`，则不计入 THD / harmonics_dbc。
4. collision / DC handling 继续沿用现有规则，但边界应与 in-band mask 一致。
5. 增加回归测试：
   - HD2 in-band: THD 应正常报告。
   - HD2 out-of-band under OSR: THD 应不再计入该 harmonic。
   - Python 与 MATLAB plotspec.m 对 OSR THD 口径应一致。
```

### 当前状态

```text
2026-07-01:
  已由动态指标一致性审计发现并记录。
  尚未修改 upstream 代码。
  建议优先级与 SNR harmonic-lobe exclusion 相近，适合一起作为 dynamic metric mask consistency PR 处理。
```

## 2026-07-01: `perfosr` / `sweep_performance_vs_osr` 与主动态指标存在 SNDR/SFDR 口径差异

### 代码位置

- `python/src/adctoolbox/spectrum/sweep_performance_vs_osr.py`

```python
err_spec = np.abs(np.fft.fft(err_windowed)) ** 2 / n ** 2 * 4
sig_power = amplitude ** 2 / 2
```

- `python/src/adctoolbox/oversampling/perfosr.py`
  - MATLAB-compatible wrapper，直接调用 `sweep_performance_vs_osr(...)`。
- `matlab/src/perfosr.m`

```matlab
err_spec = abs(fft(err_windowed)).^2 / N^2 * 4;
sig_power = mag^2 / 2;
```

### 问题陈述

`compute_spectrum` / `plotspec` 的 dBFS convention 是：

```text
full-scale sine lobe power = 1
```

也就是 peak amplitude `A` 在 full-scale peak reference 下对应 integrated tone power：

```text
P_signal = A^2
```

这来自 spectrum path 的 one-sided scaling / window RMS normalization convention。

但 `perfosr` / `sweep_performance_vs_osr` 是 residual-fit path，当前组合是：

```text
error spectrum:
    one-sided-like scaling uses *4

signal power:
    amplitude^2 / 2
```

这会让 signal power 与 error spectrum 的 power scale 不匹配，白噪声场景下 `SNDR` 相对
`analyze_spectrum` / 理论 SNR 低约 `3 dB`。

### 实验现象

确定性 / 固定 seed 实验：

```text
N = 4096
coherent sine
A = 0.5 peak
white noise rms = 1e-3
OSR = 1
window = rectangular for analyze_spectrum reference
```

结果：

```text
theory SNR       = 50.969 dB
analyze_spectrum = 50.837 dB
perfosr sweep    = 47.783 dB
```

差值约：

```text
50.837 - 47.783 = 3.054 dB
```

这不是随机误差，而是功率尺度差异。MATLAB `perfosr.m` 也继承同样公式，因此这是 Python/MATLAB
parity 下的共同 legacy 口径，不是 Python 独有偏差。

### 2026-07-02 补充：SFDR 也不是 integrated-lobe 口径

同一段代码里，`SFDR` 的 spur power 取法是：

```python
incremental = err_spec[n_inband_prev:n_inband]
spur_power = max(spur_power, np.max(incremental))
sfdr[orig_idx] = 10 * np.log10(sig_power / spur_power)
```

也就是说 `perfosr` / `sweep_performance_vs_osr` 的 SFDR 是 residual spectrum 的单 bin 最大值，
不是 `compute_spectrum` 当前采用的：

```text
largest spur lobe power = sum(center - side_bin ... center + side_bin)
```

这会带来两个不一致：

```text
1. SNDR:
   由于 signal power 与 error spectrum power scaling 不匹配，absolute SNDR 约低 3.01 dB。

2. SFDR:
   由于 spur power 用单 bin peak，不是 integrated-lobe power，和主频谱 SFDR 口径不同。
```

因此这个条目不只是 `3 dB SNDR offset`，而是 `perfosr` 整体没有复用主动态指标的
power convention / lobe convention。

### 影响范围

```text
P2: 公开 API 的动态指标口径不一致。
```

原因：

```text
`perfosr` 是公开 API；
文档说它 sweep ADC performance metrics versus OSR；
用户自然会把它的 SNDR / SFDR / ENOB 与 `analyze_spectrum(..., osr=...)` 对齐理解；
但当前 SNDR absolute value 可能低约 3 dB，SFDR 也不是 integrated-lobe SFDR。
```

相对趋势仍可能有用：

```text
OSR 增大时，white noise 下 SNDR slope 仍能反映 3 dB / octave；
但 absolute SNDR / ENOB 与主动态指标不一致。
```

### 建议修复方向

需要先决定作者意图：

```text
Option A: 与 MATLAB perfosr legacy 完全兼容
    - 保持 `mag^2/2`
    - 明确文档说明 perfosr uses RMS physical signal power convention，
      不保证与 analyze_spectrum dBFS/SNDR absolute value 对齐。

Option B: 与 ADCToolbox 主动态指标 convention 统一
    - 将 `sig_power` 改为与 `err_spec` scaling 一致的 convention。
    - 或统一调用 / 复用 compute_spectrum-style power scaling helper。
    - 更新 MATLAB perfosr 或至少记录 Python/MATLAB 兼容差异。
```

测试建议：

```text
1. Pure sine + white noise:
   perfosr(OSR=1) 应与 analyze_spectrum(osr=1) / theory SNR 一致或明确相差固定 legacy offset。

2. OSR sweep:
   修复后 slope 不应改变，absolute SNDR 应整体对齐主动态指标。

3. SFDR lobe test:
   构造一个 Hann-windowed residual spur，验证 perfosr 的 SFDR 是否与 compute_spectrum 的
   integrated-lobe SFDR 使用同一口径，或明确文档说明它是 legacy single-bin spur metric。

4. MATLAB parity:
   若改变 Python，则需决定是否同步 MATLAB perfosr。
```

### 当前状态

```text
2026-07-01:
  已记录为 dynamic metric consistency audit 发现的问题。
  尚未修改 upstream 代码。
  需要先决定 perfosr 是追求 MATLAB legacy 复刻，还是追求 toolbox 内部 metric convention 一致。
```

## 2026-07-01: `quick_sndr` 默认 `side_bin` 行为与 `compute_spectrum` 默认行为不一致

### 代码位置

- `python/src/adctoolbox/spectrum/quick_sndr.py`

```python
if side_bin is None:
    side_bin = _get_default_side_bin(win_type)
```

- `python/src/adctoolbox/spectrum/compute_spectrum.py`

```python
if side_bin is None:
    side_bin = _detect_side_bin_auto(...)
```

### 问题陈述

`quick_sndr` 文档写法强调：

```text
SNDR + ENOB from a single 1-D capture (same SNDR definition as analyze_spectrum)
```

但实际只在以下条件下严格一致：

```text
coherent capture；
或用户显式传入相同 side_bin；
或 signal leakage 正好被 coherent default side_bin 覆盖。
```

在 non-coherent capture 中，`compute_spectrum(side_bin=None)` 会自动估计 side-bin，而 `quick_sndr`
不会；它只使用 window 的 coherent main-lobe default。因此 `quick_sndr` 默认可能把 main-lobe leakage
算入 noise+distortion，得到显著偏低的 SNDR。

### 实验现象

确定性实验：

```text
N = 8192
fundamental bin = 997.37
window = Hann
spur / noise fixed
```

结果：

```text
noise=0:
    quick_sndr default    = 20.613 dB
    compute_spectrum auto = 60.000 dB
    compute_spectrum sb=1 = 20.613 dB

noise=1e-3:
    quick_sndr default    = 20.610 dB
    compute_spectrum auto = 53.120 dB
    compute_spectrum sb=1 = 20.610 dB
```

说明 `quick_sndr` 与 `compute_spectrum(side_bin=1)` 一致，但不与 `compute_spectrum(side_bin=None)`
的 auto behavior 一致。

### 影响范围

```text
P2/P3: fast path 默认语义不一致。
```

原因：

```text
它不影响显式 side_bin 的优化循环；
也不影响 coherent capture；
但 bare default `quick_sndr(x)` 很容易被用户理解成 analyze_spectrum 的轻量等价版本；
non-coherent 场景下会产生很大的 pessimistic SNDR。
```

### 建议修复方向

保守方案：

```text
1. 收窄 docstring：
   quick_sndr is aligned with compute_spectrum only for explicit/coherent side-bin settings。

2. 文档示例中建议：
   non-coherent 或未知 coherent 状态下使用 analyze_spectrum；
   optimization loop 中若使用 quick_sndr，应显式传 side_bin。
```

功能方案：

```text
1. 给 quick_sndr 增加 `side_bin="auto"` 或 `auto_side_bin=True`。
2. 默认是否改成 auto 需要谨慎，因为 quick_sndr 的卖点是 fast path。
3. 如果保持 None=coherent default，则参数文档必须明确。
```

测试建议：

```text
1. coherent Hann + side_bin=1:
   quick_sndr 与 compute_spectrum 完全一致。

2. non-coherent Hann + side_bin=None:
   测试应明确当前 default 是 coherent default，不是 auto。

3. 若新增 auto path:
   quick_sndr(auto) 与 compute_spectrum(None) 在 SNDR/ENOB 上一致。
```

### 当前状态

```text
2026-07-01:
  已记录为 consistency/documentation issue。
  尚未修改 upstream 代码。
```

## 2026-07-02: `SFDR` spur 搜索仍先按 center-bin peak 选中心，再计算 integrated-lobe power

### 代码位置

- `python/src/adctoolbox/spectrum/_harmonics.py`

```python
spectrum_copy = spectrum_power[:n_search_inband].copy()
...
spur_bin_idx = int(np.argmax(spectrum_copy))
spur_start = max(spur_bin_idx - side_bin, 0)
spur_end = min(spur_bin_idx + side_bin + 1, n_search_inband)
spur_power = float(np.sum(spectrum_copy[spur_start:spur_end]))
```

### 问题陈述

#65 / #67 之后，`SFDR` 的 reported spur power 已经改成 integrated-lobe power：

```text
SFDR = signal_lobe_power / max_spur_lobe_power
```

但当前 `_extract_highest_spur(...)` 的搜索流程仍是：

```text
1. 在单个 bin power 上找最大 bin，作为 spur center。
2. 只围绕这个 center 计算 center +/- side_bin 的 lobe sum。
```

严格的 integrated-lobe SFDR 应该是：

```text
1. 对每个候选 spur center 计算 lobe sum。
2. 选择 lobe sum 最大的 spur。
```

否则在两个 spur 接近、一个 coherent 单 bin 较高、另一个 non-coherent 或 windowed lobe 总能量更高时，
代码可能选择错误的 spur center，进而使 SFDR 略偏乐观或偏离真实最大 lobe spur。

### 数值验证

构造：

```text
N = 8192
window = hann
side_bin = 1
fundamental bin = 251
spur A: coherent, bin = 900, amplitude ~= -64 dBc
spur B: non-coherent, bin ~= 1300.37, amplitude ~= -63.5 dBc
```

扫描所有候选 center 的 integrated-lobe power 后发现：

```text
current code selected center = 900
current selected lobe        ~= -64.00 dBc
true largest lobe center     = 1300
true largest lobe            ~= -63.54 dBc
difference                   ~= 0.46 dB
```

这个例子不是常见的大失真，但证明了算法定义上存在不一致：

```text
reported SFDR 使用 integrated-lobe denominator；
spur center search 却使用 center-bin peak criterion。
```

### 严重性

```text
P2/P3
```

原因：

```text
大多数普通 coherent spur 或明显单一最大 spur 场景不受影响；
但在 windowed / non-coherent / close-spur 场景下，SFDR 可能选错 spur。
这属于主动态指标数值口径问题，严重性低于 SNR harmonic-lobe 和 OSR THD bandwidth，但高于纯显示 marker 问题。
```

### 建议修复方向

1. 抽一个 shared lobe-sum helper：

```python
_component_lobe_power(power_spectrum, center, side_bin, upper_bound)
```

2. `_extract_highest_spur(...)` 改成扫描 candidate centers 的 lobe sum，而不是先 `argmax(single_bin)`。

3. 为避免同一 lobe 多个 center 重复竞争，可选择以下策略之一：

```text
Option A:
  对所有 candidate center 计算 lobe sum，取最大；简单但相邻 center 可能返回相同 lobe。

Option B:
  先按 local maxima 找候选 center，再计算每个 local maximum 的 lobe sum；更符合 marker 语义。

Option C:
  构造 exclusion mask / connected components，按 contiguous non-signal components 计算总 power；
  最严谨，但改动较大。
```

4. 增加 regression test：

```text
同一 spectrum 里放两个 spur：
  A: center bin higher但 lobe sum 较低；
  B: center bin较低但 lobe sum 较高。

断言 SFDR 选择 B。
```

### 当前状态

```text
2026-07-02:
  已由动态指标一致性审计发现并记录。
  尚未修改 upstream 代码。
```

## 2026-07-01: Python spectrum plot marker 高度仍是 center-bin，而指标数字已是 integrated-lobe

### 代码位置

- `python/src/adctoolbox/spectrum/plot_spectrum.py`

```python
spur_db = spec_db[spur_bin_idx]
harmonic_power_db = spec_db[harmonic_bin_center]
```

- `python/src/adctoolbox/spectrum/plot_spectrum_virtuoso.py`
  - 同样使用 center-bin `spec_db[...]` 绘制 harmonic / MaxSpur marker。
- `matlab/src/plotspec.m`

```matlab
plot((sbin-1)/N_fft*Fs,10*log10(spur+10^(-20)),'rd');
```

MATLAB MaxSpur marker 当前画的是 integrated spur power，而 Python MaxSpur marker 仍画 center-bin height。

### 问题陈述

#65 / #67 后，计算指标已经采用 integrated-lobe convention：

```text
THD / harmonics_dbc:
    harmonic lobe power

SFDR:
    spur lobe power
```

但 Python 图上的 marker 仍画在：

```text
harmonic center-bin height
MaxSpur center-bin height
```

这不影响 `metrics["thd_dbc"]` / `metrics["sfdr_dbc"]` 的计算，但会造成图形语义歧义：

```text
图上的方块/钻石 y 值:
    center-bin dBFS

左侧/右侧指标文本:
    integrated-lobe dBc
```

非矩形 window 下，center-bin height 与 lobe-integrated power 可能相差 ENBW 相关的 dB 数。

### 影响范围

```text
P3: 可视化一致性 / 教学解释问题。
```

原因：

```text
不影响核心指标；
但用户会自然用 marker 高度和 SFDR/THD 数字做视觉对应；
Python 与 MATLAB MaxSpur marker 表现也不完全一致；
在 Hann / Blackman-Harris / flattop 下尤其容易 confusing。
```

### 建议修复方向

```text
1. 保留 marker 放在 center frequency，但 y 值可选择 integrated-lobe dBFS。
2. 或继续画 center-bin marker，但 tooltip/label/文档明确：
   marker y = center-bin display height；
   metrics = integrated-lobe power ratio。
3. 更完整方案：
   在 plot_data 中返回 harmonic_lobe_powers / spur_lobe_power_dbfs，
   plotter 不再从 `spec_db[center]` 反推出 integrated metric 语义。
```

测试建议：

```text
1. Hann full-scale tone + spur:
   marker center-bin height 与 integrated-lobe label 的差异应被测试覆盖或文档化。

2. Python / MATLAB plot marker convention:
   若目标是 parity，应统一 MaxSpur marker y 值。
```

### 当前状态

```text
2026-07-01:
  已记录为 visualization consistency issue。
  尚未修改 upstream 代码。
```

## 2026-07-01: `_calculate_harmonic_power_plotspec(...)` 旧 peak-bin helper 残留

### 代码位置

- `python/src/adctoolbox/spectrum/_harmonics.py`

```python
def _calculate_harmonic_power_plotspec(...):
    """THD/HD like MATLAB plotspec: single FFT bin per harmonic, sum for THD."""
```

当前主路径：

```python
compute_spectrum(...) -> _calculate_harmonic_power(...)
```

不再调用 `_calculate_harmonic_power_plotspec(...)`。

### 问题陈述

这个 helper 是 #65 之前的 peak-bin style harmonic power 口径。现在默认 metric convention 已改为
integrated-lobe，但旧 helper 仍保留在同一模块中，且名字里带 `plotspec`，容易造成维护误解：

```text
未来开发者可能误以为 MATLAB plotspec 仍是 single-bin harmonic convention；
或在新增功能时误用旧 helper，重新引入 peak-bin / integrated-lobe 混用。
```

### 影响范围

```text
P3: dead code / maintenance risk。
```

它目前不影响 runtime 指标结果，因为没有被主路径引用。

### 建议修复方向

```text
1. 如果不再需要 legacy helper，删除 `_calculate_harmonic_power_plotspec(...)`。
2. 如果需要保留作为 legacy/reference，改名并加明确注释：
   `_calculate_harmonic_power_peak_bin_legacy(...)`
3. 增加测试或 grep check，确保 compute_spectrum 不再调用 legacy peak-bin helper。
```

### 当前状态

```text
2026-07-01:
  已记录为 low-priority cleanup item。
  尚未修改 upstream 代码。
```

## 2026-07-02: calibration `_post_process` 的 `snr_db` 命名与实际时域 residual ratio 不完全一致

### 代码位置

- `python/src/adctoolbox/calibration/_post_process.py`

```python
err_k = sig_k - dc_offset - ref_k
p_sig = np.mean(ref_k**2)
p_noise = np.mean(err_k**2)
sndr_k = 10 * np.log10(p_sig / p_noise) if p_noise > 0 else 200.0
...
return {
    ...
    'snr_db': snr_list[0] if is_single else snr_list,
    'enob': enob_list[0] if is_single else enob_list,
}
```

### 问题陈述

这里计算的是：

```text
best-fit / reconstructed reference sine power
divided by
time-domain residual error power
```

它不是 `compute_spectrum` 里的 FFT `SNR`：

```text
fundamental lobe power / non-harmonic noise power
```

也不是严格的 FFT `SNDR`：

```text
fundamental lobe power / all in-band non-fundamental power
```

更准确地说，它是 calibration 后处理里的：

```text
time-domain fitted-signal-to-residual ratio
```

如果 harmonic basis 被包含在 calibration fit 中，`ref_k` 还可能包含 harmonic nuisance / fitted reference
成分；这时该 ratio 的含义更接近 residual goodness-of-fit，而不是标准 ADC FFT SNR。

### 影响

```text
P3
```

原因：

```text
这不影响 compute_spectrum 主动态指标；
但返回键叫 `snr_db`，内部变量叫 `sndr_k`，用户容易把它和 spectrum SNR/SNDR 混用。
```

### 建议修复方向

1. 保留数值，但改名或增加别名：

```text
residual_ratio_db
fit_residual_ratio_db
time_domain_sndr_db
```

2. 为兼容旧 API，可暂时保留 `snr_db`，但文档注明：

```text
`snr_db` here is a time-domain fitted-reference / residual ratio,
not the FFT SNR returned by analyze_spectrum.
```

3. 如果要报告标准动态指标，应在 calibrated signal 上显式调用 `analyze_spectrum(...)`。

### 当前状态

```text
2026-07-02:
  已由动态指标一致性审计发现并记录。
  尚未修改 upstream 代码。
```

## 2026-07-02: MATLAB `plotspec.m` 的 `harmonic < 0` 注释与 metric 行为不完全一致

### 代码位置

- `matlab/src/plotspec.m`

```matlab
% Remove harmonics from spectrum for display if harmonic < 0
if(harmonic < 0)
    for i = 2:-harmonic
        b = alias(round((bin_r-1)*i),N_fft);
        spec(max(b+1-sideBin,1):min(b+1+sideBin,Nd2)) = 0;
    end
end
```

该段位于 metric 计算之前，后续 `SNDR` / `SFDR` / `SNR` / `THD` 都继续使用被修改后的 `spec`。

### 问题陈述

注释写的是：

```text
Remove harmonics from spectrum for display
```

但实际行为不是只影响 display。它会直接改变后续指标使用的 spectrum：

```text
SNDR:
  harmonic 被从 noise+distortion spectrum 中提前清零后，SNDR 会变高。

SFDR:
  如果最大 spur 是 harmonic，清零后 SFDR 会变高或换成别的 spur。

SNR:
  后续 noise estimation 基于已修改 spec，也会受到影响。

THD:
  后续 THD 从被清零的 spec 中求 harmonic power，可能被压低。
```

因此 `harmonic < 0` 的真实语义更像：

```text
remove harmonics from analysis spectrum before metrics
```

而不是单纯 “for display”。

### Python 影响

当前 Python `compute_spectrum` / `analyze_spectrum` 没有等价的 `harmonic < 0` 参数，因此主 Python
动态指标不会直接受这个 legacy 行为影响。

但如果目标是 MATLAB/Python 文档语义一致，需要明确：

```text
MATLAB harmonic < 0 是 legacy analysis-modifying behavior；
不是纯 display option。
```

### 严重性

```text
P3
```

原因：

```text
这是 MATLAB legacy 参数语义/注释问题；
不影响 Python 主链路；
但会影响 MATLAB 用户对 SNDR/SFDR/SNR/THD 的解释，尤其在对比 harmonic-included 与 harmonic-removed 分析时。
```

### 建议修复方向

1. 若保持 MATLAB legacy 行为，修改注释和文档：

```text
Remove harmonics from the analysis spectrum and display when harmonic < 0.
```

2. 如果希望 display-only，可复制一份 `spec_plot = spec` 用于画图，不要改 metric 使用的 `spec`。

3. 增加 MATLAB/Python parity note：Python 当前没有 `harmonic < 0` 分析修改模式。

### 当前状态

```text
2026-07-02:
  已由动态指标一致性审计发现并记录。
  尚未修改 upstream 代码。
```

## 2026-06-30: `analyze_error_spectrum` residual 自归一化会弱化 dBFS 工程含义

### 代码位置

- `python/src/adctoolbox/aout/analyze_error_spectrum.py`
  - `error_signal = signal - sig_ideal`
  - `analyze_spectrum(error_signal, fs=fs, show_label=False, max_harmonic=5)`
- `python/src/adctoolbox/spectrum/analyze_spectrum.py`
  - 默认 `max_scale_range=None`
- `python/src/adctoolbox/spectrum/_prepare_fft_input.py`
  - `peak_amplitude = (np.max(data) - np.min(data)) / 2`
  - `data_normalized = data_dc_removed / peak_amplitude`
- `python/src/adctoolbox/examples/04_debug_analog/exp_a22_analyze_error_spectrum.py`
  - 当前 example 对每个 non-ideality 调用 `analyze_error_spectrum(...)`，未显式传 ADC full-scale 标尺。

### 问题陈述

`analyze_error_spectrum` 的当前流程是：

```text
signal -> fit_sine_4param -> fitted_sine
error_signal = signal - fitted_sine
analyze_spectrum(error_signal, max_scale_range=None)
```

因为 `analyze_spectrum` 在 `max_scale_range=None` 时会使用输入数据自己的 peak-to-peak
估计归一化参考，所以这里等价于：

```text
error_dc_removed = error_signal - mean(error_signal)
error_peak       = (max(error_signal) - min(error_signal)) / 2
error_normalized = error_dc_removed / error_peak
```

也就是说，`exp_a22` 中每个 panel 都把该 case 自己的 residual 拉伸到大约 `+-1`
后再做频谱。这种视图适合看 residual 的频率指纹：

```text
宽带噪声？
HD2 / HD3？
AM sideband？
reference spur？
glitch-like broadband floor？
```

但它不适合直接比较不同 case 的真实严重程度，也不适合作为真实 ADC debug 的默认工程标尺。
例如 AM Tone 在 residual-normalized 图里峰值接近图顶，并不表示它接近 ADC full-scale；
只是说明它在自己的 residual 里占主导。

真实测试时通常只有一颗 ADC / 一段 capture / 一个 residual spectrum，而不是像 example 那样
并排比较 15 个已知机制。此时更直观的默认标尺应是 ADC full-scale：

```text
relative to ADC full-scale, in dBFS
```

因为它同时回答：

```text
频率形状是什么；
这个 spur / floor 相对 ADC 满量程到底有多大。
```

### 原理推导

以 AM Tone 为例，当前 example 的模型是：

```text
y(t) = A [1 + m sin(omega_m t)] sin(omega_in t)
```

展开得：

```text
y(t) = A sin(omega_in t)
     + (mA/2) cos((omega_in - omega_m)t)
     - (mA/2) cos((omega_in + omega_m)t)
```

所以 AM tone 会在 `fin +/- fm` 处产生两个确定性边带。当前参数：

```text
A = 0.49
m = 0.05
fm = 500 kHz

sideband amplitude = mA/2 = 0.01225 Vpeak
relative to carrier = 20log10(m/2) ~= -32.04 dBc
```

在 `error_signal` 中，主基波被 `fit_sine_4param` 吸收，剩下的主要就是两个 AM 边带。
如果此时再按 residual 自己的峰值归一化，这些边带自然会接近 residual spectrum 顶部。

### 实验证据

用同一批 `exp_a22` residual 做了两种标尺对照：

```text
left:
  residual-normalized, 即当前默认 max_scale_range=None

right:
  ADC full-scale, 即 max_scale_range=(0, 1)
```

生成图：

```text
E:/ADCToolbox/python/src/adctoolbox/examples/04_debug_analog/output/exp_a22_scale_check.png
```

关键峰值对照：

```text
Case                    residual-normalized peak    ADC full-scale peak
Thermal Noise            -44.84 dB                  -101.18 dBFS
Static HD3               -3.45 dB                   -71.95 dBFS
AM Tone                  -7.80 dB                   -33.99 dBFS
Reference Error          -5.06 dB                   -77.51 dBFS
Glitch                   -53.33 dB                  -73.32 dBFS
```

该实验说明：

```text
当前默认图主要是 shape / fingerprint view；
ADC full-scale 图同时保留频率形状和真实幅度语义；
AM Tone 的高峰主要来自 residual 自归一化，而不是接近 ADC 满量程。
```

### 建议优化方向

不建议简单删除 residual-normalized 视图。它对教学和机制指纹识别仍然有价值。
更合理的优化是把标尺语义显式化：

```python
analyze_error_spectrum(
    signal,
    fs=...,
    max_scale_range=(0, 1),   # ADC full-scale / engineering diagnostic
)

analyze_error_spectrum(
    signal,
    fs=...,
    scale_mode="residual",    # residual-normalized / shape-only view
)
```

或者提供更明确的参数：

```text
scale_mode="adc_fs"       -> 使用 ADC full-scale，推荐真实诊断默认
scale_mode="residual"     -> 使用 residual 自身幅度，只看频率指纹
```

如果担心 full-scale 标尺下小 residual 看不清，应通过以下方式改善可读性，而不是隐式改标尺：

```text
调整 y-axis；
增加 max spur marker；
报告 peak spur dBFS；
报告 residual RMS / pk-pk LSB；
提供 zoom / inset；
在 example 中并排展示 fingerprint view 与 ADC-FS view。
```

### 优先级判断

```text
P2
```

原因：

```text
这不是底层算法 bug；
但它会影响 `analyze_error_spectrum` 作为真实 ADC 诊断工具时的可解释性。
当前默认 residual 自归一化适合看图样，却容易让用户误读不同 case 的误差严重程度。
建议先文档化，再考虑 API 增加显式 scale mode。
```

## 2026-06-30: `exp_a31_fit_static_nonlin` 只给 k2/k3，缺少误差量级判断

### 涉及位置

- `python/src/adctoolbox/examples/04_debug_analog/exp_a31_fit_static_nonlin.py`
  - 当前 example 注入 `k2*x^2 + k3*x^3 + noise`；
  - 调用 `fit_static_nonlin(sig_distorted, order=3)`；
  - 绘制 transfer curve 和 residual curve；
  - 只打印 injected / extracted `k2`、`k3`。
- `python/src/adctoolbox/aout/fit_static_nonlin.py`
  - 先对 distorted waveform 做 sine fit；
  - 再用 `fitted_sine -> sig_distorted` 拟合静态多项式；
  - 返回 `k2_extracted`、`k3_extracted`、`fitted_sine`、`fitted_transfer`。

### 问题描述

`exp_a31` 当前主要回答：

```text
能不能从 distorted sine 里拟合出 k2 / k3？
```

但没有回答更工程的问题：

```text
这些 k2 / k3 到底造成了多大的误差？
这个误差相对 noise、signal、LSB 或 full-scale 是否显著？
为什么 transfer curve 上几乎看不出差异，但 residual 里能看见结构？
```

这会让读者只看到“形状参数”，却缺少“误差量级”。对于 ADC 诊断来说，二者都重要：

```text
k2 / k3:
  说明误差形状和可能机制。

RMS / dBFS / LSB:
  说明误差严重程度和是否超过噪声底。
```

### 原理说明

当前 example 的数据模型是：

```text
x[n] = A sin(omega n)

y[n] = x[n]
     + k2 * x[n]^2
     + k3 * x[n]^3
     + noise[n]
```

`fit_static_nonlin` 先拟合最佳正弦：

```text
fitted_sine[n] ~= best fundamental component of y[n]
residual[n] = y[n] - fitted_sine[n]
```

因此 residual 不是原始 `k2*x^2 + k3*x^3` 的全部，而是去掉 DC / fundamental / gain / phase 后剩下的误差。

对单音输入：

```text
x^2 = A^2 sin^2(omega t)
    = A^2/2 - A^2/2 * cos(2 omega t)

x^3 = A^3 sin^3(omega t)
    = 3A^3/4 * sin(omega t) - A^3/4 * sin(3 omega t)
```

所以：

```text
k2*x^2:
  产生 DC + HD2。
  DC 会被 offset 吸收，post-fit residual 主要剩 HD2。

k3*x^3:
  产生 fundamental + HD3。
  fundamental 会被 sine fit 吸收，post-fit residual 主要剩 HD3。
```

对应的 post-fit distortion RMS 近似为：

```text
HD2 residual RMS ~= |k2| * A^2 / (2*sqrt(2))
HD3 residual RMS ~= |k3| * A^3 / (4*sqrt(2))
```

在当前 example 参数下：

```text
A = 0.5
k2 = 0.01
k3 = 0.01
noise_rms = 500 uVrms
```

理论量级约为：

```text
HD2 residual RMS ~= 0.884 mVrms
HD3 residual RMS ~= 0.221 mVrms
noise RMS        = 0.500 mVrms
```

这解释了一个教学上很重要的现象：

```text
顶部 transfer curve 使用 +-0.5 V 量级，看 mV 级非线性并不敏感；
底部 residual 图直接显示误差，因此更容易看见二次/三次结构；
同样 k=0.01 时，HD2 residual 比 HD3 residual 更大。
```

### 建议补充的 RMS 指标

建议在 `exp_a31` 中补充以下统计：

```text
noise_rms:
  已知注入噪声，当前为 500 uVrms。

measured_residual_rms:
  rms(sig_distorted - fitted_sine)，表示 post-fit 总误差。

expected_hd2_rms:
  |k2_inject| * A^2 / (2*sqrt(2))。

expected_hd3_rms:
  |k3_inject| * A^3 / (4*sqrt(2))。

excess_rms:
  sqrt(max(measured_residual_rms^2 - noise_rms^2, 0))，
  用于粗略估计扣除随机噪声后的确定性误差量级。
```

可选地同时报告：

```text
residual_rms_dBFS:
  20*log10(measured_residual_rms / full_scale_rms_or_peak_convention)

residual_rms_LSB:
  measured_residual_rms / LSB
```

但必须在图注或文档里说明 full-scale / LSB 的定义，否则容易产生新的标尺歧义。

### 需要避免的误用

不要直接对图中的 `nonlinearity_curve = transfer_y - transfer_x` 按均匀横轴取 RMS，并把它解释成动态测试里的误差 RMS。

原因是：

```text
transfer curve 横轴是均匀扫 amplitude；
真实 sine 输入在幅值两端停留时间更长；
二者的样本权重不同。
```

如果要和 spectrum、SNDR、residual 解释一致，RMS 应该优先在真实时间样本上计算：

```text
residual[n] = sig_distorted[n] - fitted_sine[n]
```

### 建议展示方式

每个 panel 的标题或角落 annotation 可以从：

```text
Injected: k2=..., k3=...
Extracted: k2=..., k3=...
```

扩展为：

```text
Injected:  k2=..., k3=...
Extracted: k2=..., k3=...
Residual RMS: ... uVrms
Expected HD2/HD3 RMS: ... / ... uVrms
Noise RMS: ... uVrms
```

console 输出也应同步改成一行可比较的表格：

```text
k2_inj  k3_inj  k2_ext  k3_ext  residual_rms(uV)  expected_hd2(uV)  expected_hd3(uV)  noise_rms(uV)
```

### 优先级判断

```text
P3
```

原因：

```text
这不是底层算法错误；
`fit_static_nonlin` 已经能正确提取 k2/k3 的主要形状信息。
但作为 example / teaching demo，当前输出缺少误差量级，导致读者难以判断：
  - 拟合出来的 k2/k3 是否工程上显著；
  - residual 图里的结构是否已经超过噪声；
  - 为什么 transfer curve 看不出东西。
```

建议先作为 example 可视化和文档增强处理；如果后续 `fit_static_nonlin` API 要返回 diagnostics，
可以把 `rmse`、`residual_rms`、`poly_residual_rms` 等作为可选诊断字段。

## 2026-06-30: `exp_d11_bit_activity` 的 DC offset case 混入 clipping/headroom 问题

### 涉及位置

- `python/src/adctoolbox/examples/05_debug_digital/exp_d11_bit_activity.py`
  - `A = 0.499`
  - `sine = 2 * A * sin(...)`
  - test cases 包含 `sine + 0.01` 和 `sine - 0.01`
  - 同时展示 `analyze_bit_activity(dout)` 和 `analyze_spectrum(dout @ ideal_weights)`
- `python/src/adctoolbox/dout/analyze_bit_activity.py`
  - 该工具本身只是统计每个 bit 为 1 的比例。

### 问题描述

`exp_d11` 名义上想展示：

```text
bit activity 可以检查 bit matrix 是否健康。
```

这对 stuck bit、poor contact、dead bit、输入覆盖不足等问题是合理的。
但当前 `+1% DC Offset` / `-1% DC Offset` case 的教学归因不够干净。

当前输入幅度是：

```text
A = 0.499
sine peak = 2*A = 0.998
```

这已经非常接近 SAR 可表示范围。加上 `+0.01` 或 `-0.01` DC 后：

```text
+1% DC:
  input range ~= [-0.988, +1.008]

-1% DC:
  input range ~= [-1.008, +0.988]
```

因此这两个 case 不是纯粹的“DC offset 导致 bit activity bias”，而是：

```text
near-full-scale sine + DC offset
  -> input headroom 不够
  -> 单边 clipping / overrange
  -> harmonic distortion
  -> ENOB 大幅下降
```

实测量化：

```text
SAR correction span excluding last comparator bit ~= +/-0.999512

ideal:
  input range = [-0.998, +0.998]
  overrange = 0%
  ENOB ~= 12.00 bit
  bit activity ~= 50.0%

+1% DC:
  input range = [-0.988, +1.008]
  positive overrange ~= 4.16% samples
  ENOB ~= 8.95 bit
  bit activity ~= 50.3% - 53.3%

-1% DC:
  input range = [-1.008, +0.988]
  negative overrange ~= 4.16% samples
  ENOB ~= 8.95 bit
  bit activity ~= 46.7% - 49.7%
```

所以 ENOB 的大幅下降主要来自 clipping / headroom，不是 bit activity 偏离 50% 本身。
如果读者只看 example 标题，容易误解为：

```text
1% DC offset -> bit activity 偏一点 -> ENOB 掉 3 bit
```

更准确的因果链应是：

```text
1% DC offset 在 near-full-scale 条件下造成 overrange；
overrange 造成削顶；
削顶造成强 harmonic；
harmonic 造成 SNDR / ENOB 下降。
```

### 这是不是代码库 bug？

```text
不是底层算法 bug。
```

原因：

```text
analyze_bit_activity 只是统计 bit matrix 每列为 1 的比例；
它没有承诺区分 activity bias、input clipping、stuck bit 或测试覆盖不足。
```

问题在于 `exp_d11` 的 case 设计和文档说明：

```text
工具方向是对的；
Poor contact in Bit-11 是很好的 bit-activity demo；
但 +/-1% DC Offset case 实际是 headroom/clipping demo，
不应被当成纯 bit-activity 健康检查案例。
```

### 建议优化方向

建议把 example 拆成三个更清晰的对照：

```text
1. Clean activity-bias case:
   降低幅度，比如 A = 0.45；
   加 +/-1% DC offset；
   确保不过量程；
   用来展示 activity 从 50% 稍微偏移，但不必然造成灾难性 ENOB 下降。

2. Explicit clipping/headroom case:
   保留 A = 0.499 + DC offset；
   但标题明确写成 "DC offset causing clipping" 或 "Headroom violation"；
   同时报告 endpoint-code fraction / overrange fraction。

3. Bit-health case:
   保留 Poor contact / stuck bit；
   这是 analyze_bit_activity 最有代表性的用途。
```

推荐在 example 输出中额外打印：

```text
input min/max；
estimated overrange fraction；
endpoint-code fraction；
bit activity min/max。
```

这样可以把三类现象分开：

```text
bit activity abnormality:
  某列 bit 的 1/0 占比异常。

input headroom / clipping:
  输入越界或端点码堆积。

dynamic performance degradation:
  由 clipping、harmonic、noise、glitch 等导致的 SNDR/ENOB 下降。
```

### 优先级判断

```text
P3
```

原因：

```text
这不是算法错误；
但当前 demo 容易造成教学误解。
建议先在 Stage 11 / notes 中说明该 case 的真实因果链；
后续再考虑改 example，把 no-clipping offset 和 clipping/headroom 分开。
```

## 2026-07-02: `ifilter` 后做 unit-element / thermometer 权重校准会造成病态非物理解

### 涉及位置

- `python/src/adctoolbox/oversampling/ifilter.py`
  - `ifilter(sigin, passband)` 直接调用 `extract_freq_components`。
- `python/src/adctoolbox/spectrum/extract_freq_components.py`
  - `np.fft.fft(din, axis=0)`
  - 构造理想 brickwall frequency mask。
  - `spec = spec * mask[:, np.newaxis]`
  - `np.real(np.fft.ifft(spec, axis=0))`
- `python/src/adctoolbox/calibration/_lstsq_solver.py`
  - 校准权重本质是无约束 least-squares。
  - 当前没有对 unit-element 权重施加非负、平滑、接近 nominal、total-variation 或 ridge/Tikhonov 约束。
- 相关 example：
  - `python/src/adctoolbox/examples/10_oversampling/exp_o02_ifilter_band_analysis.py`
  - 该 example 只展示 `ifilter` 作为频带提取工具，本身没有做权重校准。

### 问题背景

讨论中有一张内部验证图，标题大意为：

```text
64-bit 温度计码字区通过 noise shaping / ifilter 后做权重校准，
unit 权重从近似平坦变成强烈振荡的非物理权重。

NSSAR ifilter + 权重校准：
  基本无发散问题；
  但自由度过高；
  矩阵条件数差；
  非因果滤波导致带外不合理抬升。
```

这里需要把问题说精确：

```text
不是 NTF(z) = (1 - z^-1)^L 本身在 Nyquist 后无界发散；
也不是 ifilter 单独会放大信号；
而是：把 ifilter 处理后的 thermometer / unit-element code matrix
拿去做无约束权重最小二乘，会形成病态逆问题。
```

`ifilter` 在本库中是理想 FFT brickwall filter：

```text
FFT -> 频域 mask -> IFFT
```

它是离线、全记录、非因果滤波器。作为频带提取工具是合理的；但它会改变每一列 code
column 的频谱内容。如果对 64 个 thermometer/unit columns 分别滤波，再用滤波后的矩阵
去拟合 unit weights，就等价于：

```text
只要求这些权重在指定带内拟合训练目标；
带外行为不被训练目标约束；
列与列之间在带内更难区分；
最小二乘可以利用近似 null-space 生成大幅正负振荡权重。
```

### 数学解释

设原始 unit-element code matrix 为：

```text
B_raw, shape = (N samples, 64 units)
```

理想 unit 权重应近似平坦、非负：

```text
w_unit ~= constant > 0
```

若先对每列做带内 `ifilter`，得到：

```text
B_filt = ifilter(B_raw, passband)
```

再做：

```text
min_w || B_filt @ w - y_inband ||_2
```

此时最小二乘只关心带内误差。若 `B_filt` 的列相关性很强，则存在很多近似 null-space 方向：

```text
B_filt @ delta_w ~= 0
```

这些方向几乎不改变带内训练误差，却可以让权重变成：

```text
w + delta_w
```

并出现：

```text
正负交替；
大幅振荡；
unit 权重为负；
total variation 极大；
用于未滤波 raw bits 时产生非物理带外/时域行为。
```

所以问题本质是：

```text
ifilter 后的训练目标只约束带内；
无约束 least-squares 没有物理先验；
病态矩阵把不可观测自由度转化成非物理权重。
```

### 复核实验

用一个合成 64 列 thermometer code matrix 做复核：

```text
N = 8192
M = 64 unit columns
OSR = 32
输入为单音正弦驱动的 thermometer code
对每列做 centered，然后比较 raw matrix 与 in-band ifilter matrix
```

结果：

```text
raw centered thermometer:
  rank(1e-12) = 58
  cond_eff    ~= 5.29e1

ifiltered in-band thermometer:
  rank(1e-12) = 58
  cond_eff    ~= 4.19e4
```

`ifilter` 没有显著改变有效 rank，但把最小有效奇异值压得很小，条件数恶化接近 800 倍。

同一目标下做无约束 least-squares，权重形态变为：

```text
raw fit:
  weight std       ~= 1.0e-2
  weight min/max   ~= 0 ~ 3.6e-2
  total variation  ~= 8.1e-2

ifilter fit:
  weight std       ~= 2.0e-1
  weight min/max   ~= -0.83 ~ 0.64
  total variation  ~= 9.6
```

这复现了“unit 权重从近似平坦变成强烈振荡、甚至负权重”的现象。

另一个复核点：

```text
ifilter-trained weights 用在 ifiltered matrix 上：
  训练带内误差很小。

ifilter-trained weights 用回 unfiltered raw bits：
  权重的带外/时域行为不受约束，可能出现非物理振荡和异常 spur。
```

这就是典型的训练目标过窄 + 病态逆问题，而不是物理 unit 权重被真实校准出来。

### 这是不是代码库 bug？

判断：

```text
不是 `ifilter` 单独的 bug。
不是 `calibrate_weight_sine` 单独的 bug。
但如果库或示例把 `ifilter(B)` 后的 code matrix 直接用于物理 unit 权重校准，
这是一个真实且严肃的 workflow 风险。
```

原因：

```text
ifilter:
  作为离线频带提取工具合理。

least-squares weight calibration:
  作为一般线性拟合工具合理。

组合问题:
  对 unit-element / thermometer 权重，物理先验非常强；
  无约束 LS 没有这些先验；
  ifilter 又只保留带内信息；
  组合后容易得到数学上拟合好、物理上荒谬的权重。
```

### 建议优化方向

如果未来要支持 “NSSAR / noise-shaping SAR / thermometer unit-element ifilter + 权重校准”
这类 workflow，应增加显式诊断和约束。

建议至少增加诊断：

```text
1. report rank / singular values / condition number:
   cond(B_raw), cond(B_filt), singular value spectrum。

2. report weight physicality:
   min(weight), max(weight), negative_weight_fraction,
   std(weight), total_variation(weight), max_abs_jump。

3. compare train vs validation:
   fit on ifiltered training target；
   apply weights to unfiltered raw bits；
   evaluate independent frequency/amplitude/phase capture。

4. compare raw-fit vs ifilter-fit weights:
   ||w_raw - w_ifilter||；
   TV(w_raw) vs TV(w_ifilter)；
   reconstructed spectrum before/after。
```

建议增加可选约束 / 正则：

```text
ridge / Tikhonov:
  min ||B_filt w - y||^2 + lambda ||w - w_nom||^2

smoothness / total variation:
  min ||B_filt w - y||^2 + lambda ||D w||^2

non-negative least squares:
  w_i >= 0

bounded unit variation:
  |w_i - w_nom_i| <= tolerance

monotonic / segmented prior:
  对 thermometer / unit array 使用更接近物理 layout 的约束。
```

对于教学示例，应明确写：

```text
ifilter 适合做频带提取和 in-band 性能分析；
不应默认把 ifilter 后的 code matrix 当成物理 unit 权重校准输入；
如果这么做，必须报告 conditioning 和 weight physicality。
```

### 优先级判断

```text
P2
```

原因：

```text
这不是普通可视化瑕疵；
如果用户把该 workflow 用于真实 NSSAR / thermometer unit-element calibration，
可能得到训练指标看似改善、但权重明显非物理且不可泛化的结果。
```

但当前库公开 example 中 `exp_o02_ifilter_band_analysis.py` 只展示 ifilter 频带提取，
并未直接宣称 ifilter 后可用于物理 unit 权重校准。因此优先级低于会直接崩溃或错误输出的
API bug，但高于纯文档表达优化。
