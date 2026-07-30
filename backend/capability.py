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
