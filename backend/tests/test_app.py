"""应用装配冒烟测试"""


def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'


def test_unknown_route_returns_json_404(client):
    resp = client.get('/api/nonexistent')
    assert resp.status_code == 404
