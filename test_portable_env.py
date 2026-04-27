# -*- coding: utf-8 -*-
"""
便携环境测试脚本
用于验证项目是否可以正确移植到其他电脑
"""
import os
import sys
import platform

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_python():
    """检查Python环境"""
    print_section("1. Python环境检查")
    
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"架构: {platform.architecture()}")
    print(f"平台: {platform.platform()}")
    
    # 检查版本是否符合要求
    if sys.version_info >= (3, 8) and sys.version_info < (3, 9):
        print("✓ Python版本符合要求 (3.8.x)")
        return True
    else:
        print(f"⚠ Python版本可能不兼容 (推荐3.8.x，当前{sys.version_info.major}.{sys.version_info.minor})")
        return True  # 警告但不失败

def check_dependencies():
    """检查依赖包"""
    print_section("2. 依赖包检查")
    
    required_packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'comtypes': 'comtypes',
        'vncdotool': 'vncdotool',
        'onnxruntime': 'onnxruntime',
        'win32api': 'pywin32',
        'pyperclip': 'pyperclip'
    }
    
    all_ok = True
    for module_name, package_name in required_packages.items():
        try:
            if module_name == 'PIL':
                from PIL import Image
                print(f"✓ {package_name:20s} 已安装")
            elif module_name == 'win32api':
                import win32api
                print(f"✓ {package_name:20s} 已安装")
            else:
                __import__(module_name)
                print(f"✓ {package_name:20s} 已安装")
        except ImportError:
            print(f"✗ {package_name:20s} 缺失")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """检查项目结构"""
    print_section("3. 项目结构检查")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"项目根目录: {project_root}")
    
    required_dirs = [
        'app',
        'dxGame',
        'task_list',
        '资源/图片',
        '资源/配置',
        '资源/日志'
    ]
    
    required_files = [
        'main.py',
        'public.py',
        'requirement.txt',
        'run.bat',
        'install_env.bat',
        'app/controller.py',
        'app/core.py',
        'app/view.py',
        'dxGame/dx_OnnxOCR.py',
        'dxGame/dx_vnc.py',
        'dxGame/dx_core.py',
    ]
    
    all_ok = True
    
    print("\n检查必需目录:")
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if os.path.isdir(full_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} (缺失)")
            all_ok = False
    
    print("\n检查必需文件:")
    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.isfile(full_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (缺失)")
            all_ok = False
    
    return all_ok

def check_onnxocr():
    """检查OnnxOCR配置"""
    print_section("4. OnnxOCR检查")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(project_root, 'OnnxOCR-main'),
        os.path.join(project_root, 'third_party', 'OnnxOCR-main'),
        os.path.join(project_root, 'OnnxOCR'),
    ]
    
    onnxocr_found = False
    onnxocr_path = None
    
    for path in possible_paths:
        if os.path.isdir(path):
            onnxocr_module = os.path.join(path, 'onnxocr', 'onnx_paddleocr.py')
            if os.path.isfile(onnxocr_module):
                print(f"✓ OnnxOCR找到: {path}")
                onnxocr_found = True
                onnxocr_path = path
                break
    
    if not onnxocr_found:
        print("✗ OnnxOCR未找到")
        print("  提示: 将OnnxOCR-main文件夹放到项目根目录")
        return False
    
    # 检查环境变量
    env_path = os.environ.get('ONNXOCR_PATH', '')
    if env_path:
        print(f"✓ ONNXOCR_PATH环境变量: {env_path}")
    else:
        print("ℹ ONNXOCR_PATH环境变量未设置 (run.bat会临时设置)")
    
    # 尝试导入
    try:
        saved_path = list(sys.path)
        if onnxocr_path not in sys.path:
            sys.path.insert(0, onnxocr_path)
        
        from onnxocr.onnx_paddleocr import ONNXPaddleOcr
        print("✓ onnxocr模块可以导入")
        
        sys.path[:] = saved_path
        return True
        
    except ImportError as e:
        print(f"✗ onnxocr模块导入失败: {e}")
        sys.path[:] = saved_path
        return False

def check_portable_python():
    """检查便携Python"""
    print_section("5. 便携Python检查")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    python_paths = [
        ('python\\python.exe', 'python'),
        ('Python38Portable\\python.exe', 'Python38Portable'),
        ('runtime\\python.exe', 'runtime'),
        ('.venv\\Scripts\\python.exe', '.venv'),
    ]
    
    found = False
    for rel_path, name in python_paths:
        full_path = os.path.join(project_root, rel_path)
        if os.path.isfile(full_path):
            print(f"✓ 便携Python找到: {name}\\")
            print(f"  路径: {full_path}")
            found = True
            
            # 检查是否是当前运行的Python
            if os.path.abspath(sys.executable) == os.path.abspath(full_path):
                print(f"  ✓ 当前正在使用此Python")
            else:
                print(f"  ℹ 当前使用的是其他Python: {sys.executable}")
            
            break
    
    if not found:
        print("✗ 未找到便携Python")
        print("  提示: 将Python放到以下任一目录:")
        print("    - python\\")
        print("    - Python38Portable\\")
        print("    - runtime\\")
        print("    - .venv\\")
        return False
    
    return True

def check_resource_files():
    """检查资源文件"""
    print_section("6. 资源文件检查")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 检查图片目录
    image_dir = os.path.join(project_root, '资源', '图片', 'Common')
    if os.path.isdir(image_dir):
        bmp_files = [f for f in os.listdir(image_dir) if f.endswith('.bmp')]
        print(f"✓ Common图片目录: {len(bmp_files)} 个BMP文件")
    else:
        print("✗ Common图片目录缺失")
        return False
    
    # 检查配置文件
    config_file = os.path.join(project_root, '资源', '配置', '主界面配置.ini')
    if os.path.isfile(config_file):
        print(f"✓ 配置文件存在")
    else:
        print("ℹ 配置文件不存在 (首次运行会自动创建)")
    
    return True

def main():
    """主函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "dx多开框架 - 便携环境测试" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    
    results = {}
    
    # 执行各项检查
    results['Python环境'] = check_python()
    results['依赖包'] = check_dependencies()
    results['项目结构'] = check_project_structure()
    results['OnnxOCR'] = check_onnxocr()
    results['便携Python'] = check_portable_python()
    results['资源文件'] = check_resource_files()
    
    # 汇总结果
    print_section("检查结果汇总")
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{check_name:15s} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("  🎉 所有检查通过！项目可以正常运行。")
        print("  现在可以双击 run.bat 启动程序。")
    else:
        print("  ⚠️ 部分检查未通过，请根据上述提示修复问题。")
        print("  可以运行 check_and_fix_env.bat 进行自动修复。")
    print("=" * 60)
    
    print("\n按任意键退出...")
    input()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n按任意键退出...")
        input()
