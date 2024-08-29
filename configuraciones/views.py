from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from usuarios.mixins import PermisosMixin

from .forms import *
from .models import *
from .utils import insertar_programas

# region ############################################################### Secretarías


class SecretariasListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Secretarias

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query) | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class SecretariasDetailView(PermisosMixin, DetailView):
    permission_required = permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Secretarias


class SecretariasDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = permission_required = "Usuarios.rol_admin"
    model = Secretarias
    success_url = reverse_lazy("secretarias_listar")
    success_message = "El registro fue eliminado correctamente"


class SecretariasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = permission_required = "Usuarios.rol_admin"
    model = Secretarias
    form_class = SecretariasForm
    success_message = "%(nombre)s fue registrado correctamente"


class SecretariasUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Secretarias
    form_class = SecretariasForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### Subsecretarías


class SubsecretariasListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Subsecretarias

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(fk_secretaria__nombre__icontains=query)
                | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class SubsecretariasDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Subsecretarias


class SubsecretariasDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Subsecretarias
    success_url = reverse_lazy("secretarias_listar")
    success_message = "El registro fue eliminado correctamente"


class SubsecretariasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Subsecretarias
    form_class = SubsecretariasForm
    success_message = "%(nombre)s fue registrado correctamente"


class SubsecretariasUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Subsecretarias
    form_class = SubsecretariasForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### Organismos


class OrganismosListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Organismos

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class OrganismosDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Organismos

    def get_context_data(self, *args, **kwargs):
        # El pk que pasas a la URL

        pk = self.kwargs.get("pk")
        context = super(OrganismosDetailView, self).get_context_data(**kwargs)
        context["referentes"] = AgentesExternos.objects.filter(fk_organismo=pk)

        return context


class OrganismosDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Organismos
    success_url = reverse_lazy("organismos_listar")
    success_message = "El registro fue eliminado correctamente"


class OrganismosCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Organismos
    form_class = OrganismosForm
    success_message = "%(nombre)s fue registrado correctamente"


class OrganismosUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Organismos
    form_class = OrganismosForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### Programas


class ProgramasListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Programas
    template_name = "programas_list.html"

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(fk_secretaria__nombre__icontains=query)
                | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class ProgramasDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Programas


class ProgramasDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Programas
    success_url = reverse_lazy("programas_listar")
    success_message = "El registro fue eliminado correctamente"


class ProgramasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Programas
    form_class = ProgramasForm
    success_message = "%(nombre)s fue registrado correctamente"


class ProgramasUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Programas
    form_class = ProgramasForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### PlanesSociales


class PlanesSocialesListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = PlanesSociales

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(jurisdiccion__icontains=query)
                | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class PlanesSocialesDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = PlanesSociales


class PlanesSocialesDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = PlanesSociales
    success_url = reverse_lazy("planes_sociales_listar")
    success_message = "El registro fue eliminado correctamente"


class PlanesSocialesCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = PlanesSociales
    form_class = PlanesSocialesForm
    success_message = "%(nombre)s fue registrado correctamente"


class PlanesSocialesUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = PlanesSociales
    form_class = PlanesSocialesForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### AgentesExternos


class AgentesExternosListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = AgentesExternos

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(apellido__icontains=query)
                | Q(fk_organismo__nombre__icontains=query)
                | Q(email__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class AgentesExternosDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = AgentesExternos


class AgentesExternosDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = AgentesExternos
    success_url = reverse_lazy("agentesexternos_listar")
    success_message = "El registro fue eliminado correctamente"


class AgentesExternosCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = AgentesExternos
    form_class = AgentesExternosForm
    success_message = "%(nombre)s fue registrado correctamente"

    def get_initial(self):
        """

        Si la petición viene desde una organización, la asigna a la instancia como incial.

        """

        pk = self.kwargs.get("pk")
        initial = super().get_initial()
        if pk:
            initial["fk_organismo"] = pk
        return initial


class AgentesExternosUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = AgentesExternos
    form_class = AgentesExternosForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### GruposDestinatarios


class GruposDestinatariosListView(PermisosMixin, ListView):
    permission_required = [
        "Configuraciones.view_gruposdestinatarios",
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = GruposDestinatarios

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(m2m_usuarios__usuario__icontains=query)
                | Q(m2m_agentesexternos__nombre__icontains=query)
                | Q(m2m_agentesexternos__apellido__icontains=query)
                | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class GruposDestinatariosDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = GruposDestinatarios


class GruposDestinatariosDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = GruposDestinatarios
    success_url = reverse_lazy("gruposdestinatarios_listar")
    success_message = "El registro fue eliminado correctamente"


class GruposDestinatariosCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = GruposDestinatarios
    form_class = GruposDestinatariosForm
    success_message = "%(nombre)s fue registrado correctamente"


class GruposDestinatariosUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = GruposDestinatarios
    form_class = GruposDestinatariosForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### Categoría de Alertas


class CategoriaAlertasListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = CategoriaAlertas

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(nombre__icontains=query)

        else:
            object_list = self.model.objects.all()

        return object_list


class CategoriaAlertasDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = CategoriaAlertas


class CategoriaAlertasDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = CategoriaAlertas
    success_url = reverse_lazy("categoriaalertas_listar")
    success_message = "El registro fue eliminado correctamente"


class CategoriaAlertasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = CategoriaAlertas
    form_class = CategoriaAlertasForm

    success_message = "%(nombre)s fue registrado correctamente"


class CategoriaAlertasUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = CategoriaAlertas
    form_class = CategoriaAlertasForm

    success_message = "%(nombre)s fue editado correctamente"


# endregion

# region ############################################################### Alertas


class AlertasListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Alertas

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(nombre__icontains=query)

        else:
            object_list = self.model.objects.all()

        return object_list


class AlertasDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Alertas


class AlertasDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Alertas
    success_url = reverse_lazy("alertas_listar")
    success_message = "El registro fue eliminado correctamente"


class AlertasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Alertas
    form_class = AlertasForm

    success_message = "%(nombre)s fue registrado correctamente"


class AlertasUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Alertas
    form_class = AlertasForm

    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### Equipos


class EquiposListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Equipos

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(fk_programa__nombre__icontains=query)
                | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class EquiposDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Equipos


class EquiposDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Equipos
    success_url = reverse_lazy("equipos_listar")
    success_message = "El registro fue eliminado correctamente"


class EquiposCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Equipos
    form_class = EquiposForm
    success_message = "%(nombre)s fue registrado correctamente"

    def form_valid(self, form):
        """If the form is valid, save the associated model."""

        print(form.cleaned_data)

        self.object = form.save()

        return super().form_valid(form)


class EquiposUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Equipos
    form_class = EquiposForm
    success_message = "%(nombre)s fue editado correctamente"

    def form_valid(self, form):
        """If the form is valid, save the associated model."""

        print(form.cleaned_data)

        self.object = form.save()

        return super().form_valid(form)


# endregion


# region ############################################################### Acciones


class AccionesListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Acciones

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query) | Q(dimension__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class AccionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = Acciones


class AccionesDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Acciones
    success_url = reverse_lazy("acciones_listar")
    success_message = "El registro fue eliminado correctamente"


class AccionesCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Acciones
    form_class = AccionesForm
    success_message = "%(nombre)s fue registrado correctamente"


class AccionesUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Acciones
    form_class = AccionesForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### Criterios


class CriteriosListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(dimension__icontains=query)
                | Q(fk_sujeto__nombre__icontains=query)
                | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class CriteriosDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios


class CriteriosDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios
    success_url = reverse_lazy("criterios_listar")
    success_message = "El registro fue eliminado correctamente"


class CriteriosCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios
    form_class = CriteriosForm
    success_message = "%(nombre)s fue registrado correctamente"


class CriteriosUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios
    form_class = CriteriosForm
    success_message = "%(nombre)s fue editado correctamente"


# endregion


# region ############################################################### Indices


class IndicesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    model = Indices

    # Funcion de busqueda

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(m2m_criterios__nombre__icontains=query)
                | Q(m2m_programas__nombre__icontains=query)
                | Q(observaciones__icontains=query)
            ).distinct()

        else:
            object_list = self.model.objects.all()

        return object_list


class IndicesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = Indices


class IndicesDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Indices
    success_url = reverse_lazy("indices_listar")
    success_message = "El registro fue eliminado correctamente"


class IndiceInline:
    """

    De esta clase heredaran las clases create y update, para realizar validaciones.

    """

    form_class = IndicesForm
    model = Indices
    template_name = "Configuraciones/indices_form.html"

    def form_valid(self, form):
        named_formsets = self.get_named_formsets()

        if not all((x.is_valid() for x in named_formsets.values())):
            return self.render_to_response(self.get_context_data(form=form))

        self.object = form.save()

        # for every formset, attempt to find a specific formset save function

        # otherwise, just save.

        for name, formset in named_formsets.items():
            formset_save_func = getattr(self, "formset_{0}_valid".format(name), None)

            if formset_save_func is not None:
                formset_save_func(formset)

            else:
                formset.save()

        messages.success(self.request, ("Índice guardado con éxito."))

        return redirect("indices_listar")

    def formset_variants_valid(self, formset):
        """

        Hook for custom formset saving.Useful if you have multiple formsets

        """

        variants = formset.save(commit=False)

        # self.save_formset(formset, contact)

        # add this 2 lines, if you have can_delete=True parameter

        # set in inlineformset_factory func

        for obj in formset.deleted_objects:
            obj.delete()

        for variant in variants:
            variant.fk_indice = Indices.objects.get(id=self.object.id)

            variant.save()


def delete_variant(request, pk):
    try:
        variant = IndiceCriterios.objects.get(id=pk)

    except IndiceCriterios.DoesNotExist:
        messages.success(request, "No existe el criterio")

        return redirect("indices_listar")

    variant.delete()

    messages.success(request, "Criterio eliminado con éxito")

    return redirect("indices_editar", pk=variant.fk_indice.id)


class IndicesCreateView(PermisosMixin, IndiceInline, CreateView):
    permission_required = "Usuarios.rol_admin"

    def get_context_data(self, **kwargs):
        ctx = super(IndicesCreateView, self).get_context_data(**kwargs)

        ctx["named_formsets"] = self.get_named_formsets()

        return ctx

    def get_named_formsets(self):
        if self.request.method == "GET":
            return {
                "variants": IndicesFormset(prefix="variants"),
            }

        else:
            return {
                "variants": IndicesFormset(
                    self.request.POST or None,
                    self.request.FILES or None,
                    prefix="variants",
                ),
            }


class IndicesUpdateView(PermisosMixin, IndiceInline, UpdateView):
    permission_required = "Usuarios.rol_admin"

    def get_context_data(self, **kwargs):
        ctx = super(IndicesUpdateView, self).get_context_data(**kwargs)

        ctx["named_formsets"] = self.get_named_formsets()

        return ctx

    def get_named_formsets(self):
        return {
            "variants": IndicesFormset(
                self.request.POST or None,
                self.request.FILES or None,
                instance=self.object,
                prefix="variants",
            ),
        }


# endregion


# region ############################################################### Vacantes


class VacantesListView(PermisosMixin, ListView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Vacantes

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            object_list = self.model.objects.filter(
                Q(nombre__icontains=query)
                | Q(sala__icontains=query)
                | Q(turno__icontains=query)
            ).distinct()
        else:
            object_list = self.model.objects.all()

        return object_list


class VacantesDetailView(PermisosMixin, DetailView):
    permission_required = [
        "Usuarios.rol_admin",
        "Usuarios.rol_observador",
        "Usuarios.rol_consultante",
    ]
    model = Vacantes


class VacantesDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Vacantes
    success_url = reverse_lazy("vacantes_listar")
    success_message = "El registro fue eliminado correctamente"


class VacantesCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Vacantes
    form_class = VacantesForm
    success_message = "%(nombre)s fue registrado correctamente"


class VacantesUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Vacantes
    form_class = VacantesForm
    success_message = "%(nombre)s fue editado correctamente"
