import csv
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.services.csv_export import build_csv_response

from .forms import EncuestaForm
from .models import Encuesta, OperadorCondicion, RondaEncuesta, TipoPregunta
from .services import (
    actualizar_encuesta,
    actualizar_segmentacion,
    agregar_destinatario,
    cerrar_ronda,
    crear_encuesta,
    get_encuestas_queryset,
    posponer_ronda,
    publicar,
    quitar_destinatario,
    registrar_respuesta,
    reemplazar_preguntas,
    serializar_preguntas,
)
from .services_resultados import (
    build_resultados_csv_rows,
    build_resultados_excel,
    build_resultados_filename,
    get_resultados_ronda,
)
from .validators import TIPOS_PREGUNTA_CON_OPCIONES

EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _mensaje_error(exc: ValidationError) -> str:
    if hasattr(exc, "messages"):
        return " ".join(exc.messages)
    return str(exc)


def _redirect_next(request, fallback_url_name="inicio"):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect(reverse(fallback_url_name))


class EncuestaListView(LoginRequiredMixin, ListView):
    model = Encuesta
    template_name = "encuestas/encuesta_list.html"
    context_object_name = "encuestas"
    paginate_by = 20

    def get_queryset(self):
        queryset = get_encuestas_queryset()
        busqueda = (self.request.GET.get("busqueda") or "").strip()
        if busqueda:
            queryset = queryset.filter(Q(titulo__icontains=busqueda))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["puede_gestionar"] = self.request.user.has_perm(
            "encuestas.add_encuesta"
        )
        context["puede_ver_resultados"] = self.request.user.has_perm(
            "encuestas.ver_resultados"
        )
        context["busqueda"] = (self.request.GET.get("busqueda") or "").strip()
        return context


class EncuestaFormMixin:
    """Combina EncuestaForm (campos generales) con el editor dinámico de
    preguntas, que viaja en el campo oculto ``preguntas_json`` (ver
    encuestas/validators.py: parse_preguntas_payload)."""

    model = Encuesta
    form_class = EncuestaForm
    template_name = "encuestas/encuesta_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            try:
                preguntas_data = json.loads(
                    self.request.POST.get("preguntas_json", "[]")
                )
            except (TypeError, ValueError):
                preguntas_data = []
        elif getattr(self, "object", None) is not None:
            preguntas_data = serializar_preguntas(self.object)
        else:
            preguntas_data = []
        # json_script serializa y escapa el objeto de forma segura para el
        # <script type="application/json">; no pasarle un string ya volcado.
        context["preguntas_json_inicial"] = preguntas_data
        context["tipos_pregunta"] = TipoPregunta.choices
        context["operadores_condicion"] = OperadorCondicion.choices
        context["tipos_pregunta_con_opciones"] = ",".join(TIPOS_PREGUNTA_CON_OPCIONES)
        return context

    def get_success_url(self):
        return reverse("encuestas_listar")

    def _guardar_encuesta_y_preguntas(self, form, guardar_encuesta):
        preguntas_raw = self.request.POST.get("preguntas_json", "[]")
        try:
            with transaction.atomic():
                encuesta = guardar_encuesta()
                reemplazar_preguntas(encuesta, preguntas_raw)
        except ValidationError as exc:
            form.add_error(None, _mensaje_error(exc))
            return None
        return encuesta


class EncuestaCreateView(LoginRequiredMixin, EncuestaFormMixin, CreateView):
    def form_valid(self, form):
        encuesta = self._guardar_encuesta_y_preguntas(
            form,
            lambda: crear_encuesta(usuario=self.request.user, **form.cleaned_data),
        )
        if encuesta is None:
            return self.form_invalid(form)
        self.object = encuesta
        messages.success(self.request, "Encuesta creada correctamente.")
        return HttpResponseRedirect(self.get_success_url())


class EncuestaUpdateView(LoginRequiredMixin, EncuestaFormMixin, UpdateView):
    def get_queryset(self):
        return get_encuestas_queryset()

    def form_valid(self, form):
        original = self.object
        encuesta = self._guardar_encuesta_y_preguntas(
            form,
            lambda: actualizar_encuesta(
                original, usuario=self.request.user, **form.cleaned_data
            ),
        )
        if encuesta is None:
            return self.form_invalid(form)
        self.object = encuesta
        messages.success(self.request, "Encuesta actualizada correctamente.")
        return HttpResponseRedirect(self.get_success_url())


class EncuestaPublicarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        encuesta = get_object_or_404(get_encuestas_queryset(), pk=pk)
        try:
            publicar(encuesta, usuario=request.user)
        except ValidationError as exc:
            messages.error(request, _mensaje_error(exc))
        else:
            messages.success(request, "Encuesta publicada correctamente.")
        return HttpResponseRedirect(reverse("encuestas_listar"))


class RondaCerrarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ronda = get_object_or_404(RondaEncuesta, pk=pk)
        try:
            cerrar_ronda(ronda, manual=True)
        except ValidationError as exc:
            messages.error(request, _mensaje_error(exc))
        else:
            messages.success(request, "Ronda cerrada correctamente.")
        return HttpResponseRedirect(reverse("encuestas_listar"))


class ResponderRondaView(LoginRequiredMixin, View):
    """Recibe el POST del modal de encuesta pendiente (ver
    templates/includes/base.html + encuestas/partials/responder_modal.html).
    No requiere permisos de encuestas: cualquier usuario logueado segmentado
    puede responder."""

    def post(self, request, pk):
        ronda = get_object_or_404(RondaEncuesta, pk=pk)
        try:
            registrar_respuesta(ronda, request.user, request.POST)
        except ValidationError as exc:
            messages.error(request, _mensaje_error(exc))
        else:
            messages.success(request, "¡Gracias por responder la encuesta!")
        return _redirect_next(request)


class PosponerRondaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ronda = get_object_or_404(RondaEncuesta, pk=pk)
        try:
            posponer_ronda(ronda, request.user)
        except ValidationError as exc:
            messages.error(request, _mensaje_error(exc))
        return _redirect_next(request)


class EncuestaResultadosView(LoginRequiredMixin, DetailView):
    model = Encuesta
    template_name = "encuestas/encuesta_resultados.html"
    context_object_name = "encuesta"

    def get_queryset(self):
        return get_encuestas_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        encuesta = self.object
        rondas = list(encuesta.rondas.order_by("-numero_ronda"))

        ronda_pk = self.request.GET.get("ronda")
        ronda_actual = None
        if ronda_pk:
            ronda_actual = next(
                (ronda for ronda in rondas if str(ronda.pk) == ronda_pk), None
            )
        elif rondas:
            ronda_actual = rondas[0]

        context["rondas"] = rondas
        context["ronda_actual"] = ronda_actual
        context["resultados"] = (
            get_resultados_ronda(ronda_actual) if ronda_actual else []
        )
        return context


class EncuestaResultadosExportarView(LoginRequiredMixin, View):
    def get(self, request, pk, ronda_pk):
        ronda = get_object_or_404(
            RondaEncuesta.objects.select_related("encuesta"),
            pk=ronda_pk,
            encuesta_id=pk,
        )
        formato = request.GET.get("formato", "csv")

        if formato == "xlsx":
            contenido = build_resultados_excel(ronda)
            response = HttpResponse(contenido, content_type=EXCEL_CONTENT_TYPE)
            filename = build_resultados_filename(ronda.encuesta, ronda, "xlsx")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        if formato != "csv":
            raise Http404("Formato de exportación no soportado.")

        headers, filas = build_resultados_csv_rows(ronda)
        filename = build_resultados_filename(ronda.encuesta, ronda, "csv")
        response = build_csv_response(filename)
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(filas)
        return response


class EncuestaSegmentacionView(LoginRequiredMixin, DetailView):
    """Gestión de destinatarios, separada del formulario de edición general
    a propósito: a diferencia de preguntas/config, la segmentación se puede
    modificar en caliente con una ronda ya abierta (regla de negocio 12), y
    EncuestaUpdateView bloquea justamente eso."""

    model = Encuesta
    template_name = "encuestas/encuesta_segmentacion.html"
    context_object_name = "encuesta"

    def get_queryset(self):
        return get_encuestas_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        segmentacion = getattr(self.object, "segmentacion", None)
        context["segmentacion"] = segmentacion
        context["destinatarios"] = (
            segmentacion.destinatarios.order_by("tipo_documento", "numero_documento")
            if segmentacion
            else []
        )
        return context


class SegmentacionTipoUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        encuesta = get_object_or_404(get_encuestas_queryset(), pk=pk)
        try:
            actualizar_segmentacion(
                encuesta,
                tipo=request.POST.get("tipo", ""),
                archivo=request.FILES.get("archivo_listado"),
            )
        except ValidationError as exc:
            messages.error(request, _mensaje_error(exc))
        else:
            messages.success(request, "Segmentación actualizada correctamente.")
        return HttpResponseRedirect(reverse("encuestas_segmentacion", args=[pk]))


class SegmentacionAgregarDestinatarioView(LoginRequiredMixin, View):
    def post(self, request, pk):
        encuesta = get_object_or_404(get_encuestas_queryset(), pk=pk)
        try:
            agregar_destinatario(
                encuesta,
                tipo_documento=request.POST.get("tipo_documento", ""),
                numero_documento=request.POST.get("numero_documento", ""),
            )
        except ValidationError as exc:
            messages.error(request, _mensaje_error(exc))
        else:
            messages.success(request, "Destinatario agregado correctamente.")
        return HttpResponseRedirect(reverse("encuestas_segmentacion", args=[pk]))


class SegmentacionQuitarDestinatarioView(LoginRequiredMixin, View):
    def post(self, request, pk, destinatario_pk):
        encuesta = get_object_or_404(get_encuestas_queryset(), pk=pk)
        try:
            quitar_destinatario(encuesta, destinatario_pk)
        except ValidationError as exc:
            messages.error(request, _mensaje_error(exc))
        else:
            messages.success(request, "Destinatario eliminado correctamente.")
        return HttpResponseRedirect(reverse("encuestas_segmentacion", args=[pk]))
