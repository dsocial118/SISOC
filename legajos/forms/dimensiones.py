from django import forms

from legajos.models import (
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
    LegajoLocalidad,
    LegajoMunicipio,
    LegajoProvincias,
)


class DimensionFamiliaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionFamilia
        fields = "__all__"
        widgets = {
            "obs_familia": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "otro_responsable": forms.CheckboxInput(),
            #  'otro_responsable': forms.CheckboxInput(attrs={'class':'icheck-primary '}),
            "hay_embarazadas": forms.CheckboxInput(),
            "hay_prbl_smental": forms.CheckboxInput(),
            "hay_fam_discapacidad": forms.CheckboxInput(),
            "hay_enf_cronica": forms.CheckboxInput(),
            "hay_priv_libertad": forms.CheckboxInput(),
        }


class DimensionViviendaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionVivienda
        fields = "__all__"
        widgets = {
            "obs_vivienda": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            #'hay_agua_caliente': forms.CheckboxInput(),
            #'hay_desmoronamiento': forms.CheckboxInput(),
            #'hay_banio': forms.CheckboxInput(),
            #'PoseenCeludar': forms.CheckboxInput(),
            #'PoseenPC': forms.CheckboxInput(),
            #'Poseeninternet': forms.CheckboxInput()
        }


# <!-- ./Nuevos campos vivienda Form Editar o cargar -->


class DimensionSaludForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionSalud
        fields = "__all__"
        widgets = {
            "obs_salud": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "hay_obra_social": forms.CheckboxInput(),
            "hay_enfermedad": forms.CheckboxInput(),
            "hay_discapacidad": forms.CheckboxInput(),
            "hay_cud": forms.CheckboxInput(),
        }


class DimensionEducacionForm(forms.ModelForm):
    provinciaInstitucion = forms.ModelChoiceField(
        label="Provincia",
        queryset=LegajoProvincias.objects.all(),
    )
    municipioInstitucion = forms.ModelChoiceField(
        label="Municipio",
        queryset=LegajoMunicipio.objects.none(),
    )
    localidadInstitucion = forms.ModelChoiceField(
        label="Localidad",
        queryset=LegajoLocalidad.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

        # Configurar el queryset del campo 'provinciaInstitucion' para cargar solo las provincias
        self.fields["provinciaInstitucion"].queryset = LegajoProvincias.objects.all()
        # Configurar los querysets de los campos 'municipioInstitucion' y 'localidadInstitucion' para que estén vacíos inicialmente
        self.fields["municipioInstitucion"].queryset = LegajoMunicipio.objects.none()
        self.fields["localidadInstitucion"].queryset = LegajoLocalidad.objects.none()

        # Actualizar los querysets si los datos están presentes en el formulario
        if "municipioInstitucion" in self.data:
            try:
                municipio_id = int(self.data.get("municipioInstitucion"))
                self.fields["municipioInstitucion"].queryset = (
                    LegajoMunicipio.objects.filter(id=municipio_id).order_by(
                        "nombre_region"
                    )
                )
            except (ValueError, TypeError):
                self.fields["municipioInstitucion"].queryset = (
                    LegajoMunicipio.objects.none()
                )

        if "localidadInstitucion" in self.data:
            try:
                localidad_id = int(self.data.get("localidadInstitucion"))
                self.fields["localidadInstitucion"].queryset = (
                    LegajoLocalidad.objects.filter(id=localidad_id).order_by("nombre")
                )
            except (ValueError, TypeError):
                self.fields["localidadInstitucion"].queryset = (
                    LegajoLocalidad.objects.none()
                )

    class Meta:
        model = DimensionEducacion
        fields = "__all__"
        widgets = {
            "obs_educacion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "areaCurso": forms.SelectMultiple(attrs={"class": "form-control"}),
            "areaOficio": forms.SelectMultiple(attrs={"class": "form-control"}),
        }

    def clean_area_curso(self):
        data = self.cleaned_data["areaCurso"]
        if len(data) > 3:
            raise forms.ValidationError("Solo puedes seleccionar hasta 3 opciones.")
        return data


class DimensionEconomiaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionEconomia
        fields = "__all__"
        widgets = {
            "obs_economia": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            #'recibe_plan': forms.CheckboxInput(),
            "m2m_planes": forms.SelectMultiple(
                attrs={"class": "select2 w-100", "multiple": True}
            ),
        }
        labels = {"m2m_planes": "Planes sociales que recibe"}


class DimensionTrabajoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionTrabajo
        fields = "__all__"
        widgets = {
            "obs_trabajo": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            #'tiene_trabajo': forms.CheckboxInput(),
            #'conviviente_trabaja': forms.CheckboxInput(),
        }
