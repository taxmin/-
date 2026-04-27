@echo off
chcp 65001 >nul
echo ============================================
echo DX Framework - 多开并行模式（禁用OCR共享）
echo ============================================
echo.

set "PYTHON_EXE=%~dp0Python38Portable\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found: %PYTHON_EXE%
    pause
    exit /b 1
)

echo [INFO] Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version
echo.

echo [CONFIG] 启用独立 OCR 引擎模式（每个账号独立加载，更并行）
set ONNX_OCR_SHARED=0
echo [OK] ONNX_OCR_SHARED=0 （禁用共享，提升多开并行度）
echo.

echo [CONFIG] Setting ONNX OCR path...
if exist "%~dp0OnnxOCR-main\onnxocr\onnx_paddleocr.py" (
    set "ONNXOCR_PATH=%~dp0OnnxOCR-main"
    echo [OK] ONNXOCR_PATH set
) else (
    echo [WARN] OnnxOCR not found
)

echo.
echo ============================================
echo Starting Dream Fantasy Auto Daily...
echo ============================================
echo.

cd /d "%~dp0"
"%PYTHON_EXE%" main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Program exited with error
    pause
)
