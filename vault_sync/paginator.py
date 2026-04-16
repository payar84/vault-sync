from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional


@dataclass
class PaginatorConfig:
    page_size: int = 50
    max_pages: Optional[int] = None

    def validate(self) -> None:
        if self.page_size <= 0:
            raise ValueError("page_size must be positive")
        if self.max_pages is not None and self.max_pages <= 0:
            raise ValueError("max_pages must be positive when set")


@dataclass
class Page:
    index: int
    items: List[str]

    @property
    def size(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"Page(index={self.index}, size={self.size})"


@dataclass
class PaginateResult:
    pages: List[Page] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        return sum(p.size for p in self.pages)

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    def __repr__(self) -> str:
        return f"PaginateResult(pages={self.total_pages}, items={self.total_items})"


def paginate(
    fetch: Callable[[int, int], List[str]],
    config: Optional[PaginatorConfig] = None,
) -> PaginateResult:
    if config is None:
        config = PaginatorConfig()
    config.validate()

    result = PaginateResult()
    page_index = 0

    while True:
        if config.max_pages is not None and page_index >= config.max_pages:
            break
        offset = page_index * config.page_size
        items = fetch(offset, config.page_size)
        if not items:
            break
        result.pages.append(Page(index=page_index, items=items))
        page_index += 1
        if len(items) < config.page_size:
            break

    return result


def iter_pages(result: PaginateResult) -> Iterator[Page]:
    yield from result.pages
