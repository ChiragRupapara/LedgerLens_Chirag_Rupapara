import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from moderation_schemas import ModerationResult

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def moderate_image(image_path: str):
    """
    Returns:
        {
            "decision": "ALLOW" | "BLOCK" | "HUMAN_REVIEW",
            "reason": "Explanation"
        }
    """

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            ),
            """
            You are an image moderation system.

            Look at the uploaded image.

            Return ONLY valid JSON.

            Possible decisions:

            ALLOW
            BLOCK
            HUMAN_REVIEW

            Rules:

            ALLOW   
            - Receipt
            - Invoice
            - Bill
            - Business document

            BLOCK
            - Nudity
            - Sexual content
            - Graphic violence
            - Hate symbols
            - Illegal content

            HUMAN_REVIEW
            - Blurry image
            - Cannot determine content
            - Ambiguous image

            Return JSON only:

            {
                "decision": "...",
                "reason": "..."
            }
            """
                ],
        config={
            "response_mime_type": "application/json",
        },
    )

    import json

    try:
        result = json.loads(response.text)

        decision = result.get("decision", "HUMAN_REVIEW")

        if decision not in ["ALLOW", "BLOCK", "HUMAN_REVIEW"]:
            decision = "HUMAN_REVIEW"

        return ModerationResult(
            decision=decision,
            reason=result.get("reason", "No reason provided")
        )

    except Exception:
        return ModerationResult(
            decision="HUMAN_REVIEW",
            reason="Unable to parse Gemini moderation response."
        )