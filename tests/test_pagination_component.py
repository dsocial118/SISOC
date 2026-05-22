"""Tests de regresion para el componente compartido de paginacion."""

from types import SimpleNamespace

from django.template.loader import render_to_string


class _ExplodingPageRange:
    def __iter__(self):
        for number in range(1, 100_001):
            if number > 20:
                raise AssertionError("pagination.html iterated the full page_range")
            yield number


class _LargePaginator:
    count = 100_000
    num_pages = 100_000
    page_range = _ExplodingPageRange()


class _Page:
    number = 50_000
    paginator = _LargePaginator()

    def has_previous(self):
        return True

    def has_next(self):
        return True

    def previous_page_number(self):
        return self.number - 1

    def next_page_number(self):
        return self.number + 1


def test_pagination_component_does_not_iterate_full_paginator_page_range():
    html = render_to_string(
        "components/pagination.html",
        {
            "is_paginated": True,
            "page_obj": _Page(),
            "request": SimpleNamespace(GET={}),
        },
    )

    assert "page=1" in html
    assert "page=50000" in html
    assert "page=100000" in html
