def clean_string(value: str) -> str:
    return value.strip()

def clean_email(value: str) -> str:
    return value.strip().lower()