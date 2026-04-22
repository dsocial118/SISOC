from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, View

from admisiones.models.admisiones import Admision
from comedores.forms.comedor_form import (
    CiudadanoFormParaNomina,
    NominaExtraForm,
    NominaForm,
)
from comedores.models import Nomina
from comedores.services.comedor_service import ComedorService
from comedores.utils import comedor_usa_admision_para_nomina
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin


def _get_nomina_scoped_or_404(pk, user):
    """Obtiene una Nomina scoped al usuario, soportando tanto prog 2 (admision) como 3/4 (comedor)."""
    scoped_comedores = ComedorService.get_scoped_comedor_queryset(user)
    return get_object_or_404(
        Nomina.objects.select_related("admision__comedor", "comedor").filter(
            Q(admision__comedor__in=scoped_comedores)
            | Q(comedor__in=scoped_comedores, admision__isnull=True)
        ),
        pk=pk,
    )


def _get_comedor_scoped_or_404(comedor_pk, user):
    return ComedorService.get_scoped_comedor_or_404(comedor_pk, user)


def _get_comedor_directo_or_404(comedor_pk, user):
    """Obtiene un comedor habilitado para nómina directa."""
    comedor = _get_comedor_scoped_or_404(comedor_pk, user)
    if comedor_usa_admision_para_nomina(comedor):
        raise Http404("La nómina directa solo aplica a comedores con nómina directa.")
    return comedor


def _get_admision_del_comedor_or_404(comedor_pk, admision_pk, user):
    """Obtiene la admisión sólo si pertenece al comedor de la URL."""
    comedor = _get_comedor_scoped_or_404(comedor_pk, user)
    return get_object_or_404(Admision, pk=admision_pk, comedor_id=comedor.id)


def _get_cantidad_asistentes_activos(rangos):
    return (rangos or {}).get("cantidad_activos") or 0


@login_required
def nomina_editar_ajax(request, pk):
    nomina = _get_nomina_scoped_or_404(pk, request.user)
    if request.method == "POST":
        form = NominaForm(request.POST, instance=nomina)
        if form.is_valid():
            form.save()
            return JsonResponse(
                {"success": True, "message": "Datos modificados con éxito."}
            )
        else:

            return JsonResponse({"success": False, "errors": form.errors})
    else:  # GET
        form = NominaForm(instance=nomina)
        return render(request, "comedor/nomina_editar_ajax.html", {"form": form})


class NominaDetailView(LoginRequiredMixin, TemplateView):
    template_name = "comedor/nomina_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision = _get_admision_del_comedor_or_404(
            self.kwargs["pk"],
            self.kwargs["admision_pk"],
            self.request.user,
        )
        page = int(self.request.GET.get("page", 1))
        dni_query = (self.request.GET.get("dni") or "").strip()

        page_obj, nomina_m, nomina_f, nomina_x, espera, _total, rangos = (
            ComedorService.get_nomina_detail(admision.pk, page, dni_query=dni_query)
        )

        menores = (rangos.get("ninos") or 0) + (rangos.get("adolescentes") or 0)

        context.update(
            {
                "nomina": page_obj,
                "nominaM": nomina_m,
                "nominaF": nomina_f,
                "nominaX": nomina_x,
                "espera": espera,
                "cantidad_nomina": _get_cantidad_asistentes_activos(rangos),
                "menores": menores,
                "nomina_rangos": rangos,
                "object": admision.comedor,
                "admision_pk": admision.pk,
                "dni_query": dni_query,
                "estados": Nomina.ESTADO_CHOICES,
            }
        )
        return context


class NominaCreateView(LoginRequiredMixin, CreateView):
    model = Nomina
    form_class = NominaForm
    template_name = "comedor/nomina_form.html"

    def get_success_url(self):
        return reverse_lazy(
            "nomina_ver",
            kwargs={"pk": self.kwargs["pk"], "admision_pk": self.kwargs["admision_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision = _get_admision_del_comedor_or_404(
            self.kwargs["pk"],
            self.kwargs["admision_pk"],
            self.request.user,
        )
        context["object"] = admision.comedor
        context["admision_pk"] = admision.pk

        query = self.request.GET.get("query", "")
        query_clean = query.strip()
        form_ciudadano = kwargs.get("form_ciudadano")
        ciudadanos = []
        renaper_data = None
        if query:
            ciudadanos = ComedorService.buscar_ciudadanos_por_documento(query)
            if (
                not ciudadanos
                and query_clean.isdigit()
                and len(query_clean) >= 7
                and not form_ciudadano
            ):
                renaper_result = ComedorService.obtener_datos_ciudadano_desde_renaper(
                    query_clean
                )
                if renaper_result.get("success"):
                    renaper_data = self._prepare_renaper_initial_data(renaper_result)
                    mensaje = renaper_result.get("message")
                    if mensaje:
                        messages.info(self.request, mensaje)
                elif renaper_result.get("message"):
                    messages.warning(self.request, renaper_result["message"])

        if not form_ciudadano:
            if renaper_data:
                form_ciudadano = CiudadanoFormParaNomina(initial=renaper_data)
            else:
                form_ciudadano = CiudadanoFormParaNomina()

        renaper_precarga = bool(renaper_data) or (
            self.request.POST.get("origen_dato") == "renaper"
        )

        context.update(
            {
                "ciudadanos": ciudadanos,
                "no_resultados": bool(query) and not ciudadanos,
                "form_ciudadano": form_ciudadano,
                "form_nomina_extra": kwargs.get("form_nomina_extra")
                or NominaExtraForm(),
                "estados": Nomina.ESTADO_CHOICES,
                "renaper_precarga": renaper_precarga,
            }
        )
        return context

    @staticmethod
    def _prepare_renaper_initial_data(renaper_result):
        renaper_data = dict(renaper_result.get("data") or {})
        if not renaper_data:
            return renaper_data

        fecha_raw = renaper_data.get("fecha_nacimiento")
        if not fecha_raw:
            datos_api = renaper_result.get("datos_api") or {}
            fecha_raw = datos_api.get("fechaNacimiento")

        if fecha_raw:
            parsed_fecha = ComedorService._parse_fecha_renaper(fecha_raw)
            if parsed_fecha:
                renaper_data["fecha_nacimiento"] = parsed_fecha.isoformat()

        return renaper_data

    def post(self, request, *args, **kwargs):
        # Asegura que self.object exista para el contexto de CreateView
        self.object = None
        admision = _get_admision_del_comedor_or_404(
            self.kwargs["pk"],
            self.kwargs["admision_pk"],
            request.user,
        )
        admision_id = admision.pk
        ciudadano_id = request.POST.get("ciudadano_id")

        if ciudadano_id:
            # Agregar ciudadano existente
            form_nomina_extra = NominaExtraForm(request.POST)

            if not form_nomina_extra.is_valid():
                messages.error(
                    request,
                    "Datos inválidos para agregar ciudadano a la nómina.",
                )
                context = self.get_context_data(
                    form_nomina_extra=form_nomina_extra,
                )
                return self.render_to_response(context)

            estado = form_nomina_extra.cleaned_data.get("estado")
            observaciones = form_nomina_extra.cleaned_data.get("observaciones", "")

            ok, msg = ComedorService.agregar_ciudadano_a_nomina(
                admision_id=admision_id,
                ciudadano_id=ciudadano_id,
                user=request.user,
                estado=estado,
                observaciones=observaciones,
            )

            if ok:
                messages.success(request, msg)
            else:
                messages.warning(request, msg)

            return redirect(self.get_success_url())
        else:
            # Crear ciudadano nuevo
            form_ciudadano = CiudadanoFormParaNomina(request.POST)
            form_nomina_extra = NominaExtraForm(request.POST)

            if form_ciudadano.is_valid() and form_nomina_extra.is_valid():
                estado = form_nomina_extra.cleaned_data.get("estado")
                observaciones = form_nomina_extra.cleaned_data.get("observaciones")
                ciudadano_data = dict(form_ciudadano.cleaned_data)
                if request.POST.get("origen_dato") == "renaper":
                    ciudadano_data["origen_dato"] = "renaper"

                ok, msg = ComedorService.crear_ciudadano_y_agregar_a_nomina(
                    ciudadano_data=ciudadano_data,
                    admision_id=admision_id,
                    user=request.user,
                    estado=estado,
                    observaciones=observaciones,
                )

                if ok:
                    messages.success(request, msg)
                    return redirect(self.get_success_url())
                else:
                    messages.warning(request, msg)
            else:
                messages.warning(request, "Errores en el formulario de ciudadano.")

            context = self.get_context_data(
                form_ciudadano=form_ciudadano,
                form_nomina_extra=form_nomina_extra,
            )
            return self.render_to_response(context)


class NominaDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Nomina
    template_name = "comedor/nomina_confirm_delete.html"
    pk_url_kwarg = "pk2"
    success_message = "Registro de nómina dado de baja correctamente."

    def get_queryset(self):
        scoped_comedores = ComedorService.get_scoped_comedor_queryset(self.request.user)
        return (
            super()
            .get_queryset()
            .filter(
                admision_id=self.kwargs["admision_pk"],
                admision__comedor_id=self.kwargs["pk"],
                admision__comedor__in=scoped_comedores,
            )
        )

    def get_success_url(self):
        return reverse_lazy(
            "nomina_ver",
            kwargs={"pk": self.kwargs["pk"], "admision_pk": self.kwargs["admision_pk"]},
        )


@login_required
def nomina_cambiar_estado(request, pk):
    """Cambia sólo el estado de un registro de nómina vía AJAX (POST)."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Método no permitido."}, status=405
        )

    nomina = _get_nomina_scoped_or_404(pk, request.user)

    nuevo_estado = request.POST.get("estado", "").strip()
    estados_validos = {v for v, _ in Nomina.ESTADO_CHOICES}
    if nuevo_estado not in estados_validos:
        return JsonResponse({"success": False, "error": "Estado inválido."}, status=400)

    nomina.estado = nuevo_estado
    nomina.save(update_fields=["estado"])
    return JsonResponse({"success": True, "estado": nuevo_estado})


class NominaImportarView(LoginRequiredMixin, View):
    """
    Importa la nómina del convenio anterior al convenio actual.
    Redirige a la vista de nómina con mensaje de resultado.
    """

    http_method_names = ["post"]

    def post(self, request, pk, admision_pk):
        _get_admision_del_comedor_or_404(pk, admision_pk, request.user)
        ok, msg, _ = ComedorService.importar_nomina_ultimo_convenio(
            admision_id=admision_pk,
            comedor_id=pk,
        )
        if ok:
            messages.success(request, msg)
        else:
            messages.warning(request, msg)

        return redirect(
            reverse_lazy("nomina_ver", kwargs={"pk": pk, "admision_pk": admision_pk})
        )


# ---------------------------------------------------------------------------
# Vistas de nómina directa (programas 3/4 — sin admisión)
# ---------------------------------------------------------------------------


class NominaDirectaDetailView(LoginRequiredMixin, TemplateView):
    """Nómina de un comedor 3/4: sin admision_pk en la URL."""

    template_name = "comedor/nomina_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = _get_comedor_directo_or_404(self.kwargs["pk"], self.request.user)
        page = int(self.request.GET.get("page", 1))
        dni_query = (self.request.GET.get("dni") or "").strip()

        page_obj, nomina_m, nomina_f, nomina_x, espera, _total, rangos = (
            ComedorService.get_nomina_detail_by_comedor(
                comedor.pk, page, dni_query=dni_query
            )
        )

        menores = (rangos.get("ninos") or 0) + (rangos.get("adolescentes") or 0)

        context.update(
            {
                "nomina": page_obj,
                "nominaM": nomina_m,
                "nominaF": nomina_f,
                "nominaX": nomina_x,
                "espera": espera,
                "cantidad_nomina": _get_cantidad_asistentes_activos(rangos),
                "menores": menores,
                "nomina_rangos": rangos,
                "object": comedor,
                "admision_pk": None,
                "dni_query": dni_query,
                "estados": Nomina.ESTADO_CHOICES,
            }
        )
        return context


class NominaDirectaCreateView(LoginRequiredMixin, CreateView):
    """Agrega ciudadanos a la nómina de un comedor 3/4 (sin admision)."""

    model = Nomina
    form_class = NominaForm
    template_name = "comedor/nomina_form.html"

    def get_success_url(self):
        return reverse_lazy("nomina_directa_ver", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = _get_comedor_directo_or_404(self.kwargs["pk"], self.request.user)
        context["object"] = comedor
        context["admision_pk"] = None

        query = self.request.GET.get("query", "")
        query_clean = query.strip()
        form_ciudadano = kwargs.get("form_ciudadano")
        ciudadanos = []
        renaper_data = None
        if query:
            ciudadanos = ComedorService.buscar_ciudadanos_por_documento(query)
            if (
                not ciudadanos
                and query_clean.isdigit()
                and len(query_clean) >= 7
                and not form_ciudadano
            ):
                renaper_result = ComedorService.obtener_datos_ciudadano_desde_renaper(
                    query_clean
                )
                if renaper_result.get("success"):
                    renaper_data = NominaCreateView._prepare_renaper_initial_data(
                        renaper_result
                    )
                    mensaje = renaper_result.get("message")
                    if mensaje:
                        messages.info(self.request, mensaje)
                elif renaper_result.get("message"):
                    messages.warning(self.request, renaper_result["message"])

        if not form_ciudadano:
            form_ciudadano = (
                CiudadanoFormParaNomina(initial=renaper_data)
                if renaper_data
                else CiudadanoFormParaNomina()
            )

        renaper_precarga = bool(renaper_data) or (
            self.request.POST.get("origen_dato") == "renaper"
        )

        context.update(
            {
                "ciudadanos": ciudadanos,
                "no_resultados": bool(query) and not ciudadanos,
                "form_ciudadano": form_ciudadano,
                "form_nomina_extra": kwargs.get("form_nomina_extra")
                or NominaExtraForm(),
                "estados": Nomina.ESTADO_CHOICES,
                "renaper_precarga": renaper_precarga,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        comedor = _get_comedor_directo_or_404(self.kwargs["pk"], request.user)
        comedor_id = comedor.pk
        ciudadano_id = request.POST.get("ciudadano_id")

        if ciudadano_id:
            form_nomina_extra = NominaExtraForm(request.POST)
            if not form_nomina_extra.is_valid():
                messages.error(
                    request, "Datos inválidos para agregar ciudadano a la nómina."
                )
                context = self.get_context_data(form_nomina_extra=form_nomina_extra)
                return self.render_to_response(context)

            estado = form_nomina_extra.cleaned_data.get("estado")
            observaciones = form_nomina_extra.cleaned_data.get("observaciones", "")

            ok, msg = ComedorService.agregar_ciudadano_a_nomina(
                ciudadano_id=ciudadano_id,
                user=request.user,
                estado=estado,
                observaciones=observaciones,
                comedor_id=comedor_id,
            )
            if ok:
                messages.success(request, msg)
            else:
                messages.warning(request, msg)
            return redirect(self.get_success_url())
        else:
            form_ciudadano = CiudadanoFormParaNomina(request.POST)
            form_nomina_extra = NominaExtraForm(request.POST)

            if form_ciudadano.is_valid() and form_nomina_extra.is_valid():
                estado = form_nomina_extra.cleaned_data.get("estado")
                observaciones = form_nomina_extra.cleaned_data.get("observaciones")
                ciudadano_data = dict(form_ciudadano.cleaned_data)
                if request.POST.get("origen_dato") == "renaper":
                    ciudadano_data["origen_dato"] = "renaper"

                ok, msg = ComedorService.crear_ciudadano_y_agregar_a_nomina(
                    ciudadano_data=ciudadano_data,
                    user=request.user,
                    estado=estado,
                    observaciones=observaciones,
                    comedor_id=comedor_id,
                )
                if ok:
                    messages.success(request, msg)
                    return redirect(self.get_success_url())
                else:
                    messages.warning(request, msg)
            else:
                messages.warning(request, "Errores en el formulario de ciudadano.")

            context = self.get_context_data(
                form_ciudadano=form_ciudadano,
                form_nomina_extra=form_nomina_extra,
            )
            return self.render_to_response(context)


class NominaDirectaDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    """Baja de un registro de nómina directa (prog 3/4)."""

    model = Nomina
    template_name = "comedor/nomina_confirm_delete.html"
    pk_url_kwarg = "pk2"
    success_message = "Registro de nómina dado de baja correctamente."

    def get_queryset(self):
        scoped_comedores = ComedorService.get_scoped_comedor_queryset(self.request.user)
        comedor = _get_comedor_directo_or_404(self.kwargs["pk"], self.request.user)
        return (
            super()
            .get_queryset()
            .filter(
                comedor_id=comedor.pk,
                comedor__in=scoped_comedores,
                admision__isnull=True,
            )
        )

    def get_success_url(self):
        return reverse_lazy("nomina_directa_ver", kwargs={"pk": self.kwargs["pk"]})
