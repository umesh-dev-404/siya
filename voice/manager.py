"""
Voice Manager

Orchestrates voice interactions (TTS + STT).
"""

import logging
from typing import Optional

from voice.stt import STTEngine, get_stt_engine
from voice.tts import TTSEngine, get_tts_engine

logger = logging.getLogger(__name__)


class VoiceManager:
    """
    Manages voice input and output.
    """
    
    def __init__(
        self,
        tts: Optional[TTSEngine] = None,
        stt: Optional[STTEngine] = None,
    ) -> None:
        """
        Initialize voice manager.
        """
        self._tts = tts or get_tts_engine()
        self._stt = stt or get_stt_engine()
        
        logger.info("Voice Manager initialized")
    
    def speak(self, text: str) -> bool:
        """Speak text."""
        if not self._tts.is_available():
            logger.warning("TTS not available")
            return False
        return self._tts.speak(text)
    
    def listen_for_command(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for a voice command.
        
        Returns:
            Command text or None
        """
        if not self._stt.is_available():
            logger.error("STT not available (no microphone?)")
            return None
        
        return self._stt.listen(timeout=timeout)
    
    def is_fully_capable(self) -> bool:
        """Check if both TTS and STT are working."""
        return self._tts.is_available() and self._stt.is_available()


# Singleton
_default_manager: Optional[VoiceManager] = None


def get_voice_manager() -> VoiceManager:
    """Get default voice manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = VoiceManager()
    return _default_manager
