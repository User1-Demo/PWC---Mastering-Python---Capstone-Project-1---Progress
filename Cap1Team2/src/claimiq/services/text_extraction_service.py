import re
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
}


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted text."""

    text = text.replace("\x00", "")

    # Remove spaces and tabs around newline characters.
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)

    # Collapse repeated spaces and tabs.
    text = re.sub(r"[ \t]+", " ", text)

    # Keep a maximum of one blank line between paragraphs.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_text_from_txt(file_path: Path) -> str:
    """Extract text from a plain-text file."""

    return file_path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""

    from pypdf import PdfReader

    reader = PdfReader(str(file_path))

    pages: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""

        if page_text.strip():
            pages.append(page_text)

    return "\n\n".join(pages)


def extract_text_from_docx(file_path: Path) -> str:
    """Extract paragraph text from a DOCX file."""

    from docx import Document as DocxDocument

    document = DocxDocument(str(file_path))

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n\n".join(paragraphs)


def extract_text(file_path: str | Path) -> str:
    """Extract and clean text based on the file extension."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document file not found: {path}",
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))

        raise ValueError(
            f"Unsupported document type. "
            f"Allowed extensions: {allowed}",
        )

    if extension == ".txt":
        text = extract_text_from_txt(path)
    elif extension == ".pdf":
        text = extract_text_from_pdf(path)
    else:
        text = extract_text_from_docx(path)

    cleaned_text = clean_text(text)

    if not cleaned_text:
        raise ValueError(
            "No readable text was found in the document",
        )

    return cleaned_text