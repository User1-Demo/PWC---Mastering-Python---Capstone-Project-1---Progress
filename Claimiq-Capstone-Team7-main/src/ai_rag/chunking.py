"""
chunking.py (ai_rag module)

Purpose: Splits extracted document text into overlapping chunks
suitable for embedding + retrieval.

Design decision: ~500 tokens per chunk, 50 token overlap - small
enough for precise retrieval, large enough to preserve context,
overlap prevents losing meaning at chunk boundaries.
"""

import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")  # matches GPT-4/embedding tokenization

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50


def count_tokens(text: str) -> int:
    return len(ENCODING.encode(text))


def chunk_text(text: str) -> list[str]:
    """
    Splits raw text into a list of chunks, each ~CHUNK_SIZE_TOKENS
    tokens long, overlapping by CHUNK_OVERLAP_TOKENS tokens with
    the previous chunk.
    """
    tokens = ENCODING.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + CHUNK_SIZE_TOKENS
        chunk_tokens = tokens[start:end]
        chunk_str = ENCODING.decode(chunk_tokens)
        chunks.append(chunk_str)

        start += CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS  # slide forward with overlap

    return chunks