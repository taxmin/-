import time
from errno import ELOOP

from dxGame.dx_core import *
from dxGame import Window


def find_dll(dll_name):
    # 获取系统的 PATH 环境变量
    paths = os.environ.get("PATH", "").split(os.pathsep)

    # 在每个路径下查找是否有该 DLL
    for path in paths:
        potential_path = os.path.join(path, dll_name)
        if os.path.exists(potential_path):
            return os.path.abspath(potential_path)

    return None


class KMLJ:
    keys = [
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
    ]
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
    gm = None
    def __init__(self, hwnd=0):
        if not sys.maxsize > 2 ** 32:
            raise ValueError('KMLJ不支持32,请使用64位python!!!')
        self.hwnd = hwnd

        dll_name = "km_lj.dll"
        device_path = os.path.join(dx_core_path, dll_name)
        if not device_path:
            raise ValueError(f"找不到 {dll_name}")
        try:
            if KMLJ.gm is None:
                self.gm = CDLL(device_path)
                self.gm.device_close()
                self.gmok = self.gm.device_open() == 1
                if not self.gmok:
                    raise ValueError('未安装ghub或者lgs驱动!!!')
                else:
                    print('初始化成功!')
            else:
                self.gm = KMLJ.gm
        except FileNotFoundError:
            raise ValueError('缺少文件!!!')
        self.init_mouse()
        self.init_keypress()
        self.now_x, self.now_y = self.GetCursorPos()
        self.key_delay = 0.01
        self.mouse_delay = 0.01

    def __del__(self):
        self.release()

    def release(self):
        self.init_mouse()
        self.init_keypress()

    def init_mouse(self):
        self.LeftUp()
        self.RightUp()

    def init_keypress(self):
        for key in self.keys:
            self.KeyUpChar(key)

    def set_delay(self, key_delay=0.01, mouse_delay=0.01):
        self.key_delay = key_delay
        self.mouse_delay = mouse_delay

    # 按下鼠标按键
    def LeftDown(self):
        self.gm.mouse_down(1)

    # 松开鼠标按键
    def LeftUp(self):
        self.gm.mouse_up(1)

    def RightDown(self):
        self.gm.mouse_down(3)

    def RightUp(self):
        self.gm.mouse_up(3)

    def LeftClick(self):
        self.LeftDown()
        time.sleep(self.mouse_delay)
        self.LeftUp()

    def RightClick(self):
        self.RightDown()
        time.sleep(self.mouse_delay)
        self.RightUp()

    def KeyDownChar(self, code: str):
        if code.isupper():
            code = code.lower()
            self.press_capslock(True)
        else:
            self.press_capslock(False)
        if code in self.shift_keys:
            self.press_controller_down("shift")
            self.gm.key_down(self.shift_keys[code])


        self.gm.key_down(code)


    def KeyUpChar(self, code: str):
        if code.isupper():
            code = code.lower()
        self.gm.key_up(code)
        if code in self.shift_keys:                  # 弹起特殊操控键
            self.press_controller_up("shift")


    def KeyPressChar(self, code: str):
        self.KeyDownChar(code)
        time.sleep(self.key_delay)
        self.KeyUpChar(code)

    def MoveTo(self, x: int, y: int):
        self.now_x, self.now_y = self.GetCursorPos()
        if self.hwnd:
            x, y = Window.ClientToScreen(self.hwnd, x, y)
        self.MoveR(x - self.now_x, y - self.now_y)

    def MoveR(self, x: int, y: int):
        self.gm.moveR(int(x), int(y), False)
        self.now_x, self.now_y = self.now_x + x, self.now_y + y

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
                self.press_controller_key(":capslock")
        else:
            if user32.GetKeyState(self.vk_key_map[":capslock"]) & 1:
                self.press_controller_key(":capslock")

    def press_controller_key(self, key):
        self.press_controller_down(key)
        time.sleep(self.key_delay)
        self.press_controller_up(key)

    def press_controller_down(self, key):
        if not key in self.vk_key_map:
            raise ValueError("无效的按键")
        user32.keybd_event(self.vk_key_map[key], 0, 0, 0)

    def press_controller_up(self, key):
        if not key in self.vk_key_map:
            raise ValueError("无效的按键")
        # 模拟释放 Caps Lock
        user32.keybd_event(self.vk_key_map[key], 0, 2, 0)


if __name__ == '__main__':
    # 轨迹 = [[347, 245], [345, 255], [353, 260], [352, 257], [350, 262], [353, 266], [350, 272], [345, 274], [343, 275], [344, 282], [349, 284], [340, 284], [345, 283], [339, 286], [341, 290], [342, 293], [341, 295], [334, 305], [332, 301], [332, 303], [333, 304], [331, 308], [325, 313], [325, 318], [322, 315], [320, 324], [320, 321], [320, 325], [313, 324], [307, 329], [304, 327], [309, 334], [299, 336], [297, 333], [296, 336], [294, 338], [288, 337], [284, 342], [285, 345], [287, 345], [285, 348], [273, 343], [276, 349], [269, 352], [264, 347], [263, 351], [262, 349], [258, 353], [253, 353], [253, 347], [244, 353], [244, 352], [244, 353], [240, 347], [233, 348], [229, 344], [233, 348], [225, 346], [221, 344], [224, 344], [214, 345], [213, 339], [213, 346], [211, 345], [209, 339], [204, 342], [196, 341], [200, 335], [194, 330], [195, 328], [189, 326], [183, 325], [189, 324], [184, 327], [180, 325], [177, 321], [173, 316], [174, 312], [172, 316], [170, 314], [168, 306], [170, 302], [169, 299], [159, 295], [159, 296], [162, 292], [157, 295], [152, 284], [152, 285], [153, 284], [149, 283], [153, 280], [154, 270], [152, 271], [151, 271], [150, 268], [149, 257], [148, 257], [146, 250], [150, 251], [148, 243], [149, 249], [148, 240], [149, 238], [146, 232], [156, 229], [152, 231], [154, 229], [157, 228], [156, 219], [159, 217], [155, 213], [161, 213], [157, 207], [159, 204], [164, 198], [166, 195], [162, 201], [169, 199], [173, 187], [167, 187], [174, 190], [177, 180], [171, 186], [174, 176], [175, 181], [181, 172], [185, 169], [189, 174], [189, 171], [196, 162], [197, 170], [196, 164], [203, 159], [203, 162], [205, 163], [212, 160], [209, 158], [219, 153], [218, 157], [226, 150], [227, 154], [226, 147], [230, 147], [235, 149], [240, 146], [234, 146], [243, 152], [250, 154], [252, 147], [251, 150], [257, 152], [253, 154], [262, 145], [262, 152], [270, 147], [273, 154], [272, 152], [278, 156], [284, 152], [283, 158], [287, 156], [290, 162], [293, 162], [290, 162], [300, 164], [296, 166], [300, 166], [303, 166], [305, 164], [311, 172], [308, 170], [312, 176], [314, 181], [316, 176], [323, 176], [327, 179], [328, 184], [326, 191], [326, 190], [335, 194], [336, 191], [333, 203], [337, 203], [334, 199], [345, 206], [339, 207], [345, 212], [343, 212], [340, 219], [345, 221], [345, 221], [347, 225], [352, 227], [351, 231], [353, 237], [351, 239], [353, 239], [346, 248], [348, 253]]
    #
    # lj = KMLJ()
    # i = 0
    # time.sleep(5)
    # import random
    # while True:
    #     print("挂机测试中 %s" % i)
    #     i += 1
    #     for i,j in 轨迹:
    #         f = random.randint(-2, 2)
    #         lj.MoveTo(int(i), int(j))
    #         fd = random.randint(10,20)
    #         time.sleep(0.001*fd)
    #
    #     for j in range(20):
    #         time.sleep(1)
    #         print("等待中==%d s" % (20-j))
    #     lj.init_mouse()
    from dxGame import PyThread, Window

    lj = KMLJ()
    lj.KeyPressChar("LorkSidaoe@yahoo.com")
