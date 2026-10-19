from collections.abc import Iterable


def chunk_pages(
    pages: Iterable[tuple[int | None, str]],
    *,
    chunk_size: int,
    overlap: int,
) -> list[tuple[str, str | None, int | None]]:
    """Split extracted text into overlapping chunks, retaining page and heading."""
    chunks: list[tuple[str, str | None, int | None]] = []
    for page_number, text in pages:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            continue
        heading: str | None = None
        for line in lines:
            if len(line) <= 120 and (
                line.isupper() or line.endswith(":") or line.istitle()
            ):
                heading = line[:255]
                break

        normalized = "\n".join(lines)
        start = 0
        while start < len(normalized):
            end = min(start + chunk_size, len(normalized))
            content = normalized[start:end].strip()
            if content:
                chunks.append((content, heading, page_number))
            if end == len(normalized):
                break
            start = max(start + 1, end - overlap)
    return chunks
