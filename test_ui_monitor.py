# -*- coding: utf-8 -*-
"""
测试UI性能监控功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("测试UI性能监控功能")
print("="*60)

# 检查依赖
print("\n1. 检查依赖库...")
try:
    import psutil
    print("   ✅ psutil 已安装")
except ImportError:
    print("   ❌ psutil 未安装，请运行: pip install psutil")
    sys.exit(1)

try:
    from app.stability_optimizer import km_lock_enhanced, window_recovery_queue
    print("   ✅ 稳定性优化模块已安装")
except ImportError:
    print("   ⚠️ 稳定性优化模块未找到（可选）")

try:
    import tkinter as tk
    from tkinter import ttk
    print("   ✅ tkinter 可用")
except ImportError:
    print("   ❌ tkinter 不可用")
    sys.exit(1)

print("\n2. 检查文件修改...")
files_to_check = [
    "app/view.py",
    "app/stability_optimizer.py"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✅ {file} 存在")
    else:
        print(f"   ❌ {file} 不存在")

print("\n3. 启动UI测试...")
print("   即将打开主窗口，请检查:")
print("   - 是否有两个标签页（任务列表、性能监控）")
print("   - 性能监控页面是否正常显示")
print("   - 数据是否每5秒自动更新")
print("\n   按 Ctrl+C 或关闭窗口退出测试\n")

try:
    from app.view import Win
    from app.controller import Controller
    from task_list.task import Task
    
    print("   正在创建控制器...")
    控制器 = Controller(Task)
    
    print("   正在创建界面...")
    界面 = Win(控制器)
    界面.wm_title("梦幻手游自动日常 - 性能监控测试")
    
    print("   启动主循环...\n")
    界面.mainloop()
    
except KeyboardInterrupt:
    print("\n\n⚠️ 用户中断测试")
except Exception as e:
    print(f"\n\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
