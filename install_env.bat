@echo off
chcp 65001 >nul
echo ============================================
echo dx多开框架 - 环境安装脚本
echo ============================================
echo.

REM 优先使用项目内置Python（轻量化），找不到再回退系统Python
set "PY_CMD="
if exist "%~dp0python\python.exe" (
    set "PY_CMD=%~dp0python\python.exe"
    echo [信息] 使用内置Python: python\
) else if exist "%~dp0Python38Portable\python.exe" (
    set "PY_CMD=%~dp0Python38Portable\python.exe"
    echo [信息] 使用便携Python: Python38Portable\
) else if exist "%~dp0runtime\python.exe" (
    set "PY_CMD=%~dp0runtime\python.exe"
    echo [信息] 使用运行时Python: runtime\
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
    echo [信息] 使用虚拟环境: .venv\
) else (
    set "PY_CMD=python"
    echo [信息] 使用系统Python
)

REM 检查Python是否可用
%PY_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到可用Python
    echo [提示] 请在项目目录放置内置Python，或安装系统Python后重试
    pause
    exit /b 1
)

echo [信息] 检测到Python版本:
%PY_CMD% --version
echo.

REM 检查pip是否可用
%PY_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] pip不可用，请检查Python安装
    pause
    exit /b 1
)

echo [信息] 检测到pip版本:
%PY_CMD% -m pip --version
echo.

REM 升级pip
echo [步骤1] 升级pip到最新版本...
%PY_CMD% -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple
if errorlevel 1 (
    echo [警告] pip升级失败，继续安装依赖...
    echo.
)

echo.
echo [步骤2] 安装项目依赖包...
echo 使用镜像源: https://mirrors.aliyun.com/pypi/simple
echo.

if not exist requirement.txt (
    echo [错误] 未找到 requirement.txt
    pause
    exit /b 1
)

REM 安装依赖
%PY_CMD% -m pip install -r requirement.txt -i https://mirrors.aliyun.com/pypi/simple

if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败！
    echo 请检查网络连接或尝试使用其他镜像源
    echo.
    echo 可尝试的镜像源:
    echo   -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo   -i https://pypi.douban.com/simple
    pause
    exit /b 1
)

echo.
echo ============================================
echo [成功] 所有依赖安装完成！
echo ============================================
echo.

if exist "%~dp0check_ocr_env.py" (
    echo [步骤] 自动运行 OCR 环境检查...
    pushd "%~dp0" >nul
    %PY_CMD% "%~dp0check_ocr_env.py"
    if errorlevel 1 (
        echo.
        echo [提示] OCR 检查未全部通过。若使用 ONNX：install_onnxocr.bat 或 configure_onnxocr_offline.bat
    )
    popd >nul
    echo.
) else (
    echo [提示] 未找到 check_ocr_env.py，跳过 OCR 检查。
    echo.
)

echo 下一步:
echo 1. 启动主程序: %PY_CMD% main.py
echo 2. 若使用 ONNX OCR：install_onnxocr.bat 在线安装；已复制源码可运行 configure_onnxocr_offline.bat
echo 3. 可随时手动复查: %PY_CMD% "%~dp0check_ocr_env.py"
echo.
pause

