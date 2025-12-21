"""
文件处理工具函数
"""
import os
import re


def safe_filename(filename):
    """
    处理文件名，支持中文文件名

    与 werkzeug.utils.secure_filename 不同，此函数保留中文字符，
    只移除真正危险的字符（路径遍历、特殊字符等）

    Args:
        filename: 原始文件名

    Returns:
        处理后的安全文件名
    """
    if not filename:
        return 'unnamed'

    # 分离文件名和扩展名
    name, ext = os.path.splitext(filename)

    # 移除危险字符：
    # - 路径分隔符: / \
    # - 父目录引用: ..
    # - 空字节: \0
    # - 控制字符: \r \n \t
    # - Windows保留字符: < > : " | ? *
    dangerous_chars = r'[/\\<>:"|?*\0\r\n\t]'
    name = re.sub(dangerous_chars, '_', name)

    # 移除前导和尾随的空格和点
    name = name.strip('. ')

    # 如果处理后的名称为空，使用默认名称
    if not name:
        name = 'unnamed'

    # 限制文件名长度（保留255字节，考虑UTF-8编码）
    # 为扩展名预留空间
    max_name_length = 200
    if len(name.encode('utf-8')) > max_name_length:
        # 截断时保持完整的UTF-8字符
        name_bytes = name.encode('utf-8')[:max_name_length]
        # 尝试解码，如果失败则逐字节缩短直到成功
        while True:
            try:
                name = name_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                name_bytes = name_bytes[:-1]

    # 处理扩展名（通常不包含中文，但也要处理）
    ext = re.sub(dangerous_chars, '', ext)

    # 合并文件名和扩展名
    safe_name = name + ext

    return safe_name
