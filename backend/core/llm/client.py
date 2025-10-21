"""
LLM Client - Unified interface for Language Model interactions

Refactored from legacy llm_client.py with improved:
- Error handling
- Type hints
- Configuration management
- Response formatting
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from backend.core.llm.models import ModelConfig, LLMResponse
from backend.utils.exceptions import LLMError, LLMConnectionError, LLMTimeoutError

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Main interface for LLM operations using Ollama backend.

    Features:
    - Automatic model preloading
    - Configurable parameters (temperature, context window, etc.)
    - Comprehensive error handling
    - Performance metrics tracking
    """

    def __init__(self, config_path: str | Path | None = None, config_dict: Dict[str, Any] | None = None):
        """
        Initialize LLM client.

        Args:
            config_path: Path to configuration JSON file
            config_dict: Configuration dictionary (alternative to file)
        """
        self.config = self._load_config(config_path, config_dict)
        self.model_config = ModelConfig.from_dict(self.config.get("ollama", {}))
        self._initialize()

    def _load_config(
        self,
        config_path: str | Path | None,
        config_dict: Dict[str, Any] | None
    ) -> Dict[str, Any]:
        """Load configuration from file or dict."""
        if config_dict:
            return config_dict

        if config_path is None:
            config_path = Path(__file__).resolve().parents[3] / "config.json"

        config_path = Path(config_path)

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise LLMError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON in configuration file: {e}")

    def _initialize(self) -> None:
        """Initialize client and preload model."""
        self.ollama_url = self.model_config.host
        self.model = self.model_config.model
        self.timeout = self.model_config.timeout / 1000  # Convert ms to seconds

        logger.info(f"Initializing LLM client: {self.model} @ {self.ollama_url}")
        self._preload_model()

    def _preload_model(self) -> None:
        """Preload model to reduce cold start latency."""
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": "",
                "stream": False,
                "options": {"num_predict": 1}
            }
            requests.post(url, json=payload, timeout=30)
            logger.info(f"Model preloaded: {self.model}")
        except Exception as e:
            logger.warning(f"Model preload failed (non-fatal): {e}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Perform chat completion with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Returns:
            LLMResponse object with content and metrics

        Raises:
            LLMConnectionError: If connection to Ollama fails
            LLMTimeoutError: If request times out
        """
        url = f"{self.ollama_url}/api/chat"

        # Build options with defaults
        options = {
            "num_ctx": kwargs.get("num_ctx", self.model_config.num_ctx),
            "temperature": temperature if temperature is not None else self.model_config.temperature,
            "top_p": kwargs.get("top_p", self.model_config.top_p),
            "top_k": kwargs.get("top_k", self.model_config.top_k),
            "num_gpu": -1,  # Use all GPUs
            "num_thread": 1,
        }

        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options
        }

        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            elapsed_time = time.time() - start_time
            result = response.json()

            return self._parse_chat_response(result, elapsed_time)

        except requests.Timeout:
            raise LLMTimeoutError(f"Request timed out after {self.timeout}s")
        except requests.ConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to Ollama: {e}")
        except requests.HTTPError as e:
            raise LLMError(f"HTTP error from Ollama: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}")

    def _parse_chat_response(self, result: Dict[str, Any], elapsed_time: float) -> LLMResponse:
        """Parse Ollama chat response into LLMResponse object."""
        content = result.get("message", {}).get("content", "")

        # Calculate tokens per second
        tokens_per_second = 0.0
        if result.get('eval_count') and result.get('eval_duration'):
            tokens_per_second = result['eval_count'] / (result['eval_duration'] / 1e9)

        return LLMResponse(
            content=content,
            model=self.model,
            processing_time_ms=elapsed_time * 1000,
            tokens_per_second=tokens_per_second,
            total_tokens=result.get('eval_count', 0),
            prompt_tokens=result.get('prompt_eval_count', 0),
            completion_tokens=result.get('eval_count', 0),
            raw_response=result
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate completion for a single prompt.

        Args:
            prompt: Input prompt
            system_prompt: Optional system instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse object
        """
        url = f"{self.ollama_url}/api/generate"

        options = {
            "num_ctx": self.model_config.num_ctx,
            "temperature": temperature if temperature is not None else self.model_config.temperature,
            "top_p": self.model_config.top_p,
            "top_k": self.model_config.top_k,
            "num_gpu": -1,
            "num_thread": 1,
        }

        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }

        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            elapsed_time = time.time() - start_time
            result = response.json()

            return LLMResponse(
                content=result.get("response", ""),
                model=self.model,
                processing_time_ms=elapsed_time * 1000,
                raw_response=result
            )

        except requests.Timeout:
            raise LLMTimeoutError(f"Request timed out after {self.timeout}s")
        except requests.ConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}")

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models from Ollama.

        Returns:
            List of model information dicts
        """
        url = f"{self.ollama_url}/api/tags"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def health_check(self) -> bool:
        """
        Check if Ollama service is healthy.

        Returns:
            True if service is reachable and responding
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    @property
    def config_dict(self) -> Dict[str, Any]:
        """Get current configuration as dictionary."""
        return self.config

    def save_config(self, path: str | Path) -> None:
        """Save current configuration to file."""
        path = Path(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration saved to {path}")
