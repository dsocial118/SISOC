from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)


from cdi.forms import CentroDesarrolloInfantilForm
from cdi.models import CentroDesarrolloInfantil


class CDIListView(ListView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil_list.html"
    context_object_name = "centrodesarrolloinfantiles"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = CentroDesarrolloInfantil.objects.select_related(
            "organizacion", "provincia"
        ).order_by(
            "nombre"
        )  # Add ordering to prevent UnorderedObjectListWarning

        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(organizacion__nombre__icontains=query)
                | Q(numexpe__icontains=query)
                | Q(numrepo__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(telefono__icontains=query)
                | Q(email__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Breadcrumb items
        context["breadcrumb_items"] = [
            {"text": "Centro Desarrollo Infantil", "url": reverse("cdi")},
            {"text": "Listar", "active": True},
        ]

        # Search bar context
        context["query"] = self.request.GET.get("busqueda", "")

        # Data table headers (formato compatible con data_table.html)
        context["table_headers"] = [
            {"title": "Nombre"},
            {"title": "Número Expediente"},
            {"title": "Número Repi"},
            {"title": "Organización"},
            {"title": "Provincia"},
        ]

        # Fields para el componente data_table.html
        context["fields"] = [
            {"name": "nombre", "link_url": "cdi_detalle", "link_field": True},
            {"name": "numexpe"},
            {"name": "numrepo"},
            {"name": "organizacion"},
            {"name": "provincia"},
        ]

        # Actions para el componente data_table.html
        context["actions"] = [
            {"url_name": "cdi_detalle", "label": "Ver", "type": "info"},
            {"url_name": "cdi_editar", "label": "Editar", "type": "primary"},
            {"url_name": "cdi_eliminar", "label": "Eliminar", "type": "danger"},
        ]

        context["show_actions"] = True

        return context


class CDICreateView(CreateView):
    model = CentroDesarrolloInfantil
    form_class = CentroDesarrolloInfantilForm
    template_name = "centrodesarrolloinfantil_form.html"

    def get_success_url(self):
        return reverse("cdi")


class CDIDetailView(DetailView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil_detail.html"
    context_object_name = "centrodesarrolloinfantiles"


class CDIUpdateView(UpdateView):
    model = CentroDesarrolloInfantil
    form_class = CentroDesarrolloInfantilForm
    template_name = "centrodesarrolloinfantil_form.html"

    def get_success_url(self):
        return reverse("cdi_detalle", kwargs={"pk": self.object.pk})


class CDIDeleteView(DeleteView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil_confirm_delete.html"
    context_object_name = "centrodesarrolloinfantiles"
    success_url = reverse_lazy("cdi")


def cdi_ajax(request):
    """Endpoint AJAX para búsqueda filtrada de Centros de Desarrollo Infantil"""
    from django.template.loader import render_to_string
    from django.core.paginator import Paginator
    from django.http import JsonResponse
    from core.decorators import group_required

    # Aplicar el decorador manualmente para mantener permisos
    @group_required(["CDI"])
    def _cdi_ajax(request):
        query = request.GET.get("busqueda", "")
        page = request.GET.get("page", 1)

        # Obtener CDIs filtrados usando la misma lógica que la vista principal
        queryset = CentroDesarrolloInfantil.objects.select_related(
            "organizacion", "provincia"
        ).order_by("nombre")

        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(organizacion__nombre__icontains=query)
                | Q(numexpe__icontains=query)
                | Q(numrepo__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(telefono__icontains=query)
                | Q(email__icontains=query)
            )

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)

        context = {
            "centrodesarrolloinfantiles": page_obj,
            "request": request,
            "table_headers": [
                {"title": "Nombre"},
                {"title": "Número Expediente"},
                {"title": "Número Repi"},
                {"title": "Organización"},
                {"title": "Provincia"},
            ],
            "fields": [
                {"name": "nombre", "link_url": "cdi_detalle", "link_field": True},
                {"name": "numexpe"},
                {"name": "numrepo"},
                {"name": "organizacion"},
                {"name": "provincia"},
            ],
            "actions": [
                {"url_name": "cdi_detalle", "label": "Ver", "type": "info"},
                {"url_name": "cdi_editar", "label": "Editar", "type": "primary"},
                {"url_name": "cdi_eliminar", "label": "Eliminar", "type": "danger"},
            ],
            "show_actions": True,
        }

        html = render_to_string("partials/cdi_rows.html", context)

        pagination_html = render_to_string(
            "components/pagination.html",
            {"page_obj": page_obj, "is_paginated": page_obj.has_other_pages()},
        )

        return JsonResponse(
            {
                "html": html,
                "pagination_html": pagination_html,
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
                "current_page": page_obj.number,
            }
        )

    return _cdi_ajax(request)
