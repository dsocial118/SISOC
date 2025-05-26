from django import forms
from django.contrib.auth.models import Group
from expedientespagos.models import ExpedientePago

class ExpedientePagoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filtrar_campos_usuario()

    def filtrar_campos_usuario(self):
        # Filtrar usuarios que pertenezcan al grupo "Usuarios Expedientes"
        grupo_usuarios = Group.objects.filter(name="Usuarios Expedientes").first()
        if grupo_usuarios:
            self.fields["usuario"].queryset = grupo_usuarios.user_set.all()
        else:
            self.fields["usuario"].queryset = self.fields["usuario"].queryset.none()

    class Meta:
        model = ExpedientePago
        fields = "__all__"
        widgets = {
            "usuario": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "nombre": "Nombre del Expediente",
            "usuario": "Usuario Responsable",
            "estado": "Estado del Expediente",
        }


