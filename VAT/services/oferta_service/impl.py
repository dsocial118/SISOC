"""Compatibilidad minima para imports legacy del servicio de oferta."""


class OfertaService:  # pragma: no cover - shim defensivo para imports legacy
    """
    Shim temporal para evitar errores de importacion mientras el codigo migra
    a Comision + OfertaInstitucional.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "OfertaService fue reemplazado por Comision + OfertaInstitucional. "
            "Actualiza el import consumidor antes de instanciar este servicio."
        )
