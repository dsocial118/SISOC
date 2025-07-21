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

        # 1) Superuser ve tod
        if user.is_superuser:
            pass

        # 2) CDF SSE ve todo
        elif user.groups.filter(name="CDF SSE").exists():
            pass

        # 3) ReferenteCentro ve SOLO los centros donde es referente
        elif user.groups.filter(name="ReferenteCentro").exists():
            qs = qs.filter(referente=user)

        # 4) Resto de usuarios no ven nada
        else:
            return Centro.objects.none()

        # Filtro de texto
        busq = self.request.GET.get("busqueda", "").strip()
        if busq:
            qs = qs.filter(Q(nombre__icontains=busq) | Q(tipo__icontains=busq))

        return qs.order_by("nombre")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Control de botones “Agregar”
        ctx["can_add"] = (
            user.is_superuser or user.groups.filter(name="CDF SSE").exists()
        )
        return ctx


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "centros/centro_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        es_ref = obj.referente_id == user.id
        es_adherido = (
            obj.tipo == "adherido"
            and obj.faro_asociado
            and obj.faro_asociado.referente_id == user.id
        )
        es_cdf_sse = user.groups.filter(name="CDF SSE").exists()
        if not (es_ref or es_adherido or user.is_superuser
                or es_cdf_sse):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        centro = self.object

        # 1) Expedientes paginados
        qs_exp = Expediente.objects.filter(centro=centro).order_by("-fecha_subida")
        ctx["expedientes_cabal"] = Paginator(qs_exp, 3).get_page(
            self.request.GET.get("page_exp")
        )

        # 2) Actividades con inscritos y ganancia en DB
        qs_acts = (
            ActividadCentro.objects.filter(centro=centro)
            .select_related("actividad", "actividad__categoria")
            .annotate(
                inscritos=Count("participanteactividad", distinct=True),
                ganancia=ExpressionWrapper(
                    F("precio") * F("inscritos"), output_field=IntegerField()
                ),
            )
        )
        ctx["actividades"] = list(qs_acts)
        ctx["total_actividades"] = qs_acts.count()

        # 3) Otras actividades (paginadas)
        otras = (
            ActividadCentro.objects.exclude(centro=centro)
            .select_related("actividad", "actividad__categoria", "centro")
            .order_by("centro__nombre", "actividad__nombre")
        )
        ctx["actividades_paginados"] = Paginator(otras, 5).get_page(
            self.request.GET.get("page_act")
        )

        # 4) Centros adheridos FARO
        if centro.tipo == "faro":
            adheridos = Centro.objects.filter(
                faro_asociado=centro, activo=True
            ).order_by("nombre")
        else:
            adheridos = Centro.objects.none()
        ctx["centros_adheridos_paginados"] = Paginator(adheridos, 5).get_page(
            self.request.GET.get("page")
        )
        ctx["centros_adheridos_total"] = adheridos.count()

        # 5) Métricas avanzadas
        total_part = sum(a.inscritos for a in qs_acts)
        qs_part = ParticipanteActividad.objects.filter(actividad_centro__centro=centro)
        hombres = qs_part.filter(ciudadano__sexo__sexo__iexact="Masculino").count()
        mujeres = qs_part.filter(ciudadano__sexo__sexo__iexact="Femenino").count()
        mixtas = total_part - hombres - mujeres

        ctx["metricas"] = {
            "centros_faro": ctx["centros_adheridos_total"],
            "categorias": Categoria.objects.count(),
            "actividades": ctx["total_actividades"],
            "interacciones": total_part,
            "hombres": hombres,
            "mujeres": mujeres,
            "mixtas": mixtas,
        }
        ctx["asistentes"] = {
            "total": total_part,
            "hombres": hombres,
            "mujeres": mujeres,
        }
        return ctx


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
