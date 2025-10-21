"""
Base Agent Implementation

Provides core agent functionality with ReAct loop execution.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from backend.core.llm import LLMClient
from backend.core.agents.executor import ReActExecutor, ExecutionTrace
from backend.core.agents.planner import TaskPlanner
from backend.core.agents.memory import AgentMemory
from backend.utils.exceptions import AgentError, AgentExecutionError

if TYPE_CHECKING:
    from backend.services.agents.tools.base import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for agent behavior."""

    max_iterations: int = 15
    thought_temperature: float = 0.7
    action_temperature: float = 0.2
    enable_self_correction: bool = True
    enable_memory: bool = True
    enable_planning: bool = True
    timeout_seconds: int = 300
    confidence_threshold: float = 0.8


@dataclass
class AgentResult:
    """Result from agent execution."""

    agent_id: str
    task: str
    answer: str
    confidence: float
    execution_trace: ExecutionTrace
    insights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    status: str = "completed"  # completed, failed, timeout

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "agent_id": self.agent_id,
            "task": self.task,
            "answer": self.answer,
            "confidence": self.confidence,
            "execution_trace": self.execution_trace.to_dict(),
            "insights": self.insights,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
        }


class BaseAgent:
    """
    Base autonomous agent using ReAct pattern.

    The agent can:
    - Plan task execution strategies
    - Reason about the current state
    - Select and execute tools
    - Learn from past executions
    - Self-correct errors
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        tools: Optional[List[BaseTool]] = None,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize agent.

        Args:
            agent_id: Unique identifier for this agent
            llm_client: LLM client instance
            tools: List of available tools
            config: Agent configuration
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.llm_client = llm_client
        self.tools = tools or []
        self.config = config or AgentConfig()

        # Initialize components
        self.executor = ReActExecutor(
            llm_client=self.llm_client,
            tools=self.tools,
            max_iterations=self.config.max_iterations,
            thought_temperature=self.config.thought_temperature,
            action_temperature=self.config.action_temperature,
        )

        self.planner = TaskPlanner(
            llm_client=self.llm_client,
            tools=self.tools
        ) if self.config.enable_planning else None

        self.memory = AgentMemory(
            agent_id=self.agent_id
        ) if self.config.enable_memory else None

        logger.info(f"Initialized agent: {self.agent_id}")

    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Execute a task autonomously.

        Args:
            task: Task description or question
            context: Optional context data (JSON, files, etc.)

        Returns:
            AgentResult with answer and execution details

        Raises:
            AgentExecutionError: If execution fails
        """
        start_time = datetime.now()
        context = context or {}

        try:
            logger.info(f"Agent {self.agent_id} executing task: {task[:100]}...")

            # Step 1: Check memory for similar past executions
            if self.memory:
                similar_strategies = self.memory.recall_similar_strategies(task)
                if similar_strategies:
                    logger.info(f"Found {len(similar_strategies)} similar past executions")
                    context["past_strategies"] = similar_strategies

            # Step 2: Plan execution strategy
            if self.planner:
                plan = self.planner.create_plan(task, context)
                logger.info(f"Created plan with {len(plan.steps)} steps")
                context["plan"] = plan
            else:
                plan = None

            # Step 3: Execute with ReAct loop
            trace = self.executor.execute(task, context)

            # Step 4: Generate insights
            insights = self._generate_insights(trace, context)

            # Step 5: Calculate confidence
            confidence = self._calculate_confidence(trace)

            # Step 6: Extract final answer
            answer = self._extract_answer(trace)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create result
            result = AgentResult(
                agent_id=self.agent_id,
                task=task,
                answer=answer,
                confidence=confidence,
                execution_trace=trace,
                insights=insights,
                execution_time_ms=execution_time,
                metadata={
                    "plan": plan.to_dict() if plan else None,
                    "tools_used": list(trace.get_tools_used()),
                    "iterations": len(trace.steps),
                },
                status="completed"
            )

            # Step 7: Store successful execution in memory
            if self.memory and confidence >= self.config.confidence_threshold:
                self.memory.remember_successful_strategy(
                    task=task,
                    plan=plan,
                    trace=trace,
                    confidence=confidence
                )

            logger.info(f"Task completed successfully in {execution_time:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Return failure result
            return AgentResult(
                agent_id=self.agent_id,
                task=task,
                answer=f"Execution failed: {str(e)}",
                confidence=0.0,
                execution_trace=ExecutionTrace(),
                execution_time_ms=execution_time,
                status="failed",
                metadata={"error": str(e)}
            )

    def _generate_insights(
        self,
        trace: ExecutionTrace,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from execution trace."""
        insights = []

        # Check for patterns in execution
        if len(trace.steps) > 10:
            insights.append(f"Complex task required {len(trace.steps)} iterations")

        # Check tool usage
        tools_used = trace.get_tools_used()
        if len(tools_used) > 5:
            insights.append(f"Multi-tool approach: used {len(tools_used)} different tools")

        return insights

    def _calculate_confidence(self, trace: ExecutionTrace) -> float:
        """
        Calculate confidence score based on execution.

        Factors:
        - Number of iterations (fewer is better)
        - Validation results
        - Tool execution success rate
        """
        if not trace.steps:
            return 0.0

        # Base confidence
        confidence = 0.8

        # Penalize excessive iterations
        if len(trace.steps) > self.config.max_iterations * 0.7:
            confidence *= 0.9

        # Boost if validation passed
        for step in trace.steps:
            if step.action and step.action.get("tool") == "validator":
                if step.result and step.result.get("valid"):
                    confidence = min(1.0, confidence * 1.1)

        # Check for errors
        error_count = sum(1 for step in trace.steps if step.error)
        if error_count > 0:
            confidence *= (1.0 - 0.1 * error_count)

        return max(0.0, min(1.0, confidence))

    def _extract_answer(self, trace: ExecutionTrace) -> str:
        """Extract final answer from execution trace."""
        if not trace.steps:
            return "No answer generated"

        # Look for final answer in last steps
        for step in reversed(trace.steps):
            if step.thought and "final answer" in step.thought.lower():
                if step.result and isinstance(step.result, dict):
                    return step.result.get("answer", step.result.get("content", ""))

            if step.result and isinstance(step.result, dict):
                if "answer" in step.result:
                    return step.result["answer"]

        # Fallback: use last result
        last_step = trace.steps[-1]
        if last_step.result:
            if isinstance(last_step.result, str):
                return last_step.result
            elif isinstance(last_step.result, dict):
                return last_step.result.get("content", str(last_step.result))

        return "Unable to extract answer from execution"

    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent's toolset."""
        self.tools.append(tool)
        self.executor.tools.append(tool)
        logger.info(f"Added tool: {tool.name}")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "tools_count": len(self.tools),
            "tools": [tool.name for tool in self.tools],
            "config": {
                "max_iterations": self.config.max_iterations,
                "enable_memory": self.config.enable_memory,
                "enable_planning": self.config.enable_planning,
            },
            "memory_enabled": self.memory is not None,
            "planner_enabled": self.planner is not None,
        }
