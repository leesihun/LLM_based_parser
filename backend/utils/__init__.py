"""Shared utility functions and helpers."""

from backend.utils.exceptions import (
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    AgentError,
    AgentExecutionError,
    ToolError,
    ValidationError,
)
from backend.utils.json_utils import (
    extract_json_path,
    calculate_json_depth,
    format_json_safe,
)
from backend.utils.validators import (
    validate_json_schema,
    validate_numeric_range,
)

__all__ = [
    # Exceptions
    "LLMError",
    "LLMConnectionError",
    "LLMTimeoutError",
    "AgentError",
    "AgentExecutionError",
    "ToolError",
    "ValidationError",
    # JSON utilities
    "extract_json_path",
    "calculate_json_depth",
    "format_json_safe",
    # Validators
    "validate_json_schema",
    "validate_numeric_range",
]
