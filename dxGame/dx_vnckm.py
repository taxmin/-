# -*- coding: utf-8 -*-
"""
VNC键鼠操作类 - 兼容DXKM接口
使用方法：
    self.dx.KM = VNC_KM("127.0.0.1", "5600", "")  # IP, 端口, 密码
"""
# 处理直接运行时的路径问题
import sys
import os
_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)
_parent_dir = os.path.dirname(_current_dir)  # dx多开框架 目录
# 如果父目录不在路径中，尝试添加（用于直接运行此文件）
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import time
import logging
import threading
from vncdotool import api
from vncdotool.client import KEYMAP

from dxGame.dx_core import *

# 🔧 稳定性优化：全局 KM 操作锁，防止多线程并发访问 KM 驱动导致 0xC0000005 崩溃
# 多开环境下，所有 Row 的 KM 操作都必须通过这个锁，确保互斥执行
GLOBAL_KM_LOCK = threading.Lock()


class VNC_KM:
    """
    VNC键鼠操作类，兼容DXKM接口
    使用方法：self.dx.KM = VNC_KM("127.0.0.1", "5600", "")
    """
    
    # VK_CODE映射表（兼容DXKM的按键名称到VNC按键名称）
    # 注意：这些键名必须匹配vncdotool的KEYMAP中实际存在的键名
    VK_CODE = {
        'backspace': 'bsp',  # KEYMAP uses 'bsp' not 'backspace'
        'tab': 'tab',
        'clear': 'clear',
        'enter': 'return',  # KEYMAP has both 'return' and 'enter', using 'return'
        'shift': 'shift',  # KEYMAP has 'shift', 'lshift', 'rshift'
        'ctrl': 'ctrl',  # KEYMAP has 'ctrl', 'lctrl', 'rctrl'
        'alt': 'alt',  # KEYMAP has 'alt', 'lalt', 'ralt'
        'pause': 'pause',
        # 'caps_lock': 'caps_lock',  # Not in KEYMAP, will fallback to original
        'esc': 'esc',  # KEYMAP uses 'esc' not 'escape'
        'spacebar': 'space',  # KEYMAP has 'space', 'spacebar', 'sb'
        'space': 'space',
        'page_up': 'pgup',  # KEYMAP uses 'pgup' not 'page_up'
        'page_down': 'pgdn',  # KEYMAP uses 'pgdn' not 'page_down'
        'end': 'end',
        'home': 'home',
        'left': 'left',
        'up': 'up',
        'right': 'right',
        'down': 'down',
        # Note: The following keys may not exist in KEYMAP, but we keep them
        # for compatibility. The _convert_key method will validate and fallback
        # 'select': 'select',  # Not in KEYMAP
        # 'print': 'print',  # Not in KEYMAP
        # 'execute': 'execute',  # Not in KEYMAP
        # 'print_screen': 'print_screen',  # Not in KEYMAP
        'ins': 'ins',  # KEYMAP uses 'ins' not 'insert'
        'del': 'del',  # KEYMAP uses 'del' (also 'delete' exists)
        # 'help': 'help',  # Not in KEYMAP
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
        '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
        'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e',
        'f': 'f', 'g': 'g', 'h': 'h', 'i': 'i', 'j': 'j',
        'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o',
        'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't',
        'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z',
        # Note: Numpad keys are not in KEYMAP, so we don't map them
        # vncdotool doesn't support numpad keys directly
        # 'numpad_0': 'kp_0', 'numpad_1': 'kp_1', etc. - Not in KEYMAP
        # 'multiply_key': 'kp_multiply', etc. - Not in KEYMAP
        'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
        'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
        'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
    }
    
    # 虚拟键码到按键名称的映射（用于PressKey方法）
    VK_CODE_TO_NAME = {
        0x08: 'backspace',
        0x09: 'tab',
        0x0C: 'clear',
        0x0D: 'enter',
        0x10: 'shift',
        0x11: 'ctrl',
        0x12: 'alt',
        0x13: 'pause',
        0x14: 'caps_lock',
        0x1B: 'esc',  # 27 = ESC
        0x20: 'space',
        0x21: 'page_up',
        0x22: 'page_down',
        0x23: 'end',
        0x24: 'home',
        0x25: 'left',
        0x26: 'up',
        0x27: 'right',
        0x28: 'down',
        0x29: 'select',
        0x2A: 'print',
        0x2B: 'execute',
        0x2C: 'print_screen',
        0x2D: 'ins',
        0x2E: 'del',
        0x2F: 'help',
        0x30: '0', 0x31: '1', 0x32: '2', 0x33: '3', 0x34: '4',
        0x35: '5', 0x36: '6', 0x37: '7', 0x38: '8', 0x39: '9',
        0x41: 'a', 0x42: 'b', 0x43: 'c', 0x44: 'd', 0x45: 'e',
        0x46: 'f', 0x47: 'g', 0x48: 'h', 0x49: 'i', 0x4A: 'j',
        0x4B: 'k', 0x4C: 'l', 0x4D: 'm', 0x4E: 'n', 0x4F: 'o',
        0x50: 'p', 0x51: 'q', 0x52: 'r', 0x53: 's', 0x54: 't',
        0x55: 'u', 0x56: 'v', 0x57: 'w', 0x58: 'x', 0x59: 'y', 0x5A: 'z',
        0x60: 'numpad_0', 0x61: 'numpad_1', 0x62: 'numpad_2',
        0x63: 'numpad_3', 0x64: 'numpad_4', 0x65: 'numpad_5',
        0x66: 'numpad_6', 0x67: 'numpad_7', 0x68: 'numpad_8', 0x69: 'numpad_9',
        0x6A: 'multiply_key', 0x6B: 'add_key',
        0x6C: 'separator_key', 0x6D: 'subtract_key',
        0x6E: 'decimal_key', 0x6F: 'divide_key',
        0x70: 'f1', 0x71: 'f2', 0x72: 'f3', 0x73: 'f4',
        0x74: 'f5', 0x75: 'f6', 0x76: 'f7', 0x77: 'f8',
        0x78: 'f9', 0x79: 'f10', 0x7A: 'f11', 0x7B: 'f12',
    }
    
    def __init__(self, ip, port, password="", hwnd=None):
        """
        初始化VNC键鼠连接
        
        Args:
            ip: VNC服务器IP地址
            port: VNC服务器端口（字符串或数字）
            password: VNC密码，默认空字符串
            hwnd: 窗口句柄（VNC不需要，但为了兼容DXKM接口保留）
        """
        # 🔧 稳定性优化：增加超时配置
        self.operation_timeout = 5.0  # 单个操作超时 5 秒
        
        # 处理端口号
        if isinstance(port, int):
            port = str(port)
        
        # 处理密码
        if password == "":
            password = None
        
        self.ip = ip
        self.port = port
        self.password = password
        self.hwnd = hwnd  # VNC不使用hwnd，但保留用于兼容
        self.hwnd_desktop = user32.GetDesktopWindow()
        
        # 连接VNC服务器
        vnc_address = f"{ip}::{port}"
        print(f"正在连接到VNC服务器（键鼠）: {ip}:{port}...")
        try:
            self.client = api.connect(vnc_address, password, timeout=60)
            print("VNC键鼠连接成功！")
        except Exception as e:
            print(f"❌ VNC键鼠连接失败: {e}")
            raise
        
        # 等待连接稳定
        time.sleep(1)
        
        # 延迟设置（兼容DXKM）
        self.key_delay = 0.01
        self.mouse_delay = 0.01
        
        # 鼠标模拟标志（兼容DXKM）
        self.__mouse_move_flag = 0
        
        # 当前鼠标位置（VNC使用绝对坐标）
        self._current_x = 0
        self._current_y = 0
        
        # 连接状态
        self._connected = True
        
        # VNC的KEYMAP
        self.key_map = KEYMAP
    
    def __del__(self):
        """清理VNC资源"""
        try:
            self.stop()
        except:
            pass
    
    def _execute_with_timeout(self, func, args=(), kwargs={}, timeout=None):
        """
        🔧 稳定性优化：带超时保护的执行方法
        
        Args:
            func: 要执行的函数
            args: 位置参数
            kwargs: 关键字参数
            timeout: 超时时间（秒），默认使用 self.operation_timeout
        
        Returns:
            函数返回值
        
        Raises:
            TimeoutError: 操作超时
            Exception: 其他异常
        """
        if timeout is None:
            timeout = self.operation_timeout
        
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            # 超时，线程仍在运行
            error_msg = f"KM 操作超时 ({timeout}秒)，窗口可能卡死"
            logging.error(f"⚠️ [KM] {error_msg}")
            raise TimeoutError(error_msg)
        
        if exception[0] is not None:
            # 函数执行出错
            raise exception[0]
        
        return result[0]
    
    def stop(self):
        """
        断开VNC连接
        """
        if self._connected and hasattr(self, 'client') and self.client is not None:
            try:
                # 在单独线程中执行disconnect，避免阻塞
                def disconnect_thread():
                    try:
                        self.client.disconnect()
                    except Exception as e:
                        logging.debug(f"VNC键鼠断开连接时出错: {e}")
                
                disconnect_t = threading.Thread(target=disconnect_thread, daemon=True)
                disconnect_t.start()
                disconnect_t.join(timeout=1.0)  # 最多等待1秒
                if disconnect_t.is_alive():
                    logging.warning("VNC键鼠断开连接超时，但不会阻塞主线程")
                
                self._connected = False
            except Exception as e:
                logging.debug(f"断开VNC键鼠连接时出错: {e}")
    
    def set_hwnd(self, hwnd):
        """
        设置窗口句柄（VNC不需要，但为了兼容DXKM接口保留）
        
        Args:
            hwnd: 窗口句柄，VNC中会被忽略
        """
        self.hwnd = hwnd
    
    def set_delay(self, key_delay=0.01, mouse_delay=0.01):
        """
        设置按键和鼠标操作的延迟
        
        Args:
            key_delay: 按键延迟（秒）
            mouse_delay: 鼠标延迟（秒）
        """
        self.key_delay = key_delay
        self.mouse_delay = mouse_delay
    
    def EnableRealMouse(self, flag=0):
        """
        启用真实鼠标模拟（兼容DXKM接口）
        
        Args:
            flag: 0=关闭模拟, 1=开启模拟
        """
        self.__mouse_move_flag = flag
    
    def init_mouse(self):
        """初始化鼠标（释放所有按键）"""
        try:
            self.client.mouseUp(1)  # 左键
            self.client.mouseUp(2)  # 中键
            self.client.mouseUp(3)  # 右键
        except:
            pass
    
    def init_keypress(self):
        """初始化键盘（释放所有按键）"""
        # VNC不需要显式释放所有按键，但保留接口兼容性
        pass
    
    def release(self):
        """释放资源（兼容DXKM接口）"""
        self.init_keypress()
    
    # ========== 鼠标操作 ==========
    
    def LeftDown(self):
        """按下鼠标左键"""
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        try:
            self.client.mouseDown(1)
        except Exception as e:
            logging.error(f"按下鼠标左键失败: {e}")
            raise
    
    def LeftUp(self):
        """释放鼠标左键"""
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        try:
            self.client.mouseUp(1)
        except Exception as e:
            logging.error(f"释放鼠标左键失败: {e}")
            raise
    
    def LeftClick(self):
        """
        点击鼠标左键
        🔧 稳定性优化：增加超时保护
        """
        try:
            self._execute_with_timeout(
                self.LeftDown,
                timeout=self.operation_timeout
            )
            time.sleep(self.mouse_delay)
            self._execute_with_timeout(
                self.LeftUp,
                timeout=self.operation_timeout
            )
        except TimeoutError:
            logging.error(f"⚠️ [KM] LeftClick 超时，窗口可能卡死")
            raise
    
    def LeftDoubleClick(self):
        """双击鼠标左键"""
        self.LeftClick()
        time.sleep(self.mouse_delay)
        self.LeftClick()
    
    def RightDown(self):
        """按下鼠标右键"""
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        try:
            self.client.mouseDown(3)
        except Exception as e:
            logging.error(f"按下鼠标右键失败: {e}")
            raise
    
    def RightUp(self):
        """释放鼠标右键"""
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        try:
            self.client.mouseUp(3)
        except Exception as e:
            logging.error(f"释放鼠标右键失败: {e}")
            raise
    
    def RightClick(self):
        """点击鼠标右键"""
        self.RightDown()
        time.sleep(self.mouse_delay)
        self.RightUp()
    
    def RightDoubleClick(self):
        """双击鼠标右键"""
        self.RightClick()
        time.sleep(self.mouse_delay)
        self.RightClick()
    
    def MiddleDown(self):
        """按下鼠标中键"""
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        try:
            self.client.mouseDown(2)
        except Exception as e:
            logging.error(f"按下鼠标中键失败: {e}")
            raise
    
    def MiddleUp(self):
        """释放鼠标中键"""
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        try:
            self.client.mouseUp(2)
        except Exception as e:
            logging.error(f"释放鼠标中键失败: {e}")
            raise
    
    def MiddleClick(self):
        """点击鼠标中键"""
        self.MiddleDown()
        time.sleep(self.mouse_delay)
        self.MiddleUp()
    
    def MoveTo(self, x: int, y: int):
        """
        移动鼠标到指定位置（绝对坐标）
        🔧 稳定性优化：增加超时保护 + 全局锁，防止多开并发冲突
        
        Args:
            x: X坐标
            y: Y坐标
        """
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        
        # 验证坐标有效性（VNC坐标必须为非负整数）
        if x < 0 or y < 0:
            error_msg = f"无效的鼠标坐标: ({x}, {y})。VNC坐标必须为非负整数。"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # 🔧 使用全局锁保护，防止多开环境并发冲突
            with GLOBAL_KM_LOCK:
                # 🔧 使用超时保护执行移动
                self._execute_with_timeout(
                    self.client.mouseMove,
                    args=(x, y),
                    timeout=self.operation_timeout
                )
                self._current_x = x
                self._current_y = y
        except TimeoutError:
            logging.error(f"⚠️ [KM] MoveTo 超时，窗口可能卡死: ({x}, {y})")
            raise
        except Exception as e:
            logging.error(f"移动鼠标失败: {e}")
            raise
    
    def MoveR(self, x: int, y: int):
        """
        相对移动鼠标
        
        Args:
            x: X方向偏移量
            y: Y方向偏移量
        """
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        
        try:
            # 计算新的绝对坐标
            new_x = self._current_x + x
            new_y = self._current_y + y
            
            # 如果启用了真实鼠标模拟，使用路径移动
            if self.__mouse_move_flag == 1:
                # 简单的路径模拟（可以后续优化）
                steps = max(abs(x), abs(y)) // 10 + 1
                for i in range(steps):
                    step_x = self._current_x + int(x * (i + 1) / steps)
                    step_y = self._current_y + int(y * (i + 1) / steps)
                    self.client.mouseMove(step_x, step_y)
                    time.sleep(self.mouse_delay)
            else:
                self.client.mouseMove(new_x, new_y)
            
            self._current_x = new_x
            self._current_y = new_y
        except Exception as e:
            logging.error(f"相对移动鼠标失败: {e}")
            raise
    
    def slide(self, x1: int, y1: int, x2: int, y2: int, delay=1):
        """
        滑动操作（拖拽）
        
        Args:
            x1: 起始X坐标
            y1: 起始Y坐标
            x2: 结束X坐标
            y2: 结束Y坐标
            delay: 延迟（秒）
        """
        self.MoveTo(x1, y1)
        time.sleep(0.01)
        self.LeftDown()
        time.sleep(0.01)
        self.MoveTo(x2, y2)
        time.sleep(delay)
        self.LeftUp()
    
    def GetCurrMousePos(self):
        """
        获取当前鼠标位置（兼容DXKM接口）
        
        Returns:
            tuple: (x, y) 坐标
        """
        # VNC无法直接获取鼠标位置，返回最后记录的位置
        return self._current_x, self._current_y
    
    @staticmethod
    def GetCursorPos():
        """
        获取当前鼠标位置（静态方法，兼容DXKM接口）
        
        Returns:
            tuple: (x, y) 坐标
        """
        # VNC无法获取本地鼠标位置，返回(0,0)
        return 0, 0
    
    # ========== 键盘操作 ==========
    
    def _convert_key(self, key_str: str):
        """
        将DXKM的按键名称转换为VNC的按键名称（必须匹配vncdotool的KEYMAP）
        
        Args:
            key_str: DXKM的按键名称（如 'esc', 'enter'）
        
        Returns:
            VNC的按键名称（必须存在于KEYMAP中，或单个字符供vncdotool用ord()处理）
        """
        key_str = key_str.lower()
        is_single_char = len(key_str) == 1
        
        # 首先检查VK_CODE映射表
        if key_str in self.VK_CODE:
            converted_key = self.VK_CODE[key_str]
            # 验证转换后的键是否在KEYMAP中
            if converted_key in self.key_map:
                return converted_key
            else:
                # 如果转换后的键不在KEYMAP中，尝试使用原始键
                # 单个字符不警告（vncdotool会用ord()处理），多字符才警告
                if not is_single_char:
                    logging.warning(f"转换后的键 '{converted_key}' 不在KEYMAP中，尝试使用原始键 '{key_str}'")
                if key_str in self.key_map:
                    return key_str
        
        # 如果不在映射表中，直接返回（可能是单个字符或已经是VNC格式）
        # 如果原始键在KEYMAP中，直接使用
        if key_str in self.key_map:
            return key_str
        
        # 如果都不在KEYMAP中，仍然返回原始键
        # 单个字符会被vncdotool用ord()处理，这是正常行为
        # 多字符键如果不在KEYMAP中，vncdotool会报错（这是预期的）
        return key_str
    
    def KeyDownChar(self, key_str: str):
        """
        按下按键（不释放）
        🔧 稳定性优化：增加超时保护 + 全局锁
        
        Args:
            key_str: 按键名称（如 'esc', 'a', 'enter'）
        """
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        
        try:
            vnc_key = self._convert_key(key_str)
            # 🔧 使用全局锁 + 超时保护执行按键
            with GLOBAL_KM_LOCK:
                self._execute_with_timeout(
                    self.client.keyDown,
                    args=(vnc_key,),
                    timeout=self.operation_timeout
                )
        except TimeoutError:
            logging.error(f"⚠️ [KM] KeyDownChar 超时: {key_str}")
            raise
        except Exception as e:
            logging.error(f"按下按键失败 ({key_str}): {e}")
            raise
    
    def KeyUpChar(self, key_str: str):
        """
        释放按键
        🔧 稳定性优化：增加超时保护 + 全局锁
        
        Args:
            key_str: 按键名称（如 'esc', 'a', 'enter'）
        """
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        
        try:
            vnc_key = self._convert_key(key_str)
            # 🔧 使用全局锁 + 超时保护执行按键
            with GLOBAL_KM_LOCK:
                self._execute_with_timeout(
                    self.client.keyUp,
                    args=(vnc_key,),
                    timeout=self.operation_timeout
                )
        except TimeoutError:
            logging.error(f"⚠️ [KM] KeyUpChar 超时: {key_str}")
            raise
        except Exception as e:
            logging.error(f"释放按键失败 ({key_str}): {e}")
            raise
    
    def KeyPressChar(self, key_str: str):
        """
        按键一次（按下并释放）
        
        Args:
            key_str: 按键名称（如 'esc', 'a', 'enter'）
        """
        self.KeyDownChar(key_str)
        time.sleep(self.key_delay)
        self.KeyUpChar(key_str)
    
    def KeyPressStr(self, key_str: str, delay: float = 0.01):
        """
        按键字符串（逐个按键）
        
        Args:
            key_str: 字符串，如 "123abc"
            delay: 每个按键之间的延迟（秒）
        """
        for char in key_str:
            self.KeyPressChar(char)
            time.sleep(delay)
    
    def input(self, text: str, delay: float = 0.01):
        """
        输入文本（兼容DXKM接口）
        
        Args:
            text: 要输入的文本
            delay: 每个字符之间的延迟（秒）
        """
        self.KeyPressStr(text, delay)
    
    def PressKey(self, key):
        """
        按下并释放指定的按键（兼容DXKM接口）
        
        Args:
            key: 按键，可以是虚拟键码（整数，如27）或按键名称（字符串，如'esc'）
        """
        # 如果是整数，转换为按键名称
        if isinstance(key, int):
            if key not in self.VK_CODE_TO_NAME:
                raise ValueError(f"不支持的虚拟键码: {key}")
            key = self.VK_CODE_TO_NAME[key]
        
        # 使用KeyPressChar方法按键
        self.KeyPressChar(key)
    
    def hot_key(self, key_list):
        """
        组合键
        
        Args:
            key_list: 按键列表，例如 ['ctrl', 'c'] 表示 Ctrl+C
        """
        if not self._connected:
            raise ConnectionError("VNC连接已断开")
        
        try:
            # 按下所有按键
            for key_str in key_list:
                self.KeyDownChar(key_str)
                time.sleep(0.05)
            
            # 释放所有按键（逆序）
            for key_str in key_list[::-1]:
                self.KeyUpChar(key_str)
                time.sleep(0.05)
        except Exception as e:
            logging.error(f"组合键失败: {e}")
            raise


if __name__ == '__main__':
    # 测试代码
    try:
        print("=" * 60)
        print("VNC键鼠测试（兼容DXKM接口）")
        print("=" * 60)
        
        # 创建VNC键鼠对象
        vnc_km = VNC_KM("127.0.0.1", "5600", "")
        
        print("\n测试鼠标操作...")
        # 测试移动鼠标
        print("移动鼠标到 (100, 100)...")
        vnc_km.MoveTo(100, 100)
        time.sleep(0.5)
        
        # 测试左键点击
        print("左键点击...")
        vnc_km.LeftClick()
        time.sleep(0.5)
        
        # 测试双击
        print("双击...")
        vnc_km.LeftDoubleClick()
        time.sleep(0.5)
        
        print("\n测试键盘操作...")
        # 测试按键
        print("按下 ESC 键...")
        vnc_km.KeyPressChar('esc')
        time.sleep(0.5)
        
        # 测试输入字符串
        print("输入字符串 'hello'...")
        vnc_km.KeyPressStr('hello', delay=0.1)
        time.sleep(0.5)
        
        # 测试组合键
        print("按下 Ctrl+C...")
        vnc_km.hot_key(['ctrl', 'c'])
        time.sleep(0.5)
        
        print("\n✅ 测试完成")
        vnc_km.stop()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
