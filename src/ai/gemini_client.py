import json
import logging
import time
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_RETRIES = 3
RETRY_BASE_SECONDS = 2.0


class GeminiClient:
    """Unified wrapper for Google Gemini generate + embed calls."""

    def __init__(self, api_key: str | None = None):
        key = api_key or settings.google_api_key
        if not key or key == "placeholder":
            raise ValueError("GOOGLE_API_KEY is not configured")
        self.client = genai.Client(api_key=key)

    def _retry_call(self, operation: str, func):
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                return func()
            except Exception as exc:
                last_error = exc
                error_text = str(exc).lower()
                if "api_key_invalid" in error_text or "api key not valid" in error_text:
                    raise
                wait = RETRY_BASE_SECONDS * (2**attempt)
                logger.warning(
                    "%s failed (attempt %s/%s): %s — retrying in %.1fs",
                    operation,
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                time.sleep(wait)
        raise RuntimeError(f"{operation} failed after {MAX_RETRIES} attempts") from last_error

    def generate_json(
        self,
        prompt: str,
        schema_model: type[BaseModel],
        *,
        model: str | None = None,
        system_instruction: str | None = None,
    ) -> dict[str, Any]:
        model_name = model or settings.gemini_enrichment_model

        def _call():
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema_model.model_json_schema(),
                temperature=0.2,
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            text = response.text or "{}"
            logger.debug("Gemini generate_json tokens/model=%s", model_name)
            return json.loads(text)

        return self._retry_call(f"generate_json({model_name})", _call)

    def embed(self, text: str, *, model: str | None = None) -> list[float]:
        model_name = model or settings.gemini_embedding_model
        output_dim = settings.vector_dimension

        def _call():
            response = self.client.models.embed_content(
                model=model_name,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=output_dim),
            )
            if not response.embeddings:
                raise RuntimeError("No embeddings returned from Gemini")
            values = response.embeddings[0].values
            if not values:
                raise RuntimeError("Empty embedding vector from Gemini")
            if len(values) != output_dim:
                raise RuntimeError(
                    f"Expected {output_dim}-dim embedding, got {len(values)} from {model_name}"
                )
            return list(values)

        return self._retry_call(f"embed({model_name})", _call)
