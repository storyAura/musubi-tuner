"""模型下载脚本 — 由作业后端以子进程运行,tqdm 进度原样流入 UI 终端面板。

端点顺序:先默认(尊重 $HF_ENDPOINT,否则 huggingface.co;有代理的机器直连往往可用),
失败自动切换 hf-mirror 镜像。取消后重跑可断点续传(临时目录保留 .incomplete 文件),
下载成功后归位到 models/<role子目录>/ 并清理临时目录。
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

MIRROR = "https://hf-mirror.com"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--dest", required=True)
    a = p.parse_args()

    # Xet 存储协议经代理(AutoDL 学术加速/Clash)常见 401,禁用后回退传统 HTTP 下载
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    from huggingface_hub import hf_hub_download

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / ".hf_partial"

    got = None
    for endpoint in (None, MIRROR):
        if endpoint == MIRROR:
            # hf-mirror 面向直连:剥掉继承的代理(AutoDL 学术加速/Clash),否则镜像也被代理劫持
            for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
                os.environ.pop(k, None)
        label = endpoint or "default ($HF_ENDPOINT / huggingface.co)"
        print(f"[download] endpoint {label}", flush=True)
        print(f"[download] {a.repo} :: {a.file}", flush=True)
        try:
            got = hf_hub_download(repo_id=a.repo, filename=a.file,
                                  local_dir=str(tmp), endpoint=endpoint)
            break
        except Exception as e:  # noqa: BLE001 — 逐端点回退,最终失败时整体退出非零
            print(f"[download] endpoint failed · {type(e).__name__}: {str(e)[:200]}", flush=True)
    if got is None:
        print("ERROR: all endpoints failed — check network / proxy settings", flush=True)
        sys.exit(1)

    final = dest / Path(a.file).name
    shutil.move(got, final)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"[download] saved {final}", flush=True)


if __name__ == "__main__":
    main()
