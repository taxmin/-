# -*- coding: utf-8 -*-
"""
物理鼠标点击测试脚本
用于测试窗口激活时的物理鼠标点击功能
"""
import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxGame.dx_Window import Window
from app.vmware_window_monitor import _physical_mouse_click


def test_physical_click():
    """测试物理鼠标点击功能"""
    print("=" * 60)
    print("物理鼠标点击测试")
    print("=" * 60)
    
    # 1. 查找 VMware 窗口
    port = "5600"
    print(f"\n1. 查找端口 {port} 的 VMware 窗口...")
    
    hwnd = Window.FindVMwareRealWindowByPort(port)
    
    if not hwnd:
        print(f"❌ 未找到端口 {port} 的窗口")
        return
    
    print(f"✓ 找到窗口句柄: {hwnd}")
    
    # 2. 获取窗口位置
    print(f"\n2. 获取窗口位置信息...")
    rect = Window.GetWindowRect(hwnd)
    if rect:
        print(f"   窗口位置: 左上({rect[0]}, {rect[1]}), 右下({rect[2]}, {rect[3]})")
        print(f"   窗口大小: {rect[2] - rect[0]} x {rect[3] - rect[1]}")
    
    # 3. 测试物理点击
    print(f"\n3. 准备执行物理鼠标点击...")
    print(f"   点击区域: (191, 229) - (739, 561)")
    print(f"   ⚠️  注意：鼠标将会移动并点击窗口！")
    
    input("\n按 Enter 键开始测试（或 Ctrl+C 取消）...")
    
    print(f"\n4. 执行物理点击...")
    success = _physical_mouse_click(hwnd, x1=191, y1=229, x2=739, y2=561)
    
    if success:
        print(f"✓ 物理点击成功！")
    else:
        print(f"❌ 物理点击失败")
    
    print(f"\n5. 测试完成")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_physical_click()
    except KeyboardInterrupt:
        print("\n\n用户取消了测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
