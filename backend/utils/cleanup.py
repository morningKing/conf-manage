"""
清理工具模块
用于管理历史数据的清理，包括执行记录、执行空间目录和日志文件
"""
import os
import shutil
from datetime import datetime
from models import db, Execution, Schedule, WorkflowExecution, WorkflowNodeExecution, Script
from config import Config


def get_directory_size(path):
    """
    获取目录大小（字节）

    Args:
        path: 目录路径

    Returns:
        int: 目录大小（字节），如果目录不存在返回0
    """
    if not os.path.exists(path):
        return 0

    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    # 忽略无法访问的文件
                    pass
    except (OSError, IOError):
        # 忽略无法访问的目录
        pass

    return total_size


def get_cleanup_stats():
    """
    获取清理统计信息

    Returns:
        dict: 包含以下字段的字典
            - total_executions: 总执行记录数
            - whitelisted_executions: 白名单执行记录数
            - to_cleanup: 需要清理的记录数
            - execution_spaces_size_mb: 执行空间目录大小（MB）
            - workflow_spaces_size_mb: 工作流执行空间目录大小（MB）
            - threshold: 清理阈值
    """
    # 获取白名单脚本ID（两个来源）
    # 1. Script.preserve=True的脚本
    script_whitelist_ids = set(
        s.id for s in Script.query.filter_by(preserve=True).all()
    )

    # 2. Schedule.preserve=True的定时任务脚本
    schedule_whitelist_ids = set(
        s.script_id for s in Schedule.query.filter_by(preserve=True).all()
    )

    # 合并白名单脚本ID
    whitelisted_script_ids = script_whitelist_ids | schedule_whitelist_ids

    # 获取所有执行记录
    total_executions = Execution.query.count()

    # 获取白名单执行记录数
    whitelisted_executions = 0
    if whitelisted_script_ids:
        whitelisted_executions = Execution.query.filter(
            Execution.script_id.in_(whitelisted_script_ids)
        ).count()

    # 计算需要清理的记录数
    # 逻辑：总记录数 - 白名单记录数 - 阈值保留数
    threshold = Config.CLEANUP_THRESHOLD
    non_whitelisted_count = total_executions - whitelisted_executions
    to_cleanup = max(0, non_whitelisted_count - threshold)

    # 计算执行空间目录大小
    execution_spaces_size = get_directory_size(Config.EXECUTION_SPACES_DIR)
    workflow_spaces_size = get_directory_size(Config.WORKFLOW_EXECUTION_SPACES_DIR)

    return {
        'total_executions': total_executions,
        'whitelisted_executions': whitelisted_executions,
        'to_cleanup': to_cleanup,
        'execution_spaces_size_mb': round(execution_spaces_size / (1024 * 1024), 2),
        'workflow_spaces_size_mb': round(workflow_spaces_size / (1024 * 1024), 2),
        'threshold': threshold
    }


def run_cleanup():
    """
    执行清理操作

    清理逻辑：
    1. 获取白名单脚本ID（Script.preserve=True 或 Schedule.preserve=True）
    2. 获取所有Execution记录，按创建时间倒序排列
    3. 构建保留ID集合：白名单执行 + 最近CLEANUP_THRESHOLD条非白名单执行
    4. 删除不在保留集合中的执行记录（数据库记录 + 目录 + 日志）
    5. 清理WorkflowExecution中所有节点执行都已删除的记录

    Returns:
        dict: 包含以下字段
            - deleted_executions: 删除的执行记录数
            - deleted_execution_spaces: 删除的执行空间目录数
            - deleted_workflow_spaces: 删除的工作流执行空间目录数
            - freed_space_mb: 释放的空间大小（MB）
    """
    print("[Cleanup] 开始清理历史数据...")

    # 计算清理前的空间大小
    space_before = (
        get_directory_size(Config.EXECUTION_SPACES_DIR) +
        get_directory_size(Config.WORKFLOW_EXECUTION_SPACES_DIR)
    )

    # 1. 获取白名单脚本ID（两个来源）
    # Script.preserve=True的脚本
    script_whitelist_ids = set(
        s.id for s in Script.query.filter_by(preserve=True).all()
    )
    # Schedule.preserve=True的定时任务脚本
    schedule_whitelist_ids = set(
        s.script_id for s in Schedule.query.filter_by(preserve=True).all()
    )
    # 合并白名单脚本ID
    whitelisted_script_ids = script_whitelist_ids | schedule_whitelist_ids
    print(f"[Cleanup] 白名单脚本ID: {whitelisted_script_ids}")
    print(f"[Cleanup] - Script白名单: {script_whitelist_ids}")
    print(f"[Cleanup] - Schedule白名单: {schedule_whitelist_ids}")

    # 2. 获取所有Execution记录，按创建时间倒序
    all_executions = Execution.query.order_by(Execution.created_at.desc()).all()

    # 3. 构建保留ID集合
    preserve_ids = set()
    non_whitelisted_count = 0

    for exec in all_executions:
        if exec.script_id in whitelisted_script_ids:
            # 白名单执行全部保留
            preserve_ids.add(exec.id)
        else:
            # 非白名单执行保留最近的CLEANUP_THRESHOLD条
            if non_whitelisted_count < Config.CLEANUP_THRESHOLD:
                preserve_ids.add(exec.id)
                non_whitelisted_count += 1

    print(f"[Cleanup] 保留执行记录数: {len(preserve_ids)}")

    # 4. 识别要删除的执行记录
    executions_to_delete = [exec for exec in all_executions if exec.id not in preserve_ids]

    if not executions_to_delete:
        print("[Cleanup] 无需清理的执行记录")
        return {
            'deleted_executions': 0,
            'deleted_execution_spaces': 0,
            'deleted_workflow_spaces': 0,
            'freed_space_mb': 0
        }

    # 收集要删除的执行记录ID
    execution_ids_to_delete = {exec.id for exec in executions_to_delete}

    # 收集要删除的文件路径（稍后删除，在DB提交成功后）
    execution_space_paths = []
    log_file_paths = []

    for exec in executions_to_delete:
        # 收集执行空间目录路径
        space_path = Config.get_execution_space(exec.id)
        if os.path.exists(space_path):
            execution_space_paths.append(space_path)

        # 收集日志文件路径
        if exec.log_file:
            log_path = os.path.join(Config.LOGS_DIR, os.path.basename(exec.log_file))
            if os.path.exists(log_path):
                log_file_paths.append(log_path)

    # 5. 处理外键关系：设置WorkflowNodeExecution.execution_id为NULL
    # 批量更新，避免N+1查询
    db.session.query(WorkflowNodeExecution).filter(
        WorkflowNodeExecution.execution_id.in_(execution_ids_to_delete)
    ).update(
        {WorkflowNodeExecution.execution_id: None},
        synchronize_session=False
    )
    print(f"[Cleanup] 已清除 {len(execution_ids_to_delete)} 个执行记录的WorkflowNodeExecution外键关联")

    # 6. 删除数据库记录
    for exec in executions_to_delete:
        db.session.delete(exec)

    # 7. 提交数据库事务（先提交，确保数据一致性）
    try:
        db.session.commit()
        print(f"[Cleanup] 数据库事务提交成功，删除执行记录: {len(executions_to_delete)}")
    except Exception as e:
        db.session.rollback()
        print(f"[Cleanup] 数据库提交失败: {e}")
        return {
            'deleted_executions': 0,
            'deleted_execution_spaces': 0,
            'deleted_workflow_spaces': 0,
            'freed_space_mb': 0
        }

    # 8. 数据库提交成功后，删除文件系统资源
    deleted_execution_spaces = 0
    deleted_logs = 0

    for space_path in execution_space_paths:
        try:
            shutil.rmtree(space_path)
            deleted_execution_spaces += 1
            print(f"[Cleanup] 删除执行空间: {space_path}")
        except Exception as e:
            print(f"[Cleanup] 删除执行空间失败 {space_path}: {e}")

    for log_path in log_file_paths:
        try:
            os.remove(log_path)
            deleted_logs += 1
            print(f"[Cleanup] 删除日志文件: {log_path}")
        except Exception as e:
            print(f"[Cleanup] 删除日志文件失败 {log_path}: {e}")

    # 9. 清理WorkflowExecution中所有节点执行都已删除的记录
    # 批量加载所有WorkflowExecution和WorkflowNodeExecution，避免N+1查询
    deleted_workflow_spaces = 0
    workflow_executions = WorkflowExecution.query.all()

    # 预加载所有WorkflowNodeExecution，按workflow_execution_id分组
    all_node_executions = WorkflowNodeExecution.query.all()
    node_executions_by_wf = {}
    for ne in all_node_executions:
        if ne.workflow_execution_id not in node_executions_by_wf:
            node_executions_by_wf[ne.workflow_execution_id] = []
        node_executions_by_wf[ne.workflow_execution_id].append(ne)

    # 获取所有存在的Execution ID（用于检查关联）
    existing_execution_ids = set(e.id for e in Execution.query.with_entities(Execution.id).all())

    workflow_space_paths = []

    for wf_exec in workflow_executions:
        node_executions = node_executions_by_wf.get(wf_exec.id, [])

        # 如果没有节点执行记录，或者所有节点执行的execution_id都无效
        should_delete = False
        if not node_executions:
            should_delete = True
        else:
            # 检查是否所有关联的Execution都已删除
            all_deleted = all(
                ne.execution_id is None or
                ne.execution_id not in existing_execution_ids
                for ne in node_executions
            )
            should_delete = all_deleted

        if should_delete:
            # 收集工作流执行空间路径
            space_path = Config.get_workflow_execution_space(wf_exec.id)
            if os.path.exists(space_path):
                workflow_space_paths.append((wf_exec, space_path))
            else:
                # 即使没有空间目录，也要删除数据库记录
                db.session.delete(wf_exec)
                print(f"[Cleanup] 删除工作流执行记录（无空间目录）: {wf_exec.id}")

    # 提交工作流清理的数据库更改
    workflow_db_deleted = 0
    try:
        for wf_exec, space_path in workflow_space_paths:
            db.session.delete(wf_exec)
            workflow_db_deleted += 1
        db.session.commit()
        print(f"[Cleanup] 删除工作流执行记录: {workflow_db_deleted}")
    except Exception as e:
        db.session.rollback()
        print(f"[Cleanup] 工作流清理数据库提交失败: {e}")

    # 删除工作流执行空间（DB提交成功后）
    for wf_exec, space_path in workflow_space_paths:
        try:
            shutil.rmtree(space_path)
            deleted_workflow_spaces += 1
            print(f"[Cleanup] 删除工作流执行空间: {space_path}")
        except Exception as e:
            print(f"[Cleanup] 删除工作流执行空间失败 {space_path}: {e}")

    # 计算释放的空间
    space_after = (
        get_directory_size(Config.EXECUTION_SPACES_DIR) +
        get_directory_size(Config.WORKFLOW_EXECUTION_SPACES_DIR)
    )
    freed_space_mb = round((space_before - space_after) / (1024 * 1024), 2)
    # 确保不会出现负数（如果有新文件创建）
    freed_space_mb = max(0, freed_space_mb)

    print(f"[Cleanup] 清理完成:")
    print(f"  - 删除执行记录: {len(executions_to_delete)}")
    print(f"  - 删除执行空间: {deleted_execution_spaces}")
    print(f"  - 删除工作流执行空间: {deleted_workflow_spaces}")
    print(f"  - 删除日志文件: {deleted_logs}")
    print(f"  - 释放空间: {freed_space_mb} MB")

    return {
        'deleted_executions': len(executions_to_delete),
        'deleted_execution_spaces': deleted_execution_spaces,
        'deleted_workflow_spaces': deleted_workflow_spaces,
        'freed_space_mb': freed_space_mb
    }


def run_cleanup_if_needed():
    """
    在应用启动时检查并执行清理

    如果需要清理的记录数超过阈值的一半，则执行清理

    Returns:
        dict or None: 如果执行了清理返回清理结果，否则返回None
    """
    print("[Cleanup] 检查是否需要清理...")

    stats = get_cleanup_stats()

    # 如果需要清理的记录数超过阈值的一半，执行清理
    if stats['to_cleanup'] > Config.CLEANUP_THRESHOLD // 2:
        print(f"[Cleanup] 需要清理的记录数 ({stats['to_cleanup']}) 超过阈值的一半 ({Config.CLEANUP_THRESHOLD // 2})，开始清理...")
        return run_cleanup()
    else:
        print(f"[Cleanup] 无需清理，当前需要清理的记录数: {stats['to_cleanup']}")
        return None