from app.document_processor import (
    clean_text,
    chunk_text,
)


def test_clean_text():
    text = """
    ClaimIQ     insurance

    policy      document
    """

    result = clean_text(text)

    assert "ClaimIQ insurance" in result
    assert "policy document" in result


def test_chunk_text():
    text = " ".join(
        f"word{i}"
        for i in range(2500)
    )

    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert all(
        len(chunk) > 0
        for chunk in chunks
    )


def test_empty_chunk_text():
    assert chunk_text("") == []