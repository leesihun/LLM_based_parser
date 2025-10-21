"""
ReAct Execution Engine

Implements the ReAct (Reasoning + Acting) pattern for autonomous agent execution.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from backend.core.llm import LLMClient
from backend.core.llm.prompts import SystemPrompts
from backend.utils.exceptions import (
    AgentExecutionError,
    AgentMaxIterationsError,
    ToolNotFoundError
)

if TYPE_CHECKING:
    from backend.services.agents.tools.base import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    """Single step in ReAct execution."""

    iteration: int
    thought: str
    action: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "iteration": self.iteration,
            "thought": self.thought,
            "action": self.action,
            "result": self._serialize_result(),
            "error": self.error,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }

    def _serialize_result(self) -> Any:
        """Serialize result for JSON response."""
        if self.result is None:
            return None
        if isinstance(self.result, (str, int, float, bool, list, dict)):
            return self.result
        # Convert complex objects to string representation
        return str(self.result)


@dataclass
class ExecutionTrace:
    """Complete trace of agent execution."""

    steps: List[ExecutionStep] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    total_iterations: int = 0
    success: bool = False

    def add_step(self, step: ExecutionStep) -> None:
        """Add execution step."""
        self.steps.append(step)
        self.total_iterations = len(self.steps)

    def complete(self, success: bool = True) -> None:
        """Mark execution as completed."""
        self.completed_at = datetime.now().isoformat()
        self.success = success

    def get_tools_used(self) -> set:
        """Get set of tools used in execution."""
        tools = set()
        for step in self.steps:
            if step.action and "tool" in step.action:
                tools.add(step.action["tool"])
        return tools

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "steps": [step.to_dict() for step in self.steps],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_iterations": self.total_iterations,
            "success": self.success,
            "tools_used": list(self.get_tools_used()),
        }


class ReActExecutor:
    """
    Executes tasks using the ReAct (Reasoning + Acting) pattern.

    ReAct Loop:
    1. Thought: Reason about current state and what to do next
    2. Action: Select and execute a tool
    3. Observation: Observe result and update state
    4. Repeat until task is complete
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tools: List[BaseTool],
        max_iterations: int = 15,
        thought_temperature: float = 0.7,
        action_temperature: float = 0.2,
    ):
        """
        Initialize ReAct executor.

        Args:
            llm_client: LLM client for reasoning
            tools: Available tools
            max_iterations: Maximum iterations before stopping
            thought_temperature: Temperature for thought generation
            action_temperature: Temperature for action selection
        """
        self.llm_client = llm_client
        self.tools = tools
        self.max_iterations = max_iterations
        self.thought_temperature = thought_temperature
        self.action_temperature = action_temperature

        # Build tool registry
        self.tool_registry = {tool.name: tool for tool in tools}

        logger.info(f"Initialized ReAct executor with {len(tools)} tools")

    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionTrace:
        """
        Execute task using ReAct loop.

        Args:
            task: Task to execute
            context: Execution context (data, plan, etc.)

        Returns:
            ExecutionTrace with complete execution history

        Raises:
            AgentMaxIterationsError: If max iterations exceeded
        """
        context = context or {}
        trace = ExecutionTrace()

        logger.info(f"Starting ReAct execution: {task[:100]}...")

        try:
            for iteration in range(1, self.max_iterations + 1):
                logger.info(f"Iteration {iteration}/{self.max_iterations}")

                # Step 1: Generate thought
                thought = self._generate_thought(task, context, trace)

                # Step 2: Select action
                action = self._select_action(thought, context, trace)

                # Step 3: Execute tool
                result, error = self._execute_tool(action)

                # Step 4: Create execution step
                step = ExecutionStep(
                    iteration=iteration,
                    thought=thought,
                    action=action,
                    result=result,
                    error=error,
                    confidence=self._estimate_confidence(thought, action, result, error)
                )

                trace.add_step(step)

                # Step 5: Update context with result
                if result:
                    context["last_result"] = result
                    context["last_action"] = action

                # Step 6: Check if task is complete
                if self._is_complete(step, context):
                    logger.info(f"Task completed in {iteration} iterations")
                    trace.complete(success=True)
                    break

                # Step 7: Check for errors and self-correct
                if error:
                    logger.warning(f"Tool error: {error}")
                    # Self-correction happens in next iteration

            else:
                # Max iterations reached
                logger.warning(f"Max iterations ({self.max_iterations}) reached")
                trace.complete(success=False)

            return trace

        except Exception as e:
            logger.error(f"ReAct execution failed: {e}", exc_info=True)
            trace.complete(success=False)
            raise AgentExecutionError(f"Execution failed: {e}") from e

    def _generate_thought(
        self,
        task: str,
        context: Dict[str, Any],
        trace: ExecutionTrace
    ) -> str:
        """
        Generate reasoning about current state.

        Uses LLM to analyze:
        - Original task
        - Execution history
        - Available tools
        - Current context

        Returns thought about what to do next.
        """
        # Build prompt for thought generation
        execution_history = self._format_execution_history(trace)
        tools_description = self._get_tools_description()

        prompt = f"""You are an autonomous agent reasoning about a task.

Task: {task}

Available tools:
{tools_description}

Execution history:
{execution_history}

Current context:
{json.dumps(context.get('last_result', {}), indent=2)[:500]}

Think step-by-step about what to do next. Consider:
1. What have we accomplished so far?
2. What information are we still missing?
3. What tool should we use next?
4. Are we close to completing the task?

Provide your thought process (2-3 sentences):"""

        messages = [
            {"role": "system", "content": "You are a reasoning expert for an autonomous agent."},
            {"role": "user", "content": prompt}
        ]

        response = self.llm_client.chat_completion(
            messages,
            temperature=self.thought_temperature
        )

        thought = response.content.strip()
        logger.debug(f"Thought: {thought}")

        return thought

    def _select_action(
        self,
        thought: str,
        context: Dict[str, Any],
        trace: ExecutionTrace
    ) -> Dict[str, Any]:
        """
        Select next action based on thought.

        Returns action dict with:
        - tool: Tool name
        - parameters: Tool parameters
        """
        tools_description = self._get_tools_description()

        prompt = f"""Based on your reasoning, select the next action.

Thought: {thought}

Available tools:
{tools_description}

Select the best tool and specify parameters in JSON format:
```json
{{
  "tool": "tool_name",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
```

Respond with ONLY the JSON, no other text."""

        messages = [
            {"role": "system", "content": "You are an action selection expert. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = self.llm_client.chat_completion(
            messages,
            temperature=self.action_temperature
        )

        # Parse action from response
        try:
            action_text = response.content.strip()

            # Extract JSON from markdown code blocks if present
            if "```json" in action_text:
                action_text = action_text.split("```json")[1].split("```")[0].strip()
            elif "```" in action_text:
                action_text = action_text.split("```")[1].split("```")[0].strip()

            action = json.loads(action_text)

            logger.debug(f"Selected action: {action}")
            return action

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse action JSON: {e}")
            logger.error(f"Response: {response.content}")

            # Fallback: return default action
            return {
                "tool": "error",
                "parameters": {"message": f"Failed to parse action: {e}"}
            }

    def _execute_tool(self, action: Dict[str, Any]) -> tuple[Optional[Any], Optional[str]]:
        """
        Execute selected tool.

        Returns:
            (result, error) tuple
        """
        tool_name = action.get("tool")
        parameters = action.get("parameters", {})

        if not tool_name:
            return None, "No tool specified in action"

        if tool_name not in self.tool_registry:
            return None, f"Tool not found: {tool_name}"

        tool = self.tool_registry[tool_name]

        try:
            logger.info(f"Executing tool: {tool_name} with params: {parameters}")
            result = tool.execute(**parameters)
            return result, None

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg

    def _is_complete(self, step: ExecutionStep, context: Dict[str, Any]) -> bool:
        """
        Check if task execution is complete.

        Completion signals:
        - Tool is "finalize_answer"
        - Thought contains "task complete" or "final answer"
        - High confidence with answer present
        """
        # Check for finalize action
        if step.action and step.action.get("tool") == "finalize_answer":
            return True

        # Check thought for completion indicators
        if step.thought:
            completion_keywords = [
                "task complete",
                "final answer",
                "done",
                "completed",
                "finished"
            ]
            thought_lower = step.thought.lower()

            for keyword in completion_keywords:
                if keyword in thought_lower:
                    return True

        # Check for answer in result
        if step.result and isinstance(step.result, dict):
            if "answer" in step.result or "final_answer" in step.result:
                return step.confidence > 0.7

        return False

    def _estimate_confidence(
        self,
        thought: str,
        action: Dict[str, Any],
        result: Any,
        error: Optional[str]
    ) -> float:
        """Estimate confidence for this step."""
        confidence = 0.5  # Base confidence

        # Increase confidence if no error
        if error is None:
            confidence += 0.3

        # Increase if result is present
        if result is not None:
            confidence += 0.2

        # Adjust based on thought clarity
        if thought and len(thought) > 20:
            confidence += 0.1

        return min(1.0, confidence)

    def _format_execution_history(self, trace: ExecutionTrace) -> str:
        """Format execution history for prompt."""
        if not trace.steps:
            return "No steps yet."

        history = []
        for step in trace.steps[-5:]:  # Last 5 steps
            history.append(
                f"Iteration {step.iteration}:\n"
                f"  Thought: {step.thought[:100]}...\n"
                f"  Action: {step.action.get('tool') if step.action else 'None'}\n"
                f"  Result: {'Success' if step.result else 'Failed'}"
            )

        return "\n".join(history)

    def _get_tools_description(self) -> str:
        """Get formatted description of available tools."""
        if not self.tools:
            return "No tools available."

        descriptions = []
        for tool in self.tools:
            desc = f"- {tool.name}: {tool.description}"
            if hasattr(tool, 'parameters'):
                desc += f"\n  Parameters: {tool.parameters}"
            descriptions.append(desc)

        return "\n".join(descriptions)
