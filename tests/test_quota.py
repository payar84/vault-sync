import pytest

from vault_sync.quota import QuotaConfig, QuotaStatus, check_quota


# ---------------------------------------------------------------------------
# QuotaConfig validation
# ---------------------------------------------------------------------------

def test_quota_config_rejects_zero_max_keys():
    with pytest.raises(ValueError, match="max_keys"):
        QuotaConfig(max_keys=0).validate()


def test_quota_config_rejects_negative_max_paths():
    with pytest.raises(ValueError, match="max_paths"):
        QuotaConfig(max_paths=-1).validate()


def test_quota_config_rejects_warn_at_zero():
    with pytest.raises(ValueError, match="warn_at"):
        QuotaConfig(warn_at=0.0).validate()


def test_quota_config_rejects_warn_at_above_one():
    with pytest.raises(ValueError, match="warn_at"):
        QuotaConfig(warn_at=1.1).validate()


def test_quota_config_accepts_valid_values():
    cfg = QuotaConfig(max_keys=100, max_paths=10, warn_at=0.75)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# check_quota — no limits
# ---------------------------------------------------------------------------

def test_no_limits_always_ok():
    secrets = {"path/a": {"KEY": "val"}, "path/b": {"X": "1", "Y": "2"}}
    status = check_quota(secrets, QuotaConfig())
    assert status.ok()
    assert status.warnings == []


def test_counts_are_correct():
    secrets = {"p1": {"A": "1", "B": "2"}, "p2": {"C": "3"}}
    status = check_quota(secrets, QuotaConfig())
    assert status.key_count == 3
    assert status.path_count == 2


# ---------------------------------------------------------------------------
# Key quota
# ---------------------------------------------------------------------------

def test_key_quota_exceeded():
    secrets = {"p": {"A": "1", "B": "2", "C": "3"}}
    status = check_quota(secrets, QuotaConfig(max_keys=2))
    assert not status.ok()
    assert status.exceeded
    assert any("exceeded" in w.lower() for w in status.warnings)


def test_key_quota_warning_near_limit():
    secrets = {"p": {"A": "1", "B": "2", "C": "3", "D": "4"}}
    # 4/5 = 80 % >= warn_at default 0.8
    status = check_quota(secrets, QuotaConfig(max_keys=5))
    assert status.ok()
    assert any("warning" in w.lower() for w in status.warnings)


def test_key_quota_well_below_limit_no_warning():
    secrets = {"p": {"A": "1"}}
    status = check_quota(secrets, QuotaConfig(max_keys=100))
    assert status.ok()
    assert status.warnings == []


# ---------------------------------------------------------------------------
# Path quota
# ---------------------------------------------------------------------------

def test_path_quota_exceeded():
    secrets = {f"path/{i}": {"K": "v"} for i in range(5)}
    status = check_quota(secrets, QuotaConfig(max_paths=3))
    assert not status.ok()
    assert any("path quota exceeded" in w.lower() for w in status.warnings)


def test_path_quota_warning():
    secrets = {f"path/{i}": {"K": "v"} for i in range(4)}
    # 4/5 = 80 % >= 0.8
    status = check_quota(secrets, QuotaConfig(max_paths=5))
    assert status.ok()
    assert any("path quota warning" in w.lower() for w in status.warnings)


# ---------------------------------------------------------------------------
# QuotaStatus repr
# ---------------------------------------------------------------------------

def test_repr_ok():
    status = check_quota({"p": {"A": "1"}}, QuotaConfig())
    assert "OK" in repr(status)


def test_repr_exceeded():
    secrets = {"p": {"A": "1", "B": "2"}}
    status = check_quota(secrets, QuotaConfig(max_keys=1))
    assert "EXCEEDED" in repr(status)
