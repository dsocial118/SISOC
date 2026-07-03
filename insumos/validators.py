from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

INSUMO_ALLOWED_EXTENSIONS = (
    "pdf",
    "jpg",
    "jpeg",
    "png",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
)
INSUMO_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
}
INSUMO_MAX_SIZE_BYTES = 10 * 1024 * 1024
INSUMO_ACCEPT_ATTR = ".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.csv"


validate_insumo_extension = FileExtensionValidator(
    allowed_extensions=INSUMO_ALLOWED_EXTENSIONS,
    message="Solo se permiten archivos PDF, imágenes, Word, Excel o CSV.",
)


def validate_insumo_file_size(value):
    if value and value.size > INSUMO_MAX_SIZE_BYTES:
        raise ValidationError("El archivo supera el tamaño máximo de 10 MB.")


def validate_insumo_content_type(value):
    content_type = getattr(value, "content_type", None)
    if not content_type and getattr(value, "file", None):
        content_type = getattr(value.file, "content_type", None)

    if content_type and content_type not in INSUMO_ALLOWED_CONTENT_TYPES:
        raise ValidationError("El tipo de archivo no está permitido.")


INSUMO_FILE_VALIDATORS = [
    validate_insumo_extension,
    validate_insumo_file_size,
    validate_insumo_content_type,
]
