from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied
from centrodefamilia.models import Centro, ActividadCentro, ParticipanteActividad
from centrodefamilia.forms import CentroForm
from centrodefamilia.services import CentroService
from configuraciones.decorators import group_required
from django.utils.decorators import method_decorator


class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "centros/centro_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        queryset = Centro.objects.select_related("faro_asociado", "referente")
        user = self.request.user

        if user.groups.filter(name="ReferenteCentro").exists() and not user.is_superuser:
            queryset = queryset.filter(referente=user)

        busqueda = self.request.GET.get("busqueda")
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) |
                Q(direccion__icontains=busqueda) |
                Q(tipo__icontains=busqueda)
            )

        return queryset.order_by("nombre")


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "centros/centro_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        es_referente = obj.referente_id == user.id
        es_adherido_de_faro = (
            obj.tipo == "adherido" and obj.faro_asociado and obj.faro_asociado.referente_id == user.id
        )

        if not (es_referente or es_adherido_de_faro or user.is_superuser):
            raise PermissionDenied

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = self.object

        actividades = (
            ActividadCentro.objects.filter(centro=centro)
            .select_related("actividad", "actividad__categoria")
        )

        participantes = (
            ParticipanteActividad.objects
            .filter(actividad_centro__in=actividades)
            .values("actividad_centro")
            .annotate(total=Count("id"))
        )

        participantes_map = {p["actividad_centro"]: p["total"] for p in participantes}

        actividades_con_ganancia = []
        for actividad in actividades:
            cantidad = participantes_map.get(actividad.id, 0)
            ganancia = (actividad.precio or 0) * cantidad
            actividades_con_ganancia.append({
                "obj": actividad,
                "ganancia": ganancia
            })

        context["actividades"] = actividades_con_ganancia

        if centro.tipo == "faro":
            context["centros_adheridos"] = Centro.objects.filter(faro_asociado=centro)

        return context


class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centro_list")

    def form_valid(self, form):
        messages.success(self.request, "Centro creado exitosamente.")
        return super().form_valid(form)


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Centro actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centro_detail", kwargs={"pk": self.object.pk})


class CentroDeleteView(LoginRequiredMixin, DeleteView):
    model = Centro
    success_url = reverse_lazy("centro_list")
    template_name = "includes/confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Centro eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
