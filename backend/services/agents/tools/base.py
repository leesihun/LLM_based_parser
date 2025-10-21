"""
Base Tool Interface

All agent tools inherit from this base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Standardized tool execution result."""

    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """
    Base class for all agent tools.

    Each tool must implement:
    - name: Unique identifier
    - description: What the tool does
    - execute: Main execution method
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (must be unique)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass

    @property
    def parameters_description(self) -> str:
        """Description of tool parameters."""
        return "No parameters required"

    @property
    def use_cases(self) -> List[str]:
        """List of use cases for this tool."""
        return ["General purpose"]

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Dictionary with execution results

        Raises:
            ToolExecutionError: If execution fails
        """
        pass

    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate tool parameters before execution.

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if valid

        Raises:
            ToolValidationError: If validation fails
        """
        # Default implementation: no validation
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
