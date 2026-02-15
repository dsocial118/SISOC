import re

import pytest
from django.urls import URLPattern, URLResolver, get_resolver

pytestmark = pytest.mark.smoke

_REGEX_NAMED_GROUP_RE = re.compile(r"\(\?P<[^>]+>")
_ALLOWED_VIEWSET_ACTIONS = {"list", "retrieve"}
_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"}
_SKIP_NAMES = {"autocomplete", "api-root", "auditlog_logentry_add"}
_SKIP_PATHS = {
    "/admin/autocomplete/",
    "/admin/auditlog/logentry/add/",
    "/api/centrodefamilia/",
    "/login/",
}
_SKIP_PATH_SUBSTRINGS = (
    "/__debug__/",
    "/ajax/",
    "/buscar-",
    "/informecabal/preview",
    "/informecabal/process",
    "/informecabal/reprocess",
)


def _is_dynamic_regex(regex: str) -> bool:
    return bool(_REGEX_NAMED_GROUP_RE.search(regex))


def _regex_to_path(regex: str) -> str:
    cleaned = regex.lstrip("^").rstrip("$")
    cleaned = cleaned.replace(r"\A", "").replace(r"\Z", "")
    cleaned = cleaned.replace(r"\/", "/").replace(r"\.", ".")
    cleaned = cleaned.replace("\\", "")
    return cleaned


def _join_paths(prefix: str, route: str) -> str:
    if not prefix:
        return route
    if not route:
        return prefix
    if prefix.endswith("/") and route.startswith("/"):
        return f"{prefix}{route.lstrip('/')}"
    if not prefix.endswith("/") and not route.startswith("/"):
        return f"{prefix}/{route}"
    return f"{prefix}{route}"


def _iter_urlpatterns(patterns, prefix: str = "", has_params: bool = False):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            yield prefix, has_params, pattern
        elif isinstance(pattern, URLResolver):
            regex = pattern.pattern.regex.pattern
            nested_prefix = _join_paths(prefix, _regex_to_path(regex))
            nested_has_params = has_params or _is_dynamic_regex(regex)
            yield from _iter_urlpatterns(
                pattern.url_patterns, nested_prefix, nested_has_params
            )


def _iter_wrapped_callbacks(callback):
    seen = set()
    current = callback
    while current and id(current) not in seen:
        yield current
        seen.add(id(current))
        current = getattr(current, "__wrapped__", None)


def _callback_allows_get(callback) -> bool:
    callback_methods = getattr(callback, "http_method_names", None)
    if callback_methods and "get" not in callback_methods:
        return False

    actions = getattr(callback, "actions", None)
    if actions is not None:
        action_name = actions.get("get")
        return action_name in _ALLOWED_VIEWSET_ACTIONS

    view_class = getattr(callback, "view_class", None) or getattr(callback, "cls", None)
    if view_class is not None:
        http_method_names = getattr(view_class, "http_method_names", None)
        if http_method_names and "get" not in http_method_names:
            return False
        if not callable(getattr(view_class, "get", None)):
            return False

    allowed_methods = getattr(callback, "allowed_methods", None)
    required_methods = _get_required_methods(callback)
    return not (
        (allowed_methods and "GET" not in allowed_methods)
        or (required_methods and "GET" not in required_methods)
    )


def _get_required_methods(callback):
    closure = callback.__closure__ or ()
    for cell in closure:
        try:
            value = cell.cell_contents
        except ValueError:
            continue
        if isinstance(value, (list, tuple, set, frozenset)) and value:
            if all(isinstance(method, str) for method in value):
                normalized = {method.upper() for method in value}
                if normalized <= _HTTP_METHODS:
                    return normalized
    return None


def _allows_get(pattern) -> bool:
    for callback in _iter_wrapped_callbacks(pattern.callback):
        if not _callback_allows_get(callback):
            return False
    return True


def _should_skip(path: str, name: str) -> bool:
    if name in _SKIP_NAMES:
        return True
    if path in _SKIP_PATHS:
        return True
    return any(fragment in path for fragment in _SKIP_PATH_SUBSTRINGS)


def collect_url_tests():
    targets = {}
    resolver = get_resolver()
    for prefix, has_params, pattern in _iter_urlpatterns(resolver.url_patterns):
        if has_params or not _allows_get(pattern):
            continue

        regex = pattern.pattern.regex.pattern
        if _is_dynamic_regex(regex):
            continue
        route = _regex_to_path(regex)

        full_path = _join_paths(prefix, route)
        if not full_path:
            full_path = "/"
        elif not full_path.startswith("/"):
            full_path = f"/{full_path}"

        name = pattern.name or pattern.lookup_str
        if _should_skip(full_path, name):
            continue
        targets.setdefault(full_path, name)

    return sorted(list(targets.items()), key=lambda item: item[0])


@pytest.mark.parametrize("path,name", collect_url_tests())
def test_urls_no_500(request, path, name):
    if path.startswith("/api/"):
        client = request.getfixturevalue("api_client")
    else:
        client = request.getfixturevalue("auth_client")
    response = client.get(path)

    assert (
        response.status_code < 500
    ), f"GET {path} ({name}) devolvio {response.status_code}"
