# LedgerLens

Drop in a photo of a receipt or invoice → get schema-validated structured data,
per-field confidence scores, and a human-review queue for anything the model
isn't confident about.

## What this does

1. Upload a receipt/invoice image through a FastAPI endpoint (or the Streamlit UI)
2. Google Gemini 2.5 Flash extracts structured fields (vendor, date, total, line items, etc.)
3. Every extraction is validated against a Pydantic schema — no malformed data ever reaches storage
4. A confidence router checks overall and per-line-item confidence against a threshold;
   anything below it is flagged for human review instead of silently auto-approved
5. Flagged documents show up in a Streamlit reviewer UI, where a human can correct and approve them
6. Stored source images are watermarked with a document ID + timestamp before archival
7. Extracted data is PII-redacted (regex-based) before ever appearing in application logs
8. Prometheus + Grafana track extraction latency and auto-approval rate in real time

## Stack

| Layer | Tool |
|---|---|
| Vision + extraction | Google Gemini 2.5 Flash (free tier) |
| Schema enforcement | Pydantic |
| Backend | FastAPI |
| Frontend | Streamlit |
| Storage | SQLite (SQLAlchemy) |
| Observability | Prometheus + Grafana |
| Containerization | Docker + docker-compose |
| Testing | pytest |

## Project structure

LedgerLens_Chirag_Rupapara/
├── app/
│   ├── main.py              # FastAPI app: /ingest, /review, /approve, /metrics
│   ├── schemas/invoice.py   # InvoiceSchema, LineItem (Pydantic)
│   └── services/
│       ├── extract.py       # Gemini extraction
│       ├── router.py        # Confidence-based routing
│       ├── db.py            # SQLAlchemy models + session
│       ├── watermark.py     # PIL provenance stamping
│       ├── redact.py        # PII regex redaction
│       └── metrics.py       # Prometheus metric definitions
├── streamlit_app/app.py     # Reviewer UI
├── tests/                   # pytest schema-contract + router tests
├── sample_images/           # Test receipts used during development
├── Dockerfile
├── docker-compose.yml       # app + prometheus + grafana
├── prometheus.yml
└── requirements.txt

## Running locally

1. Copy `.env.example` to `.env` and add a free Gemini API key from
   https://aistudio.google.com/apikey
2. `docker-compose up` — starts the app (port 8000), Prometheus (port 9090),
   and Grafana (port 3000)
3. Open `http://127.0.0.1:8000/docs` to use the API directly, or run the
   Streamlit reviewer UI separately:

pip install -r requirements.txt
streamlit run streamlit_app/app.py

## Running tests

pytest tests/ -v

## Notes on design decisions

- Review threshold uses strict `<` (a field exactly at the threshold passes),
  not `<=` — a deliberate choice to treat the threshold as a genuine minimum
  bar rather than an exclusive cutoff.
- PII redaction is regex-based (per spec), which is a known trade-off: it
  reliably catches SSNs/emails/phone numbers but can also flag unrelated
  long digit strings (e.g. transaction reference numbers) as false positives.
  Over-redaction in logs was judged safer than under-redaction.

## Deployment

The app is deployed live on Render's free tier (Docker-based Web Service,
no credit card required):

**https://ledgerlens-chirag-rupapara.onrender.com/docs**

Note: the free instance spins down after 15 minutes of inactivity — the
first request after idle time may take 30-60 seconds to respond while it
wakes back up. This is expected free-tier behavior, not a bug.

### Storage is ephemeral on the free tier

Render's free Web Services have no persistent disk. The SQLite database
and any uploaded/watermarked images reset whenever the service restarts
or redeploys. This mirrors the same limitation the original project spec
flagged for GCP Cloud Run. For a genuinely persistent production
deployment, the storage layer would need to move to external managed
storage (e.g. a hosted Postgres database + S3/GCS-compatible object
storage) — out of scope for a zero-cost build.

### Local deployment (full stack, including observability)

Render only runs the FastAPI app itself. For the complete stack —
app + Prometheus + Grafana — run locally:

docker-compose up

- App: http://127.0.0.1:8000/docs
- Prometheus: http://127.0.0.1:9090
- Grafana: http://127.0.0.1:3000