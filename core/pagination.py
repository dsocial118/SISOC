"""Helpers de paginacion para listados grandes."""

from __future__ import annotations


class NoCountPage:
    """Representa una pagina sin requerir un COUNT(*) exacto."""

    def __init__(self, object_list, number, paginator, has_next_page):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator
        self._has_next_page = has_next_page

    def has_next(self):
        return self._has_next_page

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1


class NoCountPaginator:
    """Paginar por ventana evita el COUNT(*) sobre tablas grandes."""

    count = None
    num_pages = None
    page_range = ()

    def __init__(self, object_list, per_page):
        self.object_list = object_list
        self.per_page = per_page

    @staticmethod
    def _normalize_number(number):
        try:
            page_number = int(number)
        except (TypeError, ValueError):
            return 1
        return page_number if page_number > 0 else 1

    def _fetch_page(self, number):
        slice_start = (number - 1) * self.per_page
        slice_end = slice_start + self.per_page + 1
        items = list(self.object_list[slice_start:slice_end])
        has_next_page = len(items) > self.per_page
        if has_next_page:
            items = items[:-1]
        return items, has_next_page

    def get_page(self, number):
        page_number = self._normalize_number(number)
        items, has_next_page = self._fetch_page(page_number)

        while not items and page_number > 1:
            page_number -= 1
            items, has_next_page = self._fetch_page(page_number)

        return NoCountPage(items, page_number, self, has_next_page)


def build_no_count_page_range(page_obj, window=2):
    """Construye un rango corto alrededor de la pagina actual."""

    start = max(1, page_obj.number - window)
    page_range = []

    if start > 1:
        page_range.append(1)
        if start > 2:
            page_range.append("...")

    page_range.extend(range(start, page_obj.number + 1))

    if page_obj.has_next():
        page_range.append(page_obj.number + 1)
        page_range.append("...")

    return page_range
