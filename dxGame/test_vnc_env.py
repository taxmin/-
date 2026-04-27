# -*- coding: utf-8 -*-
"""
VNC环境检测脚本
用于检测VNC相关依赖是否正确安装
"""
import sys

def check_environment():
    """检测VNC环境依赖"""
    print("=" * 50)
    print("VNC环境检测")
    print("=" * 50)
    
    errors = []
    
    # 检查cv2
    try:
        import cv2
        print("✓ cv2 (opencv-python) 已安装")
        print(f"  版本: {cv2.__version__}")
    except ImportError as e:
        print("✗ cv2 (opencv-python) 未安装")
        errors.append("opencv-python")
        print(f"  错误: {e}")
    
    # 检查numpy
    try:
        import numpy as np
        print("✓ numpy 已安装")
        print(f"  版本: {np.__version__}")
    except ImportError as e:
        print("✗ numpy 未安装")
        errors.append("numpy")
        print(f"  错误: {e}")
    
    # 检查vncdotool
    try:
        from vncdotool import api
        print("✓ vncdotool 已安装")
        try:
            from vncdotool.client import KEYMAP
            print("  KEYMAP 可用")
        except ImportError:
            print("  ⚠ KEYMAP 导入失败")
    except ImportError as e:
        print("✗ vncdotool 未安装")
        errors.append("vncdotool")
        print(f"  错误: {e}")
    
    # 检查ctypes
    try:
        import ctypes
        print("✓ ctypes 已安装 (Python标准库)")
    except ImportError as e:
        print("✗ ctypes 未安装")
        errors.append("ctypes")
        print(f"  错误: {e}")
    
    print("=" * 50)
    
    if errors:
        print("\n❌ 缺少以下依赖包:")
        print("  安装命令:")
        print(f"  pip install {' '.join(errors)} -i https://mirrors.aliyun.com/pypi/simple")
        return False
    else:
        print("\n✅ 所有依赖已正确安装！")
        return True

if __name__ == '__main__':
    success = check_environment()
    sys.exit(0 if success else 1)

