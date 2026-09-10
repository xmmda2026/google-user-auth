#!/usr/bin/env python3
"""一次性个人 Google OAuth 授权：本地回调后保存 refresh_token。"""
import argparse, json, secrets, subprocess, sys, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/siteverification",
    "https://www.googleapis.com/auth/indexing",
    "https://www.googleapis.com/auth/webmasters",
    "https://www.googleapis.com/auth/analytics.edit"
]
DEFAULT_SCOPE_STRING = " ".join(DEFAULT_SCOPES)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--client-json", default="/root/.openclaw/skills/google-user-auth/google-oauth-client.json")
    p.add_argument("--output", default="/root/.openclaw/skills/google-user-auth/google-user-token.json")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument(
        "--scopes",
        default=DEFAULT_SCOPE_STRING,
        help="本次授权的 Google OAuth scope，空格分隔；默认包含 Gmail、GA、GSC、Site Verification 和 Indexing 所需范围",
    )
    args = p.parse_args()
    client = json.loads(Path(args.client_json).read_text())
    cfg = client.get("installed") or client.get("web") or client
    client_id, secret = cfg["client_id"], cfg["client_secret"]
    redirect = f"http://localhost:{args.port}/"
    state = secrets.token_urlsafe(24)
    params = {"client_id": client_id, "redirect_uri": redirect,
              "response_type": "code", "scope": args.scopes,
              "access_type": "offline", "prompt": "consent", "state": state}
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    print("AUTH_URL=" + url, flush=True)
    result = {}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            result.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("授权结果已收到，可以关闭此页面。".encode())
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        def log_message(self, *_): pass
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    server.serve_forever()
    if result.get("state") != state or "code" not in result:
        raise SystemExit("OAuth authorization failed")
    exchange_script = Path(__file__).with_name("exchange_code.py")
    subprocess.run([
        sys.executable, str(exchange_script),
        "--code", result["code"],
        "--client-json", args.client_json,
        "--output", args.output,
        "--redirect-uri", redirect,
        "--scopes", args.scopes,
    ], check=True)

if __name__ == "__main__": main()
