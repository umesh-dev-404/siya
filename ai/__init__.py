"""
AI Module

AI integration for intent parsing.
Per DIP Phase 5: AI Integration (Controlled).

Enforces:
- LAW 3 — LLM IS NOT AN AGENT
"""

from ai.ai_interface import AIInterface
from ai.intent_parser import IntentParser
from ai.llama_wrapper import LlamaWrapper, is_llama_available
from ai.model_manager import ModelManager

__all__ = [
    "AIInterface",
    "IntentParser",
    "LlamaWrapper",
    "ModelManager",
    "is_llama_available",
]
