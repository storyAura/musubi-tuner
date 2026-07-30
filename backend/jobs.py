"""作业管理器:真实子进程的启动、日志/进度回流、取消与状态机。

状态机(交接文档 §13.1 的最小子集):queued → running → succeeded | failed | cancelled,
running → cancelling → cancelled。单 worker 串行执行(同一 GPU 一次一个作业)。
ponytail: 作业表仅存内存,后端重启不恢复;需要持久化时按交接文档补 SQLite 存储与 orphaned 对账。
"""
from __future__ import annotations

import asyncio
import itertools
import json
import os
import re
import signal
import subprocess
import threading
import time
import uuid
from pathlib import Path

from .capability import REPO_ROOT

MAX_LOG_LINES = 2000
STDERR_TAIL = 8
GRACEFUL_TIMEOUT_S = 5

# kohya/musubi 进度行:steps:  37%|███| 1480/4000 [12:34<21:10,  1.98it/s, avr_loss=0.0912]
RE_STEPS = re.compile(r"steps:\s*(\d+)%\|.*?\|\s*(\d+)/(\d+)\s*\[[^\]]*?(?:([\d.]+)it/s)?(?:,\s*avr_loss=([\d.eE+-]+))?")
RE_EPOCH = re.compile(r"^epoch\s+(\d+)/(\d+)", re.IGNORECASE)


def now_hhmm() -> str:
    return time.strftime("%H:%M")


class Job:
    def __init__(self, workflow: str, architecture: str, note: str, argv: list[str]):
        self.id = "job_" + uuid.uuid4().hex[:6]
        self.workflow = workflow
        self.architecture = architecture
        self.note = note
        self.argv = argv
        self.status = "queued"
        self.created_at = time.time()
        self.started_hhmm = ""
        self.started_mono: float | None = None
        self.finished_mono: float | None = None
        self.exit_code: int | None = None
        self.pid: int | None = None
        self.cancel_requested = False
        self.seq = itertools.count(1)
        self.events: list[dict] = []
        self.subscribers: list[asyncio.Queue] = []
        self.progress = {"step": 0, "total": 0, "epoch": 0, "total_epochs": 0,
                         "avr_loss": None, "itps": None}
        self.stderr_tail: list[str] = []

    # ---- 序列化 ----
    def summary(self) -> dict:
        dur = ""
        if self.started_mono is not None:
            end = self.finished_mono if self.finished_mono is not None else time.monotonic()
            dur = _clock(end - self.started_mono)
        return {
            "job_id": self.id, "workflow": self.workflow, "architecture": self.architecture,
            "note": self.note, "status": self.status,
            "progress": self.progress, "started": self.started_hhmm or "—", "duration": dur or "—",
            "exit_code": self.exit_code, "stderr_tail": self.stderr_tail,
            "argv": self.argv[1:],  # 不含解释器路径;秘密从不进入 argv
        }


def _clock(sec: float) -> str:
    sec = max(0, round(sec))
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class JobManager:
    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self.pending: list[str] = []
        self.current: Job | None = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self._worker_running = False

    def bind_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    # ---- 事件 ----
    def _publish(self, job: Job, ev: dict):
        ev = {"seq": next(job.seq), "job_id": job.id, **ev}
        job.events.append(ev)
        if len(job.events) > MAX_LOG_LINES * 2:
            del job.events[: len(job.events) - MAX_LOG_LINES * 2]
        for q in list(job.subscribers):
            try:
                q.put_nowait(ev)
            except asyncio.QueueFull:
                pass

    def _publish_threadsafe(self, job: Job, ev: dict):
        if self.loop:
            self.loop.call_soon_threadsafe(self._publish, job, ev)

    def _set_status(self, job: Job, status: str, **extra):
        job.status = status
        self._publish(job, {"type": "status", "status": status, **extra})

    # ---- 提交与调度(须在事件循环线程内调用:main.py 的相关端点均为 async def) ----
    def submit(self, job: Job) -> Job:
        self.jobs[job.id] = job
        self.pending.append(job.id)
        self._publish(job, {"type": "status", "status": "queued",
                            "message": "waiting_for_gpu:0" if self.current else "starting"})
        if self.loop and not self._worker_running:
            self._worker_running = True
            self.loop.create_task(self._worker())
        return job

    async def _worker(self):
        try:
            while self.pending:
                job = self.jobs[self.pending.pop(0)]
                if job.status != "queued":
                    continue
                self.current = job
                await self._run(job)
                self.current = None
        finally:
            self._worker_running = False

    async def _run(self, job: Job):
        job.started_hhmm = now_hhmm()
        job.started_mono = time.monotonic()
        self._set_status(job, "running")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        try:
            proc = subprocess.Popen(
                job.argv, cwd=str(REPO_ROOT), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", creationflags=flags,
            )
        except OSError as e:
            job.exit_code = -1
            job.stderr_tail = [str(e)]
            job.finished_mono = time.monotonic()
            self._set_status(job, "failed", error=str(e))
            return
        job.pid = proc.pid
        self._publish(job, {"type": "log", "kind": "dim", "text": f"[job] process started · pid {proc.pid}"})

        reader = threading.Thread(target=self._read_output, args=(job, proc), daemon=True)
        reader.start()
        code = await asyncio.get_running_loop().run_in_executor(None, proc.wait)
        reader.join(timeout=3)
        job.exit_code = code
        job.finished_mono = time.monotonic()
        if job.cancel_requested:
            self._set_status(job, "cancelled", exit_code=code)
        elif code == 0:
            self._set_status(job, "succeeded", exit_code=0)
        else:
            self._set_status(job, "failed", exit_code=code, stderr_tail=job.stderr_tail)

    def _read_output(self, job: Job, proc: subprocess.Popen):
        """按 \\n 和 \\r 切分读取(tqdm 用 \\r 刷新进度,不能等换行)。"""
        buf = ""
        stream = proc.stdout
        assert stream is not None
        while True:
            ch = stream.read(1)
            if ch == "":
                break
            if ch in ("\n", "\r"):
                line = buf.strip("\x00 ")
                buf = ""
                if line:
                    self._handle_line(job, line)
            else:
                buf += ch
        if buf.strip():
            self._handle_line(job, buf.strip())

    def _handle_line(self, job: Job, line: str):
        low = line.lower()
        kind = "err" if ("error" in low or "traceback" in low or "exception" in low) \
            else ("warn" if "warning" in low else "ink")
        if kind == "err":
            job.stderr_tail.append(line)
            if len(job.stderr_tail) > STDERR_TAIL:
                job.stderr_tail.pop(0)
        m = RE_STEPS.search(line)
        if m:
            job.progress["step"] = int(m.group(2))
            job.progress["total"] = int(m.group(3))
            if m.group(4):
                job.progress["itps"] = float(m.group(4))
            if m.group(5):
                job.progress["avr_loss"] = float(m.group(5))
            self._publish_threadsafe(job, {"type": "progress", **job.progress})
        me = RE_EPOCH.match(line)
        if me:
            job.progress["epoch"] = int(me.group(1))
            job.progress["total_epochs"] = int(me.group(2))
            self._publish_threadsafe(job, {"type": "progress", **job.progress})
        self._publish_threadsafe(job, {"type": "log", "kind": kind, "text": line})

    # ---- 取消 ----
    def cancel(self, job: Job):
        if job.status == "queued":
            if job.id in self.pending:
                self.pending.remove(job.id)
            self._set_status(job, "cancelled")
            return
        if job.status != "running" or job.pid is None:
            return
        job.cancel_requested = True
        self._set_status(job, "cancelling")
        self._publish(job, {"type": "log", "kind": "warn",
                            "text": "[job] cancel_requested · sending graceful break, force kill in "
                                    f"{GRACEFUL_TIMEOUT_S}s"})
        pid = job.pid
        try:
            if os.name == "nt":
                os.kill(pid, signal.CTRL_BREAK_EVENT)  # 发给整个新进程组
            else:
                os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        if self.loop:
            self.loop.create_task(self._force_kill_later(job, pid))

    async def _force_kill_later(self, job: Job, pid: int):
        await asyncio.sleep(GRACEFUL_TIMEOUT_S)
        if job.status != "cancelling":
            return
        self._publish(job, {"type": "log", "kind": "warn", "text": "[job] force terminating process tree"})
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

    # ---- SSE ----
    async def sse_stream(self, job: Job):
        q: asyncio.Queue = asyncio.Queue(maxsize=4096)
        job.subscribers.append(q)
        terminal = ("succeeded", "failed", "cancelled")
        try:
            for ev in list(job.events):  # 重放历史,断线重连自动补齐
                yield _sse(ev)
            if job.status in terminal:  # 已终态的作业重放即完整历史
                return
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield _sse(ev)
                if ev.get("type") == "status" and ev.get("status") in ("succeeded", "failed", "cancelled"):
                    break
        finally:
            if q in job.subscribers:
                job.subscribers.remove(q)


def _sse(ev: dict) -> str:
    return f"id: {ev['seq']}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"


manager = JobManager()
