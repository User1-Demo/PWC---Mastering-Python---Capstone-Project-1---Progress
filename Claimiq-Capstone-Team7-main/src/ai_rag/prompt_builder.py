"""
prompt_builder.py (ai_rag module)

Purpose: Builds the strictly-constrained prompt sent to the LLM.
This is where BR-005 ("no fabrication, cite sources") gets enforced
at the prompt level.
"""

SYSTEM_PROMPT = """You are ClaimIQ's policy assistant. Answer ONLY using the CONTEXT below.
Do not use any outside knowledge. If the answer is not clearly present in the
CONTEXT, respond exactly with: "No relevant information was found in the
approved documents for this question."
Always end your answer with a citation in the form: [Source: <document_title>]
Never fabricate policy clauses, numbers, or amounts that are not explicitly
stated in the CONTEXT."""


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    context_blocks = []
    for chunk in chunks:
        context_blocks.append(
            f"[Document: {chunk['document_title']}, Chunk {chunk['chunk_index']}]\n{chunk['text']}"
        )

    context_text = "\n\n---\n\n".join(context_blocks)

    user_message = f"""CONTEXT:
{context_text}

QUESTION:
{question}"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]