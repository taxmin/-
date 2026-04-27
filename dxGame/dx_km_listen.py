from dxGame.dx_core import ctypes, time

from dxGame import PyThread

LISTEN_KEY_NAMES = {
    0x01: "left mouse button",
    0x02: "right mouse button",
    0x03: "control-break processing",
    0x04: "middle mouse button",
    0x05: "x1 mouse button",
    0x06: "x2 mouse button",
    0x08: "backspace",
    0x09: "tab",
    0x0D: "enter",
    0x10: "shift",
    0x11: "ctrl",
    0x12: "alt",
    0x14: "caps lock",
    0x1B: "esc",
    0x20: "space",
    0x21: "page up",
    0x22: "page down",
    0x23: "end",
    0x24: "home",
    0x25: "left arrow",
    0x26: "up arrow",
    0x27: "right arrow",
    0x28: "down arrow",
    0x2C: "print screen",
    0x2E: "delete",
    0x30: "0",
    0x31: "1",
    0x32: "2",
    0x33: "3",
    0x34: "4",
    0x35: "5",
    0x36: "6",
    0x37: "7",
    0x38: "8",
    0x39: "9",
    0x41: "a",
    0x42: "b",
    0x43: "c",
    0x44: "d",
    0x45: "e",
    0x46: "f",
    0x47: "g",
    0x48: "h",
    0x49: "i",
    0x4A: "j",
    0x4B: "k",
    0x4C: "l",
    0x4D: "m",
    0x4E: "n",
    0x4F: "o",
    0x50: "p",
    0x51: "q",
    0x52: "r",
    0x53: "s",
    0x54: "t",
    0x55: "u",
    0x56: "v",
    0x57: "w",
    0x58: "x",
    0x59: "y",
    0x5A: "z",
    0x5B: "left windows key",
    0x5C: "right windows key",
    0x5D: "application key",
    0x60: "numpad 0",
    0x61: "numpad 1",
    0x62: "numpad 2",
    0x63: "numpad 3",
    0x64: "numpad 4",
    0x65: "numpad 5",
    0x66: "numpad 6",
    0x67: "numpad 7",
    0x68: "numpad 8",
    0x69: "numpad 9",
    0x6A: "numpad multiply",
    0x6B: "numpad add",
    0x6C: "numpad separator",
    0x6D: "numpad subtract",
    0x6E: "numpad decimal",
    0x6F: "numpad divide",
    0x70: "f1",
    0x71: "f2",
    0x72: "f3",
    0x73: "f4",
    0x74: "f5",
    0x75: "f6",
    0x76: "f7",
    0x77: "f8",
    0x78: "f9",
    0x79: "f10",
    0x7A: "f11",
    0x7B: "f12",
    0x7C: "f13",
    0x7D: "f14",
    0x7E: "f15",
    0x7F: "f16",
    0x80: "f17",
    0x81: "f18",
    0x82: "f19",
    0x83: "f20",
    0x84: "f21",
    0x85: "f22",
    0x86: "f23",
    0x87: "f24",
    0x90: "num lock",
    0x91: "scroll lock",
    0xA0: "left shift",
    0xA1: "right shift",
    0xA2: "left control",
    0xA3: "right control",
    0xA4: "left menu",
    0xA5: "right menu",
    0xA6: "browser back",
    0xA7: "browser forward",
    0xA8: "browser refresh",
    0xA9: "browser stop",
    0xAA: "browser search",
    0xAB: "browser favorites",
    0xAC: "browser home",
    0xAD: "volume mute",
    0xAE: "volume down",
    0xAF: "volume up",
    0xB0: "next track",
    0xB1: "previous track",
    0xB2: "stop media",
    0xB3: "play/pause media",
    0xB4: "start mail",
    0xB5: "select media",
    0xB6: "start application 1",
    0xB7: "start application 2",
    0xB8: "calculator",
    0xB9: "my computer",
    0xBA: "my documents",
    0xBB: "my pictures",
    0xBC: "my music",
    0xBD: "my videos",
    0xBE: "media next",
    0xBF: "media previous",
    0xC0: "launch application 1",
    0xC1: "launch application 2",
    0xC2: "launch application 3",
    0xC3: "launch application 4",
    0xC4: "launch application 5",
    0xC5: "launch application 6",
    0xC6: "launch application 7",
    0xC7: "launch application 8",
    0xC8: "launch application 9",
    0xC9: "launch application 10"
}
LISTEN_NAMES_KEY = {v: k for k, v in LISTEN_KEY_NAMES.items()}
class KM_LISTEN:
    def __init__(self, listen_key, call_func, args=()):
        self.listen_key = listen_key
        self.call_func = call_func
        self.args = args
        self.t = None
        self.run = True

    def __del__(self):
        self.stop()

    def start(self):
        func = lambda: self.call_func(*self.args)  # 按键回调函数
        self.t = PyThread(target=self.listen_for_key, args=(self.listen_key, func,))
        self.t.start()

    def stop(self):
        if self.t:
            self.run = False
            s = time.time()
            while self.t.is_alive():
                # 超时1秒强制停止
                if time.time() - s > 1:
                    self.t.stop()
            self.t = None

    # 持续监听键盘事件
    def listen_for_key(self, key_name, call_func):
        # 获取按键名称的映射表（这里只列出常见的按键，你可以扩展这个表）


        LAST_STATE = 0  # 最后一次状态
        while self.run:
            time.sleep(0.001)
            code = LISTEN_NAMES_KEY.get(key_name, None)
            if code is None:
                raise ValueError(f"Unknown key name: {key_name}")
            state = self.get_key_state(code)
            if state and not LAST_STATE:  # 防止长按重复执行,只执行一次
                call_func()
                LAST_STATE = 1
            if not state:
                LAST_STATE = 0

    # 通过ctypes调用Windows API
    @staticmethod
    def get_key_state(key_code):
        # 获取键盘按键状态（0=未按下，1=按下）
        return ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000 != 0


if __name__ == "__main__":
    def test():
        print("按一次执行f2")


    KM_LISTEN("f2", test).start()
    input("")
