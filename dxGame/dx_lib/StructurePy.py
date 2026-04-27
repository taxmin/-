# 定义 BMP 文件头结构
import ctypes

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p)


class BITMAPFILEHEADER(ctypes.LittleEndianStructure):
    _pack_ = 1  # 禁用字节对齐
    _fields_ = [
        ("bfType", ctypes.c_uint16),  # 文件类型，必须为 'BM' 表示 BMP 文件
        ("bfSize", ctypes.c_uint32),  # 文件大小（字节）
        ("bfReserved1", ctypes.c_uint16),  # 保留字段，必须设置为 0
        ("bfReserved2", ctypes.c_uint16),  # 保留字段，必须设置为 0
        ("bfOffBits", ctypes.c_uint32),  # 像素数据的偏移量
    ]


# 定义 BMP 信息头结构
class BITMAPINFOHEADER(ctypes.LittleEndianStructure):
    _pack_ = 1  # 禁用字节对齐
    _fields_ = [
        ("biSize", ctypes.c_uint32),  # 结构体大小
        ("biWidth", ctypes.c_int32),  # 图像宽度（像素）
        ("biHeight", ctypes.c_int32),  # 图像高度（像素）
        ("biPlanes", ctypes.c_uint16),  # 颜色平面数，必须为 1
        ("biBitCount", ctypes.c_uint16),  # 每像素位数，常见为 24 位
        ("biCompression", ctypes.c_uint32),  # 压缩类型，通常为 0（不压缩）
        ("biSizeImage", ctypes.c_uint32),  # 图像大小（字节）
        ("biXPelsPerMeter", ctypes.c_int32),  # 水平分辨率（像素/米）
        ("biYPelsPerMeter", ctypes.c_int32),  # 垂直分辨率（像素/米）
        ("biClrUsed", ctypes.c_uint32),  # 使用的颜色数，0 表示默认值
        ("biClrImportant", ctypes.c_uint32),  # 重要颜色数，0 表示所有颜色都重要
    ]


# 定义结构，用于注册窗口类
class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint),  # 窗口的样式
        ("lpfnWndProc", WNDPROC),  # 窗口过程函数指针
        ("cbClsExtra", ctypes.c_int),  # 额外的类内存
        ("cbWndExtra", ctypes.c_int),  # 额外的窗口内存
        ("hInstance", ctypes.c_void_p),  # 应用程序实例句柄
        ("hIcon", ctypes.c_void_p),  # 图标句柄
        ("hCursor", ctypes.c_void_p),  # 光标句柄
        ("hbrBackground", ctypes.c_void_p),  # 背景画刷句柄
        ("lpszMenuName", ctypes.c_wchar_p),  # 菜单名
        ("lpszClassName", ctypes.c_wchar_p),  # 窗口类名
    ]


# 定义GDI BIT信息结构
class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", ctypes.c_uint32 * 3)
    ]


# 定义Windows API中用到的结构体
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]


# 定义 POINT 结构体
class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long)
    ]


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]
