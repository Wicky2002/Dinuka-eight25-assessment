import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, cast

import google.genai as genai
from dotenv import load_dotenv

from app.models import AIAnalysis


class AIAnalyzer:
    def __init__(self, model_name: str = "gemini-1.5-flash") -> None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from environment.")

        self._system_prompt = self._build_system_prompt()
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def analyze(self, metrics: Dict[str, Any], page_text: str) -> AIAnalysis:
        user_prompt = self._build_user_prompt(metrics, page_text)
        analysis = self._request_analysis(user_prompt, metrics, page_text)
        if not self._recommendation_count_ok(analysis):
            retry_prompt = self._build_retry_prompt(metrics, page_text)
            analysis = self._request_analysis(retry_prompt, metrics, page_text)
        return analysis

    def _build_system_prompt(self) -> str:
        return (
            "You are a Senior EIGHT25MEDIA Marketing & CRO Strategist. "
            "You MUST ground all insights ONLY in the provided factual metrics and text. "
            "Do not invent facts. If the data is insufficient, state 'Insufficient evidence.' "
            "Recommendations MUST cite concrete metrics or text evidence in the reasoning. "
            "Provide 0-100 SEO and UX scores based on the factual metrics, then predict "
            "potential 0-100 scores if all recommendations are implemented. "
            "Return 3 to 5 recommendations, prioritized. "
            "Return strictly valid JSON that matches the provided schema."
        )

    def _build_user_prompt(self, metrics: Dict[str, Any], page_text: str) -> str:
        safe_text = page_text[:4000]
        return (
            "Analyze the following website metrics and page text. "
            "Use only this information.\n\n"
            f"Metrics (JSON): {json.dumps(metrics, ensure_ascii=True)}\n\n"
            "Page text (truncated):\n"
            f"{safe_text}"
        )

    def _build_retry_prompt(self, metrics: Dict[str, Any], page_text: str) -> str:
        safe_text = page_text[:4000]
        return (
            "Regenerate the analysis. "
            "Return exactly 3 to 5 recommendations, prioritized, and grounded in the data.\n\n"
            f"Metrics (JSON): {json.dumps(metrics, ensure_ascii=True)}\n\n"
            "Page text (truncated):\n"
            f"{safe_text}"
        )

    def _request_analysis(
        self, user_prompt: str, metrics: Dict[str, Any], page_text: str
    ) -> AIAnalysis:
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=user_prompt,
                config=cast(
                    Any,
                    {
                        "systemInstruction": self._system_prompt,
                        "responseMimeType": "application/json",
                        "responseSchema": AIAnalysis,
                    },
                ),
            )
        except Exception as exc:
            if self._is_model_not_found(exc):
                fallback_model = self._resolve_model_name()
                if fallback_model and fallback_model != self._model_name:
                    self._model_name = fallback_model
                    response = self._client.models.generate_content(
                        model=self._model_name,
                        contents=user_prompt,
                        config=cast(
                            Any,
                            {
                                "systemInstruction": self._system_prompt,
                                "responseMimeType": "application/json",
                                "responseSchema": AIAnalysis,
                            },
                        ),
                    )
                else:
                    raise
            else:
                raise

        raw_json_output = response.text or ""
        self._append_prompt_log(
            self._system_prompt,
            user_prompt,
            raw_json_output,
            metrics,
            page_text,
        )

        try:
            parsed = json.loads(raw_json_output)
        except json.JSONDecodeError as exc:
            raise ValueError("AI response is not valid JSON.") from exc

        return AIAnalysis.model_validate(parsed)

    def _recommendation_count_ok(self, analysis: AIAnalysis) -> bool:
        count = len(analysis.recommendations)
        return 3 <= count <= 5

    def _is_model_not_found(self, exc: Exception) -> bool:
        message = str(exc)
        return "NOT_FOUND" in message and "models/" in message

    def _resolve_model_name(self) -> str | None:
        try:
            models = list(self._client.models.list())
        except Exception:
            return None

        def _supports_generate_content(model: Any) -> bool:
            for attr in ("supported_actions", "supported_generation_methods"):
                value = getattr(model, attr, None)
                if isinstance(value, (list, tuple)) and "generateContent" in value:
                    return True
            return False

        preferred = []
        for model in models:
            name = getattr(model, "name", "")
            if not name:
                continue
            if _supports_generate_content(model):
                if "flash" in name:
                    preferred.append(name)
                elif "gemini" in name:
                    preferred.append(name)

        if preferred:
            return preferred[0]

        for model in models:
            name = getattr(model, "name", "")
            if name:
                return name

        return None

    def _append_prompt_log(
        self,
        system_prompt: str,
        user_prompt: str,
        raw_json: str,
        metrics: Dict[str, Any],
        page_text: str,
    ) -> None:
        os.makedirs("logs", exist_ok=True)
        log_path = os.path.join("logs", "prompt_logs.json")
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "structured_inputs": {
                "metrics": metrics,
                "page_text": page_text,
            },
            "raw_json_output": raw_json,
        }

        logs = []
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as handle:
                    logs = json.load(handle) or []
            except (json.JSONDecodeError, OSError):
                logs = []

        logs.append(entry)
        with open(log_path, "w", encoding="utf-8") as handle:
            json.dump(logs, handle, ensure_ascii=True, indent=2)