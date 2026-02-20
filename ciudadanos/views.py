import logging

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
from core.soft_delete_views import SoftDeleteDeleteViewMixin

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
            from comedores.models import Nomina
        except ImportError:
            return {"nominas_comedor": []}

        try:
            nominas = (
                Nomina.objects.filter(ciudadano=ciudadano)
                .select_related(
                    "comedor__provincia", "comedor__municipio", "comedor__tipocomedor"
                )
                .order_by("-fecha")
            )
        except Exception:
            logger.exception(
                "Error cargando nominas de comedor para ciudadano %s", ciudadano.pk
            )
            return {"nominas_comedor": []}
        contexto = {"nominas_comedor": nominas}
        nomina_actual = nominas.first()
        if nomina_actual:
            contexto["nomina_actual"] = nomina_actual
        return contexto


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
