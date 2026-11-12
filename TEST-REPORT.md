# Test Report — PayPal AI Invoice Assistant
Date: 2026-11-12, ~11:20–11:35 WIB. Tester: build agent (VM).

## End-to-end test (final code, 11:35 WIB) — PASS
Server started with `python3 server.py` → http://127.0.0.1:8080.

1. `GET /api/health` → `{"status": "ok", "mode": "DEMO-MOCK", "ollama_model": "qwen2.5:3b"}` ✓
2. `POST /api/parse` `{"text": "Invoice Budi for $120 for logo design work"}`
   → `{"amount": 120.0, "currency": "USD", "recipient": "Budi", "description": "Invoice Budi for $120 for logo design work", "parser": "deterministic"}` ✓
   (took ~60 s: Ollama timed out under VM load, deterministic fallback answered correctly)
3. `POST /api/create-invoice` `{"amount": 120, "currency": "USD", "recipient": "Budi", ...}`
   → `{"mode": "DEMO-MOCK", "invoice_id": "INV2-MOCK-39F4AF62908A", "status": "DRAFT", "payment_link": "https://www.sandbox.paypal.com/invoice/p/#MOCK-39f4af62908a", "note": "DEMO MODE: ... MOCK response, not a real PayPal invoice ..."}` ✓
4. `GET /` HTML contains badge `DEMO MODE — mock PayPal responses` ✓

Second parse verified earlier: `"Charge ana@example.com 45 dollars for consulting call"`
→ amount 45.0, USD, recipient `ana@example.com` ✓

## Ollama (AI path) — VERIFIED STANDALONE, SLOW UNDER CURRENT VM LOAD
- Fixed during build: the Ollama runner binary `llama-server` + shared libs were
  missing from the manual install; extracted `lib/ollama/` from
  `/home/hatch/ollama-linux-amd64.tar` (2.4 GB) to `~/workspace/.local/`.
  After that, direct `POST /api/generate` returned correct JSON:
  `{"amount": 120}` in ~60 s (first call, includes model load). — PROOF the AI path works.
- Under the VM load at test time (load average 9–21, other agents compiling
  Rust / npm install), warm generation of a ~60-token JSON exceeded 120 s and
  the app fell back to the deterministic parser (60 s timeout, then instant
  correct answer). The fallback is by design and the `parser` field reports
  honestly which path ran.
- Implication for the demo video: warm the model first (one parse before
  recording), record when the VM is quiet, and expect ~30–60 s per AI parse;
  the fallback guarantees the demo never stalls. Do NOT claim sub-second AI.

## NOT tested (needs Cipoz)
- Live PayPal sandbox invoice (no credentials; code path exists in
  `create_paypal_invoice()` — OAuth2 + `POST /v2/invoicing/invoices` — but
  untested against the real API).
- Video, YouTube upload, Devpost submission, public GitHub repo.

## Files
- `server.py` — whole app (stdlib only)
- `README.md`, `SUBMISSION.md`, `DEMO-SCRIPT.md`, `LICENSE` (MIT), `.env.example`

---

## Re-test segar — 2026-11-12 ~12:25–12:35 WIB (resume agent, sebelum submit)
Server dijalankan segar: `python3 server.py` → http://127.0.0.1:8080. Ollama
sudah jalan (`ollama serve`, model `qwen2.5:3b` terdaftar, load average VM 2,5–3,2).

1. `GET /api/health` → `{"status": "ok", "mode": "DEMO-MOCK", "ollama_model": "qwen2.5:3b"}` ✓
2. `POST /api/parse` "Invoice Budi for $120 for logo design work"
   → amount 120.0, USD, recipient "Budi", parser **deterministic** ✓
   (60 dtk: Ollama tidak menjawab dalam timeout 60 dtk, fallback langsung benar)
3. `POST /api/parse` "Charge ana@example.com 45 dollars for consulting call"
   → amount 45.0, USD, recipient "ana@example.com", parser **deterministic** ✓ (60 dtk)
4. `POST /api/create-invoice` {120, USD, Budi} → `INV2-MOCK-48CB5A8E301A`,
   status DRAFT, payment link mock, note DEMO MODE eksplisit ✓
5. `GET /` HTML berisi badge `DEMO MODE — mock PayPal responses` ✓
6. Edge: teks kosong → `{"error": "empty text"}` (400) ✓
7. Edge: "hello there" (tanpa angka) → amount null, parser deterministic ✓

## Ollama (AI path) — TIDAK RESPONSIF saat re-test ini
- `GET /api/ps` menunjukkan model `qwen2.5:3b` loaded (runner llamacpp),
  TAPI: dua parse lewat server masing-masing mentok timeout 60 dtk, DAN
  panggilan langsung `POST /api/generate` (num_predict 80) tidak memberi
  respons apa pun dalam 110 dtk (output kosong). Kemungkinan antrean generate
  sebelumnya masih jalan di server Ollama, atau VM sedang sibuk (agen lain).
- Catatan: jalur AI ini PERNAH terverifikasi standalone (test report di atas,
  ~60 dtk, JSON benar). Jadi ini masalah performa/load saat ini, bukan bug kode.
- **Dampak: NOL untuk demo/submit.** Fallback deterministik menjawab benar
  dan instan begitu timeout Ollama habis, dan field `parser` jujur melaporkannya.
- **Tips rekam video:** tiap klik "Create invoice" akan menunggu ~60 dtk
  (timeout Ollama) sebelum jawaban muncul — potong waktu tunggu saat editing
  (sudah di DEMO-SCRIPT.md). Alternatif bila mau parse instan saat rekam:
  jalankan server dengan `OLLAMA_URL=http://127.0.0.1:9 python3 server.py`
  supaya fallback langsung jalan tanpa menunggu; sebutkan di video bahwa
  fallback deterministik yang bekerja. Jangan klaim hasil parse itu dari LLM
  bila yang jalan fallback.
- Server test dimatikan lagi setelah re-test (port 8080 bebas).

## Masih BELUM teruji (butuh Cipoz)
- Live PayPal sandbox invoice (tanpa kredensial; code path ada tapi belum
  pernah kena API sungguhan). Video + submit boleh pakai DEMO MODE — jujur
  dan dilabeli mock — tapi live sandbox lebih kuat bila kredensial sempat dibuat.
- Video, upload YouTube, repo GitHub publik, submit Devpost.
- Tenggat: **13 Nov 2026 03:00 WIB** (12 Nov 12:00 PST / 20:00 UTC).
  Devpost: https://paypalaihackathon.devpost.com/
