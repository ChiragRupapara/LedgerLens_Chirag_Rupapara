import os
import sys
from pathlib import Path
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "schemas"))
from invoice import InvoiceSchema


class FlaggedField(BaseModel):
    field_path: str
    value: str
    confidence: float


class RoutingResult(BaseModel):
    invoice: InvoiceSchema
    status: str
    flagged_fields: list[FlaggedField]


def route_invoice(invoice: InvoiceSchema, threshold: float = 0.75) -> RoutingResult:
    flagged: list[FlaggedField] = []

    # Check overall confidence
    if invoice.overall_confidence < threshold:
        flagged.append(FlaggedField(
            field_path="overall_confidence",
            value=str(invoice.overall_confidence),
            confidence=invoice.overall_confidence,
        ))

    # Check each line item's confidence
    for i, item in enumerate(invoice.line_items):
        if item.confidence < threshold:
            flagged.append(FlaggedField(
                field_path=f"line_items[{i}].{item.description}",
                value=str(item.amount),
                confidence=item.confidence,
            ))

    status = "pending_review" if flagged else "auto_approved"

    return RoutingResult(invoice=invoice, status=status, flagged_fields=flagged)

if __name__ == "__main__":
    from pathlib import Path
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "services"))
    from extract import extract_invoice

    script_dir = Path(__file__).parent
    image_path = script_dir / ".." / ".." / "sample_images" / "receipt2.jpg"

    invoice = extract_invoice(str(image_path))
    result = route_invoice(invoice, threshold=0.75)

    print(f"Status: {result.status}")
    print(f"Flagged fields: {len(result.flagged_fields)}")
    for f in result.flagged_fields:
        print(f"  - {f.field_path}: value={f.value}, confidence={f.confidence}")