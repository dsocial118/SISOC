from django.http import HttpResponseServerError
from django.template import loader
from drf_spectacular.views import SpectacularAPIView


def server_error(_request, template_name="500.html"):
    """Return a static 500 error response without invoking context processors."""
    template = loader.get_template(template_name)
    return HttpResponseServerError(template.render())


class VatSpectacularAPIView(SpectacularAPIView):
    """Expone un schema OpenAPI filtrado solo a endpoints `/api/vat/`."""

    VAT_PATH_PREFIX = "/api/vat/"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        schema = getattr(response, "data", None)
        if not isinstance(schema, dict):
            return response

        schema = dict(schema)

        paths = schema.get("paths") or {}
        schema["paths"] = {
            path: value
            for path, value in paths.items()
            if str(path).startswith(self.VAT_PATH_PREFIX)
        }

        info = schema.get("info")
        if isinstance(info, dict):
            info = dict(info)
            title = info.get("title") or "API"
            info["title"] = f"{title} - VAT"
            schema["info"] = info

        response.data = schema
        return response
