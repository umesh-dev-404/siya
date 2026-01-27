"""
Voice Interface Package

Speech-to-Text and Text-to-Speech capabilities.
Per Phase 16: Voice Interface.

LAW Compliance:
- LAW 1: No always-on listening without explicit mode.
- LAW 12: Graceful handling of missing audio hardware.
"""

from voice.tts import TTSEngine, get_tts_engine
from voice.stt import STTEngine, get_stt_engine
from voice.manager import VoiceManager, get_voice_manager

__all__ = [
    "TTSEngine",
    "get_tts_engine",
    "STTEngine",
    "get_stt_engine",
    "VoiceManager",
    "get_voice_manager",
]
