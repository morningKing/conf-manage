# -*- coding: utf-8 -*-
"""工作流：创建/执行/状态流/模板"""
import time

from helpers import find_id


def _make_workflow(api, prefix):
    s1 = api.create_script(code='print("wf step 1")')
    s2 = api.create_script(code='print("wf step 2")')
    name = f'{prefix}_{int(time.time() * 1000) % 10**9}'
    nodes = [
        {'node_id': 'node_1', 'node_type': 'script', 'script_id': s1['id'],
         'config': {}, 'position': {'x': 100, 'y': 100}},
        {'node_id': 'node_2', 'node_type': 'script', 'script_id': s2['id'],
         'config': {}, 'position': {'x': 300, 'y': 100}},
    ]
    edges = [{'edge_id': 'edge_1', 'source': 'node_1', 'target': 'node_2'}]
    created = api.payload(api.post('/workflows', {
        'name': name, 'description': 'e2e workflow',
        'nodes': nodes, 'edges': edges, 'enabled': True,
    }))
    return created, s1, s2


def test_workflow_lifecycle_and_execution(api):
    wf, s1, s2 = _make_workflow(api, 'e2e_wf')
    try:
        # 详情含节点/边
        detail = api.payload(api.get(f"/workflows/{wf['id']}"))
        node_ids = [n['node_id'] for n in detail['nodes']]
        assert set(node_ids) == {'node_1', 'node_2'}
        assert len(detail['edges']) == 1

        # 更新图（替换节点）
        detail['nodes'][1]['position'] = {'x': 400, 'y': 200}
        api.expect_ok(api.put(f"/workflows/{wf['id']}", {
            'nodes': detail['nodes'], 'edges': detail['edges'],
        }))
        updated = api.payload(api.get(f"/workflows/{wf['id']}"))
        node2 = next(n for n in updated['nodes'] if n['node_id'] == 'node_2')
        assert node2['position']['x'] == 400

        # 执行
        resp = api.post(f"/workflows/{wf['id']}/execute", {'params': {}})
        api.expect_ok(resp)
        wf_exec_id = find_id(resp)
        assert wf_exec_id

        # 轮询到终态
        result = api.wait_workflow_execution(wf_exec_id)
        assert result['status'] == 'success'
        node_execs = result.get('node_executions') or []
        if node_execs:
            assert all(ne.get('status') == 'success' for ne in node_execs), node_execs

        # 状态 SSE 流（终态后连接应能收到 complete）
        events = api.read_sse(f'/workflow-executions/{wf_exec_id}/stream',
                              max_seconds=20, stop_on=lambda e: e.get('type') == 'complete')
        assert any(e.get('type') == 'complete' for e in events), f'SSE 事件: {[e.get("type") for e in events]}'

        # 执行历史列表
        items, _ = api.items(api.get('/workflow-executions'))
        assert any(e['id'] == wf_exec_id for e in items)

        # toggle
        toggled = api.payload(api.post(f"/workflows/{wf['id']}/toggle"))
        assert toggled['enabled'] is False
    finally:
        api.delete(f"/workflows/{wf['id']}")
        api.delete(s1['id'])
        api.delete(s2['id'])


def test_workflow_template_flow(api):
    s = api.create_script(code='print("template node")')
    try:
        created = api.payload(api.post('/workflow-templates', {
            'name': f'e2e_tpl_{int(time.time() * 1000) % 10**9}',
            'description': 'e2e template',
            'category': 'e2e',
            'template_config': {
                'nodes': [{'node_id': 'node_1', 'node_type': 'script', 'script_id': s['id'],
                           'config': {}, 'position': {'x': 0, 'y': 0}}],
                'edges': [],
            },
        }))
        # 该端点返回裸模板对象（无 code 包装）
        tpl_id = created.get('id') or find_id(created)

        items, _ = api.items(api.get('/workflow-templates'))
        assert any(t['id'] == tpl_id for t in items)

        # 使用模板：端点返回模板配置（由前端据此创建工作流），不直接建工作流
        resp = api.post(f'/workflow-templates/{tpl_id}/use', {'name': f'e2e_from_tpl_{time.time()}'})
        api.expect_ok(resp)
        used_text = str(api.payload(resp))
        assert 'node_1' in used_text, f'模板配置未返回节点: {used_text[:200]}'

        api.expect_ok(api.delete(f'/workflow-templates/{tpl_id}'))
    finally:
        api.delete(s['id'])
