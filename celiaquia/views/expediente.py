import json
import logging
import traceback

from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
)
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.core.paginator import Paginator

from celiaquia.forms import ExpedienteForm, ConfirmarEnvioForm
from celiaquia.models import (
    AsignacionTecnico,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    RevisionTecnico,
    HistorialValidacionTecnica,
)
from ciudadanos.models import Ciudadano
from celiaquia.services.ciudadano_service import CiudadanoService
from celiaquia.services.expediente_service import (
    ExpedienteService,
    _set_estado,
)
from celiaquia.services.importacion_service import (
    ImportacionService,
    validar_edad_responsable,
)
from celiaquia.services.cruce_service import CruceService
from celiaquia.services.cupo_service import CupoService, CupoNoConfigurado
from django.utils import timezone
from django.db import transaction
from core.models import Nacionalidad, Provincia, Localidad

logger = logging.getLogger("django")


def _user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def _is_admin(user) -> bool:
    return user.is_authenticated and user.is_superuser


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _is_provincial(user) -> bool:
    if not user.is_authenticated:
        return False
    try:
        return bool(user.profile.es_usuario_provincial and user.profile.provincia_id)
    except ObjectDoesNotExist:
        return False


def _user_provincia(user):
    try:
        return user.profile.provincia
    except ObjectDoesNotExist:
        return None


def _parse_limit(value, default=None, max_cap=5000):
    if value is None:
        return default
    txt = str(value).strip().lower()
    if txt in ("all", "todos", "0", "none"):
        return None
    try:
        n = int(txt)
        if n <= 0:
            return None
        return min(n, max_cap) if max_cap is not None else n
    except Exception:
        return default


class LocalidadesLookupView(View):
    """Provide a JSON list of localidades filtered by provincia and municipio."""

    def get(self, request):
        user = request.user
        provincia_id = request.GET.get("provincia")
        municipio_id = request.GET.get("municipio")

        localidades = Localidad.objects.select_related("municipio__provincia")

        # Filtrar por provincia del usuario si es provincial
        if _is_provincial(user):
            prov = _user_provincia(user)
            if prov:
                localidades = localidades.filter(municipio__provincia=prov)

        if provincia_id:
            localidades = localidades.filter(municipio__provincia_id=provincia_id)
        if municipio_id:
            localidades = localidades.filter(municipio_id=municipio_id)

        data = [
            {
                "provincia_id": loc.municipio.provincia_id if loc.municipio else None,
                "provincia_nombre": (
                    loc.municipio.provincia.nombre
                    if loc.municipio and loc.municipio.provincia
                    else None
                ),
                "municipio_id": loc.municipio_id,
                "municipio_nombre": loc.municipio.nombre if loc.municipio else None,
                "localidad_id": loc.id,
                "localidad_nombre": loc.nombre,
            }
            for loc in localidades.order_by(
                "municipio__provincia__nombre", "municipio__nombre", "nombre"
            )
        ]
        return JsonResponse(data, safe=False)


class ExpedienteListView(ListView):
    model = Expediente
    template_name = "celiaquia/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 20

    def get_paginate_by(self, queryset):
        return None

    def get_queryset(self):
        user = self.request.user
        qs = (
            Expediente.objects.select_related(
                "estado",
                "usuario_provincia__profile__provincia",
            )
            .prefetch_related("asignaciones_tecnicos__tecnico")
            .annotate(
                legajos_subsanar_count=Count(
                    "expediente_ciudadanos",
                    filter=Q(expediente_ciudadanos__revision_tecnico="SUBSANAR"),
                )
            )
            .only(
                "id",
                "fecha_creacion",
                "estado__nombre",
                "usuario_provincia_id",
                "usuario_provincia__profile__id",
                "usuario_provincia__profile__provincia_id",
                "usuario_provincia__profile__provincia__id",
                "usuario_provincia__profile__provincia__nombre",
                "numero_expediente",
            )
        )
        if _is_admin(user):
            qs = qs.order_by("-fecha_creacion")
        elif _user_in_group(user, "CoordinadorCeliaquia"):
            qs = qs.filter(
                estado__nombre__in=["CONFIRMACION_DE_ENVIO", "RECEPCIONADO", "ASIGNADO"]
            ).order_by("-fecha_creacion")
        elif _user_in_group(user, "TecnicoCeliaquia"):
            qs = (
                qs.filter(asignaciones_tecnicos__tecnico=user)
                .distinct()
                .order_by("-fecha_creacion")
            )
        elif _is_provincial(user):
            prov = _user_provincia(user)
            qs = qs.filter(usuario_provincia__profile__provincia=prov).order_by(
                "-fecha_creacion"
            )
        else:
            qs = qs.filter(usuario_provincia=user).order_by("-fecha_creacion")

        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            qs = qs.filter(
                Q(id__icontains=search_query)
                | Q(numero_expediente__icontains=search_query)
                | Q(estado__nombre__icontains=search_query)
                | Q(
                    usuario_provincia__profile__provincia__nombre__icontains=search_query
                )
                | Q(asignaciones_tecnicos__tecnico__first_name__icontains=search_query)
                | Q(asignaciones_tecnicos__tecnico__last_name__icontains=search_query)
                | Q(asignaciones_tecnicos__tecnico__username__icontains=search_query)
            ).distinct()

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["tecnicos"] = []
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            ctx["tecnicos"] = User.objects.filter(
                groups__name="TecnicoCeliaquia"
            ).order_by("last_name", "first_name")
        return ctx


@method_decorator(csrf_protect, name="dispatch")
class ProcesarExpedienteView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            result = ExpedienteService.procesar_expediente(expediente, user)

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "creados": result.get("creados", 0),
                        "errores": result.get("errores", 0),
                        "excluidos": result.get("excluidos", 0),
                        "excluidos_detalle": result.get("excluidos_detalle", []),
                    }
                )

            messages.success(
                request,
                f"Importación completada. Creados: {result.get('creados', 0)} — Errores: {result.get('errores', 0)}.",
            )

            excluidos_count = result.get("excluidos", 0)
            if excluidos_count:
                det = result.get("excluidos_detalle", [])
                preview = []
                for d in det[:10]:
                    doc = d.get("documento", "")
                    ape = d.get("apellido", "")
                    nom = d.get("nombre", "")
                    estado = d.get("estado_programa") or d.get("motivo") or "-"
                    expid = d.get("expediente_origen_id", "-")
                    preview.append(f"• {doc} — {ape}, {nom} ({estado}) — Exp #{expid}")

                extra = ""
                if len(det) > 10:
                    extra = f"<br>… y {len(det) - 10} más."

                # Escapar contenido para prevenir XSS
                preview_escaped = [escape(p) for p in preview]
                extra_escaped = escape(extra) if extra else ""
                html = (
                    f"Se excluyeron {excluidos_count} registros porque ya están en otro expediente:"
                    f"<br>{'<br>'.join(preview_escaped)}{extra_escaped}"
                )
                messages.warning(request, html)

            return redirect("expediente_detail", pk=pk)

        except ValidationError as ve:
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": escape(str(ve))}, status=400
                )
            messages.error(request, f"Error de validación: {escape(str(ve))}")
            return redirect("expediente_detail", pk=pk)
        except Exception as e:
            tb = traceback.format_exc()
            logging.error("Error al procesar expediente %s:\n%s", pk, tb)
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": escape(str(e))}, status=500
                )
            messages.error(request, "Error inesperado al procesar el expediente.")
            return redirect("expediente_detail", pk=pk)


class CrearLegajosView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            payload = json.loads(request.body)
            rows = payload.get("rows", [])
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON inválido.")

        estado_inicial, _ = EstadoLegajo.objects.get_or_create(
            nombre="DOCUMENTO_PENDIENTE"
        )
        creados = existentes = 0
        for datos in rows:
            ciudadano = CiudadanoService.get_or_create_ciudadano(datos, user)
            _, was_created = ExpedienteCiudadano.objects.get_or_create(
                expediente=expediente,
                ciudadano=ciudadano,
                defaults={"estado": estado_inicial},
            )
            if was_created:
                creados += 1
            else:
                existentes += 1
        return JsonResponse({"creados": creados, "existentes": existentes})


class ExpedientePlantillaExcelView(View):
    """Genera un archivo de Excel vacío con los campos requeridos para un expediente."""

    def get(self, request, *args, **kwargs):
        content = ImportacionService.generar_plantilla_excel()
        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="plantilla_expediente.xlsx"'
        )
        return response


@method_decorator(csrf_protect, name="dispatch")
class ExpedientePreviewExcelView(View):
    def post(self, request, *args, **kwargs):
        logger.debug("PREVIEW: %s %s", request.method, request.get_full_path())
        archivo = request.FILES.get("excel_masivo")
        if not archivo:
            return JsonResponse({"error": "No se recibió ningún archivo."}, status=400)

        raw_limit = request.POST.get("limit") or request.GET.get("limit")
        max_rows = _parse_limit(raw_limit, default=None, max_cap=5000)

        try:
            preview = ImportacionService.preview_excel(archivo, max_rows=max_rows)
            return JsonResponse(preview)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception:
            tb = traceback.format_exc()
            logger.error("PREVIEW error:\n%s", tb)
            return JsonResponse({"error": "Error inesperado al procesar."}, status=500)


class ExpedienteCreateView(CreateView):
    """Formulario para la creación de expedientes provinciales."""

    model = Expediente
    form_class = ExpedienteForm
    template_name = "celiaquia/expediente_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Filtrar provincias según el usuario
        if _is_provincial(user):
            # Usuario provincial: solo su provincia
            prov = _user_provincia(user)
            ctx["provincias"] = [prov] if prov else []
        else:
            # Admin/Coordinador: todas las provincias
            ctx["provincias"] = Provincia.objects.order_by("nombre")
        return ctx

    def form_valid(self, form):
        expediente = ExpedienteService.create_expediente(
            usuario_provincia=self.request.user,
            datos_metadatos=form.cleaned_data,
            excel_masivo=form.cleaned_data["excel_masivo"],
        )
        messages.success(self.request, "Expediente creado correctamente.")
        return redirect("expediente_detail", pk=expediente.pk)


class ExpedienteDetailView(DetailView):
    """Detalle del expediente con información relacionada."""

    model = Expediente
    template_name = "celiaquia/expediente_detail.html"
    context_object_name = "expediente"

    def get_queryset(self):
        user = self.request.user
        base = Expediente.objects.select_related(
            "estado", "usuario_modificador", "usuario_provincia"
        ).prefetch_related(
            "expediente_ciudadanos__ciudadano",
            "expediente_ciudadanos__estado",
            "asignaciones_tecnicos__tecnico",
        )
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            return base
        if _user_in_group(user, "TecnicoCeliaquia"):
            return base.filter(asignaciones_tecnicos__tecnico=user)
        if _is_provincial(user):
            prov = _user_provincia(user)
            return base.filter(usuario_provincia__profile__provincia=prov)
        return base.filter(usuario_provincia=user)

    def get_context_data(self, **kwargs):
        """Arma el contexto con métricas y paginación del historial."""

        ctx = super().get_context_data(**kwargs)
        expediente = self.object
        user = self.request.user

        preview = preview_error = None
        preview_limit_actual = None

        q = expediente.expediente_ciudadanos.select_related("ciudadano", "estado")
        counts = q.aggregate(
            c_aceptados=Count(
                "id",
                filter=Q(revision_tecnico="APROBADO", resultado_sintys="MATCH"),
            ),
            c_rech_tecnico=Count("id", filter=Q(revision_tecnico="RECHAZADO")),
            c_rech_sintys=Count(
                "id",
                filter=Q(revision_tecnico="APROBADO", resultado_sintys="NO_MATCH"),
            ),
            c_subsanar=Count("id", filter=Q(revision_tecnico=RevisionTecnico.SUBSANAR)),
        )
        ctx["hay_subsanar"] = counts["c_subsanar"] > 0
        ctx["legajos_aceptados"] = q.filter(
            revision_tecnico="APROBADO", resultado_sintys="MATCH"
        )
        ctx["legajos_rech_tecnico"] = q.filter(revision_tecnico="RECHAZADO")
        ctx["legajos_rech_sintys"] = q.filter(
            revision_tecnico="APROBADO", resultado_sintys="NO_MATCH"
        )
        ctx["legajos_subsanar"] = q.filter(revision_tecnico=RevisionTecnico.SUBSANAR)

        # Enriquecer legajos con informacion de tipo (hijo/responsable)
        from celiaquia.services.legajo_service import LegajoService
        from celiaquia.services.familia_service import FamiliaService

        legajos_enriquecidos = []
        legajos_list = list(q.all())
        legajos_por_ciudadano = {}
        ciudadanos_ids = [leg.ciudadano_id for leg in legajos_list]
        responsables_ids = set()
        if ciudadanos_ids:
            try:
                responsables_ids = FamiliaService.obtener_ids_responsables(
                    ciudadanos_ids
                )
            except Exception as exc:
                logger.warning(
                    "No se pudo resolver responsables para expediente %s: %s",
                    expediente.id,
                    exc,
                )

        # Enriquecer legajos con información de responsable/hijo
        responsables_legajos = []
        hijos_por_responsable = {}
        hijos_sin_responsable = []

        for legajo in legajos_list:
            legajo.es_responsable = LegajoService._es_responsable(
                legajo.ciudadano, responsables_ids
            )
            hijos_list = []
            # Buscar hijos si es responsable O si el rol es beneficiario_y_responsable
            if (
                legajo.es_responsable
                or legajo.rol == ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
            ):
                hijos_list = FamiliaService.obtener_hijos_a_cargo(
                    legajo.ciudadano.id, expediente
                )

            # Determinar tipo de legajo segun los roles:
            # - Responsable y Beneficiario: tiene hijos a cargo en el expediente.
            # - Responsable: es responsable pero sin hijos a cargo en este expediente.
            # - Beneficiario: no es responsable.
            if legajo.es_responsable and hijos_list:
                legajo.tipo_legajo = "Responsable y Beneficiario"
            elif legajo.es_responsable:
                legajo.tipo_legajo = "Responsable"
            else:
                legajo.tipo_legajo = "Beneficiario"

            legajo.archivos_requeridos = (
                LegajoService.get_archivos_requeridos_por_legajo(
                    legajo, responsables_ids
                )
            )

            if (
                legajo.es_responsable
                or legajo.rol == ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
            ):
                legajo.hijos_a_cargo = hijos_list
                # Verificar si también es hijo de alguien
                legajo.responsable_id = FamiliaService.obtener_responsable_de_hijo(
                    legajo.ciudadano.id
                )
                responsables_legajos.append(legajo)
                # Si tiene responsable, agregarlo también a hijos_por_responsable
                if legajo.responsable_id:
                    if legajo.responsable_id not in hijos_por_responsable:
                        hijos_por_responsable[legajo.responsable_id] = []
                    hijos_por_responsable[legajo.responsable_id].append(legajo)
            else:
                legajo.hijos_a_cargo = []
                legajo.responsable_id = FamiliaService.obtener_responsable_de_hijo(
                    legajo.ciudadano.id
                )
                if legajo.responsable_id:
                    if legajo.responsable_id not in hijos_por_responsable:
                        hijos_por_responsable[legajo.responsable_id] = []
                    hijos_por_responsable[legajo.responsable_id].append(legajo)
                else:
                    hijos_sin_responsable.append(legajo)

            legajos_por_ciudadano[legajo.ciudadano_id] = legajo

        # Ordenar: construir árbol jerárquico completo
        agregados = set()

        def agregar_con_descendientes(legajo):
            """Agrega un legajo y todos sus descendientes recursivamente"""
            if legajo.ciudadano_id in agregados:
                return
            agregados.add(legajo.ciudadano_id)
            legajos_enriquecidos.append(legajo)
            # Agregar hijos de este legajo
            hijos = hijos_por_responsable.get(legajo.ciudadano_id, [])
            for hijo in hijos:
                agregar_con_descendientes(hijo)

        # Encontrar raíces (responsables que no son hijos de nadie)
        raices = []
        for responsable in responsables_legajos:
            if responsable.responsable_id is None:
                raices.append(responsable)

        # Agregar cada raíz con sus descendientes
        for raiz in raices:
            agregar_con_descendientes(raiz)

        # Agregar responsables que no fueron agregados (tienen responsable pero también son responsables)
        for responsable in responsables_legajos:
            if responsable.ciudadano_id not in agregados:
                agregar_con_descendientes(responsable)

        # Agregar hijos sin responsable al final
        legajos_enriquecidos.extend(hijos_sin_responsable)

        faltantes_list = LegajoService.faltantes_archivos(expediente)
        # Obtener estructura familiar completa
        estructura_familiar = FamiliaService.obtener_estructura_familiar_expediente(
            expediente
        )

        # Enriquecer estructura familiar con referencia a legajos
        for info in estructura_familiar.get("responsables", {}).values():
            for hijo in info.get("hijos", []):
                hijo.legajo_relacionado = legajos_por_ciudadano.get(hijo.id)

        ctx["legajos_enriquecidos"] = legajos_enriquecidos
        ctx["estructura_familiar"] = estructura_familiar

        ctx["c_aceptados"] = counts["c_aceptados"]
        ctx["c_rech_tecnico"] = counts["c_rech_tecnico"]
        ctx["c_rech_sintys"] = counts["c_rech_sintys"]
        ctx["c_subsanar"] = counts["c_subsanar"]

        if expediente.estado.nombre == "CREADO" and expediente.excel_masivo:
            raw_limit = self.request.GET.get("preview_limit")
            max_rows = _parse_limit(raw_limit, default=None, max_cap=5000)
            preview_limit_actual = (
                raw_limit if raw_limit is not None else str(max_rows or "all")
            )
            try:
                preview = ImportacionService.preview_excel(
                    expediente.excel_masivo, max_rows=max_rows
                )
            except Exception as e:
                preview_error = str(e)

        preview_limit_opciones = ["5", "10", "20", "50", "100", "all"]

        tecnicos = []
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            tecnicos = User.objects.filter(groups__name="TecnicoCeliaquia").order_by(
                "last_name", "first_name"
            )

        faltan_archivos = expediente.expediente_ciudadanos.filter(
            Q(archivo2__isnull=True) | Q(archivo3__isnull=True)
        ).exists()

        # Cupo: usar propiedad expediente.provincia (puede ser None)
        cupo = None
        cupo_metrics = None
        cupo_error = None
        prov = getattr(expediente, "provincia", None)
        if prov:
            try:
                cupo_metrics = CupoService.metrics_por_provincia(prov)
                cupo = cupo_metrics
            except CupoNoConfigurado:
                cupo_error = "La provincia no tiene cupo configurado."
        else:
            cupo_error = "No se pudo determinar la provincia del expediente."

        fuera_count = expediente.expediente_ciudadanos.filter(
            estado_cupo="FUERA"
        ).count()
        ctx["fuera_de_cupo"] = q.filter(estado_cupo="FUERA")

        historial = expediente.historial.select_related(
            "estado_anterior", "estado_nuevo", "usuario"
        )
        ctx["historial_page_obj"] = Paginator(historial, 5).get_page(
            self.request.GET.get("historial_page")
        )

        # Obtener registros erróneos
        registros_erroneos = expediente.registros_erroneos.filter(
            procesado=False
        ).order_by("fila_excel")

        # Datos para desplegables en registros erróneos
        from core.models import Sexo, Municipio, Localidad

        sexos = Sexo.objects.all()
        nacionalidades = [
            {"id": nac.id, "nombre": nac.nacionalidad}
            for nac in Nacionalidad.objects.all().order_by("nacionalidad")
        ]
        municipios = []
        localidades = []

        if prov:
            municipios = Municipio.objects.filter(provincia=prov).order_by("nombre")
            localidades = (
                Localidad.objects.filter(municipio__provincia=prov)
                .select_related("municipio")
                .order_by("municipio__nombre", "nombre")
            )

        ctx.update(
            {
                "legajos": legajos_enriquecidos,
                "registros_erroneos": registros_erroneos,
                "sexos": sexos,
                "nacionalidades": nacionalidades,
                "municipios": municipios,
                "localidades": localidades,
                "confirm_form": ConfirmarEnvioForm(),
                "preview": preview,
                "preview_error": preview_error,
                "preview_limit_actual": str(preview_limit_actual or "5").lower(),
                "preview_limit_opciones": preview_limit_opciones,
                "tecnicos": tecnicos,
                "faltan_archivos": faltan_archivos,
                "faltantes_archivos_detalle": faltantes_list,
                "cupo": cupo,  # para el template actual
                "cupo_metrics": cupo_metrics,  # compat si lo usas en JS/otros templates
                "cupo_error": cupo_error,
                "fuera_count": fuera_count,
                "total_responsables": len(estructura_familiar.get("responsables", {})),
                "total_hijos_sin_responsable": len(
                    estructura_familiar.get("hijos_sin_responsable", [])
                ),
            }
        )
        return ctx


class ExpedienteImportView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            result = ImportacionService.importar_legajos_desde_excel(
                expediente, expediente.excel_masivo, user
            )
            detalles = result.get("detalles_errores") or []
            resumen = ""
            if detalles:
                resumen = "; ".join(
                    f"Fila {d.get('fila')}: {d.get('error')}" for d in detalles[:5]
                )
                if len(detalles) > 5:
                    resumen += " (ver logs para más detalles)"

            mensaje_principal = f"Importación: {result['validos']} válidos, {result['errores']} errores."
            if resumen:
                mensaje_principal += f" Detalles: {resumen}"
            messages.success(request, mensaje_principal)

            if detalles:
                messages.error(request, f"Errores detectados: {resumen}")

            advertencias = result.get("warnings") or []
            if advertencias:
                resumen_warn = "; ".join(
                    f"Fila {w.get('fila')}: {w.get('detalle')}"
                    for w in advertencias[:5]
                )
                if len(advertencias) > 5:
                    resumen_warn += " (se muestran las primeras 5)"
                messages.warning(request, f"Advertencias: {resumen_warn}")
        except ValidationError as ve:
            messages.error(request, f"Error de validación: {ve.message}")
        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")
        return redirect("expediente_detail", pk=pk)


class ExpedienteConfirmView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        from celiaquia.models import RegistroErroneo

        registros_erroneos = RegistroErroneo.objects.filter(
            expediente=expediente, procesado=False
        )
        if registros_erroneos.exists():
            msg = f"No se puede enviar: hay {registros_erroneos.count()} registros con errores pendientes de corrección."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        try:
            result = ExpedienteService.confirmar_envio(expediente, user)
            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Expediente enviado a Subsecretaría.",
                        "validos": result["validos"],
                        "errores": result["errores"],
                    }
                )
            messages.success(
                request,
                f"Expediente enviado a Subsecretaría. Legajos: {result['validos']} (sin errores).",
            )
        except ValidationError as ve:
            error_msg = str(ve.message) if hasattr(ve, "message") else str(ve)
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": escape(error_msg)}, status=400
                )
            messages.error(request, f"Error al confirmar: {escape(error_msg)}")
        except Exception as e:
            logger.error("Error inesperado al confirmar envío: %s", e, exc_info=True)
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": escape(str(e))}, status=500
                )
            messages.error(request, f"Error inesperado: {escape(str(e))}")
        return redirect("expediente_detail", pk=pk)


class ExpedienteUpdateView(UpdateView):
    model = Expediente
    form_class = ExpedienteForm
    template_name = "celiaquia/expediente_form.html"

    def get_success_url(self):
        return reverse_lazy("expediente_detail", args=[self.object.pk])


class RecepcionarExpedienteView(View):
    def post(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": "Permiso denegado."}, status=403
                )
            raise PermissionDenied(
                "No tiene permisos para recepcionar este expediente."
            )

        expediente = get_object_or_404(Expediente, pk=pk)
        if expediente.estado.nombre != "CONFIRMACION_DE_ENVIO":
            msg = "El expediente no está pendiente de recepción."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.warning(request, msg)
            return redirect("expediente_detail", pk=pk)

        _set_estado(expediente, "RECEPCIONADO", user)

        if _is_ajax(request):
            return JsonResponse(
                {"success": True, "message": "Recepcionado correctamente."}
            )
        messages.success(
            request,
            "Expediente recepcionado correctamente. Ahora puede asignar un técnico.",
        )
        return redirect("expediente_detail", pk=pk)

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])


class AsignarTecnicoView(View):
    def post(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": "Permiso denegado."}, status=403
                )
            raise PermissionDenied("No tiene permisos para asignar técnico.")

        expediente = get_object_or_404(Expediente, pk=pk)

        tecnico_id = request.POST.get("tecnico_id")
        if not tecnico_id:
            msg = "No se seleccionó ningún técnico."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        tecnico_qs = User.objects.filter(groups__name="TecnicoCeliaquia")
        tecnico = get_object_or_404(tecnico_qs, pk=tecnico_id)

        estado_actual = expediente.estado.nombre
        if estado_actual not in ("RECEPCIONADO", "ASIGNADO"):
            msg = "Primero debe recepcionar el expediente."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        AsignacionTecnico.objects.get_or_create(
            expediente=expediente,
            tecnico=tecnico,
        )

        _set_estado(expediente, "ASIGNADO", user)

        if _is_ajax(request):
            return JsonResponse(
                {
                    "success": True,
                    "message": "Técnico asignado correctamente. Estado: ASIGNADO.",
                }
            )
        messages.success(
            request,
            f"Técnico {tecnico.get_full_name() or tecnico.username} asignado correctamente. Estado: ASIGNADO.",
        )
        return redirect("expediente_detail", pk=pk)

    def delete(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        expediente = get_object_or_404(Expediente, pk=pk)
        tecnico_id = request.GET.get("tecnico_id")

        if not tecnico_id:
            return JsonResponse(
                {"success": False, "error": "ID de técnico requerido."}, status=400
            )

        try:
            asignacion = AsignacionTecnico.objects.get(
                expediente=expediente, tecnico_id=tecnico_id
            )
            asignacion.delete()
            return JsonResponse(
                {"success": True, "message": "Técnico removido correctamente."}
            )
        except AsignacionTecnico.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Asignación no encontrada."}, status=404
            )


class ExpedienteNominaSintysExportView(View):
    """Descarga la nómina del expediente en formato compatible con Sintys."""

    def get(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk)
        content = CruceService.generar_nomina_sintys_excel(expediente)
        filename = f"nomina_sintys_{expediente.pk}.xlsx"
        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class SubirCruceExcelView(View):
    def post(self, request, pk):
        user = self.request.user

        if not (_is_admin(user) or _user_in_group(user, "TecnicoCeliaquia")):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        expediente = get_object_or_404(Expediente, pk=pk)

        if not _is_admin(user):
            # Usar prefetch para evitar query adicional
            tecnicos_ids = [
                t.tecnico_id for t in expediente.asignaciones_tecnicos.all()
            ]
            if user.id not in tecnicos_ids:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No sos un técnico asignado a este expediente.",
                    },
                    status=403,
                )

        archivo = request.FILES.get("archivo")
        if not archivo:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Debe adjuntar un Excel con columna 'documento'.",
                },
                status=400,
            )

        try:
            resumen = CruceService.procesar_cruce_por_cuit(expediente, archivo, user)
            return JsonResponse(
                {
                    "success": True,
                    "message": "Cruce finalizado. Se generó el PRD del expediente.",
                    "resumen": resumen,
                }
            )
        except ValidationError as ve:
            return JsonResponse(
                {"success": False, "error": escape(str(ve))}, status=400
            )
        except Exception as e:
            logger.error("Error en cruce por CUIT: %s", e, exc_info=True)
            return JsonResponse({"success": False, "error": escape(str(e))}, status=500)

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])


@method_decorator(csrf_protect, name="dispatch")
class RevisarLegajoView(View):
    def post(self, request, pk, legajo_id):
        user = request.user
        expediente = get_object_or_404(Expediente, pk=pk)

        es_admin = _is_admin(user)
        es_tecnico = _user_in_group(user, "TecnicoCeliaquia")
        es_coord = _user_in_group(user, "CoordinadorCeliaquia")

        # Permisos: admin, técnico o coordinador
        if not (es_admin or es_tecnico or es_coord):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        # Técnicos deben estar asignados; coordinadores quedan exceptuados
        if not (es_admin or es_coord):
            # Usar prefetch para evitar query adicional
            tecnicos_ids = [
                t.tecnico_id for t in expediente.asignaciones_tecnicos.all()
            ]
            if user.id not in tecnicos_ids:
                return JsonResponse(
                    {"success": False, "error": "No sos un técnico asignado."},
                    status=403,
                )

        leg = get_object_or_404(
            ExpedienteCiudadano, pk=legajo_id, expediente=expediente
        )

        accion = (request.POST.get("accion") or "").upper()
        if accion not in ("APROBAR", "RECHAZAR", "SUBSANAR", "ELIMINAR"):
            return JsonResponse(
                {"success": False, "error": "Acción inválida."}, status=400
            )

        # Si RECHAZAR / SUBSANAR y estaba dentro de cupo -> liberar
        if accion in ("RECHAZAR", "SUBSANAR") and leg.estado_cupo == "DENTRO":
            try:
                CupoService.liberar_slot(
                    legajo=leg,
                    usuario=user,
                    motivo=f"Salida del cupo por {accion.lower()} técnico en expediente",
                )
                leg.estado_cupo = "NO_EVAL"
                leg.es_titular_activo = False
            except Exception as e:
                logger.error(
                    "Error al liberar cupo para legajo %s: %s", leg.pk, e, exc_info=True
                )

        if accion == "APROBAR":
            estado_anterior = leg.revision_tecnico
            leg.revision_tecnico = "APROBADO"
            leg.save(
                update_fields=[
                    "revision_tecnico",
                    "modificado_en",
                    "estado_cupo",
                    "es_titular_activo",
                ]
            )

            HistorialValidacionTecnica.objects.create(
                legajo=leg,
                estado_anterior=estado_anterior,
                estado_nuevo="APROBADO",
                usuario=user,
                motivo=None,
            )

            return JsonResponse(
                {
                    "success": True,
                    "estado": leg.revision_tecnico,
                    "cupo_liberado": False,
                }
            )

        if accion == "RECHAZAR":
            estado_anterior = leg.revision_tecnico
            leg.revision_tecnico = "RECHAZADO"
            leg.save(
                update_fields=[
                    "revision_tecnico",
                    "modificado_en",
                    "estado_cupo",
                    "es_titular_activo",
                ]
            )

            HistorialValidacionTecnica.objects.create(
                legajo=leg,
                estado_anterior=estado_anterior,
                estado_nuevo="RECHAZADO",
                usuario=user,
                motivo=None,
            )

            return JsonResponse(
                {"success": True, "estado": leg.revision_tecnico, "cupo_liberado": True}
            )

        # ELIMINAR - Solo coordinadores
        if accion == "ELIMINAR":
            if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Solo coordinadores pueden eliminar legajos.",
                    },
                    status=403,
                )

            try:
                # Liberar cupo si estaba ocupado
                if leg.estado_cupo == "DENTRO":
                    try:
                        CupoService.liberar_slot(
                            legajo=leg,
                            usuario=user,
                            motivo="Eliminación de legajo del expediente",
                        )
                    except Exception as e:
                        logger.error(
                            "Error al liberar cupo para legajo %s: %s",
                            leg.pk,
                            e,
                            exc_info=True,
                        )

                leg.delete()
                return JsonResponse(
                    {"success": True, "message": "Legajo eliminado correctamente."}
                )
            except Exception as e:
                logger.error(
                    "Error al eliminar legajo %s: %s", leg.pk, e, exc_info=True
                )
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Ocurrió un error al eliminar el legajo. Inténtelo nuevamente más tarde.",
                    },
                    status=500,
                )

        # SUBSANAR
        motivo = (request.POST.get("motivo") or "").strip()
        if not motivo:
            return JsonResponse(
                {"success": False, "error": "Debe indicar un motivo de subsanación."},
                status=400,
            )

        estado_anterior = leg.revision_tecnico
        leg.revision_tecnico = RevisionTecnico.SUBSANAR
        leg.subsanacion_motivo = motivo[:500]
        leg.subsanacion_solicitada_en = timezone.now()
        leg.subsanacion_usuario = user
        leg.save(
            update_fields=[
                "revision_tecnico",
                "subsanacion_motivo",
                "subsanacion_solicitada_en",
                "subsanacion_usuario",
                "modificado_en",
                "estado_cupo",
                "es_titular_activo",
            ]
        )

        HistorialValidacionTecnica.objects.create(
            legajo=leg,
            estado_anterior=estado_anterior,
            estado_nuevo=RevisionTecnico.SUBSANAR,
            usuario=user,
            motivo=motivo[:500],
        )

        return JsonResponse(
            {
                "success": True,
                "estado": str(RevisionTecnico.SUBSANAR),
                "cupo_liberado": True,
            }
        )


class ActualizarRegistroErroneoView(View):
    def post(self, request, pk, registro_id):
        user = request.user
        expediente = get_object_or_404(Expediente, pk=pk)

        if not (_is_admin(user) or _is_provincial(user)):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        from celiaquia.models import RegistroErroneo

        registro = get_object_or_404(
            RegistroErroneo, pk=registro_id, expediente=expediente
        )

        try:
            datos_actualizados = json.loads(request.body)
            # Limpiar valores vacíos
            datos_limpios = {k: v for k, v in datos_actualizados.items() if v}
            registro.datos_raw = datos_limpios
            registro.save(update_fields=["datos_raw"])

            return JsonResponse(
                {"success": True, "message": "Registro actualizado correctamente."}
            )
        except Exception as e:
            logger.error("Error actualizando registro erróneo: %s", e, exc_info=True)
            return JsonResponse(
                {
                    "success": False,
                    "error": "Ocurrió un error interno al actualizar el registro.",
                },
                status=500,
            )


class ReprocesarRegistrosErroneosView(View):
    @transaction.atomic
    def post(self, request, pk):
        user = request.user
        expediente = get_object_or_404(Expediente, pk=pk)

        if not (_is_admin(user) or _is_provincial(user)):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        from celiaquia.models import RegistroErroneo, EstadoLegajo
        from celiaquia.services.ciudadano_service import CiudadanoService

        registros = expediente.registros_erroneos.filter(procesado=False)

        if not registros.exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "No hay registros erróneos para reprocesar.",
                },
                status=400,
            )

        creados = 0
        errores = 0
        errores_detalle = []
        relaciones_crear = []

        estado_inicial = EstadoLegajo.objects.get(nombre="DOCUMENTO_PENDIENTE")

        # Obtener provincia del usuario
        provincia_id = None
        try:
            if user.profile and user.profile.provincia_id:
                provincia_id = user.profile.provincia_id
        except Exception:
            pass

        if not provincia_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se pudo determinar la provincia del usuario.",
                },
                status=400,
            )

        for registro in registros:
            try:
                datos = registro.datos_raw.copy()
                campos_obligatorios = [
                    "apellido",
                    "nombre",
                    "documento",
                    "fecha_nacimiento",
                    "sexo",
                    "nacionalidad",
                    "telefono",
                    "email",
                    "calle",
                    "altura",
                    "municipio",
                    "localidad",
                ]
                campos_faltantes = [c for c in campos_obligatorios if not datos.get(c)]
                if campos_faltantes:
                    raise ValidationError(
                        f"Faltan campos obligatorios: {', '.join(campos_faltantes)}"
                    )
                telefono = str(datos.get("telefono", "")).strip()
                if len(telefono) < 8:
                    raise ValidationError("Telefono debe tener al menos 8 digitos")
                tiene_responsable = any(
                    [
                        datos.get("apellido_responsable"),
                        datos.get("nombre_responsable"),
                        datos.get("documento_responsable"),
                    ]
                )
                if tiene_responsable and not datos.get("email_responsable"):
                    raise ValidationError(
                        "Email del responsable es obligatorio si hay datos de responsable"
                    )
                # Agregar provincia del usuario
                datos["provincia"] = provincia_id

                # Convertir fecha de DD/MM/YYYY a objeto date si es necesario
                if "fecha_nacimiento" in datos and isinstance(
                    datos["fecha_nacimiento"], str
                ):
                    from datetime import datetime

                    try:
                        # Intentar formato DD/MM/YYYY
                        fecha_obj = datetime.strptime(
                            datos["fecha_nacimiento"], "%d/%m/%Y"
                        ).date()
                        datos["fecha_nacimiento"] = fecha_obj
                    except ValueError:
                        try:
                            # Intentar formato YYYY-MM-DD
                            fecha_obj = datetime.strptime(
                                datos["fecha_nacimiento"], "%Y-%m-%d"
                            ).date()
                            datos["fecha_nacimiento"] = fecha_obj
                        except ValueError:
                            pass

                # Intentar crear el ciudadano y legajo
                ciudadano = CiudadanoService.get_or_create_ciudadano(
                    datos=datos,
                    usuario=user,
                    expediente=expediente,
                )

                if ciudadano and ciudadano.pk:
                    # Detectar rol del beneficiario
                    doc_beneficiario = datos.get("documento")
                    doc_responsable = datos.get("documento_responsable")
                    tiene_responsable = any(
                        [
                            datos.get("apellido_responsable"),
                            datos.get("nombre_responsable"),
                            datos.get("documento_responsable"),
                        ]
                    )

                    es_mismo_documento = (
                        tiene_responsable
                        and doc_responsable
                        and str(doc_responsable).strip()
                        == str(doc_beneficiario).strip()
                    )

                    if es_mismo_documento:
                        rol_beneficiario = (
                            ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
                        )
                    else:
                        rol_beneficiario = ExpedienteCiudadano.ROLE_BENEFICIARIO

                    # Obtener o crear legajo del hijo/beneficiario CON ROL
                    legajo, created = ExpedienteCiudadano.objects.get_or_create(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        defaults={"estado": estado_inicial, "rol": rol_beneficiario},
                    )

                    # Si ya existía, actualizar el rol si cambió
                    if not created and legajo.rol != rol_beneficiario:
                        legajo.rol = rol_beneficiario
                        legajo.save(update_fields=["rol"])

                    if created:
                        creados += 1

                    # Verificar si hay datos del responsable
                    tiene_responsable = any(
                        [
                            datos.get("apellido_responsable"),
                            datos.get("nombre_responsable"),
                            datos.get("documento_responsable"),
                        ]
                    )

                    if tiene_responsable and not es_mismo_documento:
                        try:
                            # Crear responsable SOLO si es diferente al beneficiario
                            datos_resp = {
                                "apellido": datos.get("apellido_responsable"),
                                "nombre": datos.get("nombre_responsable"),
                                "documento": datos.get("documento_responsable"),
                                "fecha_nacimiento": datos.get(
                                    "fecha_nacimiento_responsable"
                                ),
                                "sexo": datos.get("sexo_responsable"),
                                "telefono": datos.get("telefono_responsable"),
                                "email": datos.get("email_responsable"),
                                "provincia": provincia_id,
                            }

                            # Limpiar valores None
                            datos_resp = {k: v for k, v in datos_resp.items() if v}

                            # Validaciones mínimas del responsable
                            if not datos_resp.get("documento"):
                                raise ValidationError(
                                    "Documento del responsable obligatorio"
                                )
                            if not datos_resp.get("nombre"):
                                raise ValidationError(
                                    "Nombre del responsable obligatorio"
                                )

                            # Convertir fecha del responsable si existe
                            if "fecha_nacimiento" in datos_resp and isinstance(
                                datos_resp["fecha_nacimiento"], str
                            ):
                                from datetime import datetime

                                try:
                                    fecha_obj = datetime.strptime(
                                        datos_resp["fecha_nacimiento"], "%d/%m/%Y"
                                    ).date()
                                    datos_resp["fecha_nacimiento"] = fecha_obj
                                except ValueError:
                                    try:
                                        fecha_obj = datetime.strptime(
                                            datos_resp["fecha_nacimiento"],
                                            "%Y-%m-%d",
                                        ).date()
                                        datos_resp["fecha_nacimiento"] = fecha_obj
                                    except ValueError:
                                        pass

                            responsable = CiudadanoService.get_or_create_ciudadano(
                                datos=datos_resp,
                                usuario=user,
                                expediente=expediente,
                            )

                            if responsable and responsable.pk:
                                # Validar edad
                                valido_edad, edad_warnings, error_edad = (
                                    validar_edad_responsable(
                                        datos_resp.get("fecha_nacimiento"),
                                        datos.get("fecha_nacimiento"),
                                    )
                                )
                                if error_edad:
                                    raise ValidationError(error_edad)
                                for warning in edad_warnings:
                                    logger.warning(
                                        "Fila %s: %s",
                                        registro.fila_excel,
                                        warning,
                                    )

                                # Crear legajo del responsable
                                ExpedienteCiudadano.objects.get_or_create(
                                    expediente=expediente,
                                    ciudadano=responsable,
                                    defaults={
                                        "estado": estado_inicial,
                                        "rol": ExpedienteCiudadano.ROLE_RESPONSABLE,
                                    },
                                )

                                # Crear GrupoFamiliar
                                relaciones_crear.append(
                                    {
                                        "responsable_id": responsable.pk,
                                        "hijo_id": ciudadano.pk,
                                    }
                                )
                        except Exception as e:
                            logger.warning(
                                "Error creando responsable para fila %s: %s",
                                registro.fila_excel,
                                e,
                            )

                    # Marcar como procesado y limpiar error anterior
                    registro.procesado = True
                    registro.procesado_en = timezone.now()
                    registro.mensaje_error = ""
                    registro.save(
                        update_fields=["procesado", "procesado_en", "mensaje_error"]
                    )
                else:
                    errores += 1
                    errores_detalle.append(
                        f"Fila {registro.fila_excel}: No se pudo crear el ciudadano"
                    )

            except Exception as e:
                errores += 1
                # Usar el error específico para el usuario, pero sin información sensible del sistema
                if "Field" in str(e) and "expected" in str(e):
                    # Error de validación de campo - es seguro mostrarlo
                    error_msg = str(e)
                elif "IntegrityError" in str(type(e).__name__):
                    error_msg = (
                        "Error de integridad: registro duplicado o datos inconsistentes"
                    )
                elif "ValidationError" in str(type(e).__name__):
                    error_msg = str(e)
                else:
                    # Para otros errores, mantener el mensaje original si existe, sino usar genérico
                    error_msg = (
                        registro.mensaje_error
                        if registro.mensaje_error
                        else "Error interno al procesar registro"
                    )

                errores_detalle.append(f"Fila {registro.fila_excel}: {error_msg}")
                logger.error(
                    "Error reprocesando registro %s: %s - Datos: %s",
                    registro.pk,
                    e,
                    datos,
                    exc_info=True,
                )
                # Actualizar con el mensaje más específico
                registro.mensaje_error = f"Error al reprocesar: {error_msg}"
                registro.save(update_fields=["mensaje_error"])

        # Crear relaciones familiares
        if relaciones_crear:
            try:
                from ciudadanos.models import GrupoFamiliar

                relaciones_creadas = 0
                for rel in relaciones_crear:
                    _, created = GrupoFamiliar.objects.get_or_create(
                        ciudadano_1_id=rel["responsable_id"],
                        ciudadano_2_id=rel["hijo_id"],
                        defaults={
                            "vinculo": GrupoFamiliar.RELACION_PADRE,
                            "estado_relacion": GrupoFamiliar.ESTADO_BUENO,
                            "conviven": True,
                            "cuidador_principal": True,
                        },
                    )
                    if created:
                        relaciones_creadas += 1

                logger.info(
                    "Creadas %s relaciones familiares al reprocesar",
                    relaciones_creadas,
                )
            except Exception as e:
                logger.error(
                    "Error creando relaciones familiares al reprocesar: %s",
                    e,
                    exc_info=True,
                )

        # Verificar registros restantes
        registros_restantes = expediente.registros_erroneos.filter(
            procesado=False
        ).count()

        return JsonResponse(
            {
                "success": True,
                "creados": creados,
                "errores": errores,
                "errores_detalle": errores_detalle,
                "registros_restantes": registros_restantes,
            }
        )


class EliminarRegistroErroneoView(View):
    def post(self, request, pk, registro_id):
        user = request.user
        expediente = get_object_or_404(Expediente, pk=pk)

        if not (_is_admin(user) or _is_provincial(user)):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        from celiaquia.models import RegistroErroneo

        registro = get_object_or_404(
            RegistroErroneo, pk=registro_id, expediente=expediente
        )

        registro.delete()
        return JsonResponse(
            {"success": True, "message": "Registro eliminado correctamente."}
        )
