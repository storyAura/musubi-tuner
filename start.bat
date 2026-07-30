@echo off
REM musubi tuner Web UI - one-click start (Windows)
REM First run installs all dependencies; later runs skip straight to launch.
cd /d %~dp0
set MARKER=backend\.runtime\setup_done

if exist %MARKER% goto :launch

echo [setup] first run: installing musubi-tuner and backend dependencies...
pip install -e . || goto :fail
pip install -r backend\requirements.txt || goto :fail

where node >nul 2>nul
if %errorlevel%==0 (
  echo [setup] building frontend...
  pushd frontend
  call npm install --no-audit --no-fund || goto :fail
  call npm run build || goto :fail
  popd
) else (
  echo [setup] node not found - using bundled frontend\dist
)

if not exist backend\.runtime mkdir backend\.runtime
echo done > %MARKER%
echo [setup] done.

:launch
echo [webui] starting on http://localhost:8787
start "" http://localhost:8787
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8787
goto :eof

:fail
echo [setup] FAILED - see errors above. Fix and run start.bat again.
pause
