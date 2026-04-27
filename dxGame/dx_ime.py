from dxGame.dx_core import *


def 切换输入法为英语美国():
    # 加载 user32.dll 和 kernel32.dll
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    # 常量定义
    WM_INPUTLANGCHANGEREQUEST = 0x0050
    HWND_BROADCAST = 0xFFFF
    KLF_ACTIVATE = 0x00000001
    KL_INPUTLANGCHANGE = 0x0001  # 触发输入语言更改

    # 英语（美国）的 KLID
    KLID_ENGLISH_US = "00000409"

    # 定义函数原型
    user32.LoadKeyboardLayoutW.argtypes = [wintypes.LPCWSTR, wintypes.UINT]
    user32.LoadKeyboardLayoutW.restype = wintypes.HKL

    user32.ActivateKeyboardLayout.argtypes = [wintypes.HKL, wintypes.UINT]
    user32.ActivateKeyboardLayout.restype = wintypes.HKL

    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL

    kernel32.GetLastError.restype = wintypes.DWORD
    kernel32.GetLastError.argtypes = []

    # 步骤 1: 加载英语（美国）键盘布局
    hkl_english = user32.LoadKeyboardLayoutW(KLID_ENGLISH_US, KLF_ACTIVATE)
    if not hkl_english:
        error_code = kernel32.GetLastError()
        # print(f"无法加载英语（美国）输入法，错误代码: {error_code}")
        return
    else:
        pass
        # print(f"已加载英语（美国）输入法，HKL: {hkl_english:#010x}")

    # 步骤 2: 激活英语（美国）键盘布局
    activated_hkl = user32.ActivateKeyboardLayout(hkl_english, KL_INPUTLANGCHANGE)
    if not activated_hkl:
        error_code = kernel32.GetLastError()
        # print(f"无法激活英语（美国）输入法，错误代码: {error_code}")
    # else:
    #     print(f"已激活英语（美国）输入法，HKL: {activated_hkl:#010x}")

    # 步骤 3: 通过消息广播请求切换输入法
    result = user32.PostMessageW(HWND_BROADCAST, WM_INPUTLANGCHANGEREQUEST, 0, hkl_english)
    if not result:
        error_code = kernel32.GetLastError()
        print(f"无法切换到英语（美国）输入法，错误代码: {error_code}")
    else:
        print("切换到英语（美国）输入法")

    # 可选步骤: 确认当前输入法
    user32.GetKeyboardLayout.restype = wintypes.HKL
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    current_hkl = user32.GetKeyboardLayout(0)
    # print(f"当前活动的键盘布局 HKL: {current_hkl:#010x}")

if __name__ == "__main__":
    切换输入法为英语美国()