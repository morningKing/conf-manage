# -*- coding: utf-8 -*-
"""定时任务：CRUD / 立即运行（app context 修复验证）/ 白名单"""
import time


def test_schedule_lifecycle_and_run_now(api):
    script = api.create_script(code='print("from schedule")')
    sid = script['id']
    name = f'e2e_sched_{int(time.time() * 1000) % 10**9}'
    try:
        created = api.payload(api.post('/schedules', {
            'name': name,
            'script_id': sid,
            'cron': '0 3 * * *',
            'params': '',
            'enabled': True,
        }))
        sched_id = created['id']
        assert created['cron'] == '0 3 * * *'

        # 立即运行：线程需携带 app context（曾为损坏路径）
        resp = api.post(f'/schedules/{sched_id}/run')
        api.expect_ok(resp)
        run_detail = api.payload(resp)
        exec_id = run_detail.get('id') or run_detail.get('execution_id')
        assert exec_id
        status = api.wait_execution(exec_id)
        assert status.get('status') == 'success'
        assert 'from schedule' in (status.get('output') or '')

        # 启用/禁用
        toggled = api.payload(api.post(f'/schedules/{sched_id}/toggle'))
        assert toggled['enabled'] is False
        toggled = api.payload(api.post(f'/schedules/{sched_id}/toggle'))
        assert toggled['enabled'] is True

        # 白名单
        pres = api.payload(api.post(f'/schedules/{sched_id}/preserve'))
        assert 'preserve' in pres

        # 列表
        items, _ = api.items(api.get('/schedules'))
        assert any(s['id'] == sched_id for s in items)

        # 删除
        api.expect_ok(api.delete(f'/schedules/{sched_id}'))
    finally:
        api.delete(sid)


def test_schedule_validation(api):
    script = api.create_script()
    # 缺 cron
    resp = api.post('/schedules', {'name': 'x', 'script_id': script['id']})
    assert resp.get('code') == 1
    # 不存在的脚本
    resp = api.post('/schedules', {'name': 'x', 'script_id': 999999, 'cron': '0 0 * * *'})
    assert resp.get('code') == 1
    api.delete(script['id'])
