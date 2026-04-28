@echo off
chcp 65001 >nul
echo ============================================
echo 修复 dxpyd 模块导入问题
echo ============================================
echo.

REM 检查 x64 目录
if not exist "dxGame\dx_lib\x64\__init__.py" (
    echo [FIX] 创建 dxGame\dx_lib\x64\__init__.py...
    (
        echo # -*- coding: utf-8 -*-
        echo """
        echo x64 位 dxpyd 模块
        echo 根据 Python 版本自动加载对应的 .pyd 文件
        echo """
        echo.
        echo import sys
        echo import os
        echo.
        echo current_dir = os.path.dirname(__file__)
        echo python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
        echo.
        echo pyd_files = [
        echo     f"dxpyd.{python_version}-win_amd64.pyd",
        echo     "dxpyd.cp39-win_amd64.pyd",
        echo     "dxpyd.cp38-win_amd64.pyd",
        echo     "dxpyd.cp312-win_amd64.pyd",
        echo ]
        echo.
        echo dxpyd = None
        echo for pyd_file in pyd_files:
        echo     pyd_path = os.path.join(current_dir, pyd_file)
        echo     if os.path.exists(pyd_path):
        echo         try:
        echo             import importlib.util
        echo             spec = importlib.util.spec_from_file_location("dxpyd", pyd_path)
        echo             dxpyd = importlib.util.module_from_spec(spec)
        echo             spec.loader.exec_module(dxpyd)
        echo             print(f"[OK] Loaded dxpyd: {pyd_file}")
        echo             break
        echo         except Exception as e:
        echo             print(f"[WARN] Failed to load {pyd_file}: {e}")
        echo             continue
        echo.
        echo if dxpyd is None:
        echo     raise ImportError(
        echo         f"Cannot find compatible dxpyd for Python {python_version}. "
        echo         f"Available files: {os.listdir(current_dir)}"
        echo     )
    ) > "dxGame\dx_lib\x64\__init__.py"
    echo [OK] 已创建 x64\__init__.py
) else (
    echo [SKIP] x64\__init__.py 已存在
)

REM 检查 x86 目录
if not exist "dxGame\dx_lib\x86\__init__.py" (
    echo [FIX] 创建 dxGame\dx_lib\x86\__init__.py...
    (
        echo # -*- coding: utf-8 -*-
        echo """
        echo x86 位 dxpyd 模块
        echo 根据 Python 版本自动加载对应的 .pyd 文件
        echo """
        echo.
        echo import sys
        echo import os
        echo.
        echo current_dir = os.path.dirname(__file__)
        echo python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
        echo.
        echo pyd_files = [
        echo     f"dxpyd.{python_version}-win32.pyd",
        echo     "dxpyd.cp39-win32.pyd",
        echo     "dxpyd.cp38-win32.pyd",
        echo ]
        echo.
        echo dxpyd = None
        echo for pyd_file in pyd_files:
        echo     pyd_path = os.path.join(current_dir, pyd_file)
        echo     if os.path.exists(pyd_path):
        echo         try:
        echo             import importlib.util
        echo             spec = importlib.util.spec_from_file_location("dxpyd", pyd_path)
        echo             dxpyd = importlib.util.module_from_spec(spec)
        echo             spec.loader.exec_module(dxpyd)
        echo             print(f"[OK] Loaded dxpyd (x86): {pyd_file}")
        echo             break
        echo         except Exception as e:
        echo             print(f"[WARN] Failed to load {pyd_file}: {e}")
        echo             continue
        echo.
        echo if dxpyd is None:
        echo     raise ImportError(
        echo         f"Cannot find compatible dxpyd (x86) for Python {python_version}. "
        echo         f"Available files: {os.listdir(current_dir)}"
        echo     )
    ) > "dxGame\dx_lib\x86\__init__.py"
    echo [OK] 已创建 x86\__init__.py
) else (
    echo [SKIP] x86\__init__.py 已存在
)

echo.
echo ============================================
echo 修复完成！请重新运行 run.bat
echo ============================================
pause
