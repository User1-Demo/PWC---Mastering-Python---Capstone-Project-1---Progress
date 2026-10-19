import pytest

from claimiq.services.text_chunking_service import chunk_text


def test_chunk_text_creates_expected_chunks() -> None:
    text = "one two three four five six seven eight nine ten"

    result = chunk_text(
        text,
        chunk_size=5,
        overlap=2,
    )

    assert result == [
        "one two three four five",
        "four five six seven eight",
        "seven eight nine ten",
    ]


def test_short_text_returns_one_chunk() -> None:
    result = chunk_text(
        "one two three",
        chunk_size=5,
        overlap=2,
    )

    assert result == ["one two three"]


def test_empty_text_returns_empty_list() -> None:
    result = chunk_text(
        "",
        chunk_size=5,
        overlap=2,
    )

    assert result == []


def test_whitespace_only_text_returns_empty_list() -> None:
    result = chunk_text(
        "   \n\t  ",
        chunk_size=5,
        overlap=2,
    )

    assert result == []


def test_invalid_chunk_size_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_size must be greater than zero",
    ):
        chunk_text(
            "one two three",
            chunk_size=0,
            overlap=0,
        )


def test_negative_overlap_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="overlap cannot be negative",
    ):
        chunk_text(
            "one two three",
            chunk_size=5,
            overlap=-1,
        )


def test_overlap_equal_to_chunk_size_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="overlap must be smaller than chunk_size",
    ):
        chunk_text(
            "one two three",
            chunk_size=5,
            overlap=5,
        )


def test_overlap_greater_than_chunk_size_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="overlap must be smaller than chunk_size",
    ):
        chunk_text(
            "one two three",
            chunk_size=5,
            overlap=6,
        )