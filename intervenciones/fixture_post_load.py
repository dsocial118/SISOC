"""Sincronizaciones de Intervenciones posteriores a los fixtures base."""

from core.services.fixture_post_load import (
    registrar_fixture_post_load_handler as registrar_handler,
)
from intervenciones.services_catalogo import sync_catalogo_intervenciones


def sincronizar_catalogo_intervenciones() -> str:
    """Normaliza el catálogo CDI y devuelve el mensaje operativo del comando."""
    resumen = sync_catalogo_intervenciones()
    return (
        "✅ Catálogo de intervenciones sincronizado: "
        f"tipos={resumen['tipos_sincronizados']}, "
        f"subtipos={resumen['subtipos_sincronizados']}, "
        f"subtipos_vacios_eliminados={resumen['subtipos_vacios_eliminados']}"
    )


def registrar_fixture_post_load_handler() -> None:
    """Registra el post-proceso del catálogo al iniciar la app."""
    registrar_handler("intervenciones.catalogo", sincronizar_catalogo_intervenciones)
