#!/usr/bin/env python3
"""
示例脚本：文件处理器
演示如何接收上传的文件并处理

使用方式：
1. 在前端上传一个或多个文件
2. 脚本会接收文件路径并处理
"""

import argparse
import json
import time
import os

def main():
    parser = argparse.ArgumentParser(description='文件处理器')
    parser.add_argument('--files', type=str, help='上传的文件路径列表(JSON格式)')
    parser.add_argument('--action', type=str, default='info', help='执行的操作: info, count, checksum')

    args = parser.parse_args()

    print("=" * 60)
    print("文件处理器启动")
    print("=" * 60)

    # 解析文件路径
    if args.files:
        file_paths = json.loads(args.files)
        print(f"\n接收到 {len(file_paths)} 个文件:")

        for i, filepath in enumerate(file_paths, 1):
            print(f"\n[{i}] 处理文件: {os.path.basename(filepath)}")
            print(f"    完整路径: {filepath}")

            if not os.path.exists(filepath):
                print(f"    ⚠️  警告: 文件不存在!")
                continue

            # 获取文件信息
            file_size = os.path.getsize(filepath)
            print(f"    文件大小: {file_size} 字节")

            # 根据action执行不同操作
            if args.action == 'info':
                # 显示文件详细信息
                stat_info = os.stat(filepath)
                print(f"    创建时间: {time.ctime(stat_info.st_ctime)}")
                print(f"    修改时间: {time.ctime(stat_info.st_mtime)}")

            elif args.action == 'count':
                # 统计行数（文本文件）
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        print(f"    总行数: {len(lines)}")
                        print(f"    非空行数: {sum(1 for line in lines if line.strip())}")
                except UnicodeDecodeError:
                    print(f"    ℹ️  非文本文件，跳过行数统计")
                except Exception as e:
                    print(f"    ❌ 读取失败: {e}")

            elif args.action == 'checksum':
                # 计算MD5校验和
                import hashlib
                print(f"    正在计算MD5...")
                md5_hash = hashlib.md5()
                with open(filepath, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                print(f"    MD5: {md5_hash.hexdigest()}")

            # 模拟处理时间
            time.sleep(0.5)
            print(f"    ✅ 处理完成")
    else:
        print("\n⚠️  未接收到文件!")
        print("请在前端上传文件后执行此脚本。")

    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
