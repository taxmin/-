# -*- coding: utf-8 -*-
"""
启动前快速检查：与 main → task 早期 import 相关的模块是否齐全。
用法: .venv\Scripts\python.exe smoke_imports.py
"""
import importlib
import sys

# (模块名, pip 包提示)
CHECKS = [
    ("cv2", "opencv-contrib-python==4.6.0.66"),
    ("numpy", "numpy"),
    ("PIL", "Pillow"),
    ("pyperclip", "pyperclip"),
    ("PyQt5", "PyQt5"),
    ("vncdotool", "vncdotool"),
]


def main() -> int:
    failed = []
    for mod, pip_hint in CHECKS:
        try:
            importlib.import_module(mod)
        except ImportError:
            failed.append((mod, pip_hint))
            print(f"[缺失] {mod}  ←  pip install {pip_hint}")
        else:
            print(f"[正常] {mod}")

    if failed:
        print()
        print("请在本目录运行 repair_env.bat，或: pip install -r requirements.txt")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
