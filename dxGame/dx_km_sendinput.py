from dxGame import Window
from dxGame.dx_core import *
class Pydirectinput:
    SendInput = user32.SendInput
    MapVirtualKey = user32.MapVirtualKeyW

    # Constants for failsafe check and pause

    FAILSAFE = True
    FAILSAFE_POINTS = [(0, 0)]
    PAUSE = 0.1  # Tenth-second pause by default.

    # Constants for the mouse button names
    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    WHEEL = "wheel"

    # Mouse Scan Code Mappings
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_LEFTCLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_RIGHTCLICK = MOUSEEVENTF_RIGHTDOWN + MOUSEEVENTF_RIGHTUP
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_MIDDLECLICK = MOUSEEVENTF_MIDDLEDOWN + MOUSEEVENTF_MIDDLEUP
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_WHEELUP = -0x0078
    MOUSEEVENTF_WHEELDOWN = 0x0078

    # KeyBdInput Flags
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    KEYEVENTF_UNICODE = 0x0004

    # MapVirtualKey Map Types
    MAPVK_VK_TO_CHAR = 2
    MAPVK_VK_TO_VSC = 0
    MAPVK_VSC_TO_VK = 1
    MAPVK_VSC_TO_VK_EX = 3

    # Keyboard Scan Code Mappings
    KEYBOARD_MAPPING = {
        'escape': 0x01,
        'esc': 0x01,
        'f1': 0x3B,
        'f2': 0x3C,
        'f3': 0x3D,
        'f4': 0x3E,
        'f5': 0x3F,
        'f6': 0x40,
        'f7': 0x41,
        'f8': 0x42,
        'f9': 0x43,
        'f10': 0x44,
        'f11': 0x57,
        'f12': 0x58,
        'printscreen': 0xB7,
        'prntscrn': 0xB7,
        'prtsc': 0xB7,
        'prtscr': 0xB7,
        'scrolllock': 0x46,
        'pause': 0xC5,
        '`': 0x29,
        '1': 0x02,
        '2': 0x03,
        '3': 0x04,
        '4': 0x05,
        '5': 0x06,
        '6': 0x07,
        '7': 0x08,
        '8': 0x09,
        '9': 0x0A,
        '0': 0x0B,
        '-': 0x0C,
        '=': 0x0D,
        'backspace': 0x0E,
        'insert': 0xD2 + 1024,
        'home': 0xC7 + 1024,
        'pageup': 0xC9 + 1024,
        'pagedown': 0xD1 + 1024,
        # numpad
        'numlock': 0x45,
        'divide': 0xB5 + 1024,
        'multiply': 0x37,
        'subtract': 0x4A,
        'add': 0x4E,
        'decimal': 0x53,
        'numpadenter': 0x9C + 1024,
        'numpad1': 0x4F,
        'numpad2': 0x50,
        'numpad3': 0x51,
        'numpad4': 0x4B,
        'numpad5': 0x4C,
        'numpad6': 0x4D,
        'numpad7': 0x47,
        'numpad8': 0x48,
        'numpad9': 0x49,
        'numpad0': 0x52,
        # end numpad
        'tab': 0x0F,
        'q': 0x10,
        'w': 0x11,
        'e': 0x12,
        'r': 0x13,
        't': 0x14,
        'y': 0x15,
        'u': 0x16,
        'i': 0x17,
        'o': 0x18,
        'p': 0x19,
        '[': 0x1A,
        ']': 0x1B,
        '\\': 0x2B,
        'del': 0xD3 + 1024,
        'delete': 0xD3 + 1024,
        'end': 0xCF + 1024,
        'capslock': 0x3A,
        'a': 0x1E,
        's': 0x1F,
        'd': 0x20,
        'f': 0x21,
        'g': 0x22,
        'h': 0x23,
        'j': 0x24,
        'k': 0x25,
        'l': 0x26,
        ';': 0x27,
        "'": 0x28,
        'enter': 0x1C,
        'return': 0x1C,
        'shift': 0x2A,
        'shiftleft': 0x2A,
        'z': 0x2C,
        'x': 0x2D,
        'c': 0x2E,
        'v': 0x2F,
        'b': 0x30,
        'n': 0x31,
        'm': 0x32,
        ',': 0x33,
        '.': 0x34,
        '/': 0x35,
        'shiftright': 0x36,
        'ctrl': 0x1D,
        'ctrlleft': 0x1D,
        'win': 0xDB + 1024,
        'winleft': 0xDB + 1024,
        'alt': 0x38,
        'altleft': 0x38,
        ' ': 0x39,
        'space': 0x39,
        'altright': 0xB8 + 1024,
        'winright': 0xDC + 1024,
        'apps': 0xDD + 1024,
        'ctrlright': 0x9D + 1024,
        # arrow key scancodes can be different depending on the hardware,
        # so I think the best solution is to look it up based on the virtual key
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-mapvirtualkeya?redirectedfrom=MSDN
        'up': MapVirtualKey(0x26, MAPVK_VK_TO_VSC),
        'left': MapVirtualKey(0x25, MAPVK_VK_TO_VSC),
        'down': MapVirtualKey(0x28, MAPVK_VK_TO_VSC),
        'right': MapVirtualKey(0x27, MAPVK_VK_TO_VSC),
    }

    # C struct redefinitions





    # Fail Safe and Pause implementation

    class FailSafeException(Exception):
        pass

    @staticmethod
    def failSafeCheck():
        if Pydirectinput.FAILSAFE and tuple(Pydirectinput.position()) in Pydirectinput.FAILSAFE_POINTS:
            raise Pydirectinput.FailSafeException(
                "PyDirectInput fail-safe triggered from mouse moving to a corner of the screen. To disable this " \
                "fail-safe, set Pydirectinput.FAILSAFE to False. DISABLING FAIL-SAFE IS NOT RECOMMENDED."
            )
    @staticmethod
    def _handlePause(_pause):
        if _pause:
            assert isinstance(Pydirectinput.PAUSE, int) or isinstance(Pydirectinput.PAUSE, float)
            time.sleep(Pydirectinput.PAUSE)


    # Helper Functions
    @staticmethod
    def _to_windows_coordinates(x=0, y=0):
        display_width, display_height = Pydirectinput.size()

        # the +1 here prevents exactly mouse movements from sometimes ending up off by 1 pixel
        windows_x = (x * 65536) // display_width + 1
        windows_y = (y * 65536) // display_height + 1

        return windows_x, windows_y

    # position() works exactly the same as PyAutoGUI. I've duplicated it here so that moveRel() can use it to calculate
    # relative mouse positions.
    @staticmethod
    def position(x=None, y=None):
        cursor = StructurePy.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor), )
        return (x if x else cursor.x, y if y else cursor.y)

    # size() works exactly the same as PyAutoGUI. I've duplicated it here so that _to_windows_coordinates() can use it
    # to calculate the window size.
    @staticmethod
    def size():
        return (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))

    # Main Mouse Functions

    # Ignored parameters: duration, tween, logScreenshot
    @staticmethod
    def mouseDown(x=None, y=None, button=PRIMARY, duration=None, tween=None, logScreenshot=None, _pause=True):
        if not x is None or not y is None:
            Pydirectinput.moveTo(x, y)
        mouseData = 0
        ev = None
        if button == Pydirectinput.PRIMARY or button == Pydirectinput.LEFT:
            ev = Pydirectinput.MOUSEEVENTF_LEFTDOWN
        elif button == Pydirectinput.MIDDLE:
            ev = Pydirectinput.MOUSEEVENTF_MIDDLEDOWN
        elif button == Pydirectinput.SECONDARY or button == Pydirectinput.RIGHT:
            ev = Pydirectinput.MOUSEEVENTF_RIGHTDOWN
        elif button == Pydirectinput.WHEEL:
            ev = Pydirectinput.MOUSEEVENTF_WHEEL
            mouseData = Pydirectinput.MOUSEEVENTF_WHEELDOWN
        if not ev:
            raise ValueError('button arg to _click() must be one of "left", "middle", or "right", not %s' % button)

        extra = ctypes.c_ulong(0)
        ii_ = StructurePy.Input_I()
        ii_.mi = StructurePy.MouseInput(0, 0, mouseData, ev, 0, ctypes.pointer(extra))
        x = StructurePy.Input(ctypes.c_ulong(0), ii_)
        Pydirectinput.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    # Ignored parameters: duration, tween, logScreenshot
    @staticmethod
    def mouseUp(x=None, y=None, button=PRIMARY, duration=None, tween=None, logScreenshot=None, _pause=True):
        if not x is None or not y is None:
            Pydirectinput.moveTo(x, y)
        mouseData = 0
        ev = None
        if button == Pydirectinput.PRIMARY or button == Pydirectinput.LEFT:
            ev = Pydirectinput.MOUSEEVENTF_LEFTUP
        elif button == Pydirectinput.MIDDLE:
            ev = Pydirectinput.MOUSEEVENTF_MIDDLEUP
        elif button == Pydirectinput.SECONDARY or button == Pydirectinput.RIGHT:
            ev = Pydirectinput.MOUSEEVENTF_RIGHTUP
        elif button == Pydirectinput.WHEEL:
            ev = Pydirectinput.MOUSEEVENTF_WHEEL
            mouseData = Pydirectinput.MOUSEEVENTF_WHEELDOWN
        if not ev:
            raise ValueError('button arg to _click() must be one of "left", "middle", or "right", not %s' % button)

        extra = ctypes.c_ulong(0)
        ii_ = StructurePy.Input_I()
        ii_.mi = StructurePy.MouseInput(0, 0, mouseData, ev, 0, ctypes.pointer(extra))
        x = StructurePy.Input(ctypes.c_ulong(0), ii_)
        Pydirectinput.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    # Ignored parameters: duration, tween, logScreenshot

    @staticmethod
    def click(x=None, y=None, clicks=1, interval=0.0, button=PRIMARY, duration=None, tween=None, logScreenshot=None,
              _pause=True):
        if not x is None or not y is None:
            Pydirectinput.moveTo(x, y)

        ev = None
        if button == Pydirectinput.PRIMARY or button == Pydirectinput.LEFT:
            ev = Pydirectinput.MOUSEEVENTF_LEFTCLICK
        elif button == Pydirectinput.MIDDLE:
            ev = Pydirectinput.MOUSEEVENTF_MIDDLECLICK
        elif button == Pydirectinput.SECONDARY or button == Pydirectinput.RIGHT:
            ev = Pydirectinput.MOUSEEVENTF_RIGHTCLICK

        if not ev:
            raise ValueError('button arg to _click() must be one of "left", "middle", or "right", not %s' % button)

        for i in range(clicks):
            Pydirectinput.failSafeCheck()

            extra = ctypes.c_ulong(0)
            ii_ = StructurePy.Input_I()
            ii_.mi = StructurePy.MouseInput(0, 0, 0, ev, 0, ctypes.pointer(extra))
            x = StructurePy.Input(ctypes.c_ulong(0), ii_)
            Pydirectinput.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

            time.sleep(interval)
    @staticmethod
    def leftClick(x=None, y=None, interval=0.0, duration=0.0, tween=None, logScreenshot=None, _pause=True):
        Pydirectinput.click(x, y, 1, interval, Pydirectinput.LEFT, duration, tween, logScreenshot, _pause)

    @staticmethod
    def rightClick(x=None, y=None, interval=0.0, duration=0.0, tween=None, logScreenshot=None, _pause=True):
        Pydirectinput.click(x, y, 1, interval, Pydirectinput.RIGHT, duration, tween, logScreenshot, _pause)

    @staticmethod
    def middleClick(x=None, y=None, interval=0.0, duration=0.0, tween=None, logScreenshot=None, _pause=True):
        Pydirectinput.click(x, y, 1, interval, Pydirectinput.MIDDLE, duration, tween, logScreenshot, _pause)

    @staticmethod
    def doubleClick(x=None, y=None, interval=0.0, button=LEFT, duration=0.0, tween=None, logScreenshot=None, _pause=True):
        Pydirectinput.click(x, y, 2, interval, button, duration, tween, logScreenshot, _pause)

    @staticmethod
    def tripleClick(x=None, y=None, interval=0.0, button=LEFT, duration=0.0, tween=None, logScreenshot=None, _pause=True):
        Pydirectinput.click(x, y, 3, interval, button, duration, tween, logScreenshot, _pause)

    # Missing feature: scroll functions

    # Ignored parameters: duration, tween, logScreenshot
    # PyAutoGUI uses ctypes.windll.user32.SetCursorPos(x, y) for this, which might still work fine in DirectInput
    # environments.
    # Use the relative flag to do a raw win32 api relative movement call (no MOUSEEVENTF_ABSOLUTE flag), which may be more
    # appropriate for some applications. Note that this may produce inexact results depending on mouse movement speed.

    @staticmethod
    def moveTo(x=None, y=None, duration=None, tween=None, logScreenshot=False, _pause=True, relative=False):
        if not relative:
            x, y = Pydirectinput.position(x, y)  # if only x or y is provided, will keep the current position for the other axis
            x, y = Pydirectinput._to_windows_coordinates(x, y)
            extra = ctypes.c_ulong(0)
            ii_ = StructurePy.Input_I()
            ii_.mi = StructurePy.MouseInput(x, y, 0, (Pydirectinput.MOUSEEVENTF_MOVE | Pydirectinput.MOUSEEVENTF_ABSOLUTE), 0, ctypes.pointer(extra))
            command = StructurePy.Input(ctypes.c_ulong(0), ii_)
            Pydirectinput.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
        else:
            currentX, currentY = Pydirectinput.position()
            Pydirectinput.moveRel(x - currentX, y - currentY, relative=True)

    # Ignored parameters: duration, tween, logScreenshot
    # move() and moveRel() are equivalent.
    # Use the relative flag to do a raw win32 api relative movement call (no MOUSEEVENTF_ABSOLUTE flag), which may be more
    # appropriate for some applications.

    @staticmethod
    def moveRel(xOffset=None, yOffset=None, duration=None, tween=None, logScreenshot=False, _pause=True, relative=False):
        if not relative:
            x, y = Pydirectinput.position()
            if xOffset is None:
                xOffset = 0
            if yOffset is None:
                yOffset = 0
            Pydirectinput.moveTo(x + xOffset, y + yOffset)
        else:
            # When using MOUSEEVENTF_MOVE for relative movement the results may be inconsistent.
            # "Relative mouse motion is subject to the effects of the mouse speed and the two-mouse threshold values. A user
            # sets these three values with the Pointer Speed slider of the Control Panel's Mouse Properties sheet. You can
            # obtain and set these values using the SystemParametersInfo function."
            # https://docs.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-mouseinput
            # https://stackoverflow.com/questions/50601200/pyhon-directinput-mouse-relative-moving-act-not-as-expected
            extra = ctypes.c_ulong(0)
            ii_ = StructurePy.Input_I()
            ii_.mi = StructurePy.MouseInput(xOffset, yOffset, 0, Pydirectinput.MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
            command = StructurePy.Input(ctypes.c_ulong(0), ii_)
            Pydirectinput.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

    move = moveRel

    # Missing feature: drag functions

    # Keyboard Functions

    # Ignored parameters: logScreenshot
    # Missing feature: auto shift for special characters (ie. '!', '@', '#'...)
    @staticmethod
    def keyDown(key, logScreenshot=None, _pause=True):
        if not key in Pydirectinput.KEYBOARD_MAPPING or Pydirectinput.KEYBOARD_MAPPING[key] is None:
            return

        keybdFlags = Pydirectinput.KEYEVENTF_SCANCODE

        # Init event tracking
        insertedEvents = 0
        expectedEvents = 1

        # arrow keys need the extended key flag
        if key in ['up', 'left', 'down', 'right']:
            keybdFlags |= Pydirectinput.KEYEVENTF_EXTENDEDKEY
            # if numlock is on and an arrow key is being pressed, we need to send an additional scancode
            # https://stackoverflow.com/questions/14026496/sendinput-sends-num8-when-i-want-to-send-vk-up-how-come
            # https://handmade.network/wiki/2823-keyboard_inputs_-_scancodes,_raw_input,_text_input,_key_names
            if ctypes.windll.user32.GetKeyState(0x90):
                # We need to press two keys, so we expect to have inserted 2 events when done
                expectedEvents = 2
                hexKeyCode = 0xE0
                extra = ctypes.c_ulong(0)
                ii_ = StructurePy.Input_I()
                ii_.ki = StructurePy.KeyBdInput(0, hexKeyCode, Pydirectinput.KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
                x = StructurePy.Input(ctypes.c_ulong(1), ii_)

                # SendInput returns the number of event successfully inserted into input stream
                # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput#return-value
                insertedEvents += Pydirectinput.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

        hexKeyCode = Pydirectinput.KEYBOARD_MAPPING[key]
        extra = ctypes.c_ulong(0)
        ii_ = StructurePy.Input_I()
        ii_.ki = StructurePy.KeyBdInput(0, hexKeyCode, keybdFlags, 0, ctypes.pointer(extra))
        x = StructurePy.Input(ctypes.c_ulong(1), ii_)
        insertedEvents += Pydirectinput.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

        return insertedEvents == expectedEvents

    # Ignored parameters: logScreenshot
    # Missing feature: auto shift for special characters (ie. '!', '@', '#'...)

    @staticmethod
    def keyUp(key, logScreenshot=None, _pause=True):
        if not key in Pydirectinput.KEYBOARD_MAPPING or Pydirectinput.KEYBOARD_MAPPING[key] is None:
            return

        keybdFlags = Pydirectinput.KEYEVENTF_SCANCODE | Pydirectinput.KEYEVENTF_KEYUP

        # Init event tracking
        insertedEvents = 0
        expectedEvents = 1

        # arrow keys need the extended key flag
        if key in ['up', 'left', 'down', 'right']:
            keybdFlags |= Pydirectinput.KEYEVENTF_EXTENDEDKEY

        hexKeyCode = Pydirectinput.KEYBOARD_MAPPING[key]
        extra = ctypes.c_ulong(0)
        ii_ = StructurePy.Input_I()
        ii_.ki = StructurePy.KeyBdInput(0, hexKeyCode, keybdFlags, 0, ctypes.pointer(extra))
        x = StructurePy.Input(ctypes.c_ulong(1), ii_)

        # SendInput returns the number of event successfully inserted into input stream
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput#return-value
        insertedEvents += Pydirectinput.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

        # if numlock is on and an arrow key is being pressed, we need to send an additional scancode
        # https://stackoverflow.com/questions/14026496/sendinput-sends-num8-when-i-want-to-send-vk-up-how-come
        # https://handmade.network/wiki/2823-keyboard_inputs_-_scancodes,_raw_input,_text_input,_key_names
        if key in ['up', 'left', 'down', 'right'] and ctypes.windll.user32.GetKeyState(0x90):
            # We need to press two keys, so we expect to have inserted 2 events when done
            expectedEvents = 2
            hexKeyCode = 0xE0
            extra = ctypes.c_ulong(0)
            ii_ = StructurePy.Input_I()
            ii_.ki = StructurePy.KeyBdInput(0, hexKeyCode, Pydirectinput.KEYEVENTF_SCANCODE | Pydirectinput.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
            x = StructurePy.Input(ctypes.c_ulong(1), ii_)
            insertedEvents += Pydirectinput.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

        return insertedEvents == expectedEvents

    # Ignored parameters: logScreenshot
    # nearly identical to PyAutoGUI's implementation

    @staticmethod
    def press(keys, presses=1, interval=0.0, logScreenshot=None, _pause=True):
        if type(keys) == str:
            if len(keys) > 1:
                keys = keys.lower()
            keys = [keys]  # If keys is 'enter', convert it to ['enter'].
        else:
            lowerKeys = []
            for s in keys:
                if len(s) > 1:
                    lowerKeys.append(s.lower())
                else:
                    lowerKeys.append(s)
            keys = lowerKeys
        interval = float(interval)

        # We need to press x keys y times, which comes out to x*y presses in total
        expectedPresses = presses * len(keys)
        completedPresses = 0

        for i in range(presses):
            for k in keys:
                Pydirectinput.failSafeCheck()
                downed = Pydirectinput.keyDown(k)
                upped = Pydirectinput.keyUp(k)
                # Count key press as complete if key was "downed" and "upped" successfully
                if downed and upped:
                    completedPresses += 1

            time.sleep(interval)

        return completedPresses == expectedPresses

    # Ignored parameters: logScreenshot
    # nearly identical to PyAutoGUI's implementation

    @staticmethod
    def typewrite(message, interval=0.0, logScreenshot=None, _pause=True):
        interval = float(interval)
        for c in message:
            if len(c) > 1:
                c = c.lower()
            Pydirectinput.press(c, _pause=False)
            time.sleep(interval)
            Pydirectinput.failSafeCheck()

    write = typewrite
class KMSI:
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
        'capslock': 0x14,
        'tab': 0x09,
        'enter': 0x0D,
        'esc': 0x1B,
        'space': 0x20,
        'backspace': 0x08,
    }

    def __init__(self, hwnd=None):
        self.hwnd:int = hwnd
        self.SetKeypadDelay()
        self.SetMouseDelay()
    def press_capslock(self, open=True):
        if open:
            if not user32.GetKeyState(self.vk_key_map["capslock"]) & 1:
                Pydirectinput.press("capslock")
        else:
            if user32.GetKeyState(self.vk_key_map["capslock"]) & 1:
                Pydirectinput.press("capslock")
    # 键盘==============================
    def SetKeypadDelay(self, delay=None):
        self.keyboard_delay = 0.03 if delay is None else delay / 1000


    def KeyDownChar(self, key_str):
        # 输入大写
        if key_str.isupper():
            self.press_capslock(True)
        else:
            self.press_capslock(False)
        # 特殊按键
        if key_str in self.shift_keys:
            Pydirectinput.keyDown("shift", _pause=False)
            key_str = self.shift_keys[key_str]
        key_str = key_str.lower()
        Pydirectinput.keyDown(key_str, _pause=False)


    def KeyUpChar(self, key_str):
        if key_str in self.shift_keys:
            key_str = self.shift_keys[key_str]
            Pydirectinput.keyUp(key_str, _pause=False)
            Pydirectinput.keyUp("shift", _pause=False)
        else:
            Pydirectinput.keyUp(key_str, _pause=False)

    def KeyPressChar(self, key_str: str):
        self.KeyDownChar(key_str)
        time.sleep(self.keyboard_delay)
        self.KeyUpChar(key_str)

    def EnableRealKeypad(self, enable):
        pass

    # 鼠标==============================

    def LeftDown(self):
        Pydirectinput.mouseDown(_pause=False)


    def LeftUp(self):
        Pydirectinput.mouseUp(_pause=False)

    def LeftClick(self):
        self.LeftDown()
        time.sleep(self.mouse_delay)
        self.LeftUp()

    def LeftDoubleClick(self):
        self.LeftClick()
        time.sleep(self.mouse_delay)
        self.LeftClick()


    def RightDown(self):
        Pydirectinput.mouseDown(button="right", _pause=False)


    def RightUp(self):
        Pydirectinput.mouseUp(button="right", _pause=False)

    def RightClick(self):
        self.RightDown()
        time.sleep(self.mouse_delay)
        self.RightUp()

    def SetMouseDelay(self, delay=None):
        self.mouse_delay = 0.03 if delay is None else delay / 1000

    def MiddleClick(self):
        self.MiddleDown()
        time.sleep(self.mouse_delay)
        self.MiddleUp()


    def MiddleDown(self):
        Pydirectinput.mouseDown(button="middle", _pause=False)


    def MiddleUp(self):
        Pydirectinput.mouseUp(button="middle", _pause=False)

    def MoveTo(self, x, y):
        if self.hwnd:
            x, y = Window.ClientToScreen(self.hwnd, x, y)
        now_x,now_y = Window.GetCursorPos()
        self.MoveR(x - now_x, y - now_y)


    def WheelDown(self):
        Pydirectinput.mouseDown(button="wheel", _pause=False)


    def WheelUp(self):
        Pydirectinput.mouseUp(button="wheel", _pause=False)

    def MoveR(self, x, y):
        Pydirectinput.moveRel(xOffset=x, yOffset=y, _pause=False)

    def HotKey(self, key_list, interval=None):
        if not interval:
            interval = self.keyboard_delay
        for key in key_list:
            self.KeyDownChar(key)
            time.sleep(interval)
        for key in key_list[::-1]:
            self.KeyUpChar(key)
            time.sleep(interval)

    def KeyPressStr(self, key_list, interval=None):
        """
        支持两种格式，一种是"a,b,c",一种是["a","b","c"],或("a","b","c")等可迭代对象
        :param key_list:
        :return:
        """
        if not interval:
            interval = self.keyboard_delay
        if isinstance(key_list, str):
            for key in key_list:
                self.KeyPressChar(key)
                time.sleep(interval)
        else:
            for key in key_list:
                self.KeyPressChar(key)
                time.sleep(interval)

if __name__ == '__main__':
    km = KMSI()
    km.KeyPressChar("up")


