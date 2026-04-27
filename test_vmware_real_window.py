# -*- coding: utf-8 -*-
"""
测试 VMware 多层级窗口句柄查找功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxGame.dx_Window import Window

def test_find_real_window():
    """测试查找真实窗口句柄"""
    
    print("=" * 80)
    print("VMware 多层级窗口句柄查找测试")
    print("=" * 80)
    print()
    
    # 测试端口列表
    test_ports = ["5600", "5601"]
    
    for port in test_ports:
        print(f"\n{'='*80}")
        print(f"测试端口: {port}")
        print(f"{'='*80}\n")
        
        try:
            # 调用多层级查找方法
            real_hwnd = Window.FindVMwareRealWindowByPort(port)
            
            if real_hwnd != 0:
                print(f"\n✅ 成功！端口 {port} 的真实窗口句柄: {real_hwnd}")
                
                # 验证窗口信息
                title = Window.GetWindowTitle(real_hwnd)
                class_name = Window.GetWindowClass(real_hwnd)
                rect = Window.GetWindowRect(real_hwnd)
                
                print(f"   窗口标题: '{title}'")
                print(f"   窗口类名: '{class_name}'")
                print(f"   窗口位置: ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
                print(f"   窗口尺寸: {rect[2]-rect[0]} x {rect[3]-rect[1]}")
                
                # 对比旧方法找到的句柄
                old_hwnd = Window.FindVMwareWindowByPort(port)
                print(f"\n   对比旧方法:")
                print(f"   - 旧方法句柄: {old_hwnd}")
                print(f"   - 新方法句柄: {real_hwnd}")
                print(f"   - 是否相同: {'是' if old_hwnd == real_hwnd else '否'}")
                
            else:
                print(f"\n❌ 失败！未找到端口 {port} 的真实窗口句柄")
                
        except Exception as e:
            print(f"\n❌ 异常: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == '__main__':
    test_find_real_window()
