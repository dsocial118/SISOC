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
from django.db.models import Q, Count
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
        qs_exp = Expediente.objects.filter(centro=centro).order_by("-fecha_subida")
        paginator_exp = Paginator(qs_exp, 3)
        page_exp = self.request.GET.get("page_exp")
        context["expedientes_cabal"] = paginator_exp.get_page(page_exp)

        #
        # 1) Actividades del propio centro
        #
        qs_centro = ActividadCentro.objects.filter(centro=centro).select_related(
            "actividad", "actividad__categoria"
        )
        part_por_act = (
            ParticipanteActividad.objects.filter(actividad_centro__in=qs_centro)
            .values("actividad_centro")
            .annotate(total=Count("id"))
        )
        mapa = {p["actividad_centro"]: p["total"] for p in part_por_act}

        actividades = []
        for act in qs_centro:
            cnt = mapa.get(act.id, 0)
            actividades.append({"obj": act, "ganancia": (act.precio or 0) * cnt})

        context["actividades"] = actividades
        context["total_actividades"] = qs_centro.count()

        #
        # 2) Paginación de TODAS las actividades (actividades_paginados)
        #
        # (2) Paginación de TODAS las actividades (actividades_paginados)
        todas_acts = (
            ActividadCentro.objects
            # Excluyo las del centro que estamos viendo
            .exclude(centro=centro)
            .select_related("actividad", "actividad__categoria", "centro")
            .order_by("centro__nombre", "actividad__nombre")
        )
        pag_all = Paginator(todas_acts, 5)
        page_act = self.request.GET.get("page_act")
        context["actividades_paginados"] = pag_all.get_page(page_act)

        #
        # 3) Centros adheridos y su paginación
        #
        if centro.tipo == "faro":
            qs_adheridos = Centro.objects.filter(
                faro_asociado=centro, activo=True
            ).order_by("nombre")
        else:
            qs_adheridos = Centro.objects.none()

        context["centros_adheridos_total"] = qs_adheridos.count()
        pag_centros = Paginator(qs_adheridos, 5)
        page = self.request.GET.get("page")
        context["centros_adheridos_paginados"] = pag_centros.get_page(page)

        #
        # 4) Métricas y asistentes (sin cambios)
        #
        total_part = sum(mapa.values())
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
            # fijamos tipo y faro_asociado iniciales
            initial["tipo"] = "adherido"
            initial["faro_asociado"] = faro_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # avisamos al form si venimos con faro=
        kwargs["from_faro"] = bool(self.request.GET.get("faro"))
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        # Si se creó con faro=, garantizamos referinte + tipo
        if form.cleaned_data.get("tipo") == "adherido":
            # opcional: asignar el faro como self.object.faro_asociado
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
