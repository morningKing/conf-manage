"""
安全的表达式求值器（基于 AST 白名单）

用于工作流条件判断等场景，替代 eval()。
仅支持：
- 字面量与变量引用
- 算术 / 比较 / 逻辑 / 一元运算
- 属性访问（映射到 dict 取键，禁用下划线开头属性）与下标访问
- 条件表达式 (a if cond else b)
不支持函数调用、import、推导式等任何其他语法。
"""
import ast

_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}

_ALLOWED_UNARYOPS = {
    ast.USub: lambda a: -a,
    ast.UAdd: lambda a: +a,
    ast.Not: lambda a: not a,
}

_ALLOWED_CMPOPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: lambda a, b: a is b,
    ast.IsNot: lambda a, b: a is not b,
}


class ExprEvalError(ValueError):
    """表达式不合法或不被支持"""


def safe_eval(expr, variables=None):
    """
    安全求值表达式，返回计算结果。

    Args:
        expr: 表达式字符串，如 "node_1.status == 'success' and node_1.code == 0"
        variables: 变量字典

    Raises:
        ExprEvalError: 表达式包含不支持的语法或引用了未定义变量
    """
    if not isinstance(expr, str) or not expr.strip():
        raise ExprEvalError('空表达式')
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        raise ExprEvalError(f'表达式语法错误: {e}') from e
    return _eval_node(tree.body, variables or {})


def _eval_node(node, variables):
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        if node.id == 'True':
            return True
        if node.id == 'False':
            return False
        if node.id == 'None':
            return None
        raise ExprEvalError(f'未定义的变量: {node.id}')

    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval_node(item, variables) for item in node.elts]

    if isinstance(node, ast.Dict):
        return {
            _eval_node(key, variables): _eval_node(value, variables)
            for key, value in zip(node.keys, node.values)
        }

    if isinstance(node, ast.Attribute):
        # 禁用下划线开头属性，阻断 __class__ 等逃逸链
        if node.attr.startswith('_'):
            raise ExprEvalError(f'不允许访问的属性: {node.attr}')
        obj = _eval_node(node.value, variables)
        if isinstance(obj, dict):
            if node.attr in obj:
                return obj[node.attr]
            raise ExprEvalError(f'字典中不存在键: {node.attr}')
        return getattr(obj, node.attr)

    if isinstance(node, ast.Subscript):
        obj = _eval_node(node.value, variables)
        key = _eval_node(node.slice, variables)
        return obj[key]

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BINOPS:
            raise ExprEvalError(f'不支持的运算符: {op_type.__name__}')
        return _ALLOWED_BINOPS[op_type](
            _eval_node(node.left, variables),
            _eval_node(node.right, variables),
        )

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_UNARYOPS:
            raise ExprEvalError(f'不支持的一元运算符: {op_type.__name__}')
        return _ALLOWED_UNARYOPS[op_type](_eval_node(node.operand, variables))

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result = True
            for value_node in node.values:
                result = _eval_node(value_node, variables)
                if not result:
                    return result
            return result
        # ast.Or
        result = False
        for value_node in node.values:
            result = _eval_node(value_node, variables)
            if result:
                return result
        return result

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for op, comparator in zip(node.ops, node.comparators):
            op_type = type(op)
            if op_type not in _ALLOWED_CMPOPS:
                raise ExprEvalError(f'不支持的比较运算符: {op_type.__name__}')
            right = _eval_node(comparator, variables)
            if not _ALLOWED_CMPOPS[op_type](left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.IfExp):
        if _eval_node(node.test, variables):
            return _eval_node(node.body, variables)
        return _eval_node(node.orelse, variables)

    raise ExprEvalError(f'不支持的语法: {type(node).__name__}')
