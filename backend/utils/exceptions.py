"""
Custom exceptions for the application.

Organized by domain for better error handling and debugging.
"""

from __future__ import annotations


# Base exception
class ApplicationError(Exception):
    """Base exception for all application errors."""
    pass


# LLM-related exceptions
class LLMError(ApplicationError):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM service fails."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class LLMInvalidResponseError(LLMError):
    """Raised when LLM returns invalid or malformed response."""
    pass


# Agent-related exceptions
class AgentError(ApplicationError):
    """Base exception for agent system errors."""
    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass


class AgentPlanningError(AgentError):
    """Raised when agent planning fails."""
    pass


class AgentMaxIterationsError(AgentError):
    """Raised when agent exceeds maximum iterations."""
    pass


# Tool-related exceptions
class ToolError(ApplicationError):
    """Base exception for tool execution errors."""
    pass


class ToolNotFoundError(ToolError):
    """Raised when requested tool doesn't exist."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool parameters fail validation."""
    pass


# Data validation exceptions
class ValidationError(ApplicationError):
    """Raised when data validation fails."""
    pass


class JSONValidationError(ValidationError):
    """Raised when JSON validation fails."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""
    pass


# Authentication exceptions
class AuthenticationError(ApplicationError):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    pass


class SessionExpiredError(AuthenticationError):
    """Raised when session has expired."""
    pass


class UnauthorizedError(AuthenticationError):
    """Raised when user lacks required permissions."""
    pass


# File handling exceptions
class FileError(ApplicationError):
    """Base exception for file operations."""
    pass


class FileNotFoundError(FileError):
    """Raised when file is not found."""
    pass


class FileTypeError(FileError):
    """Raised when file type is not supported."""
    pass


class FileSizeError(FileError):
    """Raised when file size exceeds limits."""
    pass
