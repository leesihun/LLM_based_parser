"""
Task Planner

Creates execution plans for autonomous agents based on task analysis.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from backend.core.llm import LLMClient
from backend.core.llm.prompts import SystemPrompts

if TYPE_CHECKING:
    from backend.services.agents.tools.base import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    """Single step in execution plan."""

    step_number: int
    tool: str
    parameters: Dict[str, Any]
    reasoning: str
    expected_output: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "tool": self.tool,
            "parameters": self.parameters,
            "reasoning": self.reasoning,
            "expected_output": self.expected_output,
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan for a task."""

    steps: List[PlanStep] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low, medium, high
    estimated_iterations: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "steps": [step.to_dict() for step in self.steps],
            "estimated_complexity": self.estimated_complexity,
            "estimated_iterations": self.estimated_iterations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionPlan:
        """Create from dictionary."""
        steps = [
            PlanStep(
                step_number=s["step_number"],
                tool=s["tool"],
                parameters=s.get("parameters", {}),
                reasoning=s.get("reasoning", ""),
                expected_output=s.get("expected_output", "")
            )
            for s in data.get("steps", [])
        ]

        return cls(
            steps=steps,
            estimated_complexity=data.get("estimated_complexity", "medium"),
            estimated_iterations=data.get("estimated_iterations", len(steps))
        )


class TaskPlanner:
    """
    Creates execution plans for tasks using LLM reasoning.

    Analyzes:
    - Task complexity and requirements
    - Available tools and their capabilities
    - Data structure and context
    - Past successful strategies (if available)
    """

    def __init__(self, llm_client: LLMClient, tools: List[BaseTool]):
        """
        Initialize task planner.

        Args:
            llm_client: LLM client for planning
            tools: Available tools
        """
        self.llm_client = llm_client
        self.tools = tools
        self.tool_descriptions = self._build_tool_descriptions()

    def _build_tool_descriptions(self) -> str:
        """Build formatted description of available tools."""
        if not self.tools:
            return "No tools available."

        descriptions = []
        for tool in self.tools:
            desc = f"""
Tool: {tool.name}
Description: {tool.description}
Parameters: {getattr(tool, 'parameters_description', 'See tool implementation')}
Best for: {getattr(tool, 'use_cases', 'General purpose')}
""".strip()
            descriptions.append(desc)

        return "\n\n".join(descriptions)

    def create_plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Create execution plan for task.

        Args:
            task: Task description
            context: Optional context (data structure, past strategies, etc.)

        Returns:
            ExecutionPlan with steps to execute
        """
        context = context or {}

        logger.info(f"Creating execution plan for: {task[:100]}...")

        # Analyze task intent
        intent = self._classify_task_intent(task)
        logger.debug(f"Task intent: {intent}")

        # Analyze data structure if available
        data_structure = self._analyze_data_structure(context.get("json_data"))

        # Check for similar past strategies
        past_strategies = context.get("past_strategies", [])

        # Generate plan using LLM
        plan = self._generate_plan_with_llm(
            task=task,
            intent=intent,
            data_structure=data_structure,
            past_strategies=past_strategies
        )

        logger.info(f"Created plan with {len(plan.steps)} steps")
        return plan

    def _classify_task_intent(self, task: str) -> str:
        """
        Classify task into intent category.

        Categories:
        - extraction: Get specific values
        - aggregation: Calculate statistics
        - comparison: Compare values/groups
        - pattern_detection: Find trends/anomalies
        - insight_generation: General analysis
        """
        task_lower = task.lower()

        keywords = {
            "extraction": ["find", "get", "extract", "what is", "show me"],
            "aggregation": ["sum", "total", "average", "mean", "count", "maximum", "minimum"],
            "comparison": ["compare", "difference", "versus", "vs", "better", "worse"],
            "pattern_detection": ["trend", "pattern", "anomaly", "outlier", "correlation"],
            "insight_generation": ["analyze", "why", "insight", "explain", "recommend"]
        }

        for intent, words in keywords.items():
            if any(word in task_lower for word in words):
                return intent

        return "general_analysis"

    def _analyze_data_structure(self, json_data: Optional[Any]) -> str:
        """Analyze JSON data structure for planning."""
        if not json_data:
            return "No data provided"

        if isinstance(json_data, dict):
            keys = list(json_data.keys())[:10]
            return f"Object with keys: {', '.join(keys)}"

        elif isinstance(json_data, list):
            length = len(json_data)
            if length > 0:
                sample_type = type(json_data[0]).__name__
                return f"Array of {length} {sample_type} items"
            return "Empty array"

        return f"Primitive type: {type(json_data).__name__}"

    def _generate_plan_with_llm(
        self,
        task: str,
        intent: str,
        data_structure: str,
        past_strategies: List[Dict[str, Any]]
    ) -> ExecutionPlan:
        """Generate plan using LLM reasoning."""

        # Build prompt
        prompt = f"""You are a task planning expert for an autonomous agent system.

Task: {task}
Intent: {intent}
Data Structure: {data_structure}

Available Tools:
{self.tool_descriptions}

{"Past Successful Strategies:" if past_strategies else ""}
{self._format_past_strategies(past_strategies)}

Create a step-by-step execution plan to accomplish this task.
Consider:
1. What tools are needed?
2. In what order should they be used?
3. What parameters should each tool receive?
4. How does each step build toward the goal?

Output your plan in JSON format:
```json
{{
  "steps": [
    {{
      "step_number": 1,
      "tool": "tool_name",
      "parameters": {{"key": "value"}},
      "reasoning": "Why this step is needed",
      "expected_output": "What this step should produce"
    }}
  ],
  "estimated_complexity": "low|medium|high",
  "estimated_iterations": 5
}}
```

Respond with ONLY the JSON, no other text."""

        messages = [
            {"role": "system", "content": "You are a planning expert. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.llm_client.chat_completion(
                messages,
                temperature=0.4  # Lower temperature for more consistent planning
            )

            # Parse response
            plan_text = response.content.strip()

            # Extract JSON from markdown if present
            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0].strip()

            plan_dict = json.loads(plan_text)
            plan = ExecutionPlan.from_dict(plan_dict)

            return plan

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            logger.error(f"Response: {response.content}")

            # Fallback: create basic plan based on intent
            return self._create_fallback_plan(task, intent)

        except Exception as e:
            logger.error(f"Plan generation failed: {e}", exc_info=True)
            return self._create_fallback_plan(task, intent)

    def _format_past_strategies(self, strategies: List[Dict[str, Any]]) -> str:
        """Format past strategies for prompt."""
        if not strategies:
            return ""

        formatted = []
        for i, strategy in enumerate(strategies[:3], 1):  # Top 3
            formatted.append(
                f"{i}. Task: {strategy.get('task', 'Unknown')}\n"
                f"   Success: {strategy.get('confidence', 0):.2f}\n"
                f"   Tools used: {', '.join(strategy.get('tools_used', []))}"
            )

        return "\n".join(formatted)

    def _create_fallback_plan(self, task: str, intent: str) -> ExecutionPlan:
        """Create simple fallback plan when LLM planning fails."""
        logger.warning("Using fallback plan generation")

        if intent == "extraction":
            steps = [
                PlanStep(
                    step_number=1,
                    tool="json_path_extractor",
                    parameters={"query": task},
                    reasoning="Extract requested value from JSON",
                    expected_output="Extracted value"
                )
            ]

        elif intent == "aggregation":
            steps = [
                PlanStep(
                    step_number=1,
                    tool="numeric_summary",
                    parameters={},
                    reasoning="Generate numerical statistics",
                    expected_output="Statistics summary"
                ),
                PlanStep(
                    step_number=2,
                    tool="calculator",
                    parameters={"operation": "aggregate"},
                    reasoning="Calculate aggregated value",
                    expected_output="Aggregated result"
                )
            ]

        else:
            # Generic plan
            steps = [
                PlanStep(
                    step_number=1,
                    tool="numeric_summary",
                    parameters={},
                    reasoning="Analyze data structure",
                    expected_output="Data analysis"
                )
            ]

        return ExecutionPlan(
            steps=steps,
            estimated_complexity="medium",
            estimated_iterations=len(steps) + 2
        )
