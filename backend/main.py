"""musubi tuner UI 的最小作业后端(交接文档 Phase 1 的 MVP)。

启动:  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8787
契约:  路径与 MUSUBI_TUNER_UI_ADAPTATION_HANDOFF.md §5.2 对齐。
安全:  只监听 loopback;入口脚本由服务器按架构选择;argv 为列表(shell=False);
        秘密字段(wandb_api_key / huggingface_token)从不进入 argv 与响应。
"""
from __future__ import annotations

import importlib.metadata
import platform
import subprocess
import sys
from pathlib import Path

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .capability import (
    TRAIN_ENTRY, FULL_FINETUNE_ENTRY, REPO_ROOT, MODELS_DIR, ROLE_SUBDIR,
    build_sample_prompt_text, capabilities_payload, find_catalog_entry,
    model_catalog_all, model_catalog_for, render_cache_argv, render_train_argv,
)
from .jobs import Job, manager
from . import settings as settings_store

RUNTIME_DIR = Path(__file__).resolve().parent / ".runtime"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    manager.bind_loop(asyncio.get_running_loop())
    yield


app = FastAPI(title="musubi tuner ui backend", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


# ---- 请求模型 ----

class TrainRequest(BaseModel):
    architecture: str
    workflow: str = "train_network"
    values: dict = Field(default_factory=dict)


class CacheRequest(BaseModel):
    architecture: str
    values: dict = Field(default_factory=dict)
    keep_cache: bool = False


# ---- 诊断 ----

@app.get("/api/v1/health")
def health():
    return {"ok": True, "repo_root": str(REPO_ROOT)}


def _pkg_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


@app.get("/api/v1/environment")
def environment():
    gpus = []
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version,compute_cap",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if out.returncode == 0:
            for line in out.stdout.strip().splitlines():
                name, total, used, driver, compute = [s.strip() for s in line.split(",")]
                gpus.append({"name": name, "memory_total_mb": int(float(total)),
                             "memory_used_mb": int(float(used)), "driver": driver, "compute_cap": compute})
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return {
        "gpus": gpus,
        "python": platform.python_version(),
        "torch": _pkg_version("torch"),
        "accelerate": _pkg_version("accelerate"),
        "musubi_tuner_src": (REPO_ROOT / "src" / "musubi_tuner").is_dir(),
    }


@app.get("/api/v1/capabilities")
def capabilities():
    return capabilities_payload()


# ---- 设置(token 脱敏、下载线路等;存于训练机 backend/.runtime/settings.json) ----

class SettingsPatch(BaseModel):
    hf_token: str | None = None
    modelscope_token: str | None = None
    download_route: str | None = None


@app.get("/api/v1/settings")
async def get_settings():
    return settings_store.redacted()


@app.put("/api/v1/settings")
async def put_settings(patch: SettingsPatch):
    data = patch.model_dump(exclude_unset=True)
    if "download_route" in data and data["download_route"] not in settings_store.ROUTES:
        raise HTTPException(422, f"invalid download_route {data['download_route']!r}")
    return settings_store.update(data)


# ---- 模型库 ----

class DownloadRequest(BaseModel):
    architecture: str
    filename: str


def _library_files() -> dict:
    files = {}
    for sub in sorted(set(ROLE_SUBDIR.values())):
        d = MODELS_DIR / sub
        files[sub] = sorted(f.name for f in d.iterdir() if f.is_file()) if d.is_dir() else []
    return files


@app.get("/api/v1/models")
async def list_models(architecture: str, model_version: str = ""):
    return {
        "models_dir": str(MODELS_DIR),
        "catalog": model_catalog_for(architecture, model_version),
        "files": _library_files(),
    }


@app.get("/api/v1/models/all")
async def list_all_models():
    return {
        "models_dir": str(MODELS_DIR),
        "architectures": model_catalog_all(),
        "files": _library_files(),
    }


@app.post("/api/v1/models/download")
async def download_model(req: DownloadRequest):
    entry = find_catalog_entry(req.architecture, req.filename)
    if not entry:
        raise HTTPException(422, f"no catalog entry for {req.architecture}/{req.filename}")
    if entry["exists"]:
        return {"status": "exists", **entry}
    # 同一文件已有活跃下载 → 返回现有作业(前端订阅其事件流,历史进度随重放立即可见)
    for existing in manager.jobs.values():
        if (existing.workflow.startswith("download") and existing.note == entry["filename"]
                and existing.status in ("queued", "running", "cancelling")):
            return {**existing.summary(), "attached": True}
    dest = MODELS_DIR / ROLE_SUBDIR[entry["role"]]
    route = settings_store.load().get("download_route", "auto")
    argv = [sys.executable, str(Path(__file__).resolve().parent / "download_model.py"),
            "--repo", entry["repo"], "--file", entry["remote_file"], "--dest", str(dest),
            "--route", route, "--size-mb", str(entry["size_mb"])]
    job = manager.submit(Job(f"download · {entry['role']}", req.architecture, entry["filename"], argv))
    return job.summary()


# ---- 作业 ----

def _validate_train(req: TrainRequest):
    if req.architecture not in TRAIN_ENTRY:
        raise HTTPException(400, f"unknown architecture {req.architecture!r}")
    if req.workflow == "full_finetune" and req.architecture not in FULL_FINETUNE_ENTRY:
        raise HTTPException(400, f"{req.architecture} has no full_finetune entrypoint")
    if req.workflow not in ("train_network", "full_finetune"):
        raise HTTPException(400, f"unknown workflow {req.workflow!r}")
    for key, label in (("dataset_config", "dataset_config"), ("dit", "dit")):
        if not str(req.values.get(key) or "").strip():
            raise HTTPException(422, f"{label} is required")


@app.post("/api/v1/jobs/train")
async def create_train_job(req: TrainRequest):
    _validate_train(req)
    prompts_path = None
    text = build_sample_prompt_text(req.values)
    if text:
        RUNTIME_DIR.mkdir(exist_ok=True)
        prompts_path = RUNTIME_DIR / f"prompts_{req.values.get('output_name') or 'job'}.txt"
        prompts_path.write_text(text, encoding="utf-8")
    try:
        argv = render_train_argv(req.architecture, req.workflow, req.values,
                                 str(prompts_path) if prompts_path else None)
    except ValueError as e:
        raise HTTPException(422, str(e))
    note = f"{req.values.get('output_name') or ''} · dim {req.values.get('network_dim') or '—'}"
    job = manager.submit(Job(f"{req.workflow} · {req.architecture}", req.architecture, note, argv))
    return job.summary()


@app.post("/api/v1/jobs/cache-latents")
async def create_cache_latents_job(req: CacheRequest):
    return _create_cache_job("latents", req)


@app.post("/api/v1/jobs/cache-text")
async def create_cache_text_job(req: CacheRequest):
    return _create_cache_job("text", req)


def _create_cache_job(kind: str, req: CacheRequest):
    try:
        argv = render_cache_argv(kind, req.architecture, req.values, req.keep_cache)
    except ValueError as e:
        raise HTTPException(422, str(e))
    wf = "cache_latents" if kind == "latents" else "cache_text"
    note = f"keep_cache={req.keep_cache}"
    job = manager.submit(Job(f"{wf} · {req.architecture}", req.architecture, note, argv))
    return job.summary()


@app.get("/api/v1/jobs")
async def list_jobs():
    ordered = sorted(manager.jobs.values(), key=lambda j: j.created_at, reverse=True)
    return {"jobs": [j.summary() for j in ordered]}


def _job_or_404(job_id: str) -> Job:
    job = manager.jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"unknown job {job_id!r}")
    return job


@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    return _job_or_404(job_id).summary()


@app.post("/api/v1/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    job = _job_or_404(job_id)
    manager.cancel(job)
    return job.summary()


@app.get("/api/v1/jobs/{job_id}/events")
async def job_events(job_id: str):
    job = _job_or_404(job_id)
    return StreamingResponse(
        manager.sse_stream(job), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---- 静态托管前端(单进程部署:构建产物存在时,同端口同时提供界面与 API) ----
# 用法:frontend 下 `npm run build` 后,uvicorn backend.main:app --host 0.0.0.0 --port 6006
_FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
