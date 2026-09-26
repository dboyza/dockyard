"""A small supplied dashboard backed by real Prometheus query responses."""
import json
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/':
                content = Path('metrics-dashboard.html').read_bytes()
                mime = 'text/html; charset=utf-8'
            elif self.path == '/data':
                config = json.loads(Path('/dashboard/dashboard.json').read_text())
                output = {'title': config['title'], 'observed_at': time.time(), 'panels': []}
                for panel in config['panels'][:8]:
                    query = urllib.parse.urlencode({'query': panel['query'], 'start': time.time()-180, 'end': time.time(), 'step': 5})
                    with urllib.request.urlopen('http://prometheus:9090/api/v1/query_range?' + query, timeout=5) as response:
                        result = json.load(response)
                    output['panels'].append({**panel, 'data': result.get('data', {}).get('result', []), 'status': result['status']})
                content = json.dumps(output).encode()
                mime = 'application/json'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(content)
        except (OSError, ValueError, KeyError) as error:
            self.send_error(503, 'Metrics are temporarily unavailable')
            print(json.dumps({'event': 'dashboard_unavailable', 'type': type(error).__name__}), flush=True)


ThreadingHTTPServer(('0.0.0.0', 8081), Handler).serve_forever()
