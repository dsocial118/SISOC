from __future__ import annotations

from pathlib import Path

from django import forms
from django.conf import settings


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return single_clean(data, initial)


class OCRUploadForm(forms.Form):
    archivos = MultipleFileField(
        label="Archivos",
        help_text="Formatos admitidos: JPG, JPEG, PNG, PDF.",
        required=False,
    )

    def clean_archivos(self):
        files = self.files.getlist("archivos")
        if not files:
            raise forms.ValidationError("Debe seleccionar al menos un archivo.")

        max_size = getattr(settings, "OCR_MAX_FILE_SIZE_MB", 20) * 1024 * 1024
        allowed_exts = getattr(
            settings, "OCR_ALLOWED_EXTENSIONS", {"jpg", "jpeg", "png", "pdf"}
        )
        errors = []

        for f in files:
            ext = Path(f.name).suffix.lower().lstrip(".")
            if ext not in allowed_exts:
                errors.append(
                    f"'{f.name}': tipo de archivo no admitido (.{ext}). "
                    f"Use: {', '.join(sorted(allowed_exts))}."
                )
            elif f.size > max_size:
                size_mb = f.size / 1024 / 1024
                errors.append(
                    f"'{f.name}': archivo demasiado grande "
                    f"({size_mb:.1f} MB, máximo {settings.OCR_MAX_FILE_SIZE_MB} MB)."
                )

        if errors:
            raise forms.ValidationError(errors)

        return files
