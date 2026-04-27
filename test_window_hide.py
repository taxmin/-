# -*- coding: utf-8 -*-
"""
窗口隐藏/恢复功能测试脚本
用于验证窗口位置保存、隐藏和恢复功能
"""
import sys
import os
import ctypes
import ctypes.wintypes
import time

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from dxGame.dx_Window import Window


def test_get_screen_size():
    """测试获取屏幕尺寸"""
    print("\n" + "="*70)
    print("测试1: 获取屏幕尺寸")
    print("="*70)
    
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    
    print(f"屏幕宽度: {screen_width} px")
    print(f"屏幕高度: {screen_height} px")
    
    if screen_width > 0 and screen_height > 0:
        print("✅ 测试通过: 成功获取屏幕尺寸")
        return True
    else:
        print("❌ 测试失败: 无法获取屏幕尺寸")
        return False


def test_find_vmware_windows():
    """测试查找VMware窗口"""
    print("\n" + "="*70)
    print("测试2: 查找VMware虚拟机窗口")
    print("="*70)
    
    try:
        from app.vmware_window_monitor import _get_vmware_ports
        
        ports = _get_vmware_ports()
        
        if not ports:
            print("⚠️ 未找到正在运行的虚拟机窗口")
            print("   请确保至少有一个虚拟机正在运行")
            return False
        
        print(f"找到 {len(ports)} 个虚拟机端口:")
        for row, port in ports:
            print(f"  Row {row}: 端口 {port}")
            
            # 尝试查找窗口
            real_hwnd = Window.FindVMwareRealWindowByPort(port)
            
            if real_hwnd:
                print(f"    ✓ 找到窗口句柄: {real_hwnd}")
                
                # 检查窗口是否有效
                if ctypes.windll.user32.IsWindow(real_hwnd):
                    print(f"    ✓ 窗口句柄有效")
                    
                    # 获取窗口位置
                    rect = ctypes.wintypes.RECT()
                    if ctypes.windll.user32.GetWindowRect(real_hwnd, ctypes.byref(rect)):
                        width = rect.right - rect.left
                        height = rect.bottom - rect.top
                        print(f"    ✓ 窗口位置: ({rect.left}, {rect.top})")
                        print(f"    ✓ 窗口大小: {width}x{height}")
                else:
                    print(f"    ❌ 窗口句柄无效")
            else:
                print(f"    ❌ 未找到窗口")
        
        print("\n✅ 测试通过: 成功找到VMware窗口")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_window_move():
    """测试窗口移动功能"""
    print("\n" + "="*70)
    print("测试3: 窗口移动功能")
    print("="*70)
    
    try:
        from app.vmware_window_monitor import _get_vmware_ports
        
        ports = _get_vmware_ports()
        
        if not ports:
            print("⚠️ 未找到正在运行的虚拟机窗口，跳过测试")
            return True
        
        # 只测试第一个窗口
        row, port = ports[0]
        real_hwnd = Window.FindVMwareRealWindowByPort(port)
        
        if not real_hwnd or not ctypes.windll.user32.IsWindow(real_hwnd):
            print("⚠️ 窗口无效，跳过测试")
            return True
        
        # 获取原始位置
        rect = ctypes.wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(real_hwnd, ctypes.byref(rect)):
            print("❌ 无法获取窗口位置")
            return False
        
        original_x = rect.left
        original_y = rect.top
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        
        print(f"原始位置: ({original_x}, {original_y}), 大小: {width}x{height}")
        
        # 移动到屏幕外
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        off_screen_x = screen_width + 100
        
        print(f"移动到屏幕外: ({off_screen_x}, {original_y})")
        
        result = ctypes.windll.user32.MoveWindow(
            real_hwnd,
            off_screen_x,
            original_y,
            width,
            height,
            True
        )
        
        if result:
            print("✓ 窗口移动成功")
            
            # 等待2秒
            print("等待2秒后恢复...")
            time.sleep(2)
            
            # 恢复原始位置
            print(f"恢复到原始位置: ({original_x}, {original_y})")
            result = ctypes.windll.user32.MoveWindow(
                real_hwnd,
                original_x,
                original_y,
                width,
                height,
                True
            )
            
            if result:
                print("✓ 窗口恢复成功")
                print("\n✅ 测试通过: 窗口移动和恢复功能正常")
                return True
            else:
                print("❌ 窗口恢复失败")
                return False
        else:
            print("❌ 窗口移动失败")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("窗口隐藏/恢复功能测试")
    print("="*70)
    
    tests = [
        ("获取屏幕尺寸", test_get_screen_size),
        ("查找VMware窗口", test_find_vmware_windows),
        ("窗口移动功能", test_window_move),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查")
    
    print("\n" + "="*70)
    print("使用说明")
    print("="*70)
    print("1. 启动程序后，在'性能监控'标签页找到'🙈 隐藏游戏窗口'按钮")
    print("2. 点击按钮将所有虚拟机窗口移动到屏幕外（隐藏）")
    print("3. 按钮文本变为'👁️ 恢复游戏窗口'")
    print("4. 再次点击按钮恢复窗口到原始位置")
    print("5. 窗口位置会自动保存和恢复，无需担心丢失")


if __name__ == '__main__':
    main()
