"""API pública de Centro de Infancia para otros dominios.

Los módulos internos (`access`, `models`, `services`, ...) son privados del
dominio: el contrato de arquitectura (`.importlinter`) prohíbe importarlos
desde otras apps. Este módulo es el único punto de entrada estable y expone
datos ya resueltos, sin filtrar querysets ni modelos hacia afuera.
"""

from centrodeinfancia.access import ids_centros_referente, ids_centros_trabajador
from centrodeinfancia.models import CentroDeInfancia

VINCULO_REFERENTE = "referente"
VINCULO_TRABAJADOR = "trabajador"


def centros_cdi_de_usuario(user):
    """Centros vigentes del usuario, con el tipo de vínculo de cada uno.

    Devuelve una lista de dicts ``{id, nombre, codigo_cdi, vinculo}``. Aplica
    las reglas del dominio: referentes con `AccesoCDI` activo y trabajadores no
    eliminados lógicamente. La consulta usa el manager normal de
    `CentroDeInfancia`, por lo que tampoco expone CDIs eliminados lógicamente.
    Si el usuario tiene ambos vínculos sobre un mismo CDI aparecen las dos
    entradas. Los centros se resuelven en bloque (sin N+1).
    """
    centros_por_vinculo = (
        (VINCULO_REFERENTE, set(ids_centros_referente(user) or [])),
        (VINCULO_TRABAJADOR, set(ids_centros_trabajador(user) or [])),
    )
    centros_por_id = CentroDeInfancia.objects.only(
        "id", "nombre", "codigo_cdi"
    ).in_bulk(
        {centro_id for _, centro_ids in centros_por_vinculo for centro_id in centro_ids}
    )

    return [
        {
            "id": centro.id,
            "nombre": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "vinculo": vinculo,
        }
        for vinculo, centro_ids in centros_por_vinculo
        for centro_id in sorted(centro_ids)
        if (centro := centros_por_id.get(centro_id)) is not None
    ]
