from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView

from comedores.forms.comedor_form import (
    CiudadanoFormParaNomina,
    NominaExtraForm,
    NominaForm,
)
from comedores.models import Nomina
from comedores.services.comedor_service import ComedorService
from core.soft_delete_views import SoftDeleteDeleteViewMixin


@login_required
def nomina_editar_ajax(request, pk):
    nomina = get_object_or_404(Nomina, pk=pk)
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
        comedor_pk = self.kwargs["pk"]
        page = int(self.request.GET.get("page", 1))

        page_obj, nomina_m, nomina_f, nomina_x, espera, total, rangos = (
            ComedorService.get_nomina_detail(comedor_pk, page)
        )

        menores = (rangos.get("ninos") or 0) + (rangos.get("adolescentes") or 0)

        comedor = ComedorService.get_comedor(comedor_pk)

        context.update(
            {
                "nomina": page_obj,
                "nominaM": nomina_m,
                "nominaF": nomina_f,
                "nominaX": nomina_x,
                "espera": espera,
                "cantidad_nomina": total,
                "menores": menores,
                "nomina_rangos": rangos,
                "object": comedor,
            }
        )
        return context


class NominaCreateView(LoginRequiredMixin, CreateView):
    model = Nomina
    form_class = NominaForm
    template_name = "comedor/nomina_form.html"

    def get_success_url(self):
        return reverse_lazy("nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = ComedorService.get_comedor(self.kwargs["pk"])

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
                comedor_id=self.kwargs["pk"],
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
                    comedor_id=self.kwargs["pk"],
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

    def get_success_url(self):
        return reverse_lazy("nomina_ver", kwargs={"pk": self.kwargs["pk"]})
