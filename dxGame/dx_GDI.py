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
        """
        GDI 截图方法（带完整的异常保护和资源清理）
        """
        hWndDC = None
        saveDC = None
        saveBitMap = None
        old_obj = None
        
        try:
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
            try:
                hWndDC = user32.GetDC(self.hwnd)
            except OSError as e:
                raise RuntimeError(f"GetDC 调用失败: {e}")
            if not hWndDC:
                raise RuntimeError(f"无法获取窗口 DC (hwnd={self.hwnd})")

            # Step 2: 创建一个兼容的内存设备上下文 (saveDC)
            try:
                saveDC = gdi32.CreateCompatibleDC(hWndDC)
            except OSError as e:
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError(f"CreateCompatibleDC 调用失败: {e}")
            if not saveDC:
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError("创建兼容 DC 失败")

            # Step 3: 创建一个与 hWndDC 兼容的位图 (saveBitMap)
            try:
                saveBitMap = gdi32.CreateCompatibleBitmap(hWndDC, width, height)
            except OSError as e:
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError(f"CreateCompatibleBitmap 调用失败: {e}")
            saveBitMap = ctypes.c_void_p(saveBitMap)
            if not saveBitMap:
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError("创建兼容位图失败")

            # Step 4: 将位图选择到内存设备上下文中
            try:
                old_obj = gdi32.SelectObject(saveDC, saveBitMap)
            except OSError as e:
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError(f"SelectObject 调用失败: {e}")
            if not old_obj:
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError("选择位图对象失败")

            # Step 5: 执行 BitBlt 操作
            s1 = time.time()
            SRCCOPY = 0x00CC0020
            try:
                result = gdi32.BitBlt(saveDC, 0, 0, width, height, hWndDC, x1, y1, SRCCOPY)
            except OSError as e:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError(f"BitBlt 调用失败: {e}")
            s2 = time.time()
            if not result:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError("BitBlt 返回失败")

            # 准备 BITMAPINFO 结构
            padding = (4 - (width * 3) % 4) % 4
            line_size = width * 3 + padding
            size = height * line_size
            bmi = StructurePy.BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(StructurePy.BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = width
            bmi.bmiHeader.biHeight = -height
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 24
            bmi.bmiHeader.biCompression = 0
            bmi.bmiHeader.biSizeImage = size
            bmi.bmiHeader.biXPelsPerMeter = 0
            bmi.bmiHeader.biYPelsPerMeter = 0
            bmi.bmiHeader.biClrUsed = 0
            bmi.bmiHeader.biClrImportant = 0

            # 创建一个缓冲区来存储图像数据
            buffer = ctypes.create_string_buffer(size)

            # 🔧 关键修复：为 GetDIBits 增加异常保护
            try:
                bits_result = gdi32.GetDIBits(saveDC, saveBitMap, 0, height, buffer, ctypes.byref(bmi), 0)
            except OSError as e:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError(f"GetDIBits 调用失败: {e}")
            except Exception as e:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError(f"GetDIBits 异常: {e}")
            
            if bits_result == 0:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
                raise RuntimeError(f"GetDIBits 返回 0，可能窗口已关闭")
            
            s3 = time.time()
            
            # Step 7: 释放所有的 GDI 资源
            try:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(self.hwnd, hWndDC)
            except Exception as e:
                # 资源释放失败不影响返回值，只记录日志
                import logging
                logging.warning(f"GDI 资源释放警告: {e}")
            
            return dxpyd.MiNiNumPy.bytes_bmp_to_arr3d(buffer.raw, height, width, 3, 0)
            
        except MemoryError as e:
            # 🔧 捕获内存错误，防止崩溃
            import logging
            logging.error(f"❌ GDI capture 内存错误: {e}")
            # 确保资源释放
            if saveBitMap:
                try: gdi32.DeleteObject(saveBitMap)
                except: pass
            if saveDC:
                try: gdi32.DeleteDC(saveDC)
                except: pass
            if hWndDC:
                try: user32.ReleaseDC(self.hwnd, hWndDC)
                except: pass
            raise
        except WindowsError as e:
            import logging
            logging.error(f"❌ GDI capture Windows API 错误: {e}")
            # 确保资源释放
            if saveBitMap:
                try: gdi32.DeleteObject(saveBitMap)
                except: pass
            if saveDC:
                try: gdi32.DeleteDC(saveDC)
                except: pass
            if hWndDC:
                try: user32.ReleaseDC(self.hwnd, hWndDC)
                except: pass
            raise
        except Exception as e:
            import logging
            logging.error(f"❌ GDI capture 异常: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            # 确保资源释放
            if saveBitMap:
                try: gdi32.DeleteObject(saveBitMap)
                except: pass
            if saveDC:
                try: gdi32.DeleteDC(saveDC)
                except: pass
            if hWndDC:
                try: user32.ReleaseDC(self.hwnd, hWndDC)
                except: pass
            raise

    # 前台截图
    def capture_desktop(self, x1=None, y1=None, x2=None, y2=None) -> memoryview:
        """
        桌面截图方法（带完整的异常保护和资源清理）
        """
        hWndDC = None
        saveDC = None
        saveBitMap = None
        old_obj = None
        
        try:
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
            try:
                hWndDC = user32.GetDC(hwnd)
            except OSError as e:
                raise RuntimeError(f"GetDC 调用失败: {e}")
            if not hWndDC:
                raise RuntimeError("无法获取桌面 DC")

            # Step 2: 创建一个兼容的内存设备上下文 (saveDC)
            try:
                saveDC = gdi32.CreateCompatibleDC(hWndDC)
            except OSError as e:
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError(f"CreateCompatibleDC 调用失败: {e}")
            if not saveDC:
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError("创建兼容 DC 失败")

            # Step 3: 创建一个与 hWndDC 兼容的位图 (saveBitMap)
            try:
                saveBitMap = gdi32.CreateCompatibleBitmap(hWndDC, width, height)
            except OSError as e:
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError(f"CreateCompatibleBitmap 调用失败: {e}")
            saveBitMap = ctypes.c_void_p(saveBitMap)
            if not saveBitMap:
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError("创建兼容位图失败")

            # Step 4: 将位图选择到内存设备上下文中
            try:
                old_obj = gdi32.SelectObject(saveDC, saveBitMap)
            except OSError as e:
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError(f"SelectObject 调用失败: {e}")
            if not old_obj:
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError("选择位图对象失败")

            # Step 5: 执行 BitBlt 操作
            SRCCOPY = 0x00CC0020
            left3, top3, right3, bottom3 = self.ClientToScreen()
            x1, y1 = x1 + left3, y1 + top3
            w, h = self.GetDesktopWindowSize()
            if x1 > w:
                raise ValueError("起始坐标超过屏幕横轴 %d > %d" % (x1, w))
            if y1 > h:
                raise ValueError("起始坐标超过屏幕纵轴 %d > %d" % (y1, h))
            
            try:
                result = gdi32.BitBlt(saveDC, 0, 0, width, height, hWndDC, x1, y1, SRCCOPY)
            except OSError as e:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError(f"BitBlt 调用失败: {e}")
            if not result:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError("BitBlt 返回失败")

            # 准备 BITMAPINFO 结构
            padding = (4 - (width * 3) % 4) % 4
            line_size = width * 3 + padding
            size = height * line_size
            bmi = StructurePy.BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(StructurePy.BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = width
            bmi.bmiHeader.biHeight = -height
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 24
            bmi.bmiHeader.biCompression = 0
            bmi.bmiHeader.biSizeImage = size
            bmi.bmiHeader.biXPelsPerMeter = 0
            bmi.bmiHeader.biYPelsPerMeter = 0
            bmi.bmiHeader.biClrUsed = 0
            bmi.bmiHeader.biClrImportant = 0

            # 创建一个缓冲区来存储图像数据
            buffer = ctypes.create_string_buffer(size)

            # 🔧 关键修复：为 GetDIBits 增加异常保护
            try:
                bits_result = gdi32.GetDIBits(saveDC, saveBitMap, 0, height, buffer, ctypes.byref(bmi), 0)
            except OSError as e:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError(f"GetDIBits 调用失败: {e}")
            except Exception as e:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError(f"GetDIBits 异常: {e}")
            
            if bits_result == 0:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
                raise RuntimeError("GetDIBits 返回 0，可能窗口已关闭")

            # Step 7: 释放所有的 GDI 资源
            try:
                gdi32.SelectObject(saveDC, old_obj)
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(saveDC)
                user32.ReleaseDC(hwnd, hWndDC)
            except Exception as e:
                import logging
                logging.warning(f"GDI 资源释放警告: {e}")
            
            return dxpyd.MiNiNumPy.bytes_bmp_to_arr3d(buffer.raw, height, width, 3, 0)
            
        except MemoryError as e:
            import logging
            logging.error(f"❌ GDI capture_desktop 内存错误: {e}")
            # 确保资源释放
            if saveBitMap:
                try: gdi32.DeleteObject(saveBitMap)
                except: pass
            if saveDC:
                try: gdi32.DeleteDC(saveDC)
                except: pass
            if hWndDC:
                try: user32.ReleaseDC(hwnd if 'hwnd' in locals() else 0, hWndDC)
                except: pass
            raise
        except WindowsError as e:
            import logging
            logging.error(f"❌ GDI capture_desktop Windows API 错误: {e}")
            # 确保资源释放
            if saveBitMap:
                try: gdi32.DeleteObject(saveBitMap)
                except: pass
            if saveDC:
                try: gdi32.DeleteDC(saveDC)
                except: pass
            if hWndDC:
                try: user32.ReleaseDC(hwnd if 'hwnd' in locals() else 0, hWndDC)
                except: pass
            raise
        except Exception as e:
            import logging
            logging.error(f"❌ GDI capture_desktop 异常: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            # 确保资源释放
            if saveBitMap:
                try: gdi32.DeleteObject(saveBitMap)
                except: pass
            if saveDC:
                try: gdi32.DeleteDC(saveDC)
                except: pass
            if hWndDC:
                try: user32.ReleaseDC(hwnd if 'hwnd' in locals() else 0, hWndDC)
                except: pass
            raise
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