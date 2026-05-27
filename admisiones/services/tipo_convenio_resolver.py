"""Helper compartido entre ``admisiones`` y ``organizaciones`` para mapear
``Organizacion.tipo_entidad`` con ``DocumentacionOrganizacion.categoria`` y con
``TipoConvenio``.

La heuristica historica vive en ``organizaciones/views.py`` (por nombre) y en
``admisiones/services/admisiones_service/impl.py`` (por id). Este modulo
centraliza ambas para evitar drift.
"""

from organizaciones.models import DocumentacionOrganizacion

from admisiones.models.admisiones import Admision, TipoConvenio


CATEGORIA_POR_TIPO_CONVENIO_ID = {
    1: DocumentacionOrganizacion.CATEGORIA_BASE,
    2: DocumentacionOrganizacion.CATEGORIA_ECLESIASTICA,
    3: DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
}

TIPO_CONVENIO_ID_POR_CATEGORIA = {
    categoria: tipo_id for tipo_id, categoria in CATEGORIA_POR_TIPO_CONVENIO_ID.items()
}


def categoria_para_tipo_entidad(tipo_entidad, subtipo_entidad=None):
    """Resuelve la categoria documental aplicable a una organizacion segun el
    nombre de su ``tipo_entidad`` (y opcionalmente del ``subtipo_entidad``).
    Replica la heuristica historica utilizada en ``organizaciones/views.py``.
    """

    textos = " ".join(
        str(valor or "")
        for valor in (
            getattr(tipo_entidad, "nombre", "") if tipo_entidad else "",
            getattr(subtipo_entidad, "nombre", "") if subtipo_entidad else "",
        )
    ).lower()
    if "ecles" in textos or "culto" in textos:
        return DocumentacionOrganizacion.CATEGORIA_ECLESIASTICA
    if "base" in textos or "hecho" in textos:
        return DocumentacionOrganizacion.CATEGORIA_BASE
    return DocumentacionOrganizacion.CATEGORIA_PERSONERIA


def categoria_para_organizacion(organizacion):
    if not organizacion:
        return DocumentacionOrganizacion.CATEGORIA_PERSONERIA
    return categoria_para_tipo_entidad(
        getattr(organizacion, "tipo_entidad", None),
        getattr(organizacion, "subtipo_entidad", None),
    )


def tipo_convenio_para_organizacion(organizacion):
    """Devuelve la instancia de ``TipoConvenio`` que corresponde al
    ``tipo_entidad`` de la organizacion. Si no se puede resolver, retorna
    ``None``.
    """

    categoria = categoria_para_organizacion(organizacion)
    tipo_convenio_id = TIPO_CONVENIO_ID_POR_CATEGORIA.get(categoria)
    if not tipo_convenio_id:
        return None
    return TipoConvenio.objects.filter(pk=tipo_convenio_id).first()


def admision_desincronizada(admision):
    """Indica si la ``admision`` quedo desincronizada respecto al
    ``tipo_entidad`` actual de la organizacion de su comedor. Se considera
    desincronizada cuando el snapshot guardado en ``tipo_entidad_origen``
    difiere del ``tipo_entidad`` actual.
    """

    if not isinstance(admision, Admision):
        return False
    organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
    if not organizacion:
        return False
    tipo_actual_id = getattr(organizacion, "tipo_entidad_id", None)
    snapshot_id = getattr(admision, "tipo_entidad_origen_id", None)
    if not tipo_actual_id or not snapshot_id:
        return False
    return tipo_actual_id != snapshot_id
