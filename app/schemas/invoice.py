from pydantic import BaseModel, Field
from typing import Optional


class LineItem(BaseModel):
    description: str = Field(description="What was purchased")
    quantity: float = Field(description="How many units")
    unit_price: float = Field(description="Price per single unit")
    amount: float = Field(description="quantity * unit_price")
    confidence: float = Field(
        description="Model's confidence in this line, 0 to 1", ge=0, le=1)


class InvoiceSchema(BaseModel):
    vendor: str = Field(
        description="Name of the store or company that issued the invoice")
    invoice_number: Optional[str] = Field(
        default=None, description="Invoice or receipt number, if present")
    date: Optional[str] = Field(
        default=None, description="Date on the invoice, as written")
    currency: str = Field(description="Currency code, e.g. USD, INR, EUR")
    subtotal: float = Field(description="Sum before tax")
    tax: float = Field(default=0.0, description="Tax amount")
    total: float = Field(description="Final total amount charged")
    line_items: list[LineItem] = Field(
        description="Every individual item purchased")
    overall_confidence: float = Field(
        description="Model's overall confidence in the extraction", ge=0, le=1)
