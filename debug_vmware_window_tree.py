# -*- coding: utf-8 -*-
"""
调试 VMware 窗口层级结构
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxGame.dx_Window import Window
import ctypes

def print_window_tree(hwnd, indent=0):
    """递归打印窗口树"""
    prefix = "  " * indent
    title = Window.GetWindowTitle(hwnd)
    class_name = Window.GetWindowClass(hwnd)
    
    print(f"{prefix}HWND={hwnd}, 类名='{class_name}', 标题='{title}'")
    
    # 枚举子窗口
    def enum_child(hwnd_child, lParam):
        print_window_tree(hwnd_child, indent + 1)
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    ctypes.windll.user32.EnumChildWindows(hwnd, WNDENUMPROC(enum_child), 0)


def debug_vmware_windows():
    """调试 VMware 窗口结构"""
    import psutil
    
    print("=" * 80)
    print("VMware 窗口层级结构调试")
    print("=" * 80)
    print()
    
    # 查找 vmware 进程
    vmware_pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'vmware.exe' in proc.info['name'].lower():
                vmware_pids.append(proc.info['pid'])
        except:
            continue
    
    if not vmware_pids:
        print("未找到 vmware.exe 进程")
        return
    
    print(f"找到 {len(vmware_pids)} 个 vmware.exe 进程: {vmware_pids}\n")
    
    # 查找顶级窗口
    from dxGame.dx_core import user32
    
    def enum_windows_callback(hwnd, lParam):
        if not user32.IsWindowVisible(hwnd):
            return True
        
        window_pid = ctypes.wintypes.LONG()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        
        if window_pid.value not in vmware_pids:
            return True
        
        title = Window.GetWindowTitle(hwnd)
        class_name = Window.GetWindowClass(hwnd)
        
        # 只处理包含端口号的窗口
        if '5600' in title or '5601' in title:
            print(f"\n{'='*80}")
            print(f"顶级窗口: HWND={hwnd}, PID={window_pid.value}")
            print(f"类名: '{class_name}'")
            print(f"标题: '{title}'")
            print(f"\n窗口树结构:")
            print_window_tree(hwnd)
            print(f"{'='*80}\n")
        
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)


if __name__ == '__main__':
    debug_vmware_windows()
