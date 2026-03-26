# Crea tus vistas aqui.

# Standard library
import json
import re
import logging
from pathlib import Path

# Third-party
import markdown
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

# First-party (local)
from core.models import (
    FiltroFavorito,
    Localidad,
    Municipio,
    PreferenciaColumnas,
    MontoPrestacionPrograma,
    Programa,
)
from core.forms import MontoPrestacionProgramaForm, ProgramaForm
from core.services.favorite_filters import (
    TTL_CACHE_FILTROS_FAVORITOS,
    clave_cache_filtros_favoritos,
    normalizar_carga,
    obtener_configuracion_seccion,
    obtener_items_obsoletos,
)
from organizaciones.models import Organizacion
from historial.services.historial_service import HistorialService

logger = logging.getLogger(__name__)

CHANGELOG_HEADER_PATTERN = re.compile(
    (
        r"^(?:##\s*Despliegue:\s*(?P<deploy>\d{4}\.\d{2}\.\d{2})"
        r"|#\s*(?:Versión|Vresión)\s+SISOC\s+(?P<release>\d{2}\.\d{2}\.\d{4}))\s*$"
    ),
    flags=re.MULTILINE,
)


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


def _normalizar_columnas(carga):
    if carga is None:
        return None
    if isinstance(carga, str):
        try:
            carga = json.loads(carga)
        except json.JSONDecodeError:
            return None
    if not isinstance(carga, (list, tuple)):
        return None
    columnas = []
    vistos = set()
    for item in carga:
        valor = str(item).strip()
        if not valor or valor in vistos:
            continue
        vistos.add(valor)
        columnas.append(valor)
    return columnas


def _columnas_preferencias_get(request):
    listado = str(request.GET.get("list_key") or "").strip()
    if not listado:
        return JsonResponse({"error": "Listado invalido."}, status=400)

    preferencia = (
        PreferenciaColumnas.objects.filter(usuario=request.user, listado=listado)
        .only("columnas")
        .first()
    )

    columnas = preferencia.columnas if preferencia else []
    return JsonResponse({"list_key": listado, "columns": columnas}, status=200)


def _columnas_preferencias_post(request):
    datos = _parsear_datos_request(request)
    listado = str(datos.get("list_key") or "").strip()
    if not listado:
        return JsonResponse({"error": "Listado invalido."}, status=400)

    reset = str(datos.get("reset") or "").lower() in ("1", "true", "yes")
    if reset:
        PreferenciaColumnas.objects.filter(
            usuario=request.user, listado=listado
        ).delete()
        return JsonResponse({"list_key": listado, "columns": []}, status=200)

    columnas = _normalizar_columnas(datos.get("columns"))
    if columnas is None:
        return JsonResponse({"error": "Columnas invalidas."}, status=400)

    PreferenciaColumnas.objects.update_or_create(
        usuario=request.user,
        listado=listado,
        defaults={"columnas": columnas},
    )
    return JsonResponse({"list_key": listado, "columns": columnas}, status=200)


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


@ensure_csrf_cookie
@login_required
@require_http_methods(["GET", "POST"])
def filtros_favoritos(request):
    """Lista o crea filtros favoritos para el usuario actual."""
    if request.method == "GET":
        return _filtros_favoritos_get(request)

    return _filtros_favoritos_post(request)


@ensure_csrf_cookie
@login_required
@require_http_methods(["GET", "POST"])
def columnas_preferencias(request):
    """Guarda o devuelve preferencias de columnas para el usuario actual."""
    if request.method == "GET":
        return _columnas_preferencias_get(request)

    return _columnas_preferencias_post(request)


@login_required
@require_http_methods(["GET", "DELETE"])
def detalle_filtro_favorito(request, pk):
    """Devuelve o elimina un filtro favorito."""
    favorito = FiltroFavorito.objects.filter(pk=pk, usuario=request.user).first()
    response_data = None
    status_code = 200

    if favorito is None:
        response_data = {"error": "Filtro favorito no encontrado."}
        status_code = 404
    elif request.method == "DELETE":
        seccion = favorito.seccion
        favorito.delete()
        cache.delete(clave_cache_filtros_favoritos(request.user.id, seccion))
        response_data = {"exito": True}
    else:
        seccion = str(request.GET.get("seccion") or favorito.seccion).strip()
        if seccion != favorito.seccion:
            response_data = {"error": "Seccion invalida."}
            status_code = 400
        else:
            configuracion = obtener_configuracion_seccion(seccion)
            if configuracion is None:
                response_data = {"error": "Seccion invalida."}
                status_code = 400
            else:
                carga = normalizar_carga(favorito.filtros)
                if carga is None:
                    response_data = {"error": "Filtros invalidos."}
                    status_code = 400
                else:
                    items_obsoletos = obtener_items_obsoletos(carga, configuracion)
                    if items_obsoletos:
                        response_data = {
                            "error": "El filtro contiene parametros obsoletos.",
                            "items_obsoletos": items_obsoletos,
                        }
                        status_code = 409
                    else:
                        response_data = {
                            "id": favorito.id,
                            "nombre": favorito.nombre,
                            "filtros": carga,
                        }

    return JsonResponse(response_data, status=status_code)


@login_required
def inicio_view(request):
    """Vista para la página de inicio del sistema"""
    return render(request, "inicio.html")


def _extract_first_changelog_version(content):
    """Extrae la primera versión del changelog para formatos nuevos y legacy."""
    match = CHANGELOG_HEADER_PATTERN.search(content)
    if not match:
        return None
    return match.group("deploy") or match.group("release")


def get_current_version():
    """
    Extrae la versión actual del sistema desde CHANGELOG.md.
    Retorna la primera versión encontrada (la más reciente).
    Intenta primero del archivo local, luego desde GitHub.
    """
    changelog_path = Path(settings.BASE_DIR) / "CHANGELOG.md"

    # Intentar leer del archivo local
    try:
        with open(changelog_path, "r", encoding="utf-8") as file:
            content = file.read()
            version = _extract_first_changelog_version(content)
            if version:
                return version
    except (FileNotFoundError, IOError) as e:
        logger.warning(f"No se pudo leer CHANGELOG.md local para versión: {e}")

    # Si falla, intentar obtener desde GitHub
    try:
        response = requests.get(settings.CHANGELOG_GITHUB_URL, timeout=10)
        response.raise_for_status()
        content = response.text
        version = _extract_first_changelog_version(content)
        if version:
            return version
    except requests.RequestException as e:
        logger.error(f"Error al obtener versión desde GitHub: {e}")

    return "Desconocida"


def fetch_changelog_content():
    """
    Obtiene el contenido del CHANGELOG.md.
    Primero intenta leer el archivo local y, si no puede, usa GitHub.
    """
    changelog_path = Path(settings.BASE_DIR) / "CHANGELOG.md"

    # Intentar leer del archivo local primero
    try:
        with open(changelog_path, "r", encoding="utf-8") as file:
            return file.read()
    except (FileNotFoundError, IOError) as e:
        logger.warning(f"No se pudo leer CHANGELOG.md local: {e}")

    # Como fallback, intentar obtener desde GitHub
    try:
        response = requests.get(settings.CHANGELOG_GITHUB_URL, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"No se pudo obtener CHANGELOG.md desde GitHub: {e}")
        return None


def parse_changelog_versions(content):
    """
    Divide el contenido de CHANGELOG.md en bloques individuales por versión.
    Retorna una lista de dicts con claves 'version' y 'html'.
    """
    versions = []
    matches = list(CHANGELOG_HEADER_PATTERN.finditer(content))
    for index, match in enumerate(matches):
        version_date = match.group("deploy") or match.group("release")
        block_start = match.end()
        block_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(content)
        )
        block_content = content[block_start:block_end].strip()
        md_parser = markdown.Markdown(extensions=["extra", "sane_lists"])
        block_html = md_parser.convert(block_content)
        versions.append({"version": version_date, "html": block_html})
    return versions


@login_required
def changelog_view(request):
    """
    Vista para mostrar las novedades del sistema desde CHANGELOG.md.
    El contenido se cachea por 24 horas para evitar lecturas constantes.
    """
    cache_key = "changelog_content"
    cache_timeout = 86400  # 24 horas

    # Intentar obtener desde cache
    cached_data = cache.get(cache_key)

    if cached_data and cached_data.get("versions"):
        versions = cached_data["versions"]
        current_version = cached_data["version"]
    else:
        # Obtener contenido del changelog
        changelog_content = fetch_changelog_content()

        if changelog_content:
            versions = parse_changelog_versions(changelog_content)
            current_version = get_current_version()

            # Evitar cachear respuestas parseadas vacías para no dejar la página en blanco.
            if versions:
                cache.set(
                    cache_key,
                    {"versions": versions, "version": current_version},
                    cache_timeout,
                )
            else:
                logger.warning(
                    "Se leyó CHANGELOG.md pero no se detectaron bloques de versión."
                )
        else:
            versions = None
            current_version = get_current_version()

    context = {
        "versions": versions,
        "current_version": current_version,
        "error": not versions,
    }

    return render(request, "changelog.html", context)


def error_500_view(request):
    return render(request, "500.html")


class MontoPrestacionProgramaListView(LoginRequiredMixin, ListView):
    model = MontoPrestacionPrograma
    template_name = "monto_prestacion_list.html"
    context_object_name = "prestaciones"
    paginate_by = 10

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("usuario_creador", "programa")
            .order_by("id")
        )


class MontoPrestacionProgramaContextMixin:
    @staticmethod
    def _list_url():
        return reverse("montoprestacion_listar")

    def _back_button(self):
        return {
            "url": self._list_url(),
            "text": "Volver",
            "type": "outline-light",
        }

    def _breadcrumb_items(self, actual):
        return [
            {"text": "Monto de Prestaciones", "url": self._list_url()},
            {"text": actual, "active": True},
        ]

    def _form_template_context(self, actual):
        return {
            "breadcrumb_items": self._breadcrumb_items(actual),
            "back_button": self._back_button(),
            "action_buttons": [],
            "hidden_fields_send": [],
            "guardar_otro_send": False,
        }


class MontoPrestacionProgramaCreateView(
    MontoPrestacionProgramaContextMixin, LoginRequiredMixin, CreateView
):
    model = MontoPrestacionPrograma
    form_class = MontoPrestacionProgramaForm
    template_name = "monto_prestacion_form.html"
    success_url = reverse_lazy("montoprestacion_listar")

    def form_valid(self, form):
        with transaction.atomic():
            obj = form.save(commit=False)
            if not getattr(obj, "usuario_creador", None):
                obj.usuario_creador = self.request.user
            obj.save()
            self.object = obj
            HistorialService.registrar_historial(
                accion="Creación de Monto de Prestación",
                instancia=obj,
                diferencias=form.cleaned_data,
            )
        messages.success(self.request, "Monto de Prestación creada correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._form_template_context("Crear Monto de Prestación"))
        return context


class MontoPrestacionProgramaUpdateView(
    MontoPrestacionProgramaContextMixin, LoginRequiredMixin, UpdateView
):
    model = MontoPrestacionPrograma
    form_class = MontoPrestacionProgramaForm
    template_name = "monto_prestacion_form.html"
    success_url = reverse_lazy("montoprestacion_listar")

    def form_valid(self, form):
        with transaction.atomic():
            obj = form.save()
            self.object = obj
            HistorialService.registrar_historial(
                accion="Edición de Monto de Prestación",
                instancia=obj,
                diferencias=form.cleaned_data,
            )
        messages.success(self.request, "Monto de Prestación actualizado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._form_template_context("Editar Monto de Prestación"))
        return context


class MontoPrestacionProgramaDeleteView(
    MontoPrestacionProgramaContextMixin, LoginRequiredMixin, DeleteView
):
    model = MontoPrestacionPrograma
    template_name = "monto_prestacion_confirm_delete.html"
    success_url = reverse_lazy("montoprestacion_listar")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = getattr(self, "object", None) or self.get_object()
        context["breadcrumb_items"] = [
            {"text": "Monto de Prestaciones", "url": self._list_url()},
            {"text": "Eliminar Monto de Prestación", "active": True},
        ]
        context["object_title"] = str(obj)
        context["delete_message"] = (
            "¿Desea eliminar este monto de prestación? Esta acción no se puede deshacer."
        )
        context["cancel_url"] = self._list_url()
        return context

    def form_valid(self, form):
        obj = getattr(self, "object", None) or self.get_object()
        self.object = obj
        with transaction.atomic():
            HistorialService.registrar_historial(
                accion="Eliminación de Prestación",
                instancia=obj,
                diferencias={"programa": getattr(obj, "programa", None)},
            )
            response = super().form_valid(form)
        messages.success(self.request, "Monto de Prestación eliminado correctamente.")
        return response


class MontoPrestacionProgramaDetailView(
    MontoPrestacionProgramaContextMixin, LoginRequiredMixin, DetailView
):
    model = MontoPrestacionPrograma
    template_name = "monto_prestacion_detail.html"
    context_object_name = "prestacion"

    def get_queryset(self):
        return super().get_queryset().select_related("usuario_creador", "programa")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = self._breadcrumb_items("Detalle")
        context["back_button"] = self._back_button()
        context["action_buttons"] = []
        return context


# ============================================================================
# PROGRAMA VIEWS
# ============================================================================

class ProgramaListView(LoginRequiredMixin, ListView):
    model = Programa
    template_name = "programa_list.html"
    context_object_name = "programas"
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().order_by("nombre")


class ProgramaCreateView(LoginRequiredMixin, CreateView):
    model = Programa
    form_class = ProgramaForm
    template_name = "programa_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Programa creado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("programa_detalle", kwargs={"pk": self.object.pk})


class ProgramaDetailView(LoginRequiredMixin, DetailView):
    model = Programa
    template_name = "programa_detail.html"
    context_object_name = "programa"


class ProgramaUpdateView(LoginRequiredMixin, UpdateView):
    model = Programa
    form_class = ProgramaForm
    template_name = "programa_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Programa actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("programa_detalle", kwargs={"pk": self.object.pk})


class ProgramaDeleteView(LoginRequiredMixin, DeleteView):
    model = Programa
    template_name = "programa_confirm_delete.html"
    context_object_name = "programa"
    success_url = reverse_lazy("programa_listar")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Programa eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
