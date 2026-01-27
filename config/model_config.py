"""
Model Configuration

Configuration for AI model settings.
Per DIP Phase 10: Real AI Model Integration.
"""

import os
from pathlib import Path
from typing import Optional


def get_model_path() -> Optional[str]:
    """
    Get model file path from environment variable or default location.

    Returns:
        Model file path, or None if not set and default doesn't exist

    Environment Variable:
        SIYA_MODEL_PATH: Path to model file (e.g., /opt/siya/models/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf)

    Default Locations (checked in order):
        1. Environment variable SIYA_MODEL_PATH
        2. /opt/siya/models/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf
        3. Any .gguf file in /opt/siya/models/qwen2.5-3b-q4_k_m/
        4. Any .gguf file in /opt/siya/models/ (searches subdirectories)
    """
    # First, check environment variable
    model_path = os.getenv("SIYA_MODEL_PATH")
    if model_path:
        path_obj = Path(model_path)
        if path_obj.exists():
            return str(path_obj.absolute())
        else:
            # Log warning but don't fail - will fall back to stub mode
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Model path from environment does not exist: {model_path}")
        return None
    
    # If no environment variable, check default locations in order
    default_paths = [
        Path("/opt/siya/models/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf"),
        Path("/opt/siya/models/qwen2.5-3b-q4_k_m"),  # Directory - will search for .gguf
        Path("/opt/siya/models"),  # Root models directory - will search recursively
    ]
    
    # Check specific file first
    if default_paths[0].exists():
        return str(default_paths[0].absolute())
    
    # Check default directory for any .gguf file
    if default_paths[1].exists() and default_paths[1].is_dir():
        gguf_files = list(default_paths[1].glob("*.gguf"))
        if gguf_files:
            # Prefer Q4_K_M if available, otherwise use first found
            q4_km = [f for f in gguf_files if "q4_k_m" in f.name.lower()]
            if q4_km:
                return str(q4_km[0].absolute())
            return str(gguf_files[0].absolute())
    
    # Search recursively in models directory for any .gguf file
    if default_paths[2].exists() and default_paths[2].is_dir():
        gguf_files = list(default_paths[2].rglob("*.gguf"))
        if gguf_files:
            # Prefer Q4_K_M or Q4_0 quantizations, prioritize smaller models (3B over 7B)
            q4_km = [f for f in gguf_files if "q4_k_m" in f.name.lower()]
            q4_0 = [f for f in gguf_files if "q4_0" in f.name.lower() and "q4_k_m" not in f.name.lower()]
            # Prefer 3B models over 7B
            q4_km_3b = [f for f in q4_km if "3b" in f.name.lower() or "3.8b" in f.name.lower()]
            q4_0_3b = [f for f in q4_0 if "3b" in f.name.lower() or "3.8b" in f.name.lower()]
            
            if q4_km_3b:
                return str(q4_km_3b[0].absolute())
            elif q4_0_3b:
                return str(q4_0_3b[0].absolute())
            elif q4_km:
                return str(q4_km[0].absolute())
            elif q4_0:
                return str(q4_0[0].absolute())
            else:
                return str(gguf_files[0].absolute())
    
    return None


def get_model_context_size() -> int:
    """
    Get model context window size.

    Returns:
        Context window size (default: 4096 for Qwen 2.5 3B)

    Environment Variable:
        SIYA_MODEL_CTX: Context window size (default: 4096)
    """
    ctx_str = os.getenv("SIYA_MODEL_CTX", "4096")
    try:
        ctx = int(ctx_str)
        # Cap at 4096 for Qwen 2.5 3B
        return min(ctx, 4096)
    except ValueError:
        return 4096


def get_model_threads() -> Optional[int]:
    """
    Get number of threads for model inference.

    Returns:
        Number of threads, or None for auto

    Environment Variable:
        SIYA_MODEL_THREADS: Number of threads (default: None = auto)
    """
    threads_str = os.getenv("SIYA_MODEL_THREADS")
    if threads_str:
        try:
            return int(threads_str)
        except ValueError:
            return None
    return None
