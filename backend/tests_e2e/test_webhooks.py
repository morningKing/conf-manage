# -*- coding: utf-8 -*-
"""Webhook：创建/触发（token 校验）/日志/Token 重生成"""
import time

from helpers import find_id


def test_webhook_trigger_with_token(api):
    script = api.create_script(code=(
        'import json, os\n'
        'req = json.load(open("webhook_request.json")) if os.path.exists("webhook_request.json") else {}\n'
        'print("BODY:", json.dumps(req.get("body", {}), ensure_ascii=False))\n'
    ))
    name = f'e2e_wh_{int(time.time() * 1000) % 10**9}'
    created = api.payload(api.post('/webhooks', {
        'name': name,
        'script_id': script['id'],
        'description': 'e2e webhook',
        'token_enabled': True,
        'async_mode': False,
    }))
    try:
        key = created['webhook_key']
        token = created['token']

        # 无 token → 401
        import requests
        r = requests.post(f'{api.base}/api/webhook/{key}', json={'hello': 'no-token'}, timeout=30)
        assert r.status_code == 401

        # 正确 token → 触发成功并同步执行
        url = f'{api.base}/api/webhook/{key}'
        import requests
        resp = requests.post(url, json={'value': 42},
                             headers={'Authorization': f'Bearer {token}'}, timeout=60)
        assert resp.status_code in (200, 202), resp.text[:300]
        body = resp.json()
        assert body.get('code') == 0, str(body)[:300]
        exec_id = find_id(body)
        assert exec_id

        status = api.wait_execution(exec_id)
        assert status.get('status') == 'success'
        assert 'value' in (status.get('output') or '')

        # 调用日志
        logs = api.payload(api.get(f'/webhooks/{created["id"]}/logs'))
        items = logs if isinstance(logs, list) else logs.get('items', [])
        assert items, 'webhook 调用日志为空'
    finally:
        api.delete(f"/webhooks/{created['id']}")
        api.delete(script['id'])


def test_webhook_token_regenerate(api):
    script = api.create_script()
    created = api.payload(api.post('/webhooks', {
        'name': f'e2e_wh_regen_{int(time.time() * 1000) % 10**9}',
        'script_id': script['id'],
        'token_enabled': True,
    }))
    try:
        old_token = created['token']
        resp = api.post(f"/webhooks/{created['id']}/regenerate-token")
        api.expect_ok(resp)
        data = api.payload(resp)
        new_token = data.get('token') or data.get('data', {}).get('token')
        assert new_token and new_token != old_token
    finally:
        api.delete(f"/webhooks/{created['id']}")
        api.delete(script['id'])


def test_webhook_without_token_enabled(api):
    script = api.create_script(code='print("open webhook")')
    created = api.payload(api.post('/webhooks', {
        'name': f'e2e_wh_open_{int(time.time() * 1000) % 10**9}',
        'script_id': script['id'],
        'token_enabled': False,
        'async_mode': False,
    }))
    try:
        key = created['webhook_key']
        import requests
        resp = requests.post(f'{api.base}/api/webhook/{key}', json={'open': True}, timeout=60)
        assert resp.status_code in (200, 202)
        body = resp.json()
        assert body.get('code') == 0, str(body)[:300]
        exec_id = find_id(body)
        status = api.wait_execution(exec_id)
        assert status.get('status') == 'success'
        assert 'open webhook' in (status.get('output') or '')
    finally:
        api.delete(f"/webhooks/{created['id']}")
        api.delete(script['id'])
