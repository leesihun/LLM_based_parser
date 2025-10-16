"""Search analytics and metrics tracking system."""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .types import SearchExecution


@dataclass
class SearchMetrics:
    """Individual search execution metrics."""
    query: str
    provider: str
    success: bool
    result_count: int
    response_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    cache_hit: bool = False
    filtered_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'query': self.query,
            'provider': self.provider,
            'success': self.success,
            'result_count': self.result_count,
            'response_time': self.response_time,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message,
            'cache_hit': self.cache_hit,
            'filtered_count': self.filtered_count,
        }


class SearchAnalytics:
    """Analytics and metrics collection for search operations."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.enabled = self.config.get('enabled', True)
        self.max_history_size = self.config.get('max_history_size', 1000)
        self.retention_days = self.config.get('retention_days', 7)
        self.enable_detailed_logging = self.config.get('enable_detailed_logging', True)

        # In-memory storage
        self.search_history: deque = deque(maxlen=self.max_history_size)
        self.provider_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_searches': 0,
            'successful_searches': 0,
            'total_response_time': 0.0,
            'error_count': 0,
            'cache_hits': 0,
        })
        self.query_frequency: Dict[str, int] = defaultdict(int)
        self.hourly_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            'searches': 0,
            'successes': 0,
            'failures': 0,
        })

        # Error tracking
        self.error_patterns: Dict[str, int] = defaultdict(int)

        self.logger.info(f"SearchAnalytics initialized: enabled={self.enabled}")

    def record_search(self, execution: SearchExecution, response_time: float,
                     cache_hit: bool = False, filtered_count: int = 0) -> None:
        """Record a search execution for analytics."""
        if not self.enabled:
            return

        try:
            # Extract error message if failed
            error_message = None
            if not execution.success and hasattr(execution, 'error'):
                error_message = str(execution.error)

            # Create metrics record
            metrics = SearchMetrics(
                query=execution.query,
                provider=execution.provider,
                success=execution.success,
                result_count=len(execution.results) if execution.results else 0,
                response_time=response_time,
                timestamp=datetime.now(),
                error_message=error_message,
                cache_hit=cache_hit,
                filtered_count=filtered_count,
            )

            # Store in history
            self.search_history.append(metrics)

            # Update provider statistics
            self._update_provider_stats(metrics)

            # Update query frequency
            self.query_frequency[execution.query] += 1

            # Update hourly statistics
            self._update_hourly_stats(metrics)

            # Track error patterns
            if error_message:
                self.error_patterns[error_message] += 1

            if self.enable_detailed_logging:
                self.logger.info(
                    f"Search recorded: query='{execution.query}' provider={execution.provider} "
                    f"success={execution.success} results={len(execution.results) if execution.results else 0} "
                    f"response_time={response_time:.2f}s cache_hit={cache_hit}"
                )

        except Exception as e:
            self.logger.warning(f"Failed to record search metrics: {e}")

    def _update_provider_stats(self, metrics: SearchMetrics) -> None:
        """Update statistics for a specific provider."""
        stats = self.provider_stats[metrics.provider]
        stats['total_searches'] += 1

        if metrics.success:
            stats['successful_searches'] += 1
        else:
            stats['error_count'] += 1

        stats['total_response_time'] += metrics.response_time

        if metrics.cache_hit:
            stats['cache_hits'] += 1

    def _update_hourly_stats(self, metrics: SearchMetrics) -> None:
        """Update hourly statistics."""
        hour_key = metrics.timestamp.strftime('%Y-%m-%d-%H')

        stats = self.hourly_stats[hour_key]
        stats['searches'] += 1

        if metrics.success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1

    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}

        for provider, data in self.provider_stats.items():
            total_searches = data['total_searches']
            if total_searches == 0:
                continue

            success_rate = data['successful_searches'] / total_searches
            avg_response_time = data['total_response_time'] / total_searches

            stats[provider] = {
                'total_searches': total_searches,
                'successful_searches': data['successful_searches'],
                'success_rate': round(success_rate, 3),
                'avg_response_time': round(avg_response_time, 3),
                'error_count': data['error_count'],
                'cache_hits': data['cache_hits'],
                'cache_hit_rate': round(data['cache_hits'] / total_searches, 3) if total_searches > 0 else 0,
            }

        return stats

    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently searched queries."""
        sorted_queries = sorted(
            self.query_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'query': query, 'frequency': frequency}
            for query, frequency in sorted_queries[:limit]
        ]

    def get_hourly_trends(self, hours: int = 24) -> Dict[str, Dict[str, int]]:
        """Get search trends for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_stats = {}

        for hour_key, stats in self.hourly_stats.items():
            try:
                # Parse hour key (format: YYYY-MM-DD-HH)
                hour_datetime = datetime.strptime(hour_key, '%Y-%m-%d-%H')
                if hour_datetime >= cutoff_time:
                    recent_stats[hour_key] = stats.copy()
            except ValueError:
                continue

        return recent_stats

    def get_error_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common error patterns."""
        sorted_errors = sorted(
            self.error_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'error': error, 'count': count}
            for error, count in sorted_errors[:limit]
        ]

    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall search statistics."""
        if not self.search_history:
            return {
                'total_searches': 0,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'cache_hit_rate': 0.0,
                'unique_queries': 0,
                'most_active_hour': None,
            }

        total_searches = len(self.search_history)
        successful_searches = sum(1 for m in self.search_history if m.success)
        total_response_time = sum(m.response_time for m in self.search_history)
        cache_hits = sum(1 for m in self.search_history if m.cache_hit)

        success_rate = successful_searches / total_searches if total_searches > 0 else 0
        avg_response_time = total_response_time / total_searches if total_searches > 0 else 0
        cache_hit_rate = cache_hits / total_searches if total_searches > 0 else 0

        # Find most active hour
        hourly_activity = defaultdict(int)
        for metrics in self.search_history:
            hour_key = metrics.timestamp.strftime('%Y-%m-%d-%H')
            hourly_activity[hour_key] += 1

        most_active_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None

        return {
            'total_searches': total_searches,
            'successful_searches': successful_searches,
            'success_rate': round(success_rate, 3),
            'avg_response_time': round(avg_response_time, 3),
            'cache_hits': cache_hits,
            'cache_hit_rate': round(cache_hit_rate, 3),
            'unique_queries': len(self.query_frequency),
            'most_active_hour': most_active_hour,
            'retention_days': self.retention_days,
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        return {
            'overall_stats': self.get_overall_stats(),
            'provider_stats': self.get_provider_stats(),
            'top_queries': self.get_top_queries(10),
            'error_summary': self.get_error_summary(5),
            'hourly_trends': self.get_hourly_trends(24),
            'timestamp': datetime.now().isoformat(),
        }

    def export_history(self, format: str = 'json') -> str:
        """Export search history in specified format."""
        if format.lower() == 'json':
            history_data = [metrics.to_dict() for metrics in self.search_history]
            return json.dumps(history_data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def cleanup_old_data(self) -> None:
        """Remove data older than retention period."""
        if not self.enabled:
            return

        cutoff_time = datetime.now() - timedelta(days=self.retention_days)

        # Clean up search history
        original_size = len(self.search_history)
        self.search_history = deque(
            (metrics for metrics in self.search_history if metrics.timestamp >= cutoff_time),
            maxlen=self.max_history_size
        )

        # Clean up hourly stats
        cutoff_hour = cutoff_time.strftime('%Y-%m-%d-%H')
        keys_to_remove = [
            hour_key for hour_key in self.hourly_stats.keys()
            if hour_key < cutoff_hour
        ]

        for key in keys_to_remove:
            del self.hourly_stats[key]

        removed_count = original_size - len(self.search_history)
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} old search records")

    def reset_stats(self) -> None:
        """Reset all statistics and history."""
        self.search_history.clear()
        self.provider_stats.clear()
        self.query_frequency.clear()
        self.hourly_stats.clear()
        self.error_patterns.clear()
        self.logger.info("Search analytics reset")


def create_search_analytics(config: Optional[Dict] = None) -> SearchAnalytics:
    """Factory function to create a SearchAnalytics instance."""
    return SearchAnalytics(config)
