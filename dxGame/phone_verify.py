# -*- coding: utf-8 -*-
"""
手机号验证辅助函数
支持 **** 分隔符的模糊匹配
"""


def verify_phone_number(ocr_text: str, account: str) -> tuple:
    """
    验证 OCR 识别的手机号是否与账号匹配
    
    Args:
        ocr_text: OCR 识别的文本，如 "184****117" 或 "18411231117"
        account: 完整账号，如 "18411231117"
    
    Returns:
        (bool, str, str): (是否匹配，前缀，后缀)
    """
    if len(ocr_text) < 3 or len(account) < 3:
        return False, "", ""
    
    # 尝试以 **** 为分隔符分割
    if '****' in ocr_text:
        parts = ocr_text.split('****')
        ocr_prefix = parts[0]  # 前三位，如 "184"
        ocr_suffix = parts[1] if len(parts) > 1 else ''  # 后几位，如 "117"
    else:
        # 没有分隔符时：取前三位 + OCR 可见后缀（最多后四位）
        ocr_prefix = ocr_text[:3]
        ocr_suffix = ocr_text[-4:] if len(ocr_text) >= 4 else ''
    
    # 账号基准：前三位 + 固定后四位（如 18802051824 -> 后缀 1824）
    account_prefix = account[:3]
    account_suffix = account[-4:] if len(account) >= 4 else account
    
    # 验证逻辑：
    # 1. 前三位必须相等
    # 2. OCR 后缀与账号后四位比较：可精确匹配，也可按相似度模糊匹配
    prefix_match = (ocr_prefix == account_prefix)
    suffix_match = False
    
    if ocr_suffix and account_suffix:
        # 严格模式：OCR 后缀必须完全匹配账号后缀
        exact_match = (ocr_suffix == account_suffix)
        
        # 模糊匹配：检查相似度（允许 1-2 个字符的识别错误）
        if len(ocr_suffix) >= 3 and len(account_suffix) >= 3:
            # 计算有多少个字符相同且位置相近
            common_chars = sum(1 for c in ocr_suffix if c in account_suffix)
            char_match_rate = common_chars / max(len(ocr_suffix), len(account_suffix))
            
            # 长度差异不能太大
            length_diff = abs(len(ocr_suffix) - len(account_suffix))
            
            # 如果字符匹配率高且长度接近，则认为匹配（容错 1 个字符）
            fuzzy_match = (char_match_rate >= 0.75 and length_diff <= 1)
        else:
            fuzzy_match = False
        
        # 宽松模式：只有当前缀完全匹配且后缀有较高相似度时才成功
        suffix_match = exact_match or fuzzy_match
        
    elif not ocr_suffix:
        # 没有后缀，只要前缀匹配就算成功
        suffix_match = True
    
    # 特殊情况：如果 OCR 只识别出 3 位数字，且这 3 位就是前三位
    if len(ocr_text) == 3 and ocr_text == account_prefix:
        prefix_match = True
        suffix_match = True
    
    return prefix_match and suffix_match, ocr_prefix, ocr_suffix


if __name__ == '__main__':
    # 测试用例
    test_cases = [
        ("184****117", "18411231117", True),  # 标准情况
        ("184****1117", "18411231117", True),  # 后缀 4 位
        ("18411231117", "18411231117", True),  # 无分隔符，完全匹配
        ("184", "18411231117", True),  # 只有前三位
        ("184****", "18411231117", True),  # 有分隔符但无后缀
        ("183****117", "18411231117", False),  # 前缀不匹配
        ("184****118", "18411231117", False),  # 后缀不匹配
    ]
    
    print("手机号验证测试")
    print("=" * 60)
    for ocr_text, account, expected in test_cases:
        result, prefix, suffix = verify_phone_number(ocr_text, account)
        status = "Y" if result == expected else "X"
        print(f"{status} OCR: {ocr_text:15s} Account: {account:15s} Result: {str(result):5s} (Prefix:{prefix}, Suffix:{suffix})")
