import logging
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from ciudadanos.forms import CiudadanoFiltroForm, CiudadanoForm, GrupoFamiliarForm
from ciudadanos.models import Ciudadano, GrupoFamiliar
from comedores.services.comedor_service import ComedorService
from core.models import Localidad, Municipio
from core.security import safe_redirect
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin

logger = logging.getLogger("django")


class CiudadanosListView(LoginRequiredMixin, ListView):
    template_name = "ciudadanos/ciudadano_list.html"
    context_object_name = "ciudadanos"
    paginate_by = 25

    def get_queryset(self):
        queryset = Ciudadano.objects.select_related(
            "sexo", "provincia", "municipio", "localidad"
        )
        form = CiudadanoFiltroForm(self.request.GET or None)
        if form.is_valid():
            data = form.cleaned_data
            if data.get("q"):
                term = data["q"].strip()
                queryset = queryset.filter(
                    Q(apellido__icontains=term)
                    | Q(nombre__icontains=term)
                    | Q(documento__icontains=term)
                )
            if data.get("provincia"):
                queryset = queryset.filter(provincia=data["provincia"])
        return queryset.order_by("apellido", "nombre")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = CiudadanoFiltroForm(self.request.GET or None)
        return ctx


class CiudadanosDetailView(LoginRequiredMixin, DetailView):
    model = Ciudadano
    template_name = "ciudadanos/ciudadano_detail.html"
    context_object_name = "ciudadano"
    MESES_NOMBRES = [
        "",
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ciudadano = self.object
        ctx.update(
            familia=self.build_familia(ciudadano),
            grupo_form=GrupoFamiliarForm(ciudadano=ciudadano),
            google_maps_api_key=settings.GOOGLE_MAPS_API_KEY,
            interacciones=ciudadano.interacciones.all()[:10],
        )
        ctx.update(self.get_programas_context(ciudadano))
        ctx.update(self.get_historial_context(ciudadano))
        ctx.update(self.get_celiaquia_context(ciudadano))
        ctx.update(self.get_cdf_context(ciudadano))
        ctx.update(self.get_comedor_context(ciudadano))
        ctx.update(self.get_vat_context(ciudadano))
        return ctx

    def build_familia(self, ciudadano):
        relaciones = (
            GrupoFamiliar.objects.filter(
                Q(ciudadano_1=ciudadano) | Q(ciudadano_2=ciudadano)
            )
            .select_related("ciudadano_1", "ciudadano_2")
            .order_by("ciudadano_2__apellido")
        )
        familia = []
        for relacion in relaciones:
            familiar = (
                relacion.ciudadano_2
                if relacion.ciudadano_1_id == ciudadano.id
                else relacion.ciudadano_1
            )
            familia.append((relacion, familiar))
        return familia

    def get_programas_context(self, ciudadano):
        from ciudadanos.models import ProgramaTransferencia

        programas = ciudadano.programas_transferencia.filter(activo=True)
        return {
            "programas_directos": programas.filter(
                categoria=ProgramaTransferencia.CATEGORIA_DIRECTA
            ),
            "programas_indirectos": programas.filter(
                categoria=ProgramaTransferencia.CATEGORIA_INDIRECTA
            ),
        }

    def get_historial_context(self, ciudadano):
        historial = ciudadano.historial_transferencias.filter(
            anio__gte=timezone.now().year - 1
        ).order_by("anio", "mes")

        return {
            "historial_labels": [self.MESES_NOMBRES[h.mes] for h in historial],
            "historial_auh": [float(h.monto_auh) for h in historial],
            "historial_prestacion": [
                float(h.monto_prestacion_alimentar) for h in historial
            ],
            "historial_centro_familia": [
                float(h.monto_centro_familia) for h in historial
            ],
            "historial_comedor": [float(h.monto_comedor) for h in historial],
        }

    def get_celiaquia_context(self, ciudadano):
        try:
            from celiaquia.models import ExpedienteCiudadano
        except ImportError:
            return {"expedientes_celiaquia": []}

        try:
            expedientes = (
                ExpedienteCiudadano.objects.filter(ciudadano=ciudadano)
                .select_related("expediente", "estado")
                .order_by("-creado_en")
            )
        except Exception:
            logger.exception(
                "Error cargando expedientes celiaquia para ciudadano %s", ciudadano.pk
            )
            return {"expedientes_celiaquia": []}
        contexto = {"expedientes_celiaquia": expedientes}
        expediente_actual = expedientes.first()
        if expediente_actual:
            contexto["expediente_actual"] = expediente_actual
        return contexto

    def get_cdf_context(self, ciudadano):
        try:
            from centrodefamilia.models import ParticipanteActividad
        except ImportError:
            return {"participaciones_cdf": [], "costo_total_cdf": 0}

        try:
            participaciones = (
                ParticipanteActividad.objects.filter(ciudadano=ciudadano)
                .select_related(
                    "actividad_centro__centro", "actividad_centro__actividad"
                )
                .order_by("-fecha_registro")
            )
            costo_total_cdf = (
                ParticipanteActividad.objects.filter(
                    ciudadano=ciudadano, estado="inscrito"
                ).aggregate(total=Sum("actividad_centro__precio"))["total"]
                or 0
            )
        except Exception:
            logger.exception(
                "Error cargando participaciones CDF para ciudadano %s", ciudadano.pk
            )
            return {"participaciones_cdf": [], "costo_total_cdf": 0}
        return {
            "participaciones_cdf": participaciones,
            "costo_total_cdf": costo_total_cdf,
        }

    def get_comedor_context(self, ciudadano):
        try:
            from comedores.models import ColaboradorEspacio, Nomina
        except ImportError:
            return {"nominas_comedor": [], "colaboraciones_comedor": []}

        try:
            nominas = list(
                Nomina.objects.filter(ciudadano=ciudadano)
                .select_related(
                    "admision__comedor__provincia",
                    "admision__comedor__municipio",
                    "admision__comedor__tipocomedor",
                )
                .order_by("-fecha")
            )
            colaboraciones = list(
                ColaboradorEspacio.objects.filter(ciudadano=ciudadano)
                .select_related(
                    "comedor__provincia",
                    "comedor__municipio",
                    "comedor__tipocomedor",
                )
                .prefetch_related("actividades")
                .order_by("-fecha_alta", "-id")
            )
        except Exception:
            logger.exception(
                "Error cargando nominas de comedor para ciudadano %s", ciudadano.pk
            )
            return {"nominas_comedor": [], "colaboraciones_comedor": []}
        contexto = {
            "nominas_comedor": nominas,
            "colaboraciones_comedor": colaboraciones,
        }
        nomina_actual = nominas[0] if nominas else None
        if nomina_actual:
            contexto["nomina_actual"] = nomina_actual
        return contexto

    def get_vat_context(self, ciudadano):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        try:
            from VAT.models import (
                AsistenciaSesion,
                Inscripcion,
                InscripcionOferta,
                Voucher,
            )
        except ImportError:
            return {
                "vat_inscripciones": [],
                "vat_vouchers": [],
                "vat_inscripciones_oferta": [],
                "vat_programas": [],
            }

        try:
            inscripciones = list(
                Inscripcion.objects.filter(ciudadano=ciudadano)
                .select_related(
                    "comision__oferta__centro",
                    "comision__oferta__plan_curricular__titulo_referencia",
                    "programa",
                )
                .order_by("-fecha_inscripcion")
            )
            vouchers = list(
                Voucher.objects.filter(ciudadano=ciudadano)
                .select_related("programa")
                .order_by("-fecha_asignacion")
            )
            inscripciones_oferta = list(
                InscripcionOferta.objects.filter(ciudadano=ciudadano)
                .select_related(
                    "oferta__oferta__centro",
                    "oferta__oferta__plan_curricular__titulo_referencia",
                )
                .order_by("-fecha_inscripcion")
            )
            asistencias = list(
                AsistenciaSesion.objects.filter(inscripcion__ciudadano=ciudadano)
                .select_related("inscripcion")
                .order_by("-fecha_registro")
            )
        except Exception:
            logger.exception("Error cargando datos VAT para ciudadano %s", ciudadano.pk)
            return {
                "vat_inscripciones": [],
                "vat_vouchers": [],
                "vat_inscripciones_oferta": [],
                "vat_programas": [],
            }

        creditos_totales = sum(v.cantidad_inicial for v in vouchers)
        creditos_disponibles = sum(
            v.cantidad_disponible for v in vouchers if v.estado == "activo"
        )
        voucher_activo = next((v for v in vouchers if v.estado == "activo"), None)
        asistencias_por_inscripcion = defaultdict(
            lambda: {"presentes": 0, "registradas": 0}
        )

        for asistencia in asistencias:
            resumen = asistencias_por_inscripcion[asistencia.inscripcion_id]
            resumen["registradas"] += 1
            if asistencia.presente:
                resumen["presentes"] += 1

        for inscripcion in inscripciones:
            resumen = asistencias_por_inscripcion.get(
                inscripcion.id, {"presentes": 0, "registradas": 0}
            )
            registradas = resumen["registradas"]
            inscripcion.asistencias_presentes = resumen["presentes"]
            inscripcion.asistencias_registradas = registradas
            inscripcion.asistencia_porcentaje = (
                round((resumen["presentes"] / registradas) * 100) if registradas else 0
            )

        programas = {}

        def ensure_programa(programa):
            if not programa:
                return None
            programa_id = programa.id
            if programa_id not in programas:
                programas[programa_id] = {
                    "programa": programa,
                    "vouchers": [],
                    "voucher_activo": None,
                    "voucher_referencia": None,
                    "inscripciones": [],
                    "inscripciones_oferta": [],
                    "creditos_totales": 0,
                    "creditos_actuales": 0,
                    "cursos_asignados": 0,
                    "asistencias_presentes": 0,
                    "asistencias_registradas": 0,
                }
            return programas[programa_id]

        for voucher in vouchers:
            programa_ctx = ensure_programa(voucher.programa)
            if not programa_ctx:
                continue
            programa_ctx["vouchers"].append(voucher)
            programa_ctx["creditos_totales"] += voucher.cantidad_inicial
            if voucher.estado == "activo":
                programa_ctx["creditos_actuales"] += voucher.cantidad_disponible
                if programa_ctx["voucher_activo"] is None:
                    programa_ctx["voucher_activo"] = voucher
            if programa_ctx["voucher_referencia"] is None:
                programa_ctx["voucher_referencia"] = voucher

        for inscripcion in inscripciones:
            programa_ctx = ensure_programa(inscripcion.programa)
            if not programa_ctx:
                continue
            programa_ctx["inscripciones"].append(inscripcion)
            programa_ctx["cursos_asignados"] += 1
            programa_ctx["asistencias_presentes"] += inscripcion.asistencias_presentes
            programa_ctx[
                "asistencias_registradas"
            ] += inscripcion.asistencias_registradas

        for inscripcion_oferta in inscripciones_oferta:
            programa = getattr(
                getattr(inscripcion_oferta.oferta, "oferta", None), "programa", None
            )
            programa_ctx = ensure_programa(programa)
            if not programa_ctx:
                continue
            programa_ctx["inscripciones_oferta"].append(inscripcion_oferta)
            programa_ctx["cursos_asignados"] += 1

        vat_programas = sorted(
            programas.values(),
            key=lambda item: str(item["programa"]).lower(),
        )

        return {
            "vat_inscripciones": inscripciones,
            "vat_vouchers": vouchers,
            "vat_inscripciones_oferta": inscripciones_oferta,
            "vat_creditos_totales": creditos_totales,
            "vat_creditos_disponibles": creditos_disponibles,
            "vat_voucher_activo": voucher_activo,
            "vat_programas": vat_programas,
        }


class CiudadanosCreateView(LoginRequiredMixin, CreateView):
    model = Ciudadano
    form_class = CiudadanoForm
    template_name = "ciudadanos/ciudadano_form.html"
    SEXO_BUSQUEDA_CHOICES = (
        ("M", "Masculino"),
        ("F", "Femenino"),
        ("X", "X"),
        ("D", "Desconocido"),
    )

    def get(self, request, *args, **kwargs):
        dni = (request.GET.get("dni") or "").strip()
        if dni:
            return self._handle_ciudadano_busqueda(request, dni, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def _handle_ciudadano_busqueda(self, request, dni, *args, **kwargs):
        dni_clean = str(dni or "").strip()
        if not dni_clean.isdigit() or len(dni_clean) < 7:
            messages.warning(request, "Ingrese un DNI numérico válido para buscar.")
            return super().get(request, *args, **kwargs)

        ciudadano = Ciudadano.objects.filter(
            tipo_documento=Ciudadano.DOCUMENTO_DNI, documento=int(dni_clean)
        ).first()
        if ciudadano:
            messages.info(request, "El ciudadano ya existe. Puede editar su legajo.")
            return redirect("ciudadanos_editar", pk=ciudadano.pk)

        sexo = (request.GET.get("sexo") or "M").upper()
        if sexo not in {"M", "F", "X"}:
            sexo = None

        resultado = ComedorService.obtener_datos_ciudadano_desde_renaper(
            dni_clean, sexo=sexo
        )
        if not resultado.get("success"):
            messages.warning(
                request,
                resultado.get("message", "No se encontraron datos en RENAPER."),
            )
            return super().get(request, *args, **kwargs)

        prefill = dict(resultado.get("data") or {})
        fecha_nacimiento = prefill.get("fecha_nacimiento")
        if hasattr(fecha_nacimiento, "isoformat"):
            prefill["fecha_nacimiento"] = fecha_nacimiento.isoformat()
        request.session["ciudadano_prefill"] = prefill
        request.session.modified = True

        messages.success(
            request,
            "Datos cargados desde RENAPER. Complete el formulario del ciudadano.",
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sexo_selected = (self.request.GET.get("sexo") or "M").upper()
        allowed_sexo = {choice[0] for choice in self.SEXO_BUSQUEDA_CHOICES}
        if sexo_selected not in allowed_sexo:
            sexo_selected = "M"
        ctx["sexo_busqueda_choices"] = self.SEXO_BUSQUEDA_CHOICES
        ctx["sexo_busqueda"] = sexo_selected
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        prefill = self.request.session.pop("ciudadano_prefill", None)
        if prefill:
            initial.update(prefill)
            self._prefill_ciudadano = prefill
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        prefill = getattr(self, "_prefill_ciudadano", None)
        if prefill:
            provincia_id = self._safe_int(prefill.get("provincia"))
            municipio_id = self._safe_int(prefill.get("municipio"))
            localidad_id = self._safe_int(prefill.get("localidad"))

            if localidad_id:
                localidad_obj = (
                    Localidad.objects.select_related("municipio__provincia")
                    .filter(pk=localidad_id)
                    .first()
                )
                if localidad_obj:
                    municipio_id = municipio_id or localidad_obj.municipio_id
                    if localidad_obj.municipio and not provincia_id:
                        provincia_id = localidad_obj.municipio.provincia_id

            if municipio_id and not provincia_id:
                municipio_obj = (
                    Municipio.objects.select_related("provincia")
                    .filter(pk=municipio_id)
                    .first()
                )
                if municipio_obj and not provincia_id:
                    provincia_id = municipio_obj.provincia_id

            if provincia_id:
                form.fields["provincia"].initial = provincia_id
                form.fields["municipio"].queryset = Municipio.objects.filter(
                    provincia_id=provincia_id
                ).order_by("nombre")
            elif municipio_id:
                form.fields["municipio"].queryset = Municipio.objects.filter(
                    pk=municipio_id
                )

            if municipio_id:
                form.fields["municipio"].initial = municipio_id
                form.fields["localidad"].queryset = Localidad.objects.filter(
                    municipio_id=municipio_id
                ).order_by("nombre")

            if localidad_id:
                form.fields["localidad"].initial = localidad_id

        return form

    @staticmethod
    def _safe_int(value):
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def form_valid(self, form):
        ciudadano = form.save(commit=False)
        ciudadano.creado_por = self.request.user
        ciudadano.modificado_por = self.request.user
        ciudadano.save()
        form.save_m2m()
        messages.success(self.request, "Ciudadano creado correctamente.")
        return redirect(ciudadano.get_absolute_url())


class CiudadanosUpdateView(LoginRequiredMixin, UpdateView):
    model = Ciudadano
    form_class = CiudadanoForm
    template_name = "ciudadanos/ciudadano_form.html"

    def form_valid(self, form):
        ciudadano = form.save(commit=False)
        ciudadano.modificado_por = self.request.user
        ciudadano.save()
        form.save_m2m()
        messages.success(self.request, "Ciudadano actualizado.")
        return redirect(ciudadano.get_absolute_url())


class CiudadanosDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Ciudadano
    template_name = "ciudadanos/ciudadano_confirm_delete.html"
    success_url = reverse_lazy("ciudadanos")
    success_message = "Ciudadano dado de baja correctamente."


class GrupoFamiliarCreateView(LoginRequiredMixin, FormView):
    form_class = GrupoFamiliarForm
    template_name = "ciudadanos/grupofamiliar_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.ciudadano = get_object_or_404(Ciudadano, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["ciudadano"] = self.ciudadano
        if self.request.POST:
            data = self.request.POST.copy()
            data["ciudadano_2"] = data.get("ciudadano_2_id", "")
            kwargs["data"] = data
        return kwargs

    def form_valid(self, form):
        relacion = form.save()
        messages.success(self.request, "Familiar agregado correctamente.")
        return redirect(relacion.ciudadano_1.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ciudadano"] = self.ciudadano
        return ctx


class GrupoFamiliarDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = GrupoFamiliar
    template_name = "ciudadanos/grupofamiliar_confirm_delete.html"
    success_message = None

    def get_success_url(self):
        messages.success(self.request, "Relación familiar eliminada.")
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        response = safe_redirect(
            self.request,
            default=self.object.ciudadano_1.get_absolute_url(),
            target=next_url,
        )
        return response.url
