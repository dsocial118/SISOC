from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, F, ExpressionWrapper, IntegerField
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.conf import settings
from centrodefamilia.models import Centro, ActividadCentro, ParticipanteActividad
from centrodefamilia.forms import CentroForm
from django.utils.decorators import method_decorator


class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "centros/centro_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        # Cache la verificación del grupo para evitar queries repetidas
        user = self.request.user
        cache_key = f"user_is_referente_{user.id}"
        is_referente = cache.get(cache_key)

        if is_referente is None:
            is_referente = (
                user.groups.filter(name="ReferenteCentro").exists()
                and not user.is_superuser
            )
            cache.set(
                cache_key, is_referente, settings.DEFAULT_CACHE_TIMEOUT
            )  # Cache por 5 minutos

        queryset = Centro.objects.select_related("faro_asociado", "referente")

        # Un referente ve solo sus centros y los adheridos asociados a sus centros FARO
        if is_referente:
            queryset = queryset.filter(
                Q(referente=user) | Q(faro_asociado__referente=user)
            )

        busqueda = self.request.GET.get("busqueda")
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) | Q(tipo__icontains=busqueda)
            )

        return queryset.order_by("nombre")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar información cacheada al contexto para evitar re-query en templates
        user = self.request.user

        cache_key = f"user_is_referente_{user.id}"
        context["user_is_referente"] = cache.get(cache_key, False)

        # Control de botones “Agregar”
        context["can_add"] = (
            user.is_superuser or user.groups.filter(name="CDF SSE").exists()
        )

        return context


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "centros/centro_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        # Optimización: Prefetch centros adheridos para evitar queries adicionales
        queryset = queryset.prefetch_related("centro_set")

        obj = super().get_object(queryset)
        user = self.request.user

        # Optimización: Reutilizar cache ya creado en ListView o crearlo aquí
        cache_key = f"user_is_referente_{user.id}"
        is_referente_grupo = cache.get(cache_key)

        if is_referente_grupo is None:
            is_referente_grupo = (
                user.groups.filter(name="ReferenteCentro").exists()
                and not user.is_superuser
            )
            cache.set(cache_key, is_referente_grupo, settings.DEFAULT_CACHE_TIMEOUT)

        es_referente = obj.referente_id == user.id
        es_adherido_de_faro = (
            obj.tipo == "adherido"
            and obj.faro_asociado
            and obj.faro_asociado.referente_id == user.id
        )

        if not (es_referente or es_adherido_de_faro or user.is_superuser):
            raise PermissionDenied

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = self.object

        actividades = ActividadCentro.objects.filter(centro=centro).select_related(
            "actividad", "actividad__categoria"
        )

        participantes = (
            ParticipanteActividad.objects.filter(actividad_centro__in=actividades)
            .values("actividad_centro")
            .annotate(total=Count("id"))
        )

        participantes_map = {p["actividad_centro"]: p["total"] for p in participantes}

        actividades_con_ganancia = []
        for actividad in actividades:
            cantidad = participantes_map.get(actividad.id, 0)
            ganancia = (actividad.precio or 0) * cantidad
            actividades_con_ganancia.append({"obj": actividad, "ganancia": ganancia})

        context["actividades"] = actividades_con_ganancia
        context["total_actividades"] = actividades.count()
        context["total_participantes"] = sum(participantes_map.values())

        # Optimización: Usar relación prefetched en lugar de queries adicionales
        centros_adheridos = (
            centro.centro_set.all()
            if hasattr(centro, "centro_set")
            else Centro.objects.filter(faro_asociado=centro)
        )
        context["centros_adheridos_total"] = (
            len(centros_adheridos)
            if hasattr(centro, "centro_set")
            else Centro.objects.filter(faro_asociado=centro).count()
        )

        if centro.tipo == "faro":
            context["centros_adheridos"] = centros_adheridos

        # Add metricas and asistentes to the context
        context["metricas"] = {
            "total_ganancia": sum(
                item["ganancia"] for item in actividades_con_ganancia
            ),
            "promedio_ganancia": (
                sum(item["ganancia"] for item in actividades_con_ganancia)
                / len(actividades_con_ganancia)
                if actividades_con_ganancia
                else 0
            ),
        }
        context["asistentes"] = sum(participantes_map.values())
        return context


class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centro_list")

    def form_valid(self, form):
        user = self.request.user

        # Cache la verificación del grupo para evitar queries repetidas
        cache_key = f"user_is_referente_{user.id}"
        is_referente = cache.get(cache_key)

        if is_referente is None:
            is_referente = (
                user.groups.filter(name="ReferenteCentro").exists()
                and not user.is_superuser
            )
            cache.set(
                cache_key, is_referente, settings.DEFAULT_CACHE_TIMEOUT
            )  # Cache por 5 minutos

        # Si es referente, siempre se asigna como referente y solo puede crear adheridos
        if is_referente:
            form.instance.referente = user
            if form.cleaned_data.get("tipo") != "adherido":
                messages.error(self.request, "Solo puedes crear centros ADHERIDOS.")
                return self.form_invalid(form)

        messages.success(self.request, "Centro creado exitosamente.")
        return super().form_valid(form)


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user

        # Solo el referente del centro o el superadmin puede editar
        if not (centro.referente_id == user.id or user.is_superuser):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Centro actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centro_detail", kwargs={"pk": self.object.pk})


class CentroDeleteView(LoginRequiredMixin, DeleteView):
    model = Centro
    success_url = reverse_lazy("centro_list")
    template_name = "includes/confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user

        if not (centro.referente_id == user.id or user.is_superuser):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Centro eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
