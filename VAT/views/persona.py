import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from ciudadanos.models import Ciudadano
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from VAT.forms import InscripcionForm, CiudadanoInscripcionRapidaForm
from VAT.models import Comision, Inscripcion
from VAT.services.inscripcion_service import InscripcionService

logger = logging.getLogger("django")


# ============================================================================
# INSCRIPCIÓN VIEWS
# ============================================================================


class InscripcionListView(LoginRequiredMixin, ListView):
    model = Inscripcion
    template_name = "vat/persona/inscripcion_list.html"
    context_object_name = "inscripciones"
    paginate_by = 20

    def get_queryset(self):
        queryset = Inscripcion.objects.select_related(
            "ciudadano", "comision", "programa"
        ).order_by("-fecha_inscripcion")

        ciudadano_id = self.request.GET.get("ciudadano_id")
        comision_id = self.request.GET.get("comision_id")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if buscar:
            queryset = queryset.filter(
                Q(ciudadano__apellido__icontains=buscar)
                | Q(ciudadano__nombre__icontains=buscar)
                | Q(comision__codigo_comision__icontains=buscar)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_choices"] = Inscripcion.ESTADO_INSCRIPCION_CHOICES
        return context


class InscripcionCreateView(LoginRequiredMixin, CreateView):
    model = Inscripcion
    form_class = InscripcionForm
    template_name = "vat/persona/inscripcion_form.html"
    success_url = reverse_lazy("vat_inscripcion_list")

    def get_initial(self):
        initial = super().get_initial()
        ciudadano_id = self.request.GET.get("ciudadano")
        comision_id = self.request.GET.get("comision")
        if ciudadano_id:
            initial["ciudadano"] = ciudadano_id
        if comision_id:
            initial["comision"] = comision_id
        return initial

    def form_valid(self, form):
        try:
            data = form.cleaned_data
            self.object = InscripcionService.crear_inscripcion(
                ciudadano=data["ciudadano"],
                comision=data["comision"],
                programa=data["programa"],
                estado=data["estado"],
                origen_canal=data["origen_canal"],
                observaciones=data.get("observaciones", ""),
                usuario=self.request.user,
            )
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)

        cantidad_debito = getattr(self.object, "_voucher_debito", 0)
        if cantidad_debito > 0:
            saldo = getattr(self.object, "_voucher_saldo", 0)
            messages.success(
                self.request,
                f"Inscripción creada. Se descontaron {cantidad_debito} créditos del voucher de {self.object.ciudadano} ({saldo} restantes).",
            )
        else:
            messages.success(self.request, "Inscripción creada exitosamente.")

        return HttpResponseRedirect(self.get_success_url())


class InscripcionRapidaComisionView(LoginRequiredMixin, View):
    """Alta rápida de inscripción desde el detalle de comisión vía AJAX."""

    def post(self, request, *args, **kwargs):
        comision = get_object_or_404(
            Comision.objects.select_related("oferta__programa"),
            pk=request.POST.get("comision"),
        )
        ciudadano_id = (request.POST.get("ciudadano_id") or "").strip()
        observaciones = (request.POST.get("observaciones") or "").strip()
        ciudadano_form = None

        if ciudadano_id:
            ciudadano = get_object_or_404(Ciudadano, pk=ciudadano_id)
        else:
            ciudadano_form = CiudadanoInscripcionRapidaForm(request.POST)
            if not ciudadano_form.is_valid():
                return JsonResponse(
                    {
                        "ok": False,
                        "message": "Errores en el formulario de ciudadano.",
                        "errors": ciudadano_form.errors,
                    },
                    status=400,
                )
            ciudadano = ciudadano_form.save(commit=False)
            ciudadano.creado_por = request.user
            ciudadano.modificado_por = request.user
            ciudadano.origen_dato = "manual"

        if ciudadano_id and Inscripcion.objects.filter(
            ciudadano=ciudadano, comision=comision
        ).exists():
            return JsonResponse(
                {
                    "ok": False,
                    "message": "El ciudadano ya está inscripto en esta comisión.",
                },
                status=400,
            )

        try:
            with transaction.atomic():
                if ciudadano_form is not None:
                    ciudadano.save()
                inscripcion = InscripcionService.crear_inscripcion(
                    ciudadano=ciudadano,
                    comision=comision,
                    programa=comision.oferta.programa,
                    estado="inscripta",
                    origen_canal="backoffice",
                    observaciones=observaciones,
                    usuario=request.user,
                )
        except ValueError as exc:
            return JsonResponse(
                {"ok": False, "message": str(exc)},
                status=400,
            )

        return JsonResponse(
            {
                "ok": True,
                "message": f"Inscripción creada para {inscripcion.ciudadano.nombre_completo}.",
                "inscripcion_id": inscripcion.pk,
            }
        )


class InscripcionDetailView(LoginRequiredMixin, DetailView):
    model = Inscripcion
    template_name = "vat/persona/inscripcion_detail.html"
    context_object_name = "inscripcion"


class InscripcionUpdateView(LoginRequiredMixin, UpdateView):
    model = Inscripcion
    form_class = InscripcionForm
    template_name = "vat/persona/inscripcion_form.html"
    success_url = reverse_lazy("vat_inscripcion_list")

    def form_valid(self, form):
        messages.success(self.request, "Inscripción actualizada exitosamente.")
        return super().form_valid(form)


class InscripcionDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Inscripcion
    template_name = "vat/persona/inscripcion_confirm_delete.html"
    context_object_name = "inscripcion"
    success_url = reverse_lazy("vat_inscripcion_list")
