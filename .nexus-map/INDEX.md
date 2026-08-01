> generated_by: nexus-mapper v2
> verified_at: 2026-07-30
> provenance: AST-backed for all 278 Python files; workflow semantics and GUI subprocess calls were additionally verified by manual inspection; Git history is unavailable in this snapshot.

# Musubi Tuner 项目知识索引

Musubi Tuner 是一个以命令行脚本为产品边界的多架构 LoRA/微调训练器。仓库包含 57 个顶层包装入口、12 个模型架构族，以及潜变量缓存、文本编码器缓存、网络训练、部分架构全量微调、推理和权重工具链。

当前存在 `src/musubi_tuner/gui/` Gradio 原型，但它不是完整前端：没有包级启动入口或 GUI 测试，只支持 Qwen-Image 与 Z-Image-Turbo，并由界面直接拼接 shell 命令。完整 UI 适配研究见仓库根目录 `MUSUBI_TUNER_UI_ADAPTATION_HANDOFF.md`。

## 核心边界

- `src/musubi_tuner/dataset/`：共享数据集 Schema、图像/视频数据集、缓存路径和加载规则；`config_utils.py` 被 29 个模块引用。
- `src/musubi_tuner/training/`：120 个公共训练参数、Accelerate 初始化、训练循环、指标、采样、保存与恢复。
- `src/musubi_tuner/networks/`：架构 LoRA 以及 LoHa/LoKr 网络模块和格式转换器。
- `src/musubi_tuner/*_cache_*.py`：架构缓存适配器。
- `src/musubi_tuner/*_train*.py`：网络训练或全量微调适配器。
- `src/musubi_tuner/*_generate_*.py`：图像/视频推理入口。
- `src/musubi_tuner/gui/`：有限且未发布的 Gradio 原型，不应视为稳定 API。

## 已验证规模

- AST：278 个 Python 文件、87,156 行、3,500 节点、5,148 条关系、0 个解析错误、无截断。
- CLI：扫描 `src/musubi_tuner` 下 208 个 Python 文件，65 个文件声明接口，共 925 个 `add_argument` 声明、360 个唯一参数标记、10 个位置参数。
- 测试：13 个测试模块、1,913 行；未发现 GUI、任务生命周期或全架构入口覆盖。
- Git：仓库快照没有 `.git`，因此变更热点、作者和共变耦合均为 unknown。

## 证据入口

- `.nexus-map/raw/ast_nodes.json`：完整 Python AST 图。
- `.nexus-map/raw/cli_arguments.json`：参数级机器台账，含文件、作用域、行号、类型、默认值、choices、required、help 与 UI 控件提示。
- `.nexus-map/concepts/concept_model.json`：系统级机器图谱。
- `MUSUBI_TUNER_UI_ADAPTATION_HANDOFF.md`：UI 适配的完整人工交接。

## [操作指南] 强制执行步骤

> 本节是对所有读取本文件的 AI 发出的硬性操作指令，不是建议。

### 步骤1 — 必须先读完以下所有文件（顺序不限）

读完本文件后，在执行任何任务之前，必须依次 read 以下文件完整内容：

- `.nexus-map/arch/systems.md` — 系统边界与代码位置
- `.nexus-map/arch/dependencies.md` — 系统间依赖关系与 Mermaid 图
- `.nexus-map/arch/test_coverage.md` — 测试面与证据缺口
- `.nexus-map/hotspots/git_forensics.md` — Git 热点与耦合风险
- `.nexus-map/concepts/domains.md` — 核心领域概念

> 这些文件均为高密度摘要，总量通常 < 5000 tokens，是必要的上下文成本。
> 不得以"任务简单"或"只改一个文件"为由跳过。

### 步骤2 — 按任务类型追加操作（步骤1 完成后执行）

- 若任务涉及**接口修改、新增跨模块调用、删除/重命名公共函数**：
  → 必须运行 `query_graph.py --impact <目标文件>` 确认影响半径后再写代码。
- 若任务需要**判断某文件被谁引用**：
  → 运行 `query_graph.py --who-imports <模块名>`。
- 若仓库结构已发生重大变化（新增系统、重构模块边界）：
  → 任务完成后评估是否需要重新运行 nexus-mapper 更新知识库。
