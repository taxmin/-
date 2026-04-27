@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

echo ============================================
echo dx多开框架 - 便携环境测试工具
echo ============================================
echo.

REM 检测Python
set "PY_CMD="
if exist "%~dp0python\python.exe" (
    set "PY_CMD=%~dp0python\python.exe"
) else if exist "%~dp0Python38Portable\python.exe" (
    set "PY_CMD=%~dp0Python38Portable\python.exe"
) else if exist "%~dp0runtime\python.exe" (
    set "PY_CMD=%~dp0runtime\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

%PY_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python解释器
    pause
    exit /b 1
)

echo [信息] 使用Python: %PY_CMD%
%PY_CMD% --version
echo.

cd /d "%~dp0"
%PY_CMD% test_portable_env.py

endlocal
