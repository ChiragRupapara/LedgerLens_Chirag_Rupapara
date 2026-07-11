import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app", "schemas"))
from invoice import InvoiceSchema, LineItem


def test_valid_invoice_is_accepted():
    invoice = InvoiceSchema(
        vendor="Test Store",
        currency="USD",
        subtotal=10.0,
        tax=1.0,
        total=11.0,
        line_items=[
            LineItem(description="Widget", quantity=1, unit_price=10.0, amount=10.0, confidence=0.9)
        ],
        overall_confidence=0.9,
    )
    assert invoice.vendor == "Test Store"
    assert invoice.total == 11.0
    assert len(invoice.line_items) == 1

def test_invalid_confidence_is_rejected():
    with pytest.raises(Exception):
        InvoiceSchema(
            vendor="Test Store",
            currency="USD",
            subtotal=10.0,
            tax=1.0,
            total=11.0,
            line_items=[],
            overall_confidence=1.5,  # invalid — must be <= 1
        )    

def test_invoice_round_trips_through_json():
    original = InvoiceSchema(
        vendor="Round Trip Test",
        currency="AED",
        subtotal=100.0,
        tax=5.0,
        total=105.0,
        line_items=[
            LineItem(description="Item A", quantity=2, unit_price=50.0, amount=100.0, confidence=0.99)
        ],
        overall_confidence=0.95,
    )

    json_string = original.model_dump_json()
    reconstructed = InvoiceSchema.model_validate_json(json_string)

    assert reconstructed.vendor == original.vendor
    assert reconstructed.total == original.total
    assert reconstructed.line_items[0].description == original.line_items[0].description
    assert reconstructed == original        