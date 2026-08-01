> generated_by: nexus-mapper v2
> verified_at: 2026-07-30
> provenance: Test inventory and imports are AST/text-backed; tests were intentionally not executed during this repository-mapping task.

# 静态测试覆盖

## 已发现测试面

仓库有 13 个 `tests/test_*.py` 模块，共 1,913 行。

| 测试文件 | 主要静态覆盖 |
|---|---|
| `test_grad_metrics.py` | `NetworkTrainer` 梯度指标 |
| `test_ideogram4_autoencoder.py` | Ideogram4 AutoEncoder |
| `test_ideogram4_fp8_loading.py` | Ideogram4 FP8 与 LoRA 装载 |
| `test_ideogram4_lora_sampling.py` | Ideogram4 采样策略 |
| `test_ideogram4_synthetic.py` | Ideogram4 解析、缓存、采样、网络合成路径 |
| `test_ideogram4_te_fp8_loading.py` | Ideogram4 文本编码器 FP8 |
| `test_ideogram4_timesteps.py` | 公共 parser 与 Ideogram4 timestep |
| `test_krea2_gather_valid_text.py` | Krea2 文本收集 |
| `test_krea2_timesteps.py` | Krea2 timestep 与训练工具 |
| `test_lora_dtype_bridging.py` | LoRA dtype bridge |
| `test_sai_model_spec.py` | SAI 元数据 |
| `test_save_precision.py` | 公共 parser 与保存精度 |
| `test_top_level_entrypoints.py` | 仅 3 个 Ideogram4 顶层包装器 |

## UI 适配证据缺口

- 未发现 `src/musubi_tuner/gui/` 测试。
- 未发现统一 CLI 参数 Schema 快照或 57 个顶层包装器的完整契约测试。
- 未发现真实子进程任务生命周期测试：启动、并发拒绝、取消、强制终止、退出码、日志顺序和重启恢复。
- 未发现所有 12 个架构族的“缓存 → 训练 → 样本/检查点”最小集成测试。
- 未发现数据集可视化、缓存删除预览、秘密脱敏、Hugging Face/W&B 失败传播或产物索引测试。
- 未发现桌面或 Web UI 的稳定 ID、可访问性与端到端测试。

## 推荐验收门

1. 参数注册表与实际 parser 的全量差异测试，覆盖 925 个声明和动态 helper 参数。
2. 每个架构至少一条不加载大模型的 parser/validation 集成测试。
3. 使用真实短生命周期子进程验证 job 状态、事件序列、取消和错误正文。
4. 使用临时真实文件系统验证数据集配置、缓存清理计划和产物索引。
5. GUI 以稳定 `test-id`/accessibility ID 做关键路径 E2E，不以可见文本定位。

## 本次未运行测试

本次任务的目标是只读结构研究和 Markdown 交接，且 nexus-mapper 默认禁止执行目标仓库测试。因此这里只能确认静态测试面，不能把任何测试标记为当前通过。
