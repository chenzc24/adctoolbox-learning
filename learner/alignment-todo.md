# ADCToolbox MATLAB/Python 对齐闭环记录

本文件记录 ADCToolbox 中 MATLAB 与 Python 对齐过程里的待办、审查结论、PR 顺序和最终状态。
截至 2026-07-09，本文件曾跟踪的 notable alignment / contract 问题已在 upstream PR 中闭环。
后续若发现新的对齐问题，可以继续追加；旧的 TODO 段落保留为历史推理轨迹，不再代表当前待办。

## 最终闭环状态：2026-07-09

当前 GitHub 状态：

```text
Open PRs:    none
Open issues: none
```

已解决的主线对齐项：

```text
#76  plotspec / analyze_spectrum integrated-lobe metric parity
#79  calibration output scale contract
#80  spectrum overrange warning
#84  harmonic-order calibration residual semantics
#85  wcalsin fixed-frequency parity
#86  wcalsin automatic frequency refinement
#87  frequency and radix contracts
#88  ovfchk / check_overflow parity fixture isolation
#89  ENOB sweep mode split
#90  errevspec / analyze_error_envelope_spectrum residual input contract
#91  sinfit / fit_sine_4param comparison fixture policy
#92  ntfperf integration grid policy
#93  plotphase LMS comparison fixture
#94  errsin MATLAB-compatible legacy wrapper contract
#95  cdacwgt / convert_cap_to_weight order contract
#97  ENOB sweep default restored to full-bit calibration semantics
```

当前结论：

```text
1. 已记录的核心数值 / input-output contract / compare fixture 对齐问题均已处理。
2. `adcpanel` / dashboard 仍是 workflow/UI 组织差异，不作为数值 parity bug。
3. `plotspec` 等核心算法可继续补边缘 regression tests，但这属于 hardening，不是已知 mismatch。
4. 最重要的方法论修正来自 #97：不要盲目把当前 MATLAB 行为当作真值；
   若 MATLAB 当前实现与作者定义的实验问题不一致，应修 MATLAB，并让 Python 跟随正确 contract。
```

## 条目：`calibrate_weight_sine` scale contract 修复

日期：2026-07-03  
状态：`RESOLVED / HISTORICAL`

当前说明：

```text
本条已由 #79 / #80 / #87 等 PR 落地：
scale_convention、scale_calibration_output、max_scale_range / overrange warning、
以及 bundled skill 文档均已同步。下面的计划任务保留为历史草案，不再是当前 TODO。
```

### 背景

当前问题不是 `calibrate_weight_sine` / `wcalsin` 求解器的数值算法错误，而是输出尺度契约不够明确：

```text
calibrate_weight_sine / wcalsin 输出的是 solver-unit-sine scale；
它不是自动映射到 ADC voltage/code full-scale scale 的物理量。
```

求解器为了让权重问题可辨识，会把参考 fundamental 固定为单位正弦。这个 gauge fixing 在数学上合理，也符合原作者意图；但如果用户把 `calibrated_signal` 直接送入 `analyze_spectrum` / `plotspec` 并解读 dBFS、NSD，就可能得到物理尺度错误但看起来合理的结果。

### 已确认原则

- 不改 `calibrate_weight_sine` / `wcalsin` 的默认数值输出。
- 默认输出继续保持 solver scale，避免破坏兼容性。
- 新增 metadata，明确 `scale_convention = "solver_unit_sine"`。
- 新增显式 helper，将 solver scale 映射到调用者指定的 ADC/code/full-scale convention。
- 不写成“权重按 `1/A` 缩放”；实际比例取决于 bit encoding、nominal weights、ADC convention。
- `max_scale_range=None` 是 self-referenced dBFS，对 solver-scale `calibrated_signal` 不代表物理 ADC full-scale。

### 计划任务

#### 1. Python metadata

代码位置：

```text
python/src/adctoolbox/calibration/_post_process.py
python/src/adctoolbox/calibration/calibrate_weight_sine.py
```

TODO：

- [ ] 在返回 dict 中加入 `scale_convention = "solver_unit_sine"`。
- [ ] 加入简短 `scale_note` 或等价字段，说明 `weight` / `calibrated_signal` 不保证是 ADC voltage/code FS 单位。
- [ ] 更新 `calibrate_weight_sine` docstring。

#### 2. Python scale helper

建议代码位置：

```text
python/src/adctoolbox/calibration/_scale_calibration_output.py
```

候选 API：

```python
scale_calibration_output(
    result,
    *,
    target_weights=None,
    target_span=None,
    method="span",
    inplace=False,
)
```

核心公式：

```text
scale = target_span / sum(result["weight"])
```

其中 `target_span` 可以来自：

```text
target_span = sum(target_weights)
```

TODO：

- [ ] 缩放 `weight`、`offset`、`calibrated_signal`、`ideal`、`error`。
- [ ] 不缩放 `snr_db`、`enob`、`refined_frequency`。
- [ ] 支持 single-dataset 和 multi-dataset 返回结构。
- [ ] 处理 `sum(weight) == 0`、非有限值、缺字段等错误。
- [ ] 返回 `scale_factor` 与新的 `scale_convention`，例如 `adc_reference_scale`。

文档必须说明：

```text
sum(weight) 是全码/权重 span 锚点，不是 raw waveform peak；
helper 让 ideal reference sine 映射到目标 ADC/code convention；
calibrated_signal 含 DC offset 和残差，raw peak 不一定等于 target span；
spectrum analyzer 会去 DC，dBFS 应在一致 max_scale_range 下解释。
```

#### 3. Examples 统一尺度

重点检查：

```text
python/src/adctoolbox/examples/05_debug_digital/exp_d02_cal_weight_sine.py
python/src/adctoolbox/examples/05_debug_digital/exp_d03_redundancy_comparison.py
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

TODO：

- [ ] 不只修 `analog_after`；确保 before / after 使用同一套 ADC/code/full-scale convention。
- [ ] 如果 before 已经是 nominal voltage scale，则 after 使用 helper 映射到同一 `target_weights`。
- [ ] 如果示例只比较 SNDR/SFDR 比值，可保留 self-referenced 分析，但必须避免解读绝对 dBFS / NSD。
- [ ] 替换或解释现有手写 `/2` scale bridge，避免用户误以为 `/2` 是通用规则。

#### 4. `analyze_spectrum` / `_prepare_fft_input` overrange warning

代码位置：

```text
python/src/adctoolbox/spectrum/_prepare_fft_input.py
```

TODO：

- [ ] `max_scale_range=None`：不 warning，因为没有外部 FS 参考。
- [ ] tuple/list `[min, max]`：在 DC removal 前检查 raw data 是否超出声明范围。
- [ ] scalar peak：在 DC removal 后检查 centered peak 是否超出声明 peak。
- [ ] warning 不改变数据，不 clamp。
- [ ] 文档说明 tuple 与 scalar 检查的物理含义不同：

```text
tuple raw check 能抓 DC offset + input swing 导致的实际输入越界；
scalar centered check 只关心交流峰值是否超过声明 peak。
```

#### 5. 文档和 bundled skill

需要更新：

```text
python/docs/source/algorithms/calibrate_weight_sine.md
python/docs/source/algorithms/calibrate_weight_sine_lite.md
python/src/adctoolbox/_bundled_skills/skills/adctoolbox-user-guide/SKILL.md
python/src/adctoolbox/_bundled_skills/skills/adctoolbox-user-guide/references/api-quickref.md
```

TODO：

- [ ] 明确 solver scale 与 ADC full-scale scale 的区别。
- [ ] 强调 `max_scale_range=None` 是 self-referenced dBFS。
- [ ] 给出 helper 用法示例。
- [ ] 不把 `A` 或 `1/A` 写成通用换算公式。

#### 6. MATLAB 同步

代码/文档位置：

```text
matlab/src/wcalsin.m
matlab/README.md
matlab/README.zh-CN.md
```

TODO：

- [ ] 在 `wcalsin` output 注释中说明 `weight/postcal/ideal` 是 solver-unit-sine scale。
- [ ] README 中说明接 `plotspec` 解释 dBFS 前需要显式映射到 ADC/code convention。
- [ ] 暂不改 MATLAB 默认数值。
- [ ] 是否新增 MATLAB helper 待讨论。

### 测试计划

Python 单测：

- [ ] `calibrate_weight_sine` 返回 `scale_convention == "solver_unit_sine"`。
- [ ] helper 缩放后 `sum(weight)` 匹配 `sum(target_weights)` 或 `target_span`。
- [ ] helper 缩放后 `snr_db`、`enob`、`refined_frequency` 不变。
- [ ] SAR 复现实验：helper 后 `sig_pwr_dbfs` 回到理论值。
- [ ] overrange warning：正常信号不误触发。
- [ ] overrange warning：tuple raw overrange 与 scalar centered overrange 分别覆盖。

建议验证命令：

```powershell
cd E:/ADCToolbox/python
uv run --with pytest pytest tests/unit/calibration -q
uv run --with pytest pytest tests/unit/spectrum -q
uv run --with pytest pytest tests/integration/test_user_guide_skill_examples.py -q
uv run python ../matlab/tests/run_matlab_tests.py dout --missing-ok
```

### 待讨论问题

- [ ] helper 名称：`scale_calibration_output`、`normalize_calibration_output`、还是 `calibration_to_adc_scale`？
- [ ] helper 是否从 `adctoolbox.calibration` 和顶层 `adctoolbox` 同时 export？
- [ ] `target_weights` 默认是否允许使用 `result` 里的 `nominal_weights`？当前结果并不保存 `nominal_weights`，若要支持需要新增 metadata。
- [ ] `scale_factor` 对 multi-dataset 是否应只有一个，因为共享 weights；还是允许 per-dataset signal scale？
- [ ] 是否应提供 `target_range=(-0.5, 0.5)` 这种电压式接口，自动推导 `target_span`？
- [ ] MATLAB 是否只补文档，还是也做等价 helper？
- [ ] overrange warning 的阈值是否需要容差，例如 `1 + 1e-12`，避免浮点边界误报？

### 暂定 PR 标题

```text
Clarify calibration output scale and add ADC-scale normalization helper
```

## 追加记录：`plotspec` 对齐后的下一步计划

日期：2026-07-03  
状态：`待 #76 合并后执行`

背景：

- PR #76 已从 `main` 分支创建，主题是让 Python spectrum low-bin masking、`run_plotspec` reference 和 compare 测试重新对齐当前 MATLAB `plotspec.m`。
- 该 PR 不包含 `learning/` 内容，也不应混入 calibration-scale 主题。
- 后续工作应在 #76 合并后，从最新 `main` 新开分支，避免把主仓修复、边缘测试、学习记录更新搅在同一个 PR 里。

建议顺序：

1. 等待 #76 CI 和 review。
2. 若 #76 失败，只修与 `plotspec` compare / reference / low-bin masking 直接相关的问题。
3. #76 合并后，从最新 `main` 新开分支，例如：

```text
codex/plotspec-edge-regression
```

4. 在新分支中补 `plotspec/analyze_spectrum` 边缘回归测试，优先覆盖：

- [ ] `side_bin = 0 / 1 / 3` 时，Python 低频清零是否等价 MATLAB `spec(1:sideBin)=0`。
- [ ] spur 位于 bin 1 附近时，SFDR 是否仍按当前 MATLAB 语义处理。
- [ ] harmonic alias 到 DC 附近时，THD / SNR 的处理是否一致。
- [ ] harmonic alias 接近 fundamental lobe 时，是否避免重复计数或误删。
- [ ] `OSR > 1`、Nyquist bin、band-edge bin 的 `n_inband` 边界是否稳定。

5. 如果边缘测试没有暴露算法偏差，只提交测试，不改算法。
6. 如果测试暴露真实偏差，先记录最小复现，再单独讨论是否修 Python 或 MATLAB。
7. 等主仓边缘测试 PR 稳定后，再单独更新 learning 文档，例如：

```text
learner/inconsistency.md
```

记录方向：

```text
plotspec/analyze_spectrum 的主要不一致已从“当前算法偏差”改判为
“历史 reference / skip reason 与当前实现不同步”。

#76 已恢复 run_plotspec compare，并将 noi 更新为当前 noise_floor_dbfs 语义。
后续剩余风险转入边缘测试覆盖，而不是继续扩大当前 PR。
```

## 追加记录：`ovfchk` / `check_overflow` 对齐审查

日期：2026-07-04  
状态：`已审查 / 待决定是否修测试或提 issue`

### 审查结论

`overflowChk` / `ovfchk` 对应当前 MATLAB 主函数 `bitchk`，Python 侧对应
`check_overflow` / `analyze_overflow`。当前审查结论是：**overflow 检测算法本身已经对齐**，
现有 compare 差异主要来自测试链路把两边放在了不同的 weight calibration 条件下。

### 已核实的算法等价关系

MATLAB `bitchk.m` 对每个 bit position 执行：

```matlab
tmp = bits(:,ii:end) * wgt(ii:end)';
data_decom(:,ii) = tmp / sum(wgt(ii:end));
range_min(ii) = min(tmp) / sum(wgt(ii:end));
range_max(ii) = max(tmp) / sum(wgt(ii:end));
ovf_percent_zero(ii) = sum(data_decom(:,ii) <= 0) / N * 100;
ovf_percent_one(ii) = sum(data_decom(:,ii) >= 1) / N * 100;
```

Python `analyze_overflow.py` 执行的是同一语义：

```python
tmp = raw_code[:, ii:] @ weight[ii:]
sum_weight = np.sum(weight[ii:])
data_decom[:, ii] = tmp / sum_weight
range_min[ii] = np.min(tmp) / sum_weight
range_max[ii] = np.max(tmp) / sum_weight
ovf_percent_zero[ii] = np.sum(data_decom[:, ii] <= 0) / N * 100
ovf_percent_one[ii] = np.sum(data_decom[:, ii] >= 1) / N * 100
```

因此这不是“Python overflow 公式偏离 MATLAB”的问题。

### 真实偏差来源

MATLAB compare reference 的入口 `matlab/tests/dout/run_ovfchk.m` 使用：

```matlab
[weights_cal, ~, ~, ~, ~, ~] = wcalsin(read_data);
```

即 `wcalsin` 默认设置。当前 MATLAB `wcalsin` 的 `order` 默认值是 `1`。

Python 对应测试 `python/tests/integration/test_overflow_chk.py` 使用：

```python
weight, _, _, _, _, _ = calibrate_weight_sine(
    raw_data,
    freq=0,
    order=5,
)
```

这意味着 compare 实际混入了 calibration 参数差异：MATLAB reference 是默认 1 阶校准，
Python 输出是固定 5 阶校准。`check_overflow` 接收的 weight 已经不同，后续
`range_min` / `range_max` / overflow percentage 自然可能不同。

### 数值现象

使用 `reference_dataset/dout_SAR_12b_weight_2.csv` 对比当前 MATLAB reference：

```text
配置                       range_min diff    range_max diff    ovf_zero diff    ovf_one diff
Python 默认校准             1.33e-7           1.33e-7           0                0
Python freq=0, order=5       2.3235e-4        2.3235e-4        0                0.732421875
```

其中 `ovf_percent_one` 的跳变来自硬阈值：

```text
data_decom >= 1
```

当某个 residue segment 的 `range_max` 贴近 1 时，weight 的极小变化就可能让样本从
`>= 1` 变成 `< 1`，百分比会离散跳变。因此这个测试对上游 calibration 微小差异非常敏感，
不适合作为单纯的 overflow 算法 parity test。

### 低风险修正方向

优先不改 `analyze_overflow` / `bitchk` 算法。

建议把问题拆成两层：

1. **overflow parity test**：使用固定 weight 或 MATLAB reference weight，直接验证
   `bitchk` 与 `check_overflow` 的四个返回数组。
2. **calibration + overflow integration test**：若保留自动校准链路，需要显式说明
   `wcalsin` / `calibrate_weight_sine` 的参数一致性，并接受 threshold-sensitive 指标的边界风险。

最小修法可以是：如果 `test_ovfchk` 的意图是匹配当前 MATLAB reference，则 Python
`test_overflow_chk.py` 应先改回默认 `calibrate_weight_sine(raw_data)`；如果意图是比较
`order=5` pipeline，则 MATLAB `run_ovfchk.m` 也要传入 `'freq', 0, 'order', 5`，并重新生成
reference，但这会把 compare 继续绑定到 calibration 差异上。

### 暂定判断

这个条目应归类为：

```text
测试基座不一致 / compare harness mismatch
```

而不是：

```text
overflow algorithm mismatch
```

后续若向 upstream 提 issue，标题可以聚焦为：

```text
Isolate ovfchk/check_overflow parity from calibration order differences
```

## 追加记录：2026-07-08/09 对齐队列状态刷新

状态：`CLOSED / MERGED / 仅保留历史队列`

### 总原则

按作者处理 #87 一类问题的风格，后续对齐不应先假定“谁错”，而应先分类：

```text
核心算法差异？
默认 policy 差异？
output/input contract 差异？
compare fixture 差异？
```

处理原则：

- 能保留现有清晰 API 的，优先保留，并通过显式 mode / policy 支持 MATLAB parity。
- 如果旧默认回答的问题与函数名或行业常用语义不一致，可以在有实验证据和文档说明的前提下调整默认。
- 如果已有 reference/API 已形成稳定契约，另一端应显式跟随该契约，而不是混入隐含转换。
- 每个问题单独小 PR，用测试锁住，不把算法、fixture、文档迁移混成一个大 PR。
- 学习记录只同步结论，不混入主仓 PR。

### 当前已处理

1. `calibrate_weight_sine` scale contract
   - 状态：已解决。
   - 相关内容已在 #79 / #80 / #87 等 PR 中落地：`scale_convention`、`scale_calibration_output`、`max_scale_range` overrange warning、bundled skill 文档。
   - 本文件早期 “scale contract TODO” 作为历史计划保留，但不再作为当前下一个 PR。

2. `ovfchk` / `check_overflow`
   - 状态：#88 已合并。
   - 性质：compare fixture mismatch，不是 overflow 核心算法差异。
   - 原则：不改 `check_overflow` / `bitchk` 算法；用固定 weight 或统一 calibration 参数隔离 parity。

3. `bitsweep` / `analyze_enob_sweep`
   - 状态：#89 已合并，随后 #97 已修正默认语义并关闭 #96。
   - 最终性质：两个 sweep 都有数学意义，但 canonical ENOB sweep 应是“全 bit 校准一次，再评估 full-weight prefix”。
   - `prefix_of_full_calibration` 是默认 / canonical 行为。
   - `recalibrate_each_subset` 保留为 diagnostic：回答“每个 n-bit prefix 若作为独立 ADC 重新校准，性能如何？”
   - 方法论教训：当前 MATLAB 行为不是绝对真值；若 MATLAB 实现与作者定义的实验问题不一致，应修 MATLAB。

4. `plotspec` / `analyze_spectrum`
   - 状态：主对齐已完成；后续只剩边缘测试补强。
   - 不再作为当前主线 alignment TODO。

5. `errevspec` / `analyze_error_envelope_spectrum`
   - 状态：#90 已合并。
   - 已通过 `input_kind="signal" | "error"` 拆开 signal-input convenience 与 MATLAB residual-input parity。

6. `cdacwgt` / `convert_cap_to_weight`
   - 状态：#95 已合并。
   - 已通过 `input_order` / `output_order` 显式化 MATLAB `cdacwgt` 与 legacy `cap2weight` 的顺序约定。

7. `sinfit` / `fit_sine_4param`
   - 状态：#91 已合并。
   - compare fixture 显式使用 MATLAB-compatible refinement policy；默认 API 的 lightweight fit behavior 保留。

8. `ntfperf`
   - 状态：#92 已合并。
   - MATLAB grid policy 已显式暴露，compare 固定同一 grid。

9. `plotphase`
   - 状态：#93 已合并。
   - LMS compare fixture 已对齐；FFT/LMS API 组织差异作为文档化 workflow 差异保留。

10. `errsin`
    - 状态：#94 已合并。
    - `plot_error_hist_phase/code` legacy wrappers 现在承担 MATLAB `errsin` compatibility；
      redesigned `analyze_error_by_phase/value` API 保持独立诊断语义。

11. `adcpanel` / dashboards
    - 状态：不作为数值 parity bug。
    - MATLAB 是统一面板入口，Python 是拆分 dashboard / toolset；后续只需要 migration note 或 wrapper，而非强制一比一布局。

### 剩余事项

```text
无 active alignment PR / issue。
可选后续工作：
1. 清理 learning 文档中的历史 TODO 表述；
2. 为 plotspec / spectrum collision / dashboard migration 补更多说明或 regression tests；
3. 在 release note 中总结 MATLAB/Python contract 对齐原则。
```

## 追加记录：`errevspec` / `analyze_error_envelope_spectrum` 下一步 PR 计划

日期：2026-07-08  
状态：`RESOLVED / MERGED (#90)`

当前说明：

```text
本计划已由 #90 落地。`analyze_error_envelope_spectrum` 已支持 residual/error input contract，
compare fixture 使用 error-input path，不再把 residual 二次 fit。下面保留原计划作为历史设计记录。
```

### 问题性质

这不是 Hilbert envelope 或 spectrum 核心算法差异，而是**输入对象 contract 差异**。

MATLAB reference 路径：

```matlab
err_data = read_data - sinfit(read_data);
[ENoB, SNDR, SFDR, SNR, THD, pwr, NF, ~] = errevspec(err_data, 'Fs', 1);
```

也就是说，`errevspec` 接收的是已经计算好的 error / residual。

Python 当前核心函数：

```python
analyze_error_envelope_spectrum(signal, ...)
```

内部执行：

```python
fit_result = fit_sine_4param(signal, ...)
error_signal = signal - fit_result["fitted_signal"]
env = abs(hilbert(error_signal))
```

如果 compare integration 先算 `err_data`，再调用当前 `plot_envelope_spectrum(err_data, fs=1)`，
就会把 residual 当成 signal，再次拟合 sine 并生成新的 residual。这不是 MATLAB `errevspec`
的输入语义。

### 修改原则

- 不改 Hilbert envelope 算法。
- 不删除当前 signal-input convenience 行为。
- 显式区分：

```text
input_kind="signal"  -> 当前行为：signal -> fit sine -> residual -> envelope
input_kind="error"   -> MATLAB parity：error/residual -> envelope
```

- MATLAB parity / compare 测试使用 `input_kind="error"`。
- 文档说明：不要把 residual 再传入 signal-input 路径。

### 代码定位

Python：

```text
python/src/adctoolbox/aout/analyze_error_envelope_spectrum.py
python/src/adctoolbox/aout/__init__.py
python/tests/integration/test_err_envelope_spectrum.py
python/tests/compare/test_compare_err_envelope_spectrum.py
python/tests/unit/aout/test_analyze_error_envelope_spectrum.py
```

MATLAB reference：

```text
matlab/src/dumped/errevspec.m
matlab/tests/aout/run_errevspec.m
```

### 预期修改

1. 在 `analyze_error_envelope_spectrum` 增加参数：

```python
input_kind: str = "signal"
```

允许值：

```text
"signal"
"error"
```

2. `input_kind="signal"`：
   - 保持当前默认行为。
   - 返回 `error_signal`、`envelope`，可选 `fit`。

3. `input_kind="error"`：
   - 跳过 `fit_sine_4param`。
   - 直接把输入 flatten 为 `error_signal`。
   - `return_fit=True` 时不生成 fit diagnostics，或返回 `fit=None` / 明确 metadata。
   - 增加 result metadata，例如：

```python
result["input_kind"] = input_kind
```

4. integration compare：
   - 保留先算 `err_data = raw_data - fit_sine(raw_data)` 的结构。
   - 调用：

```python
plot_envelope_spectrum(err_data, fs=1, input_kind="error")
```

5. compare test：
   - 去掉 skip。
   - 若数值仍有差异，再判断是 `sinfit` residual 差异、spectrum reference 差异，还是 envelope path 本身差异。

### 测试计划

- 单测：
  - `input_kind="error"` 不调用 `fit_sine_4param`，直接分析输入 residual。
  - `input_kind="signal"` 保持旧行为。
  - 非法 `input_kind` 抛 `ValueError`。
- integration：
  - `tests/integration/test_err_envelope_spectrum.py`
- compare：
  - `tests/compare/test_compare_err_envelope_spectrum.py`

### 暂定 PR 标题

```text
Add error-input mode for envelope spectrum parity
```
