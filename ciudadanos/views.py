from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ciudadano = self.object
        relaciones = (
            GrupoFamiliar.objects.filter(
                Q(ciudadano_1=ciudadano) | Q(ciudadano_2=ciudadano)
            )
            .select_related("ciudadano_1", "ciudadano_2")
            .order_by("ciudadano_2__apellido")
        )
        familia = []
        for relacion in relaciones:
            if relacion.ciudadano_1_id == ciudadano.id:
                familiar = relacion.ciudadano_2
            else:
                familiar = relacion.ciudadano_1
            familia.append((relacion, familiar))
        ctx["familia"] = familia
        ctx["grupo_form"] = GrupoFamiliarForm(ciudadano=ciudadano)
        
        # Programas de transferencia
        from ciudadanos.models import ProgramaTransferencia
        ctx['programas_directos'] = ciudadano.programas_transferencia.filter(
            activo=True, categoria=ProgramaTransferencia.CATEGORIA_DIRECTA
        )
        ctx['programas_indirectos'] = ciudadano.programas_transferencia.filter(
            activo=True, categoria=ProgramaTransferencia.CATEGORIA_INDIRECTA
        )
        
        return ctx


class CiudadanosCreateView(LoginRequiredMixin, CreateView):
    model = Ciudadano
    form_class = CiudadanoForm
    template_name = "ciudadanos/ciudadano_form.html"

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


class CiudadanosDeleteView(LoginRequiredMixin, DeleteView):
    model = Ciudadano
    template_name = "ciudadanos/ciudadano_confirm_delete.html"
    success_url = reverse_lazy("ciudadanos")


class GrupoFamiliarCreateView(LoginRequiredMixin, FormView):
    form_class = GrupoFamiliarForm
    template_name = "ciudadanos/grupofamiliar_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.ciudadano = get_object_or_404(Ciudadano, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["ciudadano"] = self.ciudadano
        return kwargs

    def form_valid(self, form):
        relacion = form.save()
        messages.success(self.request, "Familiar agregado correctamente.")
        return redirect(relacion.ciudadano_1.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ciudadano"] = self.ciudadano
        return ctx


class GrupoFamiliarDeleteView(LoginRequiredMixin, DeleteView):
    model = GrupoFamiliar
    template_name = "ciudadanos/grupofamiliar_confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Relación familiar eliminada.")
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return self.object.ciudadano_1.get_absolute_url()
