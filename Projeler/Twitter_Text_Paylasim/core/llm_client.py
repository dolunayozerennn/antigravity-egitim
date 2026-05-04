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
                  max_tokens: int = 2500, temperature: float = 0.7,
                  schema: dict | None = None) -> dict:
        """JSON dict döner. Hata olursa boş dict + ops log.

        schema (Anthropic): tool input_schema olarak kullanılır. None ise permissive
        ('additionalProperties: True') şema. Claude permissive şemada bazen çıktıyı
        {"response": {...}} ile sarmalıyor — explicit schema bunu engeller.
        """
        if self.provider == "anthropic":
            return self._anthropic_json(system, user, max_tokens, schema)
        return self._openai_json(system, user, max_tokens, temperature)

    _PERMISSIVE_SCHEMA = {
        "type": "object",
        "additionalProperties": True,
    }

    def _anthropic_json(self, system: str, user: str,
                        max_tokens: int, schema: dict | None) -> dict:
        # NOT: Claude Opus 4.7 `temperature` parametresini deprecate etti.
        # Anthropic çağrılarında temperature kullanılmıyor; OpenAI'da kullanılmaya devam ediyor.
        tool = {
            "name": "submit_response",
            "description": (
                "Submit your structured response. Fill the fields exactly as defined "
                "in input_schema; do not wrap in any container field."
            ),
            "input_schema": schema or self._PERMISSIVE_SCHEMA,
        }
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system + "\n\nUse the submit_response tool to return your answer. "
                                "Fill the schema fields directly — do NOT nest your output under any 'response' key.",
                messages=[{"role": "user", "content": user}],
                tools=[tool],
                tool_choice={"type": "tool", "name": "submit_response"},
            )
            for b in resp.content:
                if getattr(b, "type", "") == "tool_use" and b.name == "submit_response":
                    inp = dict(b.input) if b.input else {}
                    # Claude bazen permissive schema'ya {"response": {...}} şeklinde sarmalıyor — unwrap
                    if len(inp) == 1 and "response" in inp and isinstance(inp["response"], dict):
                        inp = inp["response"]
                    if not inp:
                        ops.warning(
                            "Anthropic: tool_use input boş",
                            f"stop_reason={resp.stop_reason}"
                        )
                    return inp
            ops.error(
                "Anthropic: submit_response tool block bulunamadı",
                message=f"stop_reason={resp.stop_reason}, blocks={[getattr(x,'type','?') for x in resp.content]}, raw={str(resp.content)[:400]}"
            )
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
