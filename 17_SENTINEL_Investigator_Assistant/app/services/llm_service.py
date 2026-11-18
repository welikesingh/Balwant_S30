"""LLM client: send the grounded prompt, get back a validated LLMExplanation.

Gemini is asked for JSON matching the Pydantic schema, and the reply is validated
with Pydantic again. An invalid reply is retried; if the primary model is overloaded
(503/504) the next model in the fallback list is tried. If nothing produces a valid
reply we raise LLMUnavailable. We never make up an explanation.
"""
import logging
import time

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.models.schemas import LLMExplanation

logger = logging.getLogger(__name__)

OVERLOADED = {500, 503, 504}


class LLMUnavailable(Exception):
    """The LLM could not produce a valid explanation."""


class GeminiExplainer:
    def __init__(self, api_key: str, model: str, temperature: float = 0.0,
                 timeout_seconds: int = 90, attempts_per_model: int = 2,
                 fallback_models: list[str] | None = None):
        self._client = genai.Client(api_key=api_key,
                                    http_options=types.HttpOptions(timeout=timeout_seconds * 1000))
        self.models = [model] + [m for m in (fallback_models or []) if m != model]
        self.temperature = temperature
        self.attempts_per_model = attempts_per_model

    def explain(self, system_instruction: str, user_prompt: str) -> tuple[LLMExplanation, int, str]:
        """Returns (validated explanation, total attempts used, model that answered)."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.temperature,
            response_mime_type="application/json",
            response_schema=LLMExplanation,
        )
        attempts, last_error = 0, "no model configured"
        for model in self.models:
            for _ in range(self.attempts_per_model):
                attempts += 1
                try:
                    response = self._client.models.generate_content(
                        model=model, contents=user_prompt, config=config)
                    return LLMExplanation.model_validate_json(response.text or ""), attempts, model
                except ValidationError as exc:
                    last_error = f"{model}: invalid JSON ({exc.error_count()} validation errors)"
                except errors.APIError as exc:
                    last_error = f"{model}: API error {exc.code} {exc.status}"
                    if exc.code == 429:
                        time.sleep(20)            # rate limit: wait, then retry
                    elif exc.code in OVERLOADED:
                        logger.warning("LLM %s overloaded, trying next model", model)
                        break                     # overloaded: move to the next model
                    else:
                        break                     # e.g. 404 model not available
                except Exception as exc:          # network problems
                    last_error = f"{model}: {type(exc).__name__}"
                logger.warning("LLM attempt %d failed: %s", attempts, last_error)
        raise LLMUnavailable(last_error)
