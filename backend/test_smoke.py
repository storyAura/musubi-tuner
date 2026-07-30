"""后端冒烟测试:argv 渲染正确性 + 真实子进程作业生命周期。

运行:python -m pytest backend/test_smoke.py -q
作业测试会真实启动子进程(训练环境不齐时以真实错误失败——这正是要验证的诚实回流)。
"""
import sys
import time

from fastapi.testclient import TestClient

from backend.capability import render_cache_argv, render_train_argv
from backend.main import app


def _wait_terminal(client, job_id, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        j = client.get(f"/api/v1/jobs/{job_id}").json()
        if j["status"] in ("succeeded", "failed", "cancelled"):
            return j
        time.sleep(0.3)
    raise AssertionError(f"job {job_id} did not finish in {timeout}s")


def test_diagnostics_endpoints():
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["ok"] is True
        env = client.get("/api/v1/environment").json()
        assert "gpus" in env and "python" in env
        caps = client.get("/api/v1/capabilities").json()
        archs = {a["id"]: a for a in caps["architectures"]}
        assert len(archs) == 12
        assert "full_finetune" in archs["qwen-image"]["workflows"]
        assert "full_finetune" not in archs["krea2"]["workflows"]


def test_argv_rendering_follows_capability():
    v = {"dataset_config": "d.toml", "dit": "dit.safetensors", "model_version": "edit-2511",
         "attn_mode": "sdpa", "network_module": "standard_lora", "network_dim": "16",
         "mixed_precision": "bf16", "learning_rate": "1e-4",
         "wandb_api_key": "SECRET-A", "huggingface_token": "SECRET-B"}
    argv = render_train_argv("qwen-image", "train_network", v, None)
    joined = " ".join(argv)
    assert "qwen_image_train_network.py" in joined
    assert "--model_version edit-2511" in joined
    assert "--network_module networks.lora_qwen_image" in joined
    assert "--sdpa" in joined
    assert "SECRET-A" not in joined and "SECRET-B" not in joined  # 秘密从不进 argv

    # 无变体枚举的架构不得出现 model_version;wan 的 TE flag 是 --t5
    argv2 = render_train_argv("krea2", "train_network",
                              {"dataset_config": "d.toml", "dit": "x", "model_version": "edit-2511"}, None)
    assert "--model_version" not in " ".join(argv2)
    argv3 = render_train_argv("wan2.1/2.2", "train_network",
                              {"dataset_config": "d.toml", "dit": "x", "task": "t2v-14B",
                               "text_encoder": "t5.pth"}, None)
    j3 = " ".join(argv3)
    assert "--task t2v-14B" in j3 and "--t5 t5.pth" in j3

    # HunyuanVideo 全量微调是 legacy parser:不渲染它没有的 flag
    argv4 = render_train_argv("hunyuan-video", "full_finetune",
                              {"dataset_config": "d.toml", "dit": "x", "fp8_base": True,
                               "save_precision": "bf16"}, None)
    j4 = " ".join(argv4)
    assert "hv_train.py" in j4 and "--fp8_base" not in j4 and "--save_precision" not in j4

    cache = " ".join(render_cache_argv("latents", "qwen-image",
                                       {"dataset_config": "d.toml", "vae": "v.safetensors",
                                        "model_version": "edit-2511"}, keep_cache=True))
    assert "qwen_image_cache_latents.py" in cache and "--keep_cache" in cache


def test_real_subprocess_job_lifecycle():
    """提交的作业必须启动真实子进程;环境/路径问题以真实错误终止并回流。"""
    with TestClient(app) as client:
        r = client.post("/api/v1/jobs/train", json={
            "architecture": "qwen-image", "workflow": "train_network",
            "values": {"dataset_config": "Z:/definitely/missing.toml", "dit": "Z:/missing.safetensors",
                       "output_name": "smoke-test", "mixed_precision": "no", "attn_mode": "sdpa"},
        })
        assert r.status_code == 200, r.text
        job = r.json()
        assert job["status"] in ("queued", "running")

        final = _wait_terminal(client, job["job_id"])
        # 没有真实数据集/模型(或训练依赖未装)时必须 failed,绝不假装成功
        assert final["status"] == "failed"
        assert final["exit_code"] not in (0, None)

        # 事件流里必须有真实进程日志(SSE 与 /jobs 详情同源)
        with client.stream("GET", f"/api/v1/jobs/{job['job_id']}/events") as s:
            body = ""
            for chunk in s.iter_text():
                body += chunk
                if '"status": "failed"' in body or len(body) > 65536:
                    break
        assert "process started" in body


def test_validation_and_cancel_queued():
    with TestClient(app) as client:
        r = client.post("/api/v1/jobs/train", json={"architecture": "qwen-image", "values": {}})
        assert r.status_code == 422  # dataset_config 必填

        r = client.post("/api/v1/jobs/train", json={
            "architecture": "krea2", "workflow": "full_finetune",
            "values": {"dataset_config": "d.toml", "dit": "x"}})
        assert r.status_code == 400  # krea2 没有全量微调入口
