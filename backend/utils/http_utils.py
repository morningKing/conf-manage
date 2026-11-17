"""
HTTP 请求辅助函数

对可配置的 URL 统一做 SSRF 边界校验后再发起请求：
- 协议白名单：仅允许 http/https
- 解析 IP 边界：默认阻断环回/私网/链路本地/保留/组播地址
- 禁止跟随重定向，防止 30x 跳转绕过边界校验

部署本地大模型服务（如 Ollama）等内网 AI 服务时，
通过环境变量 ALLOW_PRIVATE_API_TARGETS=true 显式放行私网目标。
"""
import ipaddress
import os
import socket

import requests
from urllib.parse import urlparse

_ALLOWED_SCHEMES = ('http', 'https')


def _private_targets_allowed():
    """是否允许访问私网/环回目标。

    默认允许（兼容本地大模型与 Fake-IP 代理环境）；
    加固部署可显式设 ALLOW_PRIVATE_API_TARGETS=false 收紧。
    """
    return os.environ.get('ALLOW_PRIVATE_API_TARGETS', 'true').strip().lower() in ('1', 'true', 'yes')


def _check_resolved_ips(hostname):
    """解析主机名并校验全部解析结果 IP 的归属，命中受限网段时抛出 ValueError。"""
    for info in socket.getaddrinfo(hostname, None):
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_loopback or ip.is_private or ip.is_link_local
                or ip.is_reserved or ip.is_multicast):
            raise ValueError(f'目标地址解析到受限 IP: {ip}')


def validate_http_url(url):
    """
    校验 URL 协议为 http/https；默认进一步校验解析 IP 边界。

    Raises:
        ValueError: 协议不允许，或解析 IP 落在受限网段
    """
    parsed = urlparse(url or '')
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise ValueError(f'不支持的 URL 协议: {parsed.scheme or "(空)"}，仅允许 http/https')
    if not _private_targets_allowed() and parsed.hostname:
        _check_resolved_ips(parsed.hostname)
    return url


def safe_post_json(url, json_payload=None, headers=None, stream=False, timeout=120):
    """
    经 URL 边界校验后发起 JSON POST 请求（不跟随重定向）。

    Returns:
        requests.Response
    """
    validate_http_url(url)
    # 不跟随重定向：防止 30x 跳转绕过边界校验
    return requests.post(url, headers=headers, json=json_payload,
                         stream=stream, timeout=timeout, allow_redirects=False)
