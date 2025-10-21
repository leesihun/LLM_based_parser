"""JSON Analyzer Tool - Main entry point for JSON analysis."""

from backend.services.agents.tools.base import BaseTool
from backend.utils.json_utils import get_json_statistics, extract_numeric_fields
from typing import Any, Dict


class JSONAnalyzerTool(BaseTool):
    """Analyze JSON structure and extract information."""

    @property
    def name(self) -> str:
        return "json_analyzer"

    @property
    def description(self) -> str:
        return "Analyze JSON structure, extract statistics, and provide structural information."

    @property
    def parameters_description(self) -> str:
        return """
Parameters:
  - json_data (dict|list): JSON data to analyze
  - analysis_type (str): Type of analysis (structure, fields, summary)
"""

    def execute(self, json_data: Any, analysis_type: str = "structure", **kwargs) -> Dict[str, Any]:
        """Execute JSON analysis."""
        if analysis_type == "structure":
            stats = get_json_statistics(json_data)
            return {"success": True, "analysis_type": "structure", **stats}

        elif analysis_type == "fields":
            numeric_fields = extract_numeric_fields(json_data)
            return {
                "success": True,
                "analysis_type": "fields",
                "numeric_fields": list(numeric_fields.keys()),
                "field_count": len(numeric_fields)
            }

        else:
            return {"success": True, "analysis_type": analysis_type, "data": json_data}
