#!/bin/bash
# musubi tuner Web UI - one-click start (Linux / AutoDL)
# First run installs all dependencies; later runs skip straight to launch.
# AutoDL: sources academic acceleration and serves on port 6006 (panel entry "WebUI-6006").
set -e
cd "$(dirname "$0")"

PY=python3
[ -x /root/miniconda3/bin/python ] && PY=/root/miniconda3/bin/python
PORT="${PORT:-6006}"
MARKER=backend/.runtime/setup_done

# AutoDL academic acceleration (github/huggingface reachability)
test -f /etc/network_turbo && source /etc/network_turbo

if [ ! -f "$MARKER" ]; then
  echo "[setup] first run: installing musubi-tuner and backend dependencies..."
  "$PY" -m pip install -e . -q
  "$PY" -m pip install -q -r backend/requirements.txt
  mkdir -p backend/.runtime
  echo done > "$MARKER"
  echo "[setup] done."
fi

if [ ! -f frontend/dist/index.html ]; then
  echo "[warn] frontend/dist missing - UI will 404. Build locally (npm run build) and commit/upload dist."
fi

pkill -f 'uvicorn backend.main:app' 2>/dev/null || true
sleep 1
echo "[webui] starting on 0.0.0.0:$PORT (log: webui.log)"
nohup "$PY" -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" >> webui.log 2>&1 &
sleep 2
curl -s --noproxy '*' "http://127.0.0.1:$PORT/api/v1/health" && echo " · ready"
