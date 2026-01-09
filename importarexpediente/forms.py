from django import forms


class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Archivo CSV")
    delimiter = forms.ChoiceField(
        choices=[(",", "Coma (,)"), (";", "Punto y coma (;)")],
        initial=",",
        label="Delimitador",
    )
    has_header = forms.BooleanField(
        required=False, initial=True, label="Incluye cabecera"
    )
