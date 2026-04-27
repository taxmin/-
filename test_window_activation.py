# -*- coding: utf-8 -*-
"""
测试窗口监控使用真实句柄激活功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxGame.dx_Window import Window

def test_real_window_activation():
    """测试使用真实窗口句柄激活卡住的窗口"""
    
    print("=" * 80)
    print("测试真实窗口句柄激活功能")
    print("=" * 80)
    print()
    
    # 测试端口
    test_ports = ["5600", "5601"]
    
    for port in test_ports:
        print(f"\n{'='*80}")
        print(f"测试端口: {port}")
        print(f"{'='*80}\n")
        
        # 1. 查找真实窗口句柄
        print("步骤 1: 查找真实游戏窗口句柄...")
        real_hwnd = Window.FindVMwareRealWindowByPort(port)
        
        if real_hwnd == 0:
            print(f"❌ 未找到端口 {port} 的真实窗口")
            continue
        
        print(f"✅ 找到真实窗口句柄: {real_hwnd}")
        
        # 2. 获取窗口信息
        title = Window.GetWindowTitle(real_hwnd)
        class_name = Window.GetWindowClass(real_hwnd)
        rect = Window.GetWindowRect(real_hwnd)
        
        print(f"   窗口标题: '{title}'")
        print(f"   窗口类名: '{class_name}'")
        print(f"   窗口位置: ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
        print(f"   窗口尺寸: {rect[2]-rect[0]} x {rect[3]-rect[1]}")
        
        # 3. 对比旧方法
        print("\n步骤 2: 对比旧方法...")
        old_hwnd = Window.FindVMwareWindowByPort(port)
        print(f"   旧方法句柄 (外层): {old_hwnd}")
        print(f"   新方法句柄 (真实): {real_hwnd}")
        print(f"   是否相同: {'是' if old_hwnd == real_hwnd else '否'}")
        
        # 4. 测试激活功能
        print("\n步骤 3: 测试窗口激活...")
        success = Window.ActivateWindow(real_hwnd)
        
        if success:
            print(f"✅ 成功激活真实窗口 {real_hwnd}")
        else:
            print(f"❌ 激活真实窗口 {real_hwnd} 失败")
        
        # 5. 检查窗口状态
        print("\n步骤 4: 检查窗口状态...")
        is_visible = Window.GetWindowState(real_hwnd, 2)  # 2 = IsWindowVisible
        is_minimized = Window.GetWindowState(real_hwnd, 3)  # 3 = IsIconic
        
        print(f"   窗口可见: {'是' if is_visible else '否'}")
        print(f"   窗口最小化: {'是' if is_minimized else '否'}")
        
        print()
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)
    print("\n说明:")
    print("- 真实窗口句柄用于精确的游戏画面检测和激活")
    print("- 当检测到窗口卡住时，会自动激活真实窗口")
    print("- 这样可以确保游戏画面恢复正常")
    print("=" * 80)


if __name__ == '__main__':
    test_real_window_activation()
