# Devpost Submission Draft — PayPal AI Hackathon
<!-- Draft only. Do NOT submit without Cipoz's approval. English throughout, per submission rules. -->
<!-- Hackathon: https://paypalaihackathon.devpost.com/ — deadline 12 Nov 2026 12:00 PST = 13 Nov 2026 03:00 WIB. Total prize $67,500. -->
<!-- Tested fresh 12 Nov ~12:35 WIB: end-to-end PASS in DEMO-MOCK mode (see TEST-REPORT.md). Live sandbox path exists but UNTESTED without credentials. -->

## Project title
**PayPal AI Invoice Assistant**

## Tagline
Type a payment request in plain language — AI turns it into a PayPal invoice.

## Description
Freelancers and small sellers lose time to invoicing: open a dashboard, fill
in a form, copy an amount, paste an email, send. The PayPal AI Invoice
Assistant removes the form entirely. You write what you want in plain
language — *"Invoice Budi for $120 for logo design work"* — and the app does
the rest:

1. A local LLM (Ollama, `qwen2.5:3b`) extracts the amount, currency,
   recipient and description as structured JSON.
2. The app creates a real PayPal invoice through the PayPal REST API
   (`POST /v2/invoicing/invoices`, sandbox) and returns the invoice ID,
   status and payment link.
3. If the local model is unavailable, a deterministic parser takes over
   automatically, so the app never blocks on AI latency.

Everything runs locally with zero paid dependencies: Python stdlib only,
Ollama free and local, PayPal sandbox free. No data leaves the machine
except the PayPal API call itself.

**Demo mode:** without PayPal credentials the app still runs end-to-end and
returns a clearly-labelled MOCK invoice (yellow "DEMO MODE" badge in the UI,
`INV2-MOCK-…` IDs, explicit note in the API response). It is never presented
as a real invoice. Set `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` to switch
to the live sandbox.

## How to run
```bash
ollama serve & ollama pull qwen2.5:3b   # local AI (optional; fallback works without it)
python3 server.py                        # → http://127.0.0.1:8080
# Live sandbox:
PAYPAL_CLIENT_ID=... PAYPAL_CLIENT_SECRET=... python3 server.py
```
Open http://127.0.0.1:8080, type a request, click **Create invoice**.

## AI tools used
- **Ollama + qwen2.5:3b (local LLM)** — structured extraction of payment
  details from natural-language requests (JSON-only prompt, temperature 0).
- **Deterministic regex parser** (built-in) — fallback when the local model
  is slow or unavailable; every parse response reports which parser ran.
- **Muse (Meta AI)** — assisted in writing the code and documentation.

## Built with
Python (stdlib only), PayPal REST API (sandbox, Invoicing v2), Ollama.

## Links (to fill in by Cipoz)
- Public repo URL: https://github.com/taufik52/paypal-ai-invoice-assistant
- Demo video (YouTube, < 3 min): https://www.youtube.com/watch?v=qThaHZImmbo (1:58, Public, uploaded 12 Nov 2026 from ngobel420)
- Live demo URL: http://127.0.0.1:8080 (local; no hosted URL — judges run it locally)

## License
MIT.
