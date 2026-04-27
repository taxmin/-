# -*- coding: utf-8 -*-
"""
测试 VMware 窗口句柄查找功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxGame.dx_Window import Window

def test_find_vmware_window():
    """测试查找 VMware 窗口"""
    print("=" * 60)
    print("测试 VMware 窗口句柄查找")
    print("=" * 60)
    
    # 测试端口号
    test_ports = ["5600", "5601"]
    
    for port in test_ports:
        print(f"\n查找端口 {port} 的 VMware 窗口...")
        hwnd = Window.FindVMwareWindowByPort(port)
        
        if hwnd:
            print(f"✓ 找到窗口句柄: {hwnd}")
            
            # 获取窗口信息
            title = Window.GetWindowTitle(hwnd)
            print(f"  窗口标题: '{title}'")
            
            rect = Window.GetWindowRect(hwnd)
            print(f"  窗口位置: {rect}")
            
            # 测试激活窗口
            print(f"\n尝试激活窗口 {hwnd}...")
            success = Window.ActivateWindow(hwnd)
            if success:
                print(f"✓ 窗口 {hwnd} 已激活")
            else:
                print(f"❌ 激活窗口失败")
        else:
            print(f"❌ 未找到端口 {port} 的窗口")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_find_vmware_window()
    except Exception as e:
        import traceback
        print(f"\n❌ 测试失败: {e}")
        traceback.print_exc()
