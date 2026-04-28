# -*- coding: utf-8 -*-
"""
x64 位 dxpyd 模块
根据 Python 版本自动加载对应的 .pyd 文件
"""

import sys
import os

# 获取当前目录
current_dir = os.path.dirname(__file__)

# 根据 Python 版本选择对应的 pyd 文件
python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"

# 尝试加载对应版本的 pyd
pyd_files = [
    f"dxpyd.{python_version}-win_amd64.pyd",
    "dxpyd.cp39-win_amd64.pyd",
    "dxpyd.cp38-win_amd64.pyd",
    "dxpyd.cp312-win_amd64.pyd",
]

dxpyd = None
for pyd_file in pyd_files:
    pyd_path = os.path.join(current_dir, pyd_file)
    if os.path.exists(pyd_path):
        try:
            # 动态导入
            import importlib.util
            spec = importlib.util.spec_from_file_location("dxpyd", pyd_path)
            dxpyd = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dxpyd)
            print(f"[OK] Loaded dxpyd: {pyd_file}")
            break
        except Exception as e:
            print(f"[WARN] Failed to load {pyd_file}: {e}")
            continue

if dxpyd is None:
    raise ImportError(
        f"Cannot find compatible dxpyd for Python {python_version}. "
        f"Available files: {os.listdir(current_dir)}"
    )
