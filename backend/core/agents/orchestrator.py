"""
Agent Orchestrator

Coordinates multiple specialized agents for complex tasks.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.core.agents.base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multiple agents for complex multi-step workflows.

    Features:
    - Task delegation to specialized agents
    - Result aggregation
    - Parallel execution support (future)
    """

    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        """
        Initialize orchestrator.

        Args:
            agents: List of available agents
        """
        self.agents = agents or []
        self.agent_registry = {agent.agent_id: agent for agent in self.agents}

        logger.info(f"Initialized orchestrator with {len(self.agents)} agents")

    def add_agent(self, agent: BaseAgent) -> None:
        """Add agent to orchestrator."""
        self.agents.append(agent)
        self.agent_registry[agent.agent_id] = agent
        logger.info(f"Added agent: {agent.agent_id}")

    def execute_workflow(
        self,
        tasks: List[Dict[str, Any]],
        aggregate_results: bool = True
    ) -> Dict[str, Any]:
        """
        Execute multi-task workflow.

        Args:
            tasks: List of task dicts with 'agent_id', 'task', 'context'
            aggregate_results: Whether to aggregate results

        Returns:
            Combined results from all tasks
        """
        results = []

        for task_spec in tasks:
            agent_id = task_spec.get("agent_id")
            task = task_spec.get("task")
            context = task_spec.get("context", {})

            if agent_id not in self.agent_registry:
                logger.error(f"Agent not found: {agent_id}")
                continue

            agent = self.agent_registry[agent_id]
            result = agent.execute(task, context)
            results.append(result)

        if aggregate_results:
            return self._aggregate_results(results)

        return {"results": [r.to_dict() for r in results]}

    def _aggregate_results(self, results: List[AgentResult]) -> Dict[str, Any]:
        """Aggregate results from multiple agents."""
        aggregated = {
            "total_tasks": len(results),
            "successful": sum(1 for r in results if r.status == "completed"),
            "failed": sum(1 for r in results if r.status == "failed"),
            "average_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
            "combined_answer": "\n\n".join(r.answer for r in results),
            "all_insights": [insight for r in results for insight in r.insights],
            "results": [r.to_dict() for r in results]
        }

        return aggregated
