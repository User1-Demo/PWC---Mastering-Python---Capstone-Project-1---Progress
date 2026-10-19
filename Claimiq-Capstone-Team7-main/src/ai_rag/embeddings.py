"""
embeddings.py (ai_rag module)

Purpose: Wraps Azure OpenAI's embedding model. Every other file that
needs a vector calls through here - keeps the actual API call in
ONE place.
"""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")


def embed_text(text: str) -> list[float]:
    """Returns a single embedding vector for one piece of text."""
    response = _client.embeddings.create(model=EMBEDDING_DEPLOYMENT, input=text)
    return response.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embeds multiple texts in one API call - more efficient than
    calling embed_text() in a loop when processing many chunks at once.
    """
    response = _client.embeddings.create(model=EMBEDDING_DEPLOYMENT, input=texts)
    return [item.embedding for item in response.data]