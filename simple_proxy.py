#!/usr/bin/env python3
"""
简单的反向代理服务器
同时提供静态文件服务和API代理功能
"""
import http.server
import http.client
import socketserver
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs
import os
import sys

# 配置
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
BACKEND_URL = 'http://localhost:5001'
PORT = 3000


class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            # 处理静态文件和 SPA 路由
            try:
                # 解析路径
                parsed_path = self.path.split('?')[0]  # 移除查询参数

                # 构建完整文件路径
                file_path = os.path.join(FRONTEND_DIR, parsed_path.lstrip('/'))

                # 如果路径是目录，尝试 index.html
                if os.path.isdir(file_path):
                    file_path = os.path.join(file_path, 'index.html')

                # 检查文件是否存在
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    # 文件存在，正常返回
                    super().do_GET()
                else:
                    # 文件不存在，检查是否是静态资源请求
                    # 静态资源（有扩展名）返回404，其他请求返回 index.html（SPA fallback）
                    static_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg',
                                       '.ico', '.woff', '.woff2', '.ttf', '.eot', '.map', '.json']

                    has_extension = any(parsed_path.endswith(ext) for ext in static_extensions)

                    if has_extension:
                        # 静态资源不存在，返回404
                        self.send_error(404, "File not found")
                    else:
                        # 可能是前端路由，返回 index.html
                        self.serve_index_html()

            except (BrokenPipeError, ConnectionResetError):
                # 客户端断开连接，静默处理
                pass
            except Exception as e:
                # 其他错误，记录日志
                print(f"Error serving {self.path}: {e}", file=sys.stderr)

    def serve_index_html(self):
        """返回 index.html 用于 SPA 路由"""
        try:
            index_path = os.path.join(FRONTEND_DIR, 'index.html')
            with open(index_path, 'rb') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving index.html: {e}", file=sys.stderr)
            self.send_error(500, "Internal server error")

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
        # 判断是否是 SSE 流式请求
        is_stream = '/stream' in self.path

        if is_stream:
            self.proxy_stream_request(method)
        else:
            self.proxy_normal_request(method)

    def proxy_stream_request(self, method):
        """代理 SSE 流式请求"""
        print(f"[STREAM PROXY] {method} {self.path}", file=sys.stderr)
        try:
            # 解析后端 URL
            parsed_backend = urlparse(BACKEND_URL)

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # 转发所有必要的headers
            headers = {}
            for key, value in self.headers.items():
                if key in ['Content-Type', 'Authorization']:
                    headers[key] = value

            # 创建连接
            conn = http.client.HTTPConnection(
                parsed_backend.hostname,
                parsed_backend.port or 80,
                timeout=300  # 5分钟超时，支持长连接
            )

            # 发送请求
            conn.request(method, self.path, body=body, headers=headers)

            # 获取响应
            response = conn.getresponse()

            # 发送响应头
            self.send_response(response.status)
            for header, value in response.getheaders():
                if header.lower() not in ['connection', 'transfer-encoding', 'content-length']:
                    self.send_header(header, value)
            self.end_headers()

            # 流式转发响应体
            try:
                while True:
                    chunk = response.read(1024)  # 每次读取 1KB
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()  # 立即刷新，确保实时传输
            except (BrokenPipeError, ConnectionResetError):
                # 客户端断开连接
                pass
            finally:
                conn.close()

        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print(f"Stream proxy error for {self.path}: {e}", file=sys.stderr)
            try:
                self.send_error(500, f"Stream proxy error: {str(e)}")
            except:
                pass

    def proxy_normal_request(self, method):
        """代理普通请求"""
        print(f"[NORMAL PROXY] {method} {self.path}", file=sys.stderr)
        try:
            # 构造后端URL
            backend_url = f"{BACKEND_URL}{self.path}"

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # 构造请求 - 转发所有必要的headers（使用items()遍历）
            headers = {}
            for key, value in self.headers.items():
                if key in ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin']:
                    headers[key] = value

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

        except (BrokenPipeError, ConnectionResetError):
            # 客户端断开连接，静默处理
            pass

        except Exception as e:
            # 处理其他错误
            print(f"Proxy error for {self.path}: {e}", file=sys.stderr)
            try:
                self.send_error(500, f"Proxy error: {str(e)}")
            except:
                pass

    def copyfile(self, source, outputfile):
        """重写 copyfile 方法，添加错误处理"""
        try:
            # 使用小块传输，避免大文件一次性加载到内存
            buffer_size = 16 * 1024  # 16KB
            while True:
                buf = source.read(buffer_size)
                if not buf:
                    break
                outputfile.write(buf)
        except (BrokenPipeError, ConnectionResetError):
            # 客户端断开连接，静默处理
            pass
        except Exception as e:
            print(f"Error copying file: {e}", file=sys.stderr)
            raise

    def log_message(self, format, *args):
        """自定义日志格式"""
        # 过滤掉 BrokenPipeError 相关的日志
        message = format % args
        if 'code 200' in message or 'code 304' in message:
            # 只记录成功的请求
            print(f"{self.address_string()} - [{self.log_date_time_string()}] {message}")
        elif 'code' not in message:
            # 记录没有状态码的消息
            print(f"{self.address_string()} - [{self.log_date_time_string()}] {message}")


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """支持多线程的 TCP 服务器"""
    allow_reuse_address = True
    daemon_threads = True


def main():
    # 使用 ThreadingTCPServer 支持并发请求
    with ThreadingTCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
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