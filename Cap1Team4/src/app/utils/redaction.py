import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d .()-]{7,}\d(?!\w)")
_NATIONAL_ID = re.compile(
    r"\b(?:national\s+id|identity\s+(?:number|no\.?))\s*[:#-]?\s*[A-Z0-9-]{5,}\b"
    r"|(?<![A-Z0-9])(?:[A-Z]{1,2}[- ]?)?\d{6,12}(?![A-Z0-9])",
    re.IGNORECASE,
)


def redact_pii(value: str) -> str:
    value = _EMAIL.sub("[redacted-email]", value)
    value = _PHONE.sub("[redacted-phone]", value)
    return _NATIONAL_ID.sub("[redacted-id]", value)
