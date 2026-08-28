from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

DOCUMENTACION_UPLOAD_FIELDS = (
    "documentacion_dispositivo",
    "documentacion_dispositivo_adicional_1",
    "documentacion_dispositivo_adicional_2",
    "documentacion_dispositivo_adicional_3",
    "documentacion_dispositivo_adicional_4",
)
DOCUMENTACION_ALLOWED_EXTENSIONS = ("pdf", "jpg", "jpeg", "png")
DOCUMENTACION_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}
DOCUMENTACION_MAX_SIZE_BYTES = 10 * 1024 * 1024
DOCUMENTACION_ACCEPT_ATTR = ".pdf,.jpg,.jpeg,.png"


validate_documentacion_extension = FileExtensionValidator(
    allowed_extensions=DOCUMENTACION_ALLOWED_EXTENSIONS,
    message="Solo se permiten archivos PDF, JPG o PNG.",
)


def validate_documentacion_file_size(value):
    if value and value.size > DOCUMENTACION_MAX_SIZE_BYTES:
        raise ValidationError("El archivo supera el tamaño máximo de 10 MB.")


def validate_documentacion_content_type(value):
    content_type = getattr(value, "content_type", None)
    if not content_type and getattr(value, "file", None):
        content_type = getattr(value.file, "content_type", None)

    if content_type and content_type not in DOCUMENTACION_ALLOWED_CONTENT_TYPES:
        raise ValidationError("El tipo de archivo no está permitido.")


DOCUMENTACION_FILE_VALIDATORS = [
    validate_documentacion_extension,
    validate_documentacion_file_size,
    validate_documentacion_content_type,
]
