# -*- coding: utf-8 -*-
"""
run.bat 启动前调用：缺什么装什么，避免不完整 .venv 导致 ModuleNotFoundError。
仅处理常见早期导入；完整环境仍建议 install_env.bat / repair_env.bat。
"""
import importlib
import subprocess
import sys

PY = sys.executable
MIRROR = ["-i", "https://mirrors.aliyun.com/pypi/simple"]

# (importlib 模块名, pip 参数)
ROWS = [
    ("cv2", ["opencv-contrib-python==4.6.0.66"]),
    ("numpy", ["numpy==1.24.4"]),
    ("PIL", ["Pillow==10.4.0"]),
    ("pyperclip", ["pyperclip==1.11.0"]),
    ("PyQt5", ["PyQt5==5.15.11"]),
    ("vncdotool", ["vncdotool==1.2.0"]),
]


def pip_install(args: list) -> None:
    subprocess.check_call([PY, "-m", "pip", "install", *MIRROR, *args])


def main() -> int:
    for mod, pip_args in ROWS:
        try:
            importlib.import_module(mod)
            continue
        except ImportError:
            pass
        print(f"[ensure_deps] 正在安装缺失模块: {mod} -> pip install {' '.join(pip_args)}")
        try:
            if mod == "cv2":
                subprocess.call(
                    [PY, "-m", "pip", "uninstall", "-y", "opencv-python", "opencv-python-headless"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            pip_install(pip_args)
            importlib.import_module(mod)
            print(f"[ensure_deps] OK: {mod}")
        except Exception as e:
            print(f"[ensure_deps] 失败: {mod} ({e})", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
