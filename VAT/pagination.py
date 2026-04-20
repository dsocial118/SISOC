from rest_framework.pagination import PageNumberPagination


class VATPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_page_size(self, request):
        raw_page_size = request.query_params.get(self.page_size_query_param)
        if raw_page_size in (None, ""):
            return self.page_size

        try:
            page_size = int(raw_page_size)
        except (TypeError, ValueError):
            return self.page_size

        if page_size <= 0:
            return self.page_size

        if self.max_page_size and page_size > self.max_page_size:
            return self.page_size

        return page_size
