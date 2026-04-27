@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

echo ============================================
echo Clean Test Environment
echo ============================================
echo.

set "TEST_PATH=E:\梦幻手游环境测试\dx多开框架\dx多开框架"

if not exist "%TEST_PATH%" (
    echo [ERROR] Path not found: %TEST_PATH%
    pause
    exit /b 1
)

cd /d "%TEST_PATH%"

echo Files to delete:
echo.

REM Temporary files
set "FILES_TO_DELETE="

REM get-pip files (temporary installation files)
if exist "get-pip.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% get-pip.py"
if exist "get-pip-3.8.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% get-pip-3.8.py"

REM Python installer
if exist "python-3.8.10-amd64.exe" set "FILES_TO_DELETE=%FILES_TO_DELETE% python-3.8.10-amd64.exe"

REM Old/duplicate requirement files
if exist "requirements.txt" if exist "requirement.txt" set "FILES_TO_DELETE=%FILES_TO_DELETE% requirements.txt"

REM Shortcut file
if exist "dx多开框架.lnk" set "FILES_TO_DELETE=%FILES_TO_DELETE% dx多开框架.lnk"

REM Test/debug scripts (keep only essential ones)
if exist "check_env_improved.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% check_env_improved.py"
if exist "check_env_simple.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% check_env_simple.py"
if exist "env_check_report.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% env_check_report.py"
if exist "ensure_deps.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% ensure_deps.py"
if exist "smoke_imports.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% smoke_imports.py"

REM ONNX test scripts (keep test_portable_env.py and test_env.bat)
if exist "test_onnx_diagnose.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% test_onnx_diagnose.py"
if exist "test_onnx_health_check.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% test_onnx_health_check.py"
if exist "test_onnx_ocr.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% test_onnx_ocr.py"
if exist "test_onnx_quick.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% test_onnx_quick.py"
if exist "test_onnx_simple.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% test_onnx_simple.py"

REM VNC test scripts
if exist "test_vnc_integration.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% test_vnc_integration.py"
if exist "test_vnc_stability.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% test_vnc_stability.py"

REM Repair scripts
if exist "repair_env.bat" set "FILES_TO_DELETE=%FILES_TO_DELETE% repair_env.bat"
if exist "repair_opencv.bat" set "FILES_TO_DELETE=%FILES_TO_DELETE% repair_opencv.bat"
if exist "repair_pillow.bat" set "FILES_TO_DELETE=%FILES_TO_DELETE% repair_pillow.bat"
if exist "fix_venv_after_copy.bat" set "FILES_TO_DELETE=%FILES_TO_DELETE% fix_venv_after_copy.bat"

REM Setup scripts
if exist "setup_python_portable.bat" set "FILES_TO_DELETE=%FILES_TO_DELETE% setup_python_portable.bat"
if exist "setup_test_env.bat" set "FILES_TO_DELETE=%FILES_TO_DELETE% setup_test_env.bat"

REM Monitoring/optimization scripts (not needed for runtime)
if exist "monitor_ocr_stability.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% monitor_ocr_stability.py"
if exist "performance_monitor.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% performance_monitor.py"
if exist "parallel_executor.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% parallel_executor.py"
if exist "example_optimization.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% example_optimization.py"
if exist "example_status_check.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% example_status_check.py"
if exist "cache_manager.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% cache_manager.py"

REM Duplicate CV.py (keep dxGame/dx_cv.py)
if exist "CV.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% CV.py"

REM comtypes .pyd files (not needed, using pip installed version)
if exist "comtypes.cp38-win32.pyd" set "FILES_TO_DELETE=%FILES_TO_DELETE% comtypes.cp38-win32.pyd"
if exist "comtypes.cp38-win_amd64.pyd" set "FILES_TO_DELETE=%FILES_TO_DELETE% comtypes.cp38-win_amd64.pyd"
if exist "comtypes.cp39-win32.pyd" set "FILES_TO_DELETE=%FILES_TO_DELETE% comtypes.cp39-win32.pyd"
if exist "comtypes.cp39-win_amd64.pyd" set "FILES_TO_DELETE=%FILES_TO_DELETE% comtypes.cp39-win_amd64.pyd"

REM Extra documentation (keep only essential ones)
if exist "README_嵌入式与绿色Python.txt" set "FILES_TO_DELETE=%FILES_TO_DELETE% README_嵌入式与绿色Python.txt"
if exist "README_分发说明.txt" set "FILES_TO_DELETE=%FILES_TO_DELETE% README_分发说明.txt"
if exist "打包说明_维护者.txt" set "FILES_TO_DELETE=%FILES_TO_DELETE% 打包说明_维护者.txt"
if exist "修改说明.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% 修改说明.md"
if exist "性能优化建议.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% 性能优化建议.md"
if exist "OPTIMIZATION_GUIDE.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% OPTIMIZATION_GUIDE.md"
if exist "OCR启动验证指南.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% OCR启动验证指南.md"
if exist "ONNX_OCR健康检查说明.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% ONNX_OCR健康检查说明.md"
if exist "VNC连接问题恢复指南.txt" set "FILES_TO_DELETE=%FILES_TO_DELETE% VNC连接问题恢复指南.txt"
if exist "环境安装说明.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% 环境安装说明.md"
if exist "环境检查报告.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% 环境检查报告.md"
if exist "依赖清单.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% 依赖清单.md"
if exist "项目功能清单.md" set "FILES_TO_DELETE=%FILES_TO_DELETE% 项目功能清单.md"

REM Requirements variants
if exist "requirements-torch-cuda.txt" set "FILES_TO_DELETE=%FILES_TO_DELETE% requirements-torch-cuda.txt"

REM Install script variants (keep install_env.bat and install_env.ps1)
if exist "install_onnxocr.bat" set "FILES_TO_DELETE=%FILES_TO_DELETE% install_onnxocr.bat"

REM Check scripts (keep check_ocr_env.py, check_and_fix_env.bat, check_system_status.py)
if exist "check_vnc_connection.py" set "FILES_TO_DELETE=%FILES_TO_DELETE% check_vnc_connection.py"

REM Display what will be deleted
if defined FILES_TO_DELETE (
    echo The following files will be deleted:
    for %%F in (%FILES_TO_DELETE%) do echo   - %%F
    echo.
    
    choice /C YN /M "Continue with deletion"
    if errorlevel 2 (
        echo Cancelled.
        pause
        exit /b 0
    )
    
    echo.
    echo Deleting files...
    for %%F in (%FILES_TO_DELETE%) do (
        if exist "%%F" (
            del /F /Q "%%F"
            echo Deleted: %%F
        )
    )
    
    echo.
    echo [OK] Cleanup completed.
) else (
    echo No files to delete.
)

echo.
echo Cleaning directories...

REM Remove __pycache__ folders
if exist "__pycache__" (
    rmdir /S /Q "__pycache__"
    echo Removed: __pycache__
)

REM Remove .venv if exists (using portable Python)
if exist ".venv" (
    echo Found .venv directory. This can be removed if using portable Python.
    choice /C YN /M "Remove .venv directory"
    if errorlevel 2 (
        echo Kept .venv
    ) else (
        rmdir /S /Q ".venv"
        echo Removed: .venv
    )
)

REM Remove Temporary folder contents (keep the folder)
if exist "Temporary" (
    echo Cleaning Temporary folder...
    del /F /Q "Temporary\*.*" 2>nul
    for /d %%D in ("Temporary\*") do rmdir /S /Q "%%D" 2>nul
    echo Cleaned: Temporary\
)

REM Remove .idea and .vscode (IDE configs)
if exist ".idea" (
    echo Found .idea directory (PyCharm config).
    choice /C YN /M "Remove .idea directory"
    if errorlevel 2 (
        echo Kept .idea
    ) else (
        rmdir /S /Q ".idea"
        echo Removed: .idea
    )
)

if exist ".vscode" (
    echo Found .vscode directory (VSCode config).
    choice /C YN /M "Remove .vscode directory"
    if errorlevel 2 (
        echo Kept .vscode
    ) else (
        rmdir /S /Q ".vscode"
        echo Removed: .vscode
    )
)

REM Remove third_party if empty or not used
if exist "third_party" (
    dir "third_party" /b | findstr "." >nul 2>&1
    if errorlevel 1 (
        echo third_party is empty, removing...
        rmdir /S /Q "third_party"
        echo Removed: third_party
    ) else (
        echo third_party has content, keeping it.
    )
)

echo.
echo ============================================
echo Cleanup Complete!
echo ============================================
echo.
echo Remaining important files:
echo   - run.bat (startup script)
echo   - install_env.bat (install dependencies)
echo   - check_and_fix_env.bat (environment check)
echo   - test_env.bat (environment test)
echo   - test_portable_env.py (test script)
echo   - check_ocr_env.py (OCR check)
echo   - check_system_status.py (system status)
echo   - 快速开始.txt (quick start guide)
echo   - 分发清单.txt (distribution checklist)
echo   - BAT脚本说明.txt (script documentation)
echo   - 便携版部署指南.md (deployment guide)
echo   - 便携化改造说明.md (transformation docs)
echo   - README_便携化完成.md (completion summary)
echo.

pause

