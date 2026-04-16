import pytest
from vault_sync.paginator import (
    PaginatorConfig,
    Page,
    PaginateResult,
    paginate,
    iter_pages,
)


def _make_fetch(items):
    def fetch(offset, limit):
        return items[offset : offset + limit]
    return fetch


def test_config_rejects_zero_page_size():
    with pytest.raises(ValueError, match="page_size"):
        PaginatorConfig(page_size=0).validate()


def test_config_rejects_negative_page_size():
    with pytest.raises(ValueError):
        PaginatorConfig(page_size=-1).validate()


def test_config_rejects_zero_max_pages():
    with pytest.raises(ValueError, match="max_pages"):
        PaginatorConfig(page_size=10, max_pages=0).validate()


def test_config_accepts_valid_values():
    cfg = PaginatorConfig(page_size=20, max_pages=5)
    cfg.validate()  # no exception


def test_paginate_empty_source_returns_no_pages():
    result = paginate(_make_fetch([]), PaginatorConfig(page_size=10))
    assert result.total_pages == 0
    assert result.total_items == 0


def test_paginate_single_page():
    keys = ["a", "b", "c"]
    result = paginate(_make_fetch(keys), PaginatorConfig(page_size=10))
    assert result.total_pages == 1
    assert result.total_items == 3


def test_paginate_multiple_pages():
    keys = list(range(25))
    result = paginate(_make_fetch(keys), PaginatorConfig(page_size=10))
    assert result.total_pages == 3
    assert result.total_items == 25


def test_paginate_respects_max_pages():
    keys = list(range(100))
    result = paginate(_make_fetch(keys), PaginatorConfig(page_size=10, max_pages=2))
    assert result.total_pages == 2
    assert result.total_items == 20


def test_page_index_is_sequential():
    keys = list(range(30))
    result = paginate(_make_fetch(keys), PaginatorConfig(page_size=10))
    for i, page in enumerate(result.pages):
        assert page.index == i


def test_page_repr_contains_index_and_size():
    p = Page(index=2, items=["x", "y"])
    assert "index=2" in repr(p)
    assert "size=2" in repr(p)


def test_paginate_result_repr():
    keys = list(range(15))
    result = paginate(_make_fetch(keys), PaginatorConfig(page_size=10))
    r = repr(result)
    assert "pages=2" in r
    assert "items=15" in r


def test_iter_pages_yields_all_pages():
    keys = list(range(20))
    result = paginate(_make_fetch(keys), PaginatorConfig(page_size=10))
    pages = list(iter_pages(result))
    assert len(pages) == 2
