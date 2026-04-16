"""OpenAI-compatible client wrapper with DeepSeek fallback."""

import os
import json
import re
import time
import logging
from typing import Optional, Dict, Any
from config import settings

import openai

logger = logging.getLogger(__name__)

TIMEOUT_CLASSIFY = 30.0
TIMEOUT_EXTRACT = 60.0
TIMEOUT_GENERATE = 180.0


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(self, timeout: float = 180.0):
        self.model = settings.default_model
        self._timeout = timeout

        self._primary = self._build_zhipu()
        self._fallback = self._build_deepseek()

        self._fallback_until = 0.0

    def _build_zhipu(self) -> openai.AsyncOpenAI:
        api_key = settings.zhipu_api_key or os.getenv("ZHIPU_API_KEY", "")
        base_url = os.getenv("ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
        model = os.getenv("ZHIPU_MODEL", "glm-5.1")
        return openai.AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=self._timeout)
    
    def _build_deepseek(self) -> openai.AsyncOpenAI:
        api_key = settings.deepseek_api_key
        base_url = settings.deepseek_api_base
        return openai.AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=self._timeout)

    def _get_zhipu_model(self) -> str:
        return os.getenv("ZHIPU_MODEL", "glm-5.1")

    def _client_with_timeout(self, base_client: openai.AsyncOpenAI, timeout: float) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=base_client.api_key,
            base_url=base_client.base_url,
            timeout=timeout,
        )

    async def _call_with_fallback(self, call_fn, timeout: Optional[float] = None):
        primary = self._client_with_timeout(self._primary, timeout) if timeout else self._primary
        fallback = self._client_with_timeout(self._fallback, timeout) if timeout else self._fallback

        if time.time() < self._fallback_until:
            return await call_fn(fallback, settings.deepseek_model)

        try:
            result = await call_fn(primary, self._get_zhipu_model())
            return result
        except openai.RateLimitError:
            logger.warning("Primary model rate limited, switching to DeepSeek fallback for 60s")
            self._fallback_until = time.time() + 60
            return await call_fn(fallback, settings.deepseek_model)
        except openai.APITimeoutError:
            logger.warning("Primary model timeout, trying DeepSeek fallback")
            try:
                return await call_fn(fallback, settings.deepseek_model)
            except Exception:
                raise LLMClientError("LLM call timed out on both models") from None

    async def chat(self, prompt: str, temperature: float = 0.7, timeout: Optional[float] = None) -> str:
        async def _do(client, model):
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.choices[0].message.content

        try:
            return await self._call_with_fallback(_do, timeout=timeout)
        except LLMClientError:
            return "[AI Error: Request timed out]"
        except Exception as e:
            return f"[AI Error: {str(e)}]"

    @staticmethod
    def _repair_json(text: str) -> str:
        text = re.sub(r'//.*?(\n|$)', r'\1', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r',\s*([}\]])', r'\1', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        text = re.sub(r'(?<!\\)\'', '"', text)
        return text

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        repaired = self._repair_json(content)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'\{.*\}', repaired, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Invalid JSON after repair. First 200 chars: {content[:200]}")

    @staticmethod
    def _validate_output(result: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        for key, type_hint in schema.items():
            if key not in result:
                continue
            value = result[key]
            if isinstance(type_hint, list) and not isinstance(value, list):
                if isinstance(value, dict):
                    result[key] = list(value.values())
                else:
                    result[key] = []
            elif isinstance(type_hint, str) and not isinstance(value, str):
                result[key] = str(value) if value is not None else ""
        return result

    async def structured_output(
        self, prompt: str, schema: Dict[str, Any], timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        async def _do(client, model):
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt},
                    {
                        "role": "system",
                        "content": "只返回纯JSON，不要markdown格式、注释或额外说明。格式: " + json.dumps(schema, ensure_ascii=False),
                    },
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content or ""
            return self._parse_json_response(content)

        try:
            result = await self._call_with_fallback(_do, timeout=timeout)
            return self._validate_output(result, schema)
        except openai.RateLimitError:
            raise LLMClientError("Both models rate limited") from None
        except LLMClientError:
            raise
        except Exception as e:
            raise LLMClientError(f"LLM call failed: {str(e)}") from e


llm_client = LLMClient()
