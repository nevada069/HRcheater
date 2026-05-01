import json
from openai import AsyncOpenAI
from config import GROQ_API_KEY

_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

MODEL = "llama-3.3-70b-versatile"


async def llm_json(prompt: str, temperature: float = 0.5) -> dict:
    """Один вызов LLM, всегда возвращает dict (JSON-режим)."""
    response = await _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
