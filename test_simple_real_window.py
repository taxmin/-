import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

from dxGame.dx_Window import Window

print("\n测试端口 5600:")
hwnd_5600 = Window.FindVMwareRealWindowByPort("5600")
print(f"结果: {hwnd_5600}\n")

print("\n测试端口 5601:")
hwnd_5601 = Window.FindVMwareRealWindowByPort("5601")
print(f"结果: {hwnd_5601}\n")

print(f"\n总结:")
print(f"5600 真实句柄: {hwnd_5600} (期望: 7737308)")
print(f"5601 真实句柄: {hwnd_5601} (期望: 201184)")
