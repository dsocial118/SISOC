"""Validadores de archivos de Celiaquía.

Sigue la convención por app del repo (`dispositivos/validators.py`,
`insumos/validators.py`): cada dominio declara sus formatos y topes en lugar de
importarlos de otra app.
"""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

#: Documentación complementaria que Nación adjunta al solicitar una subsanación
#: (issue #2523). Los límites los definió el área.
COMPLEMENTARIA_ALLOWED_EXTENSIONS = ("pdf", "jpg", "jpeg", "png")
COMPLEMENTARIA_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}
COMPLEMENTARIA_MAX_SIZE_BYTES = 10 * 1024 * 1024
COMPLEMENTARIA_MAX_SIZE_MB = COMPLEMENTARIA_MAX_SIZE_BYTES // (1024 * 1024)
COMPLEMENTARIA_MAX_ARCHIVOS = 5
COMPLEMENTARIA_ACCEPT_ATTR = ".pdf,.jpg,.jpeg,.png"


_validate_extension = FileExtensionValidator(
    allowed_extensions=COMPLEMENTARIA_ALLOWED_EXTENSIONS,
    message="Solo se permiten archivos PDF, JPG o PNG.",
)


def _content_type_de(archivo):
    """Content type declarado por el cliente, o None si no viene."""
    content_type = getattr(archivo, "content_type", None)
    if not content_type and getattr(archivo, "file", None):
        content_type = getattr(archivo.file, "content_type", None)
    return content_type


def validar_archivo_complementario(archivo):
    """Valida un archivo suelto de documentación complementaria.

    Chequea extensión, tamaño y content type. El content type lo declara el
    cliente y es falsificable, así que la extensión se valida siempre: es la que
    determina cómo se sirve después el archivo.
    """
    _validate_extension(archivo)

    if archivo.size > COMPLEMENTARIA_MAX_SIZE_BYTES:
        raise ValidationError(
            f'"{archivo.name}" supera el tamaño máximo de '
            f"{COMPLEMENTARIA_MAX_SIZE_MB} MB."
        )

    content_type = _content_type_de(archivo)
    if content_type and content_type not in COMPLEMENTARIA_ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            f'El tipo de archivo de "{archivo.name}" no está permitido.'
        )


def validar_archivos_complementarios(archivos):
    """Valida el lote completo y devuelve la lista sin los slots vacíos.

    Se valida todo antes de tocar la base: la carga es parte de la transacción
    que cambia el estado del legajo y no queremos subsanar a medias.
    """
    archivos = [a for a in (archivos or []) if a]

    if len(archivos) > COMPLEMENTARIA_MAX_ARCHIVOS:
        raise ValidationError(
            f"Podés adjuntar hasta {COMPLEMENTARIA_MAX_ARCHIVOS} archivos de "
            f"documentación complementaria (llegaron {len(archivos)})."
        )

    for archivo in archivos:
        validar_archivo_complementario(archivo)

    return archivos
