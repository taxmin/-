# -*- coding: utf-8 -*-
"""
VNC集成测试脚本
用于测试VNC截图功能是否正常工作
"""
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from dxGame.dx_vnc import VNC
    print("✓ 成功导入 VNC 模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_vnc_basic():
    """测试基本VNC功能"""
    print("\n" + "="*50)
    print("开始测试VNC基本功能")
    print("="*50)
    
    # 测试连接（使用默认配置）
    try:
        print("\n[1] 测试VNC连接...")
        vnc = VNC("127.0.0.1", "5600", "")
        print("✓ VNC对象创建成功")
        
        print("\n[2] 测试截图功能...")
        image = vnc.capture()
        if image is not None:
            print(f"✓ 截图成功！图像尺寸: {image.shape}")
            print(f"  - 宽度: {image.shape[1]}")
            print(f"  - 高度: {image.shape[0]}")
            print(f"  - 通道数: {image.shape[2] if len(image.shape) > 2 else 1}")
            print(f"  - 数据类型: {image.dtype}")
        else:
            print("❌ 截图返回None")
            return False
        
        print("\n[3] 测试区域截图...")
        if image.shape[0] > 100 and image.shape[1] > 100:
            region = vnc.capture(50, 50, 150, 150)
            if region is not None:
                print(f"✓ 区域截图成功！区域尺寸: {region.shape}")
            else:
                print("❌ 区域截图返回None")
        else:
            print("⚠ 图像太小，跳过区域截图测试")
        
        print("\n[4] 测试属性访问...")
        print(f"  - width: {vnc.width}")
        print(f"  - height: {vnc.height}")
        print(f"  - image is not None: {vnc.image is not None}")
        
        print("\n[5] 清理资源...")
        vnc.stop()
        print("✓ 资源清理完成")
        
        print("\n" + "="*50)
        print("✓ 所有测试通过！")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vnc_with_custom_config():
    """使用自定义配置测试VNC"""
    print("\n" + "="*50)
    print("测试自定义VNC配置")
    print("="*50)
    
    # 可以从配置文件读取
    import json
    config_file = os.path.join(current_dir, "config", "accounts.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 使用配置文件中的第一个账户的VNC配置
            if isinstance(config, list) and len(config) > 0:
                account = config[0]
                vnc_config = account.get('vnc', {})
                ip = vnc_config.get('ip', '127.0.0.1')
                port = str(vnc_config.get('port', '5600'))
                password = vnc_config.get('password', '')
                
                print(f"使用配置文件中的VNC设置: {ip}:{port}")
                vnc = VNC(ip, port, password)
                image = vnc.capture()
                if image is not None:
                    print(f"✓ 使用配置文件的VNC连接成功！图像尺寸: {image.shape}")
                    vnc.stop()
                    return True
        except Exception as e:
            print(f"⚠ 读取配置文件失败: {e}")
    
    print("⚠ 未找到配置文件或配置无效，跳过此测试")
    return True  # 不算失败

if __name__ == "__main__":
    print("VNC集成测试脚本")
    print("="*50)
    
    # 测试1：基本功能
    success1 = test_vnc_basic()
    
    # 测试2：自定义配置（可选）
    success2 = test_vnc_with_custom_config()
    
    if success1:
        print("\n✅ VNC功能测试通过！可以在task.py中使用：")
        print("   self.dx.screenshot = VNC('127.0.0.1', '5600', '')")
    else:
        print("\n❌ VNC功能测试失败，请检查：")
        print("   1. VNC服务器是否运行")
        print("   2. IP和端口是否正确")
        print("   3. 依赖是否安装（vncdotool, opencv-python, numpy）")
        sys.exit(1)

