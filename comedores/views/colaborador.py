from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, View

from ciudadanos.models import Ciudadano
from comedores.forms.comedor_form import ColaboradorEspacioForm
from comedores.models import ColaboradorEspacio
from comedores.services.colaborador_espacio_service import ColaboradorEspacioService
from comedores.services.comedor_service import ComedorService


class ColaboradorEspacioCreateView(LoginRequiredMixin, CreateView):
    model = ColaboradorEspacio
    form_class = ColaboradorEspacioForm
    template_name = "comedor/colaborador_form.html"

    def get_success_url(self):
        return reverse_lazy("comedor_detalle", kwargs={"pk": self.kwargs["pk"]})

    def _get_comedor(self):
        return ComedorService.get_scoped_comedor_or_404(
            self.kwargs["pk"], self.request.user
        )

    def _build_busqueda_context(self):
        source = (
            self.request.POST if self.request.method == "POST" else self.request.GET
        )
        query = (source.get("query") or source.get("dni") or "").strip()
        ciudadano_id = (source.get("ciudadano_id") or "").strip()
        context = {
            "query": query,
            "ciudadano_encontrado": None,
            "preview_data": None,
            "renaper_encontrado": False,
            "colaborador_existente": None,
        }
        if ciudadano_id:
            ciudadano = (
                Ciudadano.objects.select_related("sexo").filter(pk=ciudadano_id).first()
            )
            if ciudadano:
                context["ciudadano_encontrado"] = ciudadano
                context["preview_data"] = (
                    ColaboradorEspacioService.build_preview_from_ciudadano(ciudadano)
                )
                context["colaborador_existente"] = ColaboradorEspacio.objects.filter(
                    comedor=self._get_comedor(),
                    ciudadano=ciudadano,
                ).first()
            return context

        if not query:
            return context

        if not query.isdigit() or len(query) < 7:
            messages.warning(
                self.request,
                "Ingrese un DNI numérico válido para realizar la búsqueda.",
            )
            return context

        ciudadano = (
            Ciudadano.objects.select_related("sexo")
            .filter(
                tipo_documento=Ciudadano.DOCUMENTO_DNI,
                documento=int(query),
            )
            .first()
        )
        if ciudadano:
            context["ciudadano_encontrado"] = ciudadano
            context["preview_data"] = (
                ColaboradorEspacioService.build_preview_from_ciudadano(ciudadano)
            )
            context["colaborador_existente"] = ColaboradorEspacio.objects.filter(
                comedor=self._get_comedor(),
                ciudadano=ciudadano,
            ).first()
            return context

        renaper_result = ComedorService.obtener_datos_ciudadano_desde_renaper(query)
        if renaper_result.get("success"):
            context["renaper_encontrado"] = True
            context["preview_data"] = (
                ColaboradorEspacioService.build_preview_from_renaper_data(
                    renaper_result.get("data") or {}
                )
            )
            mensaje = renaper_result.get("message")
            if mensaje:
                messages.info(self.request, mensaje)
            return context

        if renaper_result.get("message"):
            messages.warning(self.request, renaper_result["message"])
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self._get_comedor()
        form = kwargs.get("form") or self.get_form()
        busqueda_context = self._build_busqueda_context()
        context.update(
            {
                "object": comedor,
                "form": form,
                **busqueda_context,
            }
        )
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial.setdefault("fecha_alta", timezone.now().date())
        return initial

    def post(self, request, *args, **kwargs):
        self.object = None
        comedor = self._get_comedor()
        form = self.get_form()
        ciudadano_id = request.POST.get("ciudadano_id") or None
        dni = (request.POST.get("dni") or "").strip()

        if not ciudadano_id and not dni:
            messages.warning(
                request,
                "Debe buscar un ciudadano o consultar RENAPER antes de guardar el colaborador.",
            )
            return self.render_to_response(self.get_context_data(form=form))

        if form.is_valid():
            result = ColaboradorEspacioService.create_for_comedor(
                comedor=comedor,
                actor=request.user,
                cleaned_data=dict(form.cleaned_data),
                ciudadano_id=ciudadano_id,
                dni=dni,
            )
            if result.get("success"):
                messages.success(request, result["message"])
                return redirect(self.get_success_url())
            messages.warning(request, result["message"])
        else:
            messages.warning(request, "Errores en el formulario del colaborador.")

        return self.render_to_response(self.get_context_data(form=form))


class ColaboradorEspacioUpdateView(LoginRequiredMixin, UpdateView):
    model = ColaboradorEspacio
    form_class = ColaboradorEspacioForm
    template_name = "comedor/colaborador_form.html"
    pk_url_kwarg = "pk2"

    def _get_comedor(self):
        return ComedorService.get_scoped_comedor_or_404(
            self.kwargs["pk"], self.request.user
        )

    def get_queryset(self):
        return (
            ColaboradorEspacio.objects.filter(comedor=self._get_comedor())
            .select_related("ciudadano__sexo")
            .prefetch_related("actividades")
        )

    def get_success_url(self):
        return reverse_lazy("comedor_detalle", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self._get_comedor()
        context.update(
            {
                "object": comedor,
                "colaborador": self.object,
                "edit_mode": True,
                "preview_data": ColaboradorEspacioService.build_preview_from_ciudadano(
                    self.object.ciudadano
                ),
            }
        )
        return context

    def form_valid(self, form):
        result = ColaboradorEspacioService.update_for_comedor(
            colaborador=self.object,
            actor=self.request.user,
            cleaned_data=dict(form.cleaned_data),
        )
        if result.get("success"):
            messages.success(self.request, result["message"])
            return redirect(self.get_success_url())
        messages.warning(self.request, result["message"])
        return self.render_to_response(self.get_context_data(form=form))


class ColaboradorEspacioDeleteView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk, pk2):
        comedor = ComedorService.get_scoped_comedor_or_404(pk, request.user)
        colaborador = (
            ColaboradorEspacio.objects.filter(pk=pk2, comedor=comedor)
            .select_related("ciudadano")
            .first()
        )
        if not colaborador:
            raise Http404("Colaborador no encontrado.")

        result = ColaboradorEspacioService.soft_delete(
            colaborador=colaborador,
            actor=request.user,
        )
        if result.get("success"):
            messages.success(request, result["message"])
        else:
            messages.warning(request, result["message"])
        return redirect("comedor_detalle", pk=pk)
