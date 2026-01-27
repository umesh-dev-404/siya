"""
Speech-to-Text Engine

Wraps SpeechRecognition for microphone input.
"""

import logging
from typing import Optional

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

logger = logging.getLogger(__name__)


class STTEngine:
    """
    Speech-to-Text Engine.
    
    Uses SpeechRecognition library to capture and transcribe audio.
    """
    
    def __init__(self, energy_threshold: int = 4000) -> None:
        """
        Initialize STT engine.
        
        Args:
            energy_threshold: Audio energy threshold for silence detection
        """
        self._recognizer = None
        self._microphone = None
        
        if HAS_SR:
            try:
                self._recognizer = sr.Recognizer()
                self._recognizer.energy_threshold = energy_threshold
                # Check for microphones
                if not sr.Microphone.list_microphone_names():
                    logger.warning("No microphones found")
                else:
                    self._microphone = sr.Microphone()
                    logger.info("STT Engine initialized (Microphone available)")
            except Exception as e:
                logger.error(f"Failed to initialize SpeechRecognition: {e}")
        else:
            logger.warning("SpeechRecognition not installed, STT disabled")
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listen for a single phrase and transcribe.
        
        Args:
            timeout: Max seconds to wait for speech start
            phrase_time_limit: Max seconds of speech duration
            
        Returns:
            Transcribed text, or None if failed/timed out
        """
        if not self.is_available():
            logger.warning("STT not available")
            return None
        
        try:
            with self._microphone as source:
                logger.debug("Adjusting for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                logger.info("Listening...")
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
            logger.debug("Transcribing...")
            # Default to Google Web Speech API (online), requires internet.
            # Ideally we'd use offline (Whisper/Sphinx) but this is simpler for Phase 16.
            text = self._recognizer.recognize_google(audio)
            logger.info(f"Heard: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.info("Listening timed out (no speech detected)")
            return None
        except sr.UnknownValueError:
            logger.info("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from service: {e}")
            return None
        except Exception as e:
            logger.error(f"STT listen failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if microphone and recognizer are available."""
        return self._recognizer is not None and self._microphone is not None


# Singleton instance
_default_stt: Optional[STTEngine] = None


def get_stt_engine() -> STTEngine:
    """Get or create default STT engine."""
    global _default_stt
    if _default_stt is None:
        _default_stt = STTEngine()
    return _default_stt
