# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import (
    Localidad,
    Municipio,
)
from organizaciones.models import Organizacion


@login_required
@require_GET
def load_municipios(request):
    """Carga municipios filtrados por provincia."""
    provincia_id = request.GET.get("provincia_id")
    municipios = Municipio.objects.filter(provincia=provincia_id)
    return JsonResponse(list(municipios.values("id", "nombre")), safe=False)


@login_required
@require_GET
def load_localidad(request):
    """Carga localidades filtradas por municipio."""
    municipio_id = request.GET.get("municipio_id")

    if municipio_id:
        localidades = Localidad.objects.filter(municipio=municipio_id)
    else:
        localidades = Localidad.objects.none()

    return JsonResponse(list(localidades.values("id", "nombre")), safe=False)


@login_required
@require_GET
def load_organizaciones(request):
    """Carga organizaciones con búsqueda para Select2."""
    search = request.GET.get("q", "").strip()
    page = int(request.GET.get("page", 1))
    page_size = 30

    organizaciones = Organizacion.objects.all().order_by("nombre")

    if search:
        organizaciones = organizaciones.filter(nombre__icontains=search)

    # Paginación
    start = (page - 1) * page_size
    end = start + page_size
    total_count = organizaciones.count()
    organizaciones_page = organizaciones[start:end]

    results = [{"id": org.id, "text": org.nombre} for org in organizaciones_page]

    return JsonResponse({"results": results, "pagination": {"more": end < total_count}})


@login_required
def inicio_view(request):
    """Vista para la página de inicio del sistema"""
    return render(request, "inicio.html")


def error_500_view(request):
    return render(request, "500.html")
