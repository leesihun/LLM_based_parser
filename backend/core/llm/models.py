"""
LLM Model Configurations and Response Types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ModelConfig:
    """Configuration for LLM model parameters."""

    host: str = "http://localhost:11434"
    model: str = "gemma3:12b"
    timeout: int = 600000  # milliseconds
    num_ctx: int = 8192
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> ModelConfig:
        """Create ModelConfig from dictionary."""
        return cls(
            host=config.get("host", cls.host),
            model=config.get("model", cls.model),
            timeout=config.get("timeout", cls.timeout),
            num_ctx=config.get("num_ctx", cls.num_ctx),
            temperature=config.get("temperature", cls.temperature),
            top_p=config.get("top_p", cls.top_p),
            top_k=config.get("top_k", cls.top_k),
        )


@dataclass
class LLMResponse:
    """Standardized response from LLM."""

    content: str
    model: str
    processing_time_ms: float = 0.0
    tokens_per_second: float = 0.0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw_response: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "content": self.content,
            "model": self.model,
            "processing_time_ms": self.processing_time_ms,
            "tokens_per_second": self.tokens_per_second,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }

    # Legacy compatibility
    def get(self, key: str, default: Any = None) -> Any:
        """Legacy dict-style access for backward compatibility."""
        if key == "content":
            return self.content
        elif key == "processing_time":
            return self.processing_time_ms
        return default


@dataclass
class ModelCapability:
    """Describes capabilities of an LLM model."""

    name: str
    max_context: int
    supports_functions: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    optimal_for: list[str] = field(default_factory=list)
