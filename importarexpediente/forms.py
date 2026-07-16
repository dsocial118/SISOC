from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


class ImportFileForm(forms.Form):
    file = forms.FileField(
        label="Archivo CSV o XLSX",
        validators=[FileExtensionValidator(["csv", "xlsx"])],
        widget=forms.ClearableFileInput(
            attrs={"accept": ".csv,.xlsx"},
        ),
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        max_size = getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
        if f.size > max_size:
            raise ValidationError("El archivo supera el tamaño permitido.")
        return f


class CSVUploadForm(ImportFileForm):
    delimiter = forms.ChoiceField(
        choices=[(",", "Coma (,)"), (";", "Punto y coma (;)")],
        initial=",",
        label="Delimitador",
    )
    has_header = forms.BooleanField(
        required=False, initial=True, label="Incluye cabecera"
    )


class AcreditacionUploadForm(ImportFileForm):
    pass
