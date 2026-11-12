#!/usr/bin/env python3
"""PayPal AI Invoice Assistant — Devpost PayPal AI Hackathon entry.

Stack: Python stdlib only (no pip dependencies).
- AI: local Ollama (qwen2.5:3b) with a deterministic regex fallback parser.
- Payments: PayPal REST API (sandbox) when PAYPAL_CLIENT_ID /
  PAYPAL_CLIENT_SECRET are set; otherwise DEMO mode with clearly-labelled
  mock PayPal responses (never presented as live).
"""
import json
import os
import re
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_BASE = "https://api-m.sandbox.paypal.com"
PORT = int(os.environ.get("PORT", "8080"))

DEMO_MODE = not (PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)

CURRENCIES = {"$": "USD", "USD": "USD", "US$": "USD", "DOLLAR": "USD",
              "RP": "IDR", "IDR": "IDR", "RUPIAH": "IDR", "€": "EUR", "EUR": "EUR",
              "£": "GBP", "GBP": "GBP"}

SYSTEM_PROMPT = (
    "You extract payment details from a natural-language request. "
    "Reply with ONLY a JSON object, no other text, with keys: "
    "amount (number), currency (3-letter ISO code, default USD), "
    "recipient (name or email string), description (short string). "
    "If a field is unknown, use null for amount, \"USD\" for currency, "
    "null for recipient, and \"\" for description."
)


def deterministic_parse(text):
    """Fallback parser: regex only, no LLM. Used when Ollama is slow/down."""
    amount = None
    currency = "USD"
    m = re.search(r"([\$€£]|USD|IDR|EUR|GBP|Rp)\s*([\d][\d,.\s]*)", text, re.I)
    if m:
        currency = CURRENCIES.get(m.group(1).upper(), "USD")
        raw = re.sub(r"[,\s]", "", m.group(2)).rstrip(".")
        try:
            amount = float(raw)
        except ValueError:
            amount = None
    if amount is None:
        m2 = re.search(r"([\d][\d,.\s]*)\s*(USD|IDR|EUR|GBP|dollars?|rupiah)?", text, re.I)
        if m2:
            raw = re.sub(r"[,\s]", "", m2.group(1)).rstrip(".")
            try:
                amount = float(raw)
            except ValueError:
                amount = None
            if m2.group(2):
                currency = CURRENCIES.get(m2.group(2).upper().rstrip("S"), currency)
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    recipient = email.group(0) if email else None
    if recipient is None:
        m3 = re.search(r"\b(?:invoice|bill|charge|to|pay)\s+([A-Z][A-Za-z' -]{1,40}?)(?:\s+for\b|\s+\$|\s*\d|\s*$)", text, re.I)
        if m3:
            recipient = m3.group(1).strip()
    desc = text.strip()
    return {"amount": amount, "currency": currency,
            "recipient": recipient, "description": desc, "parser": "deterministic"}


def ollama_parse(text):
    """Ask the local Ollama model to extract invoice fields. Returns dict or None."""
    body = json.dumps({
        "model": OLLAMA_MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": text,
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0.0, "num_predict": 80},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL + "/api/generate", data=body,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except Exception:
        return None
    raw = data.get("response", "").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        parsed = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or "amount" not in parsed:
        return None
    try:
        parsed["amount"] = float(parsed["amount"]) if parsed["amount"] is not None else None
    except (TypeError, ValueError):
        parsed["amount"] = None
    parsed.setdefault("currency", "USD")
    parsed.setdefault("recipient", None)
    parsed.setdefault("description", text.strip())
    parsed["parser"] = "ollama:" + OLLAMA_MODEL
    return parsed


def parse_request(text):
    result = ollama_parse(text)
    if result is not None:
        return result
    return deterministic_parse(text)


def paypal_access_token():
    creds = (PAYPAL_CLIENT_ID + ":" + PAYPAL_CLIENT_SECRET).encode()
    import base64
    req = urllib.request.Request(
        PAYPAL_BASE + "/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={"Authorization": "Basic " + base64.b64encode(creds).decode(),
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]


def create_paypal_invoice(inv):
    """Real PayPal sandbox call (invoicing API). Raises on any failure."""
    token = paypal_access_token()
    payload = {
        "detail": {"currency_code": inv["currency"],
                   "note": inv.get("description", "")[:500],
                   "memo": "Created by PayPal AI Invoice Assistant (hackathon demo)"},
        "invoicer": {"name": {"given_name": "PayPal AI", "surname": "Invoice Assistant"}},
        "primary_recipients": [{"billing_info": {"email_address": inv["recipient"]}}]
        if inv.get("recipient") and "@" in str(inv["recipient"]) else [],
        "items": [{"name": inv.get("description", "Payment")[:100],
                   "quantity": "1",
                   "unit_amount": {"currency_code": inv["currency"],
                                   "value": f"{inv['amount']:.2f}"}}],
    }
    req = urllib.request.Request(
        PAYPAL_BASE + "/v2/invoicing/invoices", data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "Prefer": "return=representation"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return {"mode": "live-sandbox", "invoice_id": data.get("id"),
            "status": data.get("status"),
            "payment_link": next((l["href"] for l in data.get("links", [])
                                  if l.get("rel") == "self"), None),
            "raw": data}


def create_mock_invoice(inv):
    import hashlib
    digest = hashlib.sha256(json.dumps(inv, sort_keys=True).encode()).hexdigest()[:12]
    return {"mode": "DEMO-MOCK",
            "invoice_id": "INV2-MOCK-" + digest.upper(),
            "status": "DRAFT",
            "payment_link": "https://www.sandbox.paypal.com/invoice/p/#MOCK-" + digest,
            "note": "DEMO MODE: no PayPal credentials configured. "
                    "This is a MOCK response, not a real PayPal invoice. "
                    "Set PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET to use the sandbox."}


INDEX_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>PayPal AI Invoice Assistant</title>
<style>body{font-family:system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 16px}
textarea{width:100%;height:90px}button{padding:10px 18px;font-size:16px}
pre{background:#f4f4f4;padding:12px;white-space:pre-wrap;word-break:break-word}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-weight:bold}
.demo{background:#ffe08a}.live{background:#b6f0b6}</style></head>
<body>
<h1>PayPal AI Invoice Assistant</h1>
<p><span class="badge %BADGE_CLASS%">%MODE_LABEL%</span></p>
<p>Type a payment request in plain language. The AI extracts the amount,
currency and recipient, then creates a PayPal invoice.</p>
<textarea id="q" placeholder="e.g. Invoice Budi for $120 for logo design work"></textarea><br>
<button onclick="go()">Create invoice</button>
<h3>Parsed by AI</h3><pre id="parsed">(none yet)</pre>
<h3>PayPal result</h3><pre id="result">(none yet)</pre>
<script>
async function go(){
  const text=document.getElementById('q').value;
  const p=await fetch('/api/parse',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}).then(r=>r.json());
  document.getElementById('parsed').textContent=JSON.stringify(p,null,2);
  if(p.amount==null){document.getElementById('result').textContent='Could not find an amount. Try e.g. "Invoice Ana for $45 for consulting".';return;}
  const r=await fetch('/api/create-invoice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}).then(r=>r.json());
  document.getElementById('result').textContent=JSON.stringify(r,null,2);
}
</script>
<p><small>AI: local Ollama qwen2.5:3b, deterministic parser fallback.
PayPal: sandbox REST API when credentials are set; otherwise clearly-labelled DEMO mock.</small></p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            mode = "DEMO MODE — mock PayPal responses" if DEMO_MODE else "LIVE SANDBOX — real PayPal API"
            html = (INDEX_HTML
                    .replace("%BADGE_CLASS%", "demo" if DEMO_MODE else "live")
                    .replace("%MODE_LABEL%", mode)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif self.path == "/api/health":
            self._json({"status": "ok", "mode": "DEMO-MOCK" if DEMO_MODE else "live-sandbox",
                        "ollama_model": OLLAMA_MODEL})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "invalid JSON"}, 400)
        if self.path == "/api/parse":
            text = (body.get("text") or "").strip()
            if not text:
                return self._json({"error": "empty text"}, 400)
            return self._json(parse_request(text))
        if self.path == "/api/create-invoice":
            amount = body.get("amount")
            currency = (body.get("currency") or "USD").upper()
            if amount is None:
                return self._json({"error": "amount is required"}, 400)
            inv = {"amount": float(amount), "currency": currency,
                   "recipient": body.get("recipient"),
                   "description": body.get("description", "")}
            if DEMO_MODE:
                return self._json(create_mock_invoice(inv))
            try:
                return self._json(create_paypal_invoice(inv))
            except urllib.error.HTTPError as e:
                return self._json({"error": "PayPal API error",
                                   "status": e.code, "detail": e.read().decode()[:500]}, 502)
            except Exception as e:
                return self._json({"error": "PayPal call failed", "detail": str(e)[:300]}, 502)
        return self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    print(f"PayPal AI Invoice Assistant on http://127.0.0.1:{PORT} "
          f"mode={'DEMO-MOCK' if DEMO_MODE else 'live-sandbox'} "
          f"ollama={OLLAMA_MODEL}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
