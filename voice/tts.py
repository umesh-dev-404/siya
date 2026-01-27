"""
Text-to-Speech Engine

Wraps pyttsx3 for local text-to-speech.
"""

import logging
import threading
from typing import Optional

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Text-to-Speech Engine.
    
    Uses pyttsx3 for offline speech synthesis.
    """
    
    def __init__(self, rate: int = 150, volume: float = 1.0) -> None:
        """
        Initialize TTS engine.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume (0.0 to 1.0)
        """
        self._engine = None
        self._lock = threading.Lock()
        
        if HAS_PYTTSX3:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', rate)
                self._engine.setProperty('volume', volume)
                logger.info("TTS Engine initialized (pyttsx3)")
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
                self._engine = None
        else:
            logger.warning("pyttsx3 not installed, TTS disabled")
    
    def speak(self, text: str, block: bool = True) -> bool:
        """
        Speak text.
        
        Args:
            text: Text to speak
            block: Block until speech finishes
            
        Returns:
            True if spoken (or queued), False if failed/disabled
        """
        if not self._engine:
            logger.info(f"[TTS Disabled] Would speak: {text}")
            return False
        
        with self._lock:
            try:
                self._engine.say(text)
                if block:
                    self._engine.runAndWait()
                return True
            except Exception as e:
                logger.error(f"TTS speak failed: {e}")
                return False
    
    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self._engine is not None
    
    def set_property(self, name: str, value: any) -> None:
        """Set pyttsx3 property."""
        if self._engine:
            try:
                self._engine.setProperty(name, value)
            except Exception as e:
                logger.error(f"Failed to set property {name}: {e}")


# Singleton instance
_default_tts: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    """Get or create default TTS engine."""
    global _default_tts
    if _default_tts is None:
        _default_tts = TTSEngine()
    return _default_tts
