"""Tests unitarios para core.pagination."""

from types import SimpleNamespace

from core.pagination import (
    NoCountPaginator,
    build_compact_page_range,
    build_no_count_page_range,
)


class _ExplodingPageRange:
    def __iter__(self):
        raise AssertionError("build_compact_page_range iterated paginator.page_range")


def _page(number, num_pages):
    return SimpleNamespace(
        number=number,
        paginator=SimpleNamespace(
            num_pages=num_pages,
            page_range=_ExplodingPageRange(),
        ),
    )


def test_no_count_paginator_falls_back_to_last_available_page():
    paginator = NoCountPaginator([1, 2, 3, 4, 5], 2)

    page_obj = paginator.get_page(99)

    assert page_obj.number == 3
    assert page_obj.object_list == [5]
    assert page_obj.has_previous() is True
    assert page_obj.has_next() is False


def test_build_no_count_page_range_keeps_short_window():
    paginator = NoCountPaginator([1, 2, 3, 4, 5], 2)
    page_obj = paginator.get_page(2)

    assert build_no_count_page_range(page_obj) == [1, 2, 3, "..."]


def test_build_compact_page_range_handles_single_page():
    assert build_compact_page_range(_page(1, 1)) == [1]


def test_build_compact_page_range_keeps_window_without_iterating_page_range():
    page_obj = _page(50, 100)

    assert build_compact_page_range(page_obj, window=2) == [
        1,
        "...",
        48,
        49,
        50,
        51,
        52,
        "...",
        100,
    ]


def test_build_compact_page_range_handles_edges_without_duplicate_boundaries():
    assert build_compact_page_range(_page(2, 10), window=2) == [
        1,
        2,
        3,
        4,
        "...",
        10,
    ]
    assert build_compact_page_range(_page(9, 10), window=2) == [
        1,
        "...",
        7,
        8,
        9,
        10,
    ]


def test_build_compact_page_range_returns_empty_for_invalid_num_pages():
    assert build_compact_page_range(_page(1, "invalid")) == []
    assert build_compact_page_range(_page(1, 0)) == []


def test_build_compact_page_range_falls_back_for_no_count_paginator():
    paginator = NoCountPaginator([1, 2, 3, 4, 5], 2)
    page_obj = paginator.get_page(2)

    assert build_compact_page_range(page_obj) == [1, 2, 3, "..."]
