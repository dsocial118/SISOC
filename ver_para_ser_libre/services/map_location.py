"""Resolucion segura de enlaces de ubicacion para jornadas VPSL."""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote_plus, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.core.exceptions import ValidationError


SHORT_MAP_HOST = "maps.app.goo.gl"
CANONICAL_MAP_HOST = "www.google.com"
SAFE_REDIRECT_HOSTS = frozenset(
    {SHORT_MAP_HOST, CANONICAL_MAP_HOST, "maps.google.com", "google.com"}
)
SHORT_PATH_PATTERN = re.compile(r"^/[A-Za-z0-9_-]+/?$")
CANONICAL_SEARCH_PATHS = frozenset({"/maps/search", "/maps/search/"})
CANONICAL_STREET_VIEW_PATHS = frozenset({"/maps/@", "/maps/@/"})
PLAIN_COORDINATES_PATTERN = re.compile(
    r"^(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)$"
)
COORDINATES_PATTERN = re.compile(
    r"(?<!\d)(-?\d{1,2}(?:\.\d+)?)[,+%20 ]+(-?\d{1,3}(?:\.\d+)?)(?!\d)"
)
AT_COORDINATES_PATTERN = re.compile(r"@(-?\d{1,2}(?:\.\d+)?),(-?\d{1,3}(?:\.\d+)?)")


@dataclass(frozen=True)
class MapLocation:
    original_url: str
    resolved_url: str
    latitude: Decimal | None
    longitude: Decimal | None
    address: str

    @property
    def query(self):
        if self.latitude is not None and self.longitude is not None:
            return f"{self.latitude},{self.longitude}"
        return self.address


def _parse_safe_google_url(value, *, allowed_hosts):
    value = (value or "").strip()
    if len(value) > 500:
        raise ValidationError("El enlace de Google Maps es demasiado largo.")
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError as exc:
        raise ValidationError("El enlace de Google Maps no es valido.") from exc
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or hostname not in allowed_hosts
        or parsed.username
        or parsed.password
        or port not in (None, 443)
    ):
        raise ValidationError(
            "Ingrese un enlace HTTPS oficial de Google Maps en un formato permitido."
        )
    return parsed


def _validate_resolved_google_maps_url(value):
    """Valida destinos oficiales usados internamente al expandir enlaces cortos."""
    parsed = _parse_safe_google_url(value, allowed_hosts=SAFE_REDIRECT_HOSTS)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if hostname == SHORT_MAP_HOST:
        if not SHORT_PATH_PATTERN.fullmatch(parsed.path):
            raise ValidationError("El enlace corto de Google Maps no es valido.")
    elif parsed.path != "/maps" and not parsed.path.startswith("/maps/"):
        raise ValidationError("El destino no corresponde a Google Maps.")
    return parsed.geturl()


def validate_google_maps_url(value):
    """Normaliza coordenadas y acepta formatos oficiales con ubicacion precisa."""
    value = (value or "").strip()
    plain_coordinates = PLAIN_COORDINATES_PATTERN.fullmatch(value)
    if plain_coordinates:
        latitude, longitude = _valid_coordinates(*plain_coordinates.groups())
        if latitude is None:
            raise ValidationError("Las coordenadas están fuera del rango permitido.")
        return (
            "https://www.google.com/maps/search/?api=1&query="
            f"{latitude}%2C{longitude}"
        )

    parsed = _parse_safe_google_url(
        value,
        allowed_hosts={SHORT_MAP_HOST, CANONICAL_MAP_HOST},
    )
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if hostname == SHORT_MAP_HOST:
        if not SHORT_PATH_PATTERN.fullmatch(parsed.path):
            raise ValidationError(
                "Use un enlace con formato https://maps.app.goo.gl/identificador."
            )
        return parsed.geturl()

    query = parse_qs(parsed.query)
    if parsed.path in CANONICAL_SEARCH_PATHS:
        coordinates = (query.get("query") or [""])[0].strip()
        coordinate_match = COORDINATES_PATTERN.fullmatch(coordinates)
        latitude, longitude = (
            _valid_coordinates(*coordinate_match.groups())
            if coordinate_match
            else (None, None)
        )
        if query.get("api") != ["1"] or latitude is None:
            raise ValidationError(
                "Use https://www.google.com/maps/search/?api=1&query=latitud,longitud."
            )
        return (
            "https://www.google.com/maps/search/?api=1&query="
            f"{latitude}%2C{longitude}"
        )

    if parsed.path in CANONICAL_STREET_VIEW_PATHS:
        viewpoint = (query.get("viewpoint") or [""])[0].strip()
        viewpoint_match = COORDINATES_PATTERN.fullmatch(viewpoint)
        latitude, longitude = (
            _valid_coordinates(*viewpoint_match.groups())
            if viewpoint_match
            else (None, None)
        )
        if (
            query.get("api") != ["1"]
            or query.get("map_action") != ["pano"]
            or latitude is None
        ):
            raise ValidationError(
                "Use una URL oficial de Street View con api=1, "
                "map_action=pano y viewpoint=latitud,longitud."
            )
        return (
            "https://www.google.com/maps/@?api=1&map_action=pano&viewpoint="
            f"{latitude}%2C{longitude}"
        )

    raise ValidationError(
        "Use un enlace corto, coordenadas o una URL oficial de Street View."
    )


class _SafeGoogleRedirectHandler(HTTPRedirectHandler):
    # Firma definida por urllib; no es una interfaz propia del modulo.
    # pylint: disable=too-many-arguments
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url = _validate_resolved_google_maps_url(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, safe_url)


def _resolve_short_url(url, timeout=5):
    if urlparse(url).hostname != SHORT_MAP_HOST:
        return url
    request = Request(
        url,
        method="HEAD",
        headers={"User-Agent": "SISOC/1.0 location resolver"},
    )
    try:
        with build_opener(_SafeGoogleRedirectHandler()).open(
            request, timeout=timeout
        ) as response:
            return _validate_resolved_google_maps_url(response.geturl())
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ValidationError(
            "No se pudo resolver el enlace corto de Google Maps. Intente nuevamente."
        ) from exc


def _valid_coordinates(latitude, longitude):
    try:
        latitude = Decimal(latitude)
        longitude = Decimal(longitude)
    except (InvalidOperation, TypeError, ValueError):
        return None, None
    if not Decimal("-90") <= latitude <= Decimal("90"):
        return None, None
    if not Decimal("-180") <= longitude <= Decimal("180"):
        return None, None
    return latitude, longitude


def _extract_coordinates(url):
    decoded = unquote_plus(url)
    for pattern in (AT_COORDINATES_PATTERN, COORDINATES_PATTERN):
        match = pattern.search(decoded)
        if match:
            latitude, longitude = _valid_coordinates(*match.groups())
            if latitude is not None:
                return latitude, longitude
    return None, None


def _extract_address(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("query", "q", "destination"):
        candidate = (query.get(key) or [""])[0].strip()
        if candidate and not COORDINATES_PATTERN.fullmatch(candidate):
            return candidate[:255]
    path = unquote_plus(parsed.path)
    match = re.search(r"/maps/(?:place|search)/([^/@]+)", path)
    if match:
        candidate = match.group(1).strip()
        if candidate and not COORDINATES_PATTERN.fullmatch(candidate):
            return candidate[:255]
    return ""


def resolve_google_maps_location(value, *, timeout=5):
    original_url = validate_google_maps_url(value)
    resolved_url = _resolve_short_url(original_url, timeout=timeout)
    latitude, longitude = _extract_coordinates(resolved_url)
    address = _extract_address(resolved_url)
    if latitude is None and not address:
        raise ValidationError(
            "El enlace no contiene una ubicacion reconocible. Comparta un pin o una direccion de Google Maps."
        )
    return MapLocation(
        original_url=original_url,
        resolved_url=resolved_url,
        latitude=latitude,
        longitude=longitude,
        address=address,
    )
