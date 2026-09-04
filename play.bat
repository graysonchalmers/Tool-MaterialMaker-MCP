@echo off
REM One-click launcher for the Material Maker Play surface (mm-play).
REM Double-click this file. It starts the local web server and opens your
REM browser at http://127.0.0.1:8788/ automatically. Close this window
REM (or press Ctrl+C) to stop the server.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Could not find .venv\Scripts\python.exe next to this file.
  echo Expected the project virtualenv at "%~dp0.venv".
  pause
  exit /b 1
)

echo Starting Material Maker Play...
".venv\Scripts\python.exe" -m mm_mcp.play.server

echo.
echo Server stopped.
pause
