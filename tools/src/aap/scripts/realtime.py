#!/usr/bin/env python3
"""
Realtime SSE viewer for token streaming.

Opens a browser-viewable page that streams the dashboard HTML token-by-token
using Server-Sent Events, rendering progressively in an iframe.

Usage: uv run --project python ag-realtime [--port 8080] [--tokenizer gpt2] [--delay 20]
"""
import argparse
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from aap import make_tokenizer, HF_TOKENIZERS, TT_ENCODINGS
from aap.assets import load_dashboard

VIEWER_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Artifact Generator — Realtime Viewer</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, -apple-system, sans-serif; background: #0f1117; color: #e0e0e0; height: 100vh; display: flex; flex-direction: column; }
  .toolbar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: #1a1d27; border-bottom: 1px solid #2a2d3a; flex-shrink: 0; flex-wrap: wrap; }
  .toolbar label { font-size: 13px; color: #9ca3af; }
  .toolbar select, .toolbar input[type=range] { background: #2a2d3a; color: #e0e0e0; border: 1px solid #3a3d4a; border-radius: 4px; padding: 4px 8px; font-size: 13px; }
  .toolbar select { min-width: 180px; }
  .toolbar input[type=range] { width: 120px; accent-color: #6366f1; }
  .toolbar button { background: #6366f1; color: #fff; border: none; border-radius: 4px; padding: 6px 16px; font-size: 13px; cursor: pointer; font-weight: 600; }
  .toolbar button:hover { background: #4f46e5; }
  .toolbar button.stop { background: #ef4444; }
  .toolbar button.stop:hover { background: #dc2626; }
  .stats { margin-left: auto; font-size: 12px; color: #9ca3af; font-variant-numeric: tabular-nums; display: flex; gap: 16px; }
  .stats span { white-space: nowrap; }
  iframe { flex: 1; border: none; background: #fff; }
</style>
</head>
<body>
<div class="toolbar">
  <label>Tokenizer
    <select id="tok">
      <option>gpt2</option>
      <option>bert-base-uncased</option>
      <option>google/gemma-3-1b-it</option>
      <option>o200k_base</option>
      <option>cl100k_base</option>
    </select>
  </label>
  <label>Delay <span id="delayVal">20</span>ms
    <input type="range" id="delay" min="0" max="100" value="20">
  </label>
  <button id="btn" onclick="toggle()">Start</button>
  <div class="stats">
    <span id="sTok">Tokens: 0</span>
    <span id="sTime">Elapsed: 0.0s</span>
    <span id="sRate">0 tok/s</span>
  </div>
</div>
<iframe id="frame"></iframe>
<script>
let es = null, buf = '', tokens = 0, t0 = 0, timer = null;
const btn = document.getElementById('btn');
const frame = document.getElementById('frame');
const delayInput = document.getElementById('delay');
const delayVal = document.getElementById('delayVal');
delayInput.oninput = () => delayVal.textContent = delayInput.value;

function updateStats() {
  const el = (performance.now() - t0) / 1000;
  document.getElementById('sTok').textContent = 'Tokens: ' + tokens;
  document.getElementById('sTime').textContent = 'Elapsed: ' + el.toFixed(1) + 's';
  document.getElementById('sRate').textContent = (el > 0 ? (tokens / el).toFixed(0) : '0') + ' tok/s';
}

function toggle() {
  if (es) { stop(); return; }
  buf = ''; tokens = 0; t0 = performance.now();
  frame.srcdoc = '';
  const tok = document.getElementById('tok').value;
  const d = delayInput.value;
  es = new EventSource('/stream?tokenizer=' + encodeURIComponent(tok) + '&delay=' + d);
  es.onmessage = e => {
    const msg = JSON.parse(e.data);
    buf += msg.token;
    tokens = msg.index + 1;
    frame.srcdoc = buf;
  };
  es.addEventListener('done', e => {
    updateStats();
    stop();
  });
  es.onerror = () => stop();
  btn.textContent = 'Stop';
  btn.className = 'stop';
  timer = setInterval(updateStats, 250);
}

function stop() {
  if (es) { es.close(); es = null; }
  if (timer) { clearInterval(timer); timer = null; }
  btn.textContent = 'Start';
  btn.className = '';
  updateStats();
}
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self._serve_viewer()
        elif parsed.path == "/stream":
            self._serve_stream(parsed.query)
        else:
            self.send_error(404)

    def _serve_viewer(self):
        body = VIEWER_HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_stream(self, query: str):
        params = urllib.parse.parse_qs(query)
        tok_name = params.get("tokenizer", ["gpt2"])[0]
        delay_ms = int(params.get("delay", ["20"])[0])
        delay_s = delay_ms / 1000.0

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        try:
            encode, decode = make_tokenizer(tok_name)
        except Exception as e:
            self._send_event("error", {"error": str(e)})
            return

        html = load_dashboard()
        ids = encode(html)
        total = len(ids)
        t0 = time.perf_counter()

        try:
            for i, token_id in enumerate(ids):
                token_text = decode([token_id])
                payload = json.dumps({"token": token_text, "index": i, "total": total})
                self.wfile.write(f"data: {payload}\n\n".encode())
                self.wfile.flush()
                if delay_s > 0:
                    time.sleep(delay_s)
        except (BrokenPipeError, ConnectionResetError):
            return

        elapsed = time.perf_counter() - t0
        done_payload = json.dumps({
            "elapsed": round(elapsed, 3),
            "total_tokens": total,
            "tokenizer": tok_name,
        })
        try:
            self.wfile.write(f"event: done\ndata: {done_payload}\n\n".encode())
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_event(self, event: str, data: dict):
        try:
            self.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        # Quiet request logging; only print SSE start/stop
        pass


def main():
    parser = argparse.ArgumentParser(description="Realtime SSE viewer for token streaming")
    parser.add_argument("--port", type=int, default=8080, help="HTTP port (default: 8080)")
    parser.add_argument("--tokenizer", default="gpt2", help="Default tokenizer (default: gpt2)")
    parser.add_argument("--delay", type=int, default=20, help="Default delay in ms (default: 20)")
    args = parser.parse_args()

    server = HTTPServer(("", args.port), Handler)
    print(f"Realtime viewer running at http://localhost:{args.port}")
    print(f"  Default tokenizer: {args.tokenizer}")
    print(f"  Default delay:     {args.delay}ms")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
