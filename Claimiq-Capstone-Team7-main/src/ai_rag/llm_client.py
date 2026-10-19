"""
llm_client.py (ai_rag module)

Purpose: Wraps the Azure OpenAI chat completion call.
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

CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")


def generate_answer(messages: list[dict]) -> dict:
    """
    Returns: {"answer": str, "prompt_tokens": int, "completion_tokens": int}
    """
    response = _client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=messages,
        temperature=0,  # deterministic - reduces hallucination risk
        max_tokens=500,
    )

    return {
        "answer": response.choices[0].message.content,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
    }