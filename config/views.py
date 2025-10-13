from django.shortcuts import render


def server_error(request, template_name="500.html"):
    """Render the 500 error page with the request in the context."""
    return render(request, template_name, status=500)
