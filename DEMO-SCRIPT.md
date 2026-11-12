# Demo Video Script — PayPal AI Invoice Assistant
Target: **under 3 minutes** (aim ~2:30). Record in one take, screen capture + voiceover.

> PREP BEFORE RECORDING (do this first, off-camera):
> 1. `ollama serve` running, then run ONE parse request to warm the model
>    (first load takes ~60 s; warmed parses take ~20–40 s on this VM).
> 2. `python3 server.py` running → http://127.0.0.1:8080 open in the browser.
> 3. Decide the mode: DEMO (no credentials, mock labelled on screen) or LIVE
>    SANDBOX (export PAYPAL_CLIENT_ID/SECRET first, then restart the server).
>    Demo mode is honest and judge-friendly; live sandbox is stronger if the
>    credentials are ready.

| Time | Shot | Script (say / show) |
|---|---|---|
| 0:00–0:15 | Face / title card | "Hi, I'm Cipoz. This is the PayPal AI Invoice Assistant — turn a sentence into a PayPal invoice." Show the app open at localhost:8080. |
| 0:15–0:45 | Type the request | Type: **"Invoice Budi for $120 for logo design work"**. "No forms. I just write what I want, in plain language." Click **Create invoice**. |
| 0:45–1:30 | AI parse (wait) | While it runs: "A local AI model, qwen2.5:3b running on Ollama, extracts the amount, currency, recipient and description as JSON. If the model is down, a deterministic parser takes over, so it never hangs." Show the parsed JSON when it appears: amount 120, currency USD, recipient Budi. (If the wait is long, cut the waiting time in editing — keep the JSON on screen.) |
| 1:30–2:05 | PayPal result | Show the PayPal result: invoice ID, status DRAFT, payment link. In DEMO mode, point at the yellow badge: "This is demo mode — a clearly labelled mock, because no credentials are set. With sandbox credentials it calls the real PayPal Invoicing API." In LIVE mode, point at the real sandbox invoice ID instead. |
| 2:05–2:25 | Second example (fast) | Type: "Charge ana@example.com 45 dollars for consulting call" → show parse + invoice. "Same flow, any currency, email or name." |
| 2:25–2:35 | Close | "Python stdlib only, Ollama local and free, PayPal sandbox free. Code and README on GitHub — link in the description. Thanks!" |

## Editing notes
- Hard cap 3:00 — cut waiting time, never cut the JSON or the invoice result.
- Captions on. 1080p screen capture.
- Upload as **Public** (not Unlisted) to YouTube — Devpost requires a public video.
- Title suggestion: "PayPal AI Invoice Assistant — plain language to PayPal invoice (PayPal AI Hackathon)".
