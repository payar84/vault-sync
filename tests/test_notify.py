import sys
import pytest
from unittest.mock import patch, MagicMock

from vault_sync.notify import NotifyConfig, NotifyResult, run_notify


@pytest.fixture
def config():
    return NotifyConfig(command="echo", args=["hello"], timeout=5)


def test_notify_config_rejects_empty_command():
    cfg = NotifyConfig(command="  ")
    with pytest.raises(ValueError, match="must not be empty"):
        cfg.validate()


def test_notify_config_rejects_zero_timeout():
    cfg = NotifyConfig(command="echo", timeout=0)
    with pytest.raises(ValueError, match="must be positive"):
        cfg.validate()


def test_notify_config_rejects_negative_timeout():
    cfg = NotifyConfig(command="echo", timeout=-1)
    with pytest.raises(ValueError, match="must be positive"):
        cfg.validate()


def test_notify_config_valid_passes():
    cfg = NotifyConfig(command="echo", timeout=10)
    cfg.validate()  # should not raise


def test_notify_result_ok_factory():
    result = NotifyResult.ok(stdout="done")
    assert result.success is True
    assert result.returncode == 0
    assert result.stdout == "done"


def test_notify_result_repr_ok():
    result = NotifyResult.ok()
    assert "ok" in repr(result)
    assert "rc=0" in repr(result)


def test_notify_result_repr_failed():
    result = NotifyResult(success=False, returncode=1, stdout="", stderr="err")
    assert "failed" in repr(result)


def test_run_notify_success(config):
    mock_result = MagicMock(returncode=0, stdout="hello\n", stderr="")
    with patch("vault_sync.notify.subprocess.run", return_value=mock_result) as mock_run:
        result = run_notify(config)
        assert result.success is True
        assert result.returncode == 0
        mock_run.assert_called_once()


def test_run_notify_failure(config):
    mock_result = MagicMock(returncode=1, stdout="", stderr="error")
    with patch("vault_sync.notify.subprocess.run", return_value=mock_result):
        result = run_notify(config)
        assert result.success is False
        assert result.returncode == 1


def test_run_notify_timeout(config):
    import subprocess
    with patch("vault_sync.notify.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="echo", timeout=5)):
        result = run_notify(config)
        assert result.success is False
        assert "timed out" in result.error


def test_run_notify_file_not_found():
    cfg = NotifyConfig(command="nonexistent_cmd_xyz", timeout=5)
    with patch("vault_sync.notify.subprocess.run", side_effect=FileNotFoundError):
        result = run_notify(cfg)
        assert result.success is False
        assert "not found" in result.error


def test_run_notify_passes_env_vars(config):
    mock_result = MagicMock(returncode=0, stdout="", stderr="")
    with patch("vault_sync.notify.subprocess.run", return_value=mock_result) as mock_run:
        run_notify(config, env_vars={"VAULT_SYNC_STATUS": "ok"})
        call_kwargs = mock_run.call_args.kwargs
        assert "VAULT_SYNC_STATUS" in call_kwargs["env"]
        assert call_kwargs["env"]["VAULT_SYNC_STATUS"] == "ok"
