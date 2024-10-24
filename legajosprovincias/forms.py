from datetime import date

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from usuarios.validators import MaxSizeFileValidator

from .models import (
    LegajosProvincias,
    Presupuesto,
    HistorialPresupuesto,
    Proyectos,
    DocumentacionArchivos,
)

class LegajosProvinciasForm(forms.ModelForm):
    """Formulario para las provincias de los legajos."""
    class Meta:
        model = LegajosProvincias
        fields = "__all__"
        widgets = {
            "agroindustria_alimentos": forms.CheckboxInput(),
            "agroindustria_ganaderia": forms.CheckboxInput(),
            "agroindustria_agricultura_familiar": forms.CheckboxInput(),
            "agroindustria_pesca": forms.CheckboxInput(),
            "agroindustria_forestal": forms.CheckboxInput(),
            "agroindustria_manufactura": forms.CheckboxInput(),
            "oficios_carpinteria": forms.CheckboxInput(),
            "oficios_electicista": forms.CheckboxInput(),
            "oficios_mecanica": forms.CheckboxInput(),
            "oficios_herreria": forms.CheckboxInput(),
            "oficios_jardineria": forms.CheckboxInput(),
            "oficios_gastronomico": forms.CheckboxInput(),
            "oficios_logistica": forms.CheckboxInput(),
            "oficios_textil": forms.CheckboxInput(),
            "oficios_soldador": forms.CheckboxInput(),
            "oficios_plomeria": forms.CheckboxInput(),
            "oficios_albanileria": forms.CheckboxInput(),
            "oficios_panaderia": forms.CheckboxInput(),
            "oficios_auxiliar_salud": forms.CheckboxInput(),
            "economia_circular_ener_renovable": forms.CheckboxInput(),
            "economia_circular_reciclaje": forms.CheckboxInput(),
            "tecnologia_software_soporte_tecnico": forms.CheckboxInput(),
        }

class PresupuestoForm(forms.ModelForm):
    """Formulario para el presupuesto."""
    class Meta:
        model = Presupuesto
        fields = "__all__"

class HistorialPresupuestoForm(forms.ModelForm):
    """Formulario para el presupuesto gastado."""
    class Meta:
        model = HistorialPresupuesto
        fields = "__all__"

class ProyectosForm(forms.ModelForm):
    """Formulario para los proyectos."""
    class Meta:
        model = Proyectos
        fields = "__all__"

class DocumentacionArchivosForm(forms.ModelForm):
    """Formulario para la documentacion de archivos."""
    class Meta:
        model = DocumentacionArchivos
        fields = "__all__"
        widgets = {
            "archivo": forms.FileInput(attrs={"accept": ".pdf, .doc, .docx, .xls, .xlsx, .jpg, .jpeg, .png, .gif, .zip, .rar, .7z, .tar.gz, .tar.bz2, .tar.xz, .tar"}),
        }