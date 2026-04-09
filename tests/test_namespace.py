"""Tests for vault_sync.namespace module."""

import pytest
from vault_sync.namespace import Namespace, parse_namespaces, apply_namespace


def test_format_key_with_prefix():
    ns = Namespace(path="secret/app", prefix="APP")
    assert ns.format_key("db_password") == "APP_DB_PASSWORD"


def test_format_key_without_prefix():
    ns = Namespace(path="secret/app")
    assert ns.format_key("db_password") == "DB_PASSWORD"


def test_format_key_uppercases_key():
    ns = Namespace(path="secret/app", prefix="svc")
    assert ns.format_key("api_key") == "SVC_API_KEY"


def test_prefix_is_uppercased_on_init():
    ns = Namespace(path="secret/app", prefix="myapp")
    assert ns.prefix == "MYAPP"


def test_path_strips_slashes():
    ns = Namespace(path="/secret/app/")
    assert ns.path == "secret/app"


def test_matches_path_true():
    ns = Namespace(path="secret/app")
    assert ns.matches_path("/secret/app/") is True


def test_matches_path_false():
    ns = Namespace(path="secret/app")
    assert ns.matches_path("secret/other") is False


def test_parse_namespaces_basic():
    raw = [{"path": "secret/svc", "prefix": "SVC"}]
    result = parse_namespaces(raw)
    assert len(result) == 1
    assert result[0].path == "secret/svc"
    assert result[0].prefix == "SVC"


def test_parse_namespaces_missing_path_raises():
    with pytest.raises(ValueError, match="missing 'path'"):
        parse_namespaces([{"prefix": "SVC"}])


def test_apply_namespace_transforms_keys():
    ns = Namespace(path="secret/db", prefix="DB")
    secrets = {"host": "localhost", "port": "5432"}
    result = apply_namespace(secrets, ns)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_apply_namespace_no_prefix():
    ns = Namespace(path="secret/db")
    secrets = {"host": "localhost"}
    result = apply_namespace(secrets, ns)
    assert result == {"HOST": "localhost"}
