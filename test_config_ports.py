# -*- coding: utf-8 -*-
"""
简单测试：验证配置文件中的端口号
"""
import ast

def read_config_simple():
    """简单读取配置文件"""
    config_path = r"F:\taxmin\dx多开框架\资源\配置\主界面配置.ini"
    
    print("=" * 60)
    print("测试：从配置文件读取账号配置的端口号")
    print("=" * 60)
    
    # 手动解析INI文件
    account_config = {}
    current_section = None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 检查是否是section
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                account_config[current_section] = {}
                continue
            
            # 检查是否是键值对
            if '=' in line and current_section:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 尝试解析Python字面量
                try:
                    value = ast.literal_eval(value)
                except:
                    pass
                
                account_config[current_section][key] = value
    
    # 获取账号配置部分
    if '账号配置' not in account_config:
        print("❌ 未找到[账号配置]部分")
        return False
    
    account_section = account_config['账号配置']
    
    if not account_section:
        print("❌ 账号配置为空")
        return False
    
    print(f"\n✓ 找到账号配置部分")
    print(f"  配置内容:")
    for port, accounts in account_section.items():
        print(f"    {port}: {len(accounts)} 个账号")
    
    # 提取所有端口号（即账号配置的键）
    ports = list(account_section.keys())
    
    print(f"\n✓ 提取到 {len(ports)} 个端口号:")
    for port in ports:
        print(f"  - {port}")
    
    # 验证期望的端口号
    expected_ports = ["5600", "5601"]
    
    print(f"\n期望的端口号: {expected_ports}")
    
    if set(ports) == set(expected_ports):
        print("✅ 测试通过：端口号匹配正确")
        
        # 测试窗口标题格式
        print("\n" + "=" * 60)
        print("窗口标题格式测试:")
        print("=" * 60)
        for port in ports:
            window_title = f"{port} - VMware Workstation"
            print(f"  端口 {port} 的窗口标题应该是: '{window_title}'")
        
        return True
    else:
        print("❌ 测试失败：端口号不匹配")
        print(f"  期望: {expected_ports}")
        print(f"  实际: {ports}")
        return False

if __name__ == "__main__":
    import sys
    success = read_config_simple()
    sys.exit(0 if success else 1)
