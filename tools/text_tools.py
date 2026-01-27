"""
Text/content processing tools (initial).

These tools use the local AI model for content processing (LAW 3 updated),
but do not cause side effects beyond returning processed output.
"""

import json
from typing import Any, Dict

from ai.ai_interface import AIInterface


def make_summarize_text_tool(ai: AIInterface):
    def summarize_text(args: Dict[str, Any]) -> Dict[str, Any]:
        text = args.get("text")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("INVALID_ARGUMENTS: 'text' must be a non-empty string")

        style = args.get("style", "bullet")
        max_bullets = args.get("max_bullets", 6)
        if not isinstance(style, str):
            style = "bullet"
        if not isinstance(max_bullets, int) or max_bullets < 1 or max_bullets > 20:
            max_bullets = 6

        prompt = (
            "You are Siya's local content processor. Summarize the following text.\n"
            f"Output format: {style}. Max bullets: {max_bullets}.\n\n"
            "TEXT:\n"
            f"{text}\n"
        )

        out = ai.generate_text(prompt=prompt, max_tokens=256, temperature=0.2)
        return {
            "status": "ok",
            "summary": out.strip(),
        }

    return summarize_text

