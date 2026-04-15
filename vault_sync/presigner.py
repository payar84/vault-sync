"""Presigner: generate time-limited signed tokens for secret paths."""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Optional

_DEFAULT_TTL = 300  # seconds
_DEFAULT_SECRET = "vault-sync-default-hmac-key"


@dataclass
class PresignConfig:
    ttl_seconds: int = _DEFAULT_TTL
    secret_key: str = _DEFAULT_SECRET

    def validate(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if not self.secret_key:
            raise ValueError("secret_key must not be empty")


@dataclass
class SignedToken:
    path: str
    expires_at: int
    signature: str

    def is_expired(self, now: Optional[float] = None) -> bool:
        ts = now if now is not None else time.time()
        return ts > self.expires_at

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "expires_at": self.expires_at,
            "signature": self.signature,
        }

    @staticmethod
    def from_dict(data: dict) -> "SignedToken":
        return SignedToken(
            path=data["path"],
            expires_at=int(data["expires_at"]),
            signature=data["signature"],
        )


class Presigner:
    def __init__(self, config: Optional[PresignConfig] = None) -> None:
        self._config = config or PresignConfig()
        self._config.validate()

    def _sign(self, path: str, expires_at: int) -> str:
        message = f"{path}:{expires_at}".encode()
        key = self._config.secret_key.encode()
        return hmac.new(key, message, hashlib.sha256).hexdigest()

    def sign(self, path: str, now: Optional[float] = None) -> SignedToken:
        ts = int(now if now is not None else time.time())
        expires_at = ts + self._config.ttl_seconds
        signature = self._sign(path, expires_at)
        return SignedToken(path=path, expires_at=expires_at, signature=signature)

    def verify(self, token: SignedToken, now: Optional[float] = None) -> bool:
        if token.is_expired(now):
            return False
        expected = self._sign(token.path, token.expires_at)
        return hmac.compare_digest(expected, token.signature)
