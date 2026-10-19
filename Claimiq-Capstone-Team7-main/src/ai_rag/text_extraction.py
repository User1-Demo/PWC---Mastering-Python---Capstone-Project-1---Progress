"""
text_extraction.py (ai_rag module)

Purpose: Extracts raw text from uploaded document files (PDF/DOCX/TXT).
"""

import pdfplumber
from docx import Document as DocxDocument
from pathlib import Path


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext == ".docx":
        return _extract_from_docx(file_path)
    elif ext == ".txt":
        return _extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type for extraction: {ext}")


def _extract_from_pdf(file_path: str) -> str:
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_from_docx(file_path: str) -> str:
    doc = DocxDocument(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text)


def _extract_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()