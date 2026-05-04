"""LLM Client adapter — Anthropic Claude veya OpenAI arasında geçiş.

v3.1: gpt-4o-mini → Claude Opus 4.7 (Anthropic). Bilgi doğruluğu ve nüans
yakalama nedenleriyle. OpenAI fallback env değişkeniyle aktif edilebilir
(LLM_PROVIDER=openai).

JSON çıktı garantisi:
  - Anthropic: tool_use (forced tool_choice) ile structured input garantisi.
  - OpenAI: response_format=json_object kullanılır.
"""

import json

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "LLMClient")


class LLMClient:
    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "anthropic").lower()
        if self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.WRITER_MODEL  # "claude-opus-4-7"
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.WRITER_MODEL

    def chat_json(self, system: str, user: str,
                  max_tokens: int = 2500, temperature: float = 0.7) -> dict:
        """JSON dict döner. Hata olursa boş dict + ops log."""
        if self.provider == "anthropic":
            return self._anthropic_json(system, user, max_tokens, temperature)
        return self._openai_json(system, user, max_tokens, temperature)

    _SUBMIT_TOOL = {
        "name": "submit_response",
        "description": (
            "Submit your structured response as a JSON object. "
            "Include all fields specified in the user's instructions."
        ),
        "input_schema": {
            "type": "object",
            # Permissive schema: prompt'taki JSON şablonu alanları belirler
            "additionalProperties": True,
        },
    }

    def _anthropic_json(self, system: str, user: str,
                        max_tokens: int, temperature: float) -> dict:
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system + "\n\nUse the submit_response tool to return your JSON answer.",
                messages=[{"role": "user", "content": user}],
                tools=[self._SUBMIT_TOOL],
                tool_choice={"type": "tool", "name": "submit_response"},
            )
            for b in resp.content:
                if getattr(b, "type", "") == "tool_use" and b.name == "submit_response":
                    return dict(b.input)
            ops.error("Anthropic: submit_response tool block bulunamadı", message=str(resp.content)[:300])
            return {}
        except Exception as e:
            ops.error("Anthropic JSON çağrısı başarısız", exception=e)
            return {}

    def _openai_json(self, system: str, user: str,
                     max_tokens: int, temperature: float) -> dict:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            ops.error("OpenAI JSON çağrısı başarısız", exception=e)
            return {}
