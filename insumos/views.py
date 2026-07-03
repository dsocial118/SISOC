from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from .forms import InsumoCategoriaForm, InsumoForm
from .models import Insumo, InsumoCategoria
from .services import (
    delete_categoria,
    delete_insumo,
    get_categorias_queryset,
    get_insumos_queryset,
    save_categoria_from_form,
    save_insumo_from_form,
)

SIN_CATEGORIA = "sin"


class InsumoListView(LoginRequiredMixin, ListView):
    model = Insumo
    template_name = "insumos/insumos_list.html"
    context_object_name = "insumos"
    paginate_by = 20

    def get_queryset(self):
        queryset = get_insumos_queryset()

        categoria = (self.request.GET.get("categoria") or "").strip()
        if categoria == SIN_CATEGORIA:
            queryset = queryset.filter(categoria__isnull=True)
        elif categoria.isdigit():
            queryset = queryset.filter(categoria_id=int(categoria))

        query = (self.request.GET.get("busqueda") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) | Q(descripcion__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = get_categorias_queryset().filter(activo=True)
        context["categoria_seleccionada"] = (
            self.request.GET.get("categoria") or ""
        ).strip()
        context["busqueda"] = (self.request.GET.get("busqueda") or "").strip()
        context["puede_gestionar"] = self.request.user.has_perm("insumos.add_insumo")
        context["puede_gestionar_categorias"] = self.request.user.has_perm(
            "insumos.add_insumocategoria"
        )
        context["sin_categoria_value"] = SIN_CATEGORIA
        return context


class InsumoCreateView(LoginRequiredMixin, CreateView):
    model = Insumo
    form_class = InsumoForm
    template_name = "insumos/insumos_form.html"

    def form_valid(self, form):
        self.object = save_insumo_from_form(form, self.request.user)
        messages.success(self.request, "Insumo creado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("insumos_listar")


class InsumoUpdateView(LoginRequiredMixin, UpdateView):
    model = Insumo
    form_class = InsumoForm
    template_name = "insumos/insumos_form.html"

    def get_queryset(self):
        return get_insumos_queryset()

    def form_valid(self, form):
        self.object = save_insumo_from_form(
            form, self.request.user, instance=self.object
        )
        messages.success(self.request, "Insumo actualizado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("insumos_listar")


class InsumoDeleteView(LoginRequiredMixin, DeleteView):
    model = Insumo
    template_name = "insumos/insumos_confirm_delete.html"
    context_object_name = "insumo"

    def get_queryset(self):
        return get_insumos_queryset()

    def form_valid(self, form):
        self.object = self.get_object()
        delete_insumo(self.object)
        messages.success(self.request, "Insumo eliminado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("insumos_listar")


class InsumoDescargarView(LoginRequiredMixin, View):
    """Descarga protegida: el permiso se valida en la URL (view_insumo).

    El archivo no se sirve por su URL pública de MEDIA, sino a través de esta
    vista, garantizando que solo usuarios con permiso de consulta o gestión
    puedan descargarlo. Funciona aunque el insumo esté inactivo.
    """

    def get(self, request, pk):
        insumo = get_object_or_404(Insumo, pk=pk)
        if not insumo.archivo:
            raise Http404("El insumo no tiene archivo asociado.")
        try:
            archivo = insumo.archivo.open("rb")
        except (FileNotFoundError, OSError) as exc:
            raise Http404("El archivo del insumo no está disponible.") from exc
        return FileResponse(
            archivo,
            as_attachment=True,
            filename=insumo.nombre_archivo,
        )


class InsumoCategoriaListView(LoginRequiredMixin, ListView):
    model = InsumoCategoria
    template_name = "insumos/categoria_list.html"
    context_object_name = "categorias"
    paginate_by = 20

    def get_queryset(self):
        return get_categorias_queryset()


class InsumoCategoriaCreateView(LoginRequiredMixin, CreateView):
    model = InsumoCategoria
    form_class = InsumoCategoriaForm
    template_name = "insumos/categoria_form.html"
    success_url = reverse_lazy("insumos_categorias_listar")

    def form_valid(self, form):
        self.object = save_categoria_from_form(form)
        messages.success(self.request, "Categoría creada correctamente.")
        return HttpResponseRedirect(self.get_success_url())


class InsumoCategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = InsumoCategoria
    form_class = InsumoCategoriaForm
    template_name = "insumos/categoria_form.html"
    success_url = reverse_lazy("insumos_categorias_listar")

    def form_valid(self, form):
        self.object = save_categoria_from_form(form)
        messages.success(self.request, "Categoría actualizada correctamente.")
        return HttpResponseRedirect(self.get_success_url())


class InsumoCategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = InsumoCategoria
    template_name = "insumos/categoria_confirm_delete.html"
    context_object_name = "categoria"
    success_url = reverse_lazy("insumos_categorias_listar")

    def form_valid(self, form):
        self.object = self.get_object()
        delete_categoria(self.object)
        messages.success(self.request, "Categoría eliminada correctamente.")
        return HttpResponseRedirect(self.get_success_url())
