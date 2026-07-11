import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "schemas"))
from invoice import InvoiceSchema

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_invoice(image_path: str) -> InvoiceSchema:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpg"),
            "Extract all invoice/receipt fields from this image.\n\n"
            "For EVERY field and EVERY line item, you must assign a genuinely "
            "calibrated confidence score between 0 and 1. Do not default to 1.0. "
            "Use this rubric strictly:\n"
            "- 0.95-1.0: text is printed, sharp, and completely unambiguous\n"
            "- 0.7-0.94: text is legible but has some blur, glare, or small print\n"
            "- 0.4-0.69: text is partially obscured, faded, or you are guessing "
            "between two plausible readings\n"
            "- 0.0-0.39: text is unreadable, cropped out, or you are inferring "
            "the value rather than reading it\n\n"
            "If a receipt is blurry, cropped, faded, or has handwriting, this "
            "should be reflected in LOWER confidence scores, not high ones. "
            "Be honest about uncertainty rather than optimistic.",
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": InvoiceSchema,
        },
    )

    return InvoiceSchema.model_validate_json(response.text)


if __name__ == "__main__":
    result = extract_invoice("../../sample_images/receipt2.jpg")
    print(result.model_dump_json(indent=2))
