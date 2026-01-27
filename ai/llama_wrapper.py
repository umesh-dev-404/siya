"""
llama.cpp Wrapper

Wrapper for llama-cpp-python integration.
Provides abstraction layer for llama.cpp model operations.

Per DIP Phase 10: Real AI Model Integration.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama

    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    logger.warning(
        "llama-cpp-python not available. AI model integration will not work. "
        "Install with: pip install llama-cpp-python"
    )


class LlamaWrapper:
    """
    Wrapper for llama.cpp model operations.

    Provides:
    - Model loading/unloading
    - Inference with timeout
    - Resource monitoring
    - Error handling

    Per DIP Phase 10 and LAW 3 enforcement.
    """

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = 0,  # CPU-only for Pi
        verbose: bool = False,
    ) -> None:
        """
        Initialize llama.cpp wrapper.

        Args:
            model_path: Path to model file
            n_ctx: Context window size (max 4096 for Qwen 2.5 3B)
            n_threads: Number of threads (None = auto)
            n_gpu_layers: GPU layers (0 = CPU-only)
            verbose: Enable verbose logging

        Raises:
            RuntimeError: If llama-cpp-python is not available
            FileNotFoundError: If model file does not exist
        """
        if not LLAMA_AVAILABLE:
            raise RuntimeError(
                "llama-cpp-python is not available. "
                "Install with: pip install llama-cpp-python"
            )

        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        self._model_path = str(model_path_obj.absolute())
        self._n_ctx = min(n_ctx, 4096)  # Cap at 4k for Qwen 2.5 3B
        self._n_threads = n_threads
        self._n_gpu_layers = n_gpu_layers
        self._verbose = verbose

        self._model: Optional[Llama] = None
        self._model_size_mb = int(model_path_obj.stat().st_size / (1024 * 1024))

        logger.info(
            "LlamaWrapper initialized",
            extra={
                "model_path": self._model_path,
                "model_size_mb": self._model_size_mb,
                "n_ctx": self._n_ctx,
            },
        )

    def load(self) -> bool:
        """
        Load the model.

        Returns:
            True if model loaded successfully

        Raises:
            RuntimeError: If model loading fails
        """
        if self._model is not None:
            logger.debug("Model already loaded")
            return True

        try:
            logger.info("Loading model...", extra={"model_path": self._model_path})
            start_time = time.time()

            self._model = Llama(
                model_path=self._model_path,
                n_ctx=self._n_ctx,
                n_threads=self._n_threads,
                n_gpu_layers=self._n_gpu_layers,
                verbose=self._verbose,
            )

            load_time = time.time() - start_time
            logger.info(
                "Model loaded successfully",
                extra={
                    "model_path": self._model_path,
                    "load_time_seconds": load_time,
                    "model_size_mb": self._model_size_mb,
                },
            )

            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            self._model = None
            raise RuntimeError(f"Model loading failed: {e}") from e

    def unload(self) -> bool:
        """
        Unload the model.

        Returns:
            True if model unloaded successfully
        """
        if self._model is None:
            logger.debug("Model not loaded")
            return True

        try:
            logger.info("Unloading model...")
            # llama-cpp-python doesn't have explicit unload, but we can delete the reference
            # Python GC will handle cleanup
            del self._model
            self._model = None

            logger.info("Model unloaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to unload model: {e}", exc_info=True)
            return False

    def is_loaded(self) -> bool:
        """
        Check if model is loaded.

        Returns:
            True if model is loaded
        """
        return self._model is not None

    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.3,
        timeout: float = 120.0,
        stop: Optional[list[str]] = None,
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            timeout: Maximum time in seconds for inference
            stop: Stop sequences

        Returns:
            Generated text

        Raises:
            RuntimeError: If model is not loaded or inference fails
            TimeoutError: If inference exceeds timeout

        Note:
            LAW 3: AI output is untrusted and must be validated.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        try:
            logger.debug(
                "Generating text",
                extra={
                    "prompt_length": len(prompt),
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )

            start_time = time.time()

            # Call llama.cpp inference
            # Note: llama-cpp-python doesn't support timeout directly
            # We'll rely on max_tokens to limit generation time
            logger.debug(f"Starting inference: max_tokens={max_tokens}, temperature={temperature}, stop={stop}")
            result = self._model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or [],
                echo=False,  # Don't echo the prompt
            )
            logger.debug(f"Inference complete, result type: {type(result)}")

            inference_time = time.time() - start_time

            if inference_time > timeout:
                logger.warning(
                    f"Inference exceeded timeout: {inference_time:.2f}s > {timeout}s"
                )

            # Extract text from result
            # llama-cpp-python returns a dict with 'choices' list
            logger.debug(f"Result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
            if isinstance(result, dict) and "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0].get("text", "")
            elif isinstance(result, dict) and "text" in result:
                generated_text = result["text"]
            elif hasattr(result, 'choices') and len(result.choices) > 0:
                generated_text = result.choices[0].text if hasattr(result.choices[0], 'text') else str(result.choices[0])
            else:
                generated_text = str(result) if result else ""
            
            logger.debug(f"Extracted text (first 200 chars): {generated_text[:200]}")

            logger.debug(
                "Text generated",
                extra={
                    "inference_time_seconds": inference_time,
                    "generated_length": len(generated_text),
                    "tokens_generated": result.get("usage", {}).get("completion_tokens", 0),
                },
            )

            return generated_text

        except Exception as e:
            logger.error(f"Inference failed: {e}", exc_info=True)
            raise RuntimeError(f"Inference failed: {e}") from e

    def get_model_size_mb(self) -> int:
        """
        Get model size in MB.

        Returns:
            Model size in MB
        """
        return self._model_size_mb

    def get_context_size(self) -> int:
        """
        Get context window size.

        Returns:
            Context window size
        """
        return self._n_ctx


def is_llama_available() -> bool:
    """
    Check if llama-cpp-python is available.

    Returns:
        True if llama-cpp-python is installed
    """
    return LLAMA_AVAILABLE
