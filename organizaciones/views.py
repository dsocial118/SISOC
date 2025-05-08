from django.contrib import messages
from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpResponseRedirect
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
    OrganizacionJuridicaForm,
    OrganizacionEclesiasticaForm,
    OrganizacionHechoForm,
)
from organizaciones.models import Organizacion


class OrganizacionListView(ListView):
    model = Organizacion
    template_name = "organizacion_list.html"
    context_object_name = "organizaciones"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = Organizacion.objects.all()

        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(cuit__icontains=query)
                | Q(telefono__icontains=query)
                | Q(email__icontains=query)
            )

        return queryset


class OrganizacionCreateView(CreateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["juridica_form"] = OrganizacionJuridicaForm(self.request.POST)
            context["eclesiastica_form"] = OrganizacionEclesiasticaForm(self.request.POST)
            context["hecho_form"] = OrganizacionHechoForm(self.request.POST)
        else:
            context["juridica_form"] = OrganizacionJuridicaForm()
            context["eclesiastica_form"] = OrganizacionEclesiasticaForm()
            context["hecho_form"] = OrganizacionHechoForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        juridica_form = context["juridica_form"]
        eclesiastica_form = context["eclesiastica_form"]
        hecho_form = context["hecho_form"]

        if (
            juridica_form.is_valid()
            and eclesiastica_form.is_valid()
            and hecho_form.is_valid()
        ):
            # Guarda la organización principal
            self.object = form.save()

            # Guarda los formularios relacionados y asocia sus IDs a la organización
            juridica = juridica_form.save()
            eclesiastica = eclesiastica_form.save()
            hecho = hecho_form.save()

            self.object.firmante_juridica_id = juridica.id
            self.object.firmante_eclesiastica_id = eclesiastica.id
            self.object.firmante_hecho_id = hecho.id
            self.object.save()

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
        if self.request.POST:
            context["juridica_form"] = OrganizacionJuridicaForm(
                self.request.POST, instance=self.object.firmante_juridica
            )
            context["eclesiastica_form"] = OrganizacionEclesiasticaForm(
                self.request.POST, instance=self.object.firmante_eclesiastica
            )
            context["hecho_form"] = OrganizacionHechoForm(
                self.request.POST, instance=self.object.firmante_hecho
            )
        else:
            context["juridica_form"] = OrganizacionJuridicaForm(instance=self.object.firmante_juridica)
            context["eclesiastica_form"] = OrganizacionEclesiasticaForm(instance=self.object.firmante_eclesiastica)
            context["hecho_form"] = OrganizacionHechoForm(instance=self.object.firmante_hecho)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        juridica_form = context["juridica_form"]
        eclesiastica_form = context["eclesiastica_form"]
        hecho_form = context["hecho_form"]

        if (
            juridica_form.is_valid()
            and eclesiastica_form.is_valid()
            and hecho_form.is_valid()
        ):
            # Guarda la organización principal
            self.object = form.save()

            # Guarda los formularios relacionados
            juridica = juridica_form.save()
            eclesiastica = eclesiastica_form.save()
            hecho = hecho_form.save()

            # Asocia los formularios relacionados a la organización
            self.object.firmante_juridica = juridica
            self.object.firmante_eclesiastica = eclesiastica
            self.object.firmante_hecho = hecho
            self.object.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})


class OrganizacionDetailView(DetailView):
    model = Organizacion
    template_name = "organizacion_detail.html"
    context_object_name = "organizacion"


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
