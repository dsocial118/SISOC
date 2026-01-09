import re

import pytest
from django.urls import URLPattern, URLResolver, get_resolver

pytestmark = pytest.mark.smoke

_DYNAMIC_ROUTE_RE = re.compile(r"<[^>]+>")
_REGEX_NAMED_GROUP_RE = re.compile(r"\(\?P<[^>]+>")


def _is_dynamic_route(route: str) -> bool:
    return bool(_DYNAMIC_ROUTE_RE.search(route))


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
            nested_prefix = prefix
            nested_has_params = has_params
            if hasattr(pattern.pattern, "_route"):
                route = pattern.pattern._route
                nested_prefix = _join_paths(prefix, route)
                nested_has_params = has_params or _is_dynamic_route(route)
            else:
                regex = pattern.pattern.regex.pattern
                nested_prefix = _join_paths(prefix, _regex_to_path(regex))
                nested_has_params = has_params or _is_dynamic_regex(regex)
            yield from _iter_urlpatterns(
                pattern.url_patterns, nested_prefix, nested_has_params
            )


def _allows_get(pattern) -> bool:
    callback = pattern.callback

    actions = getattr(callback, "actions", None)
    if actions:
        return "get" in actions

    view_class = getattr(callback, "view_class", None) or getattr(callback, "cls", None)
    if view_class is not None:
        http_method_names = getattr(view_class, "http_method_names", None)
        if http_method_names:
            return "get" in http_method_names

    allowed_methods = getattr(callback, "allowed_methods", None)
    if allowed_methods:
        return "GET" in allowed_methods

    return True


def collect_url_tests():
    targets = {}
    resolver = get_resolver()
    for prefix, has_params, pattern in _iter_urlpatterns(resolver.url_patterns):
        if has_params or not _allows_get(pattern):
            continue

        if hasattr(pattern.pattern, "_route"):
            route = pattern.pattern._route
            if _is_dynamic_route(route):
                continue
        else:
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
        targets.setdefault(full_path, name)

    return sorted(
        [(path, name) for path, name in targets.items()],
        key=lambda item: item[0],
    )


@pytest.mark.parametrize("path,name", collect_url_tests())
def test_urls_no_500(request, path, name):
    if path.startswith("/api/"):
        client = request.getfixturevalue("api_client")
    else:
        client = request.getfixturevalue("auth_client")
    response = client.get(path)

    assert response.status_code < 400, (
        f"GET {path} ({name}) devolvio {response.status_code}"
    )
