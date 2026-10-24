"""Voxwright neural voice server with Gumroad subscription check.

Environment variables (all optional):
  GUMROAD_PRODUCT_ID  Product ID of your Gumroad membership. When set, the server
                      enforces payment: two free listens per visitor (300 characters each),
                      then a valid license key is required.
  GUMROAD_URL         Your Gumroad product link, used by the Subscribe buttons.
  DEV_LICENSE         A key you invent for testing. It always counts as a paid license.
  TRUST_PROXY=1       Read the visitor IP from X-Forwarded-For (needed behind a proxy).
  PORT                Port to listen on (default 8000).
"""
import asyncio, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import edge_tts

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8000"))
GUMROAD_PRODUCT_ID = os.environ.get("GUMROAD_PRODUCT_ID", "")
GUMROAD_URL = os.environ.get("GUMROAD_URL", "")
DEV_LICENSE = os.environ.get("DEV_LICENSE", "")
TRUST_PROXY = os.environ.get("TRUST_PROXY", "") == "1"
VOICE_RX = re.compile(r"^[a-z]{2,3}-[A-Z]{2}-[A-Za-z]+Neural$")
RATE_RX = re.compile(r"^[+-]\d{1,3}%$")
PITCH_RX = re.compile(r"^[+-]\d{1,3}Hz$")
MAX_BODY = 5 * 1024 * 1024
TRIAL_CHARS = 300
TRIAL_LISTENS = 2

_license_cache = {}   # key -> (valid, expires_at)
_trial_counts = {}    # visitor IP -> free listens used (resets on restart)

def verify_license(key):
    """True if the key is a paid, active Gumroad license."""
    key = (key or "").strip()
    if not key:
        return False
    if DEV_LICENSE and key == DEV_LICENSE:
        return True
    if not GUMROAD_PRODUCT_ID:
        return False
    now = time.time()
    cached = _license_cache.get(key)
    if cached and cached[1] > now:
        return cached[0]
    ok = False
    try:
        data = urllib.parse.urlencode({
            "product_id": GUMROAD_PRODUCT_ID,
            "license_key": key,
            "increment_uses_count": "false",
        }).encode()
        req = urllib.request.Request("https://api.gumroad.com/v2/licenses/verify", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            j = json.loads(r.read().decode())
        p = j.get("purchase") or {}
        ok = (bool(j.get("success"))
              and not p.get("refunded") and not p.get("chargebacked") and not p.get("disputed")
              and not p.get("subscription_ended_at") and not p.get("subscription_failed_at"))
    except urllib.error.HTTPError:
        ok = False                      # 404: key does not exist or is disabled
    except Exception as e:              # network problem: do not cache the result
        print("Gumroad check error:", e, file=sys.stderr)
        return bool(cached and cached[0])
    _license_cache[key] = (ok, now + 3600)
    return ok

async def synth(text, voice, rate, pitch):
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    buf = bytearray()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            buf.extend(chunk["data"])
    return bytes(buf)

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def _ip(self):
        if TRUST_PROXY:
            fwd = self.headers.get("X-Forwarded-For", "")
            if fwd:
                return fwd.split(",")[0].strip()
        return self.client_address[0]

    def _tts(self, text, voice, rate, pitch, license_key=""):
        text = (text or "").strip()
        if not text or not VOICE_RX.match(voice) or not RATE_RX.match(rate) or not PITCH_RX.match(pitch):
            return self._send(400, b"bad request")
        if GUMROAD_PRODUCT_ID and not verify_license(license_key):
            ip = self._ip()
            used = _trial_counts.get(ip, 0)
            if used >= TRIAL_LISTENS:
                return self._send(402, b"subscription required")
            _trial_counts[ip] = used + 1
            text = text[:TRIAL_CHARS]
        try:
            audio = asyncio.run(synth(text, voice, rate, pitch))
        except Exception as e:
            print("TTS error:", e, file=sys.stderr)
            return self._send(502, b"tts failed")
        if not audio:
            return self._send(502, b"no audio")
        self._send(200, audio, "audio/mpeg")

    def do_OPTIONS(self):
        self._send(204)

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/tts", "/verify"):
            return self._send(404, b"not found")
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n <= 0 or n > MAX_BODY:
                return self._send(413, b"too large")
            data = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return self._send(400, b"bad json")
        if path == "/verify":
            return self._json({"valid": verify_license(data.get("key", ""))})
        self._tts(data.get("text", ""), data.get("voice", "en-US-GuyNeural"),
                  data.get("rate", "+0%"), data.get("pitch", "+0Hz"), data.get("license", ""))

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            with open(os.path.join(ROOT, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if u.path == "/health":
            return self._send(200, b"ok")
        if u.path == "/config":
            return self._json({"gumroad_url": GUMROAD_URL, "enforced": bool(GUMROAD_PRODUCT_ID)})
        if u.path == "/tts":
            q = parse_qs(u.query)
            return self._tts(q.get("text", [""])[0], q.get("voice", ["en-US-GuyNeural"])[0],
                             q.get("rate", ["+0%"])[0], q.get("pitch", ["+0Hz"])[0], q.get("license", [""])[0])
        self._send(404, b"not found")

if __name__ == "__main__":
    mode = "payments ENFORCED (Gumroad)" if GUMROAD_PRODUCT_ID else "open mode (no payment check)"
    print(f"Voxwright running at http://localhost:{PORT}  [{mode}]")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
