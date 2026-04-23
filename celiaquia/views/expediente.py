import json
import logging
import re
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
from django.db.models import Q, Count, OuterRef, Subquery
from django.core.paginator import Paginator
from iam.services import user_has_permission_code

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
    IMPORTACION_EDITABLE_FIELDS,
    IMPORTACION_RESPONSABLE_FIELDS,
    _beneficiario_tiene_conflicto_importacion,
    _beneficiario_requiere_responsable_importacion,
    _cargar_nacionalidades_cache,
    _cargar_paises_a_nacionalidad_importacion,
    _precargar_conflictos_y_existentes_importacion,
    _resolver_nacionalidad_payload_importacion,
    validar_y_normalizar_payloads_importacion,
)
from celiaquia.services.cruce_service import CruceService
from celiaquia.services.cupo_service import CupoService, CupoNoConfigurado
from django.utils import timezone
from django.db import transaction
from core.models import Nacionalidad, Provincia, Localidad
from core.soft_delete.preview import build_delete_preview
from core.soft_delete.view_helpers import is_soft_deletable_instance

logger = logging.getLogger("django")

ROLE_COORDINADOR_CELIAQUIA_PERMISSION = "auth.role_coordinadorceliaquia"
ROLE_TECNICO_CELIAQUIA_PERMISSION = "auth.role_tecnicoceliaquia"


def _user_has_permission(user, permission_code: str) -> bool:
    return user_has_permission_code(user, permission_code)


def _is_admin(user) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_superuser", False)
    )


def _user_in_group(user, group_name) -> bool:
    """Indica si el usuario pertenece al grupo solicitado."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    groups = getattr(user, "groups", None)
    if not groups:
        return False
    filter_fn = getattr(groups, "filter", None)
    if not callable(filter_fn) or not group_name:
        return False

    try:
        exists_fn = getattr(filter_fn(name=group_name), "exists", None)
        return bool(exists_fn() if callable(exists_fn) else False)
    except Exception:
        return False


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _is_provincial(user) -> bool:
    if not user.is_authenticated:
        return False
    try:
        return bool(user.profile.es_usuario_provincial and user.profile.provincia_id)
    except (AttributeError, ObjectDoesNotExist):
        return False


def _can_manage_registros_erroneos(user) -> bool:
    return bool(
        _is_admin(user)
        or _is_provincial(user)
        or _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
    )


def _get_nacionalidad_argentina():
    return Nacionalidad.objects.filter(nacionalidad__iexact="Argentina").first()


def _get_nacionalidad_argentina_id():
    argentina = _get_nacionalidad_argentina()
    return getattr(argentina, "pk", "") or ""


def _resolver_localidad_registro_erroneo(localidad_value):
    if localidad_value in (None, ""):
        return None

    localidad_str = str(localidad_value).strip()
    if not localidad_str:
        return None

    localidades = Localidad.objects.select_related("municipio")
    if localidad_str.isdigit():
        return localidades.filter(pk=int(localidad_str)).first()
    return localidades.filter(nombre__iexact=localidad_str).first()


def _resolver_nacionalidad_registro_erroneo(nacionalidad_value):
    if nacionalidad_value in (None, ""):
        return None

    payload = {"nacionalidad": nacionalidad_value}
    try:
        _resolver_nacionalidad_payload_importacion(
            payload,
            nacionalidades_cache=_cargar_nacionalidades_cache(),
            paises_a_nacionalidad=_cargar_paises_a_nacionalidad_importacion(),
        )
    except ValidationError:
        return None

    nacionalidad_id = payload.get("nacionalidad")
    if not nacionalidad_id:
        return None
    return Nacionalidad.objects.filter(pk=nacionalidad_id).first()


def _resolver_nacionalidad_id_registro_erroneo(nacionalidad_value):
    nacionalidad = _resolver_nacionalidad_registro_erroneo(nacionalidad_value)
    if not nacionalidad:
        return ""
    return str(nacionalidad.pk)


def _resolver_municipio_id_desde_localidad(localidad_value):
    localidad = _resolver_localidad_registro_erroneo(localidad_value)
    if not localidad or not localidad.municipio_id:
        return ""
    return str(localidad.municipio_id)


def _normalizar_mensaje_error_invalid_fields(message):
    if isinstance(message, ValidationError):
        mensajes = getattr(message, "messages", None) or [str(message)]
        msg = " ".join(str(item) for item in mensajes if item)
    else:
        msg = str(message or "")

    msg = msg.strip()
    if msg.startswith("[") and msg.endswith("]"):
        msg = msg[1:-1].strip()
    msg = msg.strip("'\" ")

    prefijo_reproceso = "error al reprocesar:"
    if msg.lower().startswith(prefijo_reproceso):
        msg = msg[len(prefijo_reproceso) :].strip()

    return msg


def _campos_invalidos_desde_mensaje_error(message):
    if not message:
        return []

    msg = _normalizar_mensaje_error_invalid_fields(message)
    msg_lower = msg.lower()
    campos = []

    faltantes_match = re.search(
        r"faltan campos obligatorios:\s*(?P<faltantes>.+)$",
        msg,
        flags=re.IGNORECASE,
    )
    if faltantes_match:
        faltantes = faltantes_match.group("faltantes")
        return [
            campo.strip()
            for campo in faltantes.split(",")
            if campo and campo.strip() in IMPORTACION_EDITABLE_FIELDS
        ]

    patrones = [
        (
            r"\bfecha_nacimiento_responsable\b|fecha de nacimiento responsable",
            "fecha_nacimiento_responsable",
        ),
        (r"\bdocumento_responsable\b|documento responsable", "documento_responsable"),
        (r"\bapellido_responsable\b|apellido responsable", "apellido_responsable"),
        (r"\bnombre_responsable\b|nombre responsable", "nombre_responsable"),
        (r"\bsexo_responsable\b|sexo responsable", "sexo_responsable"),
        (r"\bdomicilio_responsable\b|domicilio responsable", "domicilio_responsable"),
        (r"\blocalidad_responsable\b|localidad responsable", "localidad_responsable"),
        (
            r"\btelefono_responsable\b|telefono responsable",
            "telefono_responsable",
        ),
        (r"\bemail_responsable\b|email responsable", "email_responsable"),
        (r"\bcontacto_responsable\b|contacto responsable", "contacto_responsable"),
        (r"\bfecha_nacimiento\b|fecha de nacimiento", "fecha_nacimiento"),
        (r"\bdocumento\b", "documento"),
        (r"\bsexo\b", "sexo"),
        (r"\bnacionalidad\b", "nacionalidad"),
        (r"\bmunicipio\b", "municipio"),
        (r"\blocalidad\b", "localidad"),
        (r"\bcodigo_postal\b|codigo postal", "codigo_postal"),
        (r"\bcalle\b", "calle"),
        (r"\baltura\b", "altura"),
        (r"\btelefono\b", "telefono"),
        (r"\bemail\b", "email"),
    ]
    for patron, campo in patrones:
        if re.search(patron, msg_lower) and campo in IMPORTACION_EDITABLE_FIELDS:
            campos.append(campo)

    if "debe tener un responsable" in msg_lower:
        campos.extend(
            [
                "apellido_responsable",
                "nombre_responsable",
                "documento_responsable",
                "fecha_nacimiento_responsable",
                "sexo_responsable",
                "domicilio_responsable",
                "localidad_responsable",
            ]
        )

    return list(dict.fromkeys(campos))


def _aplicar_defaults_registro_erroneo(datos):
    datos_con_defaults = dict(datos)

    municipio_id = _resolver_municipio_id_desde_localidad(
        datos_con_defaults.get("localidad")
    )
    if municipio_id:
        datos_con_defaults["municipio"] = municipio_id

    return datos_con_defaults


def _normalizar_datos_registro_erroneo(payload):
    datos_normalizados = {}
    for field in IMPORTACION_EDITABLE_FIELDS:
        if field not in payload:
            continue
        value = payload.get(field)
        if isinstance(value, str):
            value = value.strip()
        datos_normalizados[field] = value
    return datos_normalizados


def _limpiar_datos_registro_erroneo(payload):
    return {k: v for k, v in payload.items() if v not in (None, "")}


def _consolidar_datos_registro_erroneo(datos_previos, datos_nuevos):
    datos_consolidados = _normalizar_datos_registro_erroneo(datos_previos or {})
    for field in IMPORTACION_EDITABLE_FIELDS:
        if field not in datos_nuevos:
            continue
        value = datos_nuevos.get(field)
        if value in (None, ""):
            datos_consolidados.pop(field, None)
            continue
        datos_consolidados[field] = value

    responsable_tocado = any(
        field in datos_nuevos for field in IMPORTACION_RESPONSABLE_FIELDS
    )
    responsable_vacio = not any(
        datos_consolidados.get(field) not in (None, "")
        for field in IMPORTACION_RESPONSABLE_FIELDS
    )
    if responsable_tocado and responsable_vacio:
        for field in IMPORTACION_RESPONSABLE_FIELDS:
            datos_consolidados.pop(field, None)

    return _aplicar_defaults_registro_erroneo(datos_consolidados)


def _resolver_provincia_id_registro_erroneo(user, expediente):
    provincia = _user_provincia(user) or getattr(expediente, "provincia", None)
    if provincia is None:
        try:
            provincia = expediente.usuario_provincia.profile.provincia
        except Exception:
            provincia = None
    for attr in ("pk", "id"):
        provincia_id = getattr(provincia, attr, None)
        if provincia_id is not None:
            return provincia_id
    return provincia


def _deduplicar_excluidos_alerta(excluidos):
    vistos = set()
    resultado = []
    for item in excluidos or []:
        if isinstance(item, dict):
            key = (
                item.get("ciudadano_id"),
                item.get("documento"),
                item.get("expediente_origen_id"),
                item.get("estado_programa"),
                item.get("estado_expediente_origen"),
                item.get("motivo"),
            )
        else:
            key = ("raw", str(item))
        if key in vistos:
            continue
        vistos.add(key)
        resultado.append(item)
    return resultado


def _build_excluidos_importacion_alerta(excluidos):
    excluidos_lineas = []
    if excluidos:
        excluidos_lineas.append(
            f"No se crearon {len(excluidos)} legajos porque ya existen en otro expediente activo."
        )
        for item in excluidos[:10]:
            if not isinstance(item, dict):
                excluidos_lineas.append(str(item))
                continue
            documento = item.get("documento", "-")
            apellido = item.get("apellido", "-")
            nombre = item.get("nombre", "-")
            estado = (
                item.get("estado_programa")
                or item.get("estado_expediente_origen")
                or item.get("motivo")
                or "-"
            )
            expediente_origen = item.get("expediente_origen_id", "-")
            excluidos_lineas.append(
                f"- Documento {documento} - {apellido}, {nombre} - {estado} - Exp #{expediente_origen}"
            )
        restantes = len(excluidos) - 10
        if restantes > 0:
            excluidos_lineas.append(f"... y {restantes} mas.")
    return "\n".join(excluidos_lineas)


def _actualizar_alerta_importacion_persistente(
    expediente, *, creados_incremento=0, errores_actuales=None, excluidos_nuevos=None
):
    historial_qs = (
        expediente.historial.filter(estado_nuevo=expediente.estado)
        .exclude(observaciones__isnull=True)
        .exclude(observaciones="")
        .order_by("-fecha")
    )
    historial_actual = historial_qs.first()
    if not historial_actual:
        return

    try:
        payload = json.loads(historial_actual.observaciones)
    except (TypeError, ValueError):
        return

    if not isinstance(payload, dict):
        return

    creados_total = int(payload.get("creados_total") or 0) + int(creados_incremento or 0)
    errores_vigentes = (
        int(errores_actuales)
        if errores_actuales is not None
        else int(payload.get("errores_actuales") or 0)
    )

    payload["resumen"] = _build_resumen_importacion_alerta(
        creados_total=creados_total,
        errores_actuales=errores_vigentes,
    )
    excluidos_detalle = _deduplicar_excluidos_alerta(
        (payload.get("excluidos_detalle") or []) + (excluidos_nuevos or [])
    )
    payload["excluidos_detalle"] = excluidos_detalle
    payload["excluidos"] = _build_excluidos_importacion_alerta(excluidos_detalle)
    payload["tiene_errores"] = bool(errores_vigentes)
    payload["creados_total"] = creados_total
    payload["errores_actuales"] = errores_vigentes

    historial_actual.observaciones = json.dumps(payload)
    historial_actual.save(update_fields=["observaciones"])
    return payload


def _build_resumen_importacion_alerta(*, creados_total=0, errores_actuales=0):
    resumen_lineas = [
        f"Importacion procesada. Se crearon {creados_total} legajos y el expediente paso a EN ESPERA."
    ]
    if errores_actuales:
        resumen_lineas.append(f"Errores detectados: {errores_actuales}.")
    return "\n".join(resumen_lineas)


def _validar_datos_registro_erroneo(payload, provincia_id, fila_excel=0):
    return validar_y_normalizar_payloads_importacion(
        payload=payload,
        provincia_usuario_id=provincia_id,
        offset=fila_excel,
    )


def _registro_erroneo_responsable_requerido(payload):
    fecha_nacimiento = payload.get("fecha_nacimiento")
    if fecha_nacimiento in (None, ""):
        return False
    try:
        payload_normalizado = dict(payload)
        payload_normalizado["fecha_nacimiento"] = CiudadanoService._to_date(
            fecha_nacimiento
        )
    except ValidationError:
        return False
    return _beneficiario_requiere_responsable_importacion(payload_normalizado)


def _user_provincia(user):
    try:
        return user.profile.provincia
    except (AttributeError, ObjectDoesNotExist):
        return None


def _tecnicos_queryset():
    qs = User.objects.filter(
        Q(
            user_permissions__content_type__app_label="auth",
            user_permissions__codename="role_tecnicoceliaquia",
        )
        | Q(
            groups__permissions__content_type__app_label="auth",
            groups__permissions__codename="role_tecnicoceliaquia",
        )
    )
    distinct = getattr(qs, "distinct", None)
    if callable(distinct):
        return distinct()
    return qs


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

        # Filtrar por provincia del usuario solo si es provincial Y NO es coordinador
        is_coord = _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        if _is_provincial(user) and not is_coord:
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
        if _is_admin(user) or _user_has_permission(
            user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION
        ):
            qs = qs.order_by("-fecha_creacion")
        elif _user_has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION):
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
        is_admin = _is_admin(user)
        is_coord = _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        is_tecnico = _user_has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)

        ctx["tecnicos"] = []
        ctx["is_admin_celiaquia"] = is_admin
        ctx["is_coord_celiaquia"] = is_coord
        ctx["is_tecnico_celiaquia"] = is_tecnico
        ctx["is_provincial_celiaquia"] = _is_provincial(user)
        ctx["can_manage_tecnicos_celiaquia"] = is_admin or is_coord
        ctx["show_tecnico_column_celiaquia"] = is_admin or is_coord or is_tecnico

        if is_admin or is_coord:
            ctx["tecnicos"] = _tecnicos_queryset().order_by("last_name", "first_name")
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
                        "alerta_resumen": _build_resumen_importacion_alerta(
                            creados_total=result.get("creados", 0),
                            errores_actuales=result.get("errores", 0),
                        ),
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
        if _is_admin(user) or _user_has_permission(
            user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION
        ):
            return base
        if _user_has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION):
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
        is_admin = _is_admin(user)
        is_coord = _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        is_tecnico = _user_has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)
        can_manage_registros_erroneos = _can_manage_registros_erroneos(user)
        ctx["is_tecnico_celiaquia"] = is_tecnico
        ctx["is_coord_celiaquia"] = is_coord
        ctx["is_provincial_celiaquia"] = _is_provincial(user)
        ctx["can_manage_tecnicos_celiaquia"] = is_admin or is_coord
        ctx["can_manage_registros_erroneos"] = can_manage_registros_erroneos

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
        ultimo_historial_tecnico_con_motivo = (
            HistorialValidacionTecnica.objects.filter(legajo_id=OuterRef("legajo_id"))
            .exclude(Q(motivo__isnull=True) | Q(motivo=""))
            .order_by("-creado_en", "-pk")
            .values("pk")[:1]
        )
        historial_tecnico = HistorialValidacionTecnica.objects.filter(
            legajo_id__in=[legajo.pk for legajo in legajos_list],
            pk=Subquery(ultimo_historial_tecnico_con_motivo),
        )
        observaciones_tecnicas_por_legajo = {}
        for historial_item in historial_tecnico:
            observaciones_tecnicas_por_legajo.setdefault(
                historial_item.legajo_id, historial_item
            )
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
            legajo.responsable_id = FamiliaService.obtener_responsable_de_hijo(
                legajo.ciudadano.id
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

            rol_normalizado = (getattr(legajo, "rol", "") or "").strip().lower()
            legajo.es_doble_rol = (
                (rol_normalizado == ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE)
                or (legajo.es_responsable and legajo.responsable_id is not None)
                or (
                    rol_normalizado == ExpedienteCiudadano.ROLE_BENEFICIARIO
                    and bool(hijos_list)
                )
            )

            # Determinar tipo de legajo segun roles efectivos.
            if legajo.es_doble_rol:
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
            legajo.observacion_tecnica_titulo = None
            legajo.observacion_tecnica_texto = None

            observacion_tecnica = observaciones_tecnicas_por_legajo.get(legajo.pk)
            if observacion_tecnica:
                if observacion_tecnica.estado_nuevo == RevisionTecnico.RECHAZADO:
                    legajo.observacion_tecnica_titulo = "Motivo del Rechazo"
                else:
                    legajo.observacion_tecnica_titulo = "Observación (subsanación)"
                legajo.observacion_tecnica_texto = observacion_tecnica.motivo
            elif legajo.subsanacion_motivo:
                legajo.observacion_tecnica_titulo = "Observación (subsanación)"
                legajo.observacion_tecnica_texto = legajo.subsanacion_motivo

            if (
                legajo.es_responsable
                or legajo.rol == ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
            ):
                legajo.hijos_a_cargo = hijos_list
                responsables_legajos.append(legajo)
                # Si tiene responsable, agregarlo también a hijos_por_responsable
                if legajo.responsable_id:
                    if legajo.responsable_id not in hijos_por_responsable:
                        hijos_por_responsable[legajo.responsable_id] = []
                    hijos_por_responsable[legajo.responsable_id].append(legajo)
            else:
                legajo.hijos_a_cargo = []
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

        # Agregar hijos sin responsable al final evitando duplicados.
        for legajo in hijos_sin_responsable:
            if legajo.ciudadano_id not in agregados:
                legajos_enriquecidos.append(legajo)
                agregados.add(legajo.ciudadano_id)

        # Agregar legajos huérfanos: tienen responsable_id pero ese responsable
        # no está en el expediente (fue eliminado o nunca se importó).
        # Sin este paso quedan invisibles en la vista pero siguen existiendo en BD,
        # lo que provoca errores en la validación de confirm_envío.
        for legajo in legajos_list:
            if legajo.ciudadano_id not in agregados:
                legajos_enriquecidos.append(legajo)
                agregados.add(legajo.ciudadano_id)

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
        if _is_admin(user) or _user_has_permission(
            user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION
        ):
            tecnicos = _tecnicos_queryset().order_by("last_name", "first_name")

        faltan_archivos = bool(faltantes_list)

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
        historial_estado_actual = historial.filter(
            estado_nuevo=expediente.estado,
            observaciones__isnull=False,
        ).exclude(observaciones="").order_by("-fecha")
        alerta_importacion_persistente = (
            historial_estado_actual.values_list("observaciones", flat=True).first()
        )
        ctx["alerta_importacion_persistente"] = alerta_importacion_persistente
        ctx["alerta_importacion_resumen"] = ""
        ctx["alerta_importacion_resumen_style"] = ""
        ctx["alerta_importacion_excluidos"] = ""
        ctx["alerta_importacion_excluidos_style"] = ""
        ctx["alerta_importacion_warning"] = ""
        ctx["alerta_importacion_warning_secundario"] = ""
        ctx["alerta_importacion_success"] = ""
        if alerta_importacion_persistente:
            try:
                alerta_payload = json.loads(alerta_importacion_persistente)
            except (TypeError, ValueError):
                alerta_payload = None

            if isinstance(alerta_payload, dict):
                resumen_alerta = alerta_payload.get("resumen", "")
                excluidos_alerta = alerta_payload.get("excluidos", "")
                creados_total = int(alerta_payload.get("creados_total") or 0)
                tiene_errores = bool(alerta_payload.get("tiene_errores"))
                resumen_bloque = ""
                resumen_bloque_style = ""
                excluidos_bloque = ""
                excluidos_bloque_style = ""

                # Al volver a entrar al expediente solo se recuperan advertencias
                # persistentes del estado EN_ESPERA; los mensajes success se
                # muestran en el flujo inmediato post-importacion / post-subsanacion.
                if tiene_errores:
                    resumen_bloque = resumen_alerta
                    resumen_bloque_style = "warning"
                    excluidos_bloque = excluidos_alerta
                    excluidos_bloque_style = "warning" if excluidos_alerta else ""
                elif creados_total == 0 and excluidos_alerta:
                    resumen_bloque = "\n".join(
                        part for part in [resumen_alerta, excluidos_alerta] if part
                    )
                    resumen_bloque_style = "warning"
                elif excluidos_alerta:
                    excluidos_bloque = excluidos_alerta
                    excluidos_bloque_style = "warning"

                ctx["alerta_importacion_resumen"] = resumen_bloque
                ctx["alerta_importacion_resumen_style"] = resumen_bloque_style
                ctx["alerta_importacion_excluidos"] = excluidos_bloque
                ctx["alerta_importacion_excluidos_style"] = excluidos_bloque_style
                ctx["alerta_importacion_warning"] = (
                    resumen_bloque if resumen_bloque_style == "warning" else ""
                )
                ctx["alerta_importacion_warning_secundario"] = (
                    excluidos_bloque if excluidos_bloque_style == "warning" else ""
                )
                ctx["alerta_importacion_success"] = (
                    resumen_bloque if resumen_bloque_style == "success" else ""
                )
        ctx["historial_page_obj"] = Paginator(historial, 5).get_page(
            self.request.GET.get("historial_page")
        )

        # Obtener registros erróneos
        registros_erroneos = list(
            expediente.registros_erroneos.filter(procesado=False).order_by("fila_excel")
        )

        # Datos para desplegables en registros erróneos
        from core.models import Sexo, Municipio, Localidad

        sexos = Sexo.objects.all()
        nacionalidades = Nacionalidad.objects.all().order_by("nacionalidad")
        nacionalidad_argentina_id = str(_get_nacionalidad_argentina_id() or "")
        municipios = []
        localidades = []

        if prov:
            municipios = Municipio.objects.filter(provincia=prov).order_by("nombre")
            localidades = (
                Localidad.objects.filter(municipio__provincia=prov)
                .select_related("municipio")
                .order_by("municipio__nombre", "nombre")
            )
        elif can_manage_registros_erroneos:
            municipios = Municipio.objects.all().order_by("nombre")
            localidades = Localidad.objects.select_related("municipio").order_by(
                "municipio__nombre", "nombre"
            )

        for registro in registros_erroneos:
            datos_render = _aplicar_defaults_registro_erroneo(
                _normalizar_datos_registro_erroneo(registro.datos_raw or {})
            )
            registro.datos_render = datos_render
            registro.invalid_fields = _campos_invalidos_desde_mensaje_error(
                registro.mensaje_error
            )
            registro.responsable_requerido = _registro_erroneo_responsable_requerido(
                datos_render
            )
            registro.nacionalidad_autocomplete_id = (
                _resolver_nacionalidad_id_registro_erroneo(
                    datos_render.get("nacionalidad")
                )
            )
            registro.municipio_autocomplete_id = datos_render.get("municipio", "")

        ctx.update(
            {
                "legajos": legajos_enriquecidos,
                "registros_erroneos": registros_erroneos,
                "sexos": sexos,
                "nacionalidades": nacionalidades,
                "nacionalidad_argentina_id": nacionalidad_argentina_id,
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
        if not (
            _is_admin(user)
            or _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        ):
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
        if not (
            _is_admin(user)
            or _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        ):
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

        tecnico_qs = _tecnicos_queryset()
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
        if not (
            _is_admin(user)
            or _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        ):
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
            get_data = getattr(request, "GET", {})
            post_data = getattr(request, "POST", {})
            preview_enabled = str(
                get_data.get("preview") or post_data.get("preview") or ""
            )
            if preview_enabled in {"1", "true", "True"} and is_soft_deletable_instance(
                asignacion
            ):
                return JsonResponse(
                    {
                        "success": True,
                        "preview": build_delete_preview(asignacion),
                    }
                )

            if is_soft_deletable_instance(asignacion):
                asignacion.delete(user=user, cascade=True)
            else:
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

        if not (
            _is_admin(user)
            or _user_has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)
        ):
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
        es_tecnico = _user_has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)
        es_coord = _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)

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

        # Validar RENAPER automáticamente antes de cualquier acción (excepto ELIMINAR)
        if accion in ("APROBAR", "RECHAZAR", "SUBSANAR"):
            estado_validacion_renaper = getattr(leg, "estado_validacion_renaper", 0)
            # Si no tiene validación RENAPER, marcar como aprobado automáticamente
            if estado_validacion_renaper == 0:
                leg.estado_validacion_renaper = 1
                leg.save(update_fields=["estado_validacion_renaper", "modificado_en"])

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
            # Asegurar que RENAPER esté validado
            if getattr(leg, "estado_validacion_renaper", 0) == 0:
                leg.estado_validacion_renaper = 1
            leg.save(
                update_fields=[
                    "revision_tecnico",
                    "estado_validacion_renaper",
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

        motivo = (request.POST.get("motivo") or "").strip()

        if accion == "RECHAZAR":
            if not motivo:
                return JsonResponse(
                    {"success": False, "error": "Debe indicar un motivo de rechazo."},
                    status=400,
                )

            estado_anterior = leg.revision_tecnico
            leg.revision_tecnico = "RECHAZADO"
            # Marcar RENAPER como rechazado también
            if getattr(leg, "estado_validacion_renaper", 0) == 0:
                leg.estado_validacion_renaper = 2
            leg.save(
                update_fields=[
                    "revision_tecnico",
                    "estado_validacion_renaper",
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
                motivo=motivo[:500],
            )

            return JsonResponse(
                {"success": True, "estado": leg.revision_tecnico, "cupo_liberado": True}
            )

        # ELIMINAR - Solo coordinadores
        if accion == "ELIMINAR":
            if not (
                _is_admin(user)
                or _user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Solo coordinadores pueden eliminar legajos.",
                    },
                    status=403,
                )

            try:
                get_data = getattr(request, "GET", {})
                post_data = getattr(request, "POST", {})
                preview_enabled = str(
                    post_data.get("preview") or get_data.get("preview") or ""
                )
                if preview_enabled in {
                    "1",
                    "true",
                    "True",
                } and is_soft_deletable_instance(leg):
                    return JsonResponse(
                        {
                            "success": True,
                            "preview": build_delete_preview(leg),
                        }
                    )

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

                if is_soft_deletable_instance(leg):
                    leg.delete(user=user, cascade=True)
                else:
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
        tipo_subsanacion = (request.POST.get("tipo_subsanacion") or "").strip()
        if not motivo:
            return JsonResponse(
                {"success": False, "error": "Debe indicar un motivo de subsanación."},
                status=400,
            )

        estado_anterior = leg.revision_tecnico
        leg.revision_tecnico = RevisionTecnico.SUBSANAR
        leg.subsanacion_tipo = tipo_subsanacion if tipo_subsanacion else None
        leg.subsanacion_motivo = motivo[:500]
        leg.subsanacion_solicitada_en = timezone.now()
        leg.subsanacion_usuario = user
        # Marcar RENAPER como subsanar también
        if leg.estado_validacion_renaper == 0:
            leg.estado_validacion_renaper = 3
        leg.save(
            update_fields=[
                "revision_tecnico",
                "subsanacion_tipo",
                "subsanacion_motivo",
                "subsanacion_solicitada_en",
                "subsanacion_usuario",
                "estado_validacion_renaper",
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

        if not _can_manage_registros_erroneos(user):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        from celiaquia.models import RegistroErroneo

        registro = get_object_or_404(
            RegistroErroneo, pk=registro_id, expediente=expediente
        )

        try:
            datos_actualizados = json.loads(request.body)
            datos_nuevos = _normalizar_datos_registro_erroneo(datos_actualizados)
            datos_normalizados = _consolidar_datos_registro_erroneo(
                registro.datos_raw, datos_nuevos
            )

            provincia_id = _resolver_provincia_id_registro_erroneo(user, expediente)
            if not provincia_id:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No se pudo determinar la provincia para validar el registro.",
                    },
                    status=400,
                )
            _validar_datos_registro_erroneo(
                datos_normalizados,
                provincia_id=provincia_id,
                fila_excel=registro.fila_excel,
            )
            datos_limpios = _limpiar_datos_registro_erroneo(datos_normalizados)
            registro.datos_raw = datos_limpios
            registro.save(update_fields=["datos_raw"])

            return JsonResponse(
                {"success": True, "message": "Registro actualizado correctamente."}
            )
        except ValidationError as exc:
            registro.mensaje_error = str(exc)
            registro.save(update_fields=["mensaje_error"])
            return JsonResponse(
                {
                    "success": False,
                    "saved_partial": True,
                    "error": str(exc),
                    "invalid_fields": _campos_invalidos_desde_mensaje_error(exc),
                },
                status=400,
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

        if not _can_manage_registros_erroneos(user):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

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
        excluidos_detalle = []
        relaciones_crear = []

        estado_inicial = EstadoLegajo.objects.get(nombre="DOCUMENTO_PENDIENTE")
        existentes_ids, en_programa, abiertos = (
            _precargar_conflictos_y_existentes_importacion(expediente)
        )

        provincia_id = _resolver_provincia_id_registro_erroneo(user, expediente)
        if not provincia_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se pudo determinar la provincia del usuario.",
                },
                status=400,
            )

        for registro in registros:
            datos = _aplicar_defaults_registro_erroneo(
                _normalizar_datos_registro_erroneo(registro.datos_raw.copy())
            )
            try:
                (
                    datos_beneficiario,
                    datos_responsable,
                    es_mismo_documento,
                ) = _validar_datos_registro_erroneo(
                    datos,
                    provincia_id=provincia_id,
                    fila_excel=registro.fila_excel,
                )

                with transaction.atomic():
                    ciudadano = CiudadanoService.get_or_create_ciudadano(
                        datos=datos_beneficiario,
                        usuario=user,
                        expediente=expediente,
                    )

                    if ciudadano and ciudadano.pk:
                        if _beneficiario_tiene_conflicto_importacion(
                            ciudadano=ciudadano,
                            offset=registro.fila_excel,
                            existentes_ids=existentes_ids,
                            en_programa=en_programa,
                            abiertos=abiertos,
                            excluidos=excluidos_detalle,
                        ):
                            registro.procesado = True
                            registro.procesado_en = timezone.now()
                            registro.mensaje_error = ""
                            registro.save(
                                update_fields=[
                                    "procesado",
                                    "procesado_en",
                                    "mensaje_error",
                                ]
                            )
                            continue

                        rol_beneficiario = (
                            ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
                            if es_mismo_documento
                            else ExpedienteCiudadano.ROLE_BENEFICIARIO
                        )
                        legajo, created = ExpedienteCiudadano.objects.get_or_create(
                            expediente=expediente,
                            ciudadano=ciudadano,
                            defaults={
                                "estado": estado_inicial,
                                "rol": rol_beneficiario,
                            },
                        )

                        if not created and legajo.rol != rol_beneficiario:
                            legajo.rol = rol_beneficiario
                            legajo.save(update_fields=["rol"])

                        if created:
                            creados += 1
                            existentes_ids.add(ciudadano.pk)

                        if datos_responsable and not es_mismo_documento:
                            responsable = CiudadanoService.get_or_create_ciudadano(
                                datos=datos_responsable,
                                usuario=user,
                                expediente=expediente,
                            )

                            if responsable and responsable.pk:
                                legajo_responsable, created_resp = (
                                    ExpedienteCiudadano.objects.get_or_create(
                                        expediente=expediente,
                                        ciudadano=responsable,
                                        defaults={
                                            "estado": estado_inicial,
                                            "rol": ExpedienteCiudadano.ROLE_RESPONSABLE,
                                        },
                                    )
                                )
                                if (
                                    not created_resp
                                    and legajo_responsable.rol
                                    == ExpedienteCiudadano.ROLE_BENEFICIARIO
                                ):
                                    legajo_responsable.rol = (
                                        ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
                                    )
                                    legajo_responsable.save(update_fields=["rol"])

                                relaciones_crear.append(
                                    {
                                        "responsable_id": responsable.pk,
                                        "hijo_id": ciudadano.pk,
                                    }
                                )

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
                if "Field" in str(e) and "expected" in str(e):
                    error_msg = str(e)
                elif "IntegrityError" in str(type(e).__name__):
                    error_msg = (
                        "Error de integridad: registro duplicado o datos inconsistentes"
                    )
                elif "ValidationError" in str(type(e).__name__):
                    error_msg = str(e)
                else:
                    error_msg = (
                        registro.mensaje_error
                        if registro.mensaje_error
                        else "Error interno al procesar registro"
                    )

                errores_detalle.append(f"Fila {registro.fila_excel}: {error_msg}")
                if not isinstance(e, ValidationError):
                    logger.error(
                        "Error reprocesando registro %s: %s - Datos: %s",
                        registro.pk,
                        e,
                        datos,
                        exc_info=True,
                    )
                registro.mensaje_error = f"Error al reprocesar: {error_msg}"
                registro.save(update_fields=["mensaje_error"])

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

        registros_restantes = expediente.registros_erroneos.filter(
            procesado=False
        ).count()
        alerta_actualizada = _actualizar_alerta_importacion_persistente(
            expediente,
            creados_incremento=creados,
            errores_actuales=registros_restantes,
            excluidos_nuevos=excluidos_detalle,
        )

        return JsonResponse(
            {
                "success": True,
                "creados": creados,
                "errores": errores,
                "errores_detalle": errores_detalle,
                "excluidos": len(excluidos_detalle),
                "excluidos_detalle": excluidos_detalle,
                "registros_restantes": registros_restantes,
                "alerta_resumen": (alerta_actualizada or {}).get("resumen", ""),
            }
        )


class EliminarRegistroErroneoView(View):
    def post(self, request, pk, registro_id):
        user = request.user
        expediente = get_object_or_404(Expediente, pk=pk)

        if not _can_manage_registros_erroneos(user):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        from celiaquia.models import RegistroErroneo

        registro = get_object_or_404(
            RegistroErroneo, pk=registro_id, expediente=expediente
        )

        get_data = getattr(request, "GET", {})
        post_data = getattr(request, "POST", {})
        preview_enabled = str(post_data.get("preview") or get_data.get("preview") or "")
        if preview_enabled in {"1", "true", "True"} and is_soft_deletable_instance(
            registro
        ):
            return JsonResponse(
                {
                    "success": True,
                    "preview": build_delete_preview(registro),
                }
            )

        if is_soft_deletable_instance(registro):
            registro.delete(user=user, cascade=True)
        else:
            registro.delete()
        return JsonResponse(
            {"success": True, "message": "Registro eliminado correctamente."}
        )


class ExpedienteDeleteView(View):
    def delete(self, request, pk):
        user = request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )
        queryset = getattr(Expediente, "all_objects", Expediente.objects)
        expediente = queryset.filter(pk=pk).first()
        if expediente is None:
            return JsonResponse(
                {
                    "success": True,
                    "message": "El expediente ya estaba eliminado.",
                    "already_deleted": True,
                }
            )

        get_data = getattr(request, "GET", {})
        post_data = getattr(request, "POST", {})
        preview_enabled = str(post_data.get("preview") or get_data.get("preview") or "")
        if preview_enabled in {"1", "true", "True"} and is_soft_deletable_instance(
            expediente
        ):
            return JsonResponse(
                {
                    "success": True,
                    "preview": build_delete_preview(expediente),
                }
            )

        try:
            if is_soft_deletable_instance(expediente):
                expediente.delete(user=user, cascade=True)
            else:
                expediente.delete()
            return JsonResponse(
                {"success": True, "message": "Expediente eliminado correctamente."}
            )
        except Exception as e:
            logger.error("Error al eliminar expediente %s: %s", pk, e, exc_info=True)
            return JsonResponse(
                {"success": False, "error": "Error al eliminar el expediente."},
                status=500,
            )
