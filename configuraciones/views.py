from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from django.shortcuts import render

from usuarios.mixins import PermisosMixin


from configuraciones.models import (
    Asentamiento,
    Departamento,
    Localidad,
    Municipio,
)

# region ############################################################### Secretarías


def load_municipios(request):
    provincia_id = request.GET.get("provincia_id")
    municipios = Municipio.objects.filter(fk_provincia=provincia_id)
    return JsonResponse(list(municipios.values("id", "nombre")), safe=False)


def load_localidad(request):
    municipio_id = request.GET.get("municipio_id")
    departamento_id = request.GET.get("departamento_id")

    if municipio_id:
        localidades = Localidad.objects.filter(fk_municipio=municipio_id)
    else:
        localidades = Localidad.objects.filter(fk_departamento=departamento_id)
    return JsonResponse(list(localidades.values("id", "nombre")), safe=False)


def load_departamento(request):
    provincia_id = request.GET.get("provincia_id")
    departamentos = Departamento.objects.filter(fk_provincia=provincia_id)
    return JsonResponse(list(departamentos.values("id", "nombre")), safe=False)


def load_asentamiento(request):
    municipio_id = request.GET.get("municipio_id")
    departamento_id = request.GET.get("departamento_id")

    if municipio_id:
        asentamientos = Asentamiento.objects.filter(fk_localidad=municipio_id)
    else:
        asentamientos = Asentamiento.objects.filter(fk_departamento=departamento_id)
    return JsonResponse(list(asentamientos.values("id", "nombre")), safe=False)


def error_500_view(request):
    return render(request, "500.html")
