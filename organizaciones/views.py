from django.contrib import messages
from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from organizaciones.forms import (
    OrganizacionForm,
    FirmanteForm,
    Aval1Form, 
    Aval2Form
)
from organizaciones.models import Organizacion, SubtipoEntidad, Firmante, Aval1, Aval2
import logging

logger = logging.getLogger("django")

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
                .select_related("tipo_entidad", "subtipo_entidad")
                .only(
                    "id",
                    "nombre",
                    "cuit",
                    "telefono",
                    "email",
                    "tipo_entidad__nombre",
                    "subtipo_entidad__nombre",
                )
            )
        else:
            # Para la vista inicial sin búsqueda, usar paginación eficiente
            queryset = (
                Organizacion.objects.select_related(
                    "tipo_entidad", "subtipo_entidad"
                )
                .only(
                    "id",
                    "nombre",
                    "cuit",
                    "telefono",
                    "email",
                    "tipo_entidad__nombre",
                    "subtipo_entidad__nombre",
                )
                .order_by("-id")
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context

class FirmanteCreateView(CreateView):
    model = Firmante
    form_class = FirmanteForm
    template_name = "firmante_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizacion_pk = (
            self.kwargs.get("organizacion_pk")
            or self.kwargs.get("pk")
            or self.request.GET.get("organizacion")
            or self.request.POST.get("organizacion")
        )

        context["organizacion_pk"] = organizacion_pk
        context["hidden_fields_send"] = [{"name": "organizacion_id", "value": organizacion_pk}]
        # botones/breadcrumbs que usan las plantillas
        context["back_button"] = {"url": reverse("organizacion_detalle", kwargs={"pk": organizacion_pk}), "label": "Volver"}
        context["action_buttons"] = [{"label": "Guardar", "type": "submit"}]
        context["breadcrumb_items"] = []
        context["guardar_otro_send"] = True
        return context

    def form_valid(self, form):
        organizacion_pk = (
            self.kwargs.get("organizacion_id")
            or self.request.POST.get("organizacion_id")
            or self.request.GET.get("organizacion_id")
        )
        if not organizacion_pk:
            messages.error(self.request, "Falta el id de la organización.")
            return self.form_invalid(form)

        # asignar FK y guardar
        form.instance.organizacion_id = organizacion_pk
        self.object = form.save()
        if "guardar_otro" in self.request.POST:
            return HttpResponseRedirect(self.get_success_url_add_new())
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})
    
    def get_success_url_add_new(self):
        return reverse("firmante_crear", kwargs={"organizacion_pk": self.object.organizacion.pk})
    
class Aval1CreateView(CreateView):
    model = Aval1
    form_class = Aval1Form
    template_name = "aval1_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizacion_pk = (
            self.kwargs.get("organizacion_pk")
            or self.kwargs.get("pk")
            or self.request.GET.get("organizacion")
            or self.request.POST.get("organizacion")
        )

        context["organizacion_pk"] = organizacion_pk
        context["hidden_fields_send"] = [{"name": "organizacion_id", "value": organizacion_pk}]
        # botones/breadcrumbs que usan las plantillas
        context["back_button"] = {"url": reverse("organizacion_detalle", kwargs={"pk": organizacion_pk}), "label": "Volver"}
        context["action_buttons"] = [{"label": "Guardar", "type": "submit"}]
        context["breadcrumb_items"] = []
        context["guardar_otro_send"] = True
        return context
    
    def form_valid(self, form):
        if (
            form.is_valid()
        ):
            organizacion_pk = (
                self.kwargs.get("organizacion_id")
                or self.request.POST.get("organizacion_id")
                or self.request.GET.get("organizacion_id")
            )
            if not organizacion_pk:
                messages.error(self.request, "Falta el id de la organización.")
                return self.form_invalid(form)
            
            form.instance.organizacion_id = organizacion_pk
            self.object = form.save()
            if "guardar_otro" in self.request.POST:
                return HttpResponseRedirect(self.get_success_url_add_new())
            else:
                return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"organizacion_pk": self.object.organizacion.pk})
    
    def get_success_url_add_new(self):
        return reverse("firmante_crear", kwargs={"organizacion_pk": self.object.organizacion.pk})
    
class Aval2CreateView(CreateView):
    model = Aval2
    form_class = Aval2Form
    template_name = "aval2_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizacion_pk = (
            self.kwargs.get("organizacion_pk")
            or self.kwargs.get("pk")
            or self.request.GET.get("organizacion")
            or self.request.POST.get("organizacion")
        )

        context["organizacion_pk"] = organizacion_pk
        context["hidden_fields_send"] = [{"name": "organizacion_id", "value": organizacion_pk}]
        # botones/breadcrumbs que usan las plantillas
        context["back_button"] = {"url": reverse("organizacion_detalle", kwargs={"pk": organizacion_pk}), "label": "Volver"}
        context["action_buttons"] = [{"label": "Guardar", "type": "submit"}]
        context["breadcrumb_items"] = []
        context["guardar_otro_send"] = True
        return context
    
    def form_valid(self, form):
        if (
            form.is_valid()
        ):
            organizacion_pk = (
                self.kwargs.get("organizacion_id")
                or self.request.POST.get("organizacion_id")
                or self.request.GET.get("organizacion_id")
            )
            if not organizacion_pk:
                messages.error(self.request, "Falta el id de la organización.")
                return self.form_invalid(form)
            
            form.instance.organizacion_id = organizacion_pk
            self.object = form.save()
            if "guardar_otro" in self.request.POST:
                return HttpResponseRedirect(self.get_success_url_add_new())
            else:
                return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"organizacion_pk": self.object.organizacion.pk})
    
    def get_success_url_add_new(self):
        return reverse("firmante_crear", kwargs={"organizacion_pk": self.object.organizacion.pk})
    
class OrganizacionCreateView(CreateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        subtipo_entidad = form.cleaned_data.get("subtipo_entidad")
        if (
            form.is_valid()
        ):
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    
class FirmanteUpdateView(UpdateView):
    model = Firmante
    form_class = FirmanteForm
    template_name = "firmante_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["guardar_otro_send"] = False
        return context

    def form_valid(self, form):
        if (
            form.is_valid()
        ):
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
        

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})

class Aval1UpdateView(UpdateView):
    model = Aval1
    form_class = Aval1Form
    template_name = "aval1_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["guardar_otro_send"] = False
        return context

    def form_valid(self, form):
        if (
            form.is_valid()
        ):
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})
    
class Aval2UpdateView(UpdateView):
    model = Aval2
    form_class = Aval2Form
    template_name = "aval2_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["guardar_otro_send"] = False
        return context

    def form_valid(self, form):
        if (
            form.is_valid()
        ):
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})

class FirmanteDeleteView(DeleteView):
    model = Firmante
    template_name = "firmante_confirm_delete.html"
    context_object_name = "firmante"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"url": reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}), "label": "Detalle de Organización"},
            {"url": "", "label": "Confirmar Eliminación"},
        ]
        context["delete_message"] = f"¿Está seguro que desea eliminar al firmante {self.object.nombre}"
        context["cancel_url"] = reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})
        return context
    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})
    
class Aval1DeleteView(DeleteView):
    model = Aval1
    template_name = "aval1_confirm_delete.html"
    context_object_name = "aval1"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"url": reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}), "label": "Detalle de Organización"},
            {"url": "", "label": "Confirmar Eliminación"},
        ]
        context["delete_message"] = f"¿Está seguro que desea eliminar el aval {self.object.nombre}"
        context["cancel_url"] = reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})
        return context
    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})
    
class Aval2DeleteView(DeleteView):
    model = Aval2
    template_name = "aval2_confirm_delete.html"
    context_object_name = "aval2"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"url": reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}), "label": "Detalle de Organización"},
            {"url": "", "label": "Confirmar Eliminación"},
        ]
        context["delete_message"] = f"¿Está seguro que desea eliminar el aval {self.object.nombre}"
        context["cancel_url"] = reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})
        return context
    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.organizacion.pk})

class OrganizacionUpdateView(UpdateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        context = self.get_context_data()

        if (
            form.is_valid()
        ):
            self.object = form.save()
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
        context["firmantes"] = self.object.firmantes.select_related("rol")
        context["avales1"] = self.object.avales1.all()
        context["avales2"] = self.object.avales2.all()
        context["table_headers"] = [
            {"title": "Nombre"},
            {"title": "Rol"},
            {"title": "CUIT"},
        ]

        context["table_fields"] = [
            {"name": "nombre"},
            {"name": "rol"},
            {"name": "cuit"},
        ]

        context["actions"] = [
            {"url_name": "firmante_editar", "label": "Editar", "type": "primary"},
            {"url_name": "firmante_eliminar", "label": "Eliminar", "type": "danger"},
        ]

        context["show_actions"] = True

        context["data_items"] = [
            {"label": "Nombre", "value": self.object.nombre},
            {"label": "CUIT", "value": self.object.cuit},
            {"label": "Teléfono", "value": self.object.telefono},
            {"label": "Email", "value": self.object.email},
            {"label": "Tipo de Entidad", "value": self.object.tipo_entidad.nombre if self.object.tipo_entidad else ""},
            {"label": "Subtipo de Entidad", "value": self.object.subtipo_entidad.nombre if self.object.subtipo_entidad else ""},
            {"label": "Domicilio", "value": self.object.domicilio},
            {"label": "Localidad", "value": self.object.localidad},
            {"label": "Provincia", "value": self.object.provincia},
            {"label": "Partido", "value": self.object.partido},
        ]

        context["table_headers_avales"] = [
            {"title": "Nombre"},
            {"title": "CUIT"},
        ]
        context["actions_firmantes"] = [
            {"url_name": "firmante_editar", "label": "Editar", "type": "primary"},
            {"url_name": "firmante_eliminar", "label": "Eliminar", "type": "danger"},
        ]
        context["table_fields_avales"] = [
            {"name": "nombre"},
            {"name": "cuit"},
        ]
        context["actions_avales1"] = [
            {"url_name": "aval1_editar", "label": "Editar", "type": "primary"},
            {"url_name": "aval1_eliminar", "label": "Eliminar", "type": "danger"},
        ]
        context["actions_avales2"] = [
            {"url_name": "aval2_editar", "label": "Editar", "type": "primary"},
            {"url_name": "aval2_eliminar", "label": "Eliminar", "type": "danger"},
        ]
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
