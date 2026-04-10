"""Tests for vault_sync.template module."""

from pathlib import Path

import pytest

from vault_sync.template import (
    RenderResult,
    collect_placeholders,
    render_template,
    render_template_file,
)


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------


def test_simple_placeholder_is_replaced():
    result = render_template("HOST={{ DB_HOST }}", {"DB_HOST": "localhost"})
    assert result.rendered == "HOST=localhost"


def test_multiple_placeholders_are_replaced():
    tmpl = "{{ HOST }}:{{ PORT }}"
    result = render_template(tmpl, {"HOST": "127.0.0.1", "PORT": "5432"})
    assert result.rendered == "127.0.0.1:5432"


def test_missing_placeholder_is_left_unchanged():
    result = render_template("{{ MISSING }}", {})
    assert result.rendered == "{{ MISSING }}"


def test_resolved_list_contains_replaced_keys():
    result = render_template("{{ A }} {{ B }}", {"A": "1", "B": "2"})
    assert set(result.resolved) == {"A", "B"}


def test_missing_list_contains_unresolved_keys():
    result = render_template("{{ A }} {{ B }}", {"A": "1"})
    assert result.missing == ["B"]


def test_ok_is_true_when_no_missing():
    result = render_template("{{ KEY }}", {"KEY": "val"})
    assert result.ok is True


def test_ok_is_false_when_missing_keys():
    result = render_template("{{ KEY }}", {})
    assert result.ok is False


def test_duplicate_placeholder_resolved_once():
    result = render_template("{{ A }} {{ A }}", {"A": "x"})
    assert result.resolved == ["A"]


def test_duplicate_missing_reported_once():
    result = render_template("{{ X }} {{ X }}", {})
    assert result.missing == ["X"]


def test_whitespace_inside_braces_is_ignored():
    result = render_template("{{  KEY  }}", {"KEY": "value"})
    assert result.rendered == "value"


# ---------------------------------------------------------------------------
# render_template_file
# ---------------------------------------------------------------------------


def test_render_template_file_reads_and_renders(tmp_path: Path):
    tmpl = tmp_path / "template.env"
    tmpl.write_text("DB={{ DB_URL }}", encoding="utf-8")
    result = render_template_file(tmpl, {"DB_URL": "postgres://localhost/db"})
    assert result.rendered == "DB=postgres://localhost/db"
    assert result.ok


def test_render_template_file_writes_output(tmp_path: Path):
    tmpl = tmp_path / "template.env"
    out = tmp_path / "output.env"
    tmpl.write_text("KEY={{ VAL }}", encoding="utf-8")
    render_template_file(tmpl, {"VAL": "hello"}, output_path=out)
    assert out.read_text(encoding="utf-8") == "KEY=hello"


def test_render_template_file_no_output_path_does_not_create_file(tmp_path: Path):
    tmpl = tmp_path / "template.env"
    tmpl.write_text("{{ X }}", encoding="utf-8")
    render_template_file(tmpl, {"X": "1"})
    assert not (tmp_path / "output.env").exists()


# ---------------------------------------------------------------------------
# collect_placeholders
# ---------------------------------------------------------------------------


def test_collect_placeholders_returns_keys():
    assert collect_placeholders("{{ A }} {{ B }}") == ["A", "B"]


def test_collect_placeholders_deduplicates():
    assert collect_placeholders("{{ A }} {{ A }} {{ B }}") == ["A", "B"]


def test_collect_placeholders_empty_template():
    assert collect_placeholders("no placeholders here") == []


# ---------------------------------------------------------------------------
# RenderResult repr
# ---------------------------------------------------------------------------


def test_render_result_repr():
    r = RenderResult(rendered="x", resolved=["A"], missing=[])
    assert "resolved=1" in repr(r)
    assert "missing=0" in repr(r)
    assert "ok=True" in repr(r)
