# -*- coding: utf-8 -*-
"""
VNC模块依赖检查脚本
运行此脚本检查所有必需的依赖是否已正确安装
"""
import sys

def check_dependencies():
    """检查VNC模块所需的所有依赖"""
    print("=" * 60)
    print("VNC模块依赖检查")
    print("=" * 60)
    print()
    
    all_ok = True
    missing_deps = []
    
    # 检查标准库（不需要安装）
    print("检查标准库...")
    stdlib_modules = ['ctypes', 'time', 'logging', 'sys', 'tempfile', 'os']
    for module in stdlib_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} - 标准库不应该缺失！")
            all_ok = False
    
    print()
    
    # 检查第三方库
    print("检查第三方库...")
    
    # 1. cv2 (opencv-python)
    try:
        import cv2
        print(f"  ✓ cv2 (opencv-python) - 版本: {cv2.__version__}")
    except ImportError:
        print("  ✗ cv2 (opencv-python) - 未安装")
        missing_deps.append("opencv-python")
        all_ok = False
    
    # 2. numpy
    try:
        import numpy as np
        print(f"  ✓ numpy - 版本: {np.__version__}")
    except ImportError:
        print("  ✗ numpy - 未安装")
        missing_deps.append("numpy")
        all_ok = False
    
    # 3. vncdotool
    try:
        from vncdotool import api
        from vncdotool.client import KEYMAP
        print("  ✓ vncdotool - 已安装")
        try:
            # 尝试获取版本
            import vncdotool
            if hasattr(vncdotool, '__version__'):
                print(f"    版本: {vncdotool.__version__}")
        except:
            pass
    except ImportError as e:
        print(f"  ✗ vncdotool - 未安装 ({e})")
        missing_deps.append("vncdotool")
        all_ok = False
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("✅ 所有依赖已正确安装！")
        print()
        print("可以开始使用VNC模块了。")
        print("测试命令: python vnc_copy_from_ai.py")
        return True
    else:
        print("❌ 缺少以下依赖包:")
        print()
        print("安装命令:")
        print(f"  pip install {' '.join(missing_deps)} -i https://mirrors.aliyun.com/pypi/simple")
        print()
        print("或者使用完整命令:")
        print("  pip install opencv-python numpy vncdotool -i https://mirrors.aliyun.com/pypi/simple")
        return False

if __name__ == '__main__':
    success = check_dependencies()
    sys.exit(0 if success else 1)

