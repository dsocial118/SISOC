"""Vinculación de expedientes de pago con la admisión correspondiente.

El expediente del convenio se carga a mano como texto libre, y del otro lado
``Admision.num_expediente`` también es texto libre. La comparación se hace sobre
una forma normalizada de ambos.

La normalización se validó contra los datos de producción: quitar espacios,
guiones, barras y puntos es lo que más matches recupera. Se probó también una
normalización "GDE" (extraer año y número, descartando ceros a la izquierda y el
sufijo de dependencia) y **no** mejora el resultado, por lo que se descartó.
"""

import logging

logger = logging.getLogger("django")

_SEPARADORES = (" ", "-", "/", ".")


def normalizar_expediente(valor):
    """Devuelve la forma comparable de un número de expediente.

    Args:
        valor: Texto del expediente, o None.

    Returns:
        str: Texto normalizado, o cadena vacía si no hay valor utilizable.
    """
    if not valor:
        return ""

    texto = str(valor).strip().upper()
    for separador in _SEPARADORES:
        texto = texto.replace(separador, "")
    return texto


def resolver_admision(comedor, expediente_convenio):
    """Busca la admisión del comedor cuyo expediente coincide con el del convenio.

    Solo se considera resuelto cuando hay **una** coincidencia. Con cero o con
    varias se devuelve ``None``: es preferible dejarlo sin asignar y que alguien
    lo resuelva a mano antes que vincularlo a la admisión equivocada.

    Args:
        comedor: Comedor dueño del expediente de pago.
        expediente_convenio: Texto del expediente del convenio.

    Returns:
        Admision | None
    """
    clave = normalizar_expediente(expediente_convenio)
    if not clave or comedor is None:
        return None

    try:
        from admisiones.models.admisiones import Admision

        candidatas = [
            admision
            for admision in Admision.objects.filter(comedor=comedor).only(
                "id", "num_expediente", "comedor_id"
            )
            if normalizar_expediente(admision.num_expediente) == clave
        ]
    except Exception:
        logger.exception(
            "Error al resolver la admisión de un expediente de pago",
            extra={"comedor_pk": getattr(comedor, "pk", None)},
        )
        return None

    if len(candidatas) == 1:
        return candidatas[0]
    return None


def asignar_admision(expediente_pago, admision_elegida=None):
    """Define la admisión de un expediente de pago.

    La elección manual siempre gana; la resolución automática solo completa el
    vacío.

    Args:
        expediente_pago: Instancia de ExpedientePago (aún sin guardar o guardada).
        admision_elegida: Admisión seleccionada por el usuario, si eligió alguna.

    Returns:
        Admision | None: la admisión finalmente asignada.
    """
    if admision_elegida is not None:
        expediente_pago.admision = admision_elegida
        return admision_elegida

    expediente_pago.admision = resolver_admision(
        expediente_pago.comedor, expediente_pago.expediente_convenio
    )
    return expediente_pago.admision
