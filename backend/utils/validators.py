"""
Data validation utilities.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.utils.exceptions import ValidationError, SchemaValidationError


def validate_json_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate JSON data against a schema.

    Args:
        data: Data to validate
        schema: Schema definition

    Returns:
        True if valid

    Raises:
        SchemaValidationError: If validation fails
    """
    # Simple schema validation (can be extended with jsonschema library)
    required_fields = schema.get('required', [])

    if isinstance(data, dict):
        for field in required_fields:
            if field not in data:
                raise SchemaValidationError(f"Missing required field: {field}")
    else:
        raise SchemaValidationError(f"Expected dict, got {type(data).__name__}")

    return True


def validate_numeric_range(
    value: float,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    field_name: str = "value"
) -> bool:
    """
    Validate numeric value is within range.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        field_name: Name of field for error messages

    Returns:
        True if valid

    Raises:
        ValidationError: If value out of range
    """
    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be >= {min_value}, got {value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must be <= {max_value}, got {value}")

    return True


def validate_non_empty(value: Any, field_name: str = "field") -> bool:
    """
    Validate value is not empty.

    Args:
        value: Value to check
        field_name: Name of field for error messages

    Returns:
        True if not empty

    Raises:
        ValidationError: If value is empty
    """
    if value is None:
        raise ValidationError(f"{field_name} cannot be None")

    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"{field_name} cannot be empty string")

    if isinstance(value, (list, dict)) and not value:
        raise ValidationError(f"{field_name} cannot be empty")

    return True
