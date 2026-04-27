@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ============================================
echo 复制/移动项目后：把 .venv 绑到本机 Python
echo ============================================
echo.

set "PORTABLE=%ROOT%Python38Portable\python.exe"
set "VENV=%ROOT%.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"

REM 失效的 .venv（仍指向旧盘符/旧路径）无法 --upgrade，必须先删掉
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [警告] 检测到 .venv 已损坏（例如仍指向 G:\ 等不存在的 Python）
        echo         正在删除，将在下方用本机 Python 重建空虚拟环境...
        rmdir /s /q "%VENV%"
        echo.
    )
)

if exist "%PORTABLE%" (
    echo [信息] 使用本目录 Python38Portable 处理 .venv
    if exist "%VENV_PY%" (
        "%PORTABLE%" -m venv "%VENV%" --upgrade
    ) else (
        "%PORTABLE%" -m venv "%VENV%"
    )
    if errorlevel 1 (
        echo [错误] venv 失败。
        pause
        exit /b 1
    )
    goto :ok
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python38Portable，且 PATH 中无 python。
    echo 请先安装 Python 3.8.x（64 位）并勾选 Add to PATH，或运行 setup_python_portable.bat
    pause
    exit /b 1
)

echo [信息] 使用 PATH 中的 python 处理 .venv
if exist "%VENV_PY%" (
    python -m venv "%VENV%" --upgrade
) else (
    python -m venv "%VENV%"
)
if errorlevel 1 (
    echo [错误] venv 失败。
    pause
    exit /b 1
)

:ok
echo.
echo [成功] 已更新 .venv（若刚才是新建的空环境，请再运行 install_env.bat 安装依赖）。
echo 若依赖已装齐，可直接 run.bat。
pause
