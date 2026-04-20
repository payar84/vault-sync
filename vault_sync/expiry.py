"""Secret expiry tracking — warns or errors when secrets exceed a maximum age."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


@dataclass
class ExpiryConfig:
    max_age_days: int = 90
    warn_before_days: int = 14

    def validate(self) -> None:
        if self.max_age_days <= 0:
            raise ValueError("max_age_days must be positive")
        if self.warn_before_days <= 0:
            raise ValueError("warn_before_days must be positive")
        if self.warn_before_days >= self.max_age_days:
            raise ValueError("warn_before_days must be less than max_age_days")


@dataclass
class ExpiryStatus:
    path: str
    synced_at: datetime
    age_days: float
    expired: bool
    warning: bool
    message: str

    def __repr__(self) -> str:
        tag = "EXPIRED" if self.expired else ("WARN" if self.warning else "OK")
        return f"<ExpiryStatus {self.path!r} [{tag}] age={self.age_days:.1f}d>"


@dataclass
class ExpiryReport:
    statuses: List[ExpiryStatus] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(s.expired for s in self.statuses)

    @property
    def expired_count(self) -> int:
        return sum(1 for s in self.statuses if s.expired)

    @property
    def warning_count(self) -> int:
        return sum(1 for s in self.statuses if s.warning and not s.expired)

    def __repr__(self) -> str:
        return (
            f"<ExpiryReport total={len(self.statuses)} "
            f"expired={self.expired_count} warnings={self.warning_count}>"
        )


def check_expiry(
    records: Dict[str, str],
    config: Optional[ExpiryConfig] = None,
    now: Optional[datetime] = None,
) -> ExpiryReport:
    """Evaluate expiry for each path->iso-timestamp mapping."""
    if config is None:
        config = ExpiryConfig()
    config.validate()
    if now is None:
        now = datetime.now(tz=timezone.utc)

    report = ExpiryReport()
    for path, ts_str in records.items():
        synced_at = datetime.fromisoformat(ts_str)
        if synced_at.tzinfo is None:
            synced_at = synced_at.replace(tzinfo=timezone.utc)
        age = now - synced_at
        age_days = age.total_seconds() / 86400
        expired = age_days >= config.max_age_days
        warning = not expired and age_days >= (config.max_age_days - config.warn_before_days)
        if expired:
            msg = f"Secret at '{path}' expired ({age_days:.1f}d >= {config.max_age_days}d)"
        elif warning:
            remaining = config.max_age_days - age_days
            msg = f"Secret at '{path}' expiring soon ({remaining:.1f}d remaining)"
        else:
            msg = f"Secret at '{path}' is current ({age_days:.1f}d old)"
        report.statuses.append(
            ExpiryStatus(
                path=path,
                synced_at=synced_at,
                age_days=age_days,
                expired=expired,
                warning=warning,
                message=msg,
            )
        )
    return report
