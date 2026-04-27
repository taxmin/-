# -*- coding: utf-8 -*-
"""
OCR 环境诊断（与当前主流程一致）

主流程使用：dxGame/dx_OnnxOCR.py（ONNX + OnnxOCR 源码目录）
- pip: onnxruntime（见 requirement.txt）
- 源码: 设置环境变量 ONNXOCR_PATH，或将 OnnxOCR 放到项目约定子目录
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))


def _resolve_onnxocr_root():
    """与 dx_OnnxOCR._resolve_onnxocr_root 逻辑一致，避免导入 dxGame 链。"""
    env = os.environ.get("ONNXOCR_PATH", "").strip()
    if env:
        return env
    for rel in (("OnnxOCR-main",), ("third_party", "OnnxOCR-main"), ("OnnxOCR",)):
        p = os.path.join(_ROOT, *rel)
        if os.path.isdir(p):
            return p
    # 未找到时返回项目目录下的默认路径
    return os.path.join(_ROOT, "OnnxOCR-main")


def _try_import_onnxocr(onnxocr_root: str) -> tuple:
    """
    尝试导入 onnxocr.onnx_paddleocr.ONNXPaddleOcr
    返回 (成功, 错误信息)
    """
    saved_path = list(sys.path)
    try:
        if os.path.isdir(onnxocr_root) and onnxocr_root not in sys.path:
            sys.path.insert(0, onnxocr_root)
        try:
            from onnxocr.onnx_paddleocr import ONNXPaddleOcr  # noqa: F401
            return True, None
        except ImportError as e1:
            sub = os.path.join(onnxocr_root, "onnxocr")
            if os.path.isdir(sub) and sub not in sys.path:
                sys.path.insert(0, sub)
            from onnxocr.onnx_paddleocr import ONNXPaddleOcr  # noqa: F401
            return True, None
    except Exception as e:
        return False, str(e)
    finally:
        sys.path[:] = saved_path


def main():
    print("=" * 60)
    print("OCR 环境诊断（主用 ONNX / OnnxOCR）")
    print("=" * 60)
    print()

    py = sys.version_info
    print(f"Python: {py.major}.{py.minor}.{py.micro}")
    if py < (3, 8):
        print("  警告: 版本过低，本项目推荐 Python 3.8.x")
    elif py >= (3, 13):
        print("  注意: 未在 3.13+ 上充分验证，若异常请改用 3.8–3.11")
    else:
        print("  版本可用于本项目（推荐 3.8.8）")
    print()

    # ---------- 主路径：onnxruntime ----------
    print("1) onnxruntime（ONNX 推理）")
    try:
        import onnxruntime as ort
        print(f"   已安装: {ort.__version__}")
    except ImportError:
        print("   未安装")
        print("   安装: python -m pip install \"onnxruntime>=1.16.0,<2.0.0\"")
    except Exception as e:
        print(f"   导入异常: {e}")
    print()

    # ---------- 主路径：OnnxOCR 源码 ----------
    root = _resolve_onnxocr_root()
    print("2) OnnxOCR 源码目录")
    print(f"   解析结果: {root}")
    env_set = bool(os.environ.get("ONNXOCR_PATH", "").strip())
    print(f"   ONNXOCR_PATH 已设置: {'是' if env_set else '否（使用项目内路径或默认）'}")
    if not os.path.isdir(root):
        print("   状态: 目录不存在 — 主流程 OCR 将无法加载")
        print("   处理: 克隆/解压 OnnxOCR 到上述路径，或设置 ONNXOCR_PATH")
    else:
        print("   状态: 目录存在")
        pkg = os.path.join(root, "onnxocr")
        req = os.path.join(root, "requirements.txt")
        if not os.path.isdir(pkg):
            print("   警告: 未找到 onnxocr 子目录，可能不是有效 OnnxOCR 根目录")
        if os.path.isfile(req):
            print(f"   提示: 若导入失败可执行: python -m pip install -r \"{req}\"")
    print()

    print("3) 尝试导入 onnxocr.onnx_paddleocr（不初始化模型、不连 VNC）")
    if os.path.isdir(root):
        ok, err = _try_import_onnxocr(root)
        if ok:
            print("   成功: 可 import ONNXPaddleOcr")
        else:
            print(f"   失败: {err}")
            print("   请确认 OnnxOCR 版本含 onnxocr/onnx_paddleocr.py，并安装其 requirements.txt")
    else:
        print("   跳过（目录不存在）")
    print()

    # ---------- 与图色脚本相关的包 ----------
    print("4) 图像栈（找图/OCR 截图依赖）")
    for name, mod in (("numpy", "numpy"), ("cv2", "opencv-python")):
        try:
            m = __import__(name)
            ver = getattr(m, "__version__", "?")
            print(f"   {mod}: 已安装 ({ver})")
        except ImportError:
            print(f"   {mod}: 未安装")
    print()

    # ---------- 可选备用（requirement.txt 仍列了） ----------
    print("5) 可选备用 OCR（非主流程）")
    for label, modname in (("pytesseract", "pytesseract"), ("easyocr", "easyocr")):
        try:
            __import__(modname)
            print(f"   {label}: 已安装")
        except ImportError:
            print(f"   {label}: 未安装（可忽略，若不用该引擎）")
    print()

    print("=" * 60)
    print("结论")
    print("=" * 60)
    try:
        import onnxruntime  # noqa: F401
        ort_ok = True
    except Exception:
        ort_ok = False
    onnxocr_ok = os.path.isdir(root) and _try_import_onnxocr(root)[0]
    if ort_ok and onnxocr_ok:
        print("主用 ONNX OCR 环境就绪（onnxruntime + onnxocr 可导入）。")
    else:
        if not ort_ok:
            print("- 请安装 onnxruntime（见 requirement.txt / install_env.bat）")
        if not os.path.isdir(root):
            print("- 请准备 OnnxOCR 源码并设置 ONNXOCR_PATH 或放入项目子目录")
        elif not onnxocr_ok:
            print("- OnnxOCR 目录存在但 onnxocr 导入失败，请按其 requirements 补依赖")
    print("=" * 60)


if __name__ == "__main__":
    main()
