import struct  # 用于处理二进制数据的打包和解包
import zlib  # 用于数据压缩和解压缩
import array  # 提供高效的数组操作
import itertools  # 提供迭代器工具
import io  # 提供内存文件操作

class Png:
    """
        用于读取和写入 PNG 图像的类，支持 RGB 和 BGR 格式的转换。
        """
    @staticmethod
    def read(path):
        """
        读取 PNG 文件，并将其转为 RGB 或 BGR 字节格式。
        :param path: PNG 文件路径
        :return: (width, height, rgb_bytes)
        """
        reader = Png.Reader(filename=path)
        width, height, rows = reader.asRGB8()
        rgb_bytes = bytearray()
        for row in rows:
            rgb_bytes.extend(row)
        return width, height, rgb_bytes

    @staticmethod
    def write(rgb_bytes, width, height, path):
        """
        将 RGB 或 BGR 字节数据写入 PNG 文件。
        :param rgb_bytes: 图像的 RGB 字节数据
        :param width: 图像宽度
        :param height: 图像高度
        :param path: PNG 文件保存路径
        """
        with open(path, 'wb') as f:
            writer = Png.Writer(width, height, greyscale=False, bitdepth=8)
            # 将 rgb_bytes 分成行并写入文件
            rows = (rgb_bytes[i:i+width*3] for i in range(0, len(rgb_bytes), width*3))
            writer.write(f, rows)

    @staticmethod
    def bytes_to_rgb(png_bytes):
        """
        接受 PNG 文件的二进制数据，并将其转为 RGB 或 BGR 字节格式。
        :param png_bytes: PNG 文件的二进制数据
        :return: (width, height, rgb_bytes)
        """
        reader = Png.Reader(bytes=png_bytes)
        width, height, rows, info = reader.asRGB8()
        rgb_bytes = bytearray()
        for row in rows:
            rgb_bytes.extend(row)
        return width, height, rgb_bytes

    class Reader:
        def __init__(self, _guess=None, filename=None, file=None, bytes=None):
            self.signature = None
            self.atchunk = None
            self.file = None
            if filename:
                self.file = open(filename, "rb")
            elif bytes:
                self.file = io.BytesIO(bytes)
            else:
                raise TypeError("Reader() expects either filename or bytes.")
            self.width = None
            self.height = None
            self.bitdepth = None
            self.color_type = None
            self.planes = None
            self.psize = None

        def chunk(self):
            if not self.signature:
                self.signature = self.file.read(8)
                if self.signature != struct.pack('8B', 137, 80, 78, 71, 13, 10, 26, 10):
                    raise ValueError("Not a PNG file")
            length, chunk_type = struct.unpack("!I4s", self.file.read(8))
            data = self.file.read(length)
            crc = self.file.read(4)
            return chunk_type, data

        def read(self):
            idat_data = b''
            while True:
                chunk_type, data = self.chunk()
                if chunk_type == b'IHDR':
                    self.width, self.height, self.bitdepth, self.color_type, _, _, _ = struct.unpack("!2I5B", data)
                    self.planes = 3 if self.color_type == 2 else 1
                    self.psize = self.bitdepth // 8 * self.planes
                elif chunk_type == b'IDAT':
                    # 收集所有 IDAT 块的数据
                    idat_data += data
                elif chunk_type == b'IEND':
                    # 解压缩所有的 IDAT 数据
                    decompressed = zlib.decompress(idat_data)
                    return self._parse_pixels(decompressed)
                elif chunk_type == b'PLTE':
                    # 如果有调色板，需要处理调色板数据（可选）
                    pass

        def _parse_pixels(self, raw_data):
            pixel_data = []
            idx = 0
            for _ in range(self.height):
                idx += 1  # Skip filter type byte
                row = array.array('B', raw_data[idx:idx + self.width * self.planes])
                pixel_data.append(row)
                idx += self.width * self.planes
            return pixel_data

        def asRGB8(self):
            rows = self.read()
            rgb_rows = [bytearray(itertools.chain(*rows))]
            for row in rows:
                # 每一行应该有 width * 3 个字节（R, G, B 3 通道）
                # 如果数据是灰度图或者其他类型，应该做转换
                rgb_row = bytearray()
                for i in range(self.width):
                    pixel = row[i * self.planes: (i + 1) * self.planes]  # 提取每个像素的字节
                    if len(pixel) == 1:  # 如果是灰度图
                        # 灰度图只包含一个通道，复制到 R, G, B 三个通道
                        rgb_row.extend(pixel * 3)
                    else:
                        rgb_row.extend(pixel[:3])  # 如果是 RGB, 直接使用
                rgb_rows.append(rgb_row)

            return self.width, self.height, rgb_rows

    class Writer:
        def __init__(self, width, height, greyscale=False, bitdepth=8):
            self.width = width
            self.height = height
            self.greyscale = greyscale
            self.bitdepth = bitdepth

        def write(self, outfile, rows):
            outfile.write(struct.pack("!8B", 137, 80, 78, 71, 13, 10, 26, 10))  # PNG signature
            ihdr = struct.pack("!2I5B", self.width, self.height, self.bitdepth, 2, 0, 0, 0)
            outfile.write(struct.pack("!I", len(ihdr)))
            outfile.write(b'IHDR' + ihdr + struct.pack("!I", zlib.crc32(b'IHDR' + ihdr)))

            compressor = zlib.compressobj()
            idat_data = b""
            for row in rows:
                idat_data += compressor.compress(b'\x00' + row)
            idat_data += compressor.flush()
            outfile.write(struct.pack("!I", len(idat_data)))
            outfile.write(b'IDAT' + idat_data + struct.pack("!I", zlib.crc32(b'IDAT' + idat_data)))

            outfile.write(struct.pack("!I", 0) + b'IEND' + struct.pack("!I", zlib.crc32(b'IEND')))


if __name__ == '__main__':
    png_path = r"D:\code\python\C_API\dxGame\dxpyd测试编译\test2.png"
    width, height, bytes_rgb = Png.read(png_path)
    from dxGame import MiniOpenCV,dxpyd
    img = dxpyd.MiNiNumPy.bytes_to_arr3d(bytes(bytes_rgb), height, width, 3)
    # MiniOpenCV.imshow("img",img)
    # MiniOpenCV.waitKey(0)
    import numpy as np,cv2
    np_array = np.asarray(img)
    cv2.imshow("img",np_array)
    cv2.waitKey(0)
    print(f"Width: {width}, Height: {height}, RGB Bytes Length: {len(bytes_rgb)}")
