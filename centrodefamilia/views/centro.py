# centrodefamilia/views/centro.py
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
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.html import format_html

from centrodefamilia.models import (
    CabalArchivo,
    Categoria,
    Centro,
    ActividadCentro,
    InformeCabalRegistro,
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

        if user.is_superuser:
            pass
        elif user.groups.filter(name="CDF SSE").exists():
            pass
        elif user.groups.filter(name="ReferenteCentro").exists():
            qs = qs.filter(referente=user)
        else:
            return Centro.objects.none()

        busq = self.request.GET.get("busqueda", "").strip()
        if busq:
            qs = qs.filter(Q(nombre__icontains=busq) | Q(tipo__icontains=busq))

        return qs.order_by("nombre")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        can_add = user.is_superuser or user.groups.filter(name="CDF SSE").exists()
        ctx["can_add"] = can_add

        # Datos para componentes
        action_buttons = []
        if can_add:
            action_buttons.extend(
                [
                    {
                        "url": reverse("centro_create"),
                        "text": "Agregar",
                        "type": "primary btn-lg",
                        "class": "d-block d-sm-inline mt-2",
                    },
                    {
                        "url": reverse("actividad_create_sola"),
                        "text": "Agregar Actividad",
                        "type": "primary btn-lg",
                        "class": "d-block d-sm-inline mt-2",
                    },
                ]
            )

        ctx.update(
            {
                # Breadcrumb
                "breadcrumb_items": [
                    {"text": "Centro de Familia", "url": reverse("centro_list")},
                    {"text": "Listar", "active": True},
                ],
                # Search bar
                "reset_url": reverse("centro_list"),
                # Action buttons
                "action_buttons": action_buttons,
                # Table headers
                "table_headers": [
                    {"title": "Nombre"},
                    {"title": "Tipo"},
                    {"title": "Dirección"},
                    {"title": "Teléfono / Celular"},
                    {"title": "Estado"},
                    {"title": "Acciones", "class": "notexport", "style": "width: 15%"},
                ],
            }
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
        if not (es_ref or es_adherido or user.is_superuser or es_cdf_sse):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        centro = self.object

        # Breadcrumb data
        ctx["breadcrumb_items"] = [
            {"text": "Centro de Familia", "url": reverse("centro_list")},
            {"text": centro.nombre, "active": True},
        ]

        # Action buttons
        action_buttons = [
            {
                "url": reverse("centro_update", args=[centro.id]),
                "text": "Editar",
                "type": "outline-primary",
                "size": "sm",
            },
            {
                "url": reverse("centro_list"),
                "text": "Volver",
                "type": "outline-secondary",
                "size": "sm",
            },
            {
                "url": reverse(
                    "actividadcentro_create", kwargs={"centro_id": centro.id}
                ),
                "text": "Agregar Actividad",
                "type": "outline-success",
                "size": "sm",
            },
        ]
        if centro.tipo == "faro":
            action_buttons.append(
                {
                    "url": f"{reverse('centro_create')}?faro={centro.id}",
                    "text": "Agregar Centro Adherido",
                    "type": "outline-info",
                    "size": "sm",
                }
            )
        ctx["action_buttons"] = action_buttons

        # 1) Expedientes
        qs_exp = Expediente.objects.filter(centro=centro).order_by("-fecha_subida")
        ctx["expedientes_cabal"] = Paginator(qs_exp, 3).get_page(
            self.request.GET.get("page_exp")
        )

        # 2) Actividades en curso
        search_curso = (
            self.request.GET.get("search_actividades_curso", "").strip().lower()
        )
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
        if search_curso:
            qs_acts = qs_acts.filter(
                Q(actividad__nombre__icontains=search_curso)
                | Q(actividad__categoria__nombre__icontains=search_curso)
                | Q(estado__icontains=search_curso)
            )
        ctx["actividades"] = list(qs_acts)
        ctx["total_actividades"] = qs_acts.count()
        ctx["total_recaudado"] = sum((act.ganancia or 0) for act in ctx["actividades"])

        # 3) Actividades de otros centros
        search_otras = self.request.GET.get("search_actividades", "").strip().lower()
        otras = (
            ActividadCentro.objects.exclude(centro=centro)
            .select_related("actividad", "actividad__categoria", "centro")
            .order_by("-id")
        )  # Add ordering to prevent UnorderedObjectListWarning
        if search_otras:
            otras = otras.filter(
                Q(actividad__nombre__icontains=search_otras)
                | Q(actividad__categoria__nombre__icontains=search_otras)
                | Q(estado__icontains=search_otras)
                | Q(centro__nombre__icontains=search_otras)
            )
        ctx["actividades_paginados"] = Paginator(otras, 5).get_page(
            self.request.GET.get("page_act")
        )

        # 4) Centros adheridos
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

        total_part = sum(a.inscritos for a in qs_acts)
        qs_inscritos = ParticipanteActividad.objects.filter(
            estado="inscrito", actividad_centro__centro=centro
        )
        hombres = qs_inscritos.filter(ciudadano__sexo__sexo__iexact="Masculino").count()
        mujeres = qs_inscritos.filter(ciudadano__sexo__sexo__iexact="Femenino").count()
        mixtas = total_part - hombres - mujeres
        espera = ParticipanteActividad.objects.filter(
            estado="lista_espera", actividad_centro__centro=centro
        ).count()

        ctx["metricas"] = {
            "centros_faro": ctx["centros_adheridos_total"],
            "categorias": Categoria.objects.count(),
            "actividades": ctx["total_actividades"],
            "interacciones": total_part,
            "inscriptos": qs_inscritos.count(),
            "hombres": hombres,
            "mujeres": mujeres,
            "mixtas": mixtas,
        }
        ctx["asistentes"] = {
            "total": total_part,
            "hombres": hombres,
            "mujeres": mujeres,
            "espera": espera,
        }

        # 6) Archivos CABAL vinculados al centro
        ctx["archivos_cabal_centro"] = (
            CabalArchivo.objects.filter(registros__centro=centro)
            .distinct()
            .order_by("-fecha_subida")
        )

        return ctx


class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centro_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "breadcrumb_items": [
                    {"text": "Centro de Familia", "url": reverse("centro_list")},
                    {"text": "Nuevo", "active": True},
                ],
                "page_title": "Nuevo Centro",
                "cancel_url": reverse("centro_list"),
                "submit_text": "Guardar",
            }
        )
        return ctx

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
        messages.success(self.request, "Centro creado exitosamente.")
        return super().form_valid(form)


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "breadcrumb_items": [
                    {"text": "Centro de Familia", "url": reverse("centro_list")},
                    {
                        "text": self.object.nombre,
                        "url": reverse("centro_detail", args=[self.object.pk]),
                    },
                    {"text": "Editar", "active": True},
                ],
                "page_title": f"Editar Centro: {self.object.nombre}",
                "cancel_url": reverse("centro_detail", args=[self.object.pk]),
                "submit_text": "Actualizar",
            }
        )
        return ctx

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
    template_name = "centros/centro_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        centro = self.object
        ctx.update(
            {
                "breadcrumb_items": [
                    {"text": "Centro de Familia", "url": reverse("centro_list")},
                    {
                        "text": centro.nombre,
                        "url": reverse("centro_detail", args=[centro.pk]),
                    },
                    {"text": "Eliminar", "active": True},
                ],
                "object_title": centro.nombre,
                "delete_message": format_html(
                    "¿Estás seguro que querés eliminar este centro?"
                    " <br><strong>Nombre:</strong> {}"
                    " <br><strong>Dirección:</strong> {}"
                    " <br><strong>Tipo:</strong> {}",
                    centro.nombre,
                    centro.calle,
                    centro.get_tipo_display(),
                ),
                "cancel_url": reverse("centro_list"),
            }
        )
        return ctx

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user
        if not (centro.referente_id == user.id or user.is_superuser):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Centro eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


class InformeCabalArchivoPorCentroDetailView(LoginRequiredMixin, DetailView):
    model = CabalArchivo
    template_name = "informecabal/archivo_por_centro.html"
    context_object_name = "archivo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro_id_raw = self.kwargs.get("centro_id")

        try:
            centro_id = int(centro_id_raw)
        except (TypeError, ValueError):
            raise Http404("Parámetro 'centro_id' inválido.")

        centro = get_object_or_404(Centro, id=centro_id)

        registros_qs = (
            InformeCabalRegistro.objects.filter(
                archivo=self.object, centro_id=centro_id
            )
            .only(
                "id",
                "nro_comercio",
                "razon_social",
                "importe",
                "fecha_trx",
                "moneda_origen",
                "importe_pesos",
                "motivo_rechazo",
                "desc_motivo_rechazo",
                "no_coincidente",
                "fila_numero",
                "centro_id",
            )
            .order_by("fila_numero")
        )

        paginator = Paginator(registros_qs, 50)
        page_param = self.request.GET.get("page") or 1
        try:
            page_obj = paginator.get_page(page_param)
        except Exception:
            page_obj = paginator.get_page(1)

        context["registros"] = page_obj
        context["centro"] = centro
        return context
