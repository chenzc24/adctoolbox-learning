# ADCToolbox 代码库基本框架

本文档解释 `E:\ADCToolbox` 这个代码库的基本结构。目标是帮助新手知道：

- 哪些目录是源码
- 哪些目录是示例和文档
- 哪些目录是测试和参考数据
- 想做 ADC 建模、分析、校准时应该从哪里开始

## 顶层目录

```text
E:\ADCToolbox
├── README.md                 # 项目总说明：安装、快速开始、功能概览
├── CHANGELOG.md              # 版本变化记录
├── CD_SETUP_GUIDE.md         # 持续交付/发布相关说明
├── AGENTS.md                 # 给 Codex/Agent 的仓库操作说明
├── ADCToolbox.prj            # MATLAB 项目入口
├── python/                   # Python 版本源码、测试、文档
├── matlab/                   # MATLAB 版本源码、测试、工具箱包
├── docs/                     # 顶层设计/规划文档和图片资源
├── reference_dataset/        # 参考输入数据
├── reference_output/         # MATLAB 或黄金参考输出
├── resources/                # 本地资源目录，已被 git 忽略
└── agent_playground/         # 本地实验区，已被 git 忽略
```

## Python 子项目

Python 子项目是当前最适合学习和运行 demo 的入口。

```text
python/
├── pyproject.toml            # Python 包配置和依赖
├── uv.lock                   # uv 锁定依赖版本
├── README.md                 # Python 包说明
├── src/adctoolbox/           # Python 源码
├── tests/                    # Python 测试
└── docs/                     # Sphinx 文档源码
```

运行 Python 脚本时，建议从 `python/` 目录执行：

```powershell
cd E:\ADCToolbox\python
uv run python <script.py>
```

这样 `uv` 会使用 `python/.venv` 和本地包源码。

## Python 源码结构

```text
python/src/adctoolbox/
├── __init__.py               # 顶层公共 API 汇总
├── fundamentals/             # 频率、单位、SNR/ENOB/NSD、FoM 等基础工具
├── spectrum/                 # FFT 频谱分析
├── aout/                     # analog output 波形误差分析
├── dout/                     # digital output 位矩阵分析
├── calibration/              # ADC 位权重校准
├── models/                   # SAR ADC 行为模型
├── siggen/                   # 信号和非理想效应生成
├── timeinterleave/           # 时间交织 ADC 工具
├── oversampling/             # 过采样/NTF 分析
├── toolset/                  # 一键 dashboard 工作流
├── examples/                 # 打包给用户运行的示例
└── _bundled_skills/          # Codex 技能包源码
```

## MATLAB 子项目

```text
matlab/
├── README.md                 # MATLAB 版本说明
├── setupLib.m                # 把 matlab/src 加入 MATLAB path
├── src/                      # MATLAB 工具函数
├── tests/                    # MATLAB 测试脚本
├── data_generation/          # MATLAB 参考数据生成脚本
└── toolbox/                  # 打包好的 .mltbx 工具箱
```

MATLAB 中可先运行：

```matlab
addpath(genpath('E:\ADCToolbox\matlab\src'))
```

然后使用 `plotspec`、`sinfit`、`inlsin`、`adcpanel` 等函数。

## 测试与参考数据

```text
python/tests/unit/            # 单元测试：函数级别
python/tests/integration/     # 集成测试：完整工作流
python/tests/compare/         # Python 与 MATLAB 输出对比
reference_dataset/            # 输入参考数据
reference_output/             # MATLAB 参考输出 CSV
```

当前仓库部分测试仍使用旧导入路径，例如 `adctoolbox.common`，所以学习时应优先运行官方示例和 playground 脚本，而不是直接把全量测试当作学习入口。

## 示例系统

官方示例位于：

```text
python/src/adctoolbox/examples/
```

可以复制到个人工作目录：

```powershell
cd E:\ADCToolbox\python
uv run adctoolbox-get-examples C:\Users\90590\adctoolbox_examples
```

示例分类：

| 目录 | 内容 |
|---|---|
| `01_basic/` | 环境检查、相干采样基础 |
| `02_spectrum/` | FFT、频谱、窗口函数、近 Nyquist 分析 |
| `03_generate_signals/` | 生成带噪声、抖动、非线性等非理想信号 |
| `04_debug_analog/` | 模拟输出误差、PDF、ACF、INL/DNL、相位分析 |
| `05_debug_digital/` | SAR 位权重校准、bit activity、overflow、ENOB sweep |
| `06_use_toolsets/` | 一键 dashboard |
| `07_conversions/` | 单位、SNR、NSD、FoM 转换 |
| `08_time_interleave/` | 时间交织 ADC |
| `09_downsample/` | 下采样和混叠 |

## 本地学习目录

本次整理后的学习目录是：

```text
agent_playground/adctoolbox_learning/
```

其中：

```text
demos/                      # 可运行脚本
guides/                     # 学习说明
outputs/                    # 生成结果
repo_framework/             # 当前代码库框架说明
```

这是推荐的学习和临时实验位置，因为它已被 `.gitignore` 忽略。
