from django.core.exceptions import ValidationError
from django.utils import timezone

from comedores.models import CapacitacionComedorCertificado


ALLOWED_CERTIFICATE_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


def is_alimentar_comunidad_program(comedor):
    programa_nombre = str(
        getattr(getattr(comedor, "programa", None), "nombre", "") or ""
    )
    normalized = " ".join(programa_nombre.lower().split())
    return normalized == "alimentar comunidad"


def _capacitacion_order_map():
    return {
        code: index
        for index, (code, _) in enumerate(
            CapacitacionComedorCertificado.CAPACITACION_CHOICES
        )
    }


def ensure_capacitaciones_certificados(comedor):
    existing_codes = set(
        CapacitacionComedorCertificado.objects.filter(comedor=comedor).values_list(
            "capacitacion", flat=True
        )
    )
    missing_objects = []
    for code, _label in CapacitacionComedorCertificado.CAPACITACION_CHOICES:
        if code in existing_codes:
            continue
        missing_objects.append(
            CapacitacionComedorCertificado(
                comedor=comedor,
                capacitacion=code,
                estado=CapacitacionComedorCertificado.ESTADO_SIN_PRESENTAR,
            )
        )
    if missing_objects:
        CapacitacionComedorCertificado.objects.bulk_create(missing_objects)


def list_capacitaciones_certificados(comedor):
    ensure_capacitaciones_certificados(comedor)
    records = list(
        CapacitacionComedorCertificado.objects.filter(comedor=comedor).select_related(
            "presentado_por",
            "revisado_por",
        )
    )
    order_map = _capacitacion_order_map()
    records.sort(key=lambda row: order_map.get(row.capacitacion, 999))
    return records


def validate_certificate_file(archivo):
    if not archivo:
        raise ValidationError("Debe adjuntar un archivo.")
    content_type = getattr(archivo, "content_type", None)
    if content_type and content_type not in ALLOWED_CERTIFICATE_CONTENT_TYPES:
        raise ValidationError("Formato inválido. Solo se permite imagen o PDF.")


def submit_certificate(certificado, archivo, actor):
    if certificado.archivo:
        raise ValidationError(
            "Ya hay un certificado cargado para esta capacitación. Debe eliminarlo para volver a subir."
        )
    validate_certificate_file(archivo)
    certificado.archivo = archivo
    certificado.estado = CapacitacionComedorCertificado.ESTADO_PRESENTADO
    certificado.observacion = None
    certificado.presentado_por = actor
    certificado.fecha_presentacion = timezone.now()
    certificado.revisado_por = None
    certificado.fecha_revision = None
    certificado.save(
        update_fields=[
            "archivo",
            "estado",
            "observacion",
            "presentado_por",
            "fecha_presentacion",
            "revisado_por",
            "fecha_revision",
            "modificado",
        ]
    )
    return certificado


def review_certificate(certificado, estado, actor, observacion=None):
    valid_statuses = {
        CapacitacionComedorCertificado.ESTADO_RECHAZADO,
        CapacitacionComedorCertificado.ESTADO_ACEPTADO,
        CapacitacionComedorCertificado.ESTADO_SIN_PRESENTAR,
    }
    if estado not in valid_statuses:
        raise ValidationError("Estado inválido.")

    estados_finales = {
        CapacitacionComedorCertificado.ESTADO_RECHAZADO,
        CapacitacionComedorCertificado.ESTADO_ACEPTADO,
    }
    estado_actual = certificado.estado
    if estado_actual in estados_finales and estado != estado_actual:
        raise ValidationError(
            "El certificado ya fue revisado y no puede cambiar de estado."
        )

    observacion = (observacion or "").strip()
    if estado == CapacitacionComedorCertificado.ESTADO_RECHAZADO and not observacion:
        raise ValidationError("Debe ingresar una observación para rechazar.")

    certificado.estado = estado
    certificado.revisado_por = actor
    certificado.fecha_revision = timezone.now()

    if estado == CapacitacionComedorCertificado.ESTADO_RECHAZADO:
        certificado.observacion = observacion
    elif estado == CapacitacionComedorCertificado.ESTADO_ACEPTADO:
        certificado.observacion = None
    else:
        certificado.observacion = None
        certificado.archivo = None
        certificado.presentado_por = None
        certificado.fecha_presentacion = None

    update_fields = [
        "estado",
        "observacion",
        "revisado_por",
        "fecha_revision",
        "modificado",
    ]
    if estado == CapacitacionComedorCertificado.ESTADO_SIN_PRESENTAR:
        update_fields.extend(["archivo", "presentado_por", "fecha_presentacion"])
    certificado.save(update_fields=update_fields)
    return certificado


def delete_certificate(certificado):
    if (
        certificado.estado == CapacitacionComedorCertificado.ESTADO_ACEPTADO
        and certificado.archivo
    ):
        raise ValidationError("No se puede eliminar un certificado aceptado.")

    certificado.archivo = None
    certificado.estado = CapacitacionComedorCertificado.ESTADO_SIN_PRESENTAR
    certificado.observacion = None
    certificado.presentado_por = None
    certificado.fecha_presentacion = None
    certificado.revisado_por = None
    certificado.fecha_revision = None
    certificado.save(
        update_fields=[
            "archivo",
            "estado",
            "observacion",
            "presentado_por",
            "fecha_presentacion",
            "revisado_por",
            "fecha_revision",
            "modificado",
        ]
    )
    return certificado


def serialize_certificate(certificado, request=None):
    archivo_url = None
    archivo_nombre = None
    if certificado.archivo:
        archivo_nombre = certificado.archivo.name.split("/")[-1]
        if request is not None:
            archivo_url = request.build_absolute_uri(certificado.archivo.url)
        else:
            archivo_url = certificado.archivo.url

    return {
        "id": certificado.id,
        "capacitacion": certificado.capacitacion,
        "capacitacion_label": certificado.get_capacitacion_display(),
        "estado": certificado.estado,
        "estado_label": certificado.get_estado_display(),
        "archivo_url": archivo_url,
        "archivo_nombre": archivo_nombre,
        "observacion": certificado.observacion,
        "fecha_presentacion": certificado.fecha_presentacion,
        "fecha_revision": certificado.fecha_revision,
        "presentado_por": (
            certificado.presentado_por.get_full_name()
            or certificado.presentado_por.username
            if certificado.presentado_por
            else None
        ),
        "revisado_por": (
            certificado.revisado_por.get_full_name()
            or certificado.revisado_por.username
            if certificado.revisado_por
            else None
        ),
    }
