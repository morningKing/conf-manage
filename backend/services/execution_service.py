"""
执行记录服务

收拢此前散落在 api/executions.py（单个/批量）与 api/selection.py 的重复逻辑：
- 删除执行记录（数据库 + 日志文件 + 执行空间）
- 终止进程树（psutil）
- 重试执行（新建记录 + 复制执行空间）
"""
import json
import logging
import os
import shutil

import psutil

from models import db, Execution
from config import Config

logger = logging.getLogger(__name__)


def delete_execution_record(execution):
    """
    删除单条执行记录：先提交数据库，成功后再清理日志文件与执行空间，
    避免"先删文件后删记录"中途失败留下孤儿记录。
    """
    execution_id = execution.id
    db.session.delete(execution)
    db.session.commit()

    # 数据库删除成功后清理文件系统资源
    if execution.log_file:
        log_path = os.path.join(Config.LOGS_DIR, os.path.basename(execution.log_file))
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
                logger.info('已删除执行 %s 的日志文件: %s', execution_id, log_path)
            except OSError as e:
                logger.warning('删除日志文件失败 %s: %s', log_path, e)

    space_path = Config.get_execution_space(execution_id)
    if os.path.exists(space_path):
        try:
            shutil.rmtree(space_path)
            logger.info('已删除执行 %s 的执行空间: %s', execution_id, space_path)
        except OSError as e:
            logger.warning('删除执行空间失败 %s: %s', space_path, e)


def kill_process_tree(pid):
    """
    终止进程及其全部子进程（先温和 terminate，超时后 kill）
    """
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)

    for child in children:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            pass

    _, alive = psutil.wait_procs(children, timeout=3)
    for proc in alive:
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass

    parent.terminate()
    try:
        parent.wait(timeout=3)
    except psutil.TimeoutExpired:
        try:
            parent.kill()
        except psutil.NoSuchProcess:
            pass


def retry_execution(execution):
    """
    基于一条已有执行记录创建重试执行：新记录 + 复制原执行空间的文件。

    Returns:
        Execution: 新建的执行记录（未提交由调用方控制提交时机）
    """
    original_params = {}
    if execution.params:
        try:
            original_params = json.loads(execution.params)
        except (json.JSONDecodeError, TypeError):
            original_params = {}

    new_execution = Execution(
        script_id=execution.script_id,
        environment_id=execution.environment_id,
        status='pending',
        params=json.dumps(original_params) if original_params else None
    )
    db.session.add(new_execution)
    db.session.flush()

    old_space = Config.get_execution_space(execution.id)
    new_space = Config.ensure_execution_space(new_execution.id)

    if os.path.exists(old_space):
        for item in os.listdir(old_space):
            src = os.path.join(old_space, item)
            dst = os.path.join(new_space, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

    return new_execution
