#!/usr/bin/env python3
"""
SearXNG Restart Helper Script
Restarts the SearXNG Docker container to ensure fresh state before searches
"""

import subprocess
import logging
import time
from typing import Dict, Optional


class SearXNGManager:
    """Manager for SearXNG container lifecycle"""

    def __init__(self):
        """Initialize SearXNG manager"""
        self.logger = logging.getLogger(__name__)
        self.container_name = "searxng"
        self.wsl_distro = "Ubuntu"

    def restart_searxng(self, wait_seconds: int = 3) -> Dict[str, any]:
        """
        Restart SearXNG Docker container

        Args:
            wait_seconds: Seconds to wait after restart for service to be ready

        Returns:
            Dictionary with restart status
        """
        try:
            # Restart container via WSL
            restart_cmd = [
                'wsl', '-d', self.wsl_distro, '-e',
                'docker', 'restart', self.container_name
            ]

            self.logger.info(f"Restarting SearXNG container: {self.container_name}")

            result = subprocess.run(
                restart_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )

            if result.returncode != 0:
                error_msg = f"Docker restart failed: {result.stderr}"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'returncode': result.returncode
                }

            # Wait for service to be ready
            self.logger.info(f"Waiting {wait_seconds} seconds for SearXNG to be ready...")
            time.sleep(wait_seconds)

            # Verify container is running
            status = self.check_container_status()

            return {
                'success': True,
                'message': f'SearXNG container restarted successfully',
                'container_status': status,
                'wait_time': wait_seconds
            }

        except subprocess.TimeoutExpired:
            error_msg = "Docker restart command timed out"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error during restart: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def check_container_status(self) -> Dict[str, any]:
        """
        Check if SearXNG container is running

        Returns:
            Dictionary with container status
        """
        try:
            status_cmd = [
                'wsl', '-d', self.wsl_distro, '-e',
                'docker', 'ps', '--filter', f'name={self.container_name}',
                '--format', '{{.Status}}'
            ]

            result = subprocess.run(
                status_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )

            if result.returncode != 0:
                return {
                    'running': False,
                    'error': result.stderr
                }

            status_output = result.stdout.strip()
            is_running = 'Up' in status_output

            return {
                'running': is_running,
                'status': status_output if status_output else 'Not running'
            }

        except Exception as e:
            return {
                'running': False,
                'error': str(e)
            }

    def test_searxng_connection(self, timeout: int = 5) -> Dict[str, any]:
        """
        Test if SearXNG is responding to requests

        Args:
            timeout: Request timeout in seconds

        Returns:
            Dictionary with test results
        """
        try:
            test_cmd = [
                'wsl', 'bash', '-c',
                f"curl -s --max-time {timeout} 'http://localhost:8080/search?q=test&format=json&language=en' | head -c 100"
            ]

            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=timeout + 2
            )

            if result.returncode != 0:
                return {
                    'responding': False,
                    'error': f'curl failed with code {result.returncode}'
                }

            # Check if we got any response
            has_response = len(result.stdout.strip()) > 0

            return {
                'responding': has_response,
                'response_preview': result.stdout[:100] if has_response else None
            }

        except Exception as e:
            return {
                'responding': False,
                'error': str(e)
            }

    def ensure_searxng_ready(self, max_retries: int = 2) -> Dict[str, any]:
        """
        Ensure SearXNG is ready by testing and restarting if needed

        Args:
            max_retries: Maximum number of restart attempts

        Returns:
            Dictionary with ready status
        """
        # First, check if it's already responding
        test_result = self.test_searxng_connection()

        if test_result['responding']:
            self.logger.info("SearXNG is already responding")
            return {
                'success': True,
                'already_ready': True,
                'restarts_needed': 0
            }

        # Not responding, try restarting
        for attempt in range(1, max_retries + 1):
            self.logger.info(f"SearXNG not responding, restart attempt {attempt}/{max_retries}")

            restart_result = self.restart_searxng(wait_seconds=5)

            if not restart_result['success']:
                if attempt == max_retries:
                    return {
                        'success': False,
                        'error': f"Failed to restart after {max_retries} attempts",
                        'last_error': restart_result.get('error')
                    }
                continue

            # Test if now responding
            test_result = self.test_searxng_connection()

            if test_result['responding']:
                self.logger.info(f"SearXNG ready after {attempt} restart(s)")
                return {
                    'success': True,
                    'already_ready': False,
                    'restarts_needed': attempt
                }

        return {
            'success': False,
            'error': 'SearXNG still not responding after restarts'
        }


def restart_searxng_command():
    """Command-line interface for restarting SearXNG"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("SearXNG Restart Helper")
    print("=" * 50)

    manager = SearXNGManager()

    # Check current status
    print("\nChecking current container status...")
    status = manager.check_container_status()
    print(f"Container running: {status.get('running')}")
    print(f"Status: {status.get('status', 'Unknown')}")

    # Test connection
    print("\nTesting SearXNG connection...")
    test_result = manager.test_searxng_connection()
    print(f"Responding: {test_result.get('responding')}")

    if not test_result.get('responding'):
        print("\nSearXNG not responding, attempting restart...")
        restart_result = manager.restart_searxng()

        if restart_result['success']:
            print(f"✓ {restart_result['message']}")
            print(f"  Wait time: {restart_result['wait_time']}s")

            # Re-test connection
            print("\nRe-testing connection after restart...")
            test_result = manager.test_searxng_connection()
            print(f"Responding: {test_result.get('responding')}")

            if test_result.get('responding'):
                print("\n✓ SearXNG is now ready!")
            else:
                print("\n✗ SearXNG still not responding")
        else:
            print(f"✗ Restart failed: {restart_result.get('error')}")
    else:
        print("\n✓ SearXNG is already responding - no restart needed")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    restart_searxng_command()
