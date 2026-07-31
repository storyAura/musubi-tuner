"""模型下载脚本 — 由作业后端以子进程运行,结构化进度驱动前端进度条。

下载源:HuggingFace 直连 / hf-mirror / ModelScope 魔搭。
route=auto 时先并行实测三条线路的真实吞吐(对目标文件 Range 拉取数 MB),
按速度排序逐个尝试;不可达或 gated(401/403)自动得 0 分垫底。
已有断点缓存的线路体系优先(HF 系与魔搭的缓存互不通用,换源会从零下载)。
均支持断点续传;成功后归位到 models/<role子目录>/。
"""
import argparse
import json
import os
import shutil
import sys
import threading
import time
import urllib.request
from pathlib import Path

MIRROR = "https://hf-mirror.com"
CHUNK = 8 * 1024 * 1024
SOURCES = ("hf", "mirror", "modelscope")
SOURCE_LABEL = {
    "hf": "huggingface.co (direct)",
    "mirror": MIRROR,
    "modelscope": "modelscope.cn (魔搭)",
}


_PROXY_KEYS = ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY")
_SAVED_PROXIES = {k: os.environ[k] for k in _PROXY_KEYS if k in os.environ}


def set_proxies(enabled: bool):
    """HF 直连要走环境代理;mirror/魔搭要直连。线路顺序不定,故可恢复地切换。"""
    if enabled:
        os.environ.update(_SAVED_PROXIES)
    else:
        for k in _PROXY_KEYS:
            os.environ.pop(k, None)


def _opener(use_env_proxy: bool):
    if use_env_proxy:
        return urllib.request.build_opener()  # 读环境代理(HF 直连在代理环境更快)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 强制直连


def _source_url(src: str, repo: str, file: str) -> str:
    if src == "modelscope":
        return f"https://modelscope.cn/models/{repo}/resolve/master/{file}"
    base = MIRROR if src == "mirror" else "https://huggingface.co"
    return f"{base}/{repo}/resolve/main/{file}"


def _fmt_bps(bps: float) -> str:
    return f"{bps / 1048576:.1f} MB/s" if bps >= 1048576 else f"{bps / 1024:.0f} KB/s"


def speed_test(src: str, repo: str, file: str, budget: float = 5.0) -> float:
    """对目标文件 Range 拉取实测吞吐;不可达/gated 返回 0。"""
    headers = {"User-Agent": "musubi-tuner-ui", "Range": "bytes=0-8388607"}
    if src == "hf" and os.environ.get("HF_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["HF_TOKEN"]
    t0 = time.monotonic()
    try:
        r = _opener(src == "hf").open(
            urllib.request.Request(_source_url(src, repo, file), headers=headers), timeout=6)
        got = 0
        while time.monotonic() - t0 < budget:
            chunk = r.read(256 * 1024)
            if not chunk:
                break
            got += len(chunk)
        dt = time.monotonic() - t0
        return got / dt if got and dt > 0 else 0.0
    except Exception:  # noqa: BLE001 — 测速失败即 0 分
        return 0.0


def rank_sources(repo: str, file: str, hf_cache: int, ms_cache: int) -> list[str]:
    results: dict[str, float] = {}
    threads = []
    for src in SOURCES:
        t = threading.Thread(target=lambda s=src: results.__setitem__(s, speed_test(s, repo, file)))
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=15)
    print("[download] speed test · " + " · ".join(
        f"{s}: {_fmt_bps(results.get(s, 0)) if results.get(s, 0) else '不可达'}" for s in SOURCES),
        flush=True)

    order = sorted([s for s in SOURCES if results.get(s, 0) > 0], key=lambda s: -results[s])
    order += [s for s in SOURCES if results.get(s, 0) <= 0]  # 不可达的垫底兜底
    # 断点缓存优先:HF 系(hf/mirror 共享缓存)与魔搭缓存不通用,换源等于从零下
    margin = 256 * 1024 * 1024
    if hf_cache > ms_cache + margin:
        pref = [s for s in order if s in ("hf", "mirror") and results.get(s, 0) > 0]
        if pref and order[0] not in ("hf", "mirror"):
            order.remove(pref[0])
            order.insert(0, pref[0])
            print(f"[download] 续传优先 · HF 系已有 {hf_cache // (1024**2)} MB 缓存", flush=True)
    elif ms_cache > hf_cache + margin and results.get("modelscope", 0) > 0 and order[0] != "modelscope":
        order.remove("modelscope")
        order.insert(0, "modelscope")
        print(f"[download] 续传优先 · 魔搭已有 {ms_cache // (1024**2)} MB 缓存", flush=True)
    print(f"[download] 线路顺序 → {' > '.join(order)}", flush=True)
    return order


def start_progress_watch(watch_paths: list[Path], total_mb: int, stop: threading.Event) -> None:
    """每 5s 发一条结构化进度([dlprog] JSON → progress 事件驱动前端进度条),不刷日志。"""
    def scan() -> int:
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
        return size

    def loop():
        total_b = total_mb * 1024 * 1024
        last_size, last_t, speed = scan(), time.monotonic(), 0.0
        last_decile = -1
        while not stop.wait(5):
            size = scan()
            now = time.monotonic()
            dt = now - last_t
            inst = (size - last_size) / dt if dt > 0 and size >= last_size else 0.0
            speed = inst if speed <= 0 else speed * 0.6 + inst * 0.4
            last_size, last_t = size, now
            if not size:
                continue
            eta = int((total_b - size) / speed) if speed > 1 and total_b > size else -1
            print("[dlprog] " + json.dumps({
                "bytes": size, "total_bytes": total_b, "speed_bps": int(speed), "eta_s": eta,
            }), flush=True)
            if total_b:  # 终端里程碑:每完成 10% 一行,可见但不刷屏
                decile = int(size / total_b * 10)
                if decile > last_decile:
                    last_decile = decile
                    print(f"[download] {decile * 10}% · {size / (1024**3):.2f}/{total_b / (1024**3):.2f} GB"
                          f" · {_fmt_bps(speed)}", flush=True)

    threading.Thread(target=loop, daemon=True).start()


def hf_download(repo: str, file: str, tmp: Path, endpoint: str | None) -> str:
    from huggingface_hub import hf_hub_download
    return hf_hub_download(repo_id=repo, filename=file, local_dir=str(tmp), endpoint=endpoint)


def modelscope_download(repo: str, file: str, final: Path, max_retries: int = 12) -> None:
    """魔搭 resolve 直链,Range 断点续传;大文件长连接中断时自动从断点重连。"""
    url = _source_url("modelscope", repo, file)
    part = final.with_suffix(final.suffix + ".part")
    retries = 0
    while True:
        pos = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": "musubi-tuner-ui"}
        if pos:
            headers["Range"] = f"bytes={pos}-"
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60)
            if pos and r.status != 206:  # 服务器不认续传就从头来
                pos = 0
                r.close()
                part.unlink(missing_ok=True)
                r = urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "musubi-tuner-ui"}), timeout=60)
            total = pos + int(r.headers.get("Content-Length") or 0)
            done = pos
            if pos:
                print(f"[download] resume from {pos // (1024**2)} MB", flush=True)
            with open(part, "ab" if pos else "wb") as f:
                while True:
                    chunk = r.read(CHUNK)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
            if total and done != total:
                raise IOError(f"connection dropped at {done}/{total} bytes")
            part.rename(final)
            return
        except (OSError, IOError) as e:
            retries += 1
            if retries > max_retries:
                raise
            print(f"[download] 连接中断({type(e).__name__}),{retries}/{max_retries} 次重连,"
                  f"5s 后从断点继续", flush=True)
            time.sleep(5)


def _dir_max_size(p: Path) -> int:
    if not p.is_dir():
        return 0
    size = 0
    for f in p.rglob("*"):
        if f.is_file():
            try:
                size = max(size, f.stat().st_size)
            except OSError:
                pass
    return size


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--dest", required=True)
    p.add_argument("--route", default="auto", choices=["auto", *SOURCES])
    p.add_argument("--size-mb", type=int, default=0, help="预期大小(仅用于进度百分比)")
    a = p.parse_args()

    # Xet 存储协议经代理(AutoDL 学术加速/Clash)常见 401,禁用后回退传统 HTTP 下载
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / ".hf_partial"
    final = dest / a.file.rsplit("/", 1)[-1]
    part = final.with_suffix(final.suffix + ".part")

    if final.exists():  # 幂等:排队期间前一个同文件作业已完成时,绝不重复下载
        print(f"[download] already exists · {final}", flush=True)
        return

    if a.route == "auto":
        order = rank_sources(a.repo, a.file, _dir_max_size(tmp), part.stat().st_size if part.exists() else 0)
    else:
        order = [a.route]

    stop = threading.Event()
    start_progress_watch([tmp, part], a.size_mb, stop)

    for src in order:
        set_proxies(src == "hf")  # HF 直连走代理;mirror/魔搭强制直连
        print(f"[download] endpoint {SOURCE_LABEL[src]}", flush=True)
        print(f"[download] {a.repo} :: {a.file}", flush=True)
        try:
            if src == "modelscope":
                modelscope_download(a.repo, a.file, final)
            else:
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
