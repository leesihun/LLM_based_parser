"""
Numeric Summary Tool

Enhanced numerical statistics generation for JSON data.
Refactored from backend/app/routes/chat.py::_generate_numeric_summary
"""

from __future__ import annotations

import statistics
from collections import deque
from typing import Any, Dict, List

from backend.services.agents.tools.base import BaseTool
from backend.utils.exceptions import ToolExecutionError


class NumericSummaryTool(BaseTool):
    """
    Generate comprehensive numerical statistics from JSON data.

    Capabilities:
    - Min, max, mean, median, sum for all numeric fields
    - Identifies location of extrema with IDs
    - Automatic path detection
    - Handles nested structures
    """

    @property
    def name(self) -> str:
        return "numeric_summary"

    @property
    def description(self) -> str:
        return """Generate comprehensive numerical statistics from JSON data.
Calculates min, max, mean, median, sum for all numeric fields.
Identifies locations of extrema with IDs if available."""

    @property
    def parameters_description(self) -> str:
        return """
Parameters:
  - json_data (dict|list): JSON data to analyze
  - max_sections (int): Maximum number of stat sections (default: 12)
  - max_child_items (int): Maximum child items to process (default: 25)
"""

    @property
    def use_cases(self) -> List[str]:
        return [
            "Find min/max values in JSON",
            "Calculate statistical aggregates",
            "Identify numeric patterns",
            "Locate extreme values"
        ]

    def execute(
        self,
        json_data: Any,
        max_sections: int = 12,
        max_child_items: int = 25,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate numeric summary.

        Args:
            json_data: JSON data structure
            max_sections: Maximum stat sections to generate
            max_child_items: Maximum child items per section

        Returns:
            Dictionary with statistics and formatted summary
        """
        try:
            summary_text = self._generate_summary(
                json_data,
                max_sections,
                max_child_items
            )

            stats = self._extract_statistics(summary_text)

            return {
                "success": True,
                "summary_text": summary_text,
                "statistics": stats,
                "sections_count": len(stats)
            }

        except Exception as e:
            raise ToolExecutionError(f"Numeric summary failed: {e}") from e

    def _generate_summary(
        self,
        data: Any,
        max_sections: int,
        max_child_items: int
    ) -> str:
        """Core summary generation logic."""

        def _is_number(value) -> bool:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        def _format_number(value):
            if isinstance(value, float):
                return f"{value:.6g}"
            return str(value)

        stats = []
        seen_paths = set()
        queue = deque([(data, "$")])
        visited = 0
        max_iterations = 10000

        def add_stat(path: str, entries):
            if not entries or len(stats) >= max_sections:
                return

            canonical_path = path or "$"
            if canonical_path in seen_paths:
                return

            values = [entry["value"] for entry in entries]
            min_entry = min(entries, key=lambda entry: entry["value"])
            max_entry = max(entries, key=lambda entry: entry["value"])
            sorted_values = sorted(values)

            entry = {
                "path": canonical_path,
                "count": len(values),
                "min": min_entry["value"],
                "max": max_entry["value"],
                "min_path": min_entry.get("path"),
                "max_path": max_entry.get("path"),
                "min_id": min_entry.get("id"),
                "max_id": max_entry.get("id"),
                "sum": sum(values),
                "mean": statistics.mean(values),
                "median": statistics.median(sorted_values) if len(sorted_values) > 1 else sorted_values[0],
            }
            stats.append(entry)
            seen_paths.add(canonical_path)

        while queue and len(stats) < max_sections and visited < max_iterations:
            current, path = queue.popleft()
            visited += 1

            if _is_number(current):
                if "[]." not in path and "[" in path and path.endswith("]"):
                    continue
                add_stat(path, [{"value": current, "path": path, "id": None}])
                continue

            if isinstance(current, dict):
                for key, value in current.items():
                    child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                    queue.append((value, child_path))

            elif isinstance(current, list):
                numeric_entries = [
                    {"value": item, "path": f"{path}[{idx}]", "id": None}
                    for idx, item in enumerate(current)
                    if _is_number(item)
                ]
                add_stat(path, numeric_entries)

                if any(isinstance(item, dict) for item in current):
                    keys = []
                    for item in current[:max_child_items]:
                        if isinstance(item, dict):
                            for key in item.keys():
                                if key not in keys:
                                    keys.append(key)

                    identifier_keys = ("id", "ID", "Id", "identifier", "name", "key", "title")
                    for key in keys:
                        numeric_entries = []
                        for idx, item in enumerate(current):
                            if not isinstance(item, dict):
                                continue
                            value = item.get(key)
                            if not _is_number(value):
                                continue

                            identifier = None
                            for identifier_key in identifier_keys:
                                if identifier_key in item and _is_number(item[identifier_key]):
                                    identifier = _format_number(item[identifier_key])
                                    break
                                if identifier_key in item and isinstance(item[identifier_key], str):
                                    identifier = item[identifier_key]
                                    break

                            numeric_entries.append({
                                "value": value,
                                "path": f"{path}[{idx}].{key}",
                                "id": identifier,
                            })

                        child_path = f"{path}[].{key}" if path != "$" else f"$[].{key}"
                        add_stat(child_path, numeric_entries)
                        if len(stats) >= max_sections:
                            break

                for idx, value in enumerate(current[:max_child_items]):
                    queue.append((value, f"{path}[{idx}]"))

        if not stats:
            return ""

        lines = ["Numeric Summary (auto-generated):"]
        for stat in stats[:max_sections]:
            min_loc = ""
            if stat.get("min_id") is not None:
                min_loc = f" @id={stat['min_id']}"
            elif stat.get("min_path"):
                path_parts = stat['min_path'].split('[')
                if len(path_parts) > 1:
                    min_loc = f" @[{path_parts[-1]}"

            max_loc = ""
            if stat.get("max_id") is not None:
                max_loc = f" @id={stat['max_id']}"
            elif stat.get("max_path"):
                path_parts = stat['max_path'].split('[')
                if len(path_parts) > 1:
                    max_loc = f" @[{path_parts[-1]}"

            line = (
                f"- {stat['path']}: "
                f"n={stat['count']}, "
                f"sum={_format_number(stat['sum'])}, "
                f"min={_format_number(stat['min'])}{min_loc}, "
                f"max={_format_number(stat['max'])}{max_loc}, "
                f"mean={_format_number(stat['mean'])}, "
                f"median={_format_number(stat['median'])}"
            )
            lines.append(line)

        return "\n".join(lines)

    def _extract_statistics(self, summary_text: str) -> List[Dict[str, Any]]:
        """Extract structured statistics from summary text."""
        stats = []

        for line in summary_text.split("\n")[1:]:  # Skip header
            if not line.strip() or not line.startswith("- "):
                continue

            # Parse line format: "- $.path: n=X, sum=Y, ..."
            parts = line[2:].split(": ", 1)
            if len(parts) != 2:
                continue

            path = parts[0]
            values_str = parts[1]

            stat = {"path": path}

            # Parse key=value pairs
            for pair in values_str.split(", "):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    # Remove location info from values
                    value = value.split(" @")[0]

                    # Convert to appropriate type
                    try:
                        if key == "n":
                            stat["count"] = int(value)
                        elif key in ["sum", "min", "max", "mean", "median"]:
                            stat[key] = float(value)
                    except ValueError:
                        pass

            if len(stat) > 1:  # Has more than just path
                stats.append(stat)

        return stats
