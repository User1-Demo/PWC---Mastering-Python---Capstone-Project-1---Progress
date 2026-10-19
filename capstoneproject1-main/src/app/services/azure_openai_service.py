from openai import AzureOpenAI

from src.app.core.config_ai import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
)

if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
    client = None
else:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )


def get_embedding(text: str) -> list[float]:
    if client is None:
        raise ValueError("Azure OpenAI client is not configured")

    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=text,
    )
    return response.data[0].embedding


def get_embeddings(texts: list[str]) -> list[list[float]]:
    if client is None:
        raise ValueError("Azure OpenAI client is not configured")

    if not texts:
        return []

    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=texts,
    )
    return [item.embedding for item in response.data]


def generate_answer(prompt: str) -> tuple[str, int | None]:
    if client is None:
        raise ValueError("Azure OpenAI client is not configured")

    response = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an insurance policy and claims assistant. "
                    "Answer only from the provided context. "
                    "Do not fabricate policy clauses or amounts. "
                    "If the context is insufficient, clearly say: "
                    "'No relevant information was found in the approved documents.'"
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=500,
    )

    answer = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else None

    return answer.strip(), tokens_used