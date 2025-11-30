#!/usr/bin/env python3
"""
综合示例脚本 - 文件处理与数据分析
演示：语法高亮、文件上传、实时日志

功能：
1. 接收上传的文件
2. 分析文件内容
3. 生成统计报告
4. 实时输出处理进度
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime


def print_banner():
    """打印横幅"""
    print("=" * 70)
    print("  📊 文件数据分析工具 v1.0")
    print("  🕒 执行时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    print()


def analyze_text_file(filepath):
    """分析文本文件"""
    print(f"\n📄 正在分析文件: {os.path.basename(filepath)}")
    print("-" * 70)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        non_empty_lines = sum(1 for line in lines if line.strip())
        total_chars = sum(len(line) for line in lines)
        total_words = sum(len(line.split()) for line in lines)

        print(f"  ✓ 总行数:         {total_lines:,}")
        print(f"  ✓ 非空行数:       {non_empty_lines:,}")
        print(f"  ✓ 总字符数:       {total_chars:,}")
        print(f"  ✓ 总单词数:       {total_words:,}")

        # 查找最长行
        if lines:
            longest_line = max(lines, key=len)
            print(f"  ✓ 最长行长度:     {len(longest_line)} 字符")

        # 文件大小
        file_size = os.path.getsize(filepath)
        print(f"  ✓ 文件大小:       {file_size:,} 字节 ({file_size/1024:.2f} KB)")

        return {
            'total_lines': total_lines,
            'non_empty_lines': non_empty_lines,
            'total_chars': total_chars,
            'total_words': total_words,
            'file_size': file_size
        }

    except UnicodeDecodeError:
        print("  ⚠️  警告: 非文本文件或编码不支持")
        return None
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None


def analyze_binary_file(filepath):
    """分析二进制文件"""
    print(f"\n🔍 二进制文件分析: {os.path.basename(filepath)}")
    print("-" * 70)

    try:
        import hashlib

        file_size = os.path.getsize(filepath)
        print(f"  ✓ 文件大小:       {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")

        # 计算MD5
        print("  🔄 计算 MD5 校验和...")
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        print(f"  ✓ MD5:            {md5.hexdigest()}")

        # 计算SHA256
        print("  🔄 计算 SHA256 校验和...")
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        print(f"  ✓ SHA256:         {sha256.hexdigest()}")

        return {
            'file_size': file_size,
            'md5': md5.hexdigest(),
            'sha256': sha256.hexdigest()
        }

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None


def process_file(filepath, analysis_type='auto'):
    """处理单个文件"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return None

    # 模拟处理延迟，展示实时日志
    time.sleep(0.3)

    if analysis_type == 'binary':
        return analyze_binary_file(filepath)
    else:
        # 尝试作为文本文件分析
        result = analyze_text_file(filepath)
        if result is None and analysis_type == 'auto':
            # 如果文本分析失败，尝试二进制分析
            result = analyze_binary_file(filepath)
        return result


def main():
    parser = argparse.ArgumentParser(
        description='文件数据分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python script.py --files '["file1.txt", "file2.csv"]'
  python script.py --files '["data.bin"]' --type binary
        """
    )

    parser.add_argument(
        '--files',
        type=str,
        help='上传的文件路径列表 (JSON 格式)'
    )

    parser.add_argument(
        '--type',
        type=str,
        choices=['auto', 'text', 'binary'],
        default='auto',
        help='分析类型: auto(自动), text(文本), binary(二进制)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出模式'
    )

    args = parser.parse_args()

    # 打印横幅
    print_banner()

    # 解析文件路径
    if not args.files:
        print("⚠️  未提供文件参数")
        print("\n使用方式:")
        print("  1. 在前端上传文件")
        print("  2. 系统会自动将文件路径作为参数传递")
        print("  3. 可选参数: --type [auto|text|binary]")
        return 1

    try:
        file_paths = json.loads(args.files)
    except json.JSONDecodeError:
        print("❌ 文件路径参数格式错误，应为 JSON 数组")
        return 1

    if not file_paths:
        print("⚠️  文件列表为空")
        return 1

    print(f"📦 接收到 {len(file_paths)} 个文件\n")

    # 处理每个文件
    results = []
    for i, filepath in enumerate(file_paths, 1):
        print(f"\n{'='*70}")
        print(f"  处理进度: [{i}/{len(file_paths)}]")
        print(f"{'='*70}")

        result = process_file(filepath, args.type)
        if result:
            results.append({
                'file': os.path.basename(filepath),
                'path': filepath,
                'result': result
            })

        # 进度条效果
        if i < len(file_paths):
            print("\n⏳ 准备处理下一个文件...")
            time.sleep(0.5)

    # 打印总结
    print("\n" + "=" * 70)
    print("  📋 处理总结")
    print("=" * 70)
    print(f"  ✓ 成功处理:       {len(results)}/{len(file_paths)} 个文件")

    if results:
        total_size = sum(r['result'].get('file_size', 0) for r in results)
        print(f"  ✓ 总数据量:       {total_size:,} 字节 ({total_size/1024/1024:.2f} MB)")

    print("\n✨ 处理完成！")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
