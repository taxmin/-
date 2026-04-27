# -*- coding: utf-8 -*-
import ctypes
import io

from dxGame.dx_core import *
from dxGame.dx_lib.StructurePy import WNDPROC
class HSV_COLOR:
    保留所有颜色 = [[0, 0, 0], [179, 255, 255]]

    保留黑色 = [[0, 0, 0], [179, 255, 46]]
    保留灰色 = [[0, 0, 46], [179, 43, 220]]
    保留白色 = [[0, 0, 221], [179, 30, 255]]
    保留红色1 = [[0, 43, 46], [10, 255, 255]]
    保留红色2 = [[156, 43, 46], [179, 255, 255]]

    保留橙色 = [[11, 43, 46], [25, 255, 255]]
    保留黄色 = [[26, 0, 0], [34, 255, 255]]
    保留绿色 = [[35, 43, 46], [77, 255, 255]]
    保留青色 = [[78, 43, 46], [99, 255, 255]]
    保留蓝色 = [[100, 43, 46], [124, 255, 255]]

    保留紫色 = [[125, 43, 46], [155, 255, 255]]

class MiniOpenCV:
    # region 全局变量
    # 颜色空间转换
    COLOR_BGRA2BGR = 1  # BGRA转BGR
    COLOR_RGBA2BGR = 4  # RGBA转BGR
    COLOR_BGR2GRAY = 6  # BGR转灰度
    COLOR_GRAY2BGR = 8  # 灰度转BGR
    COLOR_BGR2HSV = 40  # BGR转HSV,有精度损失
    COLOR_HSV2BGR = 54  # HSV转BGR,有精度损失
    # 二值化模式
    THRESH_BINARY = 0  # 大于阈值的像素值设为 maxval，否则设为 0。
    THRESH_BINARY_INV = 1  # 与 THRESH_BINARY 相反，大于阈值的像素值设为 0，否则设为 maxval。
    THRESH_TRUNC = 2  # 大于阈值的像素值设为阈值，其它像素值保持不变。
    THRESH_TOZERO = 3  # 小于阈值的像素值设为 0，其它像素值保持不变。
    THRESH_TOZERO_INV = 4  # 与 THRESH_TOZERO 相反，小于阈值的像素值设为 0，其它像素值保持不变。
    # 轮廓检索模式
    RETR_EXTERNAL = 0  # 只检索最外层的轮廓。
    RETR_LIST = 1  # 未实现   检索所有轮廓，但不建立轮廓之间的父子关系。
    RETR_CCOMP = 2  # 未实现   检索所有轮廓并建立两个层次的轮廓结构
    RETR_TREE = 3  # 未实现   检索所有轮廓并建立完整的层次关系。
    # 轮廓近似方法
    CHAIN_APPROX_NONE = 1  # 未实现   保存所有的轮廓点，不进行任何压缩。
    CHAIN_APPROX_SIMPLE = 2  # 只保留轮廓的拐点，压缩垂直、水平和对角线方向的轮廓。
    CHAIN_APPROX_TC89_L1 = 3  # 未实现   基于 Teh-Chin 89 算法的 L1 近似方法。该方法能够提供较好的近似效果，尤其是在处理一些复杂轮廓时。其实现通常是相对较复杂的。
    CHAIN_APPROX_TC89_KCOS = 4  # 未实现   基于 Teh-Chin 89 算法的 KCOS 近似方法。使用场景：类似于 L1 方法，但采用不同的处理方式，通常用于特定场景中。

    # 全局字典用于保存多个窗口的句柄和相关信息
    _windows = {}
    # endregion 全局变量
    @staticmethod
    def threshold(img,_thresh:int=0, _maxval:int=255, _type=THRESH_BINARY):
        return dxpyd.MiNiNumPy.threshold(img,_thresh,_maxval,_type)

    @staticmethod
    def rectangle(img, pts, color=(0, 0, 255), thickness=1, lineType=0):
        if len(img.shape) != 3:
            raise ValueError("rectangle 画框 只支持三维数组")
        if len(pts) != 4:
            raise ValueError("rectangle 画框 输入参数pts必须为4维数组")
        x1, y1, x2, y2 = pts
        if x1 > x2 or y1 > y2:
            raise ValueError("rectangle 画框 输入参数pts的坐标顺序错误 pts=%s" % pts)
        if len(color) != 3:
            raise ValueError("rectangle 画框 color参数只支持三通道")
        return dxpyd.MiNiNumPy.rectangle(img, (x1, y1, x2, y2), color, thickness, lineType)
    @staticmethod
    def minAreaRect(cnt):
        if len(cnt) == 0:
            raise ValueError("findContours 轮廓检测 输入参数cnt为空")
        return dxpyd.MiNiNumPy.minAreaRect(cnt)

    @staticmethod
    def findContours(_img, _mode: int = RETR_EXTERNAL, _method: int = CHAIN_APPROX_NONE):
        if len(_img.shape) != 2:
            raise ValueError("findContours 轮廓检测 只支持二维数组")
        if _mode not in [MiniOpenCV.RETR_EXTERNAL, MiniOpenCV.RETR_LIST, MiniOpenCV.RETR_TREE, MiniOpenCV.RETR_CCOMP]:
            raise ValueError("不支持的轮廓检测模式 mode=%s" % _mode)
        if _method not in [MiniOpenCV.CHAIN_APPROX_NONE, MiniOpenCV.CHAIN_APPROX_SIMPLE, MiniOpenCV.CHAIN_APPROX_TC89_L1, MiniOpenCV.CHAIN_APPROX_TC89_KCOS]:
            raise ValueError("不支持的轮廓检测方法 method=%s" % _method)
        return dxpyd.MiNiNumPy.findContours(_img, _mode, _method)

    @staticmethod
    def inRange(img, lower, upper):
        return dxpyd.MiNiNumPy.inRange(img, lower, upper)
    @staticmethod
    def vstack(img_top,img_down):
        return dxpyd.MiNiNumPy.vstack(img_top,img_down)


    @staticmethod
    def imwrite(filename: str, img: memoryview):
        if len(img.shape) == 2:
            img = MiniOpenCV.cvtColor(img, MiniOpenCV.COLOR_GRAY2BGR)
        if len(img.shape) != 3:
            raise ValueError("图像必须是三通道")
        if img.shape[2] != 3:
            raise ValueError("只支持h*w*3的维度")

        # 获取图像尺寸
        height = img.shape[0]
        width = img.shape[1]
        depth = 24  # 24 bits per pixel (8 bits for R, G, B)
        padding = (4 - (width * 3 % 4)) % 4
        # BMP 文件头（14 字节）
        file_size = 14 + 40 + (width + padding) * height * 3
        bmp_file_header = bytearray([
            0x42, 0x4D,  # 'BM' 标识
            file_size & 0xFF, (file_size >> 8) & 0xFF, (file_size >> 16) & 0xFF, (file_size >> 24) & 0xFF,  # 文件大小
            0x00, 0x00,  # 保留字段1
            0x00, 0x00,  # 保留字段2
            0x36, 0x00, 0x00, 0x00  # 像素数据的偏移量，54 字节（14 + 40）
        ])

        # DIB 信息头（40 字节）
        bmp_info_header = bytearray([
            0x28, 0x00, 0x00, 0x00,  # 信息头大小，40 字节
            width & 0xFF, (width >> 8) & 0xFF, (width >> 16) & 0xFF, (width >> 24) & 0xFF,  # 图像宽度
            height & 0xFF, (height >> 8) & 0xFF, (height >> 16) & 0xFF, (height >> 24) & 0xFF,  # 图像高度
            0x01, 0x00,  # 颜色平面数，固定为1
            depth & 0xFF, 0x00,  # 每像素位数，24 位
            0x00, 0x00, 0x00, 0x00,  # 无压缩
            0x00, 0x00, 0x00, 0x00,  # 图像大小（可以为0，表示无压缩）
            0x13, 0x0B, 0x00, 0x00,  # 水平分辨率（像素/米，默认为 2835，72 DPI）
            0x13, 0x0B, 0x00, 0x00,  # 垂直分辨率（像素/米，默认为 2835，72 DPI）
            0x00, 0x00, 0x00, 0x00,  # 调色板颜色数（0表示无调色板）
            0x00, 0x00, 0x00, 0x00  # 重要颜色数（0表示所有颜色都重要）
        ])

        # 像素数据：BMP 的像素顺序为 BGR，需要将 RGB 转换为 BGR
        bmp_img = dxpyd.MiNiNumPy.flipped_3d(img)
        bmp_data = dxpyd.MiNiNumPy.arr3d_add_padding_to_bytes(bmp_img)

        # 将文件头、信息头和像素数据写入文件
        with open(filename, 'wb') as f:
            f.write(bmp_file_header)
            f.write(bmp_info_header)
            f.write(bmp_data)

        print(f"BMP 图像已保存为 {filename}")

    @staticmethod
    def cvtColor(img, color_type):
        return dxpyd.MiNiNumPy.cvtColor(img, color_type)

    @staticmethod
    def resize(img, dsize=None, fx=None, fy=None, interpolation=None):
        if fx is None:
            fx = 0
        if fy is None:
            fy = 0
        if fx == fy == 0:
            raise ValueError("resize函数中，fx和fy不能同时为None,且必须有一个为浮点数，目前只支持使用fx和fy最近邻插值放大")
        if isinstance(fx, (int, float)) or isinstance(fy, (int, float)):
            return dxpyd.MiNiNumPy.resize(img, fx, fy)
        raise ValueError("resize函数中,目前只支持使用fx和fy最近邻插值放大")

    @staticmethod  # 窗口回调函数（处理消息）
    def wnd_proc(hWnd, message, wParam, lParam):
        WM_CLOSE = 0x0010
        WM_DESTROY = 0x0002
        WM_PAINT = 0x000F
        # 检查 wParam 和 lParam 是否为 None，如果是则设置为 0
        if wParam is None:
            wParam = 0
        if lParam is None:
            lParam = 0

        # 动态调整参数类型
        if platform.architecture()[0] == '64bit':
            wParam = ctypes.c_ulonglong(wParam)
            lParam = ctypes.c_longlong(lParam)
        else:
            wParam = ctypes.c_uint(wParam)
            lParam = ctypes.c_long(lParam)
        if message == WM_CLOSE:  # WM_CLOSE
            user32.DestroyWindow(hWnd)  # 关闭窗口
            return 0
        if message == WM_DESTROY:
            # for title, info in MiniOpenCV._windows.items():
            #     if info['hWnd'] == hWnd:
            #         del MiniOpenCV._windows[title]
            #         break
            user32.PostQuitMessage(0)  # 终止消息循环
            return 0
        elif message == WM_PAINT:
            hdc = user32.GetDC(hWnd)  # 获取设备上下文句柄
            mem_dc = gdi32.CreateCompatibleDC(hdc)  # 创建内存DC

            # 查找当前窗口的信息
            for title, win_info in MiniOpenCV._windows.items():
                if win_info['hWnd'] == hWnd:
                    # 获取窗口相关的图像和信息
                    pixel_data = win_info['pixel_data']
                    info_header = win_info['info_header']
                    # 创建DIB位图
                    hbitmap = MiniOpenCV.create_dib_bitmap(hdc, info_header, pixel_data)
                    if hbitmap:
                        gdi32.SelectObject(mem_dc, hbitmap)  # 选择位图到内存DC中
                        gdi32.BitBlt(hdc, 0, 0, info_header.biWidth, abs(info_header.biHeight), mem_dc, 0, 0,
                                     0x00CC0020)  # 复制位图
                    # 清理资源
                    gdi32.DeleteDC(mem_dc)
                    gdi32.DeleteObject(hbitmap)
                    user32.ReleaseDC(hWnd, hdc)
                    return 0
        else:
            return user32.DefWindowProcW(hWnd, message, wParam, lParam)  # 默认处理其他消息

    # 创建位图数据的方法
    @staticmethod
    def create_dib_bitmap(hdc, info_header, pixel_data):
        bmi = StructurePy.BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(StructurePy.BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = info_header.biWidth
        bmi.bmiHeader.biHeight = info_header.biHeight
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 24  # 假设是24位位图
        bmi.bmiHeader.biCompression = 0  # BI_RGB，无压缩
        bmi.bmiHeader.biSizeImage = info_header.biSizeImage
        bmi.bmiHeader.biXPelsPerMeter = info_header.biXPelsPerMeter
        bmi.bmiHeader.biYPelsPerMeter = info_header.biYPelsPerMeter
        bmi.bmiHeader.biClrUsed = 0
        bmi.bmiHeader.biClrImportant = 0

        bits = ctypes.c_void_p()
        hbitmap = gdi32.CreateDIBSection(hdc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
        ctypes.memmove(bits, pixel_data, info_header.biSizeImage)
        return hbitmap

    # 创建窗口
    @staticmethod
    def nameWindow(title):
        if title in MiniOpenCV._windows:
            print(f"Window '{title}' already exists.")
            return

        # 注册窗口类
        wnd_class = StructurePy.WNDCLASS()
        wnd_class.lpfnWndProc = WNDPROC(MiniOpenCV.wnd_proc)
        wnd_class.hInstance = kernel32.GetModuleHandleW(None)  # 获取模块实例句柄
        # wnd_class.hInstance = ctypes.c_void_p(kernel32.GetModuleHandleW(None))
        wnd_class.lpszClassName = title  # 窗口类名

        # 注册窗口类，并获取类原子值（唯一标识符）
        class_atom = user32.RegisterClassW(ctypes.byref(wnd_class))

        # 存储窗口信息，窗口尚未显示
        MiniOpenCV._windows[title] = {'class_atom': class_atom, 'wnd_class': wnd_class}

    # 显示并刷新窗口内容
    @staticmethod
    def imshow(title, img):

        if not (2 <= len(img.shape) <= 3):
            raise ValueError("图片只支持2通道灰度图或者3通道彩色图,不支持其他通道")
        h, w = img.shape[:2]
        if len(img.shape) == 2:
            img = MiniOpenCV.cvtColor(img, MiniOpenCV.COLOR_GRAY2BGR)
        pixel_data = dxpyd.MiNiNumPy.arr3d_add_padding_to_bytes(img)
        if h < 0:
            h = -h
            biHeight = h
        else:
            biHeight = -h
        if MiniOpenCV._windows.get(title) is None or not user32.IsWindow(MiniOpenCV._windows[title].get('hWnd')):
            # 如果没有创建窗口，创建新窗口
            MiniOpenCV.nameWindow(title)
            values = list(MiniOpenCV._windows.keys())
            title_index = values.index(title)
            wnd_class = MiniOpenCV._windows[title]['wnd_class']
            class_atom = MiniOpenCV._windows[title]['class_atom']
            if not MiniOpenCV._windows[title].get('hWnd') or not user32.IsWindow(MiniOpenCV._windows[title]['hWnd']):
                # 定义窗口样式
                window_style = 0x10CF0000  # 窗口样式，例如 WS_OVERLAPPEDWINDOW
                window_ex_style = 0  # 扩展窗口样式
                # 计算非客户区的大小
                rect = StructurePy.RECT(0, 0, w, h)  # 目标客户区大小
                user32.AdjustWindowRectEx(ctypes.byref(rect), window_style, False, window_ex_style)

                # 调整后的窗口宽高
                adjusted_width = rect.right - rect.left
                adjusted_height = rect.bottom - rect.top
                # 创建窗口
                hWnd = user32.CreateWindowExW(
                    0,  # 扩展窗口样式
                    class_atom,  # 窗口类名
                    title,  # 窗口标题
                    window_style,  # 窗口样式（例如 WS_OVERLAPPEDWINDOW）
                    30 * title_index,
                    30 * title_index,  # 窗口初始位置 (x, y)
                    adjusted_width,  # 窗口宽度 (设置一个默认值，如300)
                    adjusted_height,  # 窗口高度 (设置一个默认值，如300)
                    None,   # 无父窗口
                    None,  # 无父窗口和菜单
                    ctypes.c_void_p(wnd_class.hInstance),  # 应用程序实例句柄
                    None  # 无附加参数
                )
                MiniOpenCV._windows[title]['hWnd'] = hWnd
                MiniOpenCV._windows[title]['adjusted_width'] = adjusted_width
                MiniOpenCV._windows[title]['adjusted_height'] = adjusted_height
            else:
                hWnd = MiniOpenCV._windows[title]['hWnd']
                user32.InvalidateRect(hWnd, None, True)
                adjusted_width = MiniOpenCV._windows[title]['adjusted_width']
                adjusted_height = MiniOpenCV._windows[title]['adjusted_height']
        # 更新图像信息
        MiniOpenCV._windows[title]['pixel_data'] = pixel_data  # pixel_data需要对齐,不然最后一行会有些问题
        MiniOpenCV._windows[title]['info_header'] = StructurePy.BITMAPINFOHEADER()
        MiniOpenCV._windows[title]['info_header'].biWidth = w
        MiniOpenCV._windows[title]['info_header'].biHeight = biHeight  # 负值表示自上而下的位图
        MiniOpenCV._windows[title]['info_header'].biSizeImage = len(pixel_data)
        MiniOpenCV._windows[title]['info_header'].biBitCount = 24

        if not MiniOpenCV._windows[title].get('Move'):
            # user32.MoveWindow(hWnd, 0, 0, w, h, True)
            MiniOpenCV._windows[title]['Move'] = True

    # 销毁特定窗口
    @staticmethod
    def destroyWindow():
        for title in list(MiniOpenCV._windows.keys()):
            user32.DestroyWindow(MiniOpenCV._windows[title]['hWnd'])
            user32.UnregisterClassW(MiniOpenCV._windows[title]['wnd_class'].lpszClassName,
                                    MiniOpenCV._windows[title]['wnd_class'].hInstance)
            del MiniOpenCV._windows[title]  # 移除窗口信息

    # 等待按键
    @staticmethod
    def waitKey(timeout=0):
        msg = wintypes.MSG()
        if not timeout:
            # 消息循环处理
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        else:
            start_time = time.time()
            while (time.time() - start_time) < timeout / 1000:
                if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    # 如果有消息，则处理消息
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    # 如果没有消息，休眠一小段时间，避免占用过多CPU资源
                    time.sleep(0.001)

    @staticmethod  # 读取 BMP 文件并解析
    def imread(filename):
        with open(filename, 'rb') as f:
            file_header = StructurePy.BITMAPFILEHEADER()
            f.readinto(file_header)

            # 检查 BMP 文件类型
            if file_header.bfType != 0x4D42:  # 'BM' in hex，确认文件是 BMP 格式
                raise ValueError("Not a BMP file")

            # 读取 BMP 信息头
            info_header = StructurePy.BITMAPINFOHEADER()
            f.readinto(info_header)
            h = info_header.biHeight
            w = info_header.biWidth
            c = info_header.biBitCount // 8
            # 移动文件指针到像素数组开始位置
            f.seek(file_header.bfOffBits)
            # 读取像素数据
            if info_header.biSizeImage:
                pixel_data = f.read(info_header.biSizeImage)
            else:
                new_line_size = (w * c + 3) & ~ 3
                pixel_data = f.read(h * new_line_size)
            return dxpyd.MiNiNumPy.bytes_bmp_to_arr3d(pixel_data, h, w, c, flip=1)

    @staticmethod  # 读取 BMP 文件并解析
    def imread_decode(file_bytes):
        with io.BytesIO(file_bytes) as f:
            file_header = StructurePy.BITMAPFILEHEADER()
            f.readinto(file_header)

            # 检查 BMP 文件类型
            if file_header.bfType != 0x4D42:  # 'BM' in hex，确认文件是 BMP 格式
                raise ValueError("Not a BMP file")

            # 读取 BMP 信息头
            info_header = StructurePy.BITMAPINFOHEADER()
            f.readinto(info_header)
            h = info_header.biHeight
            w = info_header.biWidth
            c = info_header.biBitCount // 8
            # 移动文件指针到像素数组开始位置
            f.seek(file_header.bfOffBits)
            # 读取像素数据
            if info_header.biSizeImage:
                pixel_data = f.read(info_header.biSizeImage)
            else:
                new_line_size = (w * c + 3) & ~ 3
                pixel_data = f.read(h * new_line_size)
            return dxpyd.MiNiNumPy.bytes_bmp_to_arr3d(pixel_data, h, w, c, flip=1)

    @staticmethod
    def bitwise_and(img1,img2,mask):
        return dxpyd.MiNiNumPy.bitwise_and(img1,img2,mask)



