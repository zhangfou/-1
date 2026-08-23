from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen
import argparse
import webbrowser


ROOT = Path(__file__).resolve().parent
HOP_BY_HOP_HEADERS = {
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailer',
    'transfer-encoding',
    'upgrade',
}
REQUEST_HEADERS_TO_DROP = HOP_BY_HOP_HEADERS | {
    'accept-encoding',
    'content-length',
    'host',
    'origin',
    'referer',
}


class GatewayHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        self._dispatch('GET')

    def do_HEAD(self):
        self._dispatch('HEAD')

    def do_POST(self):
        self._dispatch('POST')

    def do_PUT(self):
        self._dispatch('PUT')

    def do_PATCH(self):
        self._dispatch('PATCH')

    def do_DELETE(self):
        self._dispatch('DELETE')

    def do_OPTIONS(self):
        if urlsplit(self.path).path == '/proxy':
            self.send_response(204)
            self._send_cors_headers()
            self.end_headers()
            return
        super().do_OPTIONS()

    def _dispatch(self, method):
        if urlsplit(self.path).path == '/proxy':
            self._proxy_request(method)
            return
        if method == 'GET':
            super().do_GET()
        elif method == 'HEAD':
            super().do_HEAD()
        else:
            self.send_error(405, 'Method Not Allowed')

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def _send_text_error(self, status, message):
        payload = message.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _proxy_request(self, method):
        query = parse_qs(urlsplit(self.path).query)
        target = query.get('url', [''])[0]
        target_parts = urlsplit(target)
        if target_parts.scheme not in ('http', 'https') or not target_parts.netloc:
            self._send_text_error(400, 'Missing or invalid ?url= target')
            return

        body = None
        if method not in ('GET', 'HEAD'):
            try:
                content_length = int(self.headers.get('Content-Length', '0') or 0)
            except ValueError:
                content_length = 0
            body = self.rfile.read(content_length) if content_length else None

        headers = {}
        for name, value in self.headers.items():
            if name.lower() not in REQUEST_HEADERS_TO_DROP:
                headers[name] = value
        headers['Accept-Encoding'] = 'identity'

        request = Request(target, data=body, headers=headers, method=method)
        try:
            upstream = urlopen(request, timeout=180)
        except HTTPError as error:
            upstream = error
        except (URLError, OSError, ValueError) as error:
            self._send_text_error(502, f'Upstream request failed: {error}')
            return

        self.close_connection = True
        status = getattr(upstream, 'status', upstream.getcode())
        self.send_response(status)
        for name, value in upstream.headers.items():
            lower_name = name.lower()
            if lower_name in HOP_BY_HOP_HEADERS or lower_name in {'content-length', 'content-encoding'}:
                continue
            self.send_header(name, value)
        self.send_header('Connection', 'close')
        self._send_cors_headers()
        self.end_headers()

        if method == 'HEAD':
            upstream.close()
            return

        try:
            while True:
                chunk = upstream.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        finally:
            upstream.close()


def main():
    parser = argparse.ArgumentParser(description='RP Hub local static server and API gateway')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), GatewayHandler)
    print(f'RP Hub gateway: http://localhost:{args.port}')
    print(f'Proxy endpoint: http://localhost:{args.port}/proxy?url=')
    if args.host == '0.0.0.0':
        print('LAN access is enabled. Use this computer\'s LAN IP from another device.')
    if args.open:
        webbrowser.open(f'http://localhost:{args.port}/')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
