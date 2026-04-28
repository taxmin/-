# dxpyd 模块导入问题修复指南

## 问题描述
```
ImportError: cannot import name 'dxpyd' from 'dxGame.dx_lib.x64' (unknown location)
```

## 原因
`dxGame/dx_lib/x64/` 和 `dxGame/dx_lib/x86/` 目录缺少 `__init__.py` 文件，导致 Python 无法将其识别为模块。

## 解决方案

### 方法1：运行修复脚本（推荐）
双击运行 `修复dxpyd导入.bat`，它会自动创建缺失的文件。

### 方法2：手动创建文件

#### 1. 创建 `dxGame/dx_lib/x64/__init__.py`
```python
# -*- coding: utf-8 -*-
import sys
import os

current_dir = os.path.dirname(__file__)
python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"

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
```

#### 2. 创建 `dxGame/dx_lib/x86/__init__.py`
```python
# -*- coding: utf-8 -*-
import sys
import os

current_dir = os.path.dirname(__file__)
python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"

pyd_files = [
    f"dxpyd.{python_version}-win32.pyd",
    "dxpyd.cp39-win32.pyd",
    "dxpyd.cp38-win32.pyd",
]

dxpyd = None
for pyd_file in pyd_files:
    pyd_path = os.path.join(current_dir, pyd_file)
    if os.path.exists(pyd_path):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("dxpyd", pyd_path)
            dxpyd = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dxpyd)
            print(f"[OK] Loaded dxpyd (x86): {pyd_file}")
            break
        except Exception as e:
            print(f"[WARN] Failed to load {pyd_file}: {e}")
            continue

if dxpyd is None:
    raise ImportError(
        f"Cannot find compatible dxpyd (x86) for Python {python_version}. "
        f"Available files: {os.listdir(current_dir)}"
    )
```

### 方法3：从原项目复制
从 `F:\游戏多开隔离技术\梦幻手游日常多开\dxGame\dx_lib\x64\` 和 `x86\` 目录复制 `__init__.py` 文件到新项目的对应位置。

## 验证修复
运行 `run.bat`，应该看到：
```
[OK] Loaded dxpyd: dxpyd.cp38-win_amd64.pyd
```

## 注意事项
1. 确保 `.pyd` 文件存在（如 `dxpyd.cp38-win_amd64.pyd`）
2. Python 版本必须与 `.pyd` 文件匹配
3. 如果是 64 位系统，使用 `x64` 目录；32 位系统使用 `x86` 目录
