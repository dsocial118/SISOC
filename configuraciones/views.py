from django.http import JsonResponse


from django.shortcuts import render

from configuraciones.models import (
    Localidad,
    Municipio,
)


def load_municipios(request):
    provincia_id = request.GET.get("provincia_id")
    municipios = Municipio.objects.filter(provincia=provincia_id)
    return JsonResponse(list(municipios.values("id", "nombre")), safe=False)


def load_localidad(request):
    municipio_id = request.GET.get("municipio_id")
    departamento_id = request.GET.get("departamento_id")

    if municipio_id:
        localidades = Localidad.objects.filter(municipio=municipio_id)
    else:
        localidades = Localidad.objects.filter(departamento=departamento_id)
    return JsonResponse(list(localidades.values("id", "nombre")), safe=False)


def error_500_view(request):
    return render(request, "500.html")
