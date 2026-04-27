# -*- coding: utf-8 -*-
"""
从 AI/modules/vnc.py 复制过来的完整VNC模块
确保环境正确后可以直接使用
"""
import ctypes
import time
import logging
import sys

import cv2, numpy as np

from vncdotool import api
from vncdotool.client import KEYMAP

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示WARNING及以上级别的日志，屏蔽INFO和DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 单独设置vncdotool相关日志级别为WARNING，屏蔽其INFO级别的屏幕更新信息
vncdotool_logger = logging.getLogger('vncdotool')
vncdotool_logger.setLevel(logging.WARNING)
vncdotool_api_logger = logging.getLogger('vncdotool.api')
vncdotool_api_logger.setLevel(logging.WARNING)
vncdotool_client_logger = logging.getLogger('vncdotool.client')
vncdotool_client_logger.setLevel(logging.WARNING)


class VNC:
    button_left = 1
    button_mid = 2
    button_right = 3

    def __init__(self, ip, prot, password=None, timeout=30):
        # 处理空字符串密码，转换为None
        if password == "":
            password = None
        
        self.ip = ip + "::" + prot
        self.cmd = f"vncdo -s {self.ip} "
        print(f"正在连接到VNC服务器: {ip}:{prot}...")
        if password:
            print(f"使用密码连接（密码长度: {len(password)}）")
        else:
            print("无密码连接")
        try:
            self.client = api.connect(self.ip, password, timeout=timeout)
            print("VNC连接成功！")
            logging.info(f"成功连接到VNC服务器: {self.ip}")
        except Exception as e:
            print(f"❌ VNC连接失败: {e}")
            logging.error(f"VNC连接失败: {e}")
            raise
        
        self.key_map = KEYMAP
        self.image_size = 1440017  # 1024*768分辨率大小的
        self.image_buffer = (ctypes.c_ubyte * self.image_size)()
        
        # 等待连接稳定
        time.sleep(2)
        print("连接已稳定，可以开始使用")

    def __del__(self):
        self.stop()

    def stop(self):
        self.client.disconnect()

    # 截图,可以保存到本地，也可以直接获取cv图像对象
    def capture(self, path=None, max_retries=3, use_file_method=True):
        """
        截图方法
        use_file_method: 如果为True，优先使用captureScreen保存到临时文件的方式（更可靠）
        """
        if path:
            try:
                self.client.captureScreen(path)
                logging.debug(f"截图已保存到: {path}")
                return None
            except Exception as e:
                logging.error(f"保存截图失败: {e}")
                raise
        else:  # 不写入图像,直接转cv图像bgr格式
            # 策略1：优先使用captureScreen保存到临时文件（最可靠，避免refreshScreen超时）
            if use_file_method:
                import tempfile
                import os
                temp_file = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        temp_file = tmp.name
                    
                    logging.debug("使用captureScreen方法（临时文件）...")
                    logging.debug(f"正在调用captureScreen保存到: {temp_file}")
                    # 添加调试信息和超时处理
                    try:
                        self.client.captureScreen(temp_file)
                        logging.debug(f"captureScreen调用完成")
                    except Exception as e:
                        logging.debug(f"captureScreen调用失败: {e}")
                        raise
                    
                    # 等待文件写入完成，并检查文件是否存在和大小
                    max_wait_time = 3.0  # 最大等待3秒
                    wait_interval = 0.1  # 每0.1秒检查一次
                    waited_time = 0.0
                    file_size = -1  # 初始化为-1，确保第一次检查时不会匹配
                    stable_count = 0  # 文件大小稳定的次数
                    stable_threshold = 2  # 需要连续2次大小相同才认为写入完成
                    
                    while waited_time < max_wait_time:
                        if os.path.exists(temp_file):
                            current_size = os.path.getsize(temp_file)
                            # 如果文件大小大于0且稳定（连续多次检查大小相同），认为写入完成
                            if current_size > 0:
                                if current_size == file_size:
                                    stable_count += 1
                                    if stable_count >= stable_threshold:
                                        break
                                else:
                                    stable_count = 0  # 大小变化，重置稳定计数
                                file_size = current_size
                        time.sleep(wait_interval)
                        waited_time += wait_interval
                    
                    # 检查文件是否存在和大小是否合理
                    if not os.path.exists(temp_file):
                        raise ValueError(f"临时文件不存在: {temp_file}")
                    
                    final_size = os.path.getsize(temp_file)
                    if final_size == 0:
                        raise ValueError(f"临时文件为空: {temp_file}")
                    
                    if final_size < 100:  # PNG文件头至少需要一些字节
                        raise ValueError(f"临时文件大小异常（{final_size}字节）: {temp_file}")
                    
                    # 读取临时文件
                    logging.debug(f"正在读取临时文件: {temp_file} (大小: {final_size}字节)")
                    image = cv2.imread(temp_file)
                    if image is not None and image.size > 0:
                        logging.debug(f"成功通过临时文件获取图像，尺寸: {image.shape}")
                        # 清理临时文件
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                        return image
                    else:
                        raise ValueError(f"无法读取临时文件中的图像（文件大小: {final_size}字节）")
                except Exception as e:
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    # 如果文件方法失败，尝试使用refreshScreen方法
                    logging.warning(f"captureScreen方法失败，尝试refreshScreen方法: {e}")
                    if not use_file_method:
                        raise
            
            # 策略2：使用refreshScreen方法（可能超时，但速度更快）
            last_error = None
            for attempt in range(max_retries):
                try:
                    # 尝试刷新屏幕（使用全量刷新，更可靠）
                    incremental = 0 if attempt >= 1 else 1  # 第一次用增量，失败后用全量
                    logging.debug(f"尝试刷新屏幕 (增量={incremental}, 尝试={attempt + 1}/{max_retries})...")
                    
                    try:
                        self.client.refreshScreen(incremental)
                        # 等待屏幕数据更新（全量刷新需要更长时间）
                        wait_time = 2.0 if incremental == 0 else 1.0
                        wait_time += attempt * 0.5  # 每次重试增加等待时间
                        logging.debug(f"等待 {wait_time:.1f} 秒让屏幕数据更新...")
                        time.sleep(wait_time)
                    except Exception as e:
                        error_str = str(e).lower()
                        is_timeout = "timeout" in error_str or "timed out" in error_str
                        if is_timeout and attempt < max_retries - 1:
                            wait_time = 3.0 + attempt * 1.0
                            logging.warning(f"刷新屏幕超时，等待 {wait_time:.1f} 秒后重试...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise
                    
                    # 检查是否有屏幕数据
                    if not hasattr(self.client, 'screen') or self.client.screen is None:
                        if attempt < max_retries - 1:
                            logging.warning(f"屏幕数据为空，重试 {attempt + 1}/{max_retries}...")
                            time.sleep(1)
                            continue
                        else:
                            raise ValueError("无法获取屏幕数据")
                    
                    # 转换为BGR格式
                    screen_array = np.asarray(self.client.screen)
                    if screen_array.size == 0:
                        if attempt < max_retries - 1:
                            logging.warning(f"屏幕数据为空数组，重试 {attempt + 1}/{max_retries}...")
                            time.sleep(1)
                            continue
                        else:
                            raise ValueError("屏幕数据为空数组")
                    
                    logging.debug(f"成功通过refreshScreen获取图像，尺寸: {screen_array.shape}")
                    return cv2.cvtColor(screen_array, cv2.COLOR_RGB2BGR)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    is_timeout = "timeout" in error_str or "timed out" in error_str
                    
                    if attempt < max_retries - 1:
                        wait_time = 3.0 if is_timeout else 1.5
                        logging.warning(f"截图失败，{wait_time:.1f}秒后重试 ({attempt + 1}/{max_retries}): {str(e)[:100]}")
                        time.sleep(wait_time)
                    else:
                        logging.error(f"截图失败（已重试{max_retries}次）: {e}")
                        raise

    def capture_to_addr(self):
        self.flush_screen(1)
        image_bytes = np.asarray(self.client.screen).tobytes()
        ctypes.memmove(self.image_buffer, image_bytes, self.image_size)
        return ctypes.addressof(self.image_buffer), self.image_size

    # 移动鼠标
    def move(self, x, y):
        self.client.mouseMove(x, y)

    # 点击鼠标按钮,123分别对应左中右键
    def click(self, button=1, delay=0.05):
        self.client.mouseDown(button)
        time.sleep(delay)
        self.client.mouseUp(button)
        # self.flush_screen()

    # 移动并点击鼠标左键
    def left_click(self, x, y):
        self.move(x, y)
        self.click()
        self.flush_screen()

    # 双击鼠标左键
    def double_left_click(self, x, y):
        self.move(x, y)
        self.click()
        time.sleep(0.1)
        self.click()

    # 点击鼠标右键
    def right_click(self, x, y):
        self.move(x, y)
        self.click(3)

    # 拖动
    def drag(self, x, y, step=1):
        return self.client.mouseDrag(x, y, step)

    # 按键一次
    def key_press(self, key_str):
        # key_str可以参考 KEYMAP
        self.client.keyPress(key_str)
        self.flush_screen()

    # 刷新屏幕
    def flush_screen(self, incremental=1, max_retries=2):
        last_error = None
        for attempt in range(max_retries):
            try:
                result = self.client.refreshScreen(incremental)  # 屏幕更改时才刷新,节省宽带
                # 等待数据更新
                time.sleep(0.3)
                return result
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                is_timeout = "timeout" in error_str or "timed out" in error_str
                
                if attempt < max_retries - 1:
                    wait_time = 2.0 if is_timeout else 1.0
                    logging.warning(f"刷新屏幕失败，{wait_time}秒后重试 ({attempt + 1}/{max_retries}): {str(e)[:100]}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"刷新屏幕失败（已重试{max_retries}次）: {e}")
                    raise

    def key_down(self, key_str):
        return self.client.keyDown(key_str)

    def key_up(self, key_str):
        return self.client.keyUp(key_str)

    # 组合键
    def hot_key(self, key_list):
        for key_str in key_list:
            self.key_down(key_str)
            time.sleep(0.05)
        for key_str in key_list[::-1]:
            self.key_up(key_str)
            time.sleep(0.05)


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("VNC测试程序")
        print("=" * 60)
        
        # 简化的测试配置（不依赖外部配置文件）
        vnc_ip = "127.0.0.1"
        vnc_port = "5900"
        vnc_password = None
        
        # 可以从命令行参数获取
        if len(sys.argv) >= 2:
            vnc_ip = sys.argv[1]
        if len(sys.argv) >= 3:
            vnc_port = sys.argv[2]
        if len(sys.argv) >= 4:
            vnc_password = sys.argv[3] if sys.argv[3] else None
        
        # 创建VNC连接
        print(f"\n步骤1: 连接VNC服务器 {vnc_ip}:{vnc_port}...")
        if vnc_password:
            print(f"使用密码连接（密码长度: {len(vnc_password)}）")
        else:
            print("无密码连接")
        v = VNC(vnc_ip, vnc_port, vnc_password, timeout=60)
        
        # 测试截图功能
        print("\n步骤2: 测试截图功能...")
        try:
            test_image = v.capture(path=None)
            if test_image is not None:
                print(f"✅ 截图测试成功，图像尺寸: {test_image.shape}")
            else:
                print("❌ 截图返回None")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 截图测试失败: {e}")
            sys.exit(1)
        
        # 键盘测试（可选）
        print("\n步骤3: 测试键盘输入（按'a'键）...")
        try:
            v.key_press("a")
            print("✅ 键盘测试完成")
        except Exception as e:
            print(f"⚠️ 键盘测试失败: {e}")
        
        # 鼠标测试（可选）
        print("\n步骤4: 测试鼠标操作（移动到200,500并点击）...")
        try:
            v.move(200, 500)
            v.click(1)
            print("✅ 鼠标测试完成")
        except Exception as e:
            print(f"⚠️ 鼠标测试失败: {e}")
        
        # 截图循环测试
        print("\n步骤5: 开始截图循环测试（按'q'键退出）...")
        print("提示: 如果窗口没有显示，可能是截图失败或OpenCV窗口问题")
        
        FPS = 0
        frame_count = 0
        max_frames = 1000  # 限制最大帧数，避免无限循环
        
        while frame_count < max_frames:
            try:
                s = time.time()
                new_image = v.capture(path=None)  # 获取新图像
                
                if new_image is None:
                    print("❌ 截图返回None，退出循环")
                    break
                
                FPS = 1 / (time.time() - s)
                frame_count += 1
                
                # 绘制帧率
                cv2.putText(new_image, f"FPS: {int(FPS)}", (0, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(new_image, f"Frame: {frame_count}", (0, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                cv2.imshow("VNC Screen", new_image)
                
                # 按 'q' 键退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n用户按下'q'键，退出循环")
                    break
                    
            except KeyboardInterrupt:
                print("\n\n用户中断 (Ctrl+C)")
                break
            except Exception as e:
                print(f"\n❌ 截图循环中发生错误: {e}")
                logging.error(f"截图循环错误: {e}", exc_info=True)
                # 可以选择继续或退出
                response = input("是否继续? (y/n): ")
                if response.lower() != 'y':
                    break
                time.sleep(2)  # 等待后重试
        
        # 清理
        print("\n清理资源...")
        cv2.destroyAllWindows()
        v.stop()
        api.shutdown()  # 关闭事件循环
        print("✅ 程序正常退出")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序")
        try:
            v.stop()
            api.shutdown()
        except:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序发生错误: {e}")
        logging.error(f"程序错误: {e}", exc_info=True)
        try:
            v.stop()
            api.shutdown()
        except:
            pass
        sys.exit(1)

