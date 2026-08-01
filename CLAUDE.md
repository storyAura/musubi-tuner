# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 必读上下文

- `.nexus-map/INDEX.md` 是本仓库的知识索引,**其中的「强制执行步骤」要求在动手前读完 `.nexus-map/arch/*.md` 与 `.nexus-map/concepts/domains.md`**(高密度摘要,总量 <5000 tokens)。
- `MUSUBI_TUNER_UI_ADAPTATION_HANDOFF.md` 是 Web UI 与训练器之间的 API 契约与逐架构参数台账(925 个 CLI 参数、12 架构的变体/扩展/跨字段规则),UI/后端改动前先查它。

## 常用命令

```bash
# 训练器本体(Python ≥3.10;torch 需自装 CUDA 版)
pip install -e .
python -m pytest tests/test_save_precision.py -q   # 单个测试模块

# Web UI 后端(FastAPI,端口 8787 本地 / 6006 云端)
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8787
python -m pytest backend/test_smoke.py -q          # 含真实子进程生命周期测试

# Web UI 前端(frontend/ 目录)
npm run dev      # vite,/api 代理到 :8787
npm test         # vitest DOM 冒烟(挂载、页面切换、状态机、capability 门控)
npm run build    # dist/ 相对路径构建;dist 提交进仓库(云端无 node)

# 一键启动(首次运行自动装依赖,marker 在 backend/.runtime/setup_done)
start.bat        # Windows,:8787
bash start.sh    # Linux/AutoDL(conda python、学术加速、:6006、清理孤儿下载进程)
```

## 大图架构

**训练器本体**(上游 kohya-ss/musubi-tuner):产品边界是 CLI + TOML + 文件系统,无 API。
仓库根的 57 个四行包装器 → `src/musubi_tuner/*.py` 真实入口。核心汇聚点:

- `src/musubi_tuner/dataset/config_utils.py` — 数据集 Schema 唯一权威(29 个反向依赖);回退顺序 dataset → general → argparse → runtime → dataclass default;**每个 dataset 的缓存目录必须唯一**;缓存器默认删除未被当前数据集引用的旧缓存(`--keep_cache` 保留)。
- `src/musubi_tuner/training/parser_common.py` — 120 个公共训练参数,16 个 `_add_*` 组合成;各架构入口再叠加自己的扩展参数。
- `src/musubi_tuner/training/trainer_base.py` — 训练编排/循环/保存;`--network_module` 经 importlib 动态加载 `networks/` 下的 LoRA/LoHa/LoKr。
- 12 架构族(qwen-image、wan2.1/2.2、hunyuan-video(-1.5)、framepack、flux.1-kontext、flux.2、z-image、hidream-o1、ideogram4、kandinsky5、krea2),每族有独立的 cache_latents / cache_text / train_network(部分有 full_finetune)入口。

**Web UI**(本 fork 新增,storyAura/musubi-tuner 的 `webui-test`/`main` 分支):

- `backend/`(FastAPI,`/api/v1/*`):
  - `capability.py` — 架构→入口脚本/变体枚举/LoRA 模块/文本编码器 flag 名的映射表 + argv 渲染(**服务器选入口、argv 列表、shell=False**);`MODEL_CATALOG` 是 12 架构官方权重清单(文件名/大小逐一经 HF API 实测,fp8 量化不收录);多模型库目录扫描(`model_roots`)。
  - `jobs.py` — 内存作业表 + 单 worker 串行子进程(cwd=仓库根、`PYTHONPATH=src`);stdout/stderr 按 `\r`/`\n` 切行,tqdm 训练进度行解析为结构化 progress 事件;SSE 重放历史+实时;取消 = CTRL_BREAK/SIGTERM 温和 5s 后强杀进程树。作业不持久化(重启即失,orphaned 对账待做)。
  - `download_model.py` — 独立下载子进程:route=auto 时并行 Range 实测 HF 直连/hf-mirror/魔搭三源速度,按速度排序(gated/不可达得 0 分垫底),**已有断点缓存的源系优先**(HF 系与魔搭缓存不互通);魔搭下载带断线自动重连;进度以 `[dlprog] {json}` 行发出,由 jobs.py 转为 progress 事件(不进日志)。代理规则:HF 直连用环境代理,mirror/魔搭强制直连(`set_proxies` 可恢复切换)。
  - `settings.py` — `backend/.runtime/settings.json` 原子写;token 只存本机,API 只回脱敏(`*_set`/`*_hint`),注入子进程走环境变量(HF_TOKEN 等),**绝不进 argv/日志/响应**。
  - dataset_config 未填时由 `main.py:generate_dataset_toml` 按 config_utils Schema 生成多数据集 TOML(多数据集共享缓存基目录时自动分配 ds1/ds2… 子目录)。
- `frontend/`(Vite + Vue 3,无 Pinia/router,内联样式):
  - `src/store.js` — 单一 reactive store + 全部动作。**双模式**:默认真实模式(空态/真实 API/诚实报错);`?demo=1` 启用演示沙盘(种子假数据 + 模拟训练引擎)。所有假数据必须锁在 `demo.demoMode` 门控内——冒烟测试断言真实模式页面不得出现 `RTX 4090`/`character-v1` 等演示值。
  - 下载与训练**状态分离**:训练/缓存作业走 `store.status` 状态机与训练页失败面板;模型下载走 `store.downloads`(按 filename),进度条显示在模型页条目和侧栏 DOWNLOADS 块,失败绝不进训练失败面板。
  - `src/derived.js` — 表单 10 组字段定义(变体/任务字段按 `ARCH_VARIANTS` 条件渲染,全量微调仅 4 架构显示)、队列行、TOML/argv 预览。`ARCH_VARIANTS`/`FULL_FINETUNE_ARCHS` 前后端各一份,**改动必须两侧同步**(store.js ↔ backend/capability.py)。
  - 视觉规范:`frontend/docs/LoRA训练器UI设计规范.md`(Vercel 式黑白极简;唯一彩色 #0070f3 蓝、成功无绿色、mono 标注一切技术信息、字重上限 600)。

## 部署与分支约定

- 云端(AutoDL):单进程部署——`main.py` 挂载 `frontend/dist` 静态托管,`bash start.sh` 起 uvicorn 于 0.0.0.0:6006(面板入口 WebUI-6006)。模型放数据盘:设置页可添加存储目录(与 ComfyUI models 子目录同构:diffusion_models/text_encoders/vae/clip_vision)并切换默认下载位置。
- 前端改动后必须 `npm run build` 并连同 `frontend/dist` 一起提交(云端无 node)。
- 推送目标是 fork `storyAura/musubi-tuner`:`webui-test` 为工作分支,完成后 fast-forward 合并进 `main`,两分支保持同步。**不向上游 kohya-ss 提 PR。**
- AutoDL 的 SSH/网络不稳:git 操作套 `timeout` 并重试;学术加速用 `source /etc/network_turbo`(会设代理 env,访问 hf-mirror/魔搭前需剥掉)。SSH 网关对频繁连接会限流(banner EOF),SFTP 传大文件易被截断——**部署 dist 首选云端 `git fetch && git reset --hard origin/webui-test`**;SSH 全断时 AutoDL 控制台的 JupyterLab 终端是不走 SSH 网关的独立通道。

## 易踩的坑

- FastAPI 端点凡触碰 `jobs.manager` 必须是 `async def`(普通 def 跑线程池,`loop.create_task` 不会唤醒事件循环,worker 永远不启动)。
- 服务重启会杀掉运行中作业的子进程(输出管道断裂),`start.sh` 已顺带清理孤儿下载进程(它们握着 HF 文件锁会卡死同文件新下载);下载均可断点续传。
- 官方文档有已证实的笔误(Qwen VAE 所在仓库、FLUX.2 klein 文件名),`MODEL_CATALOG` 以 HF API 实测为准——新增模型条目前先用 API 核实文件名与大小,不要照抄 docs。
- 前端测试用全文 `toContain` 断言,新增 UI 文案容易撞词(如"全量微调"/"训练类型"出现在 hint 里会误伤按架构隐藏字段的断言)。
- dist 静态文件传输后必须**校验字节数**:半截的 JS 会让页面白屏且无报错;上游 .gitignore 排除 CLAUDE.md,fork 里用 `git add -f` 跟踪(勿改上游 .gitignore,避免合并冲突)。
