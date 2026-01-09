import re

import pytest
from django.urls import URLPattern, URLResolver, get_resolver

_PARAM_RE = re.compile(r"<(?:(?P<converter>[^:]+):)?(?P<param>[^>]+)>")
_REGEX_NAMED_GROUP_RE = re.compile(r"\(\?P<[^>]+>([^)]+)\)")

_CONVERTER_SAMPLES = {
    "IntConverter": "1",
    "SlugConverter": "test-slug",
    "UUIDConverter": "00000000-0000-0000-0000-000000000000",
    "PathConverter": "test/path",
    "StringConverter": "test",
}

_SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


@pytest.fixture
def auth_client(db, client, django_user_model):
    user = django_user_model.objects.create_superuser(
        username="qa_superuser",
        email="qa_superuser@example.com",
        password="testpass",
    )
    client.force_login(user)
    return client


def _sample_from_regex(pattern):
    if pattern in {r"\d+", r"[0-9]+", r"\d{1,}"}:
        return "1"
    if "uuid" in pattern.lower():
        return "00000000-0000-0000-0000-000000000000"
    if pattern in {r".*", r".+", r"[^/]+", r"[^/]*"}:
        return "test"
    return "test"


def _route_for_pattern(pattern_obj):
    if hasattr(pattern_obj, "_route"):
        return pattern_obj._route
    if hasattr(pattern_obj, "pattern"):
        return pattern_obj.pattern
    return str(pattern_obj)


def _fill_route(route, converters):
    def _replace(match):
        param = match.group("param")
        converter = converters.get(param)
        if converter is None:
            return "test"
        return _CONVERTER_SAMPLES.get(converter.__class__.__name__, "test")

    return _PARAM_RE.sub(_replace, route)


def _regex_to_path(regex):
    cleaned = regex.lstrip("^").rstrip("$")

    def _replace(match):
        return _sample_from_regex(match.group(1))

    cleaned = _REGEX_NAMED_GROUP_RE.sub(_replace, cleaned)
    cleaned = re.sub(r"\([^)]*\)", "test", cleaned)
    cleaned = cleaned.replace(r"\A", "").replace(r"\Z", "")
    cleaned = cleaned.replace(r"\/", "/").replace(r"\.", ".")
    cleaned = cleaned.replace("\\", "")
    cleaned = cleaned.replace("?", "").replace("+", "").replace("*", "")
    return cleaned


def _join_paths(prefix, route):
    if not prefix:
        return route
    if not route:
        return prefix
    if prefix.endswith("/") and route.startswith("/"):
        return f"{prefix}{route.lstrip('/')}"
    if not prefix.endswith("/") and not route.startswith("/"):
        return f"{prefix}/{route}"
    return f"{prefix}{route}"


def _iter_urlpatterns(patterns, prefix=""):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            yield prefix, pattern
        elif isinstance(pattern, URLResolver):
            nested_route = _route_for_pattern(pattern.pattern)
            nested_prefix = prefix
            if hasattr(pattern.pattern, "_route"):
                nested_prefix = _join_paths(prefix, nested_route)
            else:
                nested_prefix = _join_paths(prefix, _regex_to_path(nested_route))
            yield from _iter_urlpatterns(pattern.url_patterns, nested_prefix)


def _methods_for_pattern(pattern):
    methods = {"GET"}
    callback = pattern.callback

    actions = getattr(callback, "actions", None)
    if actions:
        methods.update(method.upper() for method in actions.keys())

    view_class = getattr(callback, "view_class", None) or getattr(callback, "cls", None)
    if view_class is not None:
        http_method_names = getattr(view_class, "http_method_names", None)
        if http_method_names:
            methods.update(method.upper() for method in http_method_names)

    allowed_methods = getattr(callback, "allowed_methods", None)
    if allowed_methods:
        methods.update(method.upper() for method in allowed_methods)

    return sorted(method for method in methods if method in _SUPPORTED_METHODS)


def collect_url_tests():
    targets = {}
    resolver = get_resolver()
    for prefix, pattern in _iter_urlpatterns(resolver.url_patterns):
        if hasattr(pattern.pattern, "_route"):
            route = _fill_route(pattern.pattern._route, pattern.pattern.converters)
        else:
            route = _regex_to_path(_route_for_pattern(pattern.pattern))

        full_path = _join_paths(prefix, route)
        if not full_path:
            full_path = "/"
        elif not full_path.startswith("/"):
            full_path = f"/{full_path}"

        name = pattern.name or pattern.lookup_str
        for method in _methods_for_pattern(pattern):
            targets.setdefault((method, full_path), name)

    return sorted(
        [(method, path, name) for (method, path), name in targets.items()],
        key=lambda item: (item[1], item[0]),
    )


@pytest.mark.parametrize("method,path,name", collect_url_tests())
def test_urls_no_500(auth_client, method, path, name):
    if method == "GET":
        response = auth_client.get(path)
    elif method == "POST":
        response = auth_client.post(path, data={})
    elif method in {"PUT", "PATCH"}:
        response = getattr(auth_client, method.lower())(
            path, data="{}", content_type="application/json"
        )
    elif method == "DELETE":
        response = auth_client.delete(path, data="{}", content_type="application/json")
    elif method == "HEAD":
        response = auth_client.head(path)
    elif method == "OPTIONS":
        response = auth_client.options(path)
    else:
        response = auth_client.generic(method, path)

    assert response.status_code < 500, (
        f"{method} {path} ({name}) devolvio {response.status_code}"
    )
