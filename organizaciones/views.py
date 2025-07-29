from django.contrib import messages
from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from organizaciones.forms import (
    OrganizacionForm,
    FirmanteFormset,
    Aval1Formset,
    Aval2Formset,
)
from organizaciones.models import Organizacion, SubtipoEntidad


class OrganizacionListView(ListView):
    model = Organizacion
    template_name = "organizacion_list.html"
    context_object_name = "organizaciones"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            # Solo ejecutar queries cuando hay búsqueda específica
            queryset = (
                Organizacion.objects.filter(
                    Q(nombre__icontains=query)
                    | Q(cuit__icontains=query)
                    | Q(telefono__icontains=query)
                    | Q(email__icontains=query)
                )
                .select_related()
                .select_related("tipo_entidad", "subtipo_entidad", "tipo_organizacion")
                .only(
                    "id",
                    "nombre",
                    "cuit",
                    "telefono",
                    "email",
                    "tipo_entidad__nombre",
                    "subtipo_entidad__nombre",
                    "tipo_organizacion__nombre",
                )
            )
        else:
            # Para la vista inicial sin búsqueda, usar paginación eficiente
            queryset = (
                Organizacion.objects.select_related(
                    "tipo_entidad", "subtipo_entidad", "tipo_organizacion"
                )
                .only(
                    "id",
                    "nombre",
                    "cuit",
                    "telefono",
                    "email",
                    "tipo_entidad__nombre",
                    "subtipo_entidad__nombre",
                    "tipo_organizacion__nombre",
                )
                .order_by("-id")
            )
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener la query de búsqueda
        query = self.request.GET.get("busqueda", "")
        
        # Preparar breadcrumb_items
        breadcrumb_items = [
            {
                'url': reverse('organizaciones'),  # ✅ Correcto según tus URLs
                'text': 'Organizaciones'
            }
        ]
        
        # Obtener datos de paginación
        page_obj = context.get('page_obj')
        is_paginated = context.get('is_paginated', False)
        organizaciones = context.get('organizaciones', [])
        
        # Renderizar el contenido de la tabla
        table_content = render_to_string('components/tables/organizacion_table.html', {
            'organizaciones': page_obj if is_paginated else organizaciones,
            'page_obj': page_obj if is_paginated else None,
            'query': query,
            'is_paginated': is_paginated
        }, request=self.request)
        
        # Agregar al contexto
        context.update({
            'breadcrumb_items': breadcrumb_items,
            'table_content': table_content,
            'query': query,
        })
        
        return context

class OrganizacionCreateView(CreateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formsets existentes
        if self.request.POST:
            context["firmante_formset"] = FirmanteFormset(self.request.POST)
            context["aval1_formset"] = Aval1Formset(self.request.POST)
            context["aval2_formset"] = Aval2Formset(self.request.POST)
        else:
            context["firmante_formset"] = FirmanteFormset()
            context["aval1_formset"] = Aval1Formset()
            context["aval2_formset"] = Aval2Formset()
        
        # Breadcrumb para crear
        breadcrumb_items = [
            {
                'url': reverse('organizaciones'),
                'text': 'Organizaciones'
            }
        ]
        context['breadcrumb_items'] = breadcrumb_items
        context['current_item'] = 'Agregar'
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        firmante_formset = context["firmante_formset"]
        aval1_formset = context["aval1_formset"]
        aval2_formset = context["aval2_formset"]
        if (
            firmante_formset.is_valid()
            and aval1_formset.is_valid()
            and aval2_formset.is_valid()
        ):
            self.object = form.save()
            firmante_formset.instance = self.object
            aval1_formset.instance = self.object
            aval2_formset.instance = self.object
            firmante_formset.save()
            aval1_formset.save()
            aval2_formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})


class OrganizacionUpdateView(UpdateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formsets existentes
        if self.request.POST:
            context["firmante_formset"] = FirmanteFormset(
                self.request.POST, instance=self.object
            )
            context["aval1_formset"] = Aval1Formset(
                self.request.POST, instance=self.object
            )
            context["aval2_formset"] = Aval2Formset(
                self.request.POST, instance=self.object
            )
        else:
            context["firmante_formset"] = FirmanteFormset(instance=self.object)
            context["aval1_formset"] = Aval1Formset(instance=self.object)
            context["aval2_formset"] = Aval2Formset(instance=self.object)
        
        # Breadcrumb para editar
        breadcrumb_items = [
            {
                'url': reverse('organizaciones'),
                'text': 'Organizaciones'
            },
            {
                'url': reverse('organizacion_detalle', kwargs={'pk': self.object.pk}),
                'text': self.object.nombre
            }
        ]
        context['breadcrumb_items'] = breadcrumb_items
        context['current_item'] = 'Editar'
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        firmante_formset = context["firmante_formset"]
        aval1_formset = context["aval1_formset"]
        aval2_formset = context["aval2_formset"]
        if (
            firmante_formset.is_valid()
            and aval1_formset.is_valid()
            and aval2_formset.is_valid()
        ):
            self.object = form.save()
            firmante_formset.instance = self.object
            aval1_formset.instance = self.object
            aval2_formset.instance = self.object
            firmante_formset.save()
            aval1_formset.save()
            aval2_formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})


class OrganizacionDetailView(DetailView):
    model = Organizacion
    template_name = "organizacion_detail.html"
    context_object_name = "organizacion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Datos existentes
        context["firmantes"] = self.object.firmantes.select_related("rol")
        context["avales1"] = self.object.avales1.all()
        context["avales2"] = self.object.avales2.all()
        
        # Preparar breadcrumb_items
        breadcrumb_items = [
            {
                'url': reverse('organizaciones'),
                'text': 'Organizaciones'
            }
        ]
        
        context['breadcrumb_items'] = breadcrumb_items
        
        return context


class OrganizacionDeleteView(DeleteView):
    model = Organizacion
    template_name = "organizacion_confirm_delete.html"
    context_object_name = "organizacion"
    success_url = reverse_lazy("organizaciones")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(
                request,
                f"La organización {self.object.nombre} fue eliminada correctamente.",
            )
            return HttpResponseRedirect(self.success_url)
        except ValidationError as e:
            messages.error(request, e.message)
            return self.render_to_response(self.get_context_data(object=self.object))


def sub_tipo_entidad_ajax(request):
    tipo_entidad_id = request.GET.get("tipo_entidad")
    if tipo_entidad_id:
        subtipo_entidades = SubtipoEntidad.objects.filter(
            tipo_entidad_id=tipo_entidad_id
        ).order_by("nombre")
    else:
        subtipo_entidades = SubtipoEntidad.objects.none()

    data = [{"id": subtipo.id, "text": subtipo.nombre} for subtipo in subtipo_entidades]
    return JsonResponse(data, safe=False)
