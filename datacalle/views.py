from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from datacalle.forms import RelevamientoForm
from datacalle.models import Relevamiento
from datacalle.services import (
    apply_relevamientos_scope,
    delete_relevamiento,
    get_relevamientos_queryset,
    save_relevamiento_from_form,
)


class RelevamientoScopeMixin(LoginRequiredMixin):
    """Todo lo que se ve o se edita pasa por el alcance provincial (D2.1)."""

    def get_queryset(self):
        return apply_relevamientos_scope(
            get_relevamientos_queryset(), self.request.user
        )


class RelevamientoListView(RelevamientoScopeMixin, ListView):
    model = Relevamiento
    template_name = "datacalle/relevamiento_list.html"
    context_object_name = "relevamientos"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = (self.request.GET.get("estado") or "").strip()
        if estado in Relevamiento.Estado.values:
            queryset = queryset.filter(estado=estado)

        busqueda = (self.request.GET.get("busqueda") or "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(denominacion__icontains=busqueda)
                | Q(area_operativa__icontains=busqueda)
                | Q(provincia__nombre__icontains=busqueda)
                | Q(localidad__nombre__icontains=busqueda)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Buscar Relevamientos"
        context["reset_url"] = reverse("datacalle_relevamientos_listar")
        context["add_url"] = (
            reverse("datacalle_relevamientos_crear")
            if self.request.user.has_perm("datacalle.add_relevamiento")
            else None
        )
        context["estados"] = Relevamiento.Estado.choices
        context["estado_actual"] = self.request.GET.get("estado") or ""
        context["busqueda_actual"] = self.request.GET.get("busqueda") or ""
        return context


class RelevamientoDetailView(RelevamientoScopeMixin, DetailView):
    model = Relevamiento
    template_name = "datacalle/relevamiento_detail.html"
    context_object_name = "relevamiento"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"text": "Relevamientos", "url": reverse("datacalle_relevamientos_listar")},
            {"text": self.object.denominacion},
        ]
        return context


class RelevamientoFormMixin:
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "datacalle/relevamiento_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = save_relevamiento_from_form(form, user=self.request.user)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("datacalle_relevamientos_detalle", kwargs={"pk": self.object.pk})


class RelevamientoCreateView(RelevamientoFormMixin, LoginRequiredMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Planificar relevamiento"
        return context


class RelevamientoUpdateView(RelevamientoFormMixin, RelevamientoScopeMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar relevamiento"
        return context


class RelevamientoDeleteView(RelevamientoScopeMixin, DeleteView):
    model = Relevamiento
    template_name = "datacalle/relevamiento_confirm_delete.html"
    context_object_name = "relevamiento"
    success_url = reverse_lazy("datacalle_relevamientos_listar")

    def form_valid(self, form):
        delete_relevamiento(self.get_object(), user=self.request.user)
        return HttpResponseRedirect(self.success_url)
