"""工具模块单元测试：safe_io / expr_eval / file_utils"""
import os

import pytest

from utils.safe_io import PathEscapeError, ensure_contained, safe_open, safe_write_text
from utils.expr_eval import safe_eval
from utils.file_utils import safe_filename


class TestSafeIO:
    def test_write_and_read(self, tmp_path):
        target = tmp_path / 'sub' / 'a.txt'
        written = safe_write_text(str(target), 'hello', base_dir=str(tmp_path))
        assert os.path.realpath(written) == os.path.realpath(target)
        assert target.read_text(encoding='utf-8') == 'hello'

    def test_escape_blocked(self, tmp_path):
        with pytest.raises(PathEscapeError):
            safe_write_text(str(tmp_path / '..' / 'evil.txt'), 'x', base_dir=str(tmp_path))

    def test_missing_base_dir(self, tmp_path):
        with pytest.raises(PathEscapeError):
            safe_write_text(str(tmp_path / 'a.txt'), 'x', base_dir=None)

    def test_safe_open_append(self, tmp_path):
        target = tmp_path / 'log.txt'
        target.write_text('a', encoding='utf-8')
        with safe_open(str(target), 'a', base_dir=str(tmp_path), encoding='utf-8', buffering=1) as f:
            f.write('b')
        assert target.read_text(encoding='utf-8') == 'ab'

    def test_ensure_contained_symlink_like(self, tmp_path):
        real = ensure_contained(str(tmp_path / 'x.txt'), str(tmp_path))
        assert real.startswith(os.path.realpath(str(tmp_path)))


class TestSafeEval:
    def test_arithmetic(self):
        assert safe_eval('1 + 2 * 3 == 7', {}) is True

    def test_dict_access(self):
        ctx = {'node': {'status': 'success', 'code': 0}}
        assert safe_eval("node.status == 'success'", ctx) is True
        assert safe_eval('node.code == 0 and node.status != "failed"', ctx) is True

    def test_dunder_blocked(self):
        with pytest.raises(Exception):
            safe_eval('node.__class__', {'node': {}})

    def test_call_blocked(self):
        with pytest.raises(Exception):
            safe_eval('__import__("os").system("ls")', {})

    def test_comprehension_blocked(self):
        with pytest.raises(Exception):
            safe_eval('[x for x in [1,2]]', {})


class TestSafeFilename:
    def test_traversal_removed(self):
        assert '/' not in safe_filename('../../etc/passwd')
        assert '\\' not in safe_filename('..\\..\\evil.py')

    def test_chinese_kept(self):
        assert safe_filename('中文脚本.py') == '中文脚本.py'

    def test_empty(self):
        assert safe_filename('') == 'unnamed'
