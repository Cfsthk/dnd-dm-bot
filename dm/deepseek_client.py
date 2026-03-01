from __future__ import annotations
from openai import AsyncOpenAI
import config

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )
    return _client


async def chat(messages: list[dict], temperature: float = 0.85, max_tokens: int = 1024) -> str:
    client = get_client()
    response = await client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


async def chat_json(messages: list[dict], temperature: float = 0.3) -> str:
    """For structured outputs like character sheet generation."""
    client = get_client()
    response = await client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content.strip()