"""Health check utilities for Vault connectivity."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from vault_sync.client import VaultClient
from vault_sync.retry import RetryConfig, with_retry

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    reachable: bool
    authenticated: bool
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.reachable and self.authenticated

    def __repr__(self) -> str:
        if self.ok:
            return "HealthStatus(ok=True)"
        return f"HealthStatus(ok=False, error={self.error!r})"


def check_health(
    client: VaultClient,
    retry_config: Optional[RetryConfig] = None,
) -> HealthStatus:
    """Check if Vault is reachable and the client is authenticated."""
    cfg = retry_config or RetryConfig(max_attempts=1, base_delay=0.0)

    def _do_check() -> HealthStatus:
        try:
            authenticated = client.is_authenticated()
            return HealthStatus(reachable=True, authenticated=authenticated)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Health check failed: %s", exc)
            return HealthStatus(reachable=False, authenticated=False, error=str(exc))

    try:
        return with_retry(_do_check, cfg)
    except RuntimeError as exc:
        return HealthStatus(reachable=False, authenticated=False, error=str(exc))
