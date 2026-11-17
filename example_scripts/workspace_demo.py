#!/usr/bin/env python3
"""
工作目录演示脚本
演示每个脚本都有自己独立的工作目录

功能：
1. 显示当前工作目录
2. 列出工作目录中的所有文件
3. 处理上传的文件（文件已在工作目录中）
4. 在工作目录中创建新文件
5. 读写文件都在工作目录中进行
"""

import argparse
import json
import os
import sys
from datetime import datetime


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def show_workspace_info():
    """显示工作目录信息"""
    print_section("📁 工作目录信息")

    # 当前工作目录
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")

    # 工作目录的绝对路径
    abs_path = os.path.abspath(cwd)
    print(f"绝对路径:     {abs_path}")

    # 工作目录的父目录
    parent_dir = os.path.dirname(abs_path)
    print(f"父目录:       {parent_dir}")

    # 列出工作目录中的所有文件
    print("\n📋 工作目录内容:")
    files = os.listdir(cwd)
    if files:
        for i, filename in enumerate(sorted(files), 1):
            filepath = os.path.join(cwd, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                print(f"  [{i}] 📄 {filename} ({size} 字节)")
            elif os.path.isdir(filepath):
                print(f"  [{i}] 📁 {filename}/")
    else:
        print("  (空目录)")


def process_uploaded_files(file_names):
    """处理上传的文件（已在工作目录中）"""
    print_section("📤 处理上传的文件")

    if not file_names:
        print("⚠️  没有上传的文件")
        return

    print(f"接收到 {len(file_names)} 个文件:\n")

    for i, raw_name in enumerate(file_names, 1):
        # 文件已在当前工作目录中，只使用文件名部分，防止路径穿越
        filename = os.path.basename(raw_name)
        if not os.path.exists(filename):
            print(f"[{i}] ❌ 文件不存在: {filename}")
            continue

        print(f"[{i}] 📄 {filename}")

        # 获取文件信息
        file_size = os.path.getsize(filename)
        print(f"    大小: {file_size} 字节")

        # 尝试读取文本文件的前几行
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:3]  # 只读前3行
                print(f"    内容预览 (前3行):")
                for line in lines:
                    print(f"      {line.rstrip()}")
        except UnicodeDecodeError:
            print(f"    (二进制文件)")
        except Exception as e:
            print(f"    读取失败: {e}")

        print()


def create_output_file():
    """在工作目录中创建输出文件"""
    print_section("✍️  创建输出文件")

    # 在当前工作目录创建文件
    output_filename = os.path.basename(f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    content = f"""脚本执行报告
=============

执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
工作目录: {os.getcwd()}

系统信息:
- Python版本: {sys.version}
- 平台: {sys.platform}

工作目录文件列表:
"""

    # 添加文件列表
    for filename in sorted(os.listdir('.')):
        filepath = os.path.join('.', filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            content += f"  - {filename} ({size} 字节)\n"

    # 写入文件
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已创建输出文件: {output_filename}")
    print(f"   文件路径: {os.path.abspath(output_filename)}")
    print(f"   文件大小: {os.path.getsize(output_filename)} 字节")


def demonstrate_file_operations():
    """演示文件操作"""
    print_section("🔧 文件操作演示")

    # 创建一个测试文件
    print("1. 创建测试文件: test_data.txt")
    with open("test_data.txt", 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件\n")
        f.write("用于演示工作目录功能\n")
        f.write("所有文件操作都在独立的工作目录中进行\n")

    # 读取文件
    print(f"\n2. 读取测试文件:")
    with open("test_data.txt", 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"   内容: {content.strip()}")

    # 追加内容
    print(f"\n3. 追加内容到文件:")
    with open("test_data.txt", 'a', encoding='utf-8') as f:
        f.write(f"追加时间: {datetime.now()}\n")

    # 检查文件
    print(f"\n4. 文件信息:")
    print(f"   存在: {os.path.exists('test_data.txt')}")
    print(f"   大小: {os.path.getsize('test_data.txt')} 字节")
    print(f"   绝对路径: {os.path.abspath('test_data.txt')}")


def main():
    parser = argparse.ArgumentParser(description='工作目录演示脚本')
    parser.add_argument('--files', type=str, help='上传的文件名列表 (JSON格式)')
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  🚀 工作目录演示脚本")
    print("=" * 70)

    # 1. 显示工作目录信息
    show_workspace_info()

    # 2. 处理上传的文件
    if args.files:
        try:
            file_names = json.loads(args.files)
            process_uploaded_files(file_names)
        except json.JSONDecodeError:
            print("\n❌ 文件参数格式错误")

    # 3. 演示文件操作
    demonstrate_file_operations()

    # 4. 创建输出文件
    create_output_file()

    # 5. 最后再显示一次工作目录内容
    print_section("📋 最终工作目录内容")
    files = sorted(os.listdir('.'))
    print(f"工作目录中共有 {len(files)} 个文件/目录:\n")
    for i, filename in enumerate(files, 1):
        filepath = os.path.join('.', filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            print(f"  [{i}] 📄 {filename} ({size} 字节)")
        elif os.path.isdir(filepath):
            print(f"  [{i}] 📁 {filename}/")

    print("\n" + "=" * 70)
    print("  ✨ 演示完成！")
    print("  💡 提示: 所有文件都保存在此脚本的独立工作目录中")
    print("=" * 70 + "\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
