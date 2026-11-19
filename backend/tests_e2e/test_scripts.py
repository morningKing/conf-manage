# -*- coding: utf-8 -*-
"""脚本 CRUD / 版本 / 回滚 / 收藏 / 白名单"""
import time


def test_script_lifecycle(api):
    name = f'e2e_lifecycle_{int(time.time() * 1000) % 10**9}'
    created = api.payload(api.post('/scripts', {
        'name': name, 'type': 'python', 'code': 'print("v1")',
        'description': 'v1 desc',
    }))
    sid = created['id']
    try:
        # 详情
        detail = api.payload(api.get(f'/scripts/{sid}'))
        assert detail['name'] == name
        assert detail['version'] == 1

        # 更新代码 → 版本 +1
        api.expect_ok(api.put(f'/scripts/{sid}', {'code': 'print("v2")'}))
        detail = api.payload(api.get(f'/scripts/{sid}'))
        assert detail['code'] == 'print("v2")'
        assert detail['version'] == 2

        # 仅改描述 → 不新建版本
        api.expect_ok(api.put(f'/scripts/{sid}', {'description': 'v2 desc'}))
        assert api.payload(api.get(f'/scripts/{sid}'))['version'] == 2

        # 版本列表
        versions = api.payload(api.get(f'/scripts/{sid}/versions'))
        assert isinstance(versions, list) and len(versions) >= 2

        # 回滚到版本 1
        api.expect_ok(api.post(f'/scripts/{sid}/rollback/1'))
        detail = api.payload(api.get(f'/scripts/{sid}'))
        assert detail['code'] == 'print("v1")'

        # 收藏切换
        fav1 = api.payload(api.post(f'/scripts/{sid}/favorite'))
        fav2 = api.payload(api.post(f'/scripts/{sid}/favorite'))
        assert fav1['is_favorite'] != fav2['is_favorite']

        # 白名单切换
        pres = api.payload(api.post(f'/scripts/{sid}/preserve'))
        assert 'preserve' in pres

        # 重命名（无冲突）
        api.expect_ok(api.put(f'/scripts/{sid}', {'name': name + '_renamed'}))

        # 列表中能找到
        items, _ = api.items(api.get('/scripts'))
        assert any(s['id'] == sid for s in items)
    finally:
        api.delete(f'/scripts/{sid}')


def test_duplicate_script_name_rejected(api):
    name = f'e2e_dup_{int(time.time() * 1000) % 10**9}'
    created = api.create_script(name=name)
    try:
        resp = api.post('/scripts', {'name': name, 'type': 'python', 'code': 'x'})
        assert resp.get('code') == 1
    finally:
        api.delete(created['id'])


def test_script_update_to_existing_name_rejected(api):
    a = api.create_script()
    b = api.create_script()
    try:
        resp = api.put(f"/scripts/{b['id']}", {'name': a['name']})
        assert resp.get('code') == 1
    finally:
        api.delete(a['id'])
        api.delete(b['id'])
