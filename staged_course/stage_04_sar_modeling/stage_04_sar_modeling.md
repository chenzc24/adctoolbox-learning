# Stage 04：SAR ADC 行为建模

## 本阶段目标

学完本阶段，你应该能解释：

- SAR ADC 的逐次逼近过程。
- CDAC weights 如何决定 bit decision。
- nominal weights 和 actual weights 的区别。
- capacitor mismatch 如何造成非线性和 spur。
- sampling noise 和 comparator noise 在模型中如何进入。
- 本库 `sar_convert` 和 `sar_reconstruct` 的数据流。

## 初学者先抓住的主线

SAR ADC 的行为可以先想成一个“二分试探”过程：

```text
先试 MSB：输入有没有超过 1/2 full-scale？
再试下一位：在已有判断基础上，再加 1/4 full-scale 试一下。
继续往下，直到 LSB。
```

每一位只做一件事：

```text
临时把当前 weight 加到 DAC 输出上
比较 vin 和 v_test
如果 vin 更大，这一位保留为 1
否则这一位为 0
```

所以 SAR 模型里最重要的三个对象是：

```text
vin       -> 要转换的输入
weights   -> CDAC 每一位能产生多大的 DAC step
bits      -> 每一步比较器留下的 0/1 决策
```

先把这个过程看懂，再看 mismatch、noise、redundancy。

## 手算一个 4-bit 例子

理想 4-bit 权重：

```text
[0.5, 0.25, 0.125, 0.0625]
```

假设：

```text
vin = 0.70
```

逐次逼近：

| bit | weight | v_test | decision | v_dac |
|---|---:|---:|---:|---:|
| MSB | 0.5 | 0.5 | 1 | 0.5 |
| bit1 | 0.25 | 0.75 | 0 | 0.5 |
| bit2 | 0.125 | 0.625 | 1 | 0.625 |
| bit3 | 0.0625 | 0.6875 | 1 | 0.6875 |

得到：

```text
bits = [1, 0, 1, 1]
aout = 0.6875
residue = vin - aout = 0.0125
```

这个表就是 `sar_convert` 的核心逻辑。

## 数学需要补什么

### 1. 逐次逼近是贪心搜索——为什么它能收敛

SAR ADC 想用一组二进制权重近似输入：

```text
vin ≈ b0·w0 + b1·w1 + ... + b(N-1)·w(N-1)

其中 bi ∈ {0, 1}
理想权重: w = [1/2, 1/4, 1/8, ..., 1/2^N]
```

逐次逼近过程（贪心搜索）：

```text
v_dac = 0
for each bit j (从 MSB 到 LSB):
    v_test = v_dac + w[j]
    if vin >= v_test:
        bit[j] = 1
        v_dac = v_test          ← 接受这一位
    else:
        bit[j] = 0
              ← 拒绝，v_dac 不变
```

这个算法的直觉是"从大到小贪心"——先试最大的 weight，能接受就接受，不能就跳过。
为什么这样的贪心策略能保证收敛到最优近似？关键在二进制权重的**超增性**。

#### 1.1 贪心收敛的数学证明

**定理**：对理想二进制权重 `w[j] = 1/2^(j+1)` + 1 LSB 归一化（见 § 2），逐次逼近
保证最终残差 `r = vin - v_dac_final` 满足 `0 ≤ r < 1 LSB`。

**关键性质：权重是超增的（superincreasing）**

```text
每个 w[j] > 剩余位总和 S[j+1] = w[j+1] + w[j+2] + ...

因为 S[j+1] = w[j+1]·(1 + 1/2 + 1/4 + ...) = 2·w[j+1] - w[N-1]
           = w[j] - w[N-1]
           < w[j]
```

超增性的意义：**当前位的权重比"后面所有位加起来"还大**。所以"先取大的"永远
不会后悔——如果当前位不取，后面所有位加起来也补不到这个量。

**证明**（用剩余权重总和做归纳）：

定义 `r[j]` 为处理完 bit j 后的残差，`S[j+1]` 为 bit j 之后所有位的权重和。

```text
断言: 0 ≤ r[j] ≤ S[j+1]    （残差不超过剩余位能表示的范围）

归纳基础 j=0 (MSB):
  w[0] = 1/2, S[1] = 1/4 + 1/8 + ... = 1/2 - 1/2^N
  - 若 vin ≥ 1/2: 取 MSB, r[0] = vin - 1/2 ∈ [0, 1/2)
                  而 S[1] = 1/2 - LSB, 所以 r[0] < 1/2 但可能 > S[1]
                  -> 需要 1 LSB 的"溢出空间"（这就是归一化 +1 LSB 的原因，见 § 2）
  - 若 vin < 1/2: 不取, r[0] = vin ∈ [0, 1/2)
                  < w[0] = 1/2，也 ≤ S[1] + LSB ✓

归纳步骤:  bit j 取走 w[j] 当且仅当 r[j-1] ≥ w[j]
  - 取:  r[j] = r[j-1] - w[j]。因为 r[j-1] ≤ S[j] = w[j] + S[j+1]
         所以 r[j] ≤ S[j+1] ✓
  - 不取: r[j] = r[j-1] < w[j]。因为 w[j] > S[j+1]（超增）
         所以 r[j] < w[j]，落在剩余位能表示的范围 ✓
```

处理完 LSB（bit N-1）后，`S[N] = 0`，残差 `r ∈ [0, 1 LSB)`（1 LSB 是归一化留出的
溢出空间）。证毕。

#### 1.2 贪心的最优性

超增性还保证了贪心给出的是**唯一最优**的 N-bit 近似——每一步的决策由 vin 唯一
确定，没有选择余地。如果权重不是超增的（比如 § 数学 6 的 redundancy 用非二进制
权重），贪心可能不是最优，需要更复杂的解码。

#### 1.3 对应到 sar_convert 代码

`sar.py` 第 252-261 行：

```python
for j in range(B):
    v_test = v_dac + weights[j]
    noise = comparator_noise_norm * rng.standard_normal(...) if ...
    bit = (vin_norm + noise >= v_test).astype(np.int8)
    codes[..., j] = bit
    v_dac = np.where(bit, v_test, v_dac)
```

精确对应贪心算法：`v_test` 试探 → `bit` 比较器决策 → `np.where` 接受/拒绝。
注意 `np.where` 的向量化——整个 batch 同时决策，不需要逐样本 Python 循环。
这是 SAR 模型能快速跑大量样本的关键。


### 2. 权重向量——为什么除以 sum+1LSB 而不是 sum

本库的理想权重生成方式：

```text
raw = [2^(N-1), ..., 2, 1]          例如 4-bit: [8, 4, 2, 1]
weights = raw / (sum(raw) + raw[-1])          = [8,4,2,1] / 16
```

注意分母是 `sum(raw) + 1 LSB`，不是 `sum(raw)`。对 4-bit，是 `/16` 不是 `/15`。
这个 +1 LSB 的来源经常让人困惑，但它有严格的几何意义。

#### 2.1 从量化格子的几何看 +1 LSB

考虑 N-bit ADC，full-scale 归一化到 [0, 1]。它有 `2^N` 个量化**code**，
对应 `2^N` 个重建电平。但 code 之间的边界是 `2^N + 1` 个（包括 0 和 1 两个端点）。

```text
N=4, 16 个 code:
  code 0:  重建电平 0/16 = 0.0000
  code 1:  重建电平 1/16 = 0.0625
  code 2:  重建电平 2/16 = 0.1250
  ...
  code 15: 重建电平 15/16 = 0.9375
```

注意**最高的 code (15) 对应 15/16，不是 1.0**。这是"lower-edge reconstruction"
（Stage 01 讲过）——每个 code 用区间的下界重建。

第 16 个格子 `[15/16, 16/16]` 没有对应的 code（code 15 已经用过了）。
**所以 `2^N` 个 code 覆盖 `2^N - 1` 个完整 LSB 格子 + 最后半个格子。**

权重和：
```text
sum(weights) = sum(raw) / (sum(raw) + 1) = 15/16
```

这意味着 `Σ b[j]·w[j]` 最大只能是 `15/16`（所有 bit=1）——正好对应 code 15。
留出的 `1/16 = 1 LSB` 是"第 16 个格子"的空间，保证所有 code 都落在 [0, 1) 内。

#### 2.2 对应到 § 1 的收敛证明

§ 1.1 证明贪心收敛时，"最后 1 LSB 的溢出"正是这个 +1 LSB 设计：
```text
处理完所有 bit 后，r_final ∈ [0, 1 LSB)
v_dac_final = vin - r_final ∈ (vin - 1 LSB, vin]
```

如果用 `/15`（sum 归一化），`sum(weights) = 1`，所有 bit=1 时 `v_dac = 1.0`，
这会让 code 15 映射到 1.0（full-scale 边界），但 vin=1.0 时没法量化（没有 code 16）。
所以 `/16` 的 +1 LSB 是为了**让量化范围 [0, 1) 完整覆盖**。

#### 2.3 redundancy 时的分母——为什么多一位能纠错

如果加一个 redundant bit，raw 变长一位：

```text
4-bit + 1 redundant (在 bit1 后插入):
  raw = [8, 4, 4, 2, 1]
  sum(raw) = 19, raw[-1] = 1
  weights = raw / 20
```

分母还是 `sum + 1 LSB`，但因为多了一个 bit，总和变大了。这个 +1 bit 不是凭空加的——
它有一个明确的电路目的：**让后续 bit 能补回前面因 comparator noise 造成的误判**。
这一节解释为什么。

##### redundancy 要解决什么：MSB 误判会污染所有后续 bit

§ 数学 1 证明贪心收敛依赖**超增性**（每位权重 > 后面所有位之和）。但超增性有个
副作用：**一旦某步错了，后面补不回来**。

举例 4-bit SAR（无 redundancy），vin = 0.70：

```text
理想决策:
  bit0=1 (v_dac=0.5), bit1=0, bit2=1 (v_dac=0.625), bit3=1 (v_dac=0.6875)
  aout = 0.6875 ✓

bit0 因 comparator noise 误判为 0:
  v_dac 停在 0（本该是 0.5）
  后面 bit1-3 在错误起点上贪心: v_dac 只能到 0.4375
  aout = 0.4375 ✗  偏差 0.25 = w[0]/2
```

**MSB 一次误判，aout 偏差 0.25**——而且后面 3 个 bit 都是"正确决策"，它们只是在一个
错误起点上贪心，无法修正。因为权重超增，后面所有位加起来也补不到 MSB 的量。

##### redundancy 的核心：违反超增性，换取纠错空间

redundancy 的做法是**重复一位**（或降低 radix），让某两位权重相同。这违反了
超增性——但正是这个违反创造了纠错空间。

对 `[8,4,4,2,1]/20`，vin=0.70（= 14 个单位）：

```text
理想决策:
  bit0: 14>=8  -> 1, v_dac=8
  bit1: 14>=12 -> 1, v_dac=12
  bit2: 14<16  -> 0, v_dac=12
  bit3: 14>=14 -> 1, v_dac=14
  bit4: 14<15  -> 0, v_dac=14
  bits=[1,1,0,1,0], aout=14/20=0.70 ✓

bit0 误判为 0:
  bit0: 噪声误判 -> 0, v_dac=0
  bit1: 14>=4  -> 1, v_dac=4
  bit2: 14>=8  -> 1, v_dac=8   ← bit2 补回了 bit0 的一半!
  bit3: 14>=10 -> 1, v_dac=10
  bit4: 14>=11 -> 1, v_dac=11
  bits=[0,1,1,1,1], aout=11/20=0.55
```

对比：无 redundancy 时 bit0 误判导致 aout=0.4375（偏差 0.25），有 redundancy 时
aout=0.55（偏差 0.15）。**redundancy 让 MSB 误判的影响从 0.25 降到 0.15**——后续 bit
（bit2 和 bit0 权重相同）部分补回了错误。

##### 纠错能力：overrange margin

redundancy 的纠错能力用 **margin** 度量：

```text
margin[j] = S[j+1] - w[j]
            ↑              ↑
            后面所有位之和   当前位权重

margin > 0: 后面能补回"bit j 误判"（部分或全部）
margin < 0: 超增，补不回来（无 redundancy）
```

对 `[8,4,4,2,1]/20`：

```text
bit0: S[1]=4+4+2+1=11, margin = 11-8 = 3   → 能容忍 3/20=0.15 的错误
bit1: S[2]=4+2+1=7,    margin = 7-4  = 3   → 能容忍 0.15
bit2: S[3]=2+1=3,      margin = 3-4  = -1  → 超增，补不回来
bit3: S[4]=1,          margin = 1-2  = -1  → 超增
```

**所以 [8,4,4,2,1] 在 bit0/bit1 有 redundancy（margin>0），保护了最容易因噪声出错
的 MSB**。margin=0.15 意味着 comparator noise 让 trial 阈值偏移 < 0.15（归一化）时，
错误决策能被后续 bit 补回。

##### redundancy 的代价

redundancy 不是白来的：

```text
代价 1: 多一次 trial（速度/功耗）
  无 redundancy 4-bit: 4 次 trial
  1-bit redundancy:    5 次 trial → 多 25% 转换时间

代价 2: LSB 变小（分辨率分布变化）
  无 redundancy:  LSB = 1/16
  1-bit redundancy: LSB = 1/20
  步长变小，但有效位数不变（还是 4 位架构）

代价 3: 解码可能变复杂
  本库 sar_reconstruct 用简单线性组合 codes @ weights，对 1-bit redundancy 够用
  多 bit redundancy 可能需要专门 decode 算法
```

##### 和校准的关系（Stage 06 预告）

redundancy 和校准是**互补**的两种手段：

```text
redundancy: 转换时提供纠错空间（硬件，多一位 trial）
            -> 主要对付 comparator noise（随机误判）
            -> 对 deterministic mismatch 无效

校准:       重构时用正确权重（数字，估计 actual_weights）
            -> 主要对付 CDAC mismatch（deterministic）
            -> 对 comparator noise 无效
```

实际 SAR ADC 通常两者都用。Stage 06 会展开校准；多 bit redundancy 和校准的交互
（redundant bit 帮助估计 weights）也留到 Stage 05/06。


#### 2.4 对应到 sar_ideal_weights 代码

`sar.py` 第 79-83 行：

```python
w = [2 ** (num_bits - 1 - i) for i in range(num_bits)]   # raw = [8,4,2,1]
if redundant_bit is not None:
    w.insert(redundant_bit + 1, w[redundant_bit])        # 插入冗余位
w = np.asarray(w, dtype=float)
return w / (w.sum() + w[-1])                              # / (sum + 1 LSB)
```

`w[-1]` 就是 raw LSB（=1）。`w.sum() + w[-1]` = `sum(raw) + 1`。精确对应 § 2.1。


### 3. mismatch——sigma ∝ 1/√C 的概率推导

实际电容不是理想值：

```text
w_actual = w_nominal · (1 + error)
```

本库 `sar_apply_cap_mismatch` 的核心假设是 **unit-cap（单位电容）模型**：每个 bit 的
电容由若干个相同的"单位电容 Cu"并联组成，每个 Cu 的容值有独立随机偏差。

这一节从概率论推导 `sigma ∝ 1/√C`，并对应到代码。

#### 3.1 unit-cap 模型

假设 bit j 由 `n[j]` 个单位电容 Cu 并联组成。理想容值 `C[j] = n[j]·Cu`。

每个单位电容的容值是随机变量：

```text
Cu_i = Cu_ideal · (1 + ε_i)
ε_i ~ N(0, σ_C²)    独立同分布，σ_C 是单位电容的相对失配
```

bit j 的总容值：

```text
C[j] = Σ_{i=1}^{n[j]} Cu_i = Cu_ideal · Σ_{i=1}^{n[j]} (1 + ε_i)
     = n[j]·Cu_ideal · (1 + (1/n[j])·Σ ε_i)
     = C[j]_ideal · (1 + ε̄[j])
```

其中 `ε̄[j] = (1/n[j])·Σ ε_i` 是 n[j] 个独立失配的平均。

#### 3.2 sigma ∝ 1/√C 的推导

`ε̄[j]` 是 n[j] 个独立同分布 N(0, σ_C²) 随机变量的平均。由独立随机变量和的方差性质：

```text
Var(ε̄[j]) = Var((1/n[j])·Σ ε_i)
          = (1/n[j]²)·Σ Var(ε_i)         （独立性让方差直接相加）
          = (1/n[j]²)·n[j]·σ_C²
          = σ_C² / n[j]

所以:  std(ε̄[j]) = σ_C / √n[j]
```

**这就是 `sigma_relative ∝ 1/√n[j]` 的来源**——n[j] 个独立失配平均后，相对误差
的标准差按 `1/√n[j]` 衰减。

因为 `C[j] = n[j]·Cu`，所以 `n[j] = C[j]/Cu`，代入：

```text
std(ε̄[j]) = σ_C / √(C[j]/Cu) = σ_C·√(Cu/C[j])
           ∝ 1/√C[j]
```

**物理含义**：
```text
MSB (n 大, C 大):  相对失配小  -> 权重更准
LSB (n 小, C 小):  相对失配大  -> 权重更不准
```

这就是为什么 MSB 的权重通常比 LSB 准——不是因为 MSB 做得更精细，而是因为它由更多
单位电容并联，统计平均让随机偏差按 `1/√n` 衰减。这是集成电路里"用面积换精度"
的基本 tradeoff。

#### 3.3 对应到 sar_apply_cap_mismatch 代码

`sar.py` 第 140-157 行：

```python
if cap_units is None:
    cap_units = weights / np.min(weights)          # 从权重推断单位电容数
                                                    # 例如 [8,4,2,1]/16 -> cap_units=[8,4,2,1]
relative_sigma = sigma / np.sqrt(cap_units)         # 每个 bit 的相对失配 std
return weights * (1.0 + relative_sigma * rng.standard_normal(len(weights)))
```

逐行：
- `cap_units = weights / min(weights)`：把权重除以最小权重，得到每个 bit 的"单位电容
  数"。对 `[8,4,2,1]/16`，`cap_units = [8,4,2,1]`——MSB 是 8 个 Cu，LSB 是 1 个 Cu。
- `relative_sigma = sigma / √cap_units`：精确对应 § 3.2 的 `σ_C/√n[j]`。
  MSB 的 relative_sigma = `σ/√8`，LSB 的 = `σ/√1 = σ`。
- `weights * (1 + relative_sigma·N(0,1))`：每个权重独立加一个高斯扰动，
  std 就是上面的 relative_sigma。

所以 `sigma` 参数是**单位电容的相对失配**，不是每个 bit 的失配。一个 `sigma=0.01`
意味着 1% 的单位电容相对失配；MSB（8 个 Cu）的实际相对失配只有 `0.01/√8 ≈ 0.35%`。

#### 3.4 全流程演示：nominal vs actual 的数值对比

§ 3.3 讲了 mismatch 怎么加到权重上。但真正的失真不是"权重偏了"本身，而是**权重
偏移让 comparator 在边界附近做出不同决策**。这一节用一个具体的数值例子把全流程
走一遍。

设 4-bit SAR，sigma=0.05（故意取大让效果可见），固定 seed=42：

```text
nominal = [0.5,     0.25,    0.125,   0.0625]    sum = 0.9375 (= 15/16)
actual  = [0.5027,  0.2435,  0.1283,  0.0654]    sum = 0.9399
差值    = [+0.0027, -0.0065, +0.0033, +0.0029]
```

**注意 sum(actual) ≠ sum(nominal)**——代码不重新归一化（docstring 明确写明）。这产生
一个小的**增益误差**（线性，全局缩放 +0.26%），但这不是主要失真来源。

##### bit 翻转的例子：vin = 0.5（MSB 翻转）

```text
ideal 路径 (用 nominal):
  bit0 trial: v_test=0.5,    vin=0.5 >= 0.5    -> bit0=1, v_dac=0.5
  bit1 trial: v_test=0.75,   vin=0.5 < 0.75    -> bit1=0
  bit2 trial: v_test=0.625,  vin=0.5 < 0.625   -> bit2=0
  bit3 trial: v_test=0.5625, vin=0.5 < 0.5625  -> bit3=0
  codes=[1,0,0,0], aout=0.5  ✓

actual 路径 (用 actual):
  bit0 trial: v_test=0.5027, vin=0.5 < 0.5027  -> bit0=0  ★ MSB 翻转!
              v_dac 停在 0
  bit1 trial: v_test=0.2435, vin=0.5 >= 0.2435 -> bit1=1, v_dac=0.2435
  bit2 trial: v_test=0.3718, vin=0.5 >= 0.3718 -> bit2=1, v_dac=0.3718
  bit3 trial: v_test=0.4372, vin=0.5 >= 0.4372 -> bit3=1, v_dac=0.4372
  codes=[0,1,1,1], aout(用nominal重构)=0.25+0.125+0.0625=0.4375
```

**关键现象**：MSB 翻转了（bit0 从 1→0），但后续 bit "捡回"了大部分——bit1+bit2+bit3
用 actual 权重凑出 0.4372，接近理想的 0.5。最终 aout=0.4375，误差只有 -0.0625 = -1 LSB。

**为什么只差 1 LSB 而不是整个 MSB**：因为二进制权重有"自然冗余"——后续位加起来
（actual 的 bit1+2+3 = 0.4372）接近 MSB 偏差（actual bit0 = 0.5027）。这是 § 2.3
讲的 redundancy 思想的自然体现：即使没有显式 redundant bit，超增性让后续位部分补回
MSB 错误。差别是显式 redundancy 能完全补回，纯二进制只能部分补回。

##### 扫描所有 vin：翻转是"块状"分布

对每个 code 起点的 vin 做 nominal/actual 对比（sigma=0.05, seed=42）：

```text
code   vin 起点   ideal aout   uncal aout   error    翻转?
  0    0.0000     0.0000       0.0000       0        no
  1    0.0625     0.0625       0.0000      -0.0625   YES  (bit3 翻转)
  2    0.1250     0.1250       0.0625      -0.0625   YES
  3    0.1875     0.1875       0.1250      -0.0625   YES
  4    0.2500     0.2500       0.2500       0        no
  5    0.3125     0.3125       0.3125       0        no
  6    0.3750     0.3750       0.3750       0        no
  7    0.4375     0.4375       0.4375       0        no
  8    0.5000     0.5000       0.4375      -0.0625   YES  (bit0 MSB 翻转)
  9    0.5625     0.5625       0.5000      -0.0625   YES
 10    0.6250     0.6250       0.5625      -0.0625   YES
 11    0.6875     0.6875       0.6250      -0.0625   YES
 12    0.7500     0.7500       0.7500       0        no
 13    0.8125     0.8125       0.8125       0        no
 14    0.8750     0.8750       0.8750       0        no
 15    0.9375     0.9375       0.8750      -0.0625   YES
```

**几个关键观察**：

```text
1. error 要么是 0（没翻转），要么是 ±1 LSB（翻转）
   -> 不是"差一个 MSB"，而是后续 bit 贪心补偿后剩 ±1 LSB

2. 翻转是"块状"分布（code 1-3 翻，4-7 不翻，8-11 翻，12-14 不翻）
   -> 因为 bit0 阈值偏 +0.0027，让 vin ∈ [0.5, 0.5027] 时 MSB 翻转
   -> 这个小区间影响整个 code 8-11 区间的决策路径

3. 不是每个 code 都翻转，只在 actual 阈值和 ideal 阈值错位的 code 翻转
   -> 翻转概率约 5-15%（取决于 sigma 大小）
```

##### 这种"块状 error"在 transfer curve 上是什么样

把翻转的 code 标在 transfer curve 上：

```text
        aout
    1.0 │                              ·15·
        │                         ·14·
 0.9375 │                    ·13·
        │               ·12·
  0.75  │          ··11··← 本该到 0.75, 实际只到 0.6875 (被压低)
        │        ·10·
 0.625  │       ·9·
        │      ·8·← 本该到 0.625, 实际到 0.5625
  0.5   │    ··7··
        │   ·6·
 0.375  │  ·5·
        │ ·4·
  0.25  │··3··← 本该到 0.25, 实际到 0.1875
        │·2·
 0.125  │·1·
        │0
    0.0 ┼────────────────────────────────── vin
        0   0.25  0.5  0.75  1.0
```

**这是 transfer curve 的"局部压缩"**——翻转的 code 段输出被压低，多个 code 映射到
相近的 aout。这就是 DNL/INL 异常的来源：某些 code 宽度变宽（missing code），某些
变窄（重叠）。这种 transfer curve 非线性在正弦输入下产生 harmonic。

#### 3.5 为什么 mismatch 产生 harmonic（连接 Stage 03）

§ 3.4 的扫描表显示：error 是 **vin 的分段常数函数** `error = g(vin)`，每个 code
区间一个固定值（0 或 ±1 LSB）。这看起来不像 `cos(2ωt)` 形式的谐波——那为什么
频谱上会出现 harmonic？

##### 分段常数 error 在正弦输入下变成周期信号

关键转换：**error 是 vin 的函数，而 vin 本身是时间的正弦函数**。

```text
输入:   vin(t) = A·sin(2πft)
误差:   e(t) = g(vin(t)) = g(A·sin(2πft))
```

`g` 是分段常数（每个 code 一个值），`A·sin(2πft)` 是正弦。把它们复合：

```text
vin(t) 每个周期扫过 [0, A] 一次
-> vin(t) 经过每个 code 边界一次/周期
-> e(t) = g(vin(t)) 每周期重复同样的"翻转 pattern"
-> e(t) 是周期为 1/f 的信号
-> 任何周期信号都可以展开为 Fourier 级数（fundamental + harmonic）
```

所以 **e(t) 虽然不是纯正弦，但因为是周期的，必然包含 fundamental 的整数倍频率
（harmonic）**。这就是 mismatch 失真在频谱上表现为 HD2/HD3/.../ 的原因。

##### 为什么 harmonic 阶数和 mismatch 分布有关

```text
对称的 mismatch（所有 bit 同方向偏）:
  -> g(vin) 关于 0.5 对称
  -> Fourier 展开主要是偶阶（HD2, HD4, ...）

非对称的 mismatch（某些 bit 偏多、某些偏少）:
  -> g(vin) 不对称
  -> Fourier 展开含奇阶（HD3, HD5, ...）

实际 chip 的 mismatch 是随机的:
  -> g(vin) 是随机分段函数
  -> 通常同时有 HD2/HD3/.../，具体阶数取决于哪个 bit 偏多少
```

这就是为什么诊断时看 spectrum 的 harmonic 阶数能帮助定位问题：
- 只有 HD2 → 可能是对称类 mismatch（比如 MSB + LSB 偏，中间位不偏）
- HD3 强 → 奇阶非对称（比如中间位 MSB-1 偏）
- 所有阶都有 → 随机 mismatch（最常见）

##### 连接 Stage 03 的诊断工具

回顾 Stage 03 实验 2 的 Static HD2/HD3 case——那里的失真是用多项式
`y = x + k2·x² + k3·x³` 直接加的，产生连续的 `cos(2ωt)`。

SAR mismatch 的失真机制不同——它是**分段常数**的（每个 code 一个值），不是连续
多项式。但两者在频谱上的表现类似（都产生 harmonic），因为：

```text
Stage 03 的多项式失真:   连续的 cos(2ωt) 形式
SAR mismatch 失真:       分段常数 error(t) 的 Fourier 展开

两者都包含 fundamental 整数倍频率，所以在 spectrum 上都表现为 harmonic spur。
区别在具体形状：多项式失真的 harmonic 是单一干净的 spur；
SAR mismatch 的 harmonic 可能更"脏"（因为 g(vin) 不是平滑函数）。
```

所以 Stage 03 学的诊断能力（spectrum 看 harmonic → 怀疑 deterministic 非线性）在
SAR 上完全适用。下一步是用 by_value 看 `g(vin)` 的具体形状（分段常数的"阶梯"），
判断是哪个 bit 有问题——这是 Stage 03 by_value 分析的核心价值。

#### 3.6 一个容易混淆的点

`sigma` 是**RMS 相对失配**，不是绝对失配。对 `sigma=0.01`：
```text
1 个 Cu (LSB):     实际容值 = 1 ± 0.01·N(0,1)   -> 1% RMS
8 个 Cu (MSB):     实际容值 = 8 ± 8·(0.01/√8)·N(0,1)
                                  = 8 ± 0.028·N(0,1)   -> 0.35% RMS
```

MSB 的**绝对**偏差 std 是 `8·0.0035 = 0.028`（Cu 单位），比 LSB 的 `1·0.01=0.01` 大。
但**相对**偏差更小。校准关心的是相对偏差（因为它决定 transfer curve 的非线性度）。


### 4. 两套权重——actual vs nominal 的误差传递

必须区分两套权重，这是理解 SAR 失真和校准的关键：

```text
actual analog weights:    CDAC 真实的物理权重（含 mismatch）
digital reconstruction weights:  数字端用来重构 aout 的权重
```

#### 4.1 两套权重的数据流

```text
转换时（模拟域）:
  bits = sar_convert(vin, actual_weights)
  -> comparator 用 actual_weights 决策
  -> bits 是"在失真权重下做出的决策"

重构时（数字域）:
  aout = sar_reconstruct(bits, digital_weights)
  -> aout = bits · digital_weights
```

三种典型情况：

```text
1. 理想 ADC:
   actual_weights = nominal_weights
   digital_weights = nominal_weights
   -> aout = 理想量化输出，无失真

2. 未校准 ADC:
   actual_weights = nominal · (1 + mismatch)     ← 含失真
   digital_weights = nominal                      ← 数字端不知道失真
   -> aout 含 mismatch 引起的失真

3. 校准后:
   actual_weights = nominal · (1 + mismatch)     ← 失真还在（物理没变）
   digital_weights = calibrated ≈ actual          ← 数字端用估计的 actual 重构
   -> aout 失真被补偿
```

#### 4.2 误差传递：mismatch 怎么变成 aout 误差

设 `actual[j] = nominal[j]·(1 + ε[j])`。转换时用 actual 决策得到的 bits，
然后用 nominal 重构：

```text
aout_calibrated = Σ bits[j] · nominal[j]
aout_ideal      = Σ bits_ideal[j] · nominal[j]    （理想 bits）

误差:  e = aout_calibrated - aout_ideal
         = Σ (bits[j] - bits_ideal[j]) · nominal[j]
```

关键：bits 和 bits_ideal 在哪里不同？**当 mismatch 让某个 bit 的 trial 阈值偏移，
可能让 comparator 在边界附近做出不同决策**。

精确分析：bit j 的 trial 阈值是 `v_test_actual = v_dac_actual + actual[j]`，而理想
阈值是 `v_test_ideal = v_dac_ideal + nominal[j]`。两者差：

```text
Δv_test[j] = (v_dac_actual - v_dac_ideal) + (actual[j] - nominal[j])
           = Δv_dac[j] + nominal[j]·ε[j]
```

其中 `Δv_dac[j] = Σ_{k<j} (bit_actual[k] - bit_ideal[k])·actual[k]` 是前面 bit 累积的偏差。

**当 vin 接近某个 trial 阈值时**（即 vin 在阈值附近 ±Δv_test 内），comparator 可能
做出和理想不同的决策 → bit[j] ≠ bit_ideal[j] → 产生 aout 误差。

这就是 mismatch 产生失真的机制——**不是每个样本都受影响，只有 vin 接近 trial 阈值
的样本**。而这些样本在输入正弦下是周期性出现的（每个周期经过每个 code 边界一次），
所以失真是**周期性的 → 在频谱上表现为 harmonic**。

#### 4.3 校准为什么能修

校准的目标是让 `digital_weights ≈ actual_weights`。如果完全相等：

```text
aout = Σ bits[j] · digital_weights[j]
     = Σ bits[j] · actual[j]
     = sar_convert 内部的 v_dac_final    （因为转换时就是用 actual 累积的）

所以 aout = 转换时的实际 v_dac，和 vin 的差只剩量化误差（< 1 LSB）。
```

**校准的本质**：用数字权重"复现"转换时模拟域的真实累积，从而消除 mismatch 引起的
决策偏差。这就是为什么 `calibrate_weight_sine` 要估计 actual_weights——
它通过观察 aout 对正弦输入的响应，反推每个 bit 的实际权重。

#### 4.4 校准的局限：随机噪声修不了

§ 4.2-4.3 讨论的是 deterministic mismatch（每次转换相同）。但 SAR 还有两种随机噪声：

```text
comparator noise: 每次 trial 的比较器噪声，让 bit 决策随机翻转
sampling noise:   采样时的 kT/C 噪声，进入 vin_sampled
```

这两种噪声是 stochastic——每次转换不同，不能用 digital_weights 补偿（因为
digital_weights 是固定的，而噪声是随机的）。所以：

```text
校准能修:  capacitor mismatch（deterministic）
校准不能修: comparator noise + sampling noise（stochastic）
```

这是 Stage 06 校准的核心结论，也是 Stage 03 § 电路类别 1（随机噪声不可校准）的
数学依据。Stage 03 实验 4 step_4 已经看到：校准让 SFDR 改善（修了 harmonic），
但 SNR 几乎不变（没修 noise floor）。

#### 4.5 对应到 sar_convert / sar_reconstruct 代码

`sar_convert`（第 176-262 行）用 `weights` 参数——这是 **actual analog weights**：
```python
def sar_convert(vin, weights, ...):          # weights = actual_weights
    for j in range(B):
        v_test = v_dac + weights[j]          # 用 actual 设阈值
        bit = (vin_norm + noise >= v_test)   # comparator 决策
        v_dac = np.where(bit, v_test, v_dac) # 用 actual 累积
    return codes
```

`sar_reconstruct`（第 265-298 行）用另一个 `weights` 参数——这是 **digital weights**：
```python
def sar_reconstruct(codes, weights, ...):    # weights = digital_weights
    return (codes.astype(float) @ np.asarray(weights)) * full_scale + v_min
```

**两个函数的 weights 参数是独立的**——这正是"两套权重"设计。调用者可以：
```python
actual = sar_apply_cap_mismatch(nominal, sigma=0.01)
codes = sar_convert(vin, actual)                    # 用 actual 转换
aout_uncalibrated = sar_reconstruct(codes, nominal) # 用 nominal 重构（未校准）
aout_calibrated   = sar_reconstruct(codes, actual)  # 用 actual 重构（已校准，假设已知 actual）
```

这就是 whole_workflow demo step_4 展示的三个场景（ideal / mismatch_nominal / calibrated）。


## 电路需要理解什么

这一节把 SAR ADC 的四个核心电路块（SAR logic / CDAC / comparator / sampling）逐个
讲清"物理机制 → 代码建模 → residual 特征"。这是 Stage 03 § 电路分类的"SAR 具体化"——
Stage 03 讲了 15 种非理想的通用形态，Stage 04 要回答"这些非理想在 SAR 上具体怎么产生"。

### 1. SAR ADC 电路块——整体架构

**电路图像**：典型 SAR ADC 包含五个块：

```text
               vin
                │
                ▼
        ┌───────────────┐
        │ sample-and-hold│  采样开关 + 保持电容
        └───────┬───────┘
                │ vin_sampled
                ▼
        ┌───────────────┐    v_dac（CDAC 输出）
        │   comparator  │◀──────────┐
        └───────┬───────┘           │
                │ bit decision      │
                ▼                   │
        ┌───────────────┐           │
        │  SAR logic    │───────────┤ 切换 CDAC 的 bit
        │  （逐次控制） │           │
        └───────┬───────┘           │
                │ final bits        │
                │                   │
        ┌───────▼───────┐           │
        │ reference     │───────────┘ Vref 供电给 CDAC
        │   driver      │
        └───────────────┘
```

每一位 trial 的实际电路操作（对应 § 数学 1 的贪心步骤）：

```text
1. SAR logic 控制 CDAC: 把当前 bit 的电容切到 Vref（或地）
2. 等待 CDAC 建立到稳定（有限时间，受 RC 限制）
3. comparator 比较 vin_sampled 和 v_dac
4. 锁存 bit decision，反馈给 SAR logic
5. 进入下一位
```

**和数学模型的对应**：`sar_convert` 的 `for j in range(B)` 循环就是这五步的抽象——
每一步对应一次 comparator decision。代码省略了"等待建立"（假设无限快）和
"切换 CDAC"（用 `v_dac += weights[j]` 抽象）。

#### 1.1 SAR logic 基本结构——状态机

上面架构图里的"SAR logic"块，本质上是一个**有限状态机（FSM）**，控制 trial 顺序 +
存储 bit decision。这就是 SAR 名字里 "Register" 的部分（Successive Approximation
**Register**）。

**状态机的状态转移**：

```text
         ┌──────────────┐
         │   IDLE       │  等待转换启动
         └──────┬───────┘
                │ start
                ▼
         ┌──────────────┐
         │  SAMPLE      │  控制 S/H 进入 track 相位
         │              │  Cs 充电到 vin
         └──────┬───────┘
                │ T_track 结束
                ▼
         ┌──────────────┐
         │  HOLD        │  S/H 断开，Cs 冻结 vin_sampled
         │              │  v_dac = 0 (reset CDAC)
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐  bit index j = 0 (MSB)
         │  TRIAL       │◀─────────────────┐
         │  切 CDAC bit j│                  │
         │  等待建立     │                  │
         │  触发 comparator                  │
         │  锁存 bit[j]  │                  │
         └──────┬───────┘                   │
                │                           │
                ▼                           │
         ┌──────────────┐                   │
         │  j == N-1?   │─── no ─── j++ ───┘
         └──────┬───────┘
                │ yes
                ▼
         ┌──────────────┐
         │  DONE        │  输出 N-bit codes
         │              │  回到 IDLE
         └──────────────┘
```

**每个状态的职责**：

```text
IDLE:    等待 start 信号，CDAC 复位
SAMPLE:  控制 S/H 开关闭合，Cs 充电（持续 T_track）
HOLD:    S/H 开关断开，Cs 保持 vin_sampled；CDAC 复位到 v_dac=0
TRIAL:   核心循环（执行 N 次，对应 N bit）:
           a. 把 bit j 的电容切到 Vref（试探性"取"这位）
           b. 等待 CDAC 建立到稳定（RC 充放电）
           c. 触发 comparator，比较 vin_sampled 和 v_dac
           d. 锁存 comparator 输出 -> bit[j]
           e. 根据 bit[j] 决定该电容保留 Vref (bit=1) 还是切回 GND (bit=0)
DONE:    输出 [bit0, bit1, ..., bitN-1]，回到 IDLE
```

**和 § 数学 1 贪心算法的精确对应**：

```text
状态机 TRIAL 的 a-e 步:
  a. 切 bit j 到 Vref          ↔  v_test = v_dac + weights[j]
  b. 等待建立                  ↔  (代码假设瞬间建立，跳过)
  c. comparator 比较           ↔  bit = (vin_norm >= v_test)
  d. 锁存 bit[j]              ↔  codes[j] = bit
  e. bit=1 保留, bit=0 切回    ↔  v_dac = where(bit, v_test, v_dac)

代码的 for j in range(B) 就是状态机在 TRIAL 状态循环 N 次。
```

**SAR logic 的实现方式**：

```text
方式 1: 硬连线状态机 (传统 SAR)
  - 用 D 触发器 + 逻辑门实现状态转移
  - 固定 N 比特，不可配置
  - 速度快，面积小
  - 大多数商用 SAR ADC 用这种

方式 2: 微控制器 / 数字核 (可编程)
  - 用小型 MCU 控制 trial 顺序
  - 灵活（支持 redundancy、可变 bit 数）
  - 慢，面积大
  - 研究/校准型 ADC 用这种

代码 sar_convert 用 Python for 循环:
  - 对应方式 2 的"可编程"抽象
  - 不模拟状态机的时序（时钟周期、建立时间）
  - 只模拟"逻辑决策"部分
```

**为什么 SAR logic 本身不产生失真**：

```text
SAR logic 是纯数字电路:
  - 状态转移确定（FSM）
  - bit 存储确定（寄存器）
  - 没有 analog 噪声

SAR 的失真来自它控制的"模拟块":
  - CDAC: 电容 mismatch (§ 2)
  - comparator: 噪声 + offset (§ 3)
  - S/H: kT/C + settling (§ 4)

所以代码 sar_convert 不模拟 SAR logic 本身——
它的"for 循环"就是 SAR logic 的抽象，没有非理想参数。
```

### 2. CDAC mismatch——bit weight 偏差

**电路图像**：CDAC 由一组电容组成，每个 bit 对应一个电容（或一组单位电容）。
制造工艺让每个电容的容值偏离设计值——这是 **deterministic** 失配（同一芯片每次
转换都一样，但芯片之间不同）。

**物理机制**：光刻、蚀刻、氧化层厚度的不均匀让每个电容的尺寸/介电常数有偏差。
这个偏差在芯片制造后就固定了，不随时间变（除非老化/温度漂移）。

**代码建模**（`sar_apply_cap_mismatch`，§ 数学 3 已详述）：

```python
cap_units = weights / np.min(weights)              # 每个 bit 的单位电容数
relative_sigma = sigma / np.sqrt(cap_units)         # σ/√n 的相对失配
actual_weights = weights * (1.0 + relative_sigma * rng.standard_normal(B))
```

**误差传递**（§ 数学 4 已推导）：mismatch 让 trial 阈值偏移 → 边界附近 bit 翻转 →
周期性失真 → harmonic。

**residual 特征**（对照 Stage 03 实验 2 的 Static HD2/HD3 case）：

```text
PDF:    不对称或结构明显（KL 中等，~0.1-0.3）
        因为 mismatch 产生的是 deterministic harmonic
ACF:    周期性振荡（harmonic 是周期信号）
spectrum: 在 Fin 的整数倍处有明显 spur（HD2/HD3/...）
         -> 这是诊断 CDAC mismatch 最直接的工具
by_value: 误差随输入幅度有结构（transfer curve 非线性）
         -> by_value 能看到"哪个 code 区域有问题"
```

**诊断意义**：CDAC mismatch 是 Stage 03 类别 2（静态非线性）的典型。因为它是
deterministic，所以**适合校准**（Stage 06 的核心目标）。诊断时优先看 spectrum
的 harmonic spur 位置——HD2 强说明 MSB 有问题，高阶 harmonic 说明多位有问题。

**一个关键认知**：mismatch 的 sigma 设得越大，harmonic 越强、SFDR 越差，但
SNR 几乎不变——因为 mismatch 是 deterministic（不增加 noise floor）。这是
"SFDR 差但 SNR 好 = mismatch 问题"的诊断依据。

### 3. Comparator noise——bit decision 随机翻转

#### 3.1 comparator 基本结构

comparator（比较器）是 SAR ADC 里唯一"做决策"的电路块——它判断 vin_sampled 和
v_dac 的大小，输出 1 bit 数字结果。理解它的结构和噪声，是理解 SAR 精度极限的关键。

**两阶段结构：preamp + latch**

现代高速 comparator 几乎都是两阶段：

```text
              vin_sampled
                  │
                  ▼
          ┌───────────────┐
          │   preamp      │  预放大器（线性放大）
          │  (G ≈ 5-20)   │  把 vin - v_dac 的微小差放大
          └───────┬───────┘
                  │ G·(vin - v_dac)
                  ▼
          ┌───────────────┐
          │   latch       │  锁存器（正反馈再生）
          │  (regenerative)│  把放大后的差驱动到 rail-to-rail
          └───────┬───────┘
                  │ digital out (0 或 1)
                  ▼
```

**为什么需要两阶段**：

```text
只有 latch (没有 preamp):
  latch 的输入失调 (offset) 和噪声直接决定决策
  -> 精度差（latch 的 offset 通常几 mV 甚至几十 mV）

preamp + latch:
  preamp 先把 (vin - v_dac) 放大 G 倍
  -> latch 看到的等效输入噪声/offset 被 preamp 增益 G 压低
  -> 等效输入噪声 ≈ σ_latch / G
  -> 精度提升（但 preamp 本身也耗电、有带宽限制）

G 的 tradeoff:
  G 大 -> 噪声小，但 preamp 慢（建立时间长）-> 转换速度下降
  G 小 -> 噪声大，但 preamp 快
  典型 G ≈ 5-20，是 SAR 设计的核心 tradeoff 之一
```

**latch 的再生（regeneration）**：

latch 是一个**正反馈**电路——两个反相器交叉连接，任何微小的输入差都会被指数放大，
迅速锁存到 rail-to-rail（VDD 或 GND）。这让 comparator 的输出在锁存后是干净的
数字电平，但**锁存瞬间承受的噪声被"冻结"**——这就是 comparator noise 的来源。

**和代码模型的对应**：

```text
真实 comparator:
  preamp 放大 (vin - v_dac) + 内部热噪声
  latch 锁存 -> bit = sign(G·(vin - v_dac) + noise)

代码 sar_convert:
  bit = (vin_norm + noise >= v_test)
  -> noise 折算到输入端 (input-referred)，等效 σ_cmp
  -> G 的效应被吸收进 σ_cmp (σ_cmp = σ_latch / G)
```

所以代码里的 `comparator_noise_rms` 是 **input-referred noise**——已经把 preamp 增益
的降噪效应考虑进去了。真实设计里增大 G 能降低 σ_cmp，但代码不模拟 G 本身。

#### 3.2 comparator noise 的物理机制

（差值小于噪声幅度），比较器可能输出 0 或 1，每次不同。这是 **stochastic** 噪声。

**代码建模**（`sar_convert` 第 254-259 行）：

```python
for j in range(B):
    v_test = v_dac + weights[j]
    noise = comparator_noise_norm * rng.standard_normal(vin_norm.shape)
                                  # 每个 bit 独立抽取一个噪声（不是每个样本！）
    bit = (vin_norm + noise >= v_test).astype(np.int8)
```

**关键细节**：`rng.standard_normal(vin_norm.shape)` 生成的是**和 vin 同 shape 的
数组**——意味着每个样本的每个 bit 都有独立的噪声实现。这是 `B·N` 个独立噪声样本
（B bit × N 样本），不是 1 个。

数学上：

```text
对样本 n 的 bit j:
  bit[n,j] = 1 if (vin[n] + w_cmp[j] >= v_test[n,j]) else 0
  
  其中 w_cmp[j] ~ N(0, σ_cmp²)  独立抽取
```

**误差机制**：当 `|vin[n] - v_test[n,j]| < 3·σ_cmp` 时，bit decision 可能翻转。
这产生一个"决策噪声"——不是直接加到 aout 上，而是通过**错误的 bit decision**
间接影响 aout。

**为什么 comparator noise 比同等 RMS 的 thermal noise 更复杂**：
```text
thermal noise (加性):   aout = ideal + w     直接加，线性
comparator noise (决策): bit 可能翻转 -> aout 偏离 1·weight[j]（不是 σ_cmp）
```

comparator noise 的一个错误决策让 aout 偏差 `±weights[j]`（整个 bit 的权重），
远大于 `σ_cmp` 本身。这让 comparator noise 的非线性效应更强。

**residual 特征**：

```text
PDF:    近 Gaussian（KL 小）—— 因为噪声是随机的，幅度分布接近高斯
ACF:    近白噪声（每次 trial 独立抽取噪声）
spectrum: 抬高 noise floor（随机 bit 翻转是宽带噪声）
         -> SNR/ENOB 下降
```

**诊断意义**：comparator noise 主要影响 SNR（不是 SFDR）。如果测出 SNR 差但
SFDR 正常，且 PDF 接近 Gaussian，基本就是 comparator/sampling noise 主导。
这种噪声是 stochastic，**校准不能完全消除**——只能靠 averaging、降低噪声设计、
或用 redundancy（§ 数学 6）容忍。

### 4. Sampling noise——kT/C 噪声

#### 4.1 sample-and-hold 基本结构

sample-and-hold（采样保持，S/H）是 SAR ADC 的"前门"——它在采样相位把连续输入
电压"冻结"到电容上，在转换相位保持这个电压供后续 bit trials 使用。它的精度直接
决定 ADC 能达到的分辨率上限。

**开关电容结构**：

```text
              vin (连续)
                │
                │  采样相位 (φ1 闭合)
            ┌───⊥───┐
            │  switch│  R_on (开关导通电阻)
            └───┬───┘
                │
                ●──────── 转换相位 (φ1 断开, φ2 控制 CDAC)
                │
               ─┴─  Cs (采样电容)
                │
               ─┬─
                │
               GND

工作时序:
  φ1 闭合 (track/采样):  Cs 通过 R_on 充电到 vin
                         需要 T_track >> R_on·Cs 才能建立
  φ1 断开 (hold/保持):   Cs 上的电压被"冻结"
                         后续 bit trials 用这个冻结的电压比较
```

**两个关键参数**：

```text
1. 采样时间 T_track (track phase 持续时间)
   Cs 充电是 RC 过程: v_Cs(t) = vin·(1 - exp(-t/(R_on·Cs)))
   要建立到 0.5 LSB 精度（N bit）:
     exp(-T_track/(R_on·Cs)) < 1/(2^(N+1))
     T_track > (N+1)·ln2·R_on·Cs ≈ 0.69·(N+1)·R_on·Cs
   对 12-bit: T_track > 9·R_on·Cs
   -> 这就是 § 电路 3 incomplete settling 的物理来源
   -> T_track 不够 -> 建立不足 -> error 和输入幅度相关（HD3）

2. 采样电容 Cs 大小
   Cs 大 -> 噪声小（kT/C，下面推导），但:
     - 建立慢（R_on·Cs 大）-> 需要更长 T_track 或更小 R_on
     - 驱动难（要给大电容快速充电）-> 输入 buffer 功耗大
     - 面积大
   Cs 小 -> 噪声大，但建立快、驱动易、面积小
   -> 这是 SAR 设计的核心 tradeoff: 噪声 vs 速度/功耗/面积
```

**电荷注入（charge injection）和 clock feedthrough**——S/H 的另一个非理想：

```text
φ1 断开瞬间:
  - 开关 MOS 管的沟道电荷注入到 Cs (charge injection)
  - 时钟边沿通过寄生电容耦合到 Cs (clock feedthrough)
  -> Cs 上的电压跳变一个固定量 (通常和输入有关)
  -> 产生 offset 和非线形 error

缓解: bottom-plate sampling、dummy switch、差分结构
代码不模拟这两个（它们是 deterministic，可以校准掉）
```

**和代码模型的对应**：

```text
真实 S/H:
  Cs 充电到 vin + kT/C 噪声 + 建立不足误差 + charge injection
  -> vin_sampled = vin + w_s + e_settling + e_inj

代码 sar_convert:
  vin_sampled = vin + sampling_noise_rms · N(0,1)
  -> 只模拟 kT/C 噪声（随机）
  -> settling 在独立的 apply_incomplete_sampling（Stage 03 实验 2 用过）
  -> charge injection 不模拟（可校准，属于 offset）
```

所以代码把 S/H 的非理想**拆成两个独立函数**：`sar_convert` 的 `sampling_noise_rms`
模拟 kT/C，`apply_incomplete_sampling` 模拟建立不足。这符合 Stage 03 的"一种非理想
一个 case"设计。

#### 4.2 sampling noise 的物理机制

**电路图像**：采样开关闭合时，信号通过开关电阻 R 给采样电容 Cs 充电。开关电阻
本身有热噪声，这个噪声在采样瞬间被"冻结"进 Cs。

**物理机制**：这是经典的 **kT/C 噪声**。RC 低通滤波器的等效噪声带宽是
`1/(4RC)`，乘以电阻的热噪声功率谱密度 `4kTR`：

```text
v_noise² = 4kTR · (1/(4RC)) = kT/C
v_noise_rms = √(kT/C)
```

**关键**：kT/C 噪声只取决于温度 T 和电容 C，**和电阻 R 无关**（R 大则带宽小，
正好抵消）。这是采样电路的基本极限——增大 Cs 能降噪，但 Cs 大会让驱动更难、
功耗更高。

**代码建模**（`sar_convert` 第 243-245 行）：

```python
vin_sampled = vin.copy()
if sampling_noise_rms > 0:
    vin_sampled = vin_sampled + sampling_noise_rms * rng.standard_normal(vin_norm.shape)
```

数学上：

```text
vin_sampled[n] = vin[n] + w_s[n]
w_s[n] ~ N(0, σ_s²)    独立同分布（每个样本一个噪声）

注意: 噪声在 bit trial 之前加入，所有 bit 看到的是同一个 vin_sampled[n]
      （和 comparator noise 不同，后者每个 bit 独立）
```

**和 comparator noise 的区别**：
```text
sampling noise:  在 bit trial 之前加入，所有 bit 共享同一个噪声
                 -> 等效于"输入信号本身有噪声"
                 -> 对 aout 的影响是线性的（aout = ideal + w_s）

comparator noise: 每个 bit trial 独立抽取噪声
                 -> 影响的是 bit decision（非线性）
                 -> 对 aout 的影响通过 bit 翻转（可能很大）
```

**residual 特征**（和 thermal noise 几乎一样）：

```text
PDF:    完美 Gaussian（KL ≈ 0）—— 因为是纯加性高斯噪声
ACF:    白噪声 δ[k]（样本间独立）
spectrum: 平坦 noise floor
```

**诊断意义**：sampling noise 在 residual 上和 thermal noise 完全一样——都是加性
高斯白噪声。单从 residual 分析**无法区分** sampling noise 和 thermal noise。
要区分需要：
- 改变 Cs（硬件层面，看 SNR 是否按 `√(kT/C)` 变化）
- 或看绝对量级（sampling noise 可从 Cs 和 T 算出，thermal noise 要测量）

**设计含义**：sampling noise 是 SAR ADC 的基本 SNR 限制。对一个 12-bit ADC，
full-scale = 1V：
```text
理想量化噪声:  LSB/√12 = (1/4096)/√12 ≈ 70 µV
要让它主导（sampling noise < 量化噪声）:
  √(kT/C) < 70 µV
  C > kT/(70µV)² = (4e-21)/(4.9e-9) ≈ 0.8 pF
```

所以 12-bit ADC 的采样电容至少 ~1 pF 才能让 sampling noise 不主导。这是 SAR ADC
设计的核心 tradeoff 之一（Cs 大 → 降噪但驱动难）。

### 5. Stage 03 → 04 衔接：用三件套诊断 SAR 非理想

把上面四个电路块和 Stage 03 的诊断工具对应起来：

```text
SAR 非理想              类别（Stage 03）   最敏感工具        能否校准
--------------------------------------------------------------------
CDAC mismatch           静态非线性(类2)    spectrum spur     ✓ deterministic
comparator noise        随机噪声(类1)      SNR/PDF           ✗ stochastic
sampling noise (kT/C)   随机噪声(类1)      SNR/PDF           ✗ stochastic
（DNL/INL from mismatch）静态非线性(类2)  by_value          ✓ deterministic
```

**诊断流程**（Stage 03 § 5 的 SAR 具体化）：
```text
1. 看 spectrum: 有 harmonic spur 吗?
   有 -> CDAC mismatch（看 spur 阶数判断哪个 bit）
   无 -> 噪声主导，进 2

2. 看 SNR vs SFDR:
   SFDR 差 + SNR 好 -> mismatch 主导（可校准）
   SFDR 好 + SNR 差 -> comparator/sampling noise 主导（不可校准）

3. 看 PDF:
   Gaussian -> 噪声主导
   有结构  -> mismatch（配合 spectrum 确认）

4. 校准后再测一次:
   SFDR 改善 -> 确认是 mismatch
   SNR 不变 -> 确认 noise 是 stochastic
```

这个流程在 whole_workflow demo 的 step_4 已经演示过：校准前 SFDR=91 dB（mismatch
导致 harmonic），校准后 SFDR=98.77 dB（mismatch 被修），但 SNR 几乎不变（noise
没被修）。这正是 Stage 03 诊断能力在 SAR 上的完整应用。


## 本库对应代码

SAR 模型：

```text
python/src/adctoolbox/models/sar.py
```

官方示例：

```text
python/src/adctoolbox/examples/02_spectrum/exp_s09_sar_fft_length_near_nyquist.py
python/src/adctoolbox/examples/05_debug_digital/exp_d15_sar_unit_cap_mismatch_uncal_spectra.py
python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
python/src/adctoolbox/examples/05_debug_digital/exp_d17_sar_msb_error_binary_vs_repeat_calibration.py
python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
```

本地学习脚本：

```text
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

## 对应 API

```python
from adctoolbox.models import sar_ideal_weights
from adctoolbox.models import sar_apply_cap_mismatch
from adctoolbox.models import sar_convert
from adctoolbox.models import sar_reconstruct
```

## 完整 SAR Modeling 代码——端到端示例

前面 § 数学 1-4 和 § 电路 1-5 分散讲了 SAR 的各个组件。这一节把它们串成一个
**可运行的完整流程**，展示从权重生成到频谱分析的全链路。这个示例是 Stage 04 所有
概念的集大成——理解它就理解了 SAR 建模。

### 完整代码（可直接运行）

```python
import numpy as np
from adctoolbox.models import (
    sar_ideal_weights, sar_apply_cap_mismatch,
    sar_convert, sar_reconstruct,
)
from adctoolbox import find_coherent_frequency, analyze_spectrum

# === 1. 生成理想权重（nominal）===
N_BITS = 12
nominal = sar_ideal_weights(N_BITS)
# -> [0.5, 0.25, ..., 1/2^12]，sum = 0.999756 (= 1 - 1 LSB)

# === 2. 加 cap mismatch（actual）===
rng = np.random.default_rng(42)              # 固定 seed 锁定一个"chip"
actual = sar_apply_cap_mismatch(nominal, sigma=0.005, rng=rng)
# sigma=0.005 = 0.5% 单位电容相对失配（真实量级）
# actual 是这个 chip 的真实物理权重（deterministic，每次转换相同）

# === 3. 生成输入信号 ===
Fs = 100e6; N = 8192
Fin, _ = find_coherent_frequency(fs=Fs, fin_target=10e6, n_fft=N)
t = np.arange(N) / Fs
vin = 0.45 * np.sin(2 * np.pi * Fin * t) + 0.5   # 单音 + DC offset
# full-scale = 1.0 (range [0, 1]), A=0.45 < 0.5 不 clip

# === 4. 三种转换场景（对应 § 数学 4 两套权重）===
# (a) 理想: nominal 转换 + nominal 重构（参考基准）
codes_ideal = sar_convert(vin, nominal)
aout_ideal  = sar_reconstruct(codes_ideal, nominal)

# (b) 未校准: actual 转换 + nominal 重构（数字端不知道 mismatch）
codes_actual = sar_convert(vin, actual)
aout_uncal   = sar_reconstruct(codes_actual, nominal)

# (c) 校准后: actual 转换 + actual 重构（假设数字端已知 actual）
aout_cal     = sar_reconstruct(codes_actual, actual)

# === 5. 频谱对比 ===
for name, aout in [('ideal', aout_ideal), ('uncal', aout_uncal), ('cal', aout_cal)]:
    r = analyze_spectrum(aout, fs=Fs, max_harmonic=5, create_plot=False)
    print(f'{name:6s}: SNDR={r["sndr_dbc"]:.2f}dB  SFDR={r["sfdr_dbc"]:.2f}dB  '
          f'THD={r["thd_dbc"]:.2f}dB  ENOB={r["enob"]:.2f}')
```

### 运行输出（实测）

```text
1. nominal weights: 12-bit, 前4位=[0.5, 0.25, 0.125, 0.0625], sum=0.999756
2. actual weights:  前4位=[0.50002, 0.24996, 0.12502, 0.06252], sum=0.999731
                   增益误差 = -0.002%（sum(actual) ≠ sum(nominal)，§ 数学 4）
3. 信号: Fin=9.9976MHz, N=8192, A=0.45, full-scale=1.0
4. codes shape: (8192, 12)    ← 8192 样本 × 12 bit
   翻转样本数: 896/8192 (10.9%)   ← 11% 样本的 bit decision 因 mismatch 改变
5. 频谱对比:
   ideal: SNDR=73.07dB  SFDR=95.13dB  THD=-105.37dB  ENOB=11.85
   uncal:  SNDR=72.38dB  SFDR=83.69dB  THD= -83.62dB  ENOB=11.73
   cal:    SNDR=73.07dB  SFDR=95.85dB  THD=-101.94dB  ENOB=11.85
```

### 输出解读——三个核心观察

**观察 1：未校准时 SFDR 明显变差，但 SNR 几乎不变**

```text
ideal -> uncal:
  SFDR: 95.13 -> 83.69 dB  (恶化 11.4 dB)  ← mismatch 产生 harmonic spur
  SNDR: 73.07 -> 72.38 dB  (恶化 0.7 dB)   ← 几乎不变
  THD:  -105  -> -84 dB    (恶化 21 dB)    ← harmonic 显著增强
```

这验证了 § 电路 2 的核心结论：**CDAC mismatch 产生 deterministic harmonic（影响
SFDR/THD），但不增加 noise floor（不影响 SNR）**。因为 mismatch 是 deterministic，
每次转换相同——它产生周期性失真（§ 3.5 的 harmonic 机制），不是随机噪声。

诊断含义：**SFDR 差但 SNR 好 → mismatch 主导**（Stage 03 § 5 诊断流程的 SAR 应用）。

**观察 2：校准后 SFDR 恢复到接近理想**

```text
uncal -> cal:
  SFDR: 83.69 -> 95.85 dB  (恢复 12.2 dB)  ← harmonic spur 被修掉
  SNDR: 72.38 -> 73.07 dB  (恢复 0.7 dB)   ← 接近理想
  ENOB: 11.73 -> 11.85     (恢复 0.12 bit) ← 接近理想 11.85
```

这验证了 § 数学 4.3 的校准原理：**用 actual weights 重构（`sar_reconstruct(codes,
actual)`）能补偿 mismatch**。校准的本质是"用数字权重复现转换时模拟域的真实累积"。

**观察 3：校准前后 SNR 几乎不变（0.7 dB）**

```text
注意 cal 的 SNDR (73.07) ≈ ideal 的 SNDR (73.07)
      uncal 的 SNDR (72.38) 也接近
```

SNR 主要由量化噪声 + sampling noise + comparator noise 决定，这些是 stochastic
（§ 电路 3/4）。**校准只修 deterministic mismatch，不修 stochastic noise**——所以
校准前后 SNR 几乎不变。这是 Stage 06 校准的核心局限。

### 三种场景的权重流（对应 § 数学 4）

```text
场景 a (ideal):    vin →[sar_convert, nominal]→ codes →[sar_reconstruct, nominal]→ aout
                  模拟域用 nominal, 数字域用 nominal → 无失真（参考基准）

场景 b (uncal):    vin →[sar_convert, actual] → codes →[sar_reconstruct, nominal]→ aout
                  模拟域用 actual（含 mismatch）, 数字域用 nominal（不知道 mismatch）
                  → mismatch 暴露成 harmonic

场景 c (cal):      vin →[sar_convert, actual] → codes →[sar_reconstruct, actual] → aout
                  模拟域用 actual, 数字域用 actual（校准估计出 actual）
                  → mismatch 被补偿
```

**关键**：`sar_convert` 和 `sar_reconstruct` 的 weights 参数是独立的——这正是
"两套权重"设计的体现。Stage 06 校准的核心任务就是**估计 actual weights**，让
场景 b 变成场景 c。

### 和 whole_workflow demo step_4 的关系

这个端到端示例就是 `whole_workflow_demo.py` 的 step_4 的精简版。demo 还包含：
- 信号生成（clean + nonideal）
- Stage 02 频谱分析
- Stage 03 residual 三件套
- Stage 05 bit 层诊断

但 **SAR 建模的核心就在这个示例里**——其它都是辅助分析。理解这 30 行代码，
就理解了 Stage 04 的全部建模逻辑。

## 实验 1：运行 SAR bit trial 学习脚本


```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\sar_adc_model_study.py
```

重点看控制台：

```text
SAR bit-trial trace for one sample
```

每一行对应一次 comparator decision。

## 实验 2：改变 capacitor mismatch

打开：

```text
learning/adctoolbox-learning/demos/sar_adc_model_study.py
```

修改：

```python
cap_mismatch_sigma: float = 0.0
```

然后改成：

```python
cap_mismatch_sigma: float = 0.002
cap_mismatch_sigma: float = 0.01
```

观察：

- SFDR 是否变差。
- calibration 是否能恢复一部分性能。

## 实验 3：改变 comparator noise

修改：

```python
comparator_noise_rms: float = 0.0
```

再改成：

```python
comparator_noise_rms: float = 100e-6
```

观察：

- SNR/ENOB 下降。
- calibration 对随机噪声改善有限。

## 本阶段代码阅读

读：

```text
python/src/adctoolbox/models/sar.py
```

重点看：

- `sar_ideal_weights`
- `sar_apply_cap_mismatch`
- `sar_convert`
- `sar_reconstruct`

尤其是 `sar_convert` 中这段逻辑：

```text
v_test = v_dac + weights[j]
bit = vin_norm + noise >= v_test
v_dac = where(bit, v_test, v_dac)
```

建议你按这个顺序给自己讲出来：

```text
1. sar_ideal_weights 生成 nominal_weights
2. sar_apply_cap_mismatch 生成 actual_weights
3. sar_convert 用 actual_weights 产生 bits
4. sar_reconstruct 用 digital_weights 重构 aout
```

关键问题是第 3 步和第 4 步可以使用不同权重：

```text
转换时用 actual analog weights
重构时用 nominal/calibrated digital weights
```

这正是后面校准能发挥作用的地方。

## 容易混淆的点

- `actual_weights` 不是“真实答案输出”，它是模拟 CDAC 的实际权重。
- `nominal_weights` 是数字端以为 ADC 应该有的理想权重。
- mismatch 会先影响 bit decision，再影响数字重构；校准只能修正可由数字权重补偿的部分。
- comparator noise 是每次比较时的随机扰动，不是一个固定权重误差。
- `cap_mismatch_sigma=0.002` 表示相对失配量级，不是 ENOB 直接下降 0.002 bit。

## 阶段检查问题

1. SAR ADC 为什么从 MSB 开始 trial？
2. 为什么 actual weights 和 nominal weights 不一致会产生失真？
3. capacitor mismatch 和 comparator noise 哪个更适合校准？
4. `sar_convert` 输出的 bits 是什么 shape？
5. `sar_reconstruct(bits, weights)` 中的 weights 是模拟权重还是数字重构权重？

