import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app", "schemas"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app", "services"))

from invoice import InvoiceSchema, LineItem
from router import route_invoice


def make_test_invoice(overall_confidence, line_item_confidence):
    return InvoiceSchema(
        vendor="Test Vendor",
        currency="USD",
        subtotal=10.0,
        tax=0.0,
        total=10.0,
        line_items=[
            LineItem(description="Item", quantity=1, unit_price=10.0, amount=10.0, confidence=line_item_confidence)
        ],
        overall_confidence=overall_confidence,
    )


def test_high_confidence_is_auto_approved():
    invoice = make_test_invoice(overall_confidence=0.95, line_item_confidence=0.95)
    result = route_invoice(invoice, threshold=0.75)

    assert result.status == "auto_approved"
    assert len(result.flagged_fields) == 0


def test_low_confidence_is_flagged_for_review():
    invoice = make_test_invoice(overall_confidence=0.5, line_item_confidence=0.5)
    result = route_invoice(invoice, threshold=0.75)

    assert result.status == "pending_review"
    assert len(result.flagged_fields) == 2  # both overall AND the line item


def test_confidence_exactly_at_threshold_passes():
    invoice = make_test_invoice(overall_confidence=0.75, line_item_confidence=0.75)
    result = route_invoice(invoice, threshold=0.75)

    assert result.status == "auto_approved"