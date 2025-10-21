"""Service container wiring backend dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, TYPE_CHECKING

from backend.core.conversation_memory import ConversationMemory
from backend.core.llm import LLMClient
from backend.core.user_management import UserManager
from backend.services.files.file_handler import FileHandler
from backend.services.search.web_search_feature import WebSearchFeature

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from backend.services.rag.rag_system import RAGSystem


class NullRAGSystem:
    """Fallback RAG implementation used when optional deps are missing."""

    def get_context_for_query(self, query: str, max_context_length: int | None = None) -> str:
        return ""

    def search(self, query: str, n_results: int = 5) -> List[dict]:
        return []


@dataclass
class ServiceContainer:
    """Bundle of core backend services shared across routes."""

    llm_client: LLMClient
    memory: ConversationMemory
    user_manager: UserManager
    rag_system: "RAGSystem | NullRAGSystem"
    file_handler: FileHandler
    web_search: WebSearchFeature

    @classmethod
    def build(cls, config_path: str | None = None) -> "ServiceContainer":
        """Construct services using shared configuration."""
        config_file = config_path or str(
            Path(__file__).resolve().parents[2] / "backend" / "config" / "config.json"
        )

        llm_client = LLMClient(config_file)
        memory = ConversationMemory()
        config_dir = Path(config_file).parent
        users_path = config_dir / "users.json"
        sessions_path = config_dir / "user_sessions.json"
        user_manager = UserManager(str(users_path), str(sessions_path))
        try:
            from backend.services.rag.rag_system import RAGSystem as _RAGSystem

            rag_system = _RAGSystem(config_file)
        except ModuleNotFoundError as exc:
            import logging

            logging.getLogger(__name__).warning("RAG system disabled: %s", exc)
            rag_system = NullRAGSystem()
        file_handler = FileHandler()
        web_search = WebSearchFeature(llm_client.config.get("web_search", {}), llm_client)

        return cls(
            llm_client=llm_client,
            memory=memory,
            user_manager=user_manager,
            rag_system=rag_system,
            file_handler=file_handler,
            web_search=web_search,
        )
