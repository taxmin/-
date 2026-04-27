@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

echo ============================================
echo dx多开框架 - OnnxOCR 纯离线配置（仅路径+可选校验）
echo ============================================
echo 不进行 git 克隆与 pip 下载。无 Python 时仍会写入 ONNXOCR_PATH。
echo.

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "DEST="
if not "%~1"=="" (
    set "DEST=%~f1"
    goto :have_dest
)

if defined ONNXOCR_PATH if exist "!ONNXOCR_PATH!\onnxocr\onnx_paddleocr.py" (
    for %%I in ("!ONNXOCR_PATH!") do set "DEST=%%~fI"
    echo [信息] 使用已有环境变量 ONNXOCR_PATH: !DEST!
    goto :have_dest
)

if exist "%ROOT%\OnnxOCR-main\onnxocr\onnx_paddleocr.py" (
    set "DEST=%ROOT%\OnnxOCR-main"
    echo [信息] 使用项目目录: OnnxOCR-main
    goto :have_dest
)
if exist "%ROOT%\third_party\OnnxOCR-main\onnxocr\onnx_paddleocr.py" (
    set "DEST=%ROOT%\third_party\OnnxOCR-main"
    echo [信息] 使用项目目录: third_party\OnnxOCR-main
    goto :have_dest
)
if exist "%ROOT%\OnnxOCR\onnxocr\onnx_paddleocr.py" (
    set "DEST=%ROOT%\OnnxOCR"
    echo [信息] 使用项目目录: OnnxOCR
    goto :have_dest
)

echo [错误] 未找到有效 OnnxOCR 根目录（需含 onnxocr\onnx_paddleocr.py）。
echo.
echo 用法:
echo   configure_onnxocr_offline.bat
echo   configure_onnxocr_offline.bat "D:\已复制的OnnxOCR根目录"
echo.
pause
exit /b 1

:have_dest
for %%I in ("!DEST!") do set "DEST_ABS=%%~fI"
if not exist "!DEST_ABS!\onnxocr\onnx_paddleocr.py" (
    echo [错误] 不是有效 OnnxOCR 根目录:
    echo        !DEST_ABS!
    pause
    exit /b 1
)

echo.
echo [步骤] 写入用户环境变量 ONNXOCR_PATH（新开 CMD 生效）...
setx ONNXOCR_PATH "!DEST_ABS!" >nul
if errorlevel 1 (
    echo [警告] setx 失败，请手动: setx ONNXOCR_PATH "!DEST_ABS!"
) else (
    echo [成功] ONNXOCR_PATH=!DEST_ABS!
)
set "ONNXOCR_PATH=!DEST_ABS!"

call :run_ocr_check
set "CHK=%errorlevel%"

echo.
if "!CHK!"=="2" (
    echo [完成] ONNXOCR_PATH 已配置。当前电脑未检测到可用 Python，跳过 check_ocr_env.py。
    echo        装好 Python 或放入项目 python\python.exe 后，在项目根执行:
    echo        python\python.exe check_ocr_env.py
    echo        或先运行 install_env.bat 再双击本脚本。
) else if "!CHK!"=="1" (
    echo [完成] ONNXOCR_PATH 已配置。check_ocr_env.py 有未通过项（多为缺 pip 包）。
    echo        修好依赖后可再运行: 同上路径执行 check_ocr_env.py
) else (
    echo [完成] 离线配置已生效，OCR 检查通过。
    echo        其它程序请重开终端以读取 ONNXOCR_PATH。
)
pause
exit /b 0

REM ---------- 尝试用项目内或系统 Python 运行检查 ----------
REM 返回: 0=检查通过, 1=检查失败, 2=未运行检查(无Python/无脚本)

:run_ocr_check
set "PY_CMD="
if exist "%~dp0python\python.exe" set "PY_CMD=%~dp0python\python.exe"
if not defined PY_CMD if exist "%~dp0runtime\python.exe" set "PY_CMD=%~dp0runtime\python.exe"
if not defined PY_CMD if exist "%~dp0.venv\Scripts\python.exe" set "PY_CMD=%~dp0.venv\Scripts\python.exe"
if not defined PY_CMD set "PY_CMD=python"

"%PY_CMD%" --version >nul 2>&1
if errorlevel 1 exit /b 2
if not exist "%ROOT%\check_ocr_env.py" exit /b 2

echo.
echo [步骤] 自动运行 OCR 检查: "%PY_CMD%" "%ROOT%\check_ocr_env.py"
pushd "%ROOT%" >nul
"%PY_CMD%" "%ROOT%\check_ocr_env.py"
set "EC=!errorlevel!"
popd >nul
if "!EC!"=="0" exit /b 0
exit /b 1
