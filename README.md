# PayPal AI Invoice Assistant

Turn a plain-language payment request into a PayPal invoice — no forms, no
copy-pasting amounts.

> **"Invoice Budi for $120 for logo design work"**
> → AI extracts amount `120`, currency `USD`, recipient `Budi`,
> description `logo design work` → creates a PayPal invoice (sandbox)
> and returns a payment link.

## How it works

1. **Natural language in** — type a request like the example above.
2. **AI extraction** — a local LLM ([Ollama](https://ollama.com), model
   `qwen2.5:3b`) extracts `amount`, `currency`, `recipient`, `description`
   as JSON. If Ollama is slow or unavailable, a deterministic regex parser
   takes over automatically, so the app always works.
3. **PayPal invoice out** — the app calls the PayPal REST API
   (`POST /v2/invoicing/invoices`) against the **sandbox** and returns the
   invoice ID, status and payment link.

## Modes

| Mode | When | What happens |
|---|---|---|
| **Live sandbox** | `PAYPAL_CLIENT_ID` + `PAYPAL_CLIENT_SECRET` set | Real PayPal sandbox invoice via the REST API |
| **Demo (mock)** | No credentials | A clearly-labelled **MOCK** response — invoice ID starts with `INV2-MOCK-`, the UI shows a yellow "DEMO MODE" badge, and the response says so. It is never presented as a real invoice. |

Demo mode exists so judges can run and click through the full flow without
any credentials. It is labelled as a mock in the UI, in the API response,
and here.

## Run it

```bash
# 1. Start Ollama (optional — the regex fallback works without it)
ollama serve            # in one terminal
ollama pull qwen2.5:3b  # once

# 2. Run the app (Python 3.11+, no dependencies, stdlib only)
python3 server.py       # → http://127.0.0.1:8080

# 3. (Optional) Live sandbox: create a REST app at
#    https://developer.paypal.com/dashboard/applications/sandbox
#    and export its credentials before starting:
PAYPAL_CLIENT_ID=... PAYPAL_CLIENT_SECRET=... python3 server.py
```

Open http://127.0.0.1:8080, type a request, click **Create invoice**.

### API

- `GET /api/health` — `{status, mode, ollama_model}`
- `POST /api/parse` — `{"text": "..."}` → `{amount, currency, recipient, description, parser}`
- `POST /api/create-invoice` — `{"amount": 120, "currency": "USD", "recipient": "budi@example.com", "description": "..."}` → invoice object (live sandbox or labelled mock)

## AI tools used

- **Ollama + qwen2.5:3b (local LLM)** — structured extraction of payment
  details from natural language (prompted for JSON-only output, temperature 0).
- **Deterministic regex parser** (built-in fallback) — guarantees the app
  still works when the local model is unavailable; every parse response
  reports which parser produced it (`parser` field).
- **Muse (Meta AI)** — assisted in writing this codebase and documentation.

## Project structure

```
server.py        # whole app: HTTP server, AI parsing, PayPal client, UI
README.md        # this file
SUBMISSION.md    # Devpost submission draft
DEMO-SCRIPT.md   # <3 min demo video script
LICENSE          # MIT
.env.example     # credential template (never commit real secrets)
```

## License

MIT — see `LICENSE`.
