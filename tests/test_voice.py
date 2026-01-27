"""
Unit Tests for Phase 16 Voice Interface

Tests for:
- TTS Engine (Mocked)
- STT Engine (Mocked)
- Voice Manager
- Voice Tools
"""

from unittest.mock import MagicMock, patch

import pytest


class TestTTSEngine:
    """Tests for TTS Engine."""

    def test_speak_available(self):
        """Test speak when engine available."""
        # Create a mock for pyttsx3
        mock_pyttsx3 = MagicMock()
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine
        
        # Patch sys.modules to simulate pyttsx3 being installed
        with patch.dict('sys.modules', {'pyttsx3': mock_pyttsx3}):
            # Reload module to pick up the mock
            import voice.tts
            import importlib
            importlib.reload(voice.tts)
            
            from voice.tts import TTSEngine
            engine = TTSEngine()
            
            assert engine.is_available() is True
            assert engine.speak("Hello") is True
            mock_engine.say.assert_called_with("Hello")
            mock_engine.runAndWait.assert_called_once()

    def test_speak_unavailable(self):
        """Test speak when engine unavailable."""
        # Mock import failure
        with patch.dict('sys.modules', {'pyttsx3': None}):
            # We need to ensure the module re-evaluates the import
            import voice.tts
            import importlib
            # Force ImportError simulation is tricky with reload if it was already loaded.
            # Simpler: just patch HAS_PYTTSX3 after reload?
            
            # Alternative: Patch the module attribute directly if it exists, 
            # but if it failed import, it won't exist.
            
            # Let's rely on logic: if HAS_PYTTSX3 is False.
            with patch('voice.tts.HAS_PYTTSX3', False):
                from voice.tts import TTSEngine
                engine = TTSEngine()
                assert engine.is_available() is False
                assert engine.speak("Hello") is False


class TestSTTEngine:
    """Tests for STT Engine."""

    def test_listen_available(self):
        """Test listen when mic available."""
        mock_sr = MagicMock()
        mock_mic = MagicMock()
        mock_sr.Microphone.return_value = mock_mic
        mock_sr.Microphone.list_microphone_names.return_value = ["Mic1"]
        
        mock_recognizer = MagicMock()
        mock_sr.Recognizer.return_value = mock_recognizer
        mock_recognizer.recognize_google.return_value = "Hello World"
        
        with patch.dict('sys.modules', {'speech_recognition': mock_sr}):
            import voice.stt
            import importlib
            importlib.reload(voice.stt)
            
            from voice.stt import STTEngine
            engine = STTEngine()
            
            assert engine.is_available() is True
            text = engine.listen()
            assert text == "Hello World"

    def test_listen_no_speech(self):
        """Test listen timeout."""
        mock_sr = MagicMock()
        mock_sr.Microphone.list_microphone_names.return_value = ["Mic1"]
        mock_sr.WaitTimeoutError = Exception
        mock_sr.Recognizer.return_value.listen.side_effect = mock_sr.WaitTimeoutError
        
        with patch.dict('sys.modules', {'speech_recognition': mock_sr}):
            import voice.stt
            import importlib
            importlib.reload(voice.stt)
            
            from voice.stt import STTEngine
            engine = STTEngine()
            
            text = engine.listen()
            assert text is None


class TestVoiceTools:
    """Tests for Voice Tools."""

    def test_speak_text(self):
        """Test speak_text tool."""
        from tools.voice_tools import speak_text
        
        with patch('voice.manager.get_voice_manager') as mock_get_mgr:
            mock_mgr = MagicMock()
            mock_mgr.speak.return_value = True
            mock_get_mgr.return_value = mock_mgr
            
            result = speak_text("Hello")
            assert result["success"] is True

    def test_listen_for_input(self):
        """Test listen_for_input tool."""
        from tools.voice_tools import listen_for_input
        
        with patch('voice.manager.get_voice_manager') as mock_get_mgr:
            mock_mgr = MagicMock()
            mock_mgr.listen_for_command.return_value = "Hello"
            mock_get_mgr.return_value = mock_mgr
            
            result = listen_for_input()
            assert result["success"] is True
            assert result["text"] == "Hello"
