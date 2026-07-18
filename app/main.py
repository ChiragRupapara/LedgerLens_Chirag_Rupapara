import os
import sys
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from prometheus_client import make_asgi_app


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "app" / "schemas"))
sys.path.append(str(BASE_DIR / "app" / "services"))

from invoice import InvoiceSchema
from extract import extract_invoice
from moderation import moderate_image
from router import route_invoice
from db import SessionLocal, Document, init_db
from watermark import add_watermark
from redact import redact_pii
from metrics import (
    extraction_latency_seconds,
    token_cost_usd_total,
    auto_approvals_total,
    documents_total,
    pending_review_queue_size,
)

app = FastAPI(title="LedgerLens")

init_db()  # make sure the table exists whenever the server starts

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    # Create database session
    db = SessionLocal()

    # 1. Create a placeholder database record first
    doc_row = Document(
        filename=file.filename,
        extracted_json="",
        status="processing",
    )
    db.add(doc_row)
    db.commit()
    db.refresh(doc_row)

    # 2. Use the database ID as the folder name
    doc_folder = BASE_DIR / "uploads" / str(doc_row.id)
    doc_folder.mkdir(parents=True, exist_ok=True)

    ext = file.filename.split(".")[-1]
    saved_path = doc_folder / f"original.{ext}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2.5 Watermark the stored image with document ID
    watermarked_path = add_watermark(str(saved_path), str(doc_row.id))

    
    # 3. Moderate image first
    moderation = moderate_image(str(saved_path))

    moderation_result = moderate_image(str(saved_path))

    if moderation_result.decision == "BLOCK":
        doc_row.status = "blocked"
        db.commit()
        db.close()
        return JSONResponse(
            status_code=400,
            content=moderation_result.model_dump()
        )

    if moderation_result.decision == "HUMAN_REVIEW":
        doc_row.status = "human_review"
        db.commit()
        db.close()

        return JSONResponse(
            status_code=202,
            content=moderation_result.model_dump()
        )

    # Safe image → continue extraction
    import time

    start_time = time.time()
    invoice = extract_invoice(str(saved_path))
    elapsed = time.time() - start_time
    extraction_latency_seconds.observe(elapsed)

    # Log the extraction (PII-redacted, never log raw invoice text)
    log_line = (
        f"[INGEST] document_id={doc_row.id} "
        f"extracted={invoice.model_dump_json()}"
    )
    print(redact_pii(log_line))

    # 4. Run confidence routing
    result = route_invoice(invoice, threshold=0.75)

    # 5. Update the database record
    doc_row.extracted_json = invoice.model_dump_json()
    doc_row.status = result.status

    db.commit()
    db.refresh(doc_row)
    db.close()

    # Update metrics
    documents_total.inc()
    if result.status == "auto_approved":
        auto_approvals_total.inc()
    else:
        pending_review_queue_size.inc()

    return JSONResponse({
        "document_id": doc_row.id,
        "status": result.status,
        "flagged_fields": [f.model_dump() for f in result.flagged_fields],
        "invoice": invoice.model_dump(),
    })

@app.get("/images/{document_id}/{filename}")
def get_image(document_id: str, filename: str):
    image_path = BASE_DIR / "uploads" / document_id / filename
    if not image_path.exists():
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    return FileResponse(image_path)

@app.get("/review")
def get_pending_reviews():
    db = SessionLocal()
    pending = db.query(Document).filter(Document.status == "pending_review").all()
    db.close()

    return [
        {
            "document_id": doc.id,
            "filename": doc.filename,
            "extracted_json": doc.extracted_json,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in pending
    ]


@app.post("/approve/{document_id}")
def approve_document(document_id: int, corrected_json: InvoiceSchema):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == document_id).first()

    if doc is None:
        db.close()
        return JSONResponse(status_code=404, content={"error": "Document not found"})

    if doc.status not in ("pending_review",):
        db.close()
        return JSONResponse(
            status_code=400,
            content={"error": f"Document {document_id} is '{doc.status}', not pending review — refusing to overwrite."},
        )

    doc.reviewed_json = corrected_json.model_dump_json()
    doc.status = "approved"
    db.commit()
    db.close()

    pending_review_queue_size.dec()

    return {"document_id": document_id, "status": "approved"}

@app.get("/documents")
def list_documents():
    db = SessionLocal()
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    db.close()

    return [
        {
            "document_id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in docs
    ]