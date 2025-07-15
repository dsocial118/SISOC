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
from django.core.paginator import Paginator

from centrodefamilia.models import (
    Categoria,
    Centro,
    ActividadCentro,
    Expediente,
    ParticipanteActividad,
)
from centrodefamilia.forms import CentroForm


class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "centros/centro_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        qs = Centro.objects.select_related("faro_asociado", "referente")
        user = self.request.user

        if (
            user.groups.filter(name="ReferenteCentro").exists()
            and not user.is_superuser
        ):
            qs = qs.filter(Q(referente=user) | Q(faro_asociado__referente=user))

        busq = self.request.GET.get("busqueda")
        if busq:
            qs = qs.filter(Q(nombre__icontains=busq) | Q(tipo__icontains=busq))

        return qs.order_by("nombre")


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "centros/centro_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        es_referente = obj.referente_id == user.id
        es_adherido = (
            obj.tipo == "adherido"
            and obj.faro_asociado
            and obj.faro_asociado.referente_id == user.id
        )
        if not (es_referente or es_adherido or user.is_superuser):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = self.object

        # 1) Expedientes del centro (con paginación)
        qs_exp = Expediente.objects.filter(centro=centro).order_by("-fecha_subida")
        context["expedientes_cabal"] = Paginator(qs_exp, 3).get_page(
            self.request.GET.get("page_exp")
        )

        # 2) Actividades del centro con ganancia calculada en la base
        qs_acts = (
            ActividadCentro.objects.filter(centro=centro)
            .select_related("actividad", "actividad__categoria")
            .annotate(
                inscritos=Count("participanteactividad", distinct=True),
                ganancia=ExpressionWrapper(
                    F("precio") * F("inscritos"),
                    output_field=IntegerField(),
                ),
            )
        )
        context["actividades"] = list(qs_acts)
        context["total_actividades"] = qs_acts.count()

        # 3) Paginación de todas las actividades de otros centros
        otras = (
            ActividadCentro.objects.exclude(centro=centro)
            .select_related("actividad", "actividad__categoria", "centro")
            .order_by("centro__nombre", "actividad__nombre")
        )
        context["actividades_paginados"] = Paginator(otras, 5).get_page(
            self.request.GET.get("page_act")
        )

        # 4) Centros adheridos (si este es FARO)
        if centro.tipo == "faro":
            adheridos = Centro.objects.filter(
                faro_asociado=centro, activo=True
            ).order_by("nombre")
        else:
            adheridos = Centro.objects.none()
        context["centros_adheridos_paginados"] = Paginator(adheridos, 5).get_page(
            self.request.GET.get("page")
        )
        context["centros_adheridos_total"] = adheridos.count()

        # 5) Métricas y asistentes
        total_part = sum(a.inscritos for a in qs_acts)
        qs_part = ParticipanteActividad.objects.filter(
            actividad_centro__centro=centro
        ).select_related("ciudadano__sexo")
        hombres = qs_part.filter(ciudadano__sexo__sexo__iexact="Masculino").count()
        mujeres = qs_part.filter(ciudadano__sexo__sexo__iexact="Femenino").count()
        mixtas = total_part - hombres - mujeres

        context["metricas"] = {
            "centros_faro": context["centros_adheridos_total"],
            "categorias": Categoria.objects.count(),
            "actividades": context["total_actividades"],
            "interacciones": 0,
            "hombres": hombres,
            "mujeres": mujeres,
            "mixtas": mixtas,
        }
        context["asistentes"] = {
            "total": total_part,
            "hombres": hombres,
            "mujeres": mujeres,
        }

        return context


class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centro_list")

    def get_initial(self):
        initial = super().get_initial()
        faro_id = self.request.GET.get("faro")
        if faro_id:
            initial["tipo"] = "adherido"
            initial["faro_asociado"] = faro_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["from_faro"] = bool(self.request.GET.get("faro"))
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        if form.cleaned_data.get("tipo") == "adherido":
            form.instance.faro_asociado_id = self.request.GET.get("faro")
        if (
            user.groups.filter(name="ReferenteCentro").exists()
            and not user.is_superuser
        ):
            form.instance.referente = user
        messages.success(self.request, "Centro creado exitosamente.")
        return super().form_valid(form)


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user
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
