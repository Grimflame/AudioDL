@echo off
setlocal ENABLEDELAYEDEXPANSION
title SD Prompt App - Windows Bootstrap

echo ================================
echo  SD Prompt App - Bootstrap (Win)
echo ================================
echo.

REM 0) Move to the folder where this script lives
cd /d "%~dp0"

REM 1) Check Python (3.10+ recommended)
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Python not found. Please install Python 3.10+ from https://www.python.org/downloads/
  pause
  exit /b 1
)

REM 2) Create / activate venv and install backend deps
if not exist ".venv" (
  echo [Backend] Creating virtual environment .venv ...
  python -m venv .venv
)
call ".venv\Scripts\activate.bat"
echo [Backend] Upgrading pip and installing dependencies ...
python -m pip install --upgrade pip
pip install fastapi uvicorn requests pydantic numpy

REM 3) Check Node.js
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Node.js not found. Please install Node.js 18+ from https://nodejs.org/
  pause
  exit /b 1
)

REM 4) Frontend dependencies and default .env
if exist "frontend\package.json" (
  echo [Frontend] Installing node modules ...
  pushd frontend
  if not exist "node_modules" (
    npm install
  ) else (
    echo [Frontend] node_modules already present - skipping npm install.
  )
  if not exist ".env" (
    echo VITE_API_URL=http://localhost:8000> .env
  )
  popd
) else (
  echo [WARN] frontend\package.json not found. Skipping frontend install.
)

REM 5) Warm the Danbooru cache (optional but recommended)
if exist "warm_cache.py" (
  echo [Cache] Warming Danbooru cache (this may take a minute)...
  python warm_cache.py
) else (
  echo [Cache] warm_cache.py not found - skipping prefetch.
)

echo.
echo Done! Quick start:
echo   1) Backend:   .venv\Scripts\activate ^&^& uvicorn main:app --reload
echo   2) Frontend:  cd frontend ^&^& npm run dev
echo.
pause
