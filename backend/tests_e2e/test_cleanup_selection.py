# -*- coding: utf-8 -*-
"""清理链路（直连种子数据）+ 选择会话批量"""
import time

import psycopg2

from dbsetup import build_pg_url, E2E_DB_NAME, PG_HOST, PG_PORT, PG_USER, PG_PASSWORD


def _seed_executions(n, script_id, minutes_ago=2880):
    try:
        conn = psycopg2.connect(build_pg_url(E2E_DB_NAME), connect_timeout=3)
        conn.close()
    except Exception:
        pytest.skip('清理种子数据测试需要 PostgreSQL E2E 库')
    """直连 E2E 库插入历史执行记录（绕过逐条真实执行的成本）"""
    conn = psycopg2.connect(build_pg_url(E2E_DB_NAME))
    cur = conn.cursor()
    for _ in range(n):
        cur.execute(
            "INSERT INTO executions (script_id, status, progress, created_at) "
            "VALUES (%s, 'success', 100, now() - (%s || ' minutes')::interval)",
            (script_id, str(minutes_ago)))
    conn.commit()
    cur.close()
    conn.close()


def test_cleanup_respects_threshold_and_whitelist(api):
    # 收紧阈值（仅运行时生效，服务进程内全局生效）
    api.expect_ok(api.put('/system/cleanup/config', {'threshold': 50}))

    keeper = api.create_script(code='print("keeper")')
    api.expect_ok(api.post(f"/scripts/{keeper['id']}/preserve"))  # 白名单
    victim = api.create_script(code='print("victim")')

    try:
        _seed_executions(30, keeper['id'])
        _seed_executions(60, victim['id'])  # 非白名单需超过阈值 50 才会触发清理

        stats_before = api.payload(api.get('/system/cleanup/stats'))
        assert stats_before['total_executions'] >= 90

        result = api.payload(api.post('/system/cleanup'))
        assert result['deleted_executions'] >= 10, result

        # 白名单脚本的执行记录必须全部保留，非白名单超出阈值部分被清理
        stats_after = api.payload(api.get('/system/cleanup/stats'))
        assert stats_after['total_executions'] < stats_before['total_executions']
        assert stats_after['whitelisted_executions'] >= 30
    finally:
        api.expect_ok(api.put('/system/cleanup/config', {'threshold': 500}))
        api.delete(keeper['id'])
        api.delete(victim['id'])


def test_selection_batch_flow(api):
    script = api.create_script(code='print("selection")')
    ids = []
    try:
        for _ in range(2):
            _, exec_id = api.execute_and_wait(script['id'])
            ids.append(exec_id)

        session = api.payload(api.post('/executions/selection/create'))
        session_id = session.get('session_id') or session.get('id')

        api.expect_ok(api.post(f'/executions/selection/{session_id}/add',
                               {'execution_ids': ids}))
        current = api.payload(api.get(f'/executions/selection/{session_id}'))
        current_ids = set(current.get('ids') or current.get('execution_ids') or [])
        assert set(ids) <= current_ids, current

        api.expect_ok(api.post(f'/executions/selection/{session_id}/remove',
                               {'execution_ids': ids[:1]}))

        # 批量删除会话内全部
        resp = api.post(f'/executions/selection/{session_id}/delete')
        api.expect_ok(resp)
    finally:
        api.delete(script['id'])
