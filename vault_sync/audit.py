"""Audit logging for vault-sync operations."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    timestamp: str
    action: str
    path: str
    key: str
    status: str
    namespace: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "path": self.path,
            "key": self.key,
            "status": self.status,
            "namespace": self.namespace,
        }


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)

    def record(self, action: str, path: str, key: str, status: str, namespace: Optional[str] = None) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            path=path,
            key=key,
            status=status,
            namespace=namespace,
        )
        self.entries.append(entry)
        logger.debug("[audit] %s %s -> %s (%s)", action, path, key, status)

    def write(self, output_path: Path) -> None:
        records = [e.to_dict() for e in self.entries]
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2)
        logger.info("Audit log written to %s (%d entries)", output_path, len(records))

    def summary(self) -> dict:
        counts: dict = {}
        for entry in self.entries:
            counts[entry.status] = counts.get(entry.status, 0) + 1
        return counts
