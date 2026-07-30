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
import threading
import urllib.request
from pathlib import Path

MIRROR = "https://hf-mirror.com"
CHUNK = 8 * 1024 * 1024


def start_progress_watch(watch_paths: list[Path], total_mb: int, stop: threading.Event) -> None:
    """每 10s 打印下载中文件的当前大小(不依赖 tqdm——它在管道里常被吞掉)。"""
    def loop():
        last = -1
        while not stop.wait(10):
            size = 0
            for p in watch_paths:
                if p.is_dir():
                    for f in p.rglob("*"):
                        if f.is_file():
                            try:
                                size = max(size, f.stat().st_size)
                            except OSError:
                                pass
                elif p.exists():
                    try:
                        size = max(size, p.stat().st_size)
                    except OSError:
                        pass
            if size and size != last:
                pct = f" · {size / (total_mb * 1024 * 1024) * 100:.1f}%" if total_mb else ""
                print(f"[download] progress {size / (1024**3):.2f} GB{pct}", flush=True)
                last = size

    threading.Thread(target=loop, daemon=True).start()


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


ROUTE_SOURCES = {
    "auto": ["hf", "mirror", "modelscope"],
    "hf": ["hf"], "mirror": ["mirror"], "modelscope": ["modelscope"],
}
SOURCE_LABEL = {
    "hf": "default ($HF_ENDPOINT / huggingface.co)",
    "mirror": MIRROR,
    "modelscope": "https://modelscope.cn (魔搭)",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--dest", required=True)
    p.add_argument("--route", default="auto", choices=sorted(ROUTE_SOURCES))
    p.add_argument("--size-mb", type=int, default=0, help="预期大小(仅用于进度百分比)")
    a = p.parse_args()

    # Xet 存储协议经代理(AutoDL 学术加速/Clash)常见 401,禁用后回退传统 HTTP 下载
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / ".hf_partial"
    final = dest / a.file.rsplit("/", 1)[-1]

    if final.exists():  # 幂等:排队期间前一个同文件作业已完成时,绝不重复下载
        print(f"[download] already exists · {final}", flush=True)
        return

    stop = threading.Event()
    start_progress_watch([tmp, final.with_suffix(final.suffix + ".part")], a.size_mb, stop)

    for src in ROUTE_SOURCES[a.route]:
        print(f"[download] endpoint {SOURCE_LABEL[src]}", flush=True)
        print(f"[download] {a.repo} :: {a.file}", flush=True)
        try:
            if src == "modelscope":
                strip_proxies()  # 魔搭国内直连
                modelscope_download(a.repo, a.file, final)
            else:
                if src == "mirror":
                    strip_proxies()  # hf-mirror 面向直连,继承代理会劫持它
                got = hf_download(a.repo, a.file, tmp, MIRROR if src == "mirror" else None)
                shutil.move(got, final)
                shutil.rmtree(tmp, ignore_errors=True)
            stop.set()
            print(f"[download] saved {final}", flush=True)
            return
        except Exception as e:  # noqa: BLE001 — 逐线路回退
            print(f"[download] endpoint failed · {type(e).__name__}: {str(e)[:200]}", flush=True)

    stop.set()
    print(f"ERROR: all endpoints failed (route={a.route}) — 可在设置页切换下载线路或配置 token", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
