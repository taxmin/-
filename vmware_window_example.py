# -*- coding: utf-8 -*-
"""
VMware 窗口管理使用示例

演示如何使用 Window 类来查找和管理 VMware 虚拟机窗口
"""

from dxGame.dx_Window import Window
from dxGame.dx_core import user32
import time


def example_find_vmware_window():
    """示例1: 查找 VMware 窗口句柄"""
    
    # 通过端口号查找窗口
    port = "5600"
    hwnd = Window.FindVMwareWindowByPort(port)
    
    if hwnd:
        print(f"✓ 找到端口 {port} 的窗口句柄: {hwnd}")
        
        # 获取窗口信息
        title = Window.GetWindowTitle(hwnd)
        print(f"  窗口标题: '{title}'")
        
        rect = Window.GetWindowRect(hwnd)
        print(f"  窗口位置: {rect}")
    else:
        print(f"❌ 未找到端口 {port} 的窗口")
    
    return hwnd


def example_activate_window():
    """示例2: 激活（前置）窗口"""
    
    hwnd = Window.FindVMwareWindowByPort("5600")
    
    if hwnd:
        # 激活窗口（将其带到前台）
        success = Window.ActivateWindow(hwnd)
        
        if success:
            print(f"✓ 窗口 {hwnd} 已激活并前置")
        else:
            print(f"❌ 激活窗口失败")


def example_check_frozen():
    """示例3: 检查窗口是否卡住"""
    
    hwnd = Window.FindVMwareWindowByPort("5600")
    
    if hwnd:
        # 检查窗口是否在 5 分钟内无变化
        is_frozen = Window.CheckWindowFrozen(hwnd, timeout_seconds=300)
        
        if is_frozen:
            print("⚠️ 窗口可能已卡住，需要激活")
            # 激活窗口以恢复
            Window.ActivateWindow(hwnd)
        else:
            print("✓ 窗口正常运行")


def example_auto_recover_frozen_window():
    """
    示例4: 自动检测并恢复卡住的窗口
    
    这个函数可以在你的任务循环中定期调用
    """
    port = "5600"
    
    # 1. 查找窗口
    hwnd = Window.FindVMwareWindowByPort(port)
    
    if not hwnd:
        print(f"❌ 未找到端口 {port} 的窗口")
        return False
    
    # 2. 检查窗口是否卡住（每 5 分钟检查一次）
    print(f"检查窗口 {hwnd} 是否卡住...")
    is_frozen = Window.CheckWindowFrozen(hwnd, timeout_seconds=300)
    
    if is_frozen:
        print(f"⚠️ 检测到窗口 {hwnd} 已卡住，尝试恢复...")
        
        # 3. 激活窗口
        success = Window.ActivateWindow(hwnd)
        
        if success:
            print(f"✓ 窗口 {hwnd} 已激活恢复")
            
            # 4. 等待一下让窗口响应
            time.sleep(2)
            
            # 5. 可以发送一些按键来确保窗口响应
            # 例如：按 ESC 键关闭可能的弹窗
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            # 这里可以添加你的按键逻辑
            
            return True
        else:
            print(f"❌ 激活窗口失败")
            return False
    else:
        print(f"✓ 窗口 {hwnd} 正常运行")
        return True


def example_in_task_loop():
    """
    示例5: 在任务循环中使用
    
    这是一个完整的示例，展示如何在你的人物任务中集成窗口监控
    """
    port = "5600"
    check_interval = 300  # 每 5 分钟检查一次
    
    print(f"开始监控端口 {port} 的窗口状态...")
    last_check_time = time.time()
    
    while True:
        current_time = time.time()
        
        # 定期检查窗口状态
        if current_time - last_check_time >= check_interval:
            print("\n=== 定期窗口健康检查 ===")
            
            hwnd = Window.FindVMwareWindowByPort(port)
            
            if hwnd:
                # 检查窗口是否卡住
                is_frozen = Window.CheckWindowFrozen(hwnd, timeout_seconds=10)  # 快速检查
                
                if is_frozen:
                    print("⚠️ 检测到窗口卡住，正在恢复...")
                    Window.ActivateWindow(hwnd)
                    time.sleep(2)
                    print("✓ 窗口已恢复")
                else:
                    print("✓ 窗口状态正常")
            else:
                print("❌ 未找到窗口")
            
            last_check_time = current_time
        
        # 这里执行你的正常任务逻辑
        # ...
        
        time.sleep(1)  # 避免 CPU 占用过高


if __name__ == '__main__':
    print("=" * 70)
    print("VMware 窗口管理示例")
    print("=" * 70)
    
    # 运行示例
    print("\n【示例1】查找 VMware 窗口")
    print("-" * 70)
    example_find_vmware_window()
    
    print("\n【示例2】激活窗口")
    print("-" * 70)
    example_activate_window()
    
    print("\n" + "=" * 70)
    print("提示: 要使用自动恢复功能，请调用 example_auto_recover_frozen_window()")
    print("      或在你的任务循环中集成 example_in_task_loop() 的逻辑")
    print("=" * 70)
