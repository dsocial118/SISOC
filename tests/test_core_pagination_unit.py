"""Tests unitarios para core.pagination."""

from core.pagination import NoCountPaginator, build_no_count_page_range


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
