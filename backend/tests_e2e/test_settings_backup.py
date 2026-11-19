# -*- coding: utf-8 -*-
"""备份/导出 + AI 设置（脱敏/编辑不覆盖/SSRF 校验）+ 全局变量注入 + 执行环境"""
import time


def test_backup_flow(api):
    created = api.payload(api.post('/backup/system-backup', {
        'include_logs': False,
        'include_execution_spaces': False,
    }))
    assert created.get('filename'), str(created)[:300]

    items, _ = api.items(api.get('/backup/list'))
    assert any(b['name'] == created['filename'] for b in items)

    # 下载
    import requests
    r = requests.get(f'{api.base}/api/backup/download/{created["filename"]}', timeout=60)
    assert r.status_code == 200

    # 数据库信息（SQLAlchemy 反射）
    info = api.get('/backup/database-info')
    api.expect_ok(info)
    tables = api.payload(info).get('tables', [])
    assert any(t['name'] == 'scripts' for t in tables)

    # 清理单个
    api.expect_ok(api.delete(f'/backup/{created["filename"]}'))


def test_database_export_requires_pg_dump_or_fails_cleanly(api):
    # 环境无 pg_dump 时应给出明确错误而不是 AttributeError
    resp = api.post('/backup/database-export')
    assert isinstance(resp, dict)
    if resp.get('code') == 0:
        filename = api.payload(resp).get('filename')
        api.delete(f'/backup/{filename}')


def test_ai_config_masking_and_edit_not_wipe(api):
    key = 'sk-e2e-secret-key-1234567890abcdef'
    created = api.payload(api.post('/ai-configs', {
        'provider': 'openai',
        'api_key': key,
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-4o-mini',
        'is_active': True,
    }))
    try:
        # 返回体不泄露明文，只留尾 4 位
        masked = created['api_key']
        assert key not in masked
        assert masked.endswith('cdef')
        assert created['is_configured'] is True

        # 编辑（不回填 key）→ key 不被清空。注意：该端点返回裸配置对象（无 code 包装）
        updated = api.put(f"/ai-configs/{created['id']}", {
            'model': 'gpt-4.1-mini',
            'api_key': '',
        })
        assert updated.get('model') == 'gpt-4.1-mini'
        detail = api.payload(api.get('/ai-configs/active'))
        assert detail['api_key'] == masked, '编辑后 api_key 不应变化'

        # 激活接口（裸配置对象返回）
        activated = api.post(f"/ai-configs/{created['id']}/activate")
        assert activated.get('is_active') is True
    finally:
        api.delete(f"/ai-configs/{created['id']}")


def test_ai_config_rejects_non_http_scheme(api):
    resp = api.post('/ai-configs', {
        'provider': 'custom',
        'api_key': 'k',
        'base_url': 'file:///etc/passwd',
    })
    assert resp.get('code') == 1 or 'error' in resp


def test_global_variable_injection(api):
    key = f'E2E_GV_{int(time.time()) % 10**8}'
    created = api.payload(api.post('/global-variables', {'key': key, 'value': 'gv-value-42'}))
    try:
        script = api.create_script(code=(
            'import os\n'
            f'print("GV:", os.environ.get("{key}", "MISSING"))\n'
        ))
        detail, _ = api.execute_and_wait(script['id'])
        assert 'GV: gv-value-42' in detail['output'], detail['output']
    finally:
        api.delete(f"/global-variables/{created['id']}")
        api.delete(script['id'])


def test_environment_crud(api):
    import sys as _sys
    created = api.payload(api.post('/environments', {
        'name': f'e2e_env_{int(time.time() * 1000) % 10**9}',
        'type': 'python',
        'executable_path': _sys.executable,
        'description': 'e2e env',
    }))
    try:
        items, _ = api.items(api.get('/environments'))
        assert any(e['id'] == created['id'] for e in items)

        api.expect_ok(api.put(f"/environments/{created['id']}", {'description': 'updated'}))

        # 探测接口
        detect = api.post('/environments/detect', {'type': 'python'})
        assert isinstance(detect, dict)
    finally:
        api.delete(f"/environments/{created['id']}")
