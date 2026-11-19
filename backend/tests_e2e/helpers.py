# -*- coding: utf-8 -*-
"""
E2E 辅助工具：响应解包、执行轮询、脚本/执行快捷构造
"""
import json
import time

import requests

TERMINAL_STATUSES = {'success', 'failed', 'cancelled'}
POLL_TIMEOUT = 90


def find_id(obj):
    """深度优先找第一个 'id' / 'execution_id' 字段（对响应嵌套差异保持弹性）"""
    if isinstance(obj, dict):
        if 'id' in obj and isinstance(obj['id'], int):
            return obj['id']
        if 'execution_id' in obj and isinstance(obj['execution_id'], int):
            return obj['execution_id']
        for v in obj.values():
            r = find_id(v)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_id(v)
            if r is not None:
                return r
    return None


class Api:
    def __init__(self, base_url):
        self.base = base_url
        self.s = requests.Session()

    def _url(self, path):
        return f'{self.base}/api{path}'

    def _handle(self, resp):
        if resp.status_code == 204 or not (resp.text or '').strip():
            return {'code': 0, 'status_code': resp.status_code}
        try:
            return resp.json()
        except ValueError:
            raise AssertionError(f'非 JSON 响应 {resp.status_code}: {resp.text[:300]}')

    # --- 通用动词 ---
    def get(self, path, **kw):
        return self._handle(self.s.get(self._url(path), timeout=30, **kw))

    def post(self, path, json=None, **kw):
        return self._handle(self.s.post(self._url(path), json=json, timeout=60, **kw))

    def put(self, path, json=None, **kw):
        return self._handle(self.s.put(self._url(path), json=json, timeout=60, **kw))

    def delete(self, path, **kw):
        return self._handle(self.s.delete(self._url(path), timeout=30, **kw))

    # --- 语义封装 ---
    def payload(self, resp):
        """{code:0, data:...} -> data；裸列表/其他形状原样返回"""
        if isinstance(resp, dict) and 'data' in resp:
            return resp['data']
        return resp

    def items(self, resp):
        data = self.payload(resp)
        if isinstance(data, dict) and 'items' in data:
            return data['items'], data.get('total')
        if isinstance(data, list):
            return data, len(data)
        return data, None

    def expect_ok(self, resp):
        assert isinstance(resp, dict) and resp.get('code') == 0, \
            f'期望 code=0, 实际: {str(resp)[:300]}'
        return resp

    def create_script(self, name=None, code='print("e2e")', script_type='python', **extra):
        body = {
            'name': name or f'e2e_script_{int(time.time() * 1000) % 10**9}',
            'type': script_type,
            'code': code,
            'description': 'created by e2e',
            **extra,
        }
        resp = self.post('/scripts', body)
        assert resp.get('code') == 0, f'创建脚本失败: {str(resp)[:300]}'
        return self.payload(resp)

    def execute(self, script_id, params=None):
        # 后端从 form 字段读取 params（JSON 字符串）
        return self._handle(self.s.post(
            self._url(f'/scripts/{script_id}/execute'),
            data={'params': json.dumps(params or {})}, timeout=60))

    def execute_and_wait(self, script_id, params=None, timeout=POLL_TIMEOUT):
        resp = self.execute(script_id, params)
        assert resp.get('code') == 0, f'触发执行失败: {str(resp)[:300]}'
        execution_id = find_id(resp)
        return self.wait_execution(execution_id, timeout), execution_id

    def wait_execution(self, execution_id, timeout=POLL_TIMEOUT):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            resp = self.get(f'/executions/{execution_id}')
            data = self.payload(resp)
            last = data
            if data.get('status') in TERMINAL_STATUSES:
                return data
            time.sleep(1)
        raise AssertionError(f'执行 {execution_id} {timeout}s 未到达终态, 最后状态: {last}')

    def wait_workflow_execution(self, wf_exec_id, timeout=POLL_TIMEOUT):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            resp = self.get(f'/workflow-executions/{wf_exec_id}')
            data = self.payload(resp)
            last = data
            if data.get('status') in TERMINAL_STATUSES:
                return data
            time.sleep(1.5)
        raise AssertionError(f'工作流执行 {wf_exec_id} {timeout}s 未到达终态: {last}')

    def read_sse(self, path, max_seconds=20, stop_on=None):
        """读取 SSE 流事件（JSON dict 列表）"""
        url = f'{self.base}/api{path}'
        events = []
        deadline = time.time() + max_seconds
        with self.s.get(url, stream=True, timeout=max_seconds) as r:
            for line in r.iter_lines(decode_unicode=True):
                if time.time() > deadline:
                    break
                if not line or not line.startswith('data: '):
                    continue
                try:
                    evt = json.loads(line[6:])
                except ValueError:
                    continue
                events.append(evt)
                if stop_on and stop_on(evt):
                    break
        return events
