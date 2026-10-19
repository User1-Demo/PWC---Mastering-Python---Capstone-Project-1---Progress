from pathlib import Path

import pytest

from claimiq.services.text_extraction_service import (
    clean_text,
    extract_text,
)


def test_clean_text_removes_extra_whitespace() -> None:
    text = "  Policy   coverage  \n\n\n  details  "

    result = clean_text(text)

    assert result == "Policy coverage\n\ndetails"


def test_extract_text_from_txt_file(tmp_path: Path) -> None:
    file_path = tmp_path / "policy.txt"

    file_path.write_text(
        "Collision coverage includes vehicle damage.",
        encoding="utf-8",
    )

    result = extract_text(file_path)

    assert result == (
        "Collision coverage includes vehicle damage."
    )


def test_extract_text_rejects_unsupported_extension(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "policy.exe"
    file_path.write_bytes(b"invalid file")

    with pytest.raises(
        ValueError,
        match="Unsupported document type",
    ):
        extract_text(file_path)


def test_extract_text_rejects_missing_file(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "missing.txt"

    with pytest.raises(
        FileNotFoundError,
        match="Document file not found",
    ):
        extract_text(file_path)


def test_extract_text_rejects_empty_file(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="No readable text",
    ):
        extract_text(file_path)