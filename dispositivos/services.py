from django.shortcuts import get_object_or_404

from .models import Dispositivo


def get_dispositivos_queryset():
    return Dispositivo.objects.select_related("provincia", "municipio").order_by(
        "-created_at",
        "nombre_institucion",
    )


def get_dispositivo_or_404(pk):
    return get_object_or_404(get_dispositivos_queryset(), pk=pk)


def save_dispositivo_from_form(form, *, instance=None):
    dispositivo = form.save(commit=False)
    if instance is not None:
        dispositivo.pk = instance.pk
    dispositivo.save()
    return dispositivo


def delete_dispositivo(instance):
    instance.delete()
