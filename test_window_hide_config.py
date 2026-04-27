# -*- coding: utf-8 -*-
"""
测试窗口隐藏/恢复功能的配置文件读取
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxGame.dx_config import ConfigHandler
from dxGame.dx_model import gl_info

def test_get_ports_from_config():
    """测试从配置文件读取端口号"""
    
    # 初始化配置
    config_path = os.path.join("资源", "配置", "主界面配置.ini")
    config = ConfigHandler(config_path)
    config.读取本地配置文件()
    
    # 设置全局配置对象
    gl_info.配置 = config
    
    print("=" * 60)
    print("测试：从配置文件读取账号配置的端口号")
    print("=" * 60)
    
    # 读取账号配置部分
    account_config = config.data.get('账号配置', {})
    
    if not account_config:
        print("❌ 账号配置为空")
        return False
    
    print(f"\n✓ 找到账号配置部分")
    print(f"  配置内容: {account_config}")
    
    # 提取所有端口号（即账号配置的键）
    ports = list(account_config.keys())
    
    print(f"\n✓ 提取到 {len(ports)} 个端口号:")
    for port in ports:
        print(f"  - {port}")
    
    # 验证期望的端口号
    expected_ports = ["5600", "5601"]
    
    print(f"\n期望的端口号: {expected_ports}")
    
    if set(ports) == set(expected_ports):
        print("✅ 测试通过：端口号匹配正确")
        return True
    else:
        print("❌ 测试失败：端口号不匹配")
        print(f"  期望: {expected_ports}")
        print(f"  实际: {ports}")
        return False

if __name__ == "__main__":
    success = test_get_ports_from_config()
    sys.exit(0 if success else 1)
