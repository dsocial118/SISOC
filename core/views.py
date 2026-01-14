# Crea tus vistas aqui.
import json

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from core.models import (
    FiltroFavorito,
    Localidad,
    Municipio,
)
from core.services.favorite_filters import (
    TTL_CACHE_FILTROS_FAVORITOS,
    clave_cache_filtros_favoritos,
    normalizar_carga,
    obtener_configuracion_seccion,
    obtener_items_obsoletos,
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
    busqueda = request.GET.get("q", "").strip()
    pagina = int(request.GET.get("page", 1))
    tamano_pagina = 30

    organizaciones = Organizacion.objects.all().order_by("nombre")

    if busqueda:
        organizaciones = organizaciones.filter(nombre__icontains=busqueda)

    # Paginación
    inicio = (pagina - 1) * tamano_pagina
    fin = inicio + tamano_pagina
    total = organizaciones.count()
    organizaciones_pagina = organizaciones[inicio:fin]

    resultados = [{"id": org.id, "text": org.nombre} for org in organizaciones_pagina]

    return JsonResponse({"results": resultados, "pagination": {"more": fin < total}})


def _parsear_datos_request(request):
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    return request.POST


def _filtros_favoritos_get(request):
    seccion = str(request.GET.get("seccion") or "").strip()
    configuracion = obtener_configuracion_seccion(seccion)
    if not seccion or configuracion is None:
        response_data = {"error": "Seccion invalida."}
        status_code = 400
    else:
        clave_cache = clave_cache_filtros_favoritos(request.user.id, seccion)
        refrescar = str(request.GET.get("refrescar") or "") == "1"
        favoritos_cacheados = None if refrescar else cache.get(clave_cache)
        if favoritos_cacheados is None:
            favoritos = (
                FiltroFavorito.objects.filter(usuario=request.user, seccion=seccion)
                .order_by("fecha_creacion")
                .only("id", "nombre", "fecha_creacion")
            )
            favoritos_cacheados = [
                {
                    "id": favorito.id,
                    "nombre": favorito.nombre,
                    "fecha_creacion": favorito.fecha_creacion.isoformat(),
                }
                for favorito in favoritos
            ]
            cache.set(clave_cache, favoritos_cacheados, TTL_CACHE_FILTROS_FAVORITOS)
        response_data = {"seccion": seccion, "favoritos": favoritos_cacheados}
        status_code = 200

    return JsonResponse(response_data, status=status_code)


def _filtros_favoritos_post(request):
    datos = _parsear_datos_request(request)
    seccion = str(datos.get("seccion") or "").strip()
    nombre = str(datos.get("nombre") or "").strip()
    configuracion = obtener_configuracion_seccion(seccion)
    response_data = None
    status_code = 400
    carga = None

    if not seccion or configuracion is None:
        response_data = {"error": "Seccion invalida."}
    elif not nombre:
        response_data = {"error": "El nombre es obligatorio."}
    elif FiltroFavorito.objects.filter(
        usuario=request.user, seccion=seccion, nombre__iexact=nombre
    ).exists():
        response_data = {"error": "El nombre ya existe."}
    else:
        carga = normalizar_carga(datos.get("filtros"))
        if carga is None:
            response_data = {"error": "Filtros invalidos."}
        else:
            items_obsoletos = obtener_items_obsoletos(carga, configuracion)
            if items_obsoletos:
                response_data = {
                    "error": "El filtro contiene parametros obsoletos.",
                    "items_obsoletos": items_obsoletos,
                }
                status_code = 409

    if response_data is None:
        try:
            favorito = FiltroFavorito.objects.create(
                usuario=request.user,
                seccion=seccion,
                nombre=nombre,
                filtros=carga,
            )
        except IntegrityError:
            response_data = {"error": "El nombre ya existe."}
            status_code = 400
        else:
            cache.delete(clave_cache_filtros_favoritos(request.user.id, seccion))
            response_data = {
                "id": favorito.id,
                "nombre": favorito.nombre,
                "fecha_creacion": favorito.fecha_creacion.isoformat(),
                "seccion": seccion,
            }
            status_code = 201

    return JsonResponse(response_data, status=status_code)


@login_required
@require_http_methods(["GET", "POST"])
def filtros_favoritos(request):
    """Lista o crea filtros favoritos para el usuario actual."""
    if request.method == "GET":
        return _filtros_favoritos_get(request)

    return _filtros_favoritos_post(request)


@login_required
@require_http_methods(["GET", "DELETE"])
def detalle_filtro_favorito(request, pk):
    """Devuelve o elimina un filtro favorito."""
    favorito = get_object_or_404(FiltroFavorito, pk=pk, usuario=request.user)

    if request.method == "DELETE":
        seccion = favorito.seccion
        favorito.delete()
        cache.delete(clave_cache_filtros_favoritos(request.user.id, seccion))
        return JsonResponse({"exito": True})

    seccion = str(request.GET.get("seccion") or favorito.seccion).strip()
    if seccion != favorito.seccion:
        return JsonResponse({"error": "Seccion invalida."}, status=400)

    configuracion = obtener_configuracion_seccion(favorito.seccion)
    if configuracion is None:
        return JsonResponse({"error": "Seccion invalida."}, status=400)

    carga = normalizar_carga(favorito.filtros)
    if carga is None:
        return JsonResponse({"error": "Filtros invalidos."}, status=400)

    items_obsoletos = obtener_items_obsoletos(carga, configuracion)
    if items_obsoletos:
        return JsonResponse(
            {
                "error": "El filtro contiene parametros obsoletos.",
                "items_obsoletos": items_obsoletos,
            },
            status=409,
        )

    return JsonResponse(
        {
            "id": favorito.id,
            "nombre": favorito.nombre,
            "filtros": carga,
        }
    )


@login_required
def inicio_view(request):
    """Vista para la página de inicio del sistema"""
    return render(request, "inicio.html")


def error_500_view(request):
    return render(request, "500.html")
