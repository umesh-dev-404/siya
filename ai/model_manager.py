"""
Model Manager

Manages AI model lifecycle (load/unload on demand).
Stub implementation for Phase 5 (PC only, no real model).

Per DIP Phase 5: Model lifecycle management.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Model manager for AI model lifecycle.

    Per DIP Phase 5:
    - Stub llama.cpp on PC
    - Implement load/unload on demand
    - Measure RAM, CPU, latency (in later phases)

    Phase 5: Stub only (no real model loading).
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        """
        Initialize model manager.

        Args:
            model_path: Path to model file (ignored in Phase 5 stub)
        """
        self._model_path = Path(model_path) if model_path else None
        self._model_loaded = False
        self._model_size_mb = 0  # Stub: no actual model

        logger.info(
            "Model manager initialized (stub mode - no real model)",
            extra={"model_path": str(model_path) if model_path else None},
        )

    def load_model(self) -> bool:
        """
        Load AI model.

        Returns:
            True if load would succeed (always True in stub mode)

        Note:
            Phase 5: This is a stub. No actual model loading occurs.
            In later phases, this will:
            1. Check if model is already loaded
            2. Load model using llama.cpp
            3. Measure RAM usage
            4. Return success/failure
        """
        if self._model_loaded:
            logger.debug("Model already loaded (stub)")
            return True

        # Phase 5: Stub implementation
        logger.info("Would load model (stub mode)", extra={"model_path": str(self._model_path)})
        self._model_loaded = True
        return True

    def unload_model(self) -> bool:
        """
        Unload AI model.

        Returns:
            True if unload would succeed (always True in stub mode)

        Note:
            Phase 5: This is a stub. No actual model unloading occurs.
        """
        if not self._model_loaded:
            logger.debug("Model not loaded (stub)")
            return True

        # Phase 5: Stub implementation
        logger.info("Would unload model (stub mode)")
        self._model_loaded = False
        return True

    def is_loaded(self) -> bool:
        """
        Check if model is loaded.

        Returns:
            True if model is loaded (or would be in stub mode)
        """
        return self._model_loaded

    def get_model_size_mb(self) -> int:
        """
        Get model size in MB.

        Returns:
            Model size in MB (0 in stub mode)
        """
        return self._model_size_mb

    def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.7
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text (stub response in Phase 5)

        Raises:
            RuntimeError: If model is not loaded

        Note:
            Phase 5: This is a stub. Returns placeholder JSON.
            In later phases, this will call llama.cpp inference.
        """
        if not self._model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Phase 5: Stub implementation
        # Return a stub JSON response that matches intent_parsing_output schema
        logger.debug(
            "Generating text (stub mode)",
            extra={"prompt_length": len(prompt), "max_tokens": max_tokens},
        )

        # Stub: Return a basic JSON structure
        # In real implementation, this would be llama.cpp inference
        stub_response = '{"action": "unknown", "arguments": {}, "clarification_needed": true}'
        return stub_response
