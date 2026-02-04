from django.shortcuts import redirect, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme


def safe_redirect(request, default, next_param="next", allowed_hosts=None, target=None):
    """Safely redirect to a user-provided URL, falling back to a safe default.

    This helper prevents open redirect vulnerabilities by validating the target
    against allowed hosts (local by default). Use it whenever redirecting based
    on request data like `next`, `HTTP_REFERER`, or the current path.
    """

    if target is None:
        target = request.GET.get(next_param) or request.POST.get(next_param)

    if not target:
        return redirect(resolve_url(default))

    allowed = {request.get_host()}
    if allowed_hosts:
        allowed.update(allowed_hosts)

    if url_has_allowed_host_and_scheme(
        target,
        allowed_hosts=allowed,
        require_https=request.is_secure(),
    ):
        return redirect(target)

    # Only local URLs (or explicit allowlist) are permitted.
    return redirect(resolve_url(default))
