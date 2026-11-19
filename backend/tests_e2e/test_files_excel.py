# -*- coding: utf-8 -*-
"""文件管理 + Excel（上传目录工作簿 + 执行空间工作簿）"""
import io
import time

import openpyxl

from helpers import find_id


def _xlsx_bytes(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Sheet1'
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_file_lifecycle(api):
    import requests
    content = b'e2e file content ' + str(time.time()).encode()
    r = requests.post(f'{api.base}/api/files/upload',
                      files={'file': ('e2e_file.txt', content, 'text/plain')}, timeout=30)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get('code') == 0, str(body)[:200]
    path = body['data']['path'] if 'path' in body.get('data', {}) else body['data'].get('file_path')

    # 列表中可见
    items, _ = api.items(api.get('/files'))
    assert any(f.get('name') == 'e2e_file.txt' for f in items)

    # 更新内容
    resp = api.put('/files/update', {'path': path, 'content': 'updated-by-e2e'})
    api.expect_ok(resp)

    # 下载校验
    r = requests.get(f'{api.base}/api/files/download', params={'path': path}, timeout=30)
    assert b'updated-by-e2e' in r.content

    # 删除
    api.expect_ok(api.delete('/files/delete', params={'path': path}))


def test_excel_standalone_flow(api):
    import requests
    data = _xlsx_bytes([['name', 'score'], ['alice', 90], ['bob', 85]])
    r = requests.post(f'{api.base}/api/files/upload',
                      files={'file': ('e2e_book.xlsx', data,
                                      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
                      timeout=30)
    body = r.json()
    assert body.get('code') == 0, str(body)[:200]
    path = body['data']['path'] if 'path' in body.get('data', {}) else body['data'].get('file_path')

    # 信息
    info = api.get('/excel/info', params={'path': path})
    api.expect_ok(info)
    sheets = api.payload(info).get('sheets', [])
    assert any(s.get('name') == 'Sheet1' for s in sheets)

    # 读 sheet（按索引）
    sheet = api.get('/excel/sheet', params={'path': path, 'sheet': '0'})
    api.expect_ok(sheet)
    data_payload = api.payload(sheet)
    assert data_payload.get('total_rows', 0) >= 3 or data_payload.get('rows')

    # 改名 + 新增 + 删除
    api.expect_ok(api.put('/excel/sheet/rename', {'path': path, 'sheet': '0', 'new_name': 'Data'}))
    api.expect_ok(api.post('/excel/sheet/add', {'path': path, 'name': 'Extra'}))
    sheets2 = api.payload(api.get('/excel/info', params={'path': path})).get('sheets', [])
    names = [s.get('name') for s in sheets2]
    assert 'Data' in names and 'Extra' in names
    api.expect_ok(api.delete('/excel/sheet/delete', params={'path': path, 'sheet': '1'}))

    # 保存单元格
    save = api.post('/excel/save', {'path': path, 'sheet': '0',
                                    'cells': [{'row': 3, 'col': 1, 'value': 'carol'}]})
    api.expect_ok(save)
    api.delete('/files/delete', params={'path': path})


def test_execution_space_excel(api):
    """执行脚本生成 xlsx，再经执行空间 Excel 端点读取/保存"""
    script = api.create_script(code=(
        'import openpyxl\n'
        'wb = openpyxl.Workbook()\n'
        'ws = wb.active\n'
        'ws["A1"] = "metric"\n'
        'ws["B1"] = 123\n'
        'wb.save("report.xlsx")\n'
        'print("xlsx written")\n'
    ))
    detail, exec_id = api.execute_and_wait(script['id'])
    assert detail.get('status') == 'success'

    # 文件列表包含 report.xlsx
    files = api.payload(api.get(f'/executions/{exec_id}/files')).get('files', [])
    assert any(f['name'] == 'report.xlsx' for f in files)

    # Luckysheet 格式读取
    grid = api.get(f'/executions/{exec_id}/files/report.xlsx', params={'excel': 'true'})
    api.expect_ok(grid)
    grid_data = api.payload(grid)
    assert grid_data.get('gridData')

    # 保存回执行空间
    save = api.post(f'/executions/{exec_id}/files/report.xlsx?excel=true',
                    {'gridData': grid_data['gridData']})
    api.expect_ok(save)


def test_execution_file_text_preview(api):
    script = api.create_script(code='open("notes.md", "w").write("# e2e note")\nprint("ok")')
    detail, exec_id = api.execute_and_wait(script['id'])
    assert detail.get('status') == 'success'
    files = api.payload(api.get(f'/executions/{exec_id}/files')).get('files', [])
    notes = next(f for f in files if f['name'] == 'notes.md')
    assert notes['is_text'] is True

    import requests
    r = requests.get(f'{api.base}/api/executions/{exec_id}/files/notes.md', timeout=30)
    assert '# e2e note' in r.text
