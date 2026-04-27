# -*- coding: utf-8 -*-
"""
测试 VMware 窗口监控线程
"""
import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vmware_window_monitor import start_vmware_window_monitor, stop_vmware_window_monitor
from dxGame.dx_model import gl_info

class MockController:
    """模拟 Controller 对象"""
    pass

def test_window_monitor():
    """测试窗口监控功能"""
    print("=" * 70)
    print("测试 VMware 窗口监控线程")
    print("=" * 70)
    
    # 创建模拟 controller
    controller = MockController()
    gl_info.controller = controller
    
    print("\n启动窗口监控线程...")
    start_vmware_window_monitor()
    
    print("窗口监控线程已启动，将在后台每 60 秒检查一次窗口状态")
    print("如果检测到窗口卡住（10 秒无变化），会自动激活窗口\n")
    
    try:
        # 运行 3 分钟，观察日志输出
        print("等待 180 秒以观察监控效果...")
        for i in range(180):
            time.sleep(1)
            if i % 30 == 0:
                print(f"  已运行 {i} 秒...")
        
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        print("\n停止窗口监控线程...")
        stop_vmware_window_monitor()
        print("测试完成")


if __name__ == '__main__':
    try:
        test_window_monitor()
    except Exception as e:
        import traceback
        print(f"\n❌ 测试失败: {e}")
        traceback.print_exc()
