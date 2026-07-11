import re


SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_PATTERN = re.compile(r"\+?[\d\s\-]{10,}")

# Common date shapes: 01-07-2026, 01/07/26, 2026-07-01, etc.
DATE_PATTERN = re.compile(r"^\d{1,4}[/-]\d{1,2}[/-]\d{1,4}$")


def _redact_phone_match(match: re.Match) -> str:
    matched_text = match.group().strip()
    if DATE_PATTERN.match(matched_text):
        return match.group()  # looks like a date, leave untouched
    return "[REDACTED-PHONE]"


def redact_pii(text: str) -> str:
    text = SSN_PATTERN.sub("[REDACTED-SSN]", text)
    text = EMAIL_PATTERN.sub("[REDACTED-EMAIL]", text)
    text = PHONE_PATTERN.sub(_redact_phone_match, text)
    return text