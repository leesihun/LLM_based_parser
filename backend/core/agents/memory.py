"""
Agent Memory System

Stores and retrieves execution patterns for improved performance.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry."""

    task: str
    plan: Optional[Dict[str, Any]]
    execution_trace: Dict[str, Any]
    confidence: float
    tools_used: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task": self.task,
            "plan": self.plan,
            "execution_trace": self.execution_trace,
            "confidence": self.confidence,
            "tools_used": self.tools_used,
            "timestamp": self.timestamp,
            "success": self.success,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryEntry:
        """Create from dictionary."""
        return cls(
            task=data["task"],
            plan=data.get("plan"),
            execution_trace=data.get("execution_trace", {}),
            confidence=data.get("confidence", 0.0),
            tools_used=data.get("tools_used", []),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            success=data.get("success", True),
            notes=data.get("notes", "")
        )


class AgentMemory:
    """
    Stores and retrieves agent execution patterns.

    Features:
    - Short-term memory: Current session
    - Long-term memory: Persistent storage
    - Similarity-based recall
    - Success pattern learning
    """

    def __init__(
        self,
        agent_id: str,
        storage_path: Optional[str | Path] = None,
        max_short_term: int = 50
    ):
        """
        Initialize agent memory.

        Args:
            agent_id: Agent identifier
            storage_path: Path for persistent storage
            max_short_term: Maximum short-term memory entries
        """
        self.agent_id = agent_id
        self.max_short_term = max_short_term

        # Short-term memory (current session)
        self.short_term: List[MemoryEntry] = []

        # Long-term storage
        if storage_path is None:
            storage_path = Path(__file__).parents[3] / "data" / "agent_memory"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.memory_file = self.storage_path / f"{agent_id}_memory.json"

        # Load existing memories
        self.long_term = self._load_long_term()

        logger.info(f"Initialized memory for agent {agent_id}: {len(self.long_term)} entries")

    def remember_successful_strategy(
        self,
        task: str,
        plan: Optional[Any],
        trace: Any,
        confidence: float,
        notes: str = ""
    ) -> None:
        """
        Store successful execution strategy.

        Args:
            task: Task description
            plan: Execution plan used
            trace: Execution trace
            confidence: Confidence score
            notes: Optional notes
        """
        entry = MemoryEntry(
            task=task,
            plan=plan.to_dict() if plan and hasattr(plan, 'to_dict') else None,
            execution_trace=trace.to_dict() if hasattr(trace, 'to_dict') else {},
            confidence=confidence,
            tools_used=list(trace.get_tools_used()) if hasattr(trace, 'get_tools_used') else [],
            success=True,
            notes=notes
        )

        # Add to short-term memory
        self.short_term.append(entry)

        # Trim short-term if needed
        if len(self.short_term) > self.max_short_term:
            self.short_term = self.short_term[-self.max_short_term:]

        # Add to long-term if high confidence
        if confidence >= 0.8:
            self.long_term.append(entry)
            self._save_long_term()

            logger.info(f"Stored successful strategy: {task[:50]}... (confidence: {confidence:.2f})")

    def recall_similar_strategies(
        self,
        task: str,
        top_k: int = 3,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Recall similar past strategies.

        Args:
            task: Current task
            top_k: Number of strategies to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of similar strategy dicts
        """
        if not self.long_term:
            return []

        # Simple keyword-based similarity (can be enhanced with embeddings)
        task_lower = task.lower()
        task_words = set(task_lower.split())

        scored_entries = []
        for entry in self.long_term:
            if entry.confidence < min_confidence:
                continue

            # Calculate similarity
            entry_words = set(entry.task.lower().split())
            common_words = task_words & entry_words
            similarity = len(common_words) / max(len(task_words), len(entry_words))

            if similarity > 0.2:  # Minimum similarity threshold
                scored_entries.append((similarity, entry))

        # Sort by similarity
        scored_entries.sort(reverse=True, key=lambda x: x[0])

        # Return top-k
        results = []
        for similarity, entry in scored_entries[:top_k]:
            results.append({
                "task": entry.task,
                "similarity": similarity,
                "confidence": entry.confidence,
                "tools_used": entry.tools_used,
                "plan": entry.plan,
                "notes": entry.notes
            })

        if results:
            logger.info(f"Recalled {len(results)} similar strategies")

        return results

    def remember_error(
        self,
        task: str,
        error: str,
        failed_action: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store error pattern for future avoidance.

        Args:
            task: Task that failed
            error: Error message
            failed_action: Action that caused error
        """
        entry = MemoryEntry(
            task=task,
            plan=None,
            execution_trace={"failed_action": failed_action, "error": error},
            confidence=0.0,
            tools_used=[],
            success=False,
            notes=f"Error: {error}"
        )

        self.short_term.append(entry)
        logger.warning(f"Stored error pattern: {error[:100]}...")

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        successful = [e for e in self.long_term if e.success]

        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "successful_count": len(successful),
            "average_confidence": sum(e.confidence for e in successful) / len(successful) if successful else 0,
            "most_used_tools": self._get_most_used_tools(),
        }

    def _get_most_used_tools(self) -> List[tuple[str, int]]:
        """Get most frequently used tools."""
        tool_counts: Dict[str, int] = {}

        for entry in self.long_term:
            for tool in entry.tools_used:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1

        # Sort by count
        sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_tools[:5]

    def _load_long_term(self) -> List[MemoryEntry]:
        """Load long-term memory from disk."""
        if not self.memory_file.exists():
            return []

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            entries = [MemoryEntry.from_dict(entry) for entry in data]
            return entries

        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return []

    def _save_long_term(self) -> None:
        """Save long-term memory to disk."""
        try:
            data = [entry.to_dict() for entry in self.long_term]

            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def clear_short_term(self) -> None:
        """Clear short-term memory."""
        self.short_term = []
        logger.info("Cleared short-term memory")

    def consolidate(self) -> None:
        """Consolidate short-term memories into long-term storage."""
        high_confidence = [e for e in self.short_term if e.confidence >= 0.8]

        if high_confidence:
            self.long_term.extend(high_confidence)
            self._save_long_term()
            logger.info(f"Consolidated {len(high_confidence)} memories to long-term storage")

        self.clear_short_term()
