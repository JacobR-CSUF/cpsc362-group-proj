# apps/ai/app/services/gemini_summarizer.py

import os
import logging
from enum import Enum
from typing import Optional

from google import genai


logger = logging.getLogger(__name__)


class SummaryStyle(str, Enum):
    BRIEF = "brief"
    DETAILED = "detailed"
    BULLET_POINTS = "bullet_points"


class GeminiTextSummarizer:
    """
    Simple wrapper around Google Gemini API for text summarization.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",  
        api_key_env: str = "GEMINI_API_KEY",
    ) -> None:
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{api_key_env} environment variable is not set. "
                "Please configure your Gemini API key."
            )

        # Client for Gemini Developer API
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def _build_prompt(self, text: str, style: SummaryStyle) -> str:
        """
        Construct prompt for Gemini summarization based on request
        """
        base_instruction = (
            "You are an expert summarization assistant. "
            "Read the following text and generate a concise, accurate summary.\n\n"
        )

        if style == SummaryStyle.BRIEF:
            style_instruction = (
                "Write a very concise summary in 2–3 sentences. "
                "Focus only on the main point and outcome."
            )
        elif style == SummaryStyle.DETAILED:
            style_instruction = (
                "Write a detailed, well-structured summary in multiple paragraphs. "
                "Include key context, important details, and any conclusions or recommendations."
            )
        elif style == SummaryStyle.BULLET_POINTS:
            style_instruction = (
                "Summarize the text as a list of bullet points. "
                "Each bullet should represent one key idea or takeaway."
            )
        else:
            # default : brief summary
            style_instruction = "Write a short summary focusing on the main idea."

        prompt = (
            f"{base_instruction}"
            f"{style_instruction}\n\n"
            "=== TEXT START ===\n"
            f"{text}\n"
            "=== TEXT END ==="
        )
        return prompt

    def summarize(
        self,
        text: str,
        style: SummaryStyle = SummaryStyle.BRIEF,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """
        Summarize text using Gemini.
        - text : Original text to summarize
        - style : brief / detailed / bullet_points
        """
        if not text or not text.strip():
            raise ValueError("Input text is empty; cannot summarize.")

        prompt = self._build_prompt(text, style)

        generation_config = {}
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                generation_config=generation_config or None,
            )
        except Exception as e:
            logger.exception("Gemini summarization request failed")
            raise RuntimeError(f"Gemini summarization failed: {e}") from e

        # access final text with response.text in google-genai SDK
        summary = getattr(response, "text", None)
        if not summary:
            raise RuntimeError("Gemini returned an empty response for summarization.")

        return summary.strip()
