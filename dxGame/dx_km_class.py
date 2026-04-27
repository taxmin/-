# -*- coding: utf-8 -*-

from dxGame.dx_core import *
from dxGame.dx_Window import Window
from dxGame.dx_mouse_path import get_mouse_path
from dxGame.dx_driver import DxDriver
from dxGame import dx_km

class DXKM:

    VK_CODE = {

        'backspace': 0x08,
        'tab': 0x09,
        'clear': 0x0C,
        'enter': 0x0D,
        'shift': 0x10,
        'ctrl': 0x11,
        'alt': 0x12,
        'pause': 0x13,
        'caps_lock': 0x14,
        'esc': 0x1B,
        'spacebar': 0x20,
        'space': 0x20,
        'page_up': 0x21,
        'page_down': 0x22,
        'end': 0x23,
        'home': 0x24,
        'left': 0x25,
        'up': 0x26,
        'right': 0x27,
        'down': 0x28,
        'select': 0x29,
        'print': 0x2A,
        'execute': 0x2B,
        'print_screen': 0x2C,
        'ins': 0x2D,
        'del': 0x2E,
        'help': 0x2F,
        '0': 0x30,
        '1': 0x31,
        '2': 0x32,
        '3': 0x33,
        '4': 0x34,
        '5': 0x35,
        '6': 0x36,
        '7': 0x37,
        '8': 0x38,
        '9': 0x39,
        'a': 0x41,
        'b': 0x42,
        'c': 0x43,
        'd': 0x44,
        'e': 0x45,
        'f': 0x46,
        'g': 0x47,
        'h': 0x48,
        'i': 0x49,
        'j': 0x4A,
        'k': 0x4B,
        'l': 0x4C,
        'm': 0x4D,
        'n': 0x4E,
        'o': 0x4F,
        'p': 0x50,
        'q': 0x51,
        'r': 0x52,
        's': 0x53,
        't': 0x54,
        'u': 0x55,
        'v': 0x56,
        'w': 0x57,
        'x': 0x58,
        'y': 0x59,
        'z': 0x5A,
        'numpad_0': 0x60,
        'numpad_1': 0x61,
        'numpad_2': 0x62,
        'numpad_3': 0x63,
        'numpad_4': 0x64,
        'numpad_5': 0x65,
        'numpad_6': 0x66,
        'numpad_7': 0x67,
        'numpad_8': 0x68,
        'numpad_9': 0x69,
        'multiply_key': 0x6A,
        'add_key': 0x6B,
        'separator_key': 0x6C,
        'subtract_key': 0x6D,
        'decimal_key': 0x6E,
        'divide_key': 0x6F,
        'f1': 0x70,
        'f2': 0x71,
        'f3': 0x72,
        'f4': 0x73,
        'f5': 0x74,
        'f6': 0x75,
        'f7': 0x76,
        'f8': 0x77,
        'f9': 0x78,
        'f10': 0x79,
        'f11': 0x7A,
        'f12': 0x7B,
        'f13': 0x7C,
        'f14': 0x7D,
        'f15': 0x7E,
        'f16': 0x7F,
        'f17': 0x80,
        'f18': 0x81,
        'f19': 0x82,
        'f20': 0x83,
        'f21': 0x84,
        'f22': 0x85,
        'f23': 0x86,
        'f24': 0x87,
        'num_lock': 0x90,
        'scroll_lock': 0x91,
        'left_shift': 0xA0,
        'right_shift ': 0xA1,
        'left_control': 0xA2,
        'right_control': 0xA3,
        'left_menu': 0xA4,
        'right_menu': 0xA5,
        'browser_back': 0xA6,
        'browser_forward': 0xA7,
        'browser_refresh': 0xA8,
        'browser_stop': 0xA9,
        'browser_search': 0xAA,
        'browser_favorites': 0xAB,
        'browser_start_and_home': 0xAC,
        'volume_mute': 0xAD,
        'volume_Down': 0xAE,
        'volume_up': 0xAF,
        'next_track': 0xB0,
        'previous_track': 0xB1,
        'stop_media': 0xB2,
        'play/pause_media': 0xB3,
        'start_mail': 0xB4,
        'select_media': 0xB5,
        'start_application_1': 0xB6,
        'start_application_2': 0xB7,
        'attn_key': 0xF6,
        'crsel_key': 0xF7,
        'exsel_key': 0xF8,
        'play_key': 0xFA,
        'zoom_key': 0xFB,
        'clear_key': 0xFE,
        '+': 0xBB,
        ',': 0xBC,
        '-': 0xBD,
        '.': 0xBE,
        '/': 0xBF,
        '`': 0xC0,
        ';': 0xBA,
        '[': 0xDB,
        '\\': 0xDC,
        ']': 0xDD,
        "'": 0xDE,
        '`': 0xC0
    }
    shift_keys = {
        "!": "1",
        "@": "2",
        "#": "3",
        "$": "4",
        "%": "5",
        "^": "6",
        "&": "7",
        "*": "8",
        "(": "9",
        ")": "0"
    }
    vk_key_map = {
        'shift': 0x10,
        'ctrl': 0x11,
        'alt': 0x12,
        ':capslock': 0x14,
        'tab': 0x09,
        'enter': 0x0D,
        'esc': 0x1B,
        'space': 0x20,
        'backspace': 0x08,
    }
    dri = None
    def __init__(self, hwnd):
        self.hwnd = hwnd
        if DXKM.dri is None:
            DXKM.dri = DxDriver(os.path.join(dx_core_path,"dxkm.sys"))
            DXKM.dri.uninstall()
            res = DXKM.dri.install()
            if not res:
                DXKM.dri.uninstall()
                res = DXKM.dri.install()
                if not res:
                    raise ValueError("驱动安装失败")
            res = DXKM.dri.start()
            if not res:
                raise ValueError("驱动启动失败")
            dx_km.SetHandle()
        self.driver = dx_km
        self.EnableRealMouse()
        self.set_delay()

    def __del__(self):
        pass # 可以调用stop,也可以不调用

    def set_hwnd(self,hwnd):
        self.hwnd = hwnd

    def stop(self):
        DXKM.dri.stop()
        DXKM.dri.uninstall()
        DXKM.dri = None

    def EnableRealMouse(self, flag=0):
        # 0 关闭模拟
        # 1 开启模拟(斜线模拟,先快在慢)
        self.__mouse_move_flag = flag

    def release(self):
        # self.init_mouse()
        self.init_keypress()

    def init_mouse(self):
        self.LeftUp()  # 弹起会按一下
        self.RightUp()

    def init_keypress(self):
        for key in self.VK_CODE:
            self.KeyUpChar(key)
    def set_delay(self, key_delay=0.01, mouse_delay=0.01):
        self.key_delay = key_delay
        self.mouse_delay = mouse_delay


    # 按下鼠标按键
    def LeftDown(self):
        self.driver.MouseLeftButtonDown()

    # 松开鼠标按键
    def LeftUp(self):
        self.driver.MouseLeftButtonUp()

    def RightDown(self):
        self.driver.MouseRightButtonDown()

    def RightUp(self):
        self.driver.MouseRightButtonUp()

    def LeftClick(self):
        self.LeftDown()
        time.sleep(self.mouse_delay)
        self.LeftUp()

    def RightClick(self):
        self.RightDown()
        time.sleep(self.mouse_delay)
        self.RightUp()

    def MiddleDown(self):
        self.driver.MouseMiddleButtonDown()

    def MiddleUp(self):
        self.driver.MouseMiddleButtonUp()

    def KeyDownChar(self, code: str):
        code = code.lower()
        self.driver.KeyDown(self.VK_CODE[code])

    def KeyUpChar(self, code: str):
        code = code.lower()
        self.driver.KeyUp(self.VK_CODE[code])  # 弹起本质安监


    def KeyPressChar(self, code: str):
        self.KeyDownChar(code)
        time.sleep(self.key_delay)
        self.KeyUpChar(code)

    def GetCurrMousePos(self):
        now_x, now_y = self.GetCursorPos()
        x, y = Window.ScreenToClient(self.hwnd, now_x, now_y)
        return x,y

    def MoveTo(self, x: int, y: int):
        now_x,now_y = self.GetCursorPos()
        if self.hwnd:
            x1, y1 = Window.ClientToScreen(self.hwnd, x, y)
        else:
            x1,y1 = x,y
        self.MoveR(x1-now_x,y1-now_y)
        # now_x,now_y = self.GetCursorPos()

        # if self.hwnd:
        #     x1, y1 = Window.ClientToScreen(self.hwnd, x, y)
        # else:
        #     x1,y1 = x,y
        # self.MoveR(x1-now_x,y1-now_y)

    def MoveR(self, x: int, y: int):
        if self.__mouse_move_flag == 0:
            self.driver.MouseMoveRELATIVE(x, y)
        elif self.__mouse_move_flag == 1:
            paths = get_mouse_path(0,0,x,y)
            for x2,y2 in paths:
                self.driver.MouseMoveRELATIVE(x2, y2)
                time.sleep(self.mouse_delay)

    def KeyPressStr(self, key_str: str, delay: float = 0.01):
        for i in key_str:
            self.KeyPressChar(i)
            time.sleep(delay)

    def slide(self, x1: int, y1: int, x2: int, y2: int, delay=1):
        self.MoveTo(x1, y1)
        time.sleep(0.01)
        self.LeftDown()
        time.sleep(0.01)
        self.MoveR(x2 - x1, y2 - y1)
        self.LeftUp()
        time.sleep(delay)

    @staticmethod
    def GetCursorPos():
        class POINT(ctypes.Structure):
            _fields_ = [
                ("x", ctypes.c_long),
                ("y", ctypes.c_long)
            ]

        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    # 模拟按下 Caps Lock 键
    def press_capslock(self, open=True):
        if open:
            if not user32.GetKeyState(self.vk_key_map[":capslock"]) & 1:
                self.driver.KeyDown(self.vk_key_map[":capslock"])
                self.driver.KeyUp(self.vk_key_map[":capslock"])
                # self.press_controller_key(":capslock")
        else:
            if user32.GetKeyState(self.vk_key_map[":capslock"]) & 1:
                # self.press_controller_key(":capslock")
                self.driver.KeyDown(self.vk_key_map[":capslock"])
                self.driver.KeyUp(self.vk_key_map[":capslock"])




if __name__ == '__main__' :
    KM = DXKM(0)  # 初始化键鼠
    KM.EnableRealMouse(1)
    KM.MoveTo(1229, 38)
    time.sleep(0.1)
    KM.LeftClick()