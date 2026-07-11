import sys, os
sys.path.append(os.path.dirname(__file__))
from db import SessionLocal, Document

db = SessionLocal()
docs = db.query(Document).all()

for d in docs:
    print(f"ID: {d.id}")
    print(f"  filename: {d.filename}")
    print(f"  status: {d.status}")
    print(f"  reviewed_json: {d.reviewed_json}")
    print()

db.close()