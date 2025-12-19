"""
工作流执行引擎
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowNodeExecution
from models.script import Script
from models.execution import Execution
from services.executor import execute_script
from datetime import datetime
import json
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def execute_workflow_async(workflow_execution_id):
    """异步执行工作流"""
    app = create_app()
    with app.app_context():
        try:
            execution = WorkflowExecution.query.get(workflow_execution_id)
            if not execution:
                print(f'工作流执行记录不存在: {workflow_execution_id}')
                return

            # 更新状态为运行中
            execution.status = 'running'
            execution.start_time = datetime.utcnow()
            db.session.commit()

            # 获取工作流定义
            workflow = execution.workflow

            # 获取所有节点和边
            nodes = {n.node_id: n for n in WorkflowNode.query.filter_by(workflow_id=workflow.id).all()}
            edges = WorkflowEdge.query.filter_by(workflow_id=workflow.id).all()

            # 构建依赖关系图
            graph = build_dependency_graph(nodes, edges)

            # 获取执行参数
            params = json.loads(execution.params) if execution.params else {}

            # 执行工作流
            success = execute_workflow_graph(execution, graph, nodes, params)

            # 更新执行状态
            execution.status = 'success' if success else 'failed'
            execution.end_time = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            print(f'工作流执行失败: {str(e)}')
            if execution:
                execution.status = 'failed'
                execution.error = str(e)
                execution.end_time = datetime.utcnow()
                db.session.commit()


def build_dependency_graph(nodes, edges):
    """构建依赖关系图"""
    graph = {node_id: {'deps': [], 'next': []} for node_id in nodes.keys()}

    for edge in edges:
        # source -> target: target依赖于source
        if edge.target_node_id in graph:
            graph[edge.target_node_id]['deps'].append({
                'node_id': edge.source_node_id,
                'condition': json.loads(edge.condition) if edge.condition else None
            })
        if edge.source_node_id in graph:
            graph[edge.source_node_id]['next'].append({
                'node_id': edge.target_node_id,
                'condition': json.loads(edge.condition) if edge.condition else None
            })

    return graph


def execute_workflow_graph(workflow_execution, graph, nodes, params):
    """执行工作流图"""
    # 找到入口节点（没有依赖的节点）
    entry_nodes = [node_id for node_id, info in graph.items() if not info['deps']]

    if not entry_nodes:
        raise Exception('工作流没有入口节点')

    logger.info(f"[工作流执行] 入口节点: {entry_nodes}")
    logger.info(f"[工作流执行] 所有节点: {list(nodes.keys())}")
    logger.info(f"[工作流执行] 依赖关系图: {graph}")
    sys.stdout.flush()

    # 节点执行结果
    node_results = {}

    # 已执行的节点
    executed = set()

    # 待执行队列
    queue = entry_nodes.copy()

    while queue:
        node_id = queue.pop(0)
        logger.info(f"[工作流执行] 处理节点: {node_id}")
        sys.stdout.flush()

        if node_id in executed:
            logger.info(f"[工作流执行] 节点 {node_id} 已执行，跳过")
            sys.stdout.flush()
            continue

        node = nodes[node_id]

        # 检查依赖是否都已执行
        deps = graph[node_id]['deps']
        logger.info(f"[工作流执行] 节点 {node_id} 的依赖: {deps}")
        sys.stdout.flush()
        deps_ready = True
        for dep in deps:
            dep_node_id = dep['node_id']
            if dep_node_id not in executed:
                logger.info(f"[工作流执行] 依赖节点 {dep_node_id} 未执行，等待")
                sys.stdout.flush()
                deps_ready = False
                break

            # 检查条件
            if dep['condition']:
                logger.info(f"[工作流执行] 检查条件: {dep['condition']}")
                logger.info(f"[工作流执行] 当前node_results: {node_results}")
                sys.stdout.flush()
                # 传递整个node_results作为context，让evaluate_condition根据condition中的node_id查找
                if not evaluate_condition(dep['condition'], node_results):
                    # 条件不满足，跳过此节点
                    logger.info(f"[工作流执行] 条件不满足，跳过节点 {node_id}")
                    sys.stdout.flush()
                    executed.add(node_id)
                    create_node_execution(workflow_execution.id, node_id, 'skipped', '条件不满足')
                    deps_ready = False
                    break
                else:
                    logger.info(f"[工作流执行] 条件满足")
                    sys.stdout.flush()

        if not deps_ready:
            logger.info(f"[工作流执行] 节点 {node_id} 依赖未就绪，继续下一个")
            sys.stdout.flush()
            continue

        # 执行节点
        logger.info(f"[工作流执行] 开始执行节点 {node_id}")
        sys.stdout.flush()
        success, result = execute_node(workflow_execution, node, params, node_results)
        logger.info(f"[工作流执行] 节点 {node_id} 执行完成，success={success}, result={result}")
        sys.stdout.flush()
        node_results[node_id] = result
        executed.add(node_id)

        if not success and node.node_type == 'script':
            # 脚本节点执行失败，终止工作流
            logger.info(f"[工作流执行] 脚本节点 {node_id} 失败，终止工作流")
            sys.stdout.flush()
            return False

        # 将下一个节点加入队列
        next_nodes = graph[node_id]['next']
        logger.info(f"[工作流执行] 节点 {node_id} 的下一个节点: {next_nodes}")
        sys.stdout.flush()
        for next_node in next_nodes:
            next_node_id = next_node['node_id']
            if next_node_id not in executed and next_node_id not in queue:
                logger.info(f"[工作流执行] 将节点 {next_node_id} 加入队列")
                sys.stdout.flush()
                queue.append(next_node_id)

        logger.info(f"[工作流执行] 当前队列: {queue}, 已执行: {executed}")
        sys.stdout.flush()

    logger.info(f"[工作流执行] 工作流执行完成")
    sys.stdout.flush()
    return True


def execute_node(workflow_execution, node, params, node_results):
    """执行单个节点"""
    node_execution = None
    try:
        logger.info(f"[execute_node] 准备创建节点执行记录: node_id={node.node_id}")
        sys.stdout.flush()

        # 保存workflow_execution_id，因为session可能被清理
        workflow_execution_id = workflow_execution.id

        # 保存节点信息，因为node对象可能会从session detach
        node_id = node.node_id
        node_type = node.node_type
        script_id = node.script_id if node.node_type == 'script' else None
        node_config = node.config

        # 创建节点执行记录
        node_execution = WorkflowNodeExecution(
            workflow_execution_id=workflow_execution_id,
            node_id=node_id,
            status='running',
            start_time=datetime.utcnow()
        )
        logger.info(f"[execute_node] 节点执行记录已创建")
        sys.stdout.flush()

        db.session.add(node_execution)
        logger.info(f"[execute_node] 节点执行记录已添加到session")
        sys.stdout.flush()

        db.session.commit()
        logger.info(f"[execute_node] 节点执行记录已提交到数据库")
        sys.stdout.flush()

        # 保存节点执行ID，因为后面session可能被清理
        node_execution_id = node_execution.id
        logger.info(f"[execute_node] 节点执行记录ID: {node_execution_id}")
        sys.stdout.flush()

        result = None

        if node_type == 'script':
            # 执行脚本节点
            logger.info(f"[execute_node] 调用execute_script_node")
            sys.stdout.flush()
            result = execute_script_node(script_id, params, node_execution)
            logger.info(f"[execute_node] execute_script_node返回: {result}")
            sys.stdout.flush()

        elif node_type == 'delay':
            # 延迟节点
            result = execute_delay_node(node_config, node_execution)

        elif node_type == 'condition':
            # 条件节点（仅评估，不执行）
            result = evaluate_condition_node(node_config, node_results)

        logger.info(f"[execute_node] 准备重新获取节点执行记录")
        sys.stdout.flush()

        # 重新获取节点执行记录以确保更新生效（因为execute_script可能清理了session）
        db.session.expire_all()
        node_execution = WorkflowNodeExecution.query.get(node_execution_id)

        logger.info(f"[execute_node] 重新获取成功: {node_execution is not None}")
        sys.stdout.flush()

        if node_execution:
            # 更新节点执行状态
            node_execution.status = 'success'
            node_execution.output = json.dumps(result) if result else None
            node_execution.end_time = datetime.utcnow()
            db.session.commit()
            logger.info(f"[execute_node] 节点状态已更新为success")
            sys.stdout.flush()

        return True, result

    except Exception as e:
        logger.error(f'[execute_node] 节点执行失败 [{node.node_id}]: {str(e)}')
        import traceback
        logger.error(f'[execute_node] 异常堆栈:\n{traceback.format_exc()}')
        sys.stdout.flush()

        # 重新获取节点执行记录
        if node_execution and hasattr(node_execution, 'id') and node_execution.id:
            try:
                db.session.expire_all()
                node_execution = WorkflowNodeExecution.query.get(node_execution.id)
                if node_execution:
                    node_execution.status = 'failed'
                    node_execution.error = str(e)
                    node_execution.end_time = datetime.utcnow()
                    db.session.commit()
            except Exception as e2:
                logger.error(f'[execute_node] 更新失败状态时出错: {str(e2)}')
                sys.stdout.flush()
        return False, None


def execute_script_node(script_id, params, node_execution):
    """执行脚本节点"""
    if not script_id:
        raise Exception('脚本节点未关联脚本')

    # 创建脚本执行记录
    script_execution = Execution(
        script_id=script_id,
        status='pending',
        params=json.dumps(params) if params else None
    )
    db.session.add(script_execution)
    db.session.commit()

    script_execution_id = script_execution.id

    # 关联到节点执行
    node_execution.execution_id = script_execution_id
    db.session.commit()

    # 执行脚本
    execute_script(script_execution_id)

    # 重新查询执行记录以获取最新状态（因为execute_script可能在不同的session中更新）
    db.session.expire_all()
    script_execution = Execution.query.get(script_execution_id)

    if not script_execution:
        raise Exception('无法获取脚本执行状态')

    if script_execution.status == 'failed':
        raise Exception(f'脚本执行失败: {script_execution.error}')

    return {
        'execution_id': script_execution.id,
        'status': script_execution.status,
        'output': script_execution.output
    }


def execute_delay_node(node_config, node_execution):
    """执行延迟节点"""
    import time
    config = json.loads(node_config) if node_config else {}
    delay_seconds = config.get('delay', 0)

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    return {'delayed': delay_seconds}


def evaluate_condition_node(node_config, node_results):
    """评估条件节点"""
    config = json.loads(node_config) if node_config else {}
    condition = config.get('condition', {})

    return evaluate_condition(condition, node_results)


def evaluate_condition(condition, context):
    """评估条件"""
    if not condition:
        return True

    condition_type = condition.get('type')

    if condition_type == 'success':
        # 检查前置节点是否成功
        node_id = condition.get('node_id')
        if node_id in context:
            return context[node_id].get('status') == 'success'
        return False

    elif condition_type == 'failed':
        # 检查前置节点是否失败
        node_id = condition.get('node_id')
        if node_id in context:
            return context[node_id].get('status') == 'failed'
        return False

    elif condition_type == 'expression':
        # 表达式条件（简单实现）
        expr = condition.get('expression', '')
        try:
            # 安全的表达式评估
            return eval(expr, {"__builtins__": {}}, context)
        except:
            return False

    return True


def create_node_execution(workflow_execution_id, node_id, status, message=''):
    """创建跳过的节点执行记录"""
    node_execution = WorkflowNodeExecution(
        workflow_execution_id=workflow_execution_id,
        node_id=node_id,
        status=status,
        output=message,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )
    db.session.add(node_execution)
    db.session.commit()
