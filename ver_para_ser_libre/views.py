# Modulo extenso de vistas del programa; orquesta helpers internos de
# ComedorService y del modulo workflow (acceso protegido intencional).
# pylint: disable=too-many-lines,protected-access
import unicodedata
from urllib.parse import quote_plus

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from comedores.services.comedor_service import ComedorService
from core.mixins import CSVExportMixin
from core.models import Provincia
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from iam.services import user_has_permission_code
from ver_para_ser_libre.forms import (
    CasoLaboratorioVPSLForm,
    ChecklistSedeVPSLForm,
    CierreDiarioVPSLForm,
    ItinerarioVPSLForm,
    JornadaVPSLForm,
    RegistroNominalVPSLForm,
    SedeVPSLForm,
)
from ver_para_ser_libre.models import (
    CasoLaboratorioVPSL,
    CierreDiarioVPSL,
    EstadoEvaluacionVPSL,
    EstadoItinerario,
    EstadoLaboratorio,
    HistorialChecklistSedeVPSL,
    ItinerarioVPSL,
    JornadaVPSL,
    RegistroNominalVPSL,
    SedeVPSL,
)
from ver_para_ser_libre.services import workflow


VIEW_ALL_ITINERARIOS_PERMISSION = "ver_para_ser_libre.view_all_itinerarios_vpsl"


def _breadcrumb(*items):
    base = [{"text": "Ver Para Ser Libres", "url": reverse("vpsl_itinerario_list")}]
    return [*base, *items]


def _normalizar_busqueda(value):
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def _extraer_persona_renaper(data):
    sexo_raw = (
        data.get("sexo")
        or data.get("genero")
        or data.get("sexo_display")
        or data.get("genero_display")
        or ""
    )
    sexo_normalizado = _normalizar_sexo_renaper(sexo_raw)
    sexo_display = _display_sexo_renaper(sexo_raw, sexo_normalizado)
    return {
        "dni": str(data.get("documento") or data.get("dni") or ""),
        "nombre": data.get("nombre") or "",
        "apellido": data.get("apellido") or "",
        "genero": sexo_display,
        "sexo": sexo_normalizado,
        "fecha_nacimiento": (
            data.get("fecha_nacimiento")
            or data.get("fechaNacimiento")
            or data.get("fecha_nac")
            or ""
        ),
        "telefono": data.get("telefono") or data.get("telefono_principal") or "",
    }


def _normalizar_sexo_renaper(value):
    normalized = _normalizar_busqueda(str(value or ""))
    if normalized in {"m", "masculino", "varon", "hombre", "2", "02"}:
        return "M"
    if normalized in {"f", "femenino", "mujer", "1", "01"}:
        return "F"
    if normalized in {"x", "no binario", "nobinario", "3", "03"}:
        return "X"
    return ""


def _display_sexo_renaper(raw_value, normalized_value):
    display = {
        "M": "Masculino",
        "F": "Femenino",
        "X": "X",
    }.get(normalized_value)
    return display or str(raw_value or "")


def _provincia_usuario_provincial(user):
    profile = getattr(user, "profile", None)
    if profile and profile.es_usuario_provincial and profile.provincia_id:
        return profile.provincia
    return None


def _puede_ver_todos_los_itinerarios(user):
    return bool(
        getattr(user, "is_superuser", False)
        or user_has_permission_code(user, VIEW_ALL_ITINERARIOS_PERMISSION)
    )


def _filtrar_itinerarios_por_usuario(queryset, user):
    if _puede_ver_todos_los_itinerarios(user):
        return queryset
    provincia = _provincia_usuario_provincial(user)
    if provincia:
        return queryset.filter(provincia=provincia)
    return queryset.none()


def _filtrar_jornadas_por_usuario(queryset, user):
    if _puede_ver_todos_los_itinerarios(user):
        return queryset
    provincia = _provincia_usuario_provincial(user)
    if provincia:
        return queryset.filter(itinerario__provincia=provincia)
    return queryset.none()


def _filtrar_casos_laboratorio_por_usuario(queryset, user):
    if _puede_ver_todos_los_itinerarios(user):
        return queryset
    provincia = _provincia_usuario_provincial(user)
    if provincia:
        return queryset.filter(registro__jornada__itinerario__provincia=provincia)
    return queryset.none()


def _filtro_estado_itinerario_por_texto(query):
    query_normalizado = _normalizar_busqueda(query)
    if not query_normalizado:
        return Q()
    estados = [
        value
        for value, label in EstadoItinerario.choices
        if query_normalizado in _normalizar_busqueda(label)
        or query_normalizado in _normalizar_busqueda(value)
    ]
    return Q(estado__in=estados) if estados else Q(pk__in=[])


def _puede_exportar(user):
    if getattr(user, "is_superuser", False):
        return True
    return user_has_permission_code(user, "auth.role_exportar_a_csv")


def _extraer_persona_ciudadano(ciudadano):
    sexo_raw = str(ciudadano.sexo or "")
    sexo_normalizado = _normalizar_sexo_renaper(sexo_raw)
    fecha_nacimiento = ciudadano.fecha_nacimiento
    return {
        "dni": str(ciudadano.documento or ""),
        "nombre": ciudadano.nombre or "",
        "apellido": ciudadano.apellido or "",
        "genero": _display_sexo_renaper(sexo_raw, sexo_normalizado),
        "sexo": sexo_normalizado,
        "fecha_nacimiento": (fecha_nacimiento.isoformat() if fecha_nacimiento else ""),
        "edad": ciudadano.edad,
        "telefono": ciudadano.telefono or "",
        "ciudadano_id": ciudadano.pk,
    }


def _resolver_ciudadano_registro_vpsl(dni, sexo, user):
    resultado = ComedorService.crear_ciudadano_desde_renaper(dni, user=user, sexo=sexo)
    if not resultado.get("success"):
        return {
            "success": False,
            "message": resultado.get("message", "No se pudo validar el ciudadano."),
        }
    ciudadano = resultado.get("ciudadano")
    if not ciudadano:
        return {
            "success": False,
            "message": "No se obtuvo el legajo ciudadano validado.",
        }
    return {
        "success": True,
        "message": resultado.get("message", "Ciudadano validado correctamente."),
        "data": _extraer_persona_ciudadano(ciudadano),
        "datos_api": resultado.get("datos_api"),
        "ciudadano": ciudadano,
        "created": bool(resultado.get("created")),
    }


def _prevalidar_ciudadano_registro_vpsl(dni, sexo):
    existente = ComedorService._buscar_ciudadano_existente_por_dni_renaper(dni)
    if existente:
        return {
            "success": True,
            "message": "Ciudadano existente validado.",
            "data": _extraer_persona_ciudadano(existente),
            "datos_api": None,
            "created": False,
            "pending_creation": False,
        }

    resultado = ComedorService.obtener_datos_ciudadano_desde_renaper(dni, sexo=sexo)
    if not resultado.get("success"):
        return {
            "success": False,
            "message": resultado.get("message", "No se encontraron datos en RENAPER."),
        }
    return {
        "success": True,
        "message": resultado.get("message", "Datos obtenidos desde RENAPER."),
        "data": _extraer_persona_renaper(resultado.get("data") or {}),
        "datos_api": resultado.get("datos_api"),
        "created": False,
        "pending_creation": True,
    }


def _buscar_registro_duplicado_en_itinerario(jornada, dni, exclude_pk=None):
    dni = str(dni or "").strip()
    if not jornada or not dni:
        return None
    duplicados = RegistroNominalVPSL.objects.filter(
        jornada__itinerario_id=jornada.itinerario_id,
        dni__iexact=dni,
    ).select_related("jornada")
    if exclude_pk:
        duplicados = duplicados.exclude(pk=exclude_pk)
    return duplicados.order_by("jornada__fecha", "numero_acta").first()


def _mensaje_registro_duplicado(registro):
    return (
        "La persona ya tiene un registro nominal en este itinerario "
        f"(jornada {registro.jornada.fecha:%d/%m/%Y}, acta {registro.numero_acta}). "
        "No se puede cargar duplicada."
    )


def _validar_registro_no_duplicado(form, jornada, dni, exclude_pk=None):
    duplicado = _buscar_registro_duplicado_en_itinerario(
        jornada,
        dni,
        exclude_pk=exclude_pk,
    )
    if duplicado:
        form.add_error(None, _mensaje_registro_duplicado(duplicado))
        return False
    return True


def _aplicar_validacion_ciudadano_a_registro(registro, resultado):
    data = resultado.get("data") or {}
    registro.validado_renaper = True
    registro.no_verificar_renaper = False
    registro.dni = data.get("dni") or registro.dni
    registro.nombre = data.get("nombre") or registro.nombre
    registro.apellido = data.get("apellido") or registro.apellido
    registro.sexo = data.get("sexo") or registro.sexo
    registro.genero = data.get("genero") or registro.genero
    if data.get("edad") is not None:
        registro.edad = data.get("edad")
    if not registro.telefono and data.get("telefono"):
        registro.telefono = data.get("telefono")

    datos_renaper = dict(registro.datos_renaper or {})
    datos_renaper.update(
        {
            "ciudadano_id": data.get("ciudadano_id"),
            "ciudadano_created": resultado.get("created", False),
            "origen_validacion": (
                "renaper" if resultado.get("created") else "ciudadanos"
            ),
        }
    )
    if resultado.get("datos_api") is not None:
        datos_renaper["datos_api"] = resultado.get("datos_api")
    registro.datos_renaper = datos_renaper


def consultar_renaper_vpsl(request):
    dni = (request.GET.get("dni") or "").strip()
    sexo = (request.GET.get("sexo") or "").strip().upper() or None
    registro_nominal = request.GET.get("registro_nominal") == "1"
    if registro_nominal:
        resultado = _prevalidar_ciudadano_registro_vpsl(dni, sexo=sexo)
        if not resultado.get("success"):
            return JsonResponse(
                {"success": False, "message": resultado.get("message")},
                status=400,
            )
        jornada_id = request.GET.get("jornada")
        registro_id = request.GET.get("registro")
        if jornada_id:
            jornada = get_object_or_404(JornadaVPSL, pk=jornada_id)
            duplicado = _buscar_registro_duplicado_en_itinerario(
                jornada,
                (resultado.get("data") or {}).get("dni") or dni,
                exclude_pk=registro_id,
            )
            if duplicado:
                return JsonResponse(
                    {
                        "success": False,
                        "message": _mensaje_registro_duplicado(duplicado),
                        "data": resultado.get("data"),
                    },
                    status=409,
                )
        return JsonResponse(
            {
                "success": True,
                "message": resultado.get("message"),
                "data": resultado.get("data"),
                "datos_api": resultado.get("datos_api"),
                "ciudadano_created": resultado.get("created", False),
                "ciudadano_pendiente_creacion": resultado.get(
                    "pending_creation", False
                ),
            }
        )

    resultado = ComedorService.obtener_datos_ciudadano_desde_renaper(dni, sexo=sexo)
    if not resultado.get("success"):
        return JsonResponse(
            {
                "success": False,
                "message": resultado.get(
                    "message", "No se encontraron datos en RENAPER."
                ),
            },
            status=400,
        )
    data = _extraer_persona_renaper(resultado.get("data") or {})
    return JsonResponse(
        {
            "success": True,
            "message": resultado.get("message", "Datos obtenidos desde RENAPER."),
            "data": data,
            "datos_api": resultado.get("datos_api"),
        }
    )


def sedes_autocomplete(request):
    query = (request.GET.get("q") or "").strip()
    provincia_id = request.GET.get("provincia")
    localidad = (request.GET.get("localidad") or "").strip()
    exclude_ids = [
        int(value)
        for value in [
            *request.GET.getlist("exclude"),
            *request.GET.getlist("exclude[]"),
        ]
        if str(value).strip().isdigit()
    ]
    page = int(request.GET.get("page") or 1)
    page_size = 50
    sedes = SedeVPSL.objects.all().order_by("nombre")
    if provincia_id:
        provincia = Provincia.objects.filter(pk=provincia_id).first()
        if provincia:
            sedes = sedes.filter(jurisdiccion__icontains=provincia.nombre)
    if localidad:
        sedes = sedes.filter(localidad__iexact=localidad)
    if exclude_ids:
        sedes = sedes.exclude(pk__in=exclude_ids)
    if query:
        sedes = sedes.filter(
            Q(nombre__icontains=query)
            | Q(cueanexo__icontains=query)
            | Q(domicilio__icontains=query)
            | Q(localidad__icontains=query)
            | Q(jurisdiccion__icontains=query)
        )

    start = (page - 1) * page_size
    end = start + page_size
    total = sedes.count()
    results = [
        {
            "id": sede.pk,
            "text": f"{sede.nombre} | {sede.cueanexo} | {sede.domicilio}",
            "localidad": sede.localidad,
            "domicilio": sede.domicilio,
            "cueanexo": sede.cueanexo,
            "jurisdiccion": sede.jurisdiccion,
        }
        for sede in sedes[start:end]
    ]
    return JsonResponse(
        {
            "results": results,
            "pagination": {"more": end < total},
        }
    )


class ItinerarioListView(LoginRequiredMixin, ListView):
    model = ItinerarioVPSL
    template_name = "ver_para_ser_libre/itinerario_list.html"
    context_object_name = "itinerarios"
    paginate_by = 10

    def get_queryset(self):
        query = (self.request.GET.get("busqueda") or "").strip()
        buscar_por = (self.request.GET.get("buscar_por") or "todos").strip()
        estado = (self.request.GET.get("estado") or "").strip()
        provincia_id = (self.request.GET.get("provincia") or "").strip()
        localidad = (self.request.GET.get("localidad") or "").strip()
        fecha_desde = parse_date((self.request.GET.get("fecha_desde") or "").strip())
        fecha_hasta = parse_date((self.request.GET.get("fecha_hasta") or "").strip())
        queryset = (
            ItinerarioVPSL.objects.select_related("provincia")
            .annotate(jornadas_total=Count("jornadas", distinct=True))
            .order_by("-fecha_inicio", "provincia__nombre")
        )
        queryset = _filtrar_itinerarios_por_usuario(queryset, self.request.user)
        if query:
            filtro_estado = _filtro_estado_itinerario_por_texto(query)
            filtros_busqueda = {
                "codigo": Q(codigo__icontains=query),
                "provincia": Q(provincia__nombre__icontains=query),
                "estado": filtro_estado,
                "referente": Q(referente_nombre__icontains=query)
                | Q(referente_apellido__icontains=query),
            }
            filtro = filtros_busqueda.get(buscar_por)
            if filtro is None:
                filtro = (
                    Q(codigo__icontains=query)
                    | Q(provincia__nombre__icontains=query)
                    | filtro_estado
                    | Q(referente_nombre__icontains=query)
                    | Q(referente_apellido__icontains=query)
                    | Q(sedes__nombre__icontains=query)
                    | Q(sedes__cueanexo__icontains=query)
                )
            queryset = queryset.filter(filtro)
        if estado:
            queryset = queryset.filter(estado=estado)
        if provincia_id and _puede_ver_todos_los_itinerarios(self.request.user):
            queryset = queryset.filter(provincia_id=provincia_id)
        if localidad:
            queryset = queryset.filter(
                Q(localidades_tentativas__icontains=localidad)
                | Q(sedes__localidad__icontains=localidad)
                | Q(jornadas__sede_vpsl__localidad__icontains=localidad)
            )
        if fecha_desde:
            queryset = queryset.filter(fecha_fin__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_inicio__lte=fecha_hasta)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provincia_usuario = (
            None
            if _puede_ver_todos_los_itinerarios(self.request.user)
            else _provincia_usuario_provincial(self.request.user)
        )
        context["query"] = self.request.GET.get("busqueda", "")
        context["filtros"] = {
            "busqueda": context["query"],
            "buscar_por": self.request.GET.get("buscar_por", "todos"),
            "estado": self.request.GET.get("estado", ""),
            "provincia": self.request.GET.get("provincia", ""),
            "localidad": self.request.GET.get("localidad", ""),
            "fecha_desde": self.request.GET.get("fecha_desde", ""),
            "fecha_hasta": self.request.GET.get("fecha_hasta", ""),
        }
        context["estado_choices"] = EstadoItinerario.choices
        context["provincias"] = Provincia.objects.order_by("nombre")
        context["provincia_restringida"] = provincia_usuario
        context["breadcrumb_items"] = _breadcrumb(
            {"text": "Itinerarios", "active": True}
        )
        return context


class ItinerarioCreateView(LoginRequiredMixin, CreateView):
    model = ItinerarioVPSL
    form_class = ItinerarioVPSLForm
    template_name = "ver_para_ser_libre/itinerario_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not _provincia_usuario_provincial(request.user):
            messages.error(
                request,
                "Para crear itinerarios debe ser usuario provincial y tener una provincia asignada.",
            )
            return redirect("vpsl_itinerario_list")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["provincia_bloqueada"] = _provincia_usuario_provincial(self.request.user)
        return kwargs

    def form_valid(self, form):
        form.instance.provincia = _provincia_usuario_provincial(self.request.user)
        form.instance.creado_por = self.request.user
        form.instance.modificado_por = self.request.user
        messages.success(self.request, "Itinerario creado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("vpsl_itinerario_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = _breadcrumb(
            {"text": "Nuevo itinerario", "active": True}
        )
        return context


class ItinerarioUpdateView(LoginRequiredMixin, UpdateView):
    model = ItinerarioVPSL
    form_class = ItinerarioVPSLForm
    template_name = "ver_para_ser_libre/itinerario_form.html"

    def get_queryset(self):
        return _filtrar_itinerarios_por_usuario(
            ItinerarioVPSL.objects.select_related("provincia"),
            self.request.user,
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.estado == EstadoItinerario.RECHAZADO:
            messages.error(request, "No se puede modificar un itinerario rechazado.")
            return redirect("vpsl_itinerario_detail", pk=self.object.pk)
        if self.object.estado == EstadoItinerario.EN_SUBSANACION:
            messages.error(
                request, "Use la accion Subsanar para corregir el itinerario."
            )
            return redirect("vpsl_itinerario_detail", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["freeze_completed_fields"] = (
            self.object.estado == EstadoItinerario.APROBADO
        )
        return kwargs

    def form_valid(self, form):
        form.instance.modificado_por = self.request.user
        if form.instance.estado == EstadoItinerario.APROBADO:
            messages.success(self.request, "Itinerario actualizado correctamente.")
            return super().form_valid(form)
        if form.instance.estado in {
            EstadoItinerario.PRESENTADO,
            EstadoItinerario.EN_REVISION,
            EstadoItinerario.OBSERVADO,
            EstadoItinerario.SUBSANADO,
        }:
            form.instance.estado = EstadoItinerario.SUBSANADO
        messages.success(self.request, "Itinerario actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("vpsl_itinerario_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = _breadcrumb(
            {"text": self.object.codigo, "url": self.get_success_url()},
            {"text": "Editar", "active": True},
        )
        return context


class ItinerarioDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = ItinerarioVPSL
    template_name = "ver_para_ser_libre/confirm_delete.html"
    success_url = reverse_lazy("vpsl_itinerario_list")
    success_message = "Itinerario eliminado correctamente."

    def get_queryset(self):
        return _filtrar_itinerarios_por_usuario(
            ItinerarioVPSL.objects.all(),
            self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delete_title"] = "Eliminar itinerario"
        context["delete_name"] = self.object.codigo
        context["cancel_url"] = reverse("vpsl_itinerario_list")
        return context


class ItinerarioSubsanarView(LoginRequiredMixin, UpdateView):
    model = ItinerarioVPSL
    form_class = ItinerarioVPSLForm
    template_name = "ver_para_ser_libre/itinerario_form.html"

    def get_queryset(self):
        return _filtrar_itinerarios_por_usuario(
            ItinerarioVPSL.objects.select_related("provincia"),
            self.request.user,
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.estado != EstadoItinerario.EN_SUBSANACION:
            messages.error(request, "El itinerario no esta en subsanacion.")
            return redirect("vpsl_itinerario_detail", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["subsanacion_only"] = True
        return kwargs

    def form_valid(self, form):
        form.instance.modificado_por = self.request.user
        form.instance.estado = EstadoItinerario.SUBSANADO
        form.instance.subsanacion_observaciones = ""
        messages.success(self.request, "Itinerario subsanado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("vpsl_itinerario_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow.asegurar_evaluaciones_sedes(self.object)
        context["componentes_subsanar"] = self._componentes_subsanar()
        context["breadcrumb_items"] = _breadcrumb(
            {"text": self.object.codigo, "url": self.get_success_url()},
            {"text": "Subsanar", "active": True},
        )
        context["subsanacion_mode"] = True
        return context

    def _componentes_subsanar(self):
        componentes = []
        if self.object.carta_referencia_estado == EstadoEvaluacionVPSL.SUBSANAR:
            componentes.append(
                {
                    "tipo": "Carta referencia",
                    "detalle": self.object.carta_referencia,
                }
            )
        if self.object.carta_archivo_estado == EstadoEvaluacionVPSL.SUBSANAR:
            componentes.append(
                {
                    "tipo": "Carta archivo",
                    "detalle": self.object.carta_archivo.name,
                }
            )
        for evaluacion in self.object.evaluaciones_sedes.select_related("sede").filter(
            estado=EstadoEvaluacionVPSL.SUBSANAR
        ):
            componentes.append(
                {
                    "tipo": "Sede",
                    "detalle": f"{evaluacion.sede.nombre} - {evaluacion.sede.localidad}",
                    "observacion": evaluacion.observacion,
                }
            )
        return componentes


class ItinerarioDetailView(LoginRequiredMixin, DetailView):
    model = ItinerarioVPSL
    template_name = "ver_para_ser_libre/itinerario_detail.html"
    context_object_name = "itinerario"

    def get_queryset(self):
        queryset = ItinerarioVPSL.objects.select_related("provincia").prefetch_related(
            "sedes",
            "evaluaciones_sedes__sede",
            "jornadas",
            "jornadas__registros",
        )
        return _filtrar_itinerarios_por_usuario(queryset, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jornadas = self.object.jornadas.select_related(
            "localidad", "municipio", "sede_vpsl"
        ).annotate(registros_total=Count("registros", distinct=True))
        context["jornadas"] = jornadas
        context["mostrar_presentar"] = self.object.estado in {
            EstadoItinerario.BORRADOR,
            EstadoItinerario.OBSERVADO,
        }
        context["mostrar_aprobar"] = self.object.estado in {
            EstadoItinerario.PRESENTADO,
            EstadoItinerario.EN_REVISION,
            EstadoItinerario.SUBSANADO,
        }
        context["mostrar_subsanar"] = (
            self.object.estado == EstadoItinerario.EN_SUBSANACION
        )
        context["puede_editar_itinerario"] = self.object.estado not in {
            EstadoItinerario.RECHAZADO,
            EstadoItinerario.EN_SUBSANACION,
        }
        context["puede_crear_jornada"] = self.object.estado == EstadoItinerario.APROBADO
        workflow.asegurar_evaluaciones_sedes(self.object)
        evaluaciones = {
            evaluacion.sede_id: evaluacion
            for evaluacion in self.object.evaluaciones_sedes.select_related("sede")
        }
        context["sedes_evaluadas"] = [
            {
                "sede": sede,
                "evaluacion": evaluaciones.get(sede.pk),
            }
            for sede in self.object.sedes.all()
        ]
        context["estado_evaluacion_choices"] = EstadoEvaluacionVPSL.choices
        context["evaluacion_obliga_rechazo"] = workflow.evaluacion_obliga_rechazo(
            self.object
        )
        context["motivo_aprobar_deshabilitado"] = self._motivo_aprobar_deshabilitado()
        context["puede_exportar"] = _puede_exportar(self.request.user)
        context["breadcrumb_items"] = _breadcrumb(
            {"text": self.object.codigo, "active": True}
        )
        return context

    def _motivo_aprobar_deshabilitado(self):
        if not workflow._carta_aprobada(self.object):
            return "Debe aprobar al menos una carta cargada."
        if not workflow.sedes_aprobadas_itinerario(self.object).exists():
            return "Debe aprobar al menos una sede tentativa."
        return ""


class ItinerarioExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_vpsl_itinerario.csv"

    def get_export_columns(self):
        return [
            ("Codigo itinerario", "codigo"),
            ("Provincia", "provincia"),
            ("Estado itinerario", "estado"),
            ("Fecha inicio", "fecha_inicio"),
            ("Fecha fin", "fecha_fin"),
            ("Referente", "referente"),
            ("Telefono referente", "referente_telefono"),
            ("Email referente", "referente_email"),
            ("Jornada fecha", "jornada_fecha"),
            ("Jornada sede", "jornada_sede"),
            ("Jornada localidad", "jornada_localidad"),
            ("Jornada vehiculo", "jornada_vehiculo"),
            ("Jornada estado", "jornada_estado"),
            ("Jornada horario", "jornada_horario"),
            ("Jornada referente", "jornada_referente"),
            ("Registros nominales", "registros_total"),
            ("Casos laboratorio", "casos_laboratorio"),
        ]

    def _get_itinerario(self):
        return get_object_or_404(
            _filtrar_itinerarios_por_usuario(
                ItinerarioVPSL.objects.select_related("provincia").prefetch_related(
                    "sedes",
                    "jornadas__sede_vpsl",
                    "jornadas__registros",
                    "jornadas__registros__caso_laboratorio",
                ),
                self.request.user,
            ),
            pk=self.kwargs["pk"],
        )

    def get(self, request, *args, **kwargs):
        itinerario = self._get_itinerario()
        jornadas = list(itinerario.jornadas.all().order_by("fecha", "sede"))
        rows = []
        for jornada in jornadas or [None]:
            registros = jornada.registros.all() if jornada else []
            rows.append(
                {
                    "codigo": itinerario.codigo,
                    "provincia": itinerario.provincia,
                    "estado": itinerario.get_estado_display(),
                    "fecha_inicio": itinerario.fecha_inicio,
                    "fecha_fin": itinerario.fecha_fin,
                    "referente": (
                        f"{itinerario.referente_nombre} "
                        f"{itinerario.referente_apellido}"
                    ).strip(),
                    "referente_telefono": itinerario.referente_telefono,
                    "referente_email": itinerario.referente_email,
                    "jornada_fecha": jornada.fecha if jornada else "",
                    "jornada_sede": jornada.sede if jornada else "",
                    "jornada_localidad": (
                        jornada.sede_vpsl.localidad
                        if jornada and jornada.sede_vpsl
                        else ""
                    ),
                    "jornada_vehiculo": (
                        jornada.get_vehiculo_display() if jornada else ""
                    ),
                    "jornada_estado": jornada.get_estado_display() if jornada else "",
                    "jornada_horario": (
                        f"{jornada.horario_inicio or ''} - {jornada.horario_fin or ''}"
                        if jornada
                        else ""
                    ),
                    "jornada_referente": (
                        f"{jornada.referente_nombre} {jornada.referente_apellido}".strip()
                        if jornada
                        else ""
                    ),
                    "registros_total": len(registros) if jornada else 0,
                    "casos_laboratorio": (
                        sum(
                            1
                            for registro in registros
                            if hasattr(registro, "caso_laboratorio")
                        )
                        if jornada
                        else 0
                    ),
                }
            )
        return self.export_csv(rows)


class SedeListView(LoginRequiredMixin, ListView):
    model = SedeVPSL
    template_name = "ver_para_ser_libre/sede_list.html"
    context_object_name = "sedes"
    paginate_by = 15

    def get_queryset(self):
        query = (self.request.GET.get("busqueda") or "").strip()
        queryset = SedeVPSL.objects.order_by("jurisdiccion", "localidad", "nombre")
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(cueanexo__icontains=query)
                | Q(jurisdiccion__icontains=query)
                | Q(localidad__icontains=query)
                | Q(domicilio__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        context["breadcrumb_items"] = _breadcrumb({"text": "Sedes", "active": True})
        return context


class SedeMixin:
    model = SedeVPSL
    form_class = SedeVPSLForm
    template_name = "ver_para_ser_libre/sede_form.html"

    def get_success_url(self):
        return reverse("vpsl_sede_update", kwargs={"pk": self.object.pk})

    def _build_checklist_form(self):
        kwargs = {"sede": getattr(self, "object", None)}
        if self.request.method == "POST":
            kwargs.update({"data": self.request.POST, "files": self.request.FILES})
        return ChecklistSedeVPSLForm(**kwargs)

    def form_valid(self, form):
        checklist_form = self._build_checklist_form()
        if not checklist_form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, checklist_form=checklist_form)
            )
        self.object = form.save()
        self._guardar_checklist_sede(checklist_form)
        messages.success(self.request, "Sede guardada correctamente.")
        return redirect(self.get_success_url())

    def _guardar_checklist_sede(self, checklist_form):
        for item_code, label in ChecklistSedeVPSLForm.ITEMS:
            checklist, _ = self.object.checklist.get_or_create(
                item=item_code,
                defaults={"descripcion": label, "critico": True},
            )
            old_cumple = checklist.cumple
            old_observacion = checklist.observacion
            checklist.descripcion = label
            checklist.critico = True
            checklist.cumple = checklist_form.cleaned_data[f"{item_code}_cumple"]
            checklist.observacion = checklist_form.cleaned_data.get(
                f"{item_code}_observacion", ""
            )
            evidencia = checklist_form.cleaned_data.get(f"{item_code}_evidencia")
            if evidencia:
                checklist.evidencia = evidencia
            checklist.save()
            if (
                old_cumple != checklist.cumple
                or old_observacion != checklist.observacion
            ):
                HistorialChecklistSedeVPSL.objects.create(
                    checklist=checklist,
                    cumple_anterior=old_cumple,
                    cumple_nuevo=checklist.cumple,
                    observacion_anterior=old_observacion,
                    observacion_nueva=checklist.observacion,
                    usuario=self.request.user,
                )
        self.object.checklist_aprobado = not self.object.checklist.exclude(
            cumple=True
        ).exists()
        self.object.save(update_fields=["checklist_aprobado"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checklist_form = kwargs.get("checklist_form") or ChecklistSedeVPSLForm(
            sede=getattr(self, "object", None)
        )
        context["checklist_form"] = checklist_form
        context["field_groups"] = checklist_form.field_groups
        sede = getattr(self, "object", None)
        context["mapa_query"] = quote_plus(sede.mapa_query) if sede else ""
        context["breadcrumb_items"] = _breadcrumb(
            {"text": "Sedes", "url": reverse("vpsl_sede_list")},
            {"text": "Editar" if sede else "Nueva sede", "active": True},
        )
        return context


class SedeCreateView(LoginRequiredMixin, SedeMixin, CreateView):
    pass


class SedeUpdateView(LoginRequiredMixin, SedeMixin, UpdateView):
    pass


class SedeDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = SedeVPSL
    template_name = "ver_para_ser_libre/confirm_delete.html"
    success_url = reverse_lazy("vpsl_sede_list")
    success_message = "Sede eliminada correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delete_title"] = "Eliminar sede"
        context["delete_name"] = self.object.nombre
        context["cancel_url"] = reverse("vpsl_sede_list")
        return context


def presentar_itinerario(request, pk):
    itinerario = get_object_or_404(
        _filtrar_itinerarios_por_usuario(ItinerarioVPSL.objects.all(), request.user),
        pk=pk,
    )
    try:
        workflow.presentar_itinerario(itinerario, usuario=request.user)
        messages.success(request, "Itinerario presentado a Nacion.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("vpsl_itinerario_detail", pk=pk)


def aprobar_itinerario(request, pk):
    itinerario = get_object_or_404(
        _filtrar_itinerarios_por_usuario(ItinerarioVPSL.objects.all(), request.user),
        pk=pk,
    )
    _actualizar_evaluacion_itinerario_desde_request(itinerario, request)
    accion = request.POST.get("accion_evaluacion")
    try:
        if accion == "rechazar":
            workflow.rechazar_itinerario(
                itinerario,
                usuario=request.user,
                observacion=request.POST.get("subsanacion_observaciones", ""),
            )
            messages.success(request, "Itinerario rechazado.")
        elif accion == "subsanar":
            workflow.enviar_itinerario_a_subsanacion(
                itinerario,
                usuario=request.user,
                observacion=request.POST.get("subsanacion_observaciones", ""),
            )
            messages.success(request, "Itinerario enviado a subsanacion.")
        else:
            workflow.aprobar_itinerario(itinerario, usuario=request.user)
            messages.success(request, "Itinerario aprobado.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("vpsl_itinerario_detail", pk=pk)


def _actualizar_evaluacion_itinerario_desde_request(itinerario, request):
    if itinerario.carta_referencia:
        itinerario.carta_referencia_estado = request.POST.get(
            "carta_referencia_estado",
            itinerario.carta_referencia_estado,
        )
    if itinerario.carta_archivo:
        itinerario.carta_archivo_estado = request.POST.get(
            "carta_archivo_estado",
            itinerario.carta_archivo_estado,
        )
    itinerario.save(
        update_fields=[
            "carta_referencia_estado",
            "carta_archivo_estado",
        ]
    )
    workflow.asegurar_evaluaciones_sedes(itinerario)
    for evaluacion in itinerario.evaluaciones_sedes.all():
        estado = request.POST.get(f"sede_{evaluacion.sede_id}_estado")
        observacion = request.POST.get(f"sede_{evaluacion.sede_id}_observacion", "")
        if estado:
            evaluacion.estado = estado
            evaluacion.observacion = observacion
            evaluacion.save(update_fields=["estado", "observacion", "updated_at"])


class JornadaCreateView(LoginRequiredMixin, CreateView):
    model = JornadaVPSL
    form_class = JornadaVPSLForm
    template_name = "ver_para_ser_libre/jornada_form.html"

    def dispatch(self, request, *args, **kwargs):
        itinerario = get_object_or_404(
            _filtrar_itinerarios_por_usuario(
                ItinerarioVPSL.objects.all(), request.user
            ),
            pk=self.kwargs["itinerario_pk"],
        )
        if itinerario.estado != EstadoItinerario.APROBADO:
            messages.error(
                request,
                "Solo se pueden crear jornadas en itinerarios aprobados.",
            )
            return redirect("vpsl_itinerario_detail", pk=itinerario.pk)
        if not workflow.sedes_aprobadas_itinerario(itinerario).exists():
            messages.error(
                request,
                "El itinerario no tiene sedes aprobadas para crear jornadas.",
            )
            return redirect("vpsl_itinerario_detail", pk=itinerario.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        itinerario = get_object_or_404(
            _filtrar_itinerarios_por_usuario(
                ItinerarioVPSL.objects.all(),
                self.request.user,
            ),
            pk=self.kwargs["itinerario_pk"],
        )
        form.instance.itinerario = itinerario
        form.instance.referente_nombre = self.request.POST.get(
            "referente_nombre_renaper", ""
        )
        form.instance.referente_apellido = self.request.POST.get(
            "referente_apellido_renaper", ""
        )
        form.instance.referente_validado_renaper = bool(
            form.instance.referente_nombre or form.instance.referente_apellido
        )
        try:
            self.object = form.save()
        except IntegrityError:
            form.add_error(
                "fecha",
                "Ya existe una jornada para este itinerario con la misma fecha y sede.",
            )
            return self.form_invalid(form)
        workflow.sincronizar_estado_checklist_jornada(
            self.object,
            usuario=self.request.user,
        )
        messages.success(self.request, "Jornada creada correctamente.")
        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["itinerario"] = get_object_or_404(
            _filtrar_itinerarios_por_usuario(
                ItinerarioVPSL.objects.all(),
                self.request.user,
            ),
            pk=self.kwargs["itinerario_pk"],
        )
        return kwargs

    def get_success_url(self):
        return reverse("vpsl_jornada_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        itinerario = get_object_or_404(
            _filtrar_itinerarios_por_usuario(
                ItinerarioVPSL.objects.all(),
                self.request.user,
            ),
            pk=self.kwargs["itinerario_pk"],
        )
        context["itinerario"] = itinerario
        context["sede_data"] = {
            str(sede.pk): {
                "nombre": sede.nombre,
                "localidad": sede.localidad,
                "domicilio": sede.domicilio,
                "jurisdiccion": sede.jurisdiccion,
            }
            for sede in itinerario.sedes.all()
        }
        context["breadcrumb_items"] = _breadcrumb(
            {
                "text": itinerario.codigo,
                "url": reverse("vpsl_itinerario_detail", kwargs={"pk": itinerario.pk}),
            },
            {"text": "Nueva jornada", "active": True},
        )
        return context


class JornadaUpdateView(LoginRequiredMixin, UpdateView):
    model = JornadaVPSL
    form_class = JornadaVPSLForm
    template_name = "ver_para_ser_libre/jornada_form.html"

    def get_queryset(self):
        return _filtrar_jornadas_por_usuario(
            JornadaVPSL.objects.select_related("itinerario", "sede_vpsl"),
            self.request.user,
        )

    def get_success_url(self):
        return reverse("vpsl_jornada_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        form.instance.referente_nombre = self.request.POST.get(
            "referente_nombre_renaper", form.instance.referente_nombre
        )
        form.instance.referente_apellido = self.request.POST.get(
            "referente_apellido_renaper", form.instance.referente_apellido
        )
        if form.instance.referente_nombre or form.instance.referente_apellido:
            form.instance.referente_validado_renaper = True
        self.object = form.save()
        workflow.sincronizar_estado_checklist_jornada(
            self.object,
            usuario=self.request.user,
        )
        messages.success(self.request, "Jornada actualizada correctamente.")
        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["itinerario"] = self.object.itinerario
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["itinerario"] = self.object.itinerario
        context["sede_data"] = {
            str(sede.pk): {
                "nombre": sede.nombre,
                "localidad": sede.localidad,
                "domicilio": sede.domicilio,
                "jurisdiccion": sede.jurisdiccion,
            }
            for sede in self.object.itinerario.sedes.all()
        }
        context["breadcrumb_items"] = _breadcrumb(
            {
                "text": self.object.itinerario.codigo,
                "url": reverse(
                    "vpsl_itinerario_detail", kwargs={"pk": self.object.itinerario.pk}
                ),
            },
            {"text": "Editar jornada", "active": True},
        )
        return context


class JornadaDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = JornadaVPSL
    template_name = "ver_para_ser_libre/confirm_delete.html"
    success_message = "Jornada eliminada correctamente."

    def get_queryset(self):
        return _filtrar_jornadas_por_usuario(
            JornadaVPSL.objects.select_related("itinerario"),
            self.request.user,
        )

    def get_success_url(self):
        return reverse(
            "vpsl_itinerario_detail",
            kwargs={"pk": self.object.itinerario_id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delete_title"] = "Eliminar jornada"
        context["delete_name"] = self.object.fecha.strftime("%d/%m/%Y")
        context["cancel_url"] = self.get_success_url()
        return context


class JornadaDetailView(LoginRequiredMixin, DetailView):
    model = JornadaVPSL
    template_name = "ver_para_ser_libre/jornada_detail.html"
    context_object_name = "jornada"

    def get_queryset(self):
        queryset = JornadaVPSL.objects.select_related(
            "itinerario", "localidad", "municipio", "sede_vpsl"
        )
        return _filtrar_jornadas_por_usuario(queryset, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sede = self.object.sede_vpsl
        context["checklist"] = sede.checklist.all() if sede else []
        context["registros"] = self.object.registros.all()[:25]
        casos_laboratorio = CasoLaboratorioVPSL.objects.filter(
            registro__jornada=self.object
        ).select_related("registro")
        for caso in casos_laboratorio:
            caso.estado_siguiente = workflow.siguiente_estado_laboratorio(caso)
            caso.estado_siguiente_label = (
                EstadoLaboratorio(caso.estado_siguiente).label
                if caso.estado_siguiente
                else ""
            )
        context["casos_laboratorio"] = casos_laboratorio
        try:
            cierre = self.object.cierre
        except CierreDiarioVPSL.DoesNotExist:
            cierre = None
        if cierre:
            cierre = workflow.actualizar_consistencia_cierre(self.object)
        context["cierre"] = cierre
        context["cierre_inconsistente"] = bool(cierre and not cierre.consistente)
        context["puede_cierre_definitivo"] = bool(cierre and cierre.consistente)
        context["habilitar_bloqueado"] = not (
            sede
            and sede.checklist.exists()
            and not sede.checklist.exclude(cumple=True).exists()
        )
        context["mostrar_habilitar_jornada"] = (
            self.object.estado in workflow.JORNADA_ESTADOS_HABILITABLES
        )
        context["puede_habilitar_jornada"] = (
            self.object.estado in workflow.JORNADA_ESTADOS_HABILITABLES
            and not context["habilitar_bloqueado"]
        )
        context["puede_cerrar_jornada"] = (
            self.object.estado in workflow.JORNADA_ESTADOS_CIERRE_PERMITIDO
        )
        context["puede_registrar_jornada"] = (
            self.object.estado in workflow.JORNADA_ESTADOS_REGISTRO_PERMITIDO
        )
        context["checklist_resumen"] = [
            {
                "label": label,
                "cumple": next(
                    (
                        item.cumple
                        for item in context["checklist"]
                        if item.item == item_code
                    ),
                    None,
                ),
            }
            for item_code, label in ChecklistSedeVPSLForm.ITEMS
        ]
        context["checklist_completo"] = workflow.checklist_sede_completo(sede)
        context["mapa_query"] = quote_plus(sede.mapa_query) if sede else ""
        context["sede_resumen"] = {
            "escuela": sede.nombre if sede else self.object.sede,
            "provincia": sede.jurisdiccion if sede else "",
            "localidad": sede.localidad if sede else "",
            "calle_altura": sede.domicilio if sede else self.object.direccion,
        }
        context["puede_exportar"] = _puede_exportar(self.request.user)
        context["breadcrumb_items"] = _breadcrumb(
            {
                "text": self.object.itinerario.codigo,
                "url": reverse(
                    "vpsl_itinerario_detail", kwargs={"pk": self.object.itinerario.pk}
                ),
            },
            {"text": "Jornada", "active": True},
        )
        return context


class JornadaExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_vpsl_jornada.csv"

    def get_export_columns(self):
        return [
            ("Itinerario", "itinerario"),
            ("Provincia", "provincia"),
            ("Jornada fecha", "fecha"),
            ("Jornada estado", "estado"),
            ("Sede", "sede"),
            ("Localidad", "localidad"),
            ("Direccion", "direccion"),
            ("Vehiculo", "vehiculo"),
            ("Horario inicio", "horario_inicio"),
            ("Horario fin", "horario_fin"),
            ("Referente", "referente"),
            ("Telefono referente", "referente_telefono"),
            ("Email referente", "referente_email"),
            ("Acta", "numero_acta"),
            ("DNI", "dni"),
            ("Apellido", "apellido"),
            ("Nombre", "nombre"),
            ("Sexo", "sexo"),
            ("Edad", "edad"),
            ("Telefono", "telefono"),
            ("Fecha atencion", "fecha_atencion"),
            ("Prescripcion", "prescripcion"),
            ("Resultado", "resultado"),
            ("Cantidad lentes", "cantidad_lentes"),
            ("Primera vez anteojos", "primera_vez_anteojos"),
            ("Caso laboratorio estado", "laboratorio_estado"),
        ]

    def _get_jornada(self):
        return get_object_or_404(
            _filtrar_jornadas_por_usuario(
                JornadaVPSL.objects.select_related(
                    "itinerario",
                    "itinerario__provincia",
                    "sede_vpsl",
                ).prefetch_related("registros", "registros__caso_laboratorio"),
                self.request.user,
            ),
            pk=self.kwargs["pk"],
        )

    def get(self, request, *args, **kwargs):
        jornada = self._get_jornada()
        registros = list(jornada.registros.all())
        rows = []
        for registro in registros or [None]:
            caso = getattr(registro, "caso_laboratorio", None) if registro else None
            rows.append(
                {
                    "itinerario": jornada.itinerario.codigo,
                    "provincia": jornada.itinerario.provincia,
                    "fecha": jornada.fecha,
                    "estado": jornada.get_estado_display(),
                    "sede": jornada.sede,
                    "localidad": (
                        jornada.sede_vpsl.localidad if jornada.sede_vpsl else ""
                    ),
                    "direccion": jornada.direccion,
                    "vehiculo": jornada.get_vehiculo_display(),
                    "horario_inicio": jornada.horario_inicio,
                    "horario_fin": jornada.horario_fin,
                    "referente": (
                        f"{jornada.referente_nombre} {jornada.referente_apellido}"
                    ).strip(),
                    "referente_telefono": jornada.referente_telefono,
                    "referente_email": jornada.referente_email,
                    "numero_acta": registro.numero_acta if registro else "",
                    "dni": registro.dni if registro else "",
                    "apellido": registro.apellido if registro else "",
                    "nombre": registro.nombre if registro else "",
                    "sexo": (registro.genero or registro.sexo) if registro else "",
                    "edad": registro.edad if registro else "",
                    "telefono": registro.telefono if registro else "",
                    "fecha_atencion": registro.fecha_atencion if registro else "",
                    "prescripcion": registro.prescripcion if registro else "",
                    "resultado": registro.get_resultado_display() if registro else "",
                    "cantidad_lentes": registro.cantidad_lentes if registro else "",
                    "primera_vez_anteojos": (
                        registro.primera_vez_anteojos if registro else ""
                    ),
                    "laboratorio_estado": caso.get_estado_display() if caso else "",
                }
            )
        return self.export_csv(rows)


def habilitar_jornada(request, pk):
    jornada = get_object_or_404(
        _filtrar_jornadas_por_usuario(JornadaVPSL.objects.all(), request.user),
        pk=pk,
    )
    try:
        workflow.habilitar_jornada(jornada, usuario=request.user)
        messages.success(request, "Jornada habilitada.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("vpsl_jornada_detail", pk=pk)


def cierre_definitivo_jornada(request, pk):
    jornada = get_object_or_404(
        _filtrar_jornadas_por_usuario(JornadaVPSL.objects.all(), request.user),
        pk=pk,
    )
    try:
        workflow.cerrar_jornada_definitivamente(jornada, usuario=request.user)
        messages.success(request, "Cierre definitivo confirmado.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("vpsl_jornada_detail", pk=pk)


class ChecklistCreateView(LoginRequiredMixin, View):
    template_name = "ver_para_ser_libre/checklist_form.html"

    def _get_jornada(self):
        return get_object_or_404(
            _filtrar_jornadas_por_usuario(
                JornadaVPSL.objects.select_related("sede_vpsl"),
                self.request.user,
            ),
            pk=self.kwargs["jornada_pk"],
        )

    def get(self, request, *args, **kwargs):
        jornada = self._get_jornada()
        form = ChecklistSedeVPSLForm(sede=jornada.sede_vpsl)
        return self._render(request, jornada, form)

    def post(self, request, *args, **kwargs):
        jornada = self._get_jornada()
        form = ChecklistSedeVPSLForm(
            request.POST,
            request.FILES,
            sede=jornada.sede_vpsl,
        )
        if not form.is_valid():
            return self._render(request, jornada, form)
        for item_code, label in ChecklistSedeVPSLForm.ITEMS:
            checklist, _ = jornada.sede_vpsl.checklist.get_or_create(
                item=item_code,
                defaults={
                    "jornada": jornada,
                    "descripcion": label,
                    "critico": True,
                },
            )
            old_cumple = checklist.cumple
            old_observacion = checklist.observacion
            checklist.jornada = jornada
            checklist.descripcion = label
            checklist.critico = True
            checklist.cumple = form.cleaned_data[f"{item_code}_cumple"]
            checklist.observacion = form.cleaned_data.get(
                f"{item_code}_observacion", ""
            )
            evidencia = form.cleaned_data.get(f"{item_code}_evidencia")
            if evidencia:
                checklist.evidencia = evidencia
            checklist.save()
            if (
                old_cumple != checklist.cumple
                or old_observacion != checklist.observacion
            ):
                HistorialChecklistSedeVPSL.objects.create(
                    checklist=checklist,
                    cumple_anterior=old_cumple,
                    cumple_nuevo=checklist.cumple,
                    observacion_anterior=old_observacion,
                    observacion_nueva=checklist.observacion,
                    usuario=request.user,
                )
        jornada.sede_vpsl.checklist_aprobado = not jornada.sede_vpsl.checklist.exclude(
            cumple=True
        ).exists()
        jornada.sede_vpsl.save(update_fields=["checklist_aprobado"])
        workflow.sincronizar_estado_checklist_jornada(jornada, usuario=request.user)
        messages.success(request, "Checklist de sede guardado correctamente.")
        return redirect(self.get_success_url())

    def _render(self, request, jornada, form):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "field_groups": form.field_groups,
                "jornada": jornada,
                "sede": jornada.sede_vpsl,
            },
        )

    def get_success_url(self):
        return reverse("vpsl_jornada_detail", kwargs={"pk": self.kwargs["jornada_pk"]})


class RegistroNominalCreateView(LoginRequiredMixin, CreateView):
    model = RegistroNominalVPSL
    form_class = RegistroNominalVPSLForm
    template_name = "ver_para_ser_libre/registro_form.html"

    def get_jornada(self):
        return get_object_or_404(
            _filtrar_jornadas_por_usuario(JornadaVPSL.objects.all(), self.request.user),
            pk=self.kwargs["jornada_pk"],
        )

    def dispatch(self, request, *args, **kwargs):
        jornada = self.get_jornada()
        if jornada.estado not in workflow.JORNADA_ESTADOS_REGISTRO_PERMITIDO:
            messages.error(
                request,
                "La jornada debe estar habilitada para cargar registros nominales.",
            )
            return redirect("vpsl_jornada_detail", pk=jornada.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["jornada"] = self.get_jornada()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        jornada = self.get_jornada()
        initial.update({"fecha_atencion": jornada.fecha, "escuela_sede": jornada.sede})
        return initial

    def form_valid(self, form):
        jornada = self.get_jornada()
        form.instance.jornada = jornada
        form.instance.escuela_sede = jornada.sede
        estado_renaper = self.request.POST.get("renaper_estado")
        if estado_renaper == "validado":
            if not form.instance.dni:
                form.add_error("dni", "Debe ingresar DNI para validar RENAPER.")
                return self.form_invalid(form)
            resultado = _resolver_ciudadano_registro_vpsl(
                form.instance.dni, form.instance.sexo, self.request.user
            )
            if not resultado.get("success"):
                form.add_error(None, resultado.get("message"))
                return self.form_invalid(form)
            _aplicar_validacion_ciudadano_a_registro(form.instance, resultado)
            if not _validar_registro_no_duplicado(form, jornada, form.instance.dni):
                return self.form_invalid(form)
        else:
            form.add_error(None, "Debe verificar RENAPER antes de guardar.")
            return self.form_invalid(form)
        try:
            self.object = workflow.guardar_registro_nominal(
                form.instance, usuario=self.request.user
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Se creo el registro correctamente")
        return redirect("vpsl_registro_create", jornada_pk=jornada.pk)

    def get_success_url(self):
        return reverse("vpsl_jornada_detail", kwargs={"pk": self.kwargs["jornada_pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jornada = self.get_jornada()
        context["jornada"] = jornada
        context["submit_text"] = "Guardar y continuar"
        context["breadcrumb_items"] = _breadcrumb(
            {
                "text": jornada.itinerario.codigo,
                "url": reverse(
                    "vpsl_itinerario_detail", kwargs={"pk": jornada.itinerario.pk}
                ),
            },
            {"text": "Registro nominal", "active": True},
        )
        return context


class RegistroNominalUpdateView(LoginRequiredMixin, UpdateView):
    model = RegistroNominalVPSL
    form_class = RegistroNominalVPSLForm
    template_name = "ver_para_ser_libre/registro_form.html"

    def get_queryset(self):
        return RegistroNominalVPSL.objects.filter(
            jornada__in=_filtrar_jornadas_por_usuario(
                JornadaVPSL.objects.all(),
                self.request.user,
            )
        ).select_related("jornada", "jornada__itinerario")

    def form_valid(self, form):
        estado_renaper = self.request.POST.get("renaper_estado")
        if estado_renaper == "validado":
            if not form.instance.dni:
                form.add_error("dni", "Debe ingresar DNI para validar RENAPER.")
                return self.form_invalid(form)
            resultado = _resolver_ciudadano_registro_vpsl(
                form.instance.dni, form.instance.sexo, self.request.user
            )
            if not resultado.get("success"):
                form.add_error(None, resultado.get("message"))
                return self.form_invalid(form)
            _aplicar_validacion_ciudadano_a_registro(form.instance, resultado)
            if not _validar_registro_no_duplicado(
                form,
                form.instance.jornada,
                form.instance.dni,
                exclude_pk=form.instance.pk,
            ):
                return self.form_invalid(form)
        else:
            form.add_error(None, "Debe verificar RENAPER antes de guardar.")
            return self.form_invalid(form)
        try:
            self.object = workflow.guardar_registro_nominal(
                form.instance, usuario=self.request.user
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Registro nominal actualizado.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("vpsl_jornada_detail", kwargs={"pk": self.object.jornada_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jornada"] = self.object.jornada
        context["submit_text"] = "Guardar"
        context["breadcrumb_items"] = _breadcrumb(
            {"text": "Jornada", "url": self.get_success_url()},
            {"text": "Editar registro", "active": True},
        )
        return context


class RegistroNominalDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = RegistroNominalVPSL
    template_name = "ver_para_ser_libre/confirm_delete.html"
    success_message = "Registro nominal eliminado correctamente."

    def get_queryset(self):
        return RegistroNominalVPSL.objects.filter(
            jornada__in=_filtrar_jornadas_por_usuario(
                JornadaVPSL.objects.all(),
                self.request.user,
            )
        ).select_related("jornada")

    def get_success_url(self):
        return reverse(
            "vpsl_jornada_detail",
            kwargs={"pk": self.object.jornada_id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delete_title"] = "Eliminar registro nominal"
        context["delete_name"] = (
            f"{self.object.apellido}, {self.object.nombre} "
            f"- Acta {self.object.numero_acta}"
        )
        context["cancel_url"] = self.get_success_url()
        return context


def actualizar_laboratorio_masivo(request, pk):
    jornada = get_object_or_404(
        _filtrar_jornadas_por_usuario(JornadaVPSL.objects.all(), request.user),
        pk=pk,
    )
    caso_ids = [value for value in request.POST.getlist("casos") if value.isdigit()]
    fecha = parse_date(request.POST.get("fecha") or "")
    responsable = (request.POST.get("responsable") or "").strip()
    if not caso_ids:
        messages.error(request, "Seleccione al menos un caso de laboratorio.")
        return redirect("vpsl_jornada_detail", pk=jornada.pk)
    if not fecha or not responsable:
        messages.error(request, "Debe informar fecha y responsable.")
        return redirect("vpsl_jornada_detail", pk=jornada.pk)

    casos = list(
        _filtrar_casos_laboratorio_por_usuario(
            CasoLaboratorioVPSL.objects.filter(
                pk__in=caso_ids,
                registro__jornada=jornada,
            ).select_related("registro", "registro__jornada"),
            request.user,
        )
    )
    if len(casos) != len(set(caso_ids)):
        messages.error(request, "La seleccion contiene casos no disponibles.")
        return redirect("vpsl_jornada_detail", pk=jornada.pk)

    estados = {caso.estado for caso in casos}
    if len(estados) != 1:
        messages.error(
            request,
            "Solo se pueden actualizar de forma masiva casos que comparten estado.",
        )
        return redirect("vpsl_jornada_detail", pk=jornada.pk)
    if not workflow.siguiente_estado_laboratorio(casos[0]):
        messages.error(request, "Los casos seleccionados no tienen estado siguiente.")
        return redirect("vpsl_jornada_detail", pk=jornada.pk)

    try:
        with transaction.atomic():
            for caso in casos:
                workflow.avanzar_estado_laboratorio(
                    caso,
                    fecha=fecha,
                    responsable=responsable,
                    usuario=request.user,
                )
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        messages.success(
            request,
            f"Se actualizaron {len(casos)} casos de laboratorio correctamente.",
        )
    return redirect("vpsl_jornada_detail", pk=jornada.pk)


class CasoLaboratorioUpdateView(LoginRequiredMixin, UpdateView):
    model = CasoLaboratorioVPSL
    form_class = CasoLaboratorioVPSLForm
    template_name = "ver_para_ser_libre/simple_form.html"

    def get_queryset(self):
        return _filtrar_casos_laboratorio_por_usuario(
            CasoLaboratorioVPSL.objects.select_related("registro", "registro__jornada"),
            self.request.user,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["next_state"] = workflow.siguiente_estado_laboratorio(self.object)
        return kwargs

    def get_success_url(self):
        return reverse(
            "vpsl_jornada_detail", kwargs={"pk": self.object.registro.jornada_id}
        )

    def form_valid(self, form):
        try:
            self.object = workflow.avanzar_estado_laboratorio(
                self.object,
                fecha=form.cleaned_data["fecha"],
                responsable=form.cleaned_data["responsable"],
                usuario=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Estado de laboratorio actualizado.")
        return redirect(self.get_success_url())


class CierreDiarioCreateView(LoginRequiredMixin, CreateView):
    model = CierreDiarioVPSL
    form_class = CierreDiarioVPSLForm
    template_name = "ver_para_ser_libre/simple_form.html"

    def get_jornada(self):
        return get_object_or_404(
            _filtrar_jornadas_por_usuario(JornadaVPSL.objects.all(), self.request.user),
            pk=self.kwargs["jornada_pk"],
        )

    def get_initial(self):
        initial = super().get_initial()
        jornada = self.get_jornada()
        try:
            cierre = jornada.cierre
        except CierreDiarioVPSL.DoesNotExist:
            cierre = None
        if cierre:
            initial.update(
                {
                    "cantidad_atenciones_registradas": cierre.cantidad_atenciones_registradas,
                    "cantidad_lentes_entregados_dia": cierre.cantidad_lentes_entregados_dia,
                    "cantidad_casos_laboratorio_reportados": cierre.cantidad_casos_laboratorio_reportados,
                    "responsable_cierre": cierre.responsable_cierre,
                    "observaciones": cierre.observaciones,
                }
            )
        return initial

    def form_valid(self, form):
        jornada = self.get_jornada()
        try:
            self.object = workflow.generar_cierre_diario(
                jornada,
                responsable=form.cleaned_data["responsable_cierre"],
                cantidad_atenciones_registradas=form.cleaned_data[
                    "cantidad_atenciones_registradas"
                ],
                cantidad_lentes_entregados_dia=form.cleaned_data[
                    "cantidad_lentes_entregados_dia"
                ],
                cantidad_casos_laboratorio_reportados=form.cleaned_data[
                    "cantidad_casos_laboratorio_reportados"
                ],
                acta_adjunta=form.cleaned_data["acta_adjunta"],
                usuario=self.request.user,
                observaciones=form.cleaned_data.get("observaciones", ""),
            )
            if self.object.consistente:
                messages.success(self.request, "Cierre diario generado.")
            else:
                messages.warning(
                    self.request,
                    "No hay coincidencia entre los registros nominales y el cierre.",
                )
            return redirect(self.get_success_url())
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("vpsl_jornada_detail", kwargs={"pk": self.kwargs["jornada_pk"]})
