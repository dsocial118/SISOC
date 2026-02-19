from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from centrodeinfancia.forms import (
    CentroDeInfanciaForm,
    IntervencionCentroInfanciaForm,
    NominaCentroInfanciaCreateForm,
    NominaCentroInfanciaForm,
)
from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
)
from core.decorators import group_required


class CentroDeInfanciaListView(LoginRequiredMixin, ListView):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = CentroDeInfancia.objects.select_related("organizacion").order_by(
            "nombre"
        )
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__nombre__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"text": "Centro de Infancia", "url": reverse("centrodeinfancia")},
            {"text": "Listar", "active": True},
        ]
        context["query"] = self.request.GET.get("busqueda", "")
        return context


class CentroDeInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = CentroDeInfancia
    form_class = CentroDeInfanciaForm
    template_name = "centrodeinfancia/centrodeinfancia_form.html"

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.object.pk})


class CentroDeInfanciaDetailView(LoginRequiredMixin, DetailView):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_detail.html"
    context_object_name = "centro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nomina_qs = self.object.nominas.select_related("ciudadano").order_by("-fecha")
        intervenciones_qs = self.object.intervenciones.select_related(
            "tipo_intervencion", "subintervencion", "destinatario"
        ).order_by("-fecha")

        nomina_page = self.request.GET.get("nomina_page", 1)
        intervenciones_page = self.request.GET.get("intervenciones_page", 1)

        nomina_paginator = Paginator(nomina_qs, 10)
        intervenciones_paginator = Paginator(intervenciones_qs, 10)

        context["nomina_page_obj"] = nomina_paginator.get_page(nomina_page)
        context["intervenciones_page_obj"] = intervenciones_paginator.get_page(
            intervenciones_page
        )
        context["nomina_total"] = nomina_qs.count()
        context["intervenciones_total"] = intervenciones_qs.count()
        return context


class CentroDeInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = CentroDeInfancia
    form_class = CentroDeInfanciaForm
    template_name = "centrodeinfancia/centrodeinfancia_form.html"

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.object.pk})


class CentroDeInfanciaDeleteView(LoginRequiredMixin, DeleteView):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_confirm_delete.html"
    context_object_name = "centro"
    success_url = reverse_lazy("centrodeinfancia")


@login_required
def centrodeinfancia_ajax(request):
    @group_required(["Centro de Infancia Listar"])
    def _centrodeinfancia_ajax(req):
        query = req.GET.get("busqueda", "")
        page = req.GET.get("page", 1)
        queryset = CentroDeInfancia.objects.select_related("organizacion").order_by(
            "nombre"
        )
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__nombre__icontains=query)
            )

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)
        html = render_to_string(
            "centrodeinfancia/partials/rows.html",
            {"centros": page_obj},
            request=req,
        )
        return JsonResponse(
            {
                "html": html,
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
            }
        )

    return _centrodeinfancia_ajax(request)


class NominaCentroInfanciaDetailView(LoginRequiredMixin, ListView):
    model = NominaCentroInfancia
    template_name = "centrodeinfancia/nomina_detail.html"
    context_object_name = "nomina"
    paginate_by = 20

    def get_queryset(self):
        return NominaCentroInfancia.objects.select_related("ciudadano").filter(
            centro_id=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(CentroDeInfancia, pk=self.kwargs["pk"])
        return context


class NominaCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = NominaCentroInfancia
    form_class = NominaCentroInfanciaCreateForm
    template_name = "centrodeinfancia/nomina_form.html"

    def form_valid(self, form):
        form.instance.centro_id = self.kwargs["pk"]
        messages.success(self.request, "Persona agregada a la nómina.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centrodeinfancia_nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(CentroDeInfancia, pk=self.kwargs["pk"])
        return context


class NominaCentroInfanciaDeleteView(LoginRequiredMixin, DeleteView):
    model = NominaCentroInfancia
    template_name = "centrodeinfancia/nomina_confirm_delete.html"
    pk_url_kwarg = "pk2"

    def get_success_url(self):
        return reverse("centrodeinfancia_nomina_ver", kwargs={"pk": self.kwargs["pk"]})


def nomina_centrodeinfancia_editar_ajax(request, pk):
    nomina = get_object_or_404(NominaCentroInfancia, pk=pk)
    if request.method == "POST":
        form = NominaCentroInfanciaForm(request.POST, instance=nomina)
        if form.is_valid():
            form.save()
            return JsonResponse(
                {"success": True, "message": "Datos modificados con éxito."}
            )
        return JsonResponse({"success": False, "errors": form.errors})

    form = NominaCentroInfanciaForm(instance=nomina)
    return render(
        request,
        "centrodeinfancia/nomina_editar_ajax.html",
        {"form": form},
    )


class IntervencionCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = IntervencionCentroInfancia
    form_class = IntervencionCentroInfanciaForm
    template_name = "centrodeinfancia/intervencion_form.html"

    def form_valid(self, form):
        form.instance.centro_id = self.kwargs["pk"]
        messages.success(self.request, "Intervención creada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


class IntervencionCentroInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = IntervencionCentroInfancia
    form_class = IntervencionCentroInfanciaForm
    pk_url_kwarg = "pk2"
    template_name = "centrodeinfancia/intervencion_form.html"

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


class IntervencionCentroInfanciaDeleteView(LoginRequiredMixin, DeleteView):
    model = IntervencionCentroInfancia
    template_name = "centrodeinfancia/intervencion_confirm_delete.html"
    pk_url_kwarg = "intervencion_id"

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


@login_required
@require_POST
def subir_archivo_intervencion_centrodeinfancia(request, intervencion_id):
    intervencion = get_object_or_404(IntervencionCentroInfancia, id=intervencion_id)
    if request.method == "POST" and request.FILES.get("documentacion"):
        intervencion.documentacion = request.FILES["documentacion"]
        intervencion.tiene_documentacion = True
        intervencion.save()
        return JsonResponse(
            {"success": True, "message": "Archivo subido correctamente."}
        )
    return JsonResponse({"success": False, "message": "No se proporcionó un archivo."})


@login_required
@require_POST
def eliminar_archivo_intervencion_centrodeinfancia(request, intervencion_id):
    intervencion = get_object_or_404(IntervencionCentroInfancia, id=intervencion_id)
    if intervencion.documentacion:
        intervencion.documentacion.delete()
        intervencion.tiene_documentacion = False
        intervencion.save()
        messages.success(request, "El archivo fue eliminado correctamente.")
    else:
        messages.error(request, "No hay archivo para eliminar.")
    return redirect("centrodeinfancia_detalle", pk=intervencion.centro_id)
