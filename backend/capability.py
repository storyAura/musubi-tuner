"""架构能力表与 argv 渲染 — MUSUBI_TUNER_UI_ADAPTATION_HANDOFF.md 的最小实现。

只允许服务器选择入口脚本;客户端提交结构化字段,这里渲染成 argv 列表(shell=False)。
秘密字段(wandb_api_key / huggingface_token)一律不进 argv,待秘密引用层实现后再接。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 变体/任务枚举(交接文档 §8.2;与 frontend/src/store.js 的 ARCH_VARIANTS 保持一致)
ARCH_VARIANTS: dict[str, list[dict]] = {
    "qwen-image": [{"label": "训练类型", "flag": "model_version",
                    "options": ["original", "layered", "edit", "edit-2509", "edit-2511"]}],
    "flux.2": [{"label": "训练类型", "flag": "model_version",
                "options": ["klein-4b", "klein-base-4b", "klein-9b", "klein-base-9b", "dev"]}],
    "wan2.1/2.2": [{"label": "任务", "flag": "task",
                    "options": ["t2v-14B", "t2v-1.3B", "i2v-14B", "t2i-14B", "flf2v-14B", "t2v-1.3B-FC",
                                "t2v-14B-FC", "i2v-14B-FC", "i2v-A14B", "t2v-A14B"]}],
    "hunyuan-video-1.5": [{"label": "任务", "flag": "task", "options": ["t2v", "i2v"]}],
    "hidream-o1": [
        {"label": "模型类型", "flag": "model_type", "options": ["full", "dev"]},
        {"label": "任务", "flag": "task", "options": ["t2i", "i2i"]},
    ],
    "kandinsky5": [{"label": "任务", "flag": "task", "options": [
        "k5-lite-t2i-hd", "k5-lite-i2i-hd", "k5-lite-t2v-5s-sd", "k5-lite-t2v-10s-sd", "k5-lite-i2v-5s-sd",
        "k5-pro-t2v-5s-sd", "k5-pro-t2v-5s-hd", "k5-pro-t2v-10s-sd", "k5-pro-t2v-10s-hd",
        "k5-pro-i2v-5s-sd", "k5-pro-i2v-5s-hd",
        "k5-lite-t2v-5s-distil-sd", "k5-lite-t2v-10s-distil-sd", "k5-lite-t2v-5s-nocfg-sd",
        "k5-lite-t2v-10s-nocfg-sd", "k5-lite-t2v-5s-pretrain-sd", "k5-lite-t2v-10s-pretrain-sd",
    ]}],
}

TRAIN_ENTRY = {
    "hunyuan-video": "hv_train_network", "wan2.1/2.2": "wan_train_network", "framepack": "fpack_train_network",
    "hunyuan-video-1.5": "hv_1_5_train_network", "flux.1-kontext": "flux_kontext_train_network",
    "flux.2": "flux_2_train_network", "qwen-image": "qwen_image_train_network", "z-image": "zimage_train_network",
    "hidream-o1": "hidream_o1_train_network", "ideogram4": "ideogram4_train_network",
    "kandinsky5": "kandinsky5_train_network", "krea2": "krea2_train_network",
}
FULL_FINETUNE_ENTRY = {
    "hunyuan-video": "hv_train", "qwen-image": "qwen_image_train",
    "z-image": "zimage_train", "hidream-o1": "hidream_o1_train",
}
CACHE_LATENTS_ENTRY = {
    "hunyuan-video": "cache_latents", "wan2.1/2.2": "wan_cache_latents", "framepack": "fpack_cache_latents",
    "hunyuan-video-1.5": "hv_1_5_cache_latents", "flux.1-kontext": "flux_kontext_cache_latents",
    "flux.2": "flux_2_cache_latents", "qwen-image": "qwen_image_cache_latents", "z-image": "zimage_cache_latents",
    "hidream-o1": "hidream_o1_cache_pixel", "ideogram4": "ideogram4_cache_latents",
    "kandinsky5": "kandinsky5_cache_latents", "krea2": "krea2_cache_latents",
}
CACHE_TEXT_ENTRY = {
    "hunyuan-video": "cache_text_encoder_outputs", "wan2.1/2.2": "wan_cache_text_encoder_outputs",
    "framepack": "fpack_cache_text_encoder_outputs", "hunyuan-video-1.5": "hv_1_5_cache_text_encoder_outputs",
    "flux.1-kontext": "flux_kontext_cache_text_encoder_outputs", "flux.2": "flux_2_cache_text_encoder_outputs",
    "qwen-image": "qwen_image_cache_text_encoder_outputs", "z-image": "zimage_cache_text_encoder_outputs",
    "hidream-o1": "hidream_o1_cache_text_encoder_outputs", "ideogram4": "ideogram4_cache_text_encoder_outputs",
    "kandinsky5": "kandinsky5_cache_text_encoder_outputs", "krea2": "krea2_cache_text_encoder_outputs",
}
LORA_MODULE = {
    "hunyuan-video": "networks.lora", "wan2.1/2.2": "networks.lora_wan", "framepack": "networks.lora_framepack",
    "hunyuan-video-1.5": "networks.lora_hv_1_5", "flux.1-kontext": "networks.lora_flux",
    "flux.2": "networks.lora_flux_2", "qwen-image": "networks.lora_qwen_image", "z-image": "networks.lora_zimage",
    "hidream-o1": "networks.lora_hidream_o1", "ideogram4": "networks.lora_ideogram4",
    "kandinsky5": "networks.lora_kandinsky", "krea2": "networks.lora_krea2",
}

# 文本编码器 CLI flag 名按架构不同(交接文档 §7.3/§9);UI 目前是单 TE 表单字段
TEXT_ENCODER_FLAG = {
    "hunyuan-video": "text_encoder1", "framepack": "text_encoder1", "flux.1-kontext": "text_encoder1",
    "wan2.1/2.2": "t5", "kandinsky5": "text_encoder_qwen",
}

# 公共训练参数(parser_common.py 120 参数中表单已覆盖的部分;值为空则省略)
TRAIN_STR_KEYS = [
    "dataset_config", "dit", "vae", "vae_dtype", "dit_dtype",
    "optimizer_type", "learning_rate", "max_grad_norm",
    "lr_scheduler", "lr_warmup_steps", "lr_scheduler_num_cycles", "lr_scheduler_min_lr_ratio",
    "max_train_epochs", "max_train_steps", "seed", "gradient_accumulation_steps",
    "mixed_precision", "save_precision",
    "timestep_sampling", "discrete_flow_shift", "weighting_scheme", "min_timestep", "max_timestep",
    "blocks_to_swap",
    "save_every_n_epochs", "save_every_n_steps", "save_last_n_epochs",
    "output_dir", "output_name", "logging_dir", "resume",
]
TRAIN_BOOL_KEYS = [
    "fp8_base", "fp8_scaled", "fp8_llm", "gradient_checkpointing",
    "use_pinned_memory_for_block_swap", "split_attn", "img_in_txt_in_offloading",
    "save_state", "save_state_on_train_end",
]
# HunyuanVideo 全量微调是 legacy parser(交接文档 §7.4),以下公共 flag 它没有
HV_LEGACY_MISSING = {"fp8_base", "fp8_scaled", "save_precision", "use_pinned_memory_for_block_swap"}
ATTN_MODES = {"sdpa", "flash_attn", "flash3", "xformers", "sage_attn"}
# qwen/flux.2 的缓存入口接受 --model_version(交接文档 §9)
CACHE_VARIANT_ARCHS = {"qwen-image", "flux.2"}


def _te_flag(arch: str) -> str:
    return TEXT_ENCODER_FLAG.get(arch, "text_encoder")


def _clean(values: dict) -> dict:
    return {k: v for k, v in (values or {}).items() if v is not None}


def entry_script(entry: str) -> str:
    return str(Path("src") / "musubi_tuner" / f"{entry}.py")


def render_train_argv(arch: str, workflow: str, values: dict, sample_prompts_path: str | None) -> list[str]:
    """渲染训练 argv。返回完整命令列表(argv[0] 为 python 解释器)。"""
    v = _clean(values)
    is_ft = workflow == "full_finetune"
    entries = FULL_FINETUNE_ENTRY if is_ft else TRAIN_ENTRY
    if arch not in entries:
        raise ValueError(f"architecture {arch!r} does not support workflow {workflow!r}")
    script = entry_script(entries[arch])

    args: list[str] = []

    for vd in ARCH_VARIANTS.get(arch, []):
        val = v.get(vd["flag"])
        if val:
            if val not in vd["options"]:
                raise ValueError(f"invalid {vd['flag']}={val!r} for {arch}")
            args += [f"--{vd['flag']}", str(val)]

    attn = v.get("attn_mode") or "sdpa"
    if attn not in ATTN_MODES:
        raise ValueError(f"invalid attn_mode {attn!r}")
    args.append(f"--{attn}")

    te = v.get("text_encoder")
    if te:
        args += [f"--{_te_flag(arch)}", str(te)]

    if not is_ft:
        module = {"loha": "networks.loha", "lokr": "networks.lokr"}.get(
            v.get("network_module", "standard_lora"), LORA_MODULE[arch])
        args += ["--network_module", module]
        for k in ("network_dim", "network_alpha", "network_dropout", "scale_weight_norms"):
            if v.get(k) not in (None, ""):
                args += [f"--{k}", str(v[k])]
        if v.get("network_args"):
            args += ["--network_args", *str(v["network_args"]).split()]
        if v.get("network_weights"):
            args += ["--network_weights", str(v["network_weights"])]
        if v.get("dim_from_weights") is True:
            args.append("--dim_from_weights")

    hv_legacy = is_ft and arch == "hunyuan-video"
    for k in TRAIN_STR_KEYS:
        if hv_legacy and k in HV_LEGACY_MISSING:
            continue
        if k == "logging_dir" and v.get("log_with") in (None, "", "none"):
            continue
        if v.get(k) not in (None, ""):
            args += [f"--{k}", str(v[k])]
    if v.get("log_with") and v["log_with"] != "none":
        args += ["--log_with", str(v["log_with"])]
        # tensorboard/all 必须有 logging_dir;留空默认 logs(cwd=仓库根,即训练器目录下)
        if v["log_with"] != "wandb" and not v.get("logging_dir"):
            args += ["--logging_dir", "logs"]
    if v.get("optimizer_args"):
        args += ["--optimizer_args", *str(v["optimizer_args"]).split()]
    for k in TRAIN_BOOL_KEYS:
        if hv_legacy and k in HV_LEGACY_MISSING:
            continue
        if v.get(k) is True:
            args.append(f"--{k}")

    if sample_prompts_path:
        args += ["--sample_prompts", sample_prompts_path]
        for k in ("sample_every_n_epochs", "sample_every_n_steps"):
            if str(v.get(k) or "") not in ("", "0"):
                args += [f"--{k}", str(v[k])]
        if v.get("sample_at_first") is True:
            args.append("--sample_at_first")

    mp = v.get("mixed_precision") or "no"
    return [sys.executable, "-m", "accelerate.commands.launch",
            "--num_cpu_threads_per_process", "1", "--mixed_precision", mp, script, *args]


def render_cache_argv(kind: str, arch: str, values: dict, keep_cache: bool) -> list[str]:
    """渲染缓存 argv。kind: latents | text"""
    v = _clean(values)
    entries = CACHE_LATENTS_ENTRY if kind == "latents" else CACHE_TEXT_ENTRY
    if arch not in entries:
        raise ValueError(f"unknown architecture {arch!r}")
    script = entry_script(entries[arch])

    args: list[str] = []
    if not v.get("dataset_config"):
        raise ValueError("dataset_config is required")
    args += ["--dataset_config", str(v["dataset_config"])]

    if kind == "latents":
        if v.get("vae"):
            args += ["--vae", str(v["vae"])]
    else:
        te = v.get("text_encoder")
        if te:
            args += [f"--{_te_flag(arch)}", str(te)]

    if arch in CACHE_VARIANT_ARCHS and v.get("model_version"):
        args += ["--model_version", str(v["model_version"])]
    if keep_cache:
        args.append("--keep_cache")

    return [sys.executable, script, *args]


def build_sample_prompt_text(values: dict) -> str | None:
    """由表单采样字段生成 sample_prompts 文本(training/sampling_prompts.py 的行语法)。"""
    v = _clean(values)
    prompt = str(v.get("sample_prompt") or "").strip().replace("\n", " ")
    if not prompt:
        return None
    parts = [prompt]
    neg = str(v.get("sample_negative_prompt") or "").strip().replace("\n", " ")
    if neg:
        parts.append(f"--n {neg}")
    for key, flag in (("sample_w", "w"), ("sample_h", "h"), ("sample_steps", "s"), ("sample_seed", "d")):
        val = str(v.get(key) or "").strip()
        if val:
            parts.append(f"--{flag} {val}")
    return " ".join(parts) + "\n"


# ---- 模型库(全 12 架构清单 + 一键下载 + 自动选择) ----
# 所有文件名与大小均经 hf-mirror/HF API 实测核对(2026-07-31),不收录纯猜测条目;
# fp8/nvfp4 量化版不可用于训练故不收录(Ideogram4 例外:官方仅发布 fp8_scaled)。
# 官方文档两处笔误已按实测纠正:Qwen VAE 实际在 Qwen-Image_ComfyUI;
# FLUX.2 klein 文件名为 flux-2-klein-*(文档误写 flux2-klein-*)。
MODELS_DIR = REPO_ROOT / "models"
ROLE_SUBDIR = {
    "dit": "diffusion_models", "dit_high_noise": "diffusion_models", "unconditional_dit": "diffusion_models",
    "text_encoder": "text_encoders", "text_encoder2": "text_encoders", "byt5": "text_encoders",
    "clip": "text_encoders", "vae": "vae", "image_encoder": "clip_vision",
}

_QWEN = "Comfy-Org/Qwen-Image_ComfyUI"
_QWEN_EDIT = "Comfy-Org/Qwen-Image-Edit_ComfyUI"
_QWEN_LAYERED = "Comfy-Org/Qwen-Image-Layered_ComfyUI"
_HV_PACK = "Comfy-Org/HunyuanVideo_repackaged"
_WAN21 = "Comfy-Org/Wan_2.1_ComfyUI_repackaged"
_WAN22 = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged"
_WAN_AI = "Wan-AI/Wan2.1-I2V-14B-720P"
_HV15 = "tencent/HunyuanVideo-1.5"
_HV15_PACK = "Comfy-Org/HunyuanVideo_1.5_repackaged"
_GATED = "BFL gated 仓库:需在 HF 页面接受协议并配置 token,下载失败时请手动下载"

# 条目:role, repo, file, size_mb;可选 variants(适用变体,缺省=全部)、note、optional
MODEL_CATALOG: dict[str, list[dict]] = {
    "hunyuan-video": [
        dict(role="dit", repo="tencent/HunyuanVideo",
             file="hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt", size_mb=24454),
        dict(role="vae", repo="tencent/HunyuanVideo",
             file="hunyuan-video-t2v-720p/vae/pytorch_model.pt", size_mb=940),
        dict(role="text_encoder", repo=_HV_PACK,
             file="split_files/text_encoders/llava_llama3_fp16.safetensors", size_mb=15326),
        dict(role="text_encoder2", repo=_HV_PACK,
             file="split_files/text_encoders/clip_l.safetensors", size_mb=234),
    ],
    "wan2.1/2.2": [
        dict(role="dit", repo=_WAN21, file="split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors",
             size_mb=2706, variants=["t2v-1.3B"]),
        dict(role="dit", repo=_WAN21, file="split_files/diffusion_models/wan2.1_t2v_14B_bf16.safetensors",
             size_mb=27253, variants=["t2v-14B", "t2i-14B"]),
        dict(role="dit", repo=_WAN21, file="split_files/diffusion_models/wan2.1_i2v_720p_14B_bf16.safetensors",
             size_mb=31270, variants=["i2v-14B"]),
        dict(role="dit", repo=_WAN21, file="split_files/diffusion_models/wan2.1_flf2v_720p_14B_fp16.safetensors",
             size_mb=31273, variants=["flf2v-14B"]),
        dict(role="dit", repo=_WAN22, file="split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp16.safetensors",
             size_mb=27253, variants=["t2v-A14B"]),
        dict(role="dit_high_noise", repo=_WAN22,
             file="split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp16.safetensors",
             size_mb=27253, variants=["t2v-A14B"]),
        dict(role="dit", repo=_WAN22, file="split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp16.safetensors",
             size_mb=27254, variants=["i2v-A14B"]),
        dict(role="dit_high_noise", repo=_WAN22,
             file="split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp16.safetensors",
             size_mb=27254, variants=["i2v-A14B"]),
        dict(role="text_encoder", repo=_WAN_AI, file="models_t5_umt5-xxl-enc-bf16.pth", size_mb=10835,
             note="T5(--t5)"),
        dict(role="clip", repo=_WAN_AI, file="models_clip_open-clip-xlm-roberta-large-vit-huge-14.pth",
             size_mb=4551, note="Wan2.1 I2V 训练需要;2.2 不需要", optional=True),
        dict(role="vae", repo=_WAN21, file="split_files/vae/wan_2.1_vae.safetensors", size_mb=242),
    ],
    "framepack": [
        dict(role="dit", repo="Kijai/HunyuanVideo_comfy", file="FramePackI2V_HY_bf16.safetensors", size_mb=24555),
        dict(role="vae", repo="hunyuanvideo-community/HunyuanVideo",
             file="vae/diffusion_pytorch_model.safetensors", size_mb=940),
        dict(role="text_encoder", repo=_HV_PACK,
             file="split_files/text_encoders/llava_llama3_fp16.safetensors", size_mb=15326),
        dict(role="text_encoder2", repo=_HV_PACK,
             file="split_files/text_encoders/clip_l.safetensors", size_mb=234),
        dict(role="image_encoder", repo="Comfy-Org/sigclip_vision_384",
             file="sigclip_vision_patch14_384.safetensors", size_mb=816),
    ],
    "hunyuan-video-1.5": [
        dict(role="dit", repo=_HV15, file="transformer/720p_t2v/diffusion_pytorch_model.safetensors",
             size_mb=31763, variants=["t2v"]),
        dict(role="dit", repo=_HV15, file="transformer/720p_i2v/diffusion_pytorch_model.safetensors",
             size_mb=31763, variants=["i2v"]),
        dict(role="vae", repo=_HV15, file="vae/diffusion_pytorch_model.safetensors", size_mb=4808),
        dict(role="text_encoder", repo=_HV15_PACK,
             file="split_files/text_encoders/qwen_2.5_vl_7b.safetensors", size_mb=15816),
        dict(role="byt5", repo=_HV15_PACK,
             file="split_files/text_encoders/byt5_small_glyphxl_fp16.safetensors", size_mb=418),
        dict(role="image_encoder", repo=_HV15_PACK,
             file="split_files/clip_vision/sigclip_vision_patch14_384.safetensors", size_mb=816,
             variants=["i2v"], note="I2V 需要"),
    ],
    "flux.1-kontext": [
        dict(role="dit", repo="black-forest-labs/FLUX.1-Kontext-dev", file="flux1-kontext-dev.safetensors",
             size_mb=22700, note=_GATED),
        dict(role="vae", repo="black-forest-labs/FLUX.1-Kontext-dev", file="ae.safetensors",
             size_mb=319, note=_GATED),
        dict(role="text_encoder", repo="comfyanonymous/flux_text_encoders",
             file="t5xxl_fp16.safetensors", size_mb=9334, note="T5-XXL(--text_encoder1)"),
        dict(role="text_encoder2", repo="comfyanonymous/flux_text_encoders",
             file="clip_l.safetensors", size_mb=234),
    ],
    "flux.2": [
        dict(role="dit", repo="black-forest-labs/FLUX.2-dev", file="flux2-dev.safetensors",
             size_mb=61461, variants=["dev"], note=_GATED),
        dict(role="dit", repo="black-forest-labs/FLUX.2-klein-4B", file="flux-2-klein-4b.safetensors",
             size_mb=7392, variants=["klein-4b"]),
        dict(role="dit", repo="black-forest-labs/FLUX.2-klein-base-4B", file="flux-2-klein-base-4b.safetensors",
             size_mb=7392, variants=["klein-base-4b"]),
        dict(role="dit", repo="black-forest-labs/FLUX.2-klein-9B", file="flux-2-klein-9b.safetensors",
             size_mb=17316, variants=["klein-9b"]),
        dict(role="dit", repo="black-forest-labs/FLUX.2-klein-base-9B", file="flux-2-klein-base-9b.safetensors",
             size_mb=17316, variants=["klein-base-9b"]),
        dict(role="vae", repo="black-forest-labs/FLUX.2-dev", file="ae.safetensors", size_mb=320, note=_GATED),
        dict(role="text_encoder", repo="Comfy-Org/z_image",
             file="split_files/text_encoders/qwen_3_4b.safetensors", size_mb=7672,
             variants=["klein-4b", "klein-base-4b"], note="Qwen3 4B,与 Z-Image 共用"),
    ],
    "qwen-image": [
        dict(role="dit", repo=_QWEN, file="split_files/diffusion_models/qwen_image_bf16.safetensors",
             size_mb=38968, variants=["original"]),
        dict(role="dit", repo=_QWEN_EDIT, file="split_files/diffusion_models/qwen_image_edit_bf16.safetensors",
             size_mb=38968, variants=["edit"]),
        dict(role="dit", repo=_QWEN_EDIT, file="split_files/diffusion_models/qwen_image_edit_2509_bf16.safetensors",
             size_mb=38968, variants=["edit-2509"]),
        dict(role="dit", repo=_QWEN_EDIT, file="split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors",
             size_mb=38968, variants=["edit-2511"]),
        dict(role="dit", repo=_QWEN_LAYERED, file="split_files/diffusion_models/qwen_image_layered_bf16.safetensors",
             size_mb=38968, variants=["layered"]),
        dict(role="text_encoder", repo=_QWEN, file="split_files/text_encoders/qwen_2.5_vl_7b.safetensors",
             size_mb=15816),
        dict(role="vae", repo=_QWEN, file="split_files/vae/qwen_image_vae.safetensors", size_mb=242,
             variants=["original", "edit", "edit-2509", "edit-2511"]),
        dict(role="vae", repo=_QWEN_LAYERED, file="split_files/vae/qwen_image_layered_vae.safetensors",
             size_mb=242, variants=["layered"]),
    ],
    "z-image": [
        dict(role="dit", repo="Comfy-Org/z_image", file="split_files/diffusion_models/z_image_bf16.safetensors",
             size_mb=11739),
        dict(role="vae", repo="Comfy-Org/z_image", file="split_files/vae/ae.safetensors", size_mb=319),
        dict(role="text_encoder", repo="Comfy-Org/z_image",
             file="split_files/text_encoders/qwen_3_4b.safetensors", size_mb=7672),
    ],
    "hidream-o1": [
        dict(role="dit", repo="Comfy-Org/HiDream-O1-Image", file="checkpoints/hidream_o1_image_bf16.safetensors",
             size_mb=15607, variants=["full"]),
        dict(role="dit", repo="Comfy-Org/HiDream-O1-Image",
             file="checkpoints/hidream_o1_image_dev_bf16.safetensors", size_mb=15607, variants=["dev"],
             note="统一模型:无独立 VAE/TE,文本缓存亦从 DiT 加载"),
    ],
    "ideogram4": [
        dict(role="dit", repo="Comfy-Org/Ideogram-4", file="diffusion_models/ideogram4_fp8_scaled.safetensors",
             size_mb=8850, note="官方仅发布 fp8_scaled 格式"),
        dict(role="unconditional_dit", repo="Comfy-Org/Ideogram-4",
             file="diffusion_models/ideogram4_unconditional_fp8_scaled.safetensors", size_mb=8850,
             optional=True, note="推理/非对称 CFG 用"),
        dict(role="text_encoder", repo="Comfy-Org/Ideogram-4",
             file="text_encoders/qwen3vl_8b_fp8_scaled.safetensors", size_mb=10098),
        dict(role="vae", repo="Comfy-Org/Ideogram-4", file="vae/flux2-vae.safetensors", size_mb=320),
    ],
    "kandinsky5": [
        dict(role="dit", repo="kandinskylab/Kandinsky-5.0-T2V-Pro-sft-5s",
             file="model/kandinsky5pro_t2v_sft_5s.safetensors", size_mb=41376,
             variants=["k5-pro-t2v-5s-sd", "k5-pro-t2v-5s-hd"],
             note="其余 task 的 DiT 见 kandinskylab collection 各仓库 model/ 目录"),
        dict(role="vae", repo="hunyuanvideo-community/HunyuanVideo",
             file="vae/diffusion_pytorch_model.safetensors", size_mb=940),
    ],
    "krea2": [
        dict(role="dit", repo="krea/Krea-2-Raw", file="raw.safetensors", size_mb=25065, note="RAW,训练用"),
        dict(role="dit", repo="krea/Krea-2-Turbo", file="turbo.safetensors", size_mb=25065,
             optional=True, note="Turbo(--turbo_dit),推理/采样用"),
        dict(role="vae", repo=_QWEN, file="split_files/vae/qwen_image_vae.safetensors", size_mb=242,
             note="与 Qwen-Image 共用"),
        dict(role="text_encoder", repo="Comfy-Org/Qwen3-VL",
             file="text_encoders/qwen3vl_4b_bf16.safetensors", size_mb=8464),
    ],
}
# 单文件形式不存在、需手动准备的组件(如实列出,不提供假下载):
# - FLUX.2 dev 的 Mistral 3 TE 与 klein-9b 系 TE:官方仓库多分片
# - Kandinsky5 的 Qwen2.5-VL / CLIP:HF 目录格式
# - Wan Fun-Control(FC 变体)DiT:alibaba-pai 仓库多分片


def model_roots() -> list[Path]:
    """模型库目录:训练器内置 + 设置中的额外目录(如 ComfyUI 的 models)。"""
    from .settings import load
    roots = [MODELS_DIR]
    for d in load().get("model_dirs", []):
        s = str(d).strip()
        if s:
            roots.append(Path(s))
    return roots


def default_download_root() -> Path:
    from .settings import load
    d = (load().get("default_model_dir") or "").strip()
    return Path(d) if d else MODELS_DIR


def _entry_public(arch: str, e: dict) -> dict:
    filename = e["file"].rsplit("/", 1)[-1]
    sub = ROLE_SUBDIR[e["role"]]
    found = None
    for root in model_roots():  # 任一目录里有即算就绪;local_path 指向实际所在处
        p = root / sub / filename
        if p.is_file():
            found = p
            break
    target = default_download_root() / sub / filename
    return {
        "architecture": arch, "role": e["role"], "filename": filename,
        "repo": e["repo"], "remote_file": e["file"], "size_mb": e["size_mb"],
        "variants": e.get("variants"), "note": e.get("note", ""), "optional": bool(e.get("optional")),
        "exists": found is not None, "local_path": str(found or target),
    }


def model_catalog_for(arch: str, variant: str) -> list[dict]:
    """该架构+当前变体适用的清单(变体不匹配的条目不出现)。"""
    out = []
    for e in MODEL_CATALOG.get(arch, []):
        vs = e.get("variants")
        if vs is not None and variant not in vs:
            continue
        out.append(_entry_public(arch, e))
    return out


def model_catalog_all() -> list[dict]:
    """全部架构的完整清单(按架构分组)。"""
    return [{"id": arch, "entries": [_entry_public(arch, e) for e in entries]}
            for arch, entries in MODEL_CATALOG.items()]


def find_catalog_entry(arch: str, filename: str) -> dict | None:
    for e in MODEL_CATALOG.get(arch, []):
        if e["file"].rsplit("/", 1)[-1] == filename:
            return _entry_public(arch, e)
    return None


def capabilities_payload() -> dict:
    archs = sorted(set(TRAIN_ENTRY))
    return {
        "architectures": [
            {
                "id": a,
                "variants": ARCH_VARIANTS.get(a, []),
                "workflows": ["train_network"] + (["full_finetune"] if a in FULL_FINETUNE_ENTRY else []),
                "text_encoder_flag": _te_flag(a),
                "entries": {
                    "train_network": TRAIN_ENTRY[a],
                    **({"full_finetune": FULL_FINETUNE_ENTRY[a]} if a in FULL_FINETUNE_ENTRY else {}),
                    "cache_latents": CACHE_LATENTS_ENTRY[a],
                    "cache_text": CACHE_TEXT_ENTRY[a],
                },
            } for a in archs
        ],
    }
