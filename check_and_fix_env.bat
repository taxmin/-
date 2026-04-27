@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

echo ============================================
echo dx多开框架 - 环境检查与修复工具
echo ============================================
echo.

REM ========== 检测Python ==========
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
    echo [错误] 未检测到Python解释器！
    echo.
    echo 请先将Python放到以下任一目录:
    echo   - python\
    echo   - Python38Portable\
    echo   - runtime\
    echo 或者安装系统Python
    pause
    exit /b 1
)

echo [信息] Python版本:
%PY_CMD% --version
echo.

REM ========== 检查依赖包 ==========
echo ============================================
echo 步骤1: 检查Python依赖包
echo ============================================
echo.

set "MISSING_DEPS="

%PY_CMD% -c "import cv2" >nul 2>&1
if errorlevel 1 (
    echo [缺失] opencv-python
    set "MISSING_DEPS=1"
) else (
    echo [OK] opencv-python
)

%PY_CMD% -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo [缺失] numpy
    set "MISSING_DEPS=1"
) else (
    echo [OK] numpy
)

%PY_CMD% -c "from PIL import Image" >nul 2>&1
if errorlevel 1 (
    echo [缺失] Pillow
    set "MISSING_DEPS=1"
) else (
    echo [OK] Pillow
)

%PY_CMD% -c "import comtypes" >nul 2>&1
if errorlevel 1 (
    echo [缺失] comtypes
    set "MISSING_DEPS=1"
) else (
    echo [OK] comtypes
)

%PY_CMD% -c "import vncdotool" >nul 2>&1
if errorlevel 1 (
    echo [缺失] vncdotool
    set "MISSING_DEPS=1"
) else (
    echo [OK] vncdotool
)

%PY_CMD% -c "import onnxruntime" >nul 2>&1
if errorlevel 1 (
    echo [缺失] onnxruntime
    set "MISSING_DEPS=1"
) else (
    echo [OK] onnxruntime
)

%PY_CMD% -c "import pywin32" >nul 2>&1
if errorlevel 1 (
    echo [缺失] pywin32
    set "MISSING_DEPS=1"
) else (
    echo [OK] pywin32
)

%PY_CMD% -c "import pyperclip" >nul 2>&1
if errorlevel 1 (
    echo [缺失] pyperclip
    set "MISSING_DEPS=1"
) else (
    echo [OK] pyperclip
)

echo.

if defined MISSING_DEPS (
    echo [警告] 检测到缺失的依赖包
    echo.
    choice /C YN /M "是否现在安装缺失的依赖"
    if errorlevel 2 (
        echo [提示] 依赖未安装，程序可能无法正常运行
    ) else (
        echo.
        call "%~dp0install_env.bat"
    )
) else (
    echo [成功] 所有依赖包已安装
)

echo.

REM ========== 检查OnnxOCR ==========
echo ============================================
echo 步骤2: 检查OnnxOCR配置
echo ============================================
echo.

set "ONNXOCR_FOUND=0"

if exist "%~dp0OnnxOCR-main\onnxocr\onnx_paddleocr.py" (
    echo [OK] OnnxOCR-main 目录存在
    set "ONNXOCR_PATH=%~dp0OnnxOCR-main"
    set "ONNXOCR_FOUND=1"
) else if exist "%~dp0third_party\OnnxOCR-main\onnxocr\onnx_paddleocr.py" (
    echo [OK] third_party\OnnxOCR-main 目录存在
    set "ONNXOCR_PATH=%~dp0third_party\OnnxOCR-main"
    set "ONNXOCR_FOUND=1"
) else if exist "%~dp0OnnxOCR\onnxocr\onnx_paddleocr.py" (
    echo [OK] OnnxOCR 目录存在
    set "ONNXOCR_PATH=%~dp0OnnxOCR"
    set "ONNXOCR_FOUND=1"
) else (
    echo [缺失] OnnxOCR 源码目录
    echo.
    echo [提示] OnnxOCR 目录应放在项目根目录下，可选位置:
    echo   - OnnxOCR-main\
    echo   - third_party\OnnxOCR-main\
    echo   - OnnxOCR\
)

if !ONNXOCR_FOUND!==1 (
    echo.
    echo [信息] OnnxOCR路径: !ONNXOCR_PATH!
    
    REM 检查环境变量
    if "!ONNXOCR_PATH!"=="%ONNXOCR_PATH%" (
        echo [OK] ONNXOCR_PATH 环境变量已正确设置
    ) else (
        echo [提示] ONNXOCR_PATH 环境变量未设置或不匹配
        echo.
        choice /C YN /M "是否设置ONNXOCR_PATH环境变量"
        if errorlevel 2 (
            echo [提示] run.bat 会在启动时临时设置此变量
        ) else (
            setx ONNXOCR_PATH "!ONNXOCR_PATH!" >nul
            if errorlevel 1 (
                echo [错误] 设置环境变量失败
            ) else (
                echo [成功] ONNXOCR_PATH 已设置为: !ONNXOCR_PATH!
                echo [注意] 需要重新打开CMD窗口才能生效
            )
        )
    )
)

echo.

REM ========== 检查资源文件 ==========
echo ============================================
echo 步骤3: 检查资源文件
echo ============================================
echo.

if exist "%~dp0资源\图片" (
    echo [OK] 资源\图片 目录存在
) else (
    echo [缺失] 资源\图片 目录
)

if exist "%~dp0资源\配置\主界面配置.ini" (
    echo [OK] 配置文件存在
) else (
    echo [警告] 配置文件不存在，首次运行时会自动创建
)

if exist "%~dp0资源\日志" (
    echo [OK] 日志目录存在
) else (
    echo [提示] 日志目录不存在，首次运行时会自动创建
)

echo.

REM ========== 检查关键代码文件 ==========
echo ============================================
echo 步骤4: 检查关键代码文件
echo ============================================
echo.

if exist "%~dp0main.py" (
    echo [OK] main.py
) else (
    echo [错误] main.py 缺失！
)

if exist "%~dp0dxGame\dx_OnnxOCR.py" (
    echo [OK] dxGame\dx_OnnxOCR.py
) else (
    echo [错误] dxGame\dx_OnnxOCR.py 缺失！
)

if exist "%~dp0dxGame\dx_vnc.py" (
    echo [OK] dxGame\dx_vnc.py
) else (
    echo [错误] dxGame\dx_vnc.py 缺失！
)

if exist "%~dp0app\controller.py" (
    echo [OK] app\controller.py
) else (
    echo [错误] app\controller.py 缺失！
)

echo.

REM ========== 总结 ==========
echo ============================================
echo 环境检查完成
echo ============================================
echo.
echo 下一步操作:
echo   1. 如果有缺失的依赖，运行: install_env.bat
echo   2. 如果OnnxOCR未配置，运行: configure_onnxocr_offline.bat
echo   3. 一切就绪后，运行: run.bat 启动程序
echo.

pause
