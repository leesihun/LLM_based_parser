"""Calculator Tool for numerical operations."""

from backend.services.agents.tools.base import BaseTool
from backend.utils.exceptions import ToolExecutionError
import statistics
from typing import Any, Dict, List


class CalculatorTool(BaseTool):
    """Perform mathematical and statistical calculations."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform mathematical calculations and statistical operations on numeric data."

    @property
    def parameters_description(self) -> str:
        return """
Parameters:
  - operation (str): Operation to perform (add, subtract, multiply, divide, mean, median, sum, etc.)
  - values (list): List of numbers to operate on
"""

    def execute(self, operation: str, values: List[float], **kwargs) -> Dict[str, Any]:
        """Execute calculation."""
        try:
            if operation == "sum":
                result = sum(values)
            elif operation == "mean":
                result = statistics.mean(values)
            elif operation == "median":
                result = statistics.median(values)
            elif operation == "std_dev":
                result = statistics.stdev(values) if len(values) > 1 else 0
            else:
                raise ToolExecutionError(f"Unknown operation: {operation}")

            return {"success": True, "result": result, "operation": operation, "count": len(values)}

        except Exception as e:
            raise ToolExecutionError(f"Calculation failed: {e}") from e
