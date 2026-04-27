# ONNX OCR 集成说明

## 📦 项目概述

已成功将企业级 **OnnxOCR** 引擎集成到当前多开框架中，命名为 `dx_OnnxOCR`。

### 核心优势

1. **高性能**：基于 ONNX Runtime，推理速度快
2. **多语言支持**：单模型支持简体中文、繁体中文、中文拼音、英文、日文
3. **高精度**：使用 PP-OCRv5 模型，精度与 PaddleOCR v3.0 一致
4. **跨平台**：支持 x86 和 ARM 架构
5. **脱离训练框架**：纯推理引擎，适合生产环境部署

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd E:\新建测试\OnnxOCR-main
pip install -r requirements.txt
```

**主要依赖：**
- `onnxruntime-directml==1.16.1` (支持 DirectX 11 GPU 加速)
- `opencv-python-headless==4.7.0.72`
- `opencv-contrib-python==4.7.0.72`
- `numpy<2.0.0`
- 其他依赖见 `requirements.txt`

### 2. 下载模型（可选）

- **Mobile 版本**：已存在于 `onnxocr/models/ppocrv5` 目录下
- **Server 版本**（推荐）：精度更高，需要单独下载
  - 百度网盘：https://pan.baidu.com/s/1hpENH_SkLDdwXkmlsX0GUQ?pwd=wu8t
  - 提取码：`wu8t`
  - 下载后将 `det` 和 `rec` 模型放到 `./models/ppocrv5/` 下替换

---

## 💡 使用方法

### 方式一：复用已有 VNC 实例（推荐）

```python
from dxGame.dx_OnnxOCR import ONNX_OCR

# 假设已有 VNC 截图实例
self.dx.screenshot = VNC("127.0.0.1", "5600", "", fps=5)

# 创建 ONNX OCR 实例（复用 VNC）
self.dx.Ocr = ONNX_OCR(vnc_instance=self.dx.screenshot, use_gpu=False, drop_score=0.5)

# 使用 OCR 识别
results = self.dx.Ocr.Ocr(100, 100, 500, 200)
for text, pos, confidence in results:
    print(f"文本：{text}, 位置：{pos}, 置信度：{confidence:.2f}")
```

### 方式二：独立创建 VNC 连接

```python
from dxGame.dx_OnnxOCR import ONNX_OCR

# 直接创建 ONNX OCR 实例（会自动创建 VNC 连接）
self.dx.Ocr = ONNX_OCR("127.0.0.1", "5600", "", use_gpu=False, drop_score=0.5)

# 使用 OCR 识别
results = self.dx.Ocr.Ocr(100, 100, 500, 200)
```

### 方式三：在任务脚本中使用

```python
def 设置 OCR 识别模式 ():
    # 复用已有的截图连接，避免重复连接 VNC 服务器
    from dxGame.dx_OnnxOCR import ONNX_OCR
    self.dx.Ocr = ONNX_OCR(vnc_instance=self.dx.screenshot, use_gpu=False)

def 测试 OCR 识别 ():
    # OCR 识别区域
    x1, y1, x2, y2 = 840, 75, 861, 95
    
    # 执行 OCR 识别
    results = self.dx.Ocr.Ocr(x1, y1, x2, y2)
    
    for i, (text, pos, confidence) in enumerate(results):
        show_log(self.row, f"结果{i+1}: {text} | 位置：{pos} | 置信度：{confidence:.2f}")
```

---

## 🔧 参数说明

### ONNX_OCR 类参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ip` | str | None | VNC 服务器 IP 地址 |
| `port` | str | None | VNC 服务器端口 |
| `password` | str | "" | VNC 密码 |
| `hwnd` | int | None | 窗口句柄（VNC 不需要） |
| `vnc_instance` | VNC | None | 已有的 VNC 实例（推荐提供） |
| `use_gpu` | bool | False | 是否使用 GPU 加速 |
| `drop_score` | float | 0.5 | 置信度阈值（0-1） |

### Ocr 方法参数

```python
def Ocr(self, x1: int, y1: int, x2: int, y2: int, target_text: str = None):
    """
    Args:
        x1, y1: 识别区域左上角坐标
        x2, y2: 识别区域右下角坐标
        target_text: 目标文本（可选），用于过滤结果
    
    Returns:
        list: [(text, position, confidence), ...]
              - text: 识别的文本
              - position: (center_x, center_y) 中心坐标
              - confidence: 置信度 (0-1)
    """
```

---

## 🎯 兼容 DX 接口的方法

为了保持与现有代码兼容，提供了以下方法：

```python
# 1. OCR 识别（返回详细结果）
results = self.dx.Ocr.Ocr(x1, y1, x2, y2)

# 2. 查找文本（返回布尔值）
found = self.dx.Ocr.FindText(x1, y1, x2, y2, target_text)

# 3. 获取文本位置（返回 1 或 0）
result = self.dx.Ocr.GetTextPos(x1, y1, x2, y2, target_text)
```

---

## 📊 性能对比

| 特性 | EasyOCR | Tesseract | **ONNX OCR** |
|------|---------|-----------|--------------|
| 中文支持 | ✓ | ✗ | ✓✓✓ |
| 英文支持 | ✓ | ✓✓ | ✓✓✓ |
| 识别速度 | 慢 | 快 | **很快** |
| 识别精度 | 中 | 中 | **高** |
| GPU 加速 | ✓ | ✗ | ✓ (DirectML) |
| 多语言 | 80+ | 100+ | 5 种精选 |
| 内存占用 | 高 | 低 | **中** |

---

## 🔍 测试验证

运行测试脚本验证功能：

```bash
python dxGame/dx_OnnxOCR.py
```

**测试内容：**
1. ✓ VNC 连接创建
2. ✓ ONNX OCR 引擎初始化
3. ✓ 模型预热
4. ✓ 区域 OCR 识别
5. ✓ 文本查找功能
6. ✓ 资源清理

---

## ⚠️ 注意事项

1. **路径配置**：
   - 确保 OnnxOCR 项目在 `E:\新建测试\OnnxOCR-main`
   - 如需修改路径，编辑 `dx_OnnxOCR.py` 第 13 行的 `_onnxocr_path`

2. **GPU 加速**：
   - 使用 `use_gpu=True` 需要 AMD GPU（支持 DirectML）
   - NVIDIA GPU 可安装 `onnxruntime-gpu`
   - CPU 模式也很快，推荐使用

3. **首次初始化**：
   - 第一次创建 OCR 实例会较慢（加载模型）
   - 后续使用会很快
   - 建议复用实例，不要频繁创建销毁

4. **置信度阈值**：
   - `drop_score=0.5` 表示过滤掉置信度低于 50% 的结果
   - 可根据实际需求调整（0.3-0.8）

---

## 🐛 常见问题

### Q1: 导入模块失败
```
❌ 导入 ONNX OCR 模块失败
```
**解决：**
- 检查路径是否正确
- 确保已安装依赖：`pip install -r requirements.txt`
- 确认模型文件存在：`onnxocr/models/ppocrv5/`

### Q2: OCR 识别结果为空
**可能原因：**
- 截图区域没有文字
- 置信度阈值设置过高
- 图片质量问题（模糊、反光等）

**解决：**
- 降低 `drop_score` 参数
- 检查截图是否正常
- 尝试调整识别区域

### Q3: GPU 加速无效
**检查：**
- AMD GPU 需安装：`onnxruntime-directml`
- NVIDIA GPU 需安装：`onnxruntime-gpu`
- 确认 GPU 驱动正常

---

## 📝 迁移指南

### 从 EasyOCR 迁移到 ONNX OCR

**原代码：**
```python
from dxGame.ocr import get_ocr_instance
ocr = get_ocr_instance(vnc_capture_func=...)
results = ocr.Ocr(x1, y1, x2, y2)
```

**新代码：**
```python
from dxGame.dx_OnnxOCR import ONNX_OCR
ocr = ONNX_OCR(vnc_instance=self.dx.screenshot)
results = ocr.Ocr(x1, y1, x2, y2)
```

**优势：**
- ✓ 更快的识别速度
- ✓ 更高的识别精度
- ✓ 更好的中文支持
- ✓ 更少的依赖问题

---

## 🎉 总结

✅ **已完成：**
1. 创建 `dx_OnnxOCR.py` 类，完美兼容现有 DX 接口
2. 支持复用 VNC 实例，避免重复连接
3. 提供 GPU 加速选项
4. 完整的错误处理和日志记录
5. 提供测试脚本和使用文档

✅ **优势：**
- 企业级 OCR 引擎，性能卓越
- 支持多种语言，精度高
- 与现有框架无缝集成
- 易于使用和扩展

🚀 **立即开始使用吧！**
