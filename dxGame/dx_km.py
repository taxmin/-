import ctypes
import os.path
import time
from ctypes import wintypes

# 定义常量
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000

OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

# FILE_DEVICE_KEYBOARD = 0x0000000b
# FILE_DEVICE_MOUSE = 0x0000000f
#
# METHOD_BUFFERED = 0x0
# FILE_ANY_ACCESS = 0x0
#
# def CTL_CODE(DeviceType, Function, Method, Access):
#     return (DeviceType << 16) | (Access << 14) | (Function << 2) | Method
#
# IOCTL_KEYBOARD = CTL_CODE(FILE_DEVICE_KEYBOARD, 0x0, METHOD_BUFFERED, FILE_ANY_ACCESS)
# IOCTL_MOUSE = CTL_CODE(FILE_DEVICE_MOUSE, 0x0, METHOD_BUFFERED, FILE_ANY_ACCESS)
# 与 C 宏一致的设备类型
FILE_DEVICE_KEYMOUSE = 0x8000  # 键鼠设备类型

# 与 C 宏一致的功能码基值
KEYMOUSE_IOCTL_BASE = 0x800    # 功能码基值

# 方法和访问权限（与 C 宏一致）
METHOD_BUFFERED = 0x0
FILE_ANY_ACCESS = 0x0

# 定义 CTL_CODE 宏
def CTL_CODE(DeviceType, Function, Method, Access):
    return (DeviceType << 16) | (Access << 14) | (Function << 2) | Method

# 定义 CTL_CODE_KEYMOUSE 宏
def CTL_CODE_KEYMOUSE(i):
    return CTL_CODE(FILE_DEVICE_KEYMOUSE, KEYMOUSE_IOCTL_BASE + i, METHOD_BUFFERED, FILE_ANY_ACCESS)

# 与 C 宏一致的 IOCTL 定义
IOCTL_KEYBOARD = CTL_CODE_KEYMOUSE(0)  # 键盘 IOCTL
IOCTL_MOUSE = CTL_CODE_KEYMOUSE(1)     # 鼠标 IOCTL

# 键盘输入标志
KEY_MAKE = 0x00  # 按下
KEY_BREAK = 0x01  # 弹起
KEY_E0 = 0x02
KEY_E1 = 0x04

KEY_DOWN = KEY_MAKE
KEY_UP = KEY_BREAK

# 鼠标移动标志
MOUSE_MOVE_RELATIVE = 0x00
MOUSE_MOVE_ABSOLUTE = 0x01

# 鼠标按钮标志
MOUSE_LEFT_BUTTON_DOWN = 0x0001
MOUSE_LEFT_BUTTON_UP = 0x0002
MOUSE_RIGHT_BUTTON_DOWN = 0x0004
MOUSE_RIGHT_BUTTON_UP = 0x0008
MOUSE_MIDDLE_BUTTON_DOWN = 0x0010
MOUSE_MIDDLE_BUTTON_UP = 0x0020

# 定义键盘输入数据结构
class KEYBOARD_INPUT_DATA(ctypes.Structure):
    _fields_ = [
        ('UnitId', wintypes.USHORT),
        ('MakeCode', wintypes.USHORT),
        ('Flags', wintypes.USHORT),
        ('Reserved', wintypes.USHORT),
        ('ExtraInformation', wintypes.ULONG)
    ]

# 定义鼠标输入数据结构
class _ButtonsStruct(ctypes.Structure):
    _fields_ = [
        ('ButtonFlags', wintypes.USHORT),
        ('ButtonData', wintypes.USHORT)
    ]

class _ButtonsUnion(ctypes.Union):
    _fields_ = [
        ('Buttons', wintypes.ULONG),
        ('ButtonStruct', _ButtonsStruct)
    ]

class MOUSE_INPUT_DATA(ctypes.Structure):
    _fields_ = [
        ('UnitId', wintypes.USHORT),
        ('Flags', wintypes.USHORT),
        ('ButtonsUnion', _ButtonsUnion),
        ('RawButtons', wintypes.ULONG),
        ('LastX', wintypes.LONG),
        ('LastY', wintypes.LONG),
        ('ExtraInformation', wintypes.ULONG)
    ]

# 导入所需的Windows API函数
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
user32 = ctypes.WinDLL('user32', use_last_error=True)

CreateFileA = kernel32.CreateFileA
CreateFileA.argtypes = [wintypes.LPCSTR, wintypes.DWORD, wintypes.DWORD,
                        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
CreateFileA.restype = wintypes.HANDLE

DeviceIoControl = kernel32.DeviceIoControl
DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                            wintypes.LPVOID, wintypes.DWORD,
                            wintypes.LPVOID, wintypes.DWORD,
                            ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
DeviceIoControl.restype = wintypes.BOOL

MapVirtualKey = user32.MapVirtualKeyW
MapVirtualKey.argtypes = [wintypes.UINT, wintypes.UINT]
MapVirtualKey.restype = wintypes.UINT

GetSystemMetrics = user32.GetSystemMetrics
GetSystemMetrics.argtypes = [wintypes.INT]
GetSystemMetrics.restype = wintypes.INT

SM_CXSCREEN = 0
SM_CYSCREEN = 1
MAPVK_VK_TO_VSC = 0

# 全局驱动句柄
drvhandle = None

def SetHandle():
    """获取驱动句柄"""
    global drvhandle
    drvhandle = CreateFileA(
        b"\\\\.\\kmclass",
        GENERIC_READ | GENERIC_WRITE,
        0,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    if drvhandle == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

def KeyDown(VirtualKey):
    """按下键盘按键"""
    kid = KEYBOARD_INPUT_DATA()
    kid.MakeCode = MapVirtualKey(VirtualKey, MAPVK_VK_TO_VSC)
    # kid.Flags = KEY_DOWN

    # 判断是否需要设置扩展标志
    extended_keys = [0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F, 0x26, 0x28, 0x25, 0x27]  # 小键盘按键和方向键
    if VirtualKey in extended_keys:
        kid.Flags = KEY_DOWN | 0x0002  # 添加扩展标志,发送键值码
    else:
        kid.Flags = KEY_DOWN


    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_KEYBOARD,
                          ctypes.byref(kid), ctypes.sizeof(kid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def KeyUp(VirtualKey):
    """释放键盘按键"""
    kid = KEYBOARD_INPUT_DATA()
    # 判断是否需要设置扩展标志
    extended_keys = [0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F, 0x26, 0x28, 0x25, 0x27]  # 小键盘按键和方向键
    if VirtualKey in extended_keys:
        kid.Flags = KEY_UP | 0x0002  # 添加扩展标志,发送键值码
    else:
        kid.Flags = KEY_UP
    kid.MakeCode = MapVirtualKey(VirtualKey, MAPVK_VK_TO_VSC)
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_KEYBOARD,
                          ctypes.byref(kid), ctypes.sizeof(kid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseLeftButtonDown():
    """鼠标左键按下"""
    mid = MOUSE_INPUT_DATA()
    mid.ButtonsUnion.ButtonStruct.ButtonFlags = MOUSE_LEFT_BUTTON_DOWN
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseLeftButtonUp():
    """鼠标左键释放"""
    mid = MOUSE_INPUT_DATA()
    mid.ButtonsUnion.ButtonStruct.ButtonFlags = MOUSE_LEFT_BUTTON_UP
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseRightButtonDown():
    """鼠标右键按下"""
    mid = MOUSE_INPUT_DATA()
    mid.ButtonsUnion.ButtonStruct.ButtonFlags = MOUSE_RIGHT_BUTTON_DOWN
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseRightButtonUp():
    """鼠标右键释放"""
    mid = MOUSE_INPUT_DATA()
    mid.ButtonsUnion.ButtonStruct.ButtonFlags = MOUSE_RIGHT_BUTTON_UP
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseMiddleButtonDown():
    """鼠标中键按下"""
    mid = MOUSE_INPUT_DATA()
    mid.ButtonsUnion.ButtonStruct.ButtonFlags = MOUSE_MIDDLE_BUTTON_DOWN
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseMiddleButtonUp():
    """鼠标中键释放"""
    mid = MOUSE_INPUT_DATA()
    mid.ButtonsUnion.ButtonStruct.ButtonFlags = MOUSE_MIDDLE_BUTTON_UP
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseMoveRELATIVE(dx, dy):
    """鼠标相对移动"""
    mid = MOUSE_INPUT_DATA()
    mid.Flags = MOUSE_MOVE_RELATIVE
    mid.LastX = dx
    mid.LastY = dy
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())

def MouseMoveABSOLUTE(x, y):
    """鼠标绝对移动"""
    mid = MOUSE_INPUT_DATA()
    mid.Flags = MOUSE_MOVE_ABSOLUTE
    screen_width = GetSystemMetrics(SM_CXSCREEN)
    screen_height = GetSystemMetrics(SM_CYSCREEN)
    mid.LastX = int(x * 0xffff / screen_width)
    mid.LastY = int(y * 0xffff / screen_height)
    dwOutput = wintypes.DWORD()
    res = DeviceIoControl(drvhandle, IOCTL_MOUSE,
                          ctypes.byref(mid), ctypes.sizeof(mid),
                          None, 0,
                          ctypes.byref(dwOutput), None)
    if not res:
        raise ctypes.WinError(ctypes.get_last_error())


if __name__ == '__main__':
    time.sleep(1)
    from dxGame import dx_core_path
    from dx_driver import DxDriver
    dxd =  DxDriver(os.path.join(dx_core_path, 'dxkm.sys'))
    # dxd.uninstall()
    dxd.install()
    dxd.start()
    SetHandle()
    a = 0x41
    KeyDown(a)
    KeyUp(a)
    # dxd.stop()
    # dxd.uninstall()