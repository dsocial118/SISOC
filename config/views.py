from django.http import HttpResponseServerError
from django.template import loader


def server_error(_request, template_name="500.html"):
    """Return a static 500 error response without invoking context processors."""
    template = loader.get_template(template_name)
    return HttpResponseServerError(template.render())
