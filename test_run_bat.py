# -*- coding: utf-8 -*-
"""
测试 run.bat 是否能正常运行
"""
import sys
import os

print("=" * 60)
print("测试：run.bat 运行环境")
print("=" * 60)

# 检查Python路径
print(f"\n1. Python路径: {sys.executable}")
print(f"   Python版本: {sys.version}")

# 检查当前目录
print(f"\n2. 当前工作目录: {os.getcwd()}")

# 检查配置文件
config_path = os.path.join("资源", "配置", "主界面配置.ini")
if os.path.exists(config_path):
    print(f"\n3. ✅ 配置文件存在: {config_path}")
else:
    print(f"\n3. ❌ 配置文件不存在: {config_path}")

# 测试导入
try:
    from app.controller import Controller
    from app.view import Win
    from task_list.task import Task
    print("\n4. ✅ 所有模块导入成功")
except Exception as e:
    print(f"\n4. ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试配置读取
try:
    from dxGame.dx_config import ConfigHandler
    config = ConfigHandler(config_path)
    config.读取本地配置文件()
    
    account_config = config.data.get('账号配置', {})
    if account_config:
        ports = list(account_config.keys())
        print(f"\n5. ✅ 配置读取成功，端口号: {ports}")
    else:
        print("\n5. ⚠️  账号配置为空")
except Exception as e:
    print(f"\n5. ❌ 配置读取失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！环境正常，可以运行 run.bat")
print("=" * 60)
