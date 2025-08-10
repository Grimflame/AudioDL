@echo off
setlocal ENABLEDELAYEDEXPANSION
title SD Prompt App - Create Folders (Win)

echo =========================================
echo  SD Prompt App - Create Project Folders
echo =========================================
echo.
cd /d "%~dp0"

REM Recommended folders (idempotent: only created if missing)
set FOLDERS=docs assets\screenshots scripts data .github\workflows

for %%D in (%FOLDERS%) do (
  if not exist "%%D" (
    echo [+] Creating folder: %%D
    mkdir "%%D"
  ) else (
    echo [=] Exists: %%D
  )
)

REM Optional helper files
if not exist "README_DEPLOY.md" (
  echo [+] Creating README_DEPLOY.md
  > README_DEPLOY.md echo # SD Prompt App \- Quick Deploy
  >> README_DEPLOY.md echo.
  >> README_DEPLOY.md echo See scripts: ^`bootstrap_windows.bat^` (setup) and ^`cleanup_windows.bat^` (clean heavy files).
)

if not exist "scripts\start_backend_example.bat" (
  echo [+] Creating scripts\start_backend_example.bat
  > scripts\start_backend_example.bat echo @echo off
  >> scripts\start_backend_example.bat echo call ..\^.venv\Scripts\activate.bat ^&^& uvicorn main:app --reload
)

if not exist "scripts\start_frontend_example.bat" (
  echo [+] Creating scripts\start_frontend_example.bat
  > scripts\start_frontend_example.bat echo @echo off
  >> scripts\start_frontend_example.bat echo cd /d "%%~dp0\..\frontend" ^&^& npm run dev
)

echo.
echo Folders and helper files are ready.
pause
