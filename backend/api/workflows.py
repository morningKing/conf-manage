"""
工作流管理API
"""
from flask import request, jsonify, Response, stream_with_context
from models import db
from models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowNodeExecution
from models.script import Script
from models.execution import Execution
from datetime import datetime
import json
import time
from . import api_bp


@api_bp.route('/workflows', methods=['GET'])
def get_workflows():
    """获取工作流列表"""
    try:
        workflows = Workflow.query.order_by(Workflow.created_at.desc()).all()
        return jsonify({
            'code': 0,
            'data': [w.to_dict() for w in workflows]
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflows/<int:workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """获取工作流详情"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)

        # 获取节点和边
        nodes = WorkflowNode.query.filter_by(workflow_id=workflow_id).all()
        edges = WorkflowEdge.query.filter_by(workflow_id=workflow_id).all()

        data = workflow.to_dict()
        data['nodes'] = [n.to_dict() for n in nodes]
        data['edges'] = [e.to_dict() for e in edges]

        return jsonify({
            'code': 0,
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflows', methods=['POST'])
def create_workflow():
    """创建工作流"""
    try:
        data = request.get_json()

        if not data.get('name'):
            return jsonify({'code': 1, 'message': '工作流名称不能为空'}), 400

        # 检查名称是否重复
        if Workflow.query.filter_by(name=data['name']).first():
            return jsonify({'code': 1, 'message': '工作流名称已存在'}), 400

        # 创建工作流
        workflow = Workflow(
            name=data['name'],
            description=data.get('description', ''),
            config=json.dumps(data.get('config', {})),
            enabled=data.get('enabled', True)
        )
        db.session.add(workflow)
        db.session.flush()

        # 创建节点
        nodes_data = data.get('nodes', [])
        for node_data in nodes_data:
            node = WorkflowNode(
                workflow_id=workflow.id,
                node_id=node_data['node_id'],
                node_type=node_data['node_type'],
                script_id=node_data.get('script_id'),
                config=json.dumps(node_data.get('config', {})),
                position_x=node_data.get('position', {}).get('x', 0),
                position_y=node_data.get('position', {}).get('y', 0)
            )
            db.session.add(node)

        # 创建边
        edges_data = data.get('edges', [])
        for edge_data in edges_data:
            edge = WorkflowEdge(
                workflow_id=workflow.id,
                edge_id=edge_data['edge_id'],
                source_node_id=edge_data['source'],
                target_node_id=edge_data['target'],
                condition=json.dumps(edge_data.get('condition')) if edge_data.get('condition') else None
            )
            db.session.add(edge)

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': workflow.to_dict(),
            'message': '工作流创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflows/<int:workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """更新工作流"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)
        data = request.get_json()

        # 更新基本信息
        if 'name' in data:
            if data['name'] != workflow.name and Workflow.query.filter_by(name=data['name']).first():
                return jsonify({'code': 1, 'message': '工作流名称已存在'}), 400
            workflow.name = data['name']

        if 'description' in data:
            workflow.description = data['description']
        if 'config' in data:
            workflow.config = json.dumps(data['config'])
        if 'enabled' in data:
            workflow.enabled = data['enabled']

        workflow.updated_at = datetime.utcnow()

        # 更新节点和边
        if 'nodes' in data:
            # 删除旧节点
            WorkflowNode.query.filter_by(workflow_id=workflow_id).delete()

            # 创建新节点
            for node_data in data['nodes']:
                node = WorkflowNode(
                    workflow_id=workflow.id,
                    node_id=node_data['node_id'],
                    node_type=node_data['node_type'],
                    script_id=node_data.get('script_id'),
                    config=json.dumps(node_data.get('config', {})),
                    position_x=node_data.get('position', {}).get('x', 0),
                    position_y=node_data.get('position', {}).get('y', 0)
                )
                db.session.add(node)

        if 'edges' in data:
            # 删除旧边
            WorkflowEdge.query.filter_by(workflow_id=workflow_id).delete()

            # 创建新边
            for edge_data in data['edges']:
                edge = WorkflowEdge(
                    workflow_id=workflow.id,
                    edge_id=edge_data['edge_id'],
                    source_node_id=edge_data['source'],
                    target_node_id=edge_data['target'],
                    condition=json.dumps(edge_data.get('condition')) if edge_data.get('condition') else None
                )
                db.session.add(edge)

        db.session.commit()

        return jsonify({
            'code': 0,
            'data': workflow.to_dict(),
            'message': '工作流更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflows/<int:workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """删除工作流"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)
        db.session.delete(workflow)
        db.session.commit()

        return jsonify({
            'code': 0,
            'message': '工作流删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflows/<int:workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """执行工作流"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)

        if not workflow.enabled:
            return jsonify({'code': 1, 'message': '工作流已禁用'}), 400

        data = request.get_json() or {}
        params = data.get('params', {})

        # 创建工作流执行记录
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status='pending',
            params=json.dumps(params)
        )
        db.session.add(execution)
        db.session.commit()

        # 异步执行工作流
        from threading import Thread
        from services.workflow_executor import execute_workflow_async
        execution_id = execution.id  # 先获取ID,避免在线程中访问ORM对象
        thread = Thread(target=lambda: execute_workflow_async(execution_id))
        thread.start()

        return jsonify({
            'code': 0,
            'data': execution.to_dict(),
            'message': '工作流执行已启动'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflows/<int:workflow_id>/toggle', methods=['POST'])
def toggle_workflow(workflow_id):
    """启用/禁用工作流"""
    try:
        workflow = Workflow.query.get_or_404(workflow_id)
        workflow.enabled = not workflow.enabled
        workflow.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': workflow.to_dict(),
            'message': f'工作流已{"启用" if workflow.enabled else "禁用"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-executions', methods=['GET'])
def get_workflow_executions():
    """获取工作流执行历史"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        workflow_id = request.args.get('workflow_id', type=int)

        query = WorkflowExecution.query

        if workflow_id:
            query = query.filter_by(workflow_id=workflow_id)

        pagination = query.order_by(WorkflowExecution.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'code': 0,
            'data': {
                'items': [e.to_dict() for e in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-executions/<int:execution_id>', methods=['GET'])
def get_workflow_execution(execution_id):
    """获取工作流执行详情"""
    try:
        execution = WorkflowExecution.query.get_or_404(execution_id)

        # 获取节点执行记录
        node_executions = WorkflowNodeExecution.query.filter_by(
            workflow_execution_id=execution_id
        ).all()

        data = execution.to_dict()
        data['node_executions'] = [ne.to_dict() for ne in node_executions]

        return jsonify({
            'code': 0,
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-executions/<int:execution_id>/cancel', methods=['POST'])
def cancel_workflow_execution(execution_id):
    """取消工作流执行"""
    try:
        execution = WorkflowExecution.query.get_or_404(execution_id)

        if execution.status not in ['pending', 'running']:
            return jsonify({'code': 1, 'message': '工作流已完成，无法取消'}), 400

        execution.status = 'cancelled'
        execution.end_time = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'data': execution.to_dict(),
            'message': '工作流执行已取消'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/workflow-executions/<int:execution_id>/stream', methods=['GET'])
def stream_workflow_execution(execution_id):
    """实时流式传输工作流执行状态 (Server-Sent Events)"""
    def generate():
        execution = WorkflowExecution.query.get(execution_id)
        if not execution:
            yield f"data: {json.dumps({'error': '执行记录不存在'})}\n\n"
            return

        # 持续推送状态更新
        last_status = None
        node_statuses = {}

        while True:
            db.session.refresh(execution)

            # 获取所有节点执行状态
            node_executions = WorkflowNodeExecution.query.filter_by(
                workflow_execution_id=execution_id
            ).all()

            # 检查节点状态是否有变化
            current_node_statuses = {}
            for ne in node_executions:
                current_node_statuses[ne.node_id] = {
                    'node_id': ne.node_id,
                    'status': ne.status,
                    'start_time': ne.start_time.isoformat() if ne.start_time else None,
                    'end_time': ne.end_time.isoformat() if ne.end_time else None,
                    'error': ne.error,
                    'output': ne.output
                }

            # 如果节点状态有变化，推送更新
            if current_node_statuses != node_statuses:
                node_statuses = current_node_statuses
                yield f"data: {json.dumps({'type': 'nodes', 'nodes': list(node_statuses.values())})}\n\n"

            # 推送总体状态
            current_status = {
                'type': 'status',
                'status': execution.status,
                'start_time': execution.start_time.isoformat() if execution.start_time else None,
                'end_time': execution.end_time.isoformat() if execution.end_time else None,
                'error': execution.error
            }

            if current_status != last_status:
                last_status = current_status
                yield f"data: {json.dumps(current_status)}\n\n"

            # 如果执行完成，发送最终状态并结束
            if execution.status in ['success', 'failed', 'cancelled']:
                # 发送最终节点状态
                yield f"data: {json.dumps({'type': 'nodes', 'nodes': list(node_statuses.values())})}\n\n"

                # 发送完成信息
                completion_data = {
                    'type': 'complete',
                    'status': execution.status,
                    'error': execution.error or '',
                    'end_time': execution.end_time.isoformat() if execution.end_time else None
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                break

            time.sleep(0.5)  # 每0.5秒检查一次

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

