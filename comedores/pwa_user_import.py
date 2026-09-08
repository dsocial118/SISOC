"""Proveedor de espacios PWA para el importador de usuarios."""

from django.core.exceptions import ValidationError

from comedores.models import Comedor
from comedores.services.capacitaciones_certificados_service import (
    is_alimentar_comunidad_program,
)
from organizaciones.models import Organizacion
from users.pwa_import_access import (
    ComedorOrganizacionPWA,
    SeleccionAccesosPWAImportacion,
    registrar_resolvedor_accesos_pwa_importacion,
)


def _parse_semicolon_field(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _resolver_organizacion_ids(organizaciones_raw: str) -> tuple[int, ...]:
    organizacion_ids = []
    for token in _parse_semicolon_field(organizaciones_raw):
        try:
            organizacion_id = int(token)
        except ValueError as exc:
            raise ValidationError(
                f"El ID de organizacion '{token}' no es valido."
            ) from exc
        if not Organizacion.objects.filter(pk=organizacion_id).exists():
            raise ValidationError(
                f"La organizacion con ID '{token}' no existe en el sistema."
            )
        organizacion_ids.append(organizacion_id)
    return tuple(organizacion_ids)


def _resolver_comedores(comedores_raw: str) -> tuple[list[Comedor], tuple[int, ...]]:
    comedores = []
    comedor_ids = []
    for token in _parse_semicolon_field(comedores_raw):
        try:
            comedor_id = int(token)
        except ValueError as exc:
            raise ValidationError(f"El ID de comedor '{token}' no es valido.") from exc
        comedor = (
            Comedor.objects.select_related("programa").filter(pk=comedor_id).first()
        )
        if comedor is None:
            raise ValidationError(
                f"El comedor con ID '{token}' no existe en el sistema."
            )
        comedores.append(comedor)
        comedor_ids.append(comedor_id)
    return comedores, tuple(comedor_ids)


def resolver_accesos_pwa_importacion(
    organizaciones_raw: str, comedores_raw: str
) -> SeleccionAccesosPWAImportacion:
    """Conserva la validación y expansión de accesos del importador PWA."""
    organizacion_ids = _resolver_organizacion_ids(organizaciones_raw)
    comedores, comedor_ids = _resolver_comedores(comedores_raw)
    comedor_id_alimentar_comunidad = next(
        (
            comedor.pk
            for comedor in comedores
            if is_alimentar_comunidad_program(comedor)
        ),
        None,
    )
    comedores_por_organizacion = tuple(
        ComedorOrganizacionPWA(comedor_id=comedor_id, organizacion_id=organizacion_id)
        for comedor_id, organizacion_id in Comedor.objects.filter(
            organizacion_id__in=set(organizacion_ids)
        ).values_list("pk", "organizacion_id")
    )
    return SeleccionAccesosPWAImportacion(
        organizacion_ids=organizacion_ids,
        comedor_ids=comedor_ids,
        comedores_por_organizacion=comedores_por_organizacion,
        comedor_id_alimentar_comunidad=comedor_id_alimentar_comunidad,
    )


def registrar_resolvedor_user_import_pwa() -> None:
    """Conecta el proveedor de Comedores con la importación PWA de Users."""
    registrar_resolvedor_accesos_pwa_importacion(resolver_accesos_pwa_importacion)
