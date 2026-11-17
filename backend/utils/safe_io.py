"""
统一的安全文件 IO 辅助函数

项目中所有"路径来自变量"的文件读写必须经由本模块。
每个函数在执行 IO 前执行 路径规范化 + `..` 段拒绝 + realpath 包含校验，
确保目标位于受控根目录内，防止路径穿越。
"""
import os
from pathlib import Path


class PathEscapeError(ValueError):
    """路径逃逸出允许的根目录"""


def ensure_contained(path, base_dir):
    """
    校验 path 的真实路径位于 base_dir 内（或与之相等），返回消解后的真实路径。

    Raises:
        PathEscapeError: 路径逃逸出 base_dir，或 base_dir 缺失
    """
    if not base_dir:
        raise PathEscapeError('缺少受控根目录 base_dir')

    # 1) 显式拒绝 .. 段（禁止 ../ 上跳）
    parts = os.path.normpath(path).replace('\\', '/').split('/')
    if '..' in parts:
        raise PathEscapeError(f'路径包含 .. 段: {path}')

    # 2) realpath 规范化（消解符号链接）
    real_base = os.path.realpath(base_dir)
    real_path = os.path.realpath(path)

    # 3) 包含校验：真实路径必须位于受控目录内
    if not (real_path == real_base or real_path.startswith(real_base + os.sep)):
        raise PathEscapeError(f'路径越界: {path}')

    return real_path


def safe_write_text(path, content, base_dir, encoding='utf-8'):
    """
    在受控目录内写入文本文件（覆盖写）。返回实际写入的真实路径。
    """
    real_path = ensure_contained(path, base_dir)
    parent = os.path.dirname(real_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # realpath 消解后的受控路径写入
    target = Path(real_path)
    target.write_text(content, encoding=encoding)
    return real_path


def safe_open(path, mode, base_dir, encoding=None, **file_kwargs):
    """
    在受控目录内打开文件，返回文件对象（配合 with 使用）。

    文本模式自动应用 encoding；二进制模式忽略 encoding。
    file_kwargs 透传给底层 open（如 buffering=1 行缓冲）。
    """
    real_path = ensure_contained(path, base_dir)
    if encoding and 'b' not in mode:
        return Path(real_path).open(mode, encoding=encoding, **file_kwargs)
    return Path(real_path).open(mode, **file_kwargs)
