import os,sys
import platform

arch = platform.architecture()[0]
if arch == '64bit':
    __dll = "x64"
else:
    __dll = "x86"
if __dll == "x64":
    from dxGame.dx_lib.x64 import dxpyd
else:
    from dxGame.dx_lib.x86 import dxpyd
dx_core_path = os.path.join(os.path.dirname(__file__), __dll)
sys.path.append(dx_core_path)




