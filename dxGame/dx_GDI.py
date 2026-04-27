# -*- coding: utf-8 -*-
import time

from dxGame.dx_core import *


class GDI:
    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.__img_bytes = b""

    def __call_rect(self, function_name, hwnd=None):
        if hwnd is None:
            hwnd = self.hwnd
        rect = StructurePy.RECT()
        func = getattr(user32, function_name)
        result = func(hwnd, ctypes.byref(rect))
        if not result:
            return [-1, -1, -1, -1]
        return (rect.left, rect.top, rect.right, rect.bottom)

    def GetWindowRect(self) -> Tuple[int, int, int, int]:
        return self.__call_rect("GetWindowRect")

    def GetClientRect(self):
        return self.__call_rect("GetClientRect")

    def ClientToScreen(self):
        client_rect = StructurePy.RECT()
        if not user32.GetClientRect(self.hwnd, ctypes.byref(client_rect)):
            raise ctypes.WinError(ctypes.get_last_error())

        # 客户区左上角相对于窗口的坐标为 (0, 0)
        point = StructurePy.POINT(0, 0)

        # 将客户区左上角 (0, 0) 转换为屏幕坐标
        if not user32.ClientToScreen(self.hwnd, ctypes.byref(point)):
            raise ctypes.WinError(ctypes.get_last_error())

        # 计算客户区的绝对位置
        left = point.x
        top = point.y
        right = left + (client_rect.right - client_rect.left)
        bottom = top + (client_rect.bottom - client_rect.top)

        return left, top, right, bottom

    def GetDesktopWindowSize(self):
        width = user32.GetSystemMetrics(0)  # 获取屏幕宽度
        height = user32.GetSystemMetrics(1)  # 获取屏幕高度
        return width, height

    def get_bitmap_info(self, hBitmap):
        # 创建 BITMAPINFOHEADER 实例
        bmp_info = StructurePy.BITMAPINFOHEADER()
        bmp_info.biSize = ctypes.sizeof(StructurePy.BITMAPINFOHEADER)
        # 获取窗口的设备上下文
        hdc = user32.GetDC(self.hwnd)
        if not hdc:
            raise ctypes.WinError(ctypes.get_last_error())
        # 获取位图信息
        result = gdi32.GetDIBits(
            hdc,  # HDC (not needed here)
            hBitmap,  # HBITMAP
            0,  # Start scan line
            0,  # Number of scan lines (0 to retrieve header info)
            None,  # lpvBits (None because we are just getting info)
            ctypes.byref(bmp_info),  # LPBITMAPINFO (pointer to the structure)
            0  # DIB_RGB_COLORS (not using a palette)
        )

        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())

        # 返回位深
        return bmp_info

    def get_client_loc(self):
        left, top, right, bottom = self.GetWindowRect()
        left2, top2, right2, bottom2 = self.GetClientRect()
        left3, top3, right3, bottom3 = self.ClientToScreen()
        w, h = self.GetDesktopWindowSize()
        x1 = left - left3
        x1 = 0 if x1 < 0 else x1
        y1 = top - top3
        y1 = 0 if y1 < 0 else y1
        x2 = w if right2 > w else right2
        y2 = h if bottom2 > h else bottom2

        return x1, y1, x2, y2

    def get_bitmap_bits(self, hBitmap, width, height):
        # 计算图像的字节数（每行按 4 字节对齐）
        bit_count = self.get_bitmap_info(hBitmap).biBitCount
        bytes_per_pixel = bit_count // 8
        stride = (width * bytes_per_pixel + 3) & ~3  # 每行的字节数必须是 4 的倍数
        buffer_size = stride * height

        # 创建缓冲区
        bmp_buffer = ctypes.create_string_buffer(buffer_size)

        # 调用 GetBitmapBits
        result = gdi32.GetBitmapBits(hBitmap, buffer_size, bmp_buffer)

        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())

        return bmp_buffer

    def capture(self, x1=None, y1=None, x2=None, y2=None) -> memoryview:
        x1_, y1_, x2_, y2_ = self.GetClientRect()
        width_, height_ = x2_ - x1_, y2_ - y1_
        if x1 is None or y1 is None or x2 is None or y2 is None:
            x1, y1, x2, y2 = 0, 0, width_, height_
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        if x2 > width_:
            x2 = width_
        if y2 > height_:
            y2 = height_
        width = x2 - x1
        height = y2 - y1
        # Step 1: 获取窗口的设备上下文 (DC)
        # DC 是 GDI 操作的基础，代表了绘图的目标（如屏幕、内存中的位图等）
        # hWndDC 是窗口的设备上下文句柄，它提供了一个接口来与窗口绘图

        hWndDC = user32.GetDC(self.hwnd)
        if not hWndDC:
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 2: 创建一个兼容的内存设备上下文 (saveDC)
        # CreateCompatibleDC 函数创建一个与指定的 DC 兼容的内存 DC（虚拟的画布）
        # 内存 DC 是用于在内存中进行绘图操作的，而不直接影响屏幕显示
        saveDC = gdi32.CreateCompatibleDC(hWndDC)
        if not saveDC:
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 3: 创建一个与 hWndDC 兼容的位图 (saveBitMap)
        # CreateCompatibleBitmap 创建一个与指定的 DC 兼容的位图
        # 这个位图是内存 DC 的实际绘图目标，所有绘图操作的结果都会存储在这个位图中
        saveBitMap = gdi32.CreateCompatibleBitmap(hWndDC, width, height)
        saveBitMap = ctypes.c_void_p(saveBitMap)
        if not saveBitMap:
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 4: 将位图选择到内存设备上下文中
        # SelectObject 将 saveBitMap 选择到 saveDC 中，使得 saveDC 的绘图操作作用于这个位图
        # 这是内存 DC 开始绘制的基础，所有在 saveDC 上进行的操作都将反映到 saveBitMap 上
        old_obj = gdi32.SelectObject(saveDC, saveBitMap)
        if not old_obj:
            gdi32.DeleteObject(saveBitMap)
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 5: 执行 BitBlt 操作，将窗口的内容复制到内存设备上下文中
        # BitBlt 是一个核心的 GDI 操作，负责将源 DC 的内容复制到目标 DC 中
        # 在这里，我们将 hWndDC 的内容（窗口客户区）复制到 saveDC 中（即 saveBitMap 上）
        s1 = time.time()
        SRCCOPY = 0x00CC0020  # 表示直接复制源位图的内容
        result = gdi32.BitBlt(saveDC, 0, 0, width, height, hWndDC, x1, y1, SRCCOPY)
        s2 = time.time()
        if not result:
            gdi32.SelectObject(saveDC, old_obj)
            gdi32.DeleteObject(saveBitMap)
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # 准备 BITMAPINFO 结构来接收位图数据
        padding = (4 - (width * 3) % 4) % 4
        line_size = width * 3 + padding
        size = height * line_size
        bmi = StructurePy.BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(StructurePy.BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # 正常的 DIB 是自底向上，负值表示自顶向下
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 24  # 24 位 BGR 格式
        bmi.bmiHeader.biCompression = 0  # BI_RGB，无压缩
        bmi.bmiHeader.biSizeImage = size
        bmi.bmiHeader.biXPelsPerMeter = 0
        bmi.bmiHeader.biYPelsPerMeter = 0
        bmi.bmiHeader.biClrUsed = 0
        bmi.bmiHeader.biClrImportant = 0

        # 创建一个缓冲区来存储图像数据
        buffer = ctypes.create_string_buffer(size)

        # 获取位图字节数据
        bits_result = gdi32.GetDIBits(saveDC, saveBitMap, 0, height, buffer, ctypes.byref(bmi), 0)
        if bits_result == 0:
            gdi32.SelectObject(saveDC, old_obj)
            gdi32.DeleteObject(saveBitMap)
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())
        s3 = time.time()
        # print(f"总耗时:{s3-s1}, 复制图像:{s2-s1},读取图像{s3-s2}")
        # buffer = self.get_bitmap_bits(saveBitMap, width, height)  # 这个默认是BGRA
        # Step 7: 释放所有的 GDI 资源
        # 在 GDI 操作中，必须显式释放所有分配的资源，否则会导致内存泄漏
        # 我们首先将 saveDC 恢复到原来的状态，然后删除 saveBitMap 和 saveDC，并释放窗口的 DC
        gdi32.SelectObject(saveDC, old_obj)
        gdi32.DeleteObject(saveBitMap)
        gdi32.DeleteDC(saveDC)
        user32.ReleaseDC(self.hwnd, hWndDC)
        return dxpyd.MiNiNumPy.bytes_bmp_to_arr3d(buffer.raw, height, width, 3, 0)

    # 前台截图
    def capture_desktop(self, x1=None, y1=None, x2=None, y2=None) -> memoryview:
        # hwnd = user32.GetDesktopWindow()
        hwnd = 0
        x1_, y1_, x2_, y2_ = self.GetClientRect()
        width_, height_ = x2_ - x1_, y2_ - y1_
        if x1 is None or y1 is None or x2 is None or y2 is None:
            x1, y1, x2, y2 = 0, 0, width_, height_
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        if x2 > width_:
            x2 = width_
        if y2 > height_:
            y2 = height_
        width = x2 - x1
        height = y2 - y1
        # Step 1: 获取窗口的设备上下文 (DC)
        # DC 是 GDI 操作的基础，代表了绘图的目标（如屏幕、内存中的位图等）
        # hWndDC 是窗口的设备上下文句柄，它提供了一个接口来与窗口绘图

        hWndDC = user32.GetDC(hwnd)
        if not hWndDC:
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 2: 创建一个兼容的内存设备上下文 (saveDC)
        # CreateCompatibleDC 函数创建一个与指定的 DC 兼容的内存 DC（虚拟的画布）
        # 内存 DC 是用于在内存中进行绘图操作的，而不直接影响屏幕显示
        saveDC = gdi32.CreateCompatibleDC(hWndDC)
        if not saveDC:
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 3: 创建一个与 hWndDC 兼容的位图 (saveBitMap)
        # CreateCompatibleBitmap 创建一个与指定的 DC 兼容的位图
        # 这个位图是内存 DC 的实际绘图目标，所有绘图操作的结果都会存储在这个位图中
        saveBitMap = gdi32.CreateCompatibleBitmap(hWndDC, width, height)
        saveBitMap = ctypes.c_void_p(saveBitMap)
        if not saveBitMap:
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 4: 将位图选择到内存设备上下文中
        # SelectObject 将 saveBitMap 选择到 saveDC 中，使得 saveDC 的绘图操作作用于这个位图
        # 这是内存 DC 开始绘制的基础，所有在 saveDC 上进行的操作都将反映到 saveBitMap 上
        old_obj = gdi32.SelectObject(saveDC, saveBitMap)
        if not old_obj:
            gdi32.DeleteObject(saveBitMap)
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # Step 5: 执行 BitBlt 操作，将窗口的内容复制到内存设备上下文中
        # BitBlt 是一个核心的 GDI 操作，负责将源 DC 的内容复制到目标 DC 中
        # 在这里，我们将 hWndDC 的内容（窗口客户区）复制到 saveDC 中（即 saveBitMap 上）
        SRCCOPY = 0x00CC0020  # 表示直接复制源位图的内容
        left3, top3, right3, bottom3 = self.ClientToScreen()
        x1, y1 = x1 + left3, y1 + top3
        w, h = self.GetDesktopWindowSize()
        if x1 > w:
            raise ValueError("起始坐标超过屏幕横轴 %d > %d" % (x1, w))
        if y1 > h:
            raise ValueError("起始坐标超过屏幕纵轴 %d > %d" % (y1, h))
        result = gdi32.BitBlt(saveDC, 0, 0, width, height, hWndDC, x1, y1, SRCCOPY)
        if not result:
            gdi32.SelectObject(saveDC, old_obj)
            gdi32.DeleteObject(saveBitMap)
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # 准备 BITMAPINFO 结构来接收位图数据
        padding = (4 - (width * 3) % 4) % 4
        line_size = width * 3 + padding
        size = height * line_size
        bmi = StructurePy.BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(StructurePy.BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # 正常的 DIB 是自底向上，负值表示自顶向下
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 24  # 24 位 BGR 格式
        bmi.bmiHeader.biCompression = 0  # BI_RGB，无压缩
        bmi.bmiHeader.biSizeImage = size
        bmi.bmiHeader.biXPelsPerMeter = 0
        bmi.bmiHeader.biYPelsPerMeter = 0
        bmi.bmiHeader.biClrUsed = 0
        bmi.bmiHeader.biClrImportant = 0

        # 创建一个缓冲区来存储图像数据
        buffer = ctypes.create_string_buffer(size)

        # 获取位图字节数据
        bits_result = gdi32.GetDIBits(saveDC, saveBitMap, 0, height, buffer, ctypes.byref(bmi), 0)
        if bits_result == 0:
            gdi32.SelectObject(saveDC, old_obj)
            gdi32.DeleteObject(saveBitMap)
            gdi32.DeleteDC(saveDC)
            user32.ReleaseDC(self.hwnd, hWndDC)
            raise ctypes.WinError(ctypes.get_last_error())

        # buffer = self.get_bitmap_bits(saveBitMap, width, height)  # 这个默认是BGRA
        # Step 7: 释放所有的 GDI 资源
        # 在 GDI 操作中，必须显式释放所有分配的资源，否则会导致内存泄漏
        # 我们首先将 saveDC 恢复到原来的状态，然后删除 saveBitMap 和 saveDC，并释放窗口的 DC
        gdi32.SelectObject(saveDC, old_obj)
        gdi32.DeleteObject(saveBitMap)
        gdi32.DeleteDC(saveDC)
        user32.ReleaseDC(self.hwnd, hWndDC)
        return dxpyd.MiNiNumPy.bytes_bmp_to_arr3d(buffer.raw, height, width, 3, 0)
# endregion GDI
# region Display_gdi 屏幕截图
class Display_gdi:
    def __init__(self, hwnd,mode=0):
        self.mode = mode
        self.gdi = GDI(hwnd)  # 已经翻转

    def Capture(self, x1=None, y1=None, x2=None, y2=None):
        if self.mode == 0:
            img = self.gdi.capture(x1, y1, x2, y2)
        else:
            img = self.gdi.capture_desktop(x1,y1,x2,y2)
        # MiniOpenCV.imshow("img",img)
        # MiniOpenCV.waitKey(0)
        return img

if __name__ == '__main__':
    from dxGame import MiniOpenCV
    import numpy as np,cv2
    hwnd = 6555140
    gdi = Display_gdi(hwnd,1)
    image = gdi.Capture()
    # memoryview_image = image.get_memoryview()
    # cv2_image = np.asarray(memoryview_image)
    # cv2.imshow("image", cv2_image)
    # cv2.waitKey(0)
    MiniOpenCV.imshow("image", image)
    MiniOpenCV.waitKey(0)