from django.core.cache import cache


def _build_footer_version_label(current_version: str) -> str:
    if not current_version:
        return "Versiones"

    parts = str(current_version).split(".")
    if len(parts) != 3:
        return "Versiones"

    day, month, year = parts
    try:
        return f"v{int(day):02d}.{int(month):02d}.{int(year[-2:]):02d}"
    except ValueError:
        return "Versiones"


def footer_version(request):
    del request

    cache_key = "footer_version_label"
    cached_label = cache.get(cache_key)
    if cached_label is not None:
        return {"footer_version_label": cached_label}

    from core.views import (
        get_current_version,
    )  # pylint: disable=import-outside-toplevel

    label = _build_footer_version_label(get_current_version())
    cache.set(cache_key, label, 300)
    return {"footer_version_label": label}


def boton_volver(request):
    """Defaults del boton "Volver" unificado (issue #2460).

    El componente se renderiza desde ``includes/main.html`` en todas las
    pantallas, asi que sus variables tienen que existir siempre: sin esto cada
    render loguea "Exception while resolving variable". Las vistas que quieran
    otro comportamiento pisan estos valores desde su propio contexto.
    """

    del request

    return {
        "ocultar_volver": False,
        "volver_url": "",
        "volver_texto": "Volver",
    }
