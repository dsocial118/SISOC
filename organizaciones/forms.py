from django import forms
from django.forms import inlineformset_factory
from organizaciones.models import (
    Organizacion,
    ProyectoOrganizacion,
    Firmante,
    Aval,
    SubtipoEntidad,
)
from core.models import Municipio, Provincia, Localidad


class OrganizacionForm(forms.ModelForm):
    codigos_proyecto = forms.CharField(
        required=False,
        label="Códigos de Proyecto",
        help_text="Separá múltiples códigos con comas.",
    )
    cuit = forms.RegexField(
        regex=r"^[0-9]{11}$",
        required=False,
        strip=False,
        error_messages={
            "invalid": "Ingresá un CUIT de 11 dígitos, solo con números y sin espacios.",
        },
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "maxlength": "11",
                "pattern": "[0-9]{11}",
                "title": "Ingresá 11 dígitos, solo con números y sin espacios.",
            }
        ),
    )
    cuil_duplicado_confirmado = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput,
    )
    cuil_duplicado_confirmado_valor = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Asegura que el campo date cargue el valor previo (almacenado como DateTime)
        fecha_vencimiento = getattr(self.instance, "fecha_vencimiento", None)
        if not self.is_bound and fecha_vencimiento:
            self.initial["fecha_vencimiento"] = fecha_vencimiento.date()
        self.fields["fecha_vencimiento"].input_formats = ["%Y-%m-%d"]
        self.fields["fecha_vencimiento"].required = False

        self.popular_campos_ubicacion()
        subtipo_actual_id = (
            self.data.get(self.add_prefix("subtipo_entidad"))
            if self.is_bound
            else getattr(self.instance, "subtipo_entidad_id", None)
        )
        subtipos = SubtipoEntidad.objects.filter(activo=True)
        if subtipo_actual_id:
            subtipos = subtipos | SubtipoEntidad.objects.filter(pk=subtipo_actual_id)
        self.fields["subtipo_entidad"].queryset = subtipos.order_by("nombre")
        if not self.is_bound and self.instance.pk:
            self.initial["codigos_proyecto"] = ", ".join(
                self.instance.proyectos.filter(activo=True).values_list(
                    "codigo", flat=True
                )
            )

    def popular_campos_ubicacion(self):

        def pk_formatter(value):
            return int(value) if value and value.isdigit() else None

        provincia = Provincia.objects.filter(
            pk=pk_formatter(self.data.get("provincia"))
        ).first() or getattr(self.instance, "provincia", None)

        municipio = Municipio.objects.filter(
            pk=pk_formatter(self.data.get("municipio"))
        ).first() or getattr(self.instance, "municipio", None)

        localidad = Localidad.objects.filter(
            pk=pk_formatter(self.data.get("localidad"))
        ).first() or getattr(self.instance, "localidad", None)

        if provincia:
            self.fields["provincia"].initial = Provincia.objects.get(id=provincia.id)
            self.fields["provincia"].queryset = Provincia.objects.all()
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=provincia
            )
        else:
            self.fields["provincia"].queryset = Provincia.objects.all()
            self.fields["municipio"].queryset = Municipio.objects.none()
            self.fields["localidad"].queryset = Localidad.objects.none()

        if municipio:
            self.fields["municipio"].initial = municipio
            self.fields["localidad"].queryset = Localidad.objects.filter(
                municipio=municipio
            )

        if localidad:
            self.fields["localidad"].initial = localidad

    def clean_cuit(self):
        cuit = self.cleaned_data.get("cuit")
        if not cuit:
            return None
        return int(cuit)

    def clean(self):
        cleaned_data = super().clean()
        cuit = cleaned_data.get("cuit")
        confirmado = cleaned_data.get("cuil_duplicado_confirmado")
        cuit_confirmado = cleaned_data.get("cuil_duplicado_confirmado_valor")

        if cuit is not None:
            exclude_pk = (
                self.instance.pk if self.instance and self.instance.pk else None
            )
            qs = Organizacion.objects.filter(cuit=cuit)
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)

            if qs.exists() and (not confirmado or cuit_confirmado != str(cuit)):
                self.add_error(
                    "cuit",
                    forms.ValidationError(
                        "El CUIL ingresado ya está registrado en otra organización. "
                        "Revisá la advertencia y confirmá para continuar.",
                        code="cuil_duplicado_sin_confirmar",
                    ),
                )

        sin_vencimiento = cleaned_data.get("sin_vencimiento")
        if sin_vencimiento:
            cleaned_data["fecha_vencimiento"] = None
        elif not cleaned_data.get("fecha_vencimiento"):
            self.add_error(
                "fecha_vencimiento",
                "Ingresá una fecha o seleccioná Sin Vencimiento.",
            )

        return cleaned_data

    def clean_codigos_proyecto(self):
        codigos = {
            codigo.strip()
            for codigo in (self.cleaned_data.get("codigos_proyecto") or "").split(",")
            if codigo.strip()
        }
        return sorted(codigos)

    def save(self, commit=True):
        organizacion = super().save(commit=commit)
        if commit:
            codigos = self.cleaned_data.get("codigos_proyecto", [])
            organizacion.proyectos.exclude(codigo__in=codigos).update(activo=False)
            for codigo in codigos:
                ProyectoOrganizacion.objects.update_or_create(
                    organizacion=organizacion,
                    codigo=codigo,
                    defaults={"activo": True},
                )
        return organizacion

    class Meta:
        model = Organizacion
        fields = "__all__"
        widgets = {
            "fecha_vencimiento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d",
            ),
        }


class FirmanteForm(forms.ModelForm):
    class Meta:
        model = Firmante
        fields = ["nombre", "rol", "cuit", "programa"]

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")
        cuit = cleaned_data.get("cuit")

        if rol == "aval" and not cuit:
            self.add_error("cuit", "El CUIT es obligatorio para el rol Aval")


class AvalForm(forms.ModelForm):
    class Meta:
        model = Aval
        fields = ["nombre", "cuit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].required = False
        self.fields["cuit"].required = False


AvalFormset = inlineformset_factory(
    Organizacion, Aval, form=AvalForm, extra=1, max_num=1, can_delete=True
)
FirmanteFormset = inlineformset_factory(
    Organizacion, Firmante, form=FirmanteForm, extra=0, can_delete=True
)
