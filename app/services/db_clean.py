import sys, os
sys.path.append(os.path.dirname(__file__))
from db import SessionLocal, Document

db = SessionLocal()
deleted_count = db.query(Document).delete()
db.commit()
db.close()

print(f"Deleted {deleted_count} document(s).")