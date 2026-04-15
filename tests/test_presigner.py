"""Tests for vault_sync.presigner."""
import pytest
from vault_sync.presigner import Presigner, PresignConfig, SignedToken

_NOW = 1_700_000_000.0


@pytest.fixture
def presigner():
    return Presigner(PresignConfig(ttl_seconds=60, secret_key="test-secret"))


def test_config_rejects_zero_ttl():
    with pytest.raises(ValueError, match="ttl_seconds"):
        PresignConfig(ttl_seconds=0).validate()


def test_config_rejects_negative_ttl():
    with pytest.raises(ValueError, match="ttl_seconds"):
        PresignConfig(ttl_seconds=-1).validate()


def test_config_rejects_empty_secret():
    with pytest.raises(ValueError, match="secret_key"):
        PresignConfig(secret_key="").validate()


def test_config_accepts_valid_values():
    cfg = PresignConfig(ttl_seconds=120, secret_key="abc")
    cfg.validate()  # should not raise


def test_sign_returns_token(presigner):
    token = presigner.sign("secret/myapp", now=_NOW)
    assert token.path == "secret/myapp"
    assert token.expires_at == int(_NOW) + 60
    assert len(token.signature) == 64  # sha256 hex digest


def test_verify_valid_token(presigner):
    token = presigner.sign("secret/myapp", now=_NOW)
    assert presigner.verify(token, now=_NOW + 30) is True


def test_verify_expired_token(presigner):
    token = presigner.sign("secret/myapp", now=_NOW)
    assert presigner.verify(token, now=_NOW + 61) is False


def test_verify_tampered_signature(presigner):
    token = presigner.sign("secret/myapp", now=_NOW)
    bad = SignedToken(path=token.path, expires_at=token.expires_at, signature="deadbeef" * 8)
    assert presigner.verify(bad, now=_NOW + 1) is False


def test_verify_tampered_path(presigner):
    token = presigner.sign("secret/myapp", now=_NOW)
    bad = SignedToken(path="secret/other", expires_at=token.expires_at, signature=token.signature)
    assert presigner.verify(bad, now=_NOW + 1) is False


def test_token_is_expired_past_deadline():
    token = SignedToken(path="p", expires_at=int(_NOW), signature="x")
    assert token.is_expired(now=_NOW + 1) is True


def test_token_is_not_expired_before_deadline():
    token = SignedToken(path="p", expires_at=int(_NOW) + 10, signature="x")
    assert token.is_expired(now=_NOW) is False


def test_to_dict_roundtrip(presigner):
    token = presigner.sign("secret/db", now=_NOW)
    restored = SignedToken.from_dict(token.to_dict())
    assert restored.path == token.path
    assert restored.expires_at == token.expires_at
    assert restored.signature == token.signature


def test_different_keys_produce_different_signatures():
    p1 = Presigner(PresignConfig(ttl_seconds=60, secret_key="key-a"))
    p2 = Presigner(PresignConfig(ttl_seconds=60, secret_key="key-b"))
    t1 = p1.sign("secret/x", now=_NOW)
    t2 = p2.sign("secret/x", now=_NOW)
    assert t1.signature != t2.signature
