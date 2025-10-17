"""TypeScript Web Search Bridge - Node.js 프로세스 호출"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TypeScriptSearchBridge:
    """Page Assist TypeScript 검색을 Python에서 호출"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.ts_dir = Path(__file__).parent.parent.parent.parent / "websearch_ts"
        self.node_script = self.ts_dir / "search.js"

        # Check if Node.js is available
        self._check_node()

        # Check if dependencies are installed
        self._check_dependencies()

    def _check_node(self) -> bool:
        """Node.js 설치 확인"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            if result.returncode == 0:
                logger.info(f"Node.js found: {result.stdout.strip()}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        logger.warning("Node.js not found. TypeScript search will not work.")
        return False

    def _check_dependencies(self) -> bool:
        """npm 패키지 설치 확인"""
        package_json = self.ts_dir / "package.json"
        node_modules = self.ts_dir / "node_modules"

        if not package_json.exists():
            logger.error(f"package.json not found at {package_json}")
            return False

        if not node_modules.exists():
            logger.info("Installing npm dependencies...")
            try:
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=str(self.ts_dir),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                )
                if result.returncode == 0:
                    logger.info("npm dependencies installed successfully")
                    return True
                logger.error(f"npm install failed: {result.stderr}")
                return False
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Failed to install npm dependencies: {exc}")
                return False

        return True

    def search(
        self,
        query: str,
        provider: str = "google",
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """
        TypeScript 검색 실행 (Page Assist 원본 코드)

        Args:
            query: 검색어
            provider: google, duckduckgo, brave_api, tavily_api, exa_api
            max_results: 최대 결과 수

        Returns:
            검색 결과 딕셔너리
        """
        if not self.node_script.exists():
            return {
                "success": False,
                "error": f"TypeScript search script not found at {self.node_script}",
                "results": [],
            }

        # Prepare config
        config = {
            "max_results": max_results,
            "google_domain": self.config.get("google_domain", "google.com"),
            "brave_api_key": self.config.get("brave_api_key", ""),
            "tavily_api_key": self.config.get("tavily_api_key", ""),
            "exa_api_key": self.config.get("exa_api_key", ""),
        }

        config_json = json.dumps(config)

        try:
            # Run Node.js script
            logger.info(f"Running TypeScript search: {provider} - {query}")

            result = subprocess.run(
                ["node", str(self.node_script), provider, query, config_json],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=str(self.ts_dir),
            )

            if result.returncode != 0:
                error_output = result.stderr or result.stdout
                logger.error(f"TypeScript search failed: {error_output}")
                return {
                    "success": False,
                    "error": error_output,
                    "results": [],
                }

            # Parse JSON output
            try:
                output = (result.stdout or "").strip()
                data = json.loads(output)

                if data.get("success"):
                    logger.info(f"TypeScript search succeeded: {data.get('result_count')} results")
                else:
                    logger.warning(f"TypeScript search returned error: {data.get('error')}")

                return data

            except json.JSONDecodeError as exc:
                logger.error(f"Failed to parse TypeScript output: {exc}")
                logger.error(f"Output: {result.stdout}")
                return {
                    "success": False,
                    "error": f"Invalid JSON output: {str(exc)}",
                    "results": [],
                }

        except subprocess.TimeoutExpired:
            logger.error("TypeScript search timed out")
            return {
                "success": False,
                "error": "Search timeout",
                "results": [],
            }

        except Exception as exc:
            logger.error(f"TypeScript search exception: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "results": [],
            }
