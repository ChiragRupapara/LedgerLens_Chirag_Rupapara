## Key Features

- Gemini 2.5 Flash invoice extraction
- Gemini-powered image moderation gate
- Confidence-based routing
- Human review workflow
- Pydantic schema validation
- Automatic image watermarking
- PII-redacted logging
- Prometheus & Grafana monitoring
- Dockerized deployment
- Streamlit web interface
- Render cloud deployment

# LedgerLens

Drop in a photo of a receipt or invoice → get schema-validated structured data,
per-field confidence scores, and a human-review queue for anything the model
isn't confident about.

## What this does

1. Upload a receipt/invoice image through the Streamlit UI (or directly via the FastAPI endpoint)
2. Every uploaded image first passes through a Gemini-powered moderation gate.
3. The moderation gate classifies the image as:
   - ALLOW → Continue to invoice extraction.
   - BLOCK → Reject unsafe images (nudity, violence, illegal content, etc.).
   - HUMAN_REVIEW → Hold ambiguous or unreadable images for manual review.
4. Only images classified as ALLOW are processed by Google Gemini 2.5 Flash for invoice extraction.
5. Every extraction is validated against a Pydantic schema — no malformed data ever reaches storage.
6. A confidence router checks overall and per-line-item confidence against a threshold;
   anything below it is flagged for human review instead of silently auto-approved.
7. Flagged documents show up in the Streamlit reviewer UI, where a human can correct and approve them.
8. A gallery view lets you browse every uploaded documents, showing both the original and
   watermarked image side by side with its status.
9. Stored source images are watermarked with a document ID + timestamp before archival.
10. Extracted data is PII-redacted (regex-based) before ever appearing in application logs.
11. Prometheus + Grafana track extraction latency and auto-approval rate in real time.

## Stack

| Layer | Tool |
|---|---|
| Vision + extraction | Google Gemini 2.5 Flash (free tier) |
| Image Moderation | Google Gemini 2.5 Flash |
| Schema enforcement | Pydantic |
| Backend | FastAPI |
| Frontend | Streamlit (multi-page: Upload / Pending Review / Gallery) |
| Storage | SQLite (SQLAlchemy) |
| Observability | Prometheus + Grafana |
| Containerization | Docker + docker-compose |
| Testing | pytest |
| Deployment | Render (two independent free-tier web services) |

## Project structure
```
LedgerLens_Chirag_Rupapara/
├── app/
│   ├── main.py                        # FastAPI app: /ingest, /review, /approve, /documents, /images, /metrics
│   ├── schemas/
│   │   ├── invoice.py                 # InvoiceSchema, LineItem (Pydantic)
│   │   └── moderation_schemas.py      # ModerationSchema (Pydantic)
│   └── services/
│       ├── extract.py                 # Gemini extraction
│       ├── router.py                  # Confidence-based routing
│       ├── db.py                      # SQLAlchemy models + session
│       ├── watermark.py               # PIL provenance stamping
│       ├── redact.py                  # PII regex redaction
│       ├── moderation.py              # Gemini moderation gate
│       └── metrics.py                 # Prometheus metric definitions
├── streamlit_app/app.py               # Multi-page UI: Upload, Pending Review, Gallery
├── tests/                             # pytest schema-contract + router tests + moderation tests
├── sample_images/                     # Test receipts used during development
├── Dockerfile                         # FastAPI backend image
├── Dockerfile.streamlit               # Streamlit frontend image
├── docker-compose.yml                 # app + prometheus + grafana (local dev)
├── prometheus.yml
└── requirements.txt
```
## API endpoints (FastAPI backend)

| Endpoint | Method | Purpose |
|---|---|---|
| `/ingest` | POST | Upload an image, perform moderation, extract invoice data (if allowed), confidence routing, and save to the database |
| `/review` | GET | List documents currently pending human review |
| `/approve/{document_id}` | POST | Submit a human-corrected invoice, mark approved |
| `/documents` | GET | List every document (any status) — powers the Gallery view |
| `/images/{document_id}/{filename}` | GET | Serve a stored image (original or watermarked) |
| `/metrics` | GET | Prometheus metrics endpoint |

## Image Moderation Workflow

Before any invoice extraction begins, every uploaded image passes through a Gemini-powered moderation gate.

The moderation system returns one of three decisions:

| Decision     | Description |
|--------------|-------------|
| ALLOW        | Safe business document (receipt, invoice, bill). Invoice extraction continues. |
| BLOCK        | Unsafe content such as nudity, graphic violence, hate symbols, or illegal content. Processing stops immediately. |
| HUMAN_REVIEW | Ambiguous, blurry, unreadable, or non-business images requiring manual review. |

Only images classified as **ALLOW** are sent to the invoice extraction model.

```
Upload Image
      │
      ▼
Gemini Moderation Gate
      ├───────────────┬───────────────┐
      ▼               ▼               ▼
   Allow            Block         Human Review
      │               │               │
      ▼               ▼               ▼
Gemini Invoice     Reject      Hold for Review
  Extraction
      │
      ▼
Pydantic Validation
      │
      ▼
Confidence Routing
      ├───────────────┐
      ▼               ▼
Auto Approve     Pending Review
```
## Running locally

1. Copy `.env.example` to `.env` and add a free Gemini API key from
   https://aistudio.google.com/apikey
2. `docker-compose up` — starts the FastAPI app (port 8000), Prometheus (port 9090),
   and Grafana (port 3000)
3. Open `http://127.0.0.1:8000/docs` to use the API directly, or run the
   Streamlit UI separately:

pip install -r requirements.txt
streamlit run streamlit_app/app.py

   By default Streamlit points at `http://127.0.0.1:8000`. To point it at a
   different backend (e.g. the deployed Render API), set the `API_URL`
   environment variable before running it.

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

## Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
API_URL=http://127.0.0.1:8000
```

When deploying Streamlit on Render:

```
API_URL=https://ledgerlens-chirag-rupapara.onrender.com
```

## Deployment

The app is deployed live on Render's free tier as **two independent
Docker-based Web Services** (no credit card required for either):

- **FastAPI backend:** https://ledgerlens-chirag-rupapara.onrender.com/docs
- **Streamlit frontend:** https://ledgerlens-chirag-rupapara-api.onrender.com/

The Streamlit service is configured with an `API_URL` environment variable
pointing at the live FastAPI URL above, so the two deployed services talk to
each other over the public internet — the same code that runs locally against
`127.0.0.1` runs unchanged against the deployed backend.

Note: each free instance spins down independently after 15 minutes of
inactivity. The first request after idle time may take 30-60 seconds to
respond while it wakes back up — and if both services have been idle, the
very first action on the Streamlit UI may trigger two cold starts in a row
(Streamlit waking up, then its first backend call waking up FastAPI too).
This is expected free-tier behavior, not a bug.

On Render's free tier, services may go to sleep after a period of inactivity. 
Before uploading an image through the Streamlit application, 
the FastAPI backend (Render URL) must be awakened by making an initial request. 
The first request may take a short time to complete while the service starts up.

### Storage is ephemeral on the free tier

Render's free Web Services have no persistent disk. The SQLite database
and any uploaded/watermarked images reset whenever the FastAPI service
restarts or redeploys — so the Gallery view and document history only
reflect documents uploaded since the last restart. This mirrors the same
limitation the original project spec flagged for GCP Cloud Run. For a
genuinely persistent production deployment, the storage layer would need
to move to external managed storage (e.g. a hosted Postgres database +
S3/GCS-compatible object storage such as Cloudflare R2) — out of scope
for a zero-cost build.

### Local deployment (full stack, including observability)

Render only runs the FastAPI and Streamlit services. For the complete
stack — app + Prometheus + Grafana — run locally:

docker-compose up

- App: http://127.0.0.1:8000/docs
- Streamlit: `streamlit run streamlit_app/app.py` (separate terminal)
- Prometheus: http://127.0.0.1:9090
- Grafana: http://127.0.0.1:3000