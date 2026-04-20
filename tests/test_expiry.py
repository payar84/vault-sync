"""Tests for vault_sync.expiry."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from vault_sync.expiry import ExpiryConfig, ExpiryReport, ExpiryStatus, check_expiry


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _ts(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


# --- ExpiryConfig validation ---

def test_config_rejects_zero_max_age():
    with pytest.raises(ValueError, match="max_age_days"):
        ExpiryConfig(max_age_days=0).validate()


def test_config_rejects_negative_max_age():
    with pytest.raises(ValueError, match="max_age_days"):
        ExpiryConfig(max_age_days=-1).validate()


def test_config_rejects_zero_warn_before():
    with pytest.raises(ValueError, match="warn_before_days"):
        ExpiryConfig(max_age_days=30, warn_before_days=0).validate()


def test_config_rejects_warn_at_or_above_max_age():
    with pytest.raises(ValueError, match="warn_before_days must be less than max_age_days"):
        ExpiryConfig(max_age_days=30, warn_before_days=30).validate()


def test_config_accepts_valid_values():
    cfg = ExpiryConfig(max_age_days=60, warn_before_days=10)
    cfg.validate()  # should not raise


# --- check_expiry logic ---

def test_current_secret_is_ok():
    records = {"secret/app": _ts(10)}
    report = check_expiry(records, config=ExpiryConfig(max_age_days=90, warn_before_days=14), now=NOW)
    assert len(report.statuses) == 1
    s = report.statuses[0]
    assert not s.expired
    assert not s.warning


def test_secret_in_warning_window():
    records = {"secret/app": _ts(80)}  # 90-14=76 days threshold
    report = check_expiry(records, config=ExpiryConfig(max_age_days=90, warn_before_days=14), now=NOW)
    s = report.statuses[0]
    assert not s.expired
    assert s.warning


def test_expired_secret_is_flagged():
    records = {"secret/app": _ts(100)}
    report = check_expiry(records, config=ExpiryConfig(max_age_days=90, warn_before_days=14), now=NOW)
    s = report.statuses[0]
    assert s.expired
    assert not s.warning


def test_report_ok_when_no_expired():
    records = {"a": _ts(5), "b": _ts(10)}
    report = check_expiry(records, config=ExpiryConfig(), now=NOW)
    assert report.ok


def test_report_not_ok_when_expired():
    records = {"a": _ts(5), "b": _ts(200)}
    report = check_expiry(records, config=ExpiryConfig(max_age_days=90, warn_before_days=14), now=NOW)
    assert not report.ok
    assert report.expired_count == 1


def test_warning_count_excludes_expired():
    records = {"a": _ts(200), "b": _ts(80)}
    report = check_expiry(records, config=ExpiryConfig(max_age_days=90, warn_before_days=14), now=NOW)
    assert report.expired_count == 1
    assert report.warning_count == 1


def test_empty_records_returns_empty_report():
    report = check_expiry({}, now=NOW)
    assert report.ok
    assert len(report.statuses) == 0


def test_status_repr_expired():
    s = ExpiryStatus("p", NOW, 100.0, expired=True, warning=False, message="x")
    assert "EXPIRED" in repr(s)


def test_status_repr_warn():
    s = ExpiryStatus("p", NOW, 80.0, expired=False, warning=True, message="x")
    assert "WARN" in repr(s)


def test_status_repr_ok():
    s = ExpiryStatus("p", NOW, 5.0, expired=False, warning=False, message="x")
    assert "OK" in repr(s)


def test_report_repr_contains_counts():
    report = ExpiryReport()
    assert "expired=0" in repr(report)
