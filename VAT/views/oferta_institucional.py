import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from VAT.models import (
    Centro,
    OfertaInstitucional,
    Comision,
    ComisionHorario,
    Inscripcion,
    SesionComision,
    AsistenciaSesion,
    InstitucionUbicacion,
)
from VAT.forms import (
    OfertaInstitucionalForm,
    ComisionForm,
    ComisionHorarioForm,
    CiudadanoInscripcionRapidaForm,
)
from VAT.services.access_scope import (
    filter_centros_queryset_for_user,
    filter_comisiones_queryset_for_user,
    filter_ofertas_queryset_for_user,
    filter_sesiones_queryset_for_user,
)

logger = logging.getLogger("django")


# ============================================================================
# OFERTA INSTITUCIONAL VIEWS
# ============================================================================


class OfertaInstitucionalListView(LoginRequiredMixin, ListView):
    model = OfertaInstitucional
    template_name = "vat/oferta_institucional/oferta_list.html"
    context_object_name = "ofertas"
    paginate_by = 20

    def get_queryset(self):
        queryset = OfertaInstitucional.objects.select_related(
            "centro", "plan_curricular", "programa"
        ).order_by("-ciclo_lectivo")
        queryset = filter_ofertas_queryset_for_user(queryset, self.request.user)

        centro_id = self.request.GET.get("centro_id")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if buscar:
            queryset = queryset.filter(
                Q(centro__nombre__icontains=buscar)
                | Q(plan_curricular__titulos__nombre__icontains=buscar)
                | Q(nombre_local__icontains=buscar)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_choices"] = OfertaInstitucional.ESTADO_OFERTA_CHOICES
        return context


class OfertaInstitucionalCreateView(LoginRequiredMixin, CreateView):
    model = OfertaInstitucional
    form_class = OfertaInstitucionalForm
    template_name = "vat/oferta_institucional/oferta_form.html"
    success_url = reverse_lazy("vat_oferta_institucional_list")

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.request.GET.get("centro")
        if (
            centro_id
            and filter_centros_queryset_for_user(
                Centro.objects.filter(pk=centro_id), self.request.user
            ).exists()
        ):
            initial["centro"] = centro_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["centro"].queryset = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        ).order_by("nombre")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Oferta institucional creada exitosamente.")
        return super().form_valid(form)


class OfertaInstitucionalDetailView(LoginRequiredMixin, DetailView):
    model = OfertaInstitucional
    template_name = "vat/oferta_institucional/oferta_detail.html"
    context_object_name = "oferta"

    def get_queryset(self):
        queryset = OfertaInstitucional.objects.select_related(
            "centro", "plan_curricular", "programa"
        )
        return filter_ofertas_queryset_for_user(queryset, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # self.object ya está cargado por DetailView, no genera query extra
        comisiones = list(self.object.comisiones.prefetch_related("horarios"))
        context["comisiones"] = comisiones
        context["total_comisiones"] = len(comisiones)
        return context


class OfertaInstitucionalUpdateView(LoginRequiredMixin, UpdateView):
    model = OfertaInstitucional
    form_class = OfertaInstitucionalForm
    template_name = "vat/oferta_institucional/oferta_form.html"
    success_url = reverse_lazy("vat_oferta_institucional_list")

    def get_queryset(self):
        queryset = OfertaInstitucional.objects.select_related(
            "centro", "plan_curricular", "programa"
        )
        return filter_ofertas_queryset_for_user(queryset, self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["centro"].queryset = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        ).order_by("nombre")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Oferta institucional actualizada exitosamente.")
        return super().form_valid(form)


class OfertaInstitucionalDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = OfertaInstitucional
    template_name = "vat/oferta_institucional/oferta_confirm_delete.html"
    context_object_name = "oferta"

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse_lazy("vat_oferta_institucional_list")

    def get_queryset(self):
        queryset = OfertaInstitucional.objects.select_related("centro")
        return filter_ofertas_queryset_for_user(queryset, self.request.user)


# ============================================================================
# COMISIÓN VIEWS
# ============================================================================


class ComisionListView(LoginRequiredMixin, ListView):
    model = Comision
    template_name = "vat/oferta_institucional/comision_list.html"
    context_object_name = "comisiones"
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Comision.objects.select_related("oferta")
            .prefetch_related("horarios")
            .order_by("codigo_comision")
        )
        queryset = filter_comisiones_queryset_for_user(queryset, self.request.user)

        oferta_id = self.request.GET.get("oferta_id")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if oferta_id:
            queryset = queryset.filter(oferta_id=oferta_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if buscar:
            queryset = queryset.filter(
                Q(codigo_comision__icontains=buscar)
                | Q(nombre__icontains=buscar)
                | Q(oferta__nombre__icontains=buscar)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_choices"] = Comision.ESTADO_COMISION_CHOICES
        return context


class ComisionCreateView(LoginRequiredMixin, CreateView):
    model = Comision
    form_class = ComisionForm
    template_name = "vat/oferta_institucional/comision_form.html"

    def get_initial(self):
        initial = super().get_initial()
        oferta_id = self.request.GET.get("oferta")
        if (
            oferta_id
            and filter_ofertas_queryset_for_user(
                OfertaInstitucional.objects.filter(pk=oferta_id), self.request.user
            ).exists()
        ):
            initial["oferta"] = oferta_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_ofertas = filter_ofertas_queryset_for_user(
            OfertaInstitucional.objects.select_related("centro"), self.request.user
        ).order_by("-ciclo_lectivo")
        scoped_centros_ids = scoped_ofertas.values_list(
            "centro_id", flat=True
        ).distinct()
        form.fields["oferta"].queryset = scoped_ofertas
        form.fields["ubicacion"].queryset = InstitucionUbicacion.objects.filter(
            centro_id__in=scoped_centros_ids
        ).select_related("localidad")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Comisión creada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("vat_comision_detail", kwargs={"pk": self.object.pk})


class ComisionDetailView(LoginRequiredMixin, DetailView):
    model = Comision
    template_name = "vat/oferta_institucional/comision_detail.html"
    context_object_name = "comision"

    def get_queryset(self):
        queryset = Comision.objects.select_related(
            "oferta__centro", "oferta__plan_curricular"
        )
        return filter_comisiones_queryset_for_user(queryset, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comision = self.object
        context["comision_tipo_titulo"] = "Comisión"
        context["comision_back_url"] = reverse(
            "vat_centro_detail", kwargs={"pk": comision.oferta.centro_id}
        )
        context["comision_edit_url"] = reverse(
            "vat_comision_update", kwargs={"pk": comision.pk}
        )
        context["comision_delete_url"] = reverse(
            "vat_comision_delete", kwargs={"pk": comision.pk}
        )
        context["puede_editar_comision"] = self.request.user.has_perm(
            "VAT.change_comision"
        )
        context["puede_eliminar_comision"] = self.request.user.has_perm(
            "VAT.delete_comision"
        )
        context["comision_subtitle"] = str(comision.oferta)
        context["unidad_label"] = "Oferta"
        context["unidad_valor"] = str(comision.oferta)
        context["unidad_sidebar_title"] = "Oferta asociada"
        context["unidad_detail_url"] = reverse(
            "vat_oferta_institucional_detail", kwargs={"pk": comision.oferta_id}
        )
        context["unidad_detail_text"] = "Ver oferta"
        context["inscripcion_estado_url_name"] = "vat_inscripcion_cambiar_estado"
        context["asistencia_url_name"] = "vat_asistencia_sesion"
        context["horario_create_url_name"] = "vat_comision_horario_create"
        context["horario_create_query_param"] = "comision"
        context["horario_update_url_name"] = "vat_comision_horario_update"
        context["horario_delete_url_name"] = "vat_comision_horario_delete"
        context["inscripcion_rapida_url_name"] = "vat_inscripcion_rapida_comision"
        horario_form = ComisionHorarioForm(initial={"comision": comision.id})
        horario_form.fields["comision"].queryset = Comision.objects.filter(
            pk=comision.pk
        )
        context["horario_form"] = horario_form
        context["ciudadano_rapido_form"] = CiudadanoInscripcionRapidaForm(
            initial={"documento": "", "tipo_documento": "DNI"}
        )
        context["horarios"] = list(
            ComisionHorario.objects.filter(comision=comision).select_related(
                "dia_semana"
            )
        )
        context["sesiones"] = list(
            SesionComision.objects.filter(comision=comision)
            .select_related("horario__dia_semana")
            .order_by("fecha", "horario__hora_desde")
        )
        context["inscripciones"] = list(
            Inscripcion.objects.filter(comision=comision)
            .select_related("ciudadano", "programa")
            .order_by("estado", "fecha_inscripcion")
        )
        context["estado_choices"] = Inscripcion.ESTADO_INSCRIPCION_CHOICES
        return context


class InscripcionCambiarEstadoView(LoginRequiredMixin, View):
    """Cambia el estado de una Inscripcion. POST: {estado: <nuevo_estado>}."""

    def post(self, request, pk):
        scoped_inscripciones = filter_comisiones_queryset_for_user(
            Comision.objects.all(), request.user
        ).values_list("id", flat=True)
        inscripcion = get_object_or_404(
            Inscripcion,
            pk=pk,
            comision_id__in=scoped_inscripciones,
        )
        nuevo_estado = request.POST.get("estado")
        estados_validos = dict(Inscripcion.ESTADO_INSCRIPCION_CHOICES)
        if nuevo_estado not in estados_validos:
            messages.error(request, "Estado no válido.")
        else:
            inscripcion.estado = nuevo_estado
            update_fields = ["estado"]
            if nuevo_estado == "validada_presencial":
                inscripcion.fecha_validacion_presencial = timezone.now()
                update_fields.append("fecha_validacion_presencial")
            inscripcion.save(update_fields=update_fields)
            messages.success(
                request,
                f"Inscripción de {inscripcion.ciudadano.nombre_completo} "
                f"actualizada a '{estados_validos[nuevo_estado]}'.",
            )
        return redirect("vat_comision_detail", pk=inscripcion.comision_id)


class AsistenciaSesionView(LoginRequiredMixin, TemplateView):
    """
    GET: muestra tabla de inscriptos aceptados para tomar asistencia en una sesión.
    POST: guarda/actualiza los registros de AsistenciaSesion.
    """

    template_name = "vat/oferta_institucional/asistencia_sesion.html"

    def get_sesion(self, sesion_pk):
        scoped_qs = filter_sesiones_queryset_for_user(
            SesionComision.objects.select_related(
                "comision__oferta__centro",
                "horario__dia_semana",
            ),
            self.request.user,
        )
        return get_object_or_404(scoped_qs, pk=sesion_pk)

    def _inscripciones_activas(self, comision):
        return list(
            Inscripcion.objects.filter(
                comision=comision,
                estado__in=["inscripta", "validada_presencial"],
            ).select_related("ciudadano")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sesion = self.get_sesion(self.kwargs["sesion_pk"])
        inscripciones = self._inscripciones_activas(sesion.comision)
        asistencias_existentes = {
            a.inscripcion_id: a
            for a in AsistenciaSesion.objects.filter(
                sesion=sesion,
                inscripcion__in=[i.pk for i in inscripciones],
            )
        }
        filas = []
        for insc in inscripciones:
            asist = asistencias_existentes.get(insc.pk)
            filas.append(
                {
                    "inscripcion": insc,
                    "presente": asist.presente if asist else None,
                    "observaciones": asist.observaciones if asist else "",
                }
            )
        context["sesion"] = sesion
        context["filas"] = filas
        context["ya_tomada"] = bool(asistencias_existentes)
        context["comision_detail_url"] = reverse(
            "vat_comision_detail", kwargs={"pk": sesion.comision_id}
        )
        context["comision_label"] = str(sesion.comision)
        return context

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        sesion = self.get_sesion(self.kwargs["sesion_pk"])
        inscripciones = self._inscripciones_activas(sesion.comision)
        for insc in inscripciones:
            presente = request.POST.get(f"presente_{insc.pk}") == "1"
            obs = request.POST.get(f"obs_{insc.pk}", "").strip()
            AsistenciaSesion.objects.update_or_create(
                sesion=sesion,
                inscripcion=insc,
                defaults={
                    "presente": presente,
                    "observaciones": obs or None,
                    "registrado_por": request.user,
                },
            )
        # Marcar sesión como realizada si estaba programada
        if sesion.estado == "programada":
            sesion.estado = "realizada"
            sesion.save(update_fields=["estado"])
        messages.success(request, "Asistencia registrada exitosamente.")
        return redirect("vat_comision_detail", pk=sesion.comision_id)


class ComisionUpdateView(LoginRequiredMixin, UpdateView):
    model = Comision
    form_class = ComisionForm
    template_name = "vat/oferta_institucional/comision_form.html"
    success_url = reverse_lazy("vat_comision_list")

    def get_queryset(self):
        queryset = Comision.objects.select_related("oferta__centro")
        return filter_comisiones_queryset_for_user(queryset, self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_ofertas = filter_ofertas_queryset_for_user(
            OfertaInstitucional.objects.select_related("centro"), self.request.user
        ).order_by("-ciclo_lectivo")
        scoped_centros_ids = scoped_ofertas.values_list(
            "centro_id", flat=True
        ).distinct()
        form.fields["oferta"].queryset = scoped_ofertas
        form.fields["ubicacion"].queryset = InstitucionUbicacion.objects.filter(
            centro_id__in=scoped_centros_ids
        ).select_related("localidad")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Comisión actualizada exitosamente.")
        return super().form_valid(form)


class ComisionDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Comision
    template_name = "vat/oferta_institucional/comision_confirm_delete.html"
    context_object_name = "comision"

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse_lazy("vat_comision_list")

    def get_queryset(self):
        queryset = Comision.objects.select_related("oferta__centro")
        return filter_comisiones_queryset_for_user(queryset, self.request.user)


# ============================================================================
# COMISIÓN HORARIO VIEWS
# ============================================================================


class ComisionHorarioListView(LoginRequiredMixin, ListView):
    model = ComisionHorario
    template_name = "vat/oferta_institucional/horario_list.html"
    context_object_name = "horarios"
    paginate_by = 20

    def get_queryset(self):
        queryset = ComisionHorario.objects.select_related(
            "comision", "dia_semana"
        ).order_by("comision", "dia_semana", "hora_desde")
        queryset = queryset.filter(
            comision_id__in=filter_comisiones_queryset_for_user(
                Comision.objects.all(), self.request.user
            ).values("id")
        )

        comision_id = self.request.GET.get("comision_id")
        dia = self.request.GET.get("dia_semana")

        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if dia:
            queryset = queryset.filter(dia_semana_id=dia)

        return queryset


class ComisionHorarioCreateView(LoginRequiredMixin, CreateView):
    model = ComisionHorario
    form_class = ComisionHorarioForm
    template_name = "vat/oferta_institucional/horario_form.html"

    def get_initial(self):
        initial = super().get_initial()
        comision_id = self.request.GET.get("comision")
        if (
            comision_id
            and filter_comisiones_queryset_for_user(
                Comision.objects.filter(pk=comision_id), self.request.user
            ).exists()
        ):
            initial["comision"] = comision_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["comision"].queryset = filter_comisiones_queryset_for_user(
            Comision.objects.select_related("oferta__centro"), self.request.user
        ).order_by("codigo_comision")
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        from VAT.services.sesion_comision_service.impl import SesionComisionService

        cantidad = SesionComisionService.generar_para_horario(self.object)
        if cantidad:
            messages.success(
                self.request, f"Horario creado. Se generaron {cantidad} sesiones."
            )
        else:
            messages.success(self.request, "Horario creado exitosamente.")
        return response

    def get_success_url(self):
        return reverse("vat_comision_detail", kwargs={"pk": self.object.comision_id})


class ComisionHorarioDetailView(LoginRequiredMixin, DetailView):
    model = ComisionHorario
    template_name = "vat/oferta_institucional/horario_detail.html"
    context_object_name = "horario"

    def get_queryset(self):
        scoped_comisiones = filter_comisiones_queryset_for_user(
            Comision.objects.all(), self.request.user
        )
        return ComisionHorario.objects.select_related("comision", "dia_semana").filter(
            comision_id__in=scoped_comisiones.values("id")
        )


class ComisionHorarioUpdateView(LoginRequiredMixin, UpdateView):
    model = ComisionHorario
    form_class = ComisionHorarioForm
    template_name = "vat/oferta_institucional/horario_form.html"

    def get_queryset(self):
        scoped_comisiones = filter_comisiones_queryset_for_user(
            Comision.objects.all(), self.request.user
        )
        return ComisionHorario.objects.select_related("comision", "dia_semana").filter(
            comision_id__in=scoped_comisiones.values("id")
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["comision"].queryset = filter_comisiones_queryset_for_user(
            Comision.objects.select_related("oferta__centro"), self.request.user
        ).order_by("codigo_comision")
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        from VAT.services.sesion_comision_service.impl import SesionComisionService

        cantidad = SesionComisionService.regenerar_para_horario(self.object)
        messages.success(
            self.request, f"Horario actualizado. {cantidad} sesiones regeneradas."
        )
        return response

    def get_success_url(self):
        return reverse("vat_comision_detail", kwargs={"pk": self.object.comision_id})


class ComisionHorarioDeleteView(LoginRequiredMixin, DeleteView):
    model = ComisionHorario
    template_name = "vat/oferta_institucional/horario_confirm_delete.html"
    context_object_name = "horario"

    def get_queryset(self):
        scoped_comisiones = filter_comisiones_queryset_for_user(
            Comision.objects.all(), self.request.user
        )
        return ComisionHorario.objects.select_related("comision", "dia_semana").filter(
            comision_id__in=scoped_comisiones.values("id")
        )

    def form_valid(self, form):
        from VAT.services.sesion_comision_service.impl import SesionComisionService

        SesionComisionService.eliminar_para_horario(self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("vat_comision_detail", kwargs={"pk": self.object.comision_id})
