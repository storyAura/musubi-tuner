> generated_by: nexus-mapper v2
> verified_at: 2026-07-30
> provenance: Domain definitions are derived from AST-backed code structure and manually verified CLI/workflow behavior; no Git history is available.

# 核心领域概念

## Architecture

模型家族与变体的组合。当前 UI 范围是 12 个家族：HunyuanVideo、Wan、FramePack、HunyuanVideo 1.5、FLUX.1 Kontext、FLUX.2、Qwen-Image、Z-Image、HiDream-O1、Ideogram4、Kandinsky5、Krea2。变体会改变必填模型文件、数据集能力、缓存格式、训练扩展和推理参数。

## Workflow

用户可启动的顶层动作：`cache_latents`、`cache_text_encoder_outputs`、`train_network`、`full_finetune`、`inference`、`convert`、`merge`、`extract`、`post_hoc_ema`、`caption`。并非每个 Architecture 都支持每个 Workflow。

## Capability

由 Architecture、variant 和 Workflow 共同决定的字段集合、默认值、choices、条件规则、危险操作、产物类型及可用网络模块。未来 UI 必须从后端 Capability Registry 渲染，不能只按架构名切换少量硬编码表单。

## Dataset Blueprint

数据集配置的运行时模型。用户文件结构是 `{general, datasets[]}`；dataset 条目根据图像或视频键自动判型，并应用 dataset → general → argparse → runtime → dataclass default 的回退顺序。

## Cache

训练前生成的 safetensors 数据。潜变量缓存名含分辨率与架构，文本缓存名含架构和 `_te`。旧缓存默认可能被删除，因此 UI 需要“清理计划 → 用户确认 → 执行”的明确边界。

## Training Configuration

公共 120 参数、架构扩展、动态 model-version helper、Accelerate launch 配置和网络模块参数的合成结果。TOML 配置会把各 section 展平到一个 argparse namespace。

## Job

一次可追踪的长任务。当前仓库没有这一领域对象；目标实现至少需要 `job_id`、类型、架构、变体、不可变请求快照、状态、PID/进程组、开始/结束时间、退出信息和产物引用。

## Event

Job 的有序结构化输出，包括阶段、进度、训练指标、日志、告警、检查点、样本、外部上传结果与错误。stdout 只能作为原始日志来源，不能作为唯一状态接口。

## Artifact

缓存、训练状态、safetensors 检查点、样本图像/视频/latent、TensorBoard 日志、转换结果和远端上传记录。Artifact 应记录来源 Job、路径、类型、大小、创建时间和可选校验值。

## Secret Reference

W&B API key 与 Hugging Face token 的非明文引用。UI 请求、持久化配置、命令预览和日志中都不应包含秘密原值。
