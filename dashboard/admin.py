from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Dashboard, Tablero


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ("llave", "cantidad")
    list_filter = ("llave",)


class TableroAdminForm(forms.ModelForm):
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        help_text="Selecciona los grupos con acceso al tablero.",
    )

    class Meta:
        model = Tablero
        fields = (
            "nombre",
            "slug",
            "url",
            "mensaje_construccion",
            "orden",
            "activo",
            "grupos",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.permisos:
            self.fields["grupos"].initial = Group.objects.filter(
                name__in=self.instance.permisos
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        grupos = self.cleaned_data.get("grupos")
        instance.permisos = (
            list(grupos.values_list("name", flat=True)) if grupos else []
        )
        if commit:
            instance.save()
        return instance


@admin.register(Tablero)
class TableroAdmin(admin.ModelAdmin):
    form = TableroAdminForm
    list_display = ("nombre", "slug", "activo", "orden")
    list_filter = ("activo",)
    ordering = ("orden", "nombre")
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
