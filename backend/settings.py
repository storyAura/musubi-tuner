"""设置持久化(backend/.runtime/settings.json,gitignore 内,只存训练机本地)。

秘密纪律:API 响应一律脱敏(仅返回是否已设置 + 尾 4 位);token 通过环境变量
注入作业子进程,绝不进入 argv、日志或版本库。结构为平面 JSON,新设置项直接加键。
"""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent / ".runtime" / "settings.json"
SECRET_KEYS = ("hf_token", "modelscope_token")
ROUTES = ("auto", "hf", "mirror", "modelscope")
DEFAULTS = {"hf_token": "", "modelscope_token": "", "download_route": "auto"}


def load() -> dict:
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    return {**DEFAULTS, **data}


def save(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SETTINGS_PATH)  # 原子替换,写入中断不损坏原文件


def redacted() -> dict:
    d = load()
    out = {k: v for k, v in d.items() if k not in SECRET_KEYS}
    for k in SECRET_KEYS:
        v = d.get(k) or ""
        out[k + "_set"] = bool(v)
        out[k + "_hint"] = ("····" + v[-4:]) if len(v) >= 8 else ""
    return out


def update(patch: dict) -> dict:
    d = load()
    route = patch.get("download_route")
    if route in ROUTES:
        d["download_route"] = route
    for k in SECRET_KEYS:
        if k in patch and patch[k] is not None:  # 缺省=不动;"" = 清除;值 = 更新
            d[k] = str(patch[k]).strip()
    save(d)
    return redacted()


def token_env() -> dict:
    """作业子进程的秘密环境变量(hf_hub_download 自动识别 HF_TOKEN)。"""
    d = load()
    env = {}
    if d.get("hf_token"):
        env["HF_TOKEN"] = d["hf_token"]
    if d.get("modelscope_token"):
        env["MODELSCOPE_API_TOKEN"] = d["modelscope_token"]
    return env
