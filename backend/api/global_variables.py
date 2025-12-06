"""
全局变量管理API
"""
from flask import request, jsonify
from models import db, GlobalVariable
from sqlalchemy.exc import IntegrityError
from . import api_bp


@api_bp.route('/global-variables', methods=['GET'])
def get_global_variables():
    """获取全局变量列表"""
    try:
        # 查询参数：是否显示加密变量的值
        show_encrypted = request.args.get('show_encrypted', 'false').lower() == 'true'

        variables = GlobalVariable.query.order_by(GlobalVariable.created_at.desc()).all()
        return jsonify({
            'code': 0,
            'data': [var.to_dict(show_value=not var.is_encrypted or show_encrypted) for var in variables]
        }), 200
    except Exception as e:
        return jsonify({'code': 1, 'message': f'获取全局变量列表失败: {str(e)}'}), 500


@api_bp.route('/global-variables/<int:variable_id>', methods=['GET'])
def get_global_variable(variable_id):
    """获取单个全局变量详情"""
    try:
        variable = GlobalVariable.query.get(variable_id)
        if not variable:
            return jsonify({'code': 1, 'message': '全局变量不存在'}), 404

        # 查询参数：是否显示加密变量的值
        show_encrypted = request.args.get('show_encrypted', 'false').lower() == 'true'

        return jsonify({
            'code': 0,
            'data': variable.to_dict(show_value=not variable.is_encrypted or show_encrypted)
        }), 200
    except Exception as e:
        return jsonify({'code': 1, 'message': f'获取全局变量详情失败: {str(e)}'}), 500


@api_bp.route('/global-variables', methods=['POST'])
def create_global_variable():
    """创建全局变量"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('key'):
            return jsonify({'code': 1, 'message': '变量名不能为空'}), 400
        if not data.get('value'):
            return jsonify({'code': 1, 'message': '变量值不能为空'}), 400

        # 创建全局变量
        variable = GlobalVariable(
            key=data['key'],
            value=data['value'],
            description=data.get('description', ''),
            is_encrypted=data.get('is_encrypted', False)
        )

        db.session.add(variable)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '创建成功',
            'data': variable.to_dict()
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'code': 1, 'message': '变量名已存在'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': f'创建全局变量失败: {str(e)}'}), 500


@api_bp.route('/global-variables/<int:variable_id>', methods=['PUT'])
def update_global_variable(variable_id):
    """更新全局变量"""
    try:
        variable = GlobalVariable.query.get(variable_id)
        if not variable:
            return jsonify({'code': 1, 'message': '全局变量不存在'}), 404

        data = request.get_json()

        # 更新字段
        if 'key' in data:
            variable.key = data['key']
        if 'value' in data:
            variable.value = data['value']
        if 'description' in data:
            variable.description = data['description']
        if 'is_encrypted' in data:
            variable.is_encrypted = data['is_encrypted']

        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '更新成功',
            'data': variable.to_dict()
        }), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'code': 1, 'message': '变量名已存在'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': f'更新全局变量失败: {str(e)}'}), 500


@api_bp.route('/global-variables/<int:variable_id>', methods=['DELETE'])
def delete_global_variable(variable_id):
    """删除全局变量"""
    try:
        variable = GlobalVariable.query.get(variable_id)
        if not variable:
            return jsonify({'code': 1, 'message': '全局变量不存在'}), 404

        db.session.delete(variable)
        db.session.commit()

        return jsonify({'code': 0, 'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': f'删除全局变量失败: {str(e)}'}), 500


@api_bp.route('/global-variables/dict', methods=['GET'])
def get_variables_dict():
    """获取全局变量字典（用于脚本执行时注入）"""
    try:
        variables = GlobalVariable.query.all()
        var_dict = {var.key: var.value for var in variables}
        return jsonify({'code': 0, 'data': var_dict}), 200
    except Exception as e:
        return jsonify({'code': 1, 'message': f'获取全局变量字典失败: {str(e)}'}), 500
