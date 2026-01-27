"""
Model Manager

Manages AI model lifecycle (load/unload on demand).
Per DIP Phase 10: Real AI Model Integration.

Per DIP Phase 5: Model lifecycle management (stub).
Per DIP Phase 10: Real llama.cpp integration.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ai.llama_wrapper import LlamaWrapper, is_llama_available

logger = logging.getLogger(__name__)

# Try to import resource monitor for RAM checking
try:
    from system.resource_monitor import ResourceMonitor

    RESOURCE_MONITOR_AVAILABLE = True
except ImportError:
    RESOURCE_MONITOR_AVAILABLE = False
    ResourceMonitor = None  # type: ignore


class ModelManager:
    """
    Model manager for AI model lifecycle.

    Per DIP Phase 10:
    - Real llama.cpp integration
    - Load/unload on demand
    - Resource monitoring
    - Performance optimization

    Falls back to stub mode if llama-cpp-python is not available.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
    ) -> None:
        """
        Initialize model manager.

        Args:
            model_path: Path to model file
            n_ctx: Context window size (max 4096 for Qwen 2.5 3B)
            n_threads: Number of threads (None = auto)
        """
        self._model_path = Path(model_path) if model_path else None
        self._n_ctx = n_ctx
        self._n_threads = n_threads

        # Check if llama-cpp-python is available
        self._llama_available = is_llama_available()

        # Initialize resource monitor if available
        self._resource_monitor: Optional[Any] = None
        if RESOURCE_MONITOR_AVAILABLE and ResourceMonitor:
            try:
                self._resource_monitor = ResourceMonitor(ram_threshold=0.85)  # 85% RAM threshold
            except Exception as e:
                logger.warning(f"Failed to initialize resource monitor: {e}")

        if self._llama_available and model_path:
            # Real llama.cpp integration
            try:
                self._llama_wrapper: Optional[LlamaWrapper] = LlamaWrapper(
                    model_path=str(self._model_path),
                    n_ctx=n_ctx,
                    n_threads=n_threads,
                    n_gpu_layers=0,  # CPU-only for Pi
                    verbose=False,
                )
                self._model_size_mb = self._llama_wrapper.get_model_size_mb()
                logger.info(
                    "Model manager initialized (real llama.cpp)",
                    extra={
                        "model_path": str(model_path),
                        "model_size_mb": self._model_size_mb,
                        "n_ctx": n_ctx,
                    },
                )
            except Exception as e:
                logger.error(f"Failed to initialize llama wrapper: {e}", exc_info=True)
                self._llama_wrapper = None
                self._model_size_mb = 0
                self._llama_available = False
        else:
            # Stub mode (no model path or llama-cpp-python not available)
            self._llama_wrapper = None
            self._model_size_mb = 0
            if not model_path:
                logger.info("Model manager initialized (stub mode - no model path)")
            else:
                logger.warning(
                    "Model manager initialized (stub mode - llama-cpp-python not available)",
                    extra={"model_path": str(model_path)},
                )

    def load_model(self) -> bool:
        """
        Load AI model.

        Returns:
            True if model loaded successfully

        Raises:
            RuntimeError: If model loading fails

        Note:
            Phase 10: Real llama.cpp integration.
            Falls back to stub mode if llama-cpp-python not available.
        """
        if self.is_loaded():
            logger.debug("Model already loaded")
            return True

        if not self._llama_available or self._llama_wrapper is None:
            # Stub mode
            logger.info("Would load model (stub mode)", extra={"model_path": str(self._model_path)})
            return True

        try:
            # Check resources before loading
            ram_before_mb = None
            ram_after_mb = None
            if self._resource_monitor:
                resources_before = self._resource_monitor.check_resources()
                ram_usage_before = resources_before.get("ram_usage", 0.0)
                ram_available_before = resources_before.get("ram_available_mb", 0.0)
                # Calculate used RAM
                ram_before_mb = ram_available_before / (1 - ram_usage_before) - ram_available_before if ram_usage_before > 0 else 0
                
                logger.info(
                    f"RAM before model load: {ram_usage_before*100:.1f}% used, {ram_available_before:.0f} MB available, ~{ram_before_mb:.0f} MB used",
                    extra={
                        "ram_usage_before": ram_usage_before,
                        "ram_available_before_mb": ram_available_before,
                        "ram_used_before_mb": ram_before_mb,
                    },
                )
                
                if ram_usage_before > 0.85:  # 85% RAM threshold
                    logger.warning(
                        f"High RAM usage before model load: {ram_usage_before:.1%}",
                        extra={"ram_usage": ram_usage_before},
                    )

            # Real model loading
            success = self._llama_wrapper.load()
            if success:
                # Check resources after loading - wait a moment for memory allocation
                import time
                time.sleep(0.5)  # Give system time to allocate memory
                
                if self._resource_monitor:
                    resources_after = self._resource_monitor.check_resources()
                    ram_usage_after = resources_after.get("ram_usage", 0.0)
                    ram_available_after = resources_after.get("ram_available_mb", 0.0)
                    ram_after_mb = ram_available_after / (1 - ram_usage_after) - ram_available_after if ram_usage_after > 0 else 0
                    ram_increase_mb = ram_after_mb - ram_before_mb if ram_before_mb else 0
                    
                    logger.info(
                        f"RAM after model load: {ram_usage_after*100:.1f}% used, {ram_available_after:.0f} MB available, ~{ram_after_mb:.0f} MB used",
                        extra={
                            "ram_usage_after": ram_usage_after,
                            "ram_available_after_mb": ram_available_after,
                            "ram_used_after_mb": ram_after_mb,
                            "ram_increase_mb": ram_increase_mb,
                            "model_size_mb": self._model_size_mb,
                        },
                    )
                    
                    # Warn if RAM didn't increase significantly
                    if ram_increase_mb < self._model_size_mb * 0.5:  # Less than 50% of model size
                        logger.warning(
                            f"Model loaded but RAM only increased by {ram_increase_mb:.0f} MB (expected ~{self._model_size_mb} MB). "
                            f"Model may be using memory-mapped I/O (mmap) instead of full RAM loading.",
                            extra={
                                "ram_increase_mb": ram_increase_mb,
                                "model_size_mb": self._model_size_mb,
                            },
                        )
                else:
                    logger.info("Model loaded successfully (resource monitor not available)")
            return success
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise RuntimeError(f"Model loading failed: {e}") from e

    def unload_model(self) -> bool:
        """
        Unload AI model.

        Returns:
            True if model unloaded successfully

        Note:
            Phase 10: Real llama.cpp integration.
            Falls back to stub mode if llama-cpp-python not available.
        """
        if not self.is_loaded():
            logger.debug("Model not loaded")
            return True

        if not self._llama_available or self._llama_wrapper is None:
            # Stub mode
            logger.info("Would unload model (stub mode)")
            return True

        try:
            # Real model unloading
            success = self._llama_wrapper.unload()
            if success:
                logger.info("Model unloaded successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to unload model: {e}", exc_info=True)
            return False

    def is_loaded(self) -> bool:
        """
        Check if model is loaded.

        Returns:
            True if model is loaded
        """
        if not self._llama_available or self._llama_wrapper is None:
            return False
        return self._llama_wrapper.is_loaded()

    def get_model_size_mb(self) -> int:
        """
        Get model size in MB.

        Returns:
            Model size in MB (0 in stub mode)
        """
        return self._model_size_mb

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
            stop: Stop sequences (model stops when it encounters these)

        Returns:
            Generated text

        Raises:
            RuntimeError: If model is not loaded or inference fails
            TimeoutError: If inference exceeds timeout

        Note:
            Phase 10: Real llama.cpp inference.
            Falls back to stub mode if llama-cpp-python not available.
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if not self._llama_available or self._llama_wrapper is None:
            # Stub mode
            logger.debug(
                "Generating text (stub mode)",
                extra={"prompt_length": len(prompt), "max_tokens": max_tokens},
            )
            stub_response = '{"action": "unknown", "arguments": {}, "clarification_needed": true}'
            return stub_response

        try:
            # Real inference
            generated_text = self._llama_wrapper.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                stop=stop,
            )
            return generated_text
        except Exception as e:
            logger.error(f"Inference failed: {e}", exc_info=True)
            raise RuntimeError(f"Inference failed: {e}") from e
