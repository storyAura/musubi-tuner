> generated_by: nexus-mapper v2
> verified_at: 2026-07-30
> provenance: AST-backed for Python boundaries and import relationships; subprocess-based workflow calls and release-surface conclusions were verified by manual inspection; Git history is unavailable.

# 系统边界

## 1. 工作流入口层

**位置**：`src/musubi_tuner/` 与仓库根目录 57 个四行包装器。

**职责**：把架构选择和工作流选择映射到具体 `argparse` 接口。覆盖潜变量或像素缓存、文本缓存、LoRA/LoHa/LoKr 网络训练、部分全量微调、图像/视频推理和权重工具。

**关键事实**：

- 网络训练普遍组合 `training/parser_common.py` 的 120 个公共参数与架构扩展。
- 缓存脚本组合 `cache_latents.py` 或 `cache_text_encoder_outputs.py` 的公共参数与架构扩展。
- 推理脚本各自维护参数面，部分复用 HunyuanVideo 的六个 compile 参数。
- `flux_2_train_network_self_flow.py` 只有 `src/` 入口，没有顶层包装器。

## 2. 数据集与缓存层

**位置**：`src/musubi_tuner/dataset/`、`src/musubi_tuner/cache_latents.py`、`src/musubi_tuner/cache_text_encoder_outputs.py`。

**职责**：校验 `{general, datasets[]}` 配置，解析图像或视频数据集，应用 dataset → general → argparse → runtime → dataclass default 的优先级，并生成架构化缓存。

**影响半径**：`dataset/config_utils.py` 有 29 个反向依赖，是全架构 UI 数据集编辑器必须复用的真实 Schema 权威。

**危险行为**：除非传入 `--keep_cache`，缓存流程会删除当前数据集中未引用的旧缓存文件。

## 3. 训练运行时

**位置**：`src/musubi_tuner/training/`。

**职责**：公共参数、Accelerate 初始化、数据集构建、DiT 与网络装载、优化器和调度器、训练循环、采样、指标、检查点、状态保存及外部追踪。

**关键入口**：

- `parser_common.py:35-783`：公共参数组。
- `trainer_base.py:1332-1397`：训练编排。
- `trainer_base.py:1399-1440`：公共校验。
- `trainer_base.py:1552-1633`：动态网络导入和装配。
- `trainer_base.py:1938-2202`：进度、训练循环、采样与保存。

**UI 缺口**：运行时没有结构化任务状态、取消令牌、事件流或持久化作业注册表；可观测性目前是 stdout、`tqdm` 和 tracker。

## 4. 网络适配层

**位置**：`src/musubi_tuner/networks/`。

**职责**：各架构 LoRA、通用 LoHa/LoKr、权重加载、合并、保存及 ComfyUI 转换。

**关键事实**：

- `--network_module` 由 `importlib.import_module` 动态加载。
- 网络 API 同时支持 `create_arch_network` 与 LyCORIS 风格 `create_network`。
- Kandinsky5 不支持 LoHa/LoKr。
- `merge_lora.py` 只支持标准 LoRA；`convert_lora.py` 支持 LoRA/LoHa/LoKr 的 Musubi 与 Diffusers 格式转换。

## 5. 外部集成与产物层

**位置**：`src/musubi_tuner/utils/`、`training/accelerator_setup.py`、`training/trainer_base.py`。

**职责**：TensorBoard/W&B、Hugging Face 上传、SAI 元数据、训练状态、检查点和样本产物。

**关键事实**：

- W&B API key 和 Hugging Face token 属于秘密字段。
- tracker 配置会过滤秘密和本地路径，但 GUI 当前仍会回显完整命令。
- Hugging Face 异步上传在线程中执行，上传异常只记录日志，调用方没有结构化结果。

## 6. Gradio GUI 原型

**位置**：`src/musubi_tuner/gui/`。

**职责**：为 Qwen-Image 和 Z-Image-Turbo 提供单页项目初始化、简单数据集 TOML、缓存、训练和 Z-Image 转换。

**边界判断**：

- `pyproject.toml` 只有可选 `gui` 依赖，没有 `project.scripts` 或 `project.gui-scripts`。
- 没有根目录 GUI 包装器，也没有 GUI 测试。
- `gui.py` 直接负责配置 I/O、参数拼接、shell 执行和 Windows 控制台启动。
- 该目录应作为需求样例与迁移来源，不应作为未来稳定后端。
