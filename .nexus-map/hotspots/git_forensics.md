> generated_by: nexus-mapper v2
> verified_at: 2026-07-30
> provenance: Git analysis is unavailable because this repository snapshot has no .git directory; structural hotspots below are AST-backed and are not change-frequency claims.

# Git 热点与耦合风险

## 降级说明

仓库根目录没有 `.git`，因此无法确认：

- 最近 90 天提交数与作者数。
- 文件变更频率和真实热点。
- 文件共变次数与耦合分数。
- 当前快照对应的分支、提交或远端。

`.nexus-map/raw/git_stats.json` 明确记录了该降级，不应把下面的结构热点描述成 Git 热点。

## 结构热点

| 文件/区域 | 结构证据 | 风险 |
|---|---|---|
| `dataset/image_video_dataset.py` | 43 个模块导入 | 缓存命名、数据集发现和训练输入的广泛公共依赖 |
| `dataset/config_utils.py` | 29 个模块导入 | 修改 Schema 或回退顺序会影响几乎全部缓存和多种训练入口 |
| `training/trainer_base.py` | 2,202 行，训练主循环与扩展缝合点 | 任务事件、取消、保存和外部集成都汇聚于此 |
| `training/parser_common.py` | 120 个公共 CLI 参数 | 字段重命名或默认值变化会同时影响多个架构 |
| `gui/gui.py` | 1,134 行，UI/I/O/命令/进程混合 | 虽无反向导入，但当前原型的职责耦合很高 |
| 架构推理脚本 | Wan/FramePack/HV1.5 等高 fan-out | 每个脚本自行维护参数与交互模式，统一 UI 适配容易漂移 |

## 恢复完整 Git 分析的条件

获得带 `.git` 的原始克隆后，重新运行 `git_detective.py`，再用 `query_graph.py --impact <path> --git-stats .nexus-map/raw/git_stats.json` 复核结构边界和高风险文件。
