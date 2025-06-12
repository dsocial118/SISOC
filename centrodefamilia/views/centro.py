from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from acompanamientos import forms
from centrodefamilia.forms import CentroForm
from centrodefamilia.models import Centro
from centrodefamilia.services import CentroService
from centrodefamilia.models import ActividadCentro
from django import forms
from django.views.generic.edit import DeleteView
from django.db.models import Q


class CentroDeleteView(LoginRequiredMixin, DeleteView):
    model = Centro
    template_name = "centros/centro_confirm_delete.html"
    success_url = reverse_lazy("centro_list")

    def post(self, request, *args, **kwargs):
        centro = self.get_object()
        centro.activo = False  # Eliminación lógica
        centro.save()
        messages.success(
            request, f"El centro '{centro.nombre}' fue desactivado correctamente."
        )
        return super().post(request, *args, **kwargs)


class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "centros/centro_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        queryset = Centro.objects.all()

        # Filtra por referente si pertenece al grupo 'ReferenteCentro' y no es superadmin
        if (
            self.request.user.groups.filter(name="ReferenteCentro").exists()
            and not self.request.user.is_superuser
        ):
            queryset = queryset.filter(referente=self.request.user)

        # Aplicar búsqueda si hay parámetro 'busqueda'
        busqueda = self.request.GET.get("busqueda")
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda)
                | Q(direccion__icontains=busqueda)
                | Q(tipo__icontains=busqueda)
            )

        return queryset


class CentroCreateView(CreateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centro_list")

    def get_initial(self):
        initial = super().get_initial()
        faro_id = self.request.GET.get("faro")
        if faro_id:
            initial["faro_asociado"] = faro_id
            initial["tipo"] = "adherido"
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        faro_id = self.request.GET.get("faro")
        if faro_id:
            form.fields["faro_asociado"].widget = forms.HiddenInput()
            form.fields["tipo"].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        messages.success(self.request, "Centro creado correctamente.")
        return super().form_valid(form)


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    fields = ["nombre", "tipo", "direccion", "contacto", "activo", "faro_asociado"]
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centro_list")

    def form_valid(self, form):
        messages.success(self.request, "Centro actualizado correctamente.")
        return super().form_valid(form)


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "centros/centro_detail.html"
    context_object_name = "centro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = self.get_object()

        # Actividades del centro
        context["actividades"] = ActividadCentro.objects.filter(centro=centro)

        if centro.tipo == "faro":
            # Centros adheridos obtenidos por servicio (si hay lógica extra)
            context["adheridos"] = CentroService.obtener_adheridos(centro)
            # Centros adheridos obtenidos directamente del modelo (para tabla)
            context["centros_adheridos"] = Centro.objects.filter(faro_asociado=centro)

        return context
