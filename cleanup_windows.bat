@echo off
setlocal ENABLEDELAYEDEXPANSION
title SD Prompt App - Windows Cleanup

echo ================================
echo  SD Prompt App - Cleanup (Win)
echo ================================
echo.
cd /d "%~dp0"

if exist ".venv" (
  echo Deleting .venv ...
  rmdir /s /q ".venv"
)

if exist "frontend\node_modules" (
  echo Deleting frontend\node_modules ...
  rmdir /s /q "frontend\node_modules"
)

if exist "frontend\dist" (
  echo Deleting frontend\dist ...
  rmdir /s /q "frontend\dist"
)

if exist "__pycache__" (
  echo Deleting __pycache__ ...
  rmdir /s /q "__pycache__"
)

if exist "tags_cache.db" (
  echo Deleting tags_cache.db ...
  del /f /q "tags_cache.db"
)

echo.
echo Cleanup complete. Only lightweight source files remain.
pause
