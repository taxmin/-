# -*- coding: utf-8 -*-
"""
测试 GUI 是否能正常启动
"""
import sys
import os

print("测试：GUI 启动")
print("=" * 60)

try:
    from app.controller import Controller
    from app.view import Win
    from task_list.task import Task
    
    print("✓ 模块导入成功")
    
    # 创建控制器
    print("创建控制器...")
    控制器 = Controller(Task)
    print("✓ 控制器创建成功")
    
    # 创建界面
    print("创建界面...")
    界面 = Win(控制器)
    界面.wm_title("梦幻手游自动日常 - 测试模式")
    print("✓ 界面创建成功")
    
    print("\n现在应该能看到GUI窗口")
    print("如果窗口出现，说明程序正常运行")
    print("关闭窗口后，测试完成")
    
    # 启动主循环
    界面.mainloop()
    
    print("\n✅ GUI 测试完成！")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
