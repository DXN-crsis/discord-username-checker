@echo off
REM ╔═══════════════════════════════════════════════════════════╗
REM ║  SHOTER - One-click launcher (Windows)                   ║
REM ╚═══════════════════════════════════════════════════════════╝

cd /d "%~dp0"

set VENV_DIR=venv

REM ── Find Python ───────────────────────────────────────────
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version

REM ── Create venv if needed ─────────────────────────────────
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM ── Activate and install ──────────────────────────────────
call %VENV_DIR%\Scripts\activate.bat

echo Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

REM ── Launch ────────────────────────────────────────────────
echo.
echo   Launching SHOTER...
echo.
python main.py

pause
