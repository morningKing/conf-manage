"""核心只读 API 端点冒烟测试"""

READ_ENDPOINTS = [
    '/api/scripts',
    '/api/folders/tree',
    '/api/tags',
    '/api/schedules',
    '/api/environments',
    '/api/global-variables',
    '/api/webhooks',
    '/api/ai-configs',
]


def test_read_endpoints(client):
    for endpoint in READ_ENDPOINTS:
        resp = client.get(endpoint)
        assert resp.status_code == 200, f'{endpoint} -> {resp.status_code}: {resp.get_data(as_text=True)[:200]}'


def test_scripts_create_and_list(client):
    # 创建脚本
    resp = client.post('/api/scripts', json={
        'name': 'smoke_test_script',
        'type': 'python',
        'code': 'print("hello")',
        'description': 'created by smoke test',
    })
    assert resp.status_code in (200, 201), resp.get_data(as_text=True)[:300]
    body = resp.get_json()
    script_id = body.get('data', body).get('id')

    # 列表中应能找到
    resp = client.get('/api/scripts')
    items = resp.get_json()
    items = items.get('data', items)
    if isinstance(items, dict):
        items = items.get('items', items.get('scripts', []))
    assert any(s['id'] == script_id for s in items)
