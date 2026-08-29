from __future__ import annotations
import json
import httpx
from app.core.config import get_settings

SYSTEM_PROMPT = """You are DevGuard AI, a senior secure-code reviewer. Summarize the most important risks and practical fixes. Be concise. Never claim you executed the code. Return plain text with sections: Summary, Highest-risk issues, Recommended next steps."""


async def enhance_review(code: str, language: str, findings: list[dict]) -> str | None:
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider in {"", "disabled", "none"}:
        return None

    payload_text = json.dumps(findings[:25], ensure_ascii=False)
    user_prompt = f"Language: {language}\nStatic findings: {payload_text}\n\nCode:\n{code[:20000]}"

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            if provider == "ollama":
                response = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                    json={
                        "model": settings.ollama_model,
                        "stream": False,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
                response.raise_for_status()
                return response.json().get("message", {}).get("content")

            if provider == "openai_compatible":
                headers = {"Authorization": f"Bearer {settings.llm_api_key}"} if settings.llm_api_key else {}
                response = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json={
                        "model": settings.llm_model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"LLM enhancement unavailable: {type(exc).__name__}. Static analysis completed successfully."

    return None
