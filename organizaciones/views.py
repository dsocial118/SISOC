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
        context["query"] = self.request.GET.get("busqueda", "")
        return context

class FirmanteCreateView(CreateView):
    model = Firmante
    form_class = FirmanteForm
    template_name = "firmante_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
    
class Aval1CreateView(CreateView):
    model = Aval1
    form_class = Aval1Form
    template_name = "aval1_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
    
class Aval2CreateView(CreateView):
    model = Aval2
    form_class = Aval2Form
    template_name = "aval2_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
    
class OrganizacionCreateView(CreateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    def get_success_url_firmates(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    def get_success_url_avales1(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    def get_success_url_avales2(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    
class FirmanteUpdateView(UpdateView):
    model = Firmante
    form_class = FirmanteForm
    template_name = "firmante_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    def get_success_url_firmates(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    def get_success_url_avales1(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})
    def get_success_url_avales2(self):
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
