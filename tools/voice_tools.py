"""
Voice Tools

MCP tools for voice interaction.
Per Phase 16: Voice Interface.

LAW Compliance:
- LAW 1: Listening requires explicit trigger (no always-on).
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def speak_text(text: str) -> Dict[str, Any]:
    """
    Speak text using TTS.
    
    Args:
        text: Text to speak
        
    Returns:
        Result dictionary
    """
    try:
        from voice.manager import get_voice_manager
        
        manager = get_voice_manager()
        success = manager.speak(text)
        
        if not success:
            return {
                "success": False,
                "error": "TTS failed or unavailable",
            }
        
        return {
            "success": True,
            "message": "Spoken",
        }
        
    except ImportError as e:
        return {"success": False, "error": f"Voice module missing: {e}"}
    except Exception as e:
        logger.error(f"Speak failed: {e}")
        return {"success": False, "error": str(e)}


def listen_for_input(timeout: int = 10) -> Dict[str, Any]:
    """
    Listen for voice input.
    
    Args:
        timeout: Seconds to wait
        
    Returns:
        Result with transcribed text
    """
    try:
        from voice.manager import get_voice_manager
        
        manager = get_voice_manager()
        text = manager.listen_for_command(timeout=timeout)
        
        if text is None:
            return {
                "success": False,
                "error": "No speech detected or STT unavailable",
            }
        
        return {
            "success": True,
            "text": text,
        }
        
    except Exception as e:
        logger.error(f"Listen failed: {e}")
        return {"success": False, "error": str(e)}


# Schemas
VOICE_TOOL_SCHEMAS = [
    {
        "name": "speak_text",
        "description": "Speak text using the device's speakers.",
        "permission_level": "EXECUTE",
        "requires_confirmation": False,
        "parameters": {
            "text": {
                "type": "string",
                "description": "Text to speak",
                "required": True,
            },
        },
        "handler": speak_text,
    },
    {
        "name": "listen_for_input",
        "description": "Listen for voice input from the microphone.",
        "permission_level": "EXECUTE",
        "requires_confirmation": False,
        "parameters": {
            "timeout": {
                "type": "integer",
                "description": "Seconds to wait for speech",
                "required": False,
            },
        },
        "handler": listen_for_input,
    },
]
