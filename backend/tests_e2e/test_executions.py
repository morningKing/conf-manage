# -*- coding: utf-8 -*-
"""脚本执行全链路：成功/失败/JS/文件上传/重执行/取消/SSE/统计"""
import json
import time

import requests

from helpers import find_id

LONG_SLEEP_CODE = 'import time\nprint("started")\ntime.sleep(60)\n'


def test_python_execution_success(api, base_url):
    script = api.create_script(code=(
        'import os, sys\n'
        'print("hello e2e")\n'
        'print("PARAM:", os.environ.get("E2E_PARAM", ""))\n'
        'print("GLOBAL:", os.environ.get("E2E_GREETING", ""))\n'
        'with open("out_result.txt", "w") as f:\n'
        '    f.write("done")\n'
    ))
    detail, exec_id = api.execute_and_wait(script['id'], {'E2E_PARAM': 'abc123'})
    assert detail.get('status') == 'success'
    assert 'hello e2e' in (detail['output'] or '')

    detail = api.payload(api.get(f'/executions/{exec_id}'))
    assert detail['output'] and 'PARAM: abc123' in detail['output']

    # 日志文件落盘
    log_file = detail.get('log_file')
    assert log_file


def test_execution_param_types(api):
    # multiselect 列表值 → 逗号分隔；switch 布尔 → true/false（依据脚本参数定义转换）
    import json as _json
    script = api.create_script(code=(
        'import os\n'
        'print("TAGS:", os.environ.get("TAGS", ""))\n'
        'print("SWITCH:", os.environ.get("SWITCH", ""))\n'
    ), parameters=_json.dumps([
        {'key': 'TAGS', 'type': 'multiselect',
         'options': [{'value': 'a', 'label': 'A'},
                     {'value': 'b', 'label': 'B'},
                     {'value': 'c', 'label': 'C'}]},
        {'key': 'SWITCH', 'type': 'switch'},
    ]))
    detail, _ = api.execute_and_wait(script['id'], {
        'TAGS': ['a', 'b', 'c'],
        'SWITCH': True,
    })
    assert 'TAGS: a,b,c' in detail['output']
    assert 'SWITCH: true' in detail['output']


def test_execution_failure_path(api):
    script = api.create_script(code='raise SystemExit("boom-e2e")')
    detail, _ = api.execute_and_wait(script['id'])
    assert detail.get('status') == 'failed'
    assert detail.get('error')


def test_javascript_execution(api):
    script = api.create_script(code=(
        'console.log("hello from node", process.env.E2E_JS_PARAM);\n'
    ), script_type='javascript')
    detail, _ = api.execute_and_wait(script['id'], {'E2E_JS_PARAM': 'js-ok'})
    assert 'hello from node js-ok' in (detail['output'] or '')


def test_execution_with_uploaded_files(api):
    script = api.create_script(code=(
        'import os, json\n'
        'names = json.loads(os.environ.get("FILES", "[]"))\n'
        'print("FILES:", names)\n'
        'for n in names:\n'
        '    with open(n) as f:\n'
        '        print(n, "content:", f.read().strip())\n'
    ))
    # FormData 上传执行
    files = {'files': ('e2e_input.txt', b'e2e-file-body', 'text/plain')}
    fields = {'params': json.dumps({})}
    r = requests.post(
        f'{api.base}/api/scripts/{script["id"]}/execute',
        data=fields, files=files, timeout=60)
    body = r.json()
    assert body.get('code') == 0, str(body)[:300]
    exec_id = find_id(body)
    status = api.wait_execution(exec_id)
    assert 'FILES:' in (status['output'] or '')
    assert 'e2e_input.txt content: e2e-file-body' in status['output']


def test_execution_sse_stream(base_url):
    client = api_for(base_url)
    script = client.create_script(code=(
        'import time\n'
        'for i in range(3):\n'
        '    print(f"line {i}", flush=True)\n'
        '    time.sleep(0.8)\n'
    ))
    resp = client.execute(script['id'])
    exec_id = find_id(resp)

    events = client.read_sse(
        f'/executions/{exec_id}/logs/stream', max_seconds=40,
        stop_on=lambda e: e.get('type') == 'status')
    types = [e.get('type') for e in events]
    assert 'status' in types, f'SSE 未收到完成事件: {types[-5:]}'
    log_events = [e for e in events if e.get('type') == 'log']
    assert log_events, 'SSE 未收到日志事件'
    assert any('line 2' in e.get('content', '') for e in log_events)


def api_for(base_url):
    from helpers import Api
    return Api(base_url)


def test_reexecute_creates_new_execution(api):
    script = api.create_script(code='print("reexec")')
    detail, first_id = api.execute_and_wait(script['id'])
    assert detail.get('status') == 'success'

    resp = api.post(f'/executions/{first_id}/re-execute')
    api.expect_ok(resp)
    new_id = api.payload(resp).get('new_execution_id')
    assert new_id and new_id != first_id
    api.wait_execution(new_id)


def test_cancel_running_execution(api):
    script = api.create_script(code=LONG_SLEEP_CODE)
    resp = api.execute(script['id'])
    exec_id = find_id(resp)

    # 等待进入 running
    deadline = time.time() + 30
    while time.time() < deadline:
        st = api.payload(api.get(f'/executions/{exec_id}'))
        if st.get('status') == 'running':
            break
        time.sleep(0.5)
    assert st.get('status') == 'running', st

    api.expect_ok(api.post(f'/executions/{exec_id}/cancel'))
    deadline = time.time() + 30
    while time.time() < deadline:
        st = api.payload(api.get(f'/executions/{exec_id}'))
        if st.get('status') in ('failed', 'cancelled'):
            break
        time.sleep(0.5)
    assert st.get('status') in ('failed', 'cancelled'), st
    # 进程确实在 60s 睡眠结束前被终止（终态与结束时间已落库）
    assert st.get('end_time'), '取消后应记录结束时间'


def test_executions_statistics(api):
    resp = api.get('/executions/statistics')
    api.expect_ok(resp)
    stats = api.payload(resp)
    assert 'summary' in stats and 'total' in stats['summary']


def test_batch_manage_delete(api):
    script = api.create_script(code='print("batch")')
    ids = []
    for _ in range(2):
        _, exec_id = api.execute_and_wait(script['id'])
        ids.append(exec_id)
    resp = api.post('/executions/batch', {
        'action': 'delete', 'execution_ids': ids,
    })
    api.expect_ok(resp)
    result = api.payload(resp)
    assert result['success'] == 2

    # 删除后详情 404
    r = requests.get(f'{api.base}/api/executions/{ids[0]}', timeout=10)
    assert r.status_code == 404
