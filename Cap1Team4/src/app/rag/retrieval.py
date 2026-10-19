import re
from collections import Counter
from math import log

from app.models.document import DocumentChunk

_STOP_WORDS = {
    "about", "after", "also", "and", "are", "can", "does", "for", "from",
    "how", "into", "its", "what", "when", "where", "which", "with", "would",
    "your", "the", "this", "that", "was", "were", "will", "who", "why",
}


def terms(text: str) -> list[str]:
    return [
        word
        for word in re.findall(r"[a-z0-9]{3,}", text.lower())
        if word not in _STOP_WORDS
    ]


def rank_chunks(
    question: str,
    chunks: list[DocumentChunk],
    *,
    top_k: int,
) -> list[tuple[float, DocumentChunk]]:
    query_terms = set(terms(question))
    if not query_terms or not chunks:
        return []

    tokenized = [terms(f"{chunk.content} {chunk.section_heading or ''}") for chunk in chunks]
    document_frequency = Counter(
        term for tokens in tokenized for term in query_terms if term in set(tokens)
    )
    total_docs = len(chunks)
    scored: list[tuple[float, DocumentChunk]] = []
    for chunk, tokens in zip(chunks, tokenized):
        counts = Counter(tokens)
        matched = query_terms.intersection(counts)
        if not matched:
            continue
        weighted = sum(
            (1 + log((total_docs + 1) / (document_frequency[term] + 1)))
            * min(counts[term], 3)
            for term in matched
        )
        coverage = len(matched) / len(query_terms)
        score = coverage * min(1.0, weighted / (len(matched) * 2))
        if score >= 0.15:
            scored.append((score, chunk))
    scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    return scored[:top_k]


def grounded_answer(results: list[tuple[float, DocumentChunk]]) -> str:
    if not results:
        return "No relevant content was found in active approved documents."

    excerpts: list[str] = []
    seen: set[str] = set()
    for _, chunk in results:
        excerpt = " ".join(chunk.content.split())
        if excerpt and excerpt not in seen:
            excerpts.append(excerpt)
            seen.add(excerpt)
    return "Relevant excerpts from approved documents:\n" + "\n".join(
        f"- {excerpt}" for excerpt in excerpts
    )
