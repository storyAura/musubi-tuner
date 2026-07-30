"""模型下载脚本 — 由作业后端以子进程运行,进度原样流入 UI 终端面板。

下载源三级回退:
1. HuggingFace 默认端点(尊重 $HF_ENDPOINT;有代理的机器直连往往可用)
2. hf-mirror 镜像(剥掉继承代理直连;绕不过 gated 授权)
3. ModelScope 魔搭(国内直连,多数 HF gated 模型在魔搭免授权,同名仓库同名文件)

均支持断点续传;成功后归位到 models/<role子目录>/ 并清理临时文件。
"""
import argparse
import os
import shutil
import sys
import urllib.request
from pathlib import Path

MIRROR = "https://hf-mirror.com"
CHUNK = 8 * 1024 * 1024


def strip_proxies():
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
        os.environ.pop(k, None)


def hf_download(repo: str, file: str, tmp: Path, endpoint: str | None) -> str:
    from huggingface_hub import hf_hub_download
    return hf_hub_download(repo_id=repo, filename=file, local_dir=str(tmp), endpoint=endpoint)


def modelscope_download(repo: str, file: str, final: Path) -> None:
    """魔搭 resolve 直链,Range 断点续传,进度按百分比打印。"""
    url = f"https://modelscope.cn/models/{repo}/resolve/master/{file}"
    part = final.with_suffix(final.suffix + ".part")
    pos = part.stat().st_size if part.exists() else 0
    headers = {"User-Agent": "musubi-tuner-ui"}
    if pos:
        headers["Range"] = f"bytes={pos}-"
        print(f"[download] resume from {pos // (1024**2)} MB", flush=True)
    r = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60)
    if pos and r.status != 206:  # 服务器不认续传就从头来
        pos = 0
    total = pos + int(r.headers.get("Content-Length") or 0)
    done = pos
    step = max(total // 50, 128 * 1024 * 1024) if total else 256 * 1024 * 1024
    next_mark = done + step
    with open(part, "ab" if pos else "wb") as f:
        while True:
            chunk = r.read(CHUNK)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if done >= next_mark:
                pct = f"{done / total * 100:5.1f}%" if total else "?"
                print(f"[download] modelscope {pct} ({done / (1024**3):.2f}/{total / (1024**3):.2f} GB)",
                      flush=True)
                next_mark += step
    if total and done != total:
        raise IOError(f"incomplete download: {done}/{total} bytes")
    part.rename(final)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--dest", required=True)
    a = p.parse_args()

    # Xet 存储协议经代理(AutoDL 学术加速/Clash)常见 401,禁用后回退传统 HTTP 下载
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / ".hf_partial"
    final = dest / a.file.rsplit("/", 1)[-1]

    for endpoint in (None, MIRROR):
        if endpoint == MIRROR:
            strip_proxies()  # hf-mirror 面向直连,继承代理会劫持它
        label = endpoint or "default ($HF_ENDPOINT / huggingface.co)"
        print(f"[download] endpoint {label}", flush=True)
        print(f"[download] {a.repo} :: {a.file}", flush=True)
        try:
            got = hf_download(a.repo, a.file, tmp, endpoint)
            shutil.move(got, final)
            shutil.rmtree(tmp, ignore_errors=True)
            print(f"[download] saved {final}", flush=True)
            return
        except Exception as e:  # noqa: BLE001 — 逐端点回退
            print(f"[download] endpoint failed · {type(e).__name__}: {str(e)[:200]}", flush=True)

    strip_proxies()  # 魔搭国内直连
    print("[download] endpoint https://modelscope.cn (魔搭)", flush=True)
    print(f"[download] {a.repo} :: {a.file}", flush=True)
    try:
        modelscope_download(a.repo, a.file, final)
        print(f"[download] saved {final}", flush=True)
        return
    except Exception as e:  # noqa: BLE001
        print(f"[download] endpoint failed · {type(e).__name__}: {str(e)[:200]}", flush=True)

    print("ERROR: all endpoints failed — HF(direct/mirror) and ModelScope", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
