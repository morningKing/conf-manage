#!/usr/bin/env python3
"""
测试中文文件名处理功能
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils import safe_filename


def test_safe_filename():
    """测试 safe_filename 函数"""

    test_cases = [
        # (输入, 预期输出描述)
        ('测试文件.txt', '测试文件.txt'),
        ('测试 文件.pdf', '测试 文件.pdf'),
        ('中文文档-2024.docx', '中文文档-2024.docx'),
        ('项目/报告.xlsx', '项目_报告.xlsx'),  # / 被替换为 _
        ('文件<名>.txt', '文件_名_.txt'),  # < > 被替换
        ('../../../etc/passwd', '.._.._.._etc_passwd'),  # 路径遍历攻击
        ('测试\0文件.txt', '测试_文件.txt'),  # 空字节
        ('', 'unnamed'),  # 空文件名
        ('   .txt', 'unnamed.txt'),  # 只有空格和扩展名
        ('很长的文件名' * 50 + '.txt', None),  # 超长文件名会被截断
    ]

    print("=" * 60)
    print("测试中文文件名处理功能")
    print("=" * 60)

    passed = 0
    failed = 0

    for i, (input_name, expected) in enumerate(test_cases, 1):
        result = safe_filename(input_name)

        # 对于超长文件名，只检查是否被截断
        if expected is None:
            success = len(result.encode('utf-8')) <= 255
            status = "✓" if success else "✗"
        else:
            success = result == expected
            status = "✓" if success else "✗"

        if success:
            passed += 1
        else:
            failed += 1

        print(f"\n测试 {i}: {status}")
        print(f"  输入:   {repr(input_name[:50])}")
        print(f"  输出:   {repr(result[:50])}")
        if expected:
            print(f"  预期:   {repr(expected[:50])}")
        print(f"  字节数: {len(result.encode('utf-8'))}")

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = test_safe_filename()
    sys.exit(0 if success else 1)
