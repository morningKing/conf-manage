#!/usr/bin/env python3
"""
简单的反向代理服务器
同时提供静态文件服务和API代理功能
"""
import http.server
import socketserver
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs
import os

# 配置
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
BACKEND_URL = 'http://localhost:5000'
PORT = 3000


class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            self.send_error(404)

    def do_PUT(self):
        if self.path.startswith('/api/'):
            self.proxy_request('PUT')
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.proxy_request('DELETE')
        else:
            self.send_error(404)

    def proxy_request(self, method):
        """代理请求到后端"""
        try:
            # 构造后端URL
            backend_url = f"{BACKEND_URL}{self.path}"

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # 构造请求
            headers = {
                'Content-Type': self.headers.get('Content-Type', 'application/json')
            }

            req = urllib.request.Request(
                backend_url,
                data=body,
                headers=headers,
                method=method
            )

            # 发送请求
            with urllib.request.urlopen(req, timeout=30) as response:
                # 返回响应
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())

        except urllib.error.HTTPError as e:
            # 处理HTTP错误
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(e.read())

        except Exception as e:
            # 处理其他错误
            self.send_error(500, f"Proxy error: {str(e)}")

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}")


def main():
    with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"反向代理服务器启动在 http://localhost:{PORT}")
        print(f"静态文件目录: {FRONTEND_DIR}")
        print(f"API代理到: {BACKEND_URL}")
        print("按 Ctrl+C 停止服务器")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")


if __name__ == "__main__":
    main()
