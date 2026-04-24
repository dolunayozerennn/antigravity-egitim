---
name: llm-structured-output-rules
description: Official best practices for enforcing structured JSON outputs from Large Language Models (LLMs) across all providers (OpenAI, Anthropic, Groq, etc.). Eliminates hallucinated text parsing errors by mandating Pydantic schemas.
license: MIT
metadata:
  author: antigravity
  version: "1.0.0"
  organization: Antigravity
  date: April 2026
  abstract: Defines the standard operating procedures for integrating LLM outputs into automated pipelines. Mandates the shift from "prompt engineering with regex parsing" to "schema-driven structured outputs" using tools like the Instructor library or native JSON schema parameters. This ensures data integrity and prevents downstream crashes in Antigravity projects.
---

# LLM Structured Output Rules (AI Best Practices)

In Antigravity automation projects, LLMs are not just chatbots; they are data processors and decision engines. Relying on an LLM to return plain text and then using `regex` or `split()` to parse the data is strictly forbidden. It is fragile and leads to system crashes.

**You must always enforce Structured Output (JSON) strictly validated against a schema.**

## 1. Provider-Agnostic Approach

This rule applies to ALL LLM providers used in the Antigravity ecosystem:
- OpenAI (GPT-4o, etc.)
- Anthropic (Claude 3.5 Sonnet, etc.)
- Groq (Llama 3, Mixtral, etc.)
- Gemini

## 2. The Golden Rule: Pydantic First

- **Rule:** Define the expected output structure using Python's `pydantic` library before writing the LLM call.
- **Action:** Create a `BaseModel` class that strictly defines the types, constraints, and descriptions of the data you want the LLM to extract or generate.

```python
from pydantic import BaseModel, Field
from typing import Optional

class LeadScore(BaseModel):
    is_qualified: bool = Field(description="True if the business meets the criteria.")
    estimated_budget: Optional[int] = Field(description="Estimated budget in USD. Null if unknown.")
    reasoning: str = Field(description="Short explanation of the decision.")
```

## 3. Recommended Tools & Implementation

### Option A: The `instructor` Library (Highly Recommended)
The `instructor` library patches existing SDKs (OpenAI, Anthropic, Groq) to natively return Pydantic objects. This is the preferred method for Antigravity.

```python
import instructor
from openai import AsyncOpenAI
import os

# Patch the client
client = instructor.from_openai(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

async def score_lead(text: str) -> LeadScore:
    return await client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=LeadScore, # <--- Magic happens here
        messages=[{"role": "user", "content": text}],
    )
```

### Option B: Native Structured Outputs (e.g., OpenAI `response_format`)
If you prefer not to add dependencies, use the native structured output features of the latest APIs (like OpenAI's `response_format={"type": "json_schema", "json_schema": {"strict": True, "name": "...", "schema": ...}}`).

## 4. Prompt Engineering for Schemas

Even with strict schema enforcement, the LLM still needs guidance.
- **Rule:** Include field-level instructions in your Pydantic `Field(description="...")` tags. The LLM reads these descriptions as prompt instructions.
- **Fallback Rule:** Always provide an "escape hatch" in the schema. For example, use `Optional[str]` or define an `error_message` field in the schema so the LLM can cleanly indicate if it failed to find the data, rather than hallucinating fake data to satisfy the schema.

## 5. Retry Mechanisms & Error Handling

- **Rule:** Anticipate validation failures.
- **Action:** If the LLM returns data that violates the schema, `pydantic` will raise a `ValidationError`. You MUST catch this error, log it as a P2 warning, and implement a retry mechanism (often, `instructor` handles retries automatically if configured with `max_retries`).
