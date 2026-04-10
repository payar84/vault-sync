"""Secret rotation tracking and enforcement for vault-sync."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class RotationPolicy:
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
class RotationStatus:
    key: str
    last_rotated: Optional[datetime]
    is_expired: bool
    is_expiring_soon: bool
    days_until_expiry: Optional[int]

    def __repr__(self) -> str:
        state = "expired" if self.is_expired else ("expiring soon" if self.is_expiring_soon else "ok")
        return f"<RotationStatus key={self.key!r} state={state} days_left={self.days_until_expiry}>"


@dataclass
class RotationTracker:
    policy: RotationPolicy
    _records: Dict[str, datetime] = field(default_factory=dict)

    def record_rotation(self, key: str, when: Optional[datetime] = None) -> None:
        self._records[key] = when or datetime.utcnow()

    def check(self, key: str) -> RotationStatus:
        now = datetime.utcnow()
        last = self._records.get(key)
        if last is None:
            return RotationStatus(
                key=key,
                last_rotated=None,
                is_expired=True,
                is_expiring_soon=False,
                days_until_expiry=None,
            )
        expiry = last + timedelta(days=self.policy.max_age_days)
        days_left = (expiry - now).days
        return RotationStatus(
            key=key,
            last_rotated=last,
            is_expired=days_left < 0,
            is_expiring_soon=0 <= days_left <= self.policy.warn_before_days,
            days_until_expiry=max(days_left, 0) if days_left >= 0 else None,
        )

    def check_all(self, keys: List[str]) -> List[RotationStatus]:
        return [self.check(k) for k in keys]

    def expired_keys(self, keys: List[str]) -> List[str]:
        return [s.key for s in self.check_all(keys) if s.is_expired]

    def expiring_soon_keys(self, keys: List[str]) -> List[str]:
        return [s.key for s in self.check_all(keys) if s.is_expiring_soon]
