# -*- coding: utf-8 -*-
"""
系统状态检查工具
用于检查 VNC、OCR 等组件的运行状态
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxGame.dx_vnc import VNC
from dxGame.dx_OnnxOCR import ONNX_OCR


def check_vnc_status(ip="127.0.0.1", port="5600", password=""):
    """
    检查 VNC 状态
    
    Args:
        ip: VNC IP 地址
        port: VNC 端口
        password: VNC 密码
    
    Returns:
        dict: VNC 状态信息
    """
    print("\n" + "="*60)
    print("VNC 状态检查")
    print("="*60)
    
    try:
        # 创建 VNC 实例
        vnc = VNC(ip, port, password, fps=5)
        
        # 获取状态
        status = vnc.get_status()
        
        # 打印状态
        vnc.print_status()
        
        # 判断是否正常
        if status['status'] == 'healthy':
            print("\n✅ VNC 状态正常")
            result = True
        else:
            print(f"\n⚠️ VNC 状态异常：{status['status']}")
            result = False
        
        # 清理资源
        vnc.stop()
        return result
        
    except Exception as e:
        print(f"\n❌ VNC 检查失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def check_ocr_status():
    """
    检查 OCR 状态（需要先有 VNC 连接）
    
    Returns:
        bool: OCR 是否正常
    """
    print("\n" + "="*60)
    print("ONNX OCR 状态检查")
    print("="*60)
    
    try:
        # 先创建 VNC
        vnc = VNC("127.0.0.1", "5600", "", fps=5)
        
        # 再创建 OCR
        ocr = ONNX_OCR(vnc_instance=vnc, use_gpu=False)
        
        # 获取统计信息
        stats = ocr.get_stats()
        
        # 打印统计信息
        ocr.print_stats()
        
        # 判断是否正常
        if stats['engine_status'] in ['healthy', 'unknown']:
            print("\n✅ OCR 引擎状态正常")
            result = True
        elif stats['engine_status'] == 'degraded':
            print(f"\n⚠️ OCR 性能下降：成功率 {stats['success_rate']}")
            result = False
        else:
            print(f"\n❌ OCR 引擎状态：{stats['engine_status']}")
            result = False
        
        # 清理资源
        ocr.stop()
        vnc.stop()
        return result
        
    except Exception as e:
        print(f"\n❌ OCR 检查失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def check_all():
    """
    检查所有组件状态
    
    Returns:
        bool: 是否全部正常
    """
    print("\n" + "="*60)
    print("系统状态全面检查")
    print("="*60)
    
    results = {}
    
    # 检查 VNC
    print("\n[1/2] 检查 VNC...")
    results['vnc'] = check_vnc_status()
    
    # 检查 OCR
    print("\n[2/2] 检查 OCR...")
    results['ocr'] = check_ocr_status()
    
    # 总结
    print("\n" + "="*60)
    print("检查结果总结")
    print("="*60)
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {component.upper()}: {'正常' if status else '异常'}")
    print("="*60)
    
    all_ok = all(results.values())
    if all_ok:
        print("\n🎉 所有组件状态正常！")
    else:
        print("\n⚠️ 部分组件存在异常，请检查日志")
    
    return all_ok


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='系统状态检查工具')
    parser.add_argument('--component', '-c', 
                       choices=['all', 'vnc', 'ocr'],
                       default='all',
                       help='要检查的组件 (默认: all)')
    
    args = parser.parse_args()
    
    if args.component == 'all':
        check_all()
    elif args.component == 'vnc':
        check_vnc_status()
    elif args.component == 'ocr':
        check_ocr_status()
