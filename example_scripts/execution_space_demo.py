#!/usr/bin/env python3
"""
执行空间演示脚本
用于测试每次执行的独立空间隔离
"""
import os
import json
import argparse
from datetime import datetime

print("=" * 70)
print("  📦 执行空间隔离演示")
print("=" * 70)

# 获取当前工作目录
cwd = os.getcwd()
print(f"\n当前工作目录: {cwd}")
print(f"执行空间ID: {os.path.basename(cwd)}")

# 列出执行空间中的所有文件
print(f"\n📋 执行空间内容:")
files = os.listdir('.')
if files:
    for i, filename in enumerate(files, 1):
        file_path = os.path.join('.', filename)
        size = os.path.getsize(file_path)
        print(f"  [{i}] 📄 {filename} ({size} 字节)")
else:
    print("  (空)")

# 处理上传的文件
parser = argparse.ArgumentParser()
parser.add_argument('--files', type=str, help='上传的文件列表(JSON格式)')
args = parser.parse_args()

if args.files:
    file_list = json.loads(args.files)
    print(f"\n📤 处理上传的文件 (共 {len(file_list)} 个):")

    for i, filename in enumerate(file_list, 1):
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"\n[{i}] 📄 {filename}")
            print(f"    大小: {size} 字节")

            # 读取并显示文件内容前5行
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]
                    if lines:
                        print(f"    内容预览 (前{len(lines)}行):")
                        for line in lines:
                            print(f"      {line.rstrip()}")
            except:
                print("    (二进制文件或无法读取)")
else:
    print("\n📤 未上传文件")

# 创建一个输出文件
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_filename = f'output_{timestamp}.txt'

print(f"\n📝 创建输出文件: {output_filename}")
with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(f"执行时间: {datetime.now().isoformat()}\n")
    f.write(f"执行空间: {cwd}\n")
    f.write(f"执行空间ID: {os.path.basename(cwd)}\n")
    f.write("\n这是脚本执行生成的输出文件\n")
    f.write("每次执行都会在独立的执行空间中创建此文件\n")
    f.write("不同的执行互不影响\n")

print(f"✅ 文件已创建: {output_filename}")

# 创建子目录和文件
subdir = 'results'
os.makedirs(subdir, exist_ok=True)
print(f"\n📁 创建子目录: {subdir}/")

result_file = os.path.join(subdir, f'result_{timestamp}.json')
with open(result_file, 'w', encoding='utf-8') as f:
    json.dump({
        'execution_time': datetime.now().isoformat(),
        'workspace': cwd,
        'workspace_id': os.path.basename(cwd),
        'status': 'success',
        'message': '这是一个独立的执行空间'
    }, f, indent=2, ensure_ascii=False)

print(f"✅ 结果文件已创建: {result_file}")

# 再次列出执行空间中的所有文件
print(f"\n📋 执行后的执行空间内容:")
for root, dirs, files in os.walk('.'):
    level = root.replace('.', '').count(os.sep)
    indent = '  ' * level
    print(f"{indent}📁 {os.path.basename(root)}/")
    sub_indent = '  ' * (level + 1)
    for file in files:
        file_path = os.path.join(root, file)
        size = os.path.getsize(file_path)
        print(f"{sub_indent}📄 {file} ({size} 字节)")

print("\n" + "=" * 70)
print("✅ 执行完成!")
print("=" * 70)
print("\n💡 提示:")
print("   - 每次执行都有独立的执行空间")
print("   - 上传的文件只在当前执行空间可见")
print("   - 输出的文件保存在当前执行空间")
print("   - 多次执行同一脚本,各执行空间完全隔离")
print("=" * 70)
