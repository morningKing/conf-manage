# -*- coding: utf-8 -*-
"""健康检查、错误语义与系统端点"""
import requests


def test_health(base_url):
    r = requests.get(f'{base_url}/health', timeout=10)
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_unknown_route_is_json_404(api):
    r = requests.get(f'{api.base}/api/nonexistent', timeout=10)
    assert r.status_code == 404
    body = r.json()
    assert body['code'] == 1
    assert '资源不存在' in body['message']


def test_unknown_api_method_is_405_json(api):
    # /api/scripts 只允许 GET/POST
    r = requests.put(f'{api.base}/api/scripts', json={}, timeout=10)
    assert r.status_code == 405


def test_system_cleanup_config(api):
    resp = api.get('/system/cleanup/config')
    api.expect_ok(resp)
    config = api.payload(resp)
    assert 'threshold' in config


def test_cleanup_threshold_validation(api):
    # 低于下限必须被拒
    resp = api.put('/system/cleanup/config', {'threshold': 1})
    assert resp.get('code') == 1
