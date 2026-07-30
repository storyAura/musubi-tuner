# musubi tuner Web UI

黑白极简开发者工具风(Vercel 体系定制)的 LoRA 训练器 Web UI:
**Vite + Vue 3 前端** + **FastAPI 作业后端**(`../backend/`),直接驱动本仓库的
musubi-tuner 训练/缓存入口脚本。交互契约遵循
`../MUSUBI_TUNER_UI_ADAPTATION_HANDOFF.md`,视觉遵循
[`docs/LoRA训练器UI设计规范.md`](docs/LoRA训练器UI设计规范.md)。

```
浏览器 UI ──HTTP/SSE──▶ backend (FastAPI :8787)
                          │  渲染 argv(shell=False,秘密不入参)
                          ▼
                accelerate launch src/musubi_tuner/<arch>_train_network.py …
                          │  stdout/stderr 逐行回流,tqdm 进度解析为结构化事件
                          ▼
                日志 / step / avr_loss / 状态机(queued→running→succeeded|failed|cancelled)
```

## 启动(两个进程)

```bash
# 1. 作业后端(仓库根目录;需先 pip install -e . 装好训练依赖)
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8787

# 2. 前端(frontend/ 目录)
npm install
npm run dev        # http://localhost:5173(/api 自动代理到 :8787)
```

其他命令:`npm run build`(产物 dist/,相对路径可直开)、`npm test`(DOM 冒烟)、
`python -m pytest backend/test_smoke.py`(后端 + 真实子进程生命周期)。

## 已实现的真实能力

- **提交训练**:表单(公共 120 参数中的常用面)→ 前端即时校验(与后端同源的跨字段规则)
  → `POST /api/v1/jobs/train` → 后端按 `architecture + workflow` 选入口脚本、渲染 argv
  列表(`shell=False`)→ `accelerate launch` 真实子进程(`PYTHONPATH=src`,cwd=仓库根)
- **实时监控**:SSE(`/api/v1/jobs/{id}/events`)回流日志与进度;kohya/tqdm 进度行解析为
  step / total / avr_loss / it/s,驱动进度条与 loss 曲线(后端只解析 avr_loss,曲线两线同值,
  不编造原始损失)
- **取消**:确认弹窗 → `POST /jobs/{id}/cancel` → 先 CTRL_BREAK 温和终止,5s 后强杀进程树
- **缓存作业**:latents / 文本编码器缓存(`--keep_cache` 经确认弹窗显式选择)
- **训练中采样**:表单的提示词/尺寸/步数/种子序列化为 `--sample_prompts` 文件
- **环境诊断**:GPU/显存/驱动(nvidia-smi,5s 刷新,顶栏与环境页同源)、python/torch/
  accelerate 探测;后端掉线自动降级(WebGL 读 GPU 名 + 明确「未连接」提示)
- **变体/任务字段按架构条件显示**(前端 `ARCH_VARIANTS` 与后端 `backend/capability.py`
  同表);全量微调仅对有入口的 4 个架构开放,HunyuanVideo legacy parser 差异已过滤
- **秘密安全**:`wandb_api_key` / `huggingface_token` 从不进入请求、argv 与日志

## URL 参数

| 参数 | 取值 | 说明 |
|---|---|---|
| `demo` | `1` | 演示沙盘:种子数据 + 模拟训练引擎(默认关闭,生产使用无需理会) |
| `theme` | `light` / `dark` | 初始主题 |
| `showAdvanced` | `true` | 默认展开全部高级参数 |
| `accent` | 颜色值 | 覆盖蓝色档位(默认亮 `#0070f3` / 暗 `#3291ff`) |

## 结构

```
frontend/src/
  api.js                后端客户端(fetch + SSE;提交前剔除秘密字段)
  store.js              全局状态 + 动作;真实模式走后端,?demo=1 走模拟引擎
  derived.js            表单 10 组字段、队列行、TOML/argv 预览
  App.vue + pages/ + components/   页面与组件(见各文件头注释)
backend/
  main.py               FastAPI 路由(/api/v1/environment|capabilities|jobs…)
  jobs.py               作业管理器:子进程、日志/进度解析、SSE、两段式取消
  capability.py         架构入口/变体/LoRA 模块映射与 argv 渲染
  test_smoke.py         含真实子进程生命周期的冒烟测试
```

## 已知边界(如实声明)

- 作业表存内存,后端重启不恢复(交接文档的持久化 Job Store 与 orphaned 对账待做)
- 队列页的历史来自本会话;跨会话作业列表待接 `GET /api/v1/jobs` 轮询
- 模型区是单 Text Encoder 表单;双 TE 架构(HunyuanVideo/FramePack/FLUX.1-Kontext)与
  Wan CLIP 等扩展参数待 Capability Registry 驱动的动态表单
- 缓存删除的精确文件预览待 `POST /api/v1/cache/cleanup-plan`
- 产物索引、预设持久化、TOML 导入导出待后端对应端点
