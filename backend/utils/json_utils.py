"""
JSON utility functions for data manipulation and analysis.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.utils.exceptions import JSONValidationError


def extract_json_path(data: Any, path: str) -> Any:
    """
    Extract data from JSON using dot notation path.

    Examples:
        extract_json_path(data, "users.0.name")
        extract_json_path(data, "$.materials[*].warpage")

    Args:
        data: JSON data structure
        path: Dot-notation path (supports array indices)

    Returns:
        Extracted data at the specified path

    Raises:
        JSONValidationError: If path is invalid or not found
    """
    # Remove leading '$.' if present
    if path.startswith('$.'):
        path = path[2:]
    elif path == '$':
        return data

    parts = path.split('.')
    current = data

    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                raise JSONValidationError(f"Path not found: {part} in {path}")
            current = current[part]

        elif isinstance(current, list):
            try:
                # Handle array index
                if '[' in part and ']' in part:
                    key = part[:part.index('[')]
                    index_str = part[part.index('[') + 1:part.index(']')]
                    index = int(index_str)

                    if key:
                        current = current[index][key]
                    else:
                        current = current[index]
                else:
                    index = int(part)
                    current = current[index]

            except (ValueError, IndexError, KeyError) as e:
                raise JSONValidationError(f"Invalid array index in path: {part}") from e

        else:
            raise JSONValidationError(f"Cannot navigate path '{path}' - not a dict or list at {part}")

    return current


def calculate_json_depth(data: Any, current_depth: int = 0) -> int:
    """
    Calculate maximum nesting depth of JSON structure.

    Args:
        data: JSON data structure
        current_depth: Current depth level (used in recursion)

    Returns:
        Maximum depth as integer
    """
    if isinstance(data, dict):
        if not data:
            return current_depth
        return max(calculate_json_depth(v, current_depth + 1) for v in data.values())

    elif isinstance(data, list):
        if not data:
            return current_depth
        return max(calculate_json_depth(item, current_depth + 1) for item in data)

    else:
        return current_depth


def format_json_safe(data: Any, indent: int = 2, max_length: Optional[int] = None) -> str:
    """
    Format JSON data safely with optional truncation.

    Args:
        data: Data to format
        indent: Indentation spaces
        max_length: Maximum length before truncation

    Returns:
        Formatted JSON string
    """
    try:
        formatted = json.dumps(data, indent=indent, ensure_ascii=False)

        if max_length and len(formatted) > max_length:
            formatted = formatted[:max_length] + "\n... (truncated)"

        return formatted

    except (TypeError, ValueError) as e:
        return f"<Unable to format JSON: {e}>"


def get_json_statistics(data: Any) -> Dict[str, Any]:
    """
    Get statistics about JSON structure.

    Args:
        data: JSON data structure

    Returns:
        Dictionary with statistics (type, size, depth, keys, etc.)
    """
    stats = {
        'type': type(data).__name__,
        'size_bytes': len(json.dumps(data)),
        'depth': calculate_json_depth(data),
        'array_length': 0,
        'key_count': 0,
        'keys': []
    }

    if isinstance(data, list):
        stats['type'] = 'array'
        stats['array_length'] = len(data)

        # Get sample of item types
        if data:
            item_types = set(type(item).__name__ for item in data[:100])
            stats['item_types'] = list(item_types)

    elif isinstance(data, dict):
        stats['type'] = 'object'
        stats['key_count'] = len(data)
        stats['keys'] = list(data.keys())

    return stats


def flatten_json(data: Any, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested JSON into single-level dictionary.

    Args:
        data: JSON data to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Flattened dictionary

    Example:
        Input: {"a": {"b": 1, "c": 2}}
        Output: {"a.b": 1, "a.c": 2}
    """
    items: List[tuple] = []

    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, (dict, list)):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))

    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_key = f"{parent_key}[{i}]"

            if isinstance(v, (dict, list)):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))

    return dict(items)


def extract_numeric_fields(data: Any, max_depth: int = 10) -> Dict[str, List[float]]:
    """
    Extract all numeric fields from JSON structure.

    Args:
        data: JSON data structure
        max_depth: Maximum depth to traverse

    Returns:
        Dictionary mapping field paths to lists of numeric values
    """
    numeric_fields: Dict[str, List[float]] = {}

    def traverse(obj: Any, path: str = "", depth: int = 0):
        if depth > max_depth:
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                traverse(value, new_path, depth + 1)

        elif isinstance(obj, list):
            for item in obj:
                traverse(item, path, depth + 1)

        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            if path not in numeric_fields:
                numeric_fields[path] = []
            numeric_fields[path].append(float(obj))

    traverse(data)
    return numeric_fields
