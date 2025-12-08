# serve_with_proxy.py
"""
Usage:
    python serve_with_proxy.py --dir dist --port 3000 --proxy-path /api --backend http://localhost:8000

This serves static files from --dir and proxies requests starting with --proxy-path to --backend.
"""
import argparse
import io
import sys
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urljoin, urlsplit

class ProxyAndStaticHandler(SimpleHTTPRequestHandler):
    backend = "http://localhost:8000"
    proxy_path = "/api"

    def _should_proxy(self):
        # proxy if path starts with proxy_path
        return self.path.startswith(self.proxy_path)

    def _proxy_request(self):
        target = urljoin(self.backend, self.path)
        # Build headers to forward (exclude some hop-by-hop headers)
        headers = {}
        for k, v in self.headers.items():
            if k.lower() in ("host", "connection", "keep-alive", "proxy-authenticate",
                             "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"):
                continue
            headers[k] = v

        data = None
        content_length = self.headers.get("Content-Length")
        if content_length:
            try:
                length = int(content_length)
                data = self.rfile.read(length)
            except Exception:
                data = None

        req = urllib.request.Request(target, data=data, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp_body = resp.read()
                self.send_response(resp.getcode())
                # copy headers
                for key, val in resp.getheaders():
                    # prevent overriding content-length by double-setting; we'll set it from body
                    if key.lower() in ("transfer-encoding", "connection", "keep-alive"):
                        continue
                    self.send_header(key, val)
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                if resp_body:
                    self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, 'read') else b''
            self.send_response(e.code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)
        except Exception as e:
            msg = ("Proxy error: %s\n" % e).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def do_GET(self):
        if self._should_proxy():
            return self._proxy_request()
        return super().do_GET()

    def do_POST(self):
        if self._should_proxy():
            return self._proxy_request()
        return super().do_POST()

    def do_PUT(self):
        if self._should_proxy():
            return self._proxy_request()
        return super().do_PUT()

    def do_DELETE(self):
        if self._should_proxy():
            return self._proxy_request()
        return super().do_DELETE()

    def do_OPTIONS(self):
        if self._should_proxy():
            return self._proxy_request()
        return super().do_OPTIONS()

def run(port, directory, backend, proxy_path):
    handler_class = ProxyAndStaticHandler
    handler_class.backend = backend
    handler_class.proxy_path = proxy_path
    # Python 3.7+: SimpleHTTPRequestHandler accepts directory arg
    try:
        server = HTTPServer(("", port), handler_class)
        handler_class.directory = directory
        print(f"Serving directory '{directory}' on :{port}, proxying '{proxy_path}' to {backend}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="dist", help="directory to serve")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--backend", default="http://localhost:8000", help="backend to proxy to")
    parser.add_argument("--proxy-path", default="/api", help="request path prefix to proxy")
    args = parser.parse_args()
    run(args.port, args.dir, args.backend, args.proxy_path)