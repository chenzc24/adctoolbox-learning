# ADCToolbox Learning Workspace

这个目录用于本地学习和实验，位于 `agent_playground/` 下，已经被
`.gitignore` 忽略，不会进入源码提交。

## 目录

```text
adctoolbox_learning/
├── demos/            # 可运行的学习脚本
├── guides/           # 面向新手的流程说明
├── outputs/          # 脚本生成的图片、CSV、NPZ 数据
└── repo_framework/   # 本代码库的框架和模块功能说明
```

## 推荐阅读顺序

1. `repo_framework/README.md`：先了解代码库整体结构。
2. `repo_framework/MODULE_FUNCTION_MAP.md`：再看各模块能做什么。
3. `staged_course/overview.md`：按 6 个阶段系统学习 ADC 建模、分析、校准。
4. `guides/theory_to_practice_adc_learning_path.md`：按理论+实践路径系统学习。
5. `guides/whole_workflow_guide.md`：学习完整 ADC 分析流程。
6. `demos/whole_workflow_demo.py`：运行完整流程。
7. `demos/sar_adc_model_study.py`：单独学习 SAR ADC 建模。

## 运行完整流程

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\whole_workflow_demo.py
```

## 运行 SAR ADC 建模学习脚本

```powershell
cd E:\ADCToolbox\python
uv run python ..\agent_playground\adctoolbox_learning\demos\sar_adc_model_study.py
```

输出会写入：

```text
E:\ADCToolbox\agent_playground\adctoolbox_learning\outputs\
```

`outputs/` 是可再生成结果，学习仓库默认不跟踪它；长期版本管理的内容是
`demos/`、`guides/`、`repo_framework/`、`staged_course/` 和个人笔记。
