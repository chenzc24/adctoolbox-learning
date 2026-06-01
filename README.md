# ADCToolbox Learning Workspace

这个目录用于本地学习和实验，位于：

```text
E:\ADCToolbox\learning\adctoolbox-learning
```

它和 ADCToolbox 主源码分开，用来放学习路径、demo、读码笔记和输出结果。不要把个人学习实验直接写进 `python/src/adctoolbox/`，除非你明确要贡献源码。

## 目录

```text
adctoolbox-learning/
├── demos/            # 可运行的学习脚本
├── guides/           # 面向新手的流程说明
├── learner/          # 个人学习笔记
├── outputs/          # 脚本生成的图片、CSV、NPZ 数据
├── repo_framework/   # ADCToolbox 代码框架和模块功能说明
└── staged_course/    # 分阶段课程
```

## 推荐阅读顺序

1. `repo_framework/README.md`：先了解代码库整体结构。
2. `repo_framework/MODULE_FUNCTION_MAP.md`：再看各模块能做什么。
3. `repo_framework/LEARNING_PATH.md`：了解从新手到能改实验的总路线。
4. `staged_course/overview.md`：按 8 个阶段系统学习 ADC 建模、分析、校准和验证。
5. `guides/theory_to_practice_adc_learning_path.md`：按理论 + 实践路线学习。
6. `guides/whole_workflow_guide.md`：学习完整 ADC 分析流程。
7. `demos/whole_workflow_demo.py`：运行完整闭环。
8. `demos/sar_adc_model_study.py`：单独学习 SAR ADC 建模。

## 运行完整流程

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\whole_workflow_demo.py
```

## 运行 SAR ADC 建模学习脚本

```powershell
cd E:\ADCToolbox\python
uv run python ..\learning\adctoolbox-learning\demos\sar_adc_model_study.py
```

输出会写入：

```text
E:\ADCToolbox\learning\adctoolbox-learning\outputs\
```

`outputs/` 是可再生成结果；长期版本管理的内容是：

```text
demos/
guides/
repo_framework/
staged_course/
learner/
```

## 当前学习主线

```text
Stage 00: Python 数值仿真基础
Stage 01: ADC 基础、采样、量化、LSB
Stage 02: FFT 和动态性能指标
Stage 03: 正弦拟合和 residual 误差分析
Stage 04: SAR ADC 行为建模
Stage 05: bit matrix 数字诊断
Stage 06: sine-based 位权重校准
Stage 07: 校准验证、模型边界与工程严谨性
```

这条路线的目标是：先能解释模型，再能运行实验，最后能判断实验结论是否可信。
