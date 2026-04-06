from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse
from django.views import View
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    TemplateView,
)

from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from VAT.forms import (
    CursoForm,
    ComisionCursoForm,
    ComisionCursoHorarioForm,
    CiudadanoInscripcionRapidaForm,
)
from VAT.models import (
    Centro,
    Curso,
    ComisionCurso,
    ComisionHorario,
    SesionComision,
    Inscripcion,
    AsistenciaSesion,
    InstitucionUbicacion,
)
from VAT.services.access_scope import (
    can_user_access_centro,
    filter_centros_queryset_for_user,
)
from VAT.services.inscripcion_service import InscripcionService
from VAT.services.sesion_comision_service.impl import SesionComisionService


def _scoped_centros_ids(user):
    return filter_centros_queryset_for_user(Centro.objects.all(), user).values_list(
        "id", flat=True
    )


def _scoped_comisiones_curso_queryset(user):
    return ComisionCurso.objects.select_related(
        "curso__centro",
        "curso__modalidad",
        "curso__plan_estudio",
        "ubicacion__localidad",
    ).filter(curso__centro_id__in=_scoped_centros_ids(user))


class CursoCreateView(LoginRequiredMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = "vat/curso/curso_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro_id = request.GET.get("centro") or request.POST.get("centro")
        if not centro_id:
            raise PermissionDenied

        try:
            centro = Centro.objects.get(pk=centro_id)
        except Centro.DoesNotExist as exc:
            raise PermissionDenied from exc

        if not can_user_access_centro(request.user, centro):
            raise PermissionDenied

        self.centro = centro
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["centro"] = self.centro.id
        return initial

    def form_valid(self, form):
        form.instance.centro = self.centro
        messages.success(self.request, "Curso creado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_embedded"] = self.request.GET.get("modal") == "1"
        context["base_template"] = (
            "vat/curso/curso_embedded_base.html"
            if context["is_embedded"]
            else "includes/main.html"
        )
        context["cancel_url"] = (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.centro.id})}#cursos"
        )
        return context

    def get_success_url(self):
        return f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"


class CursoUpdateView(LoginRequiredMixin, UpdateView):
    model = Curso
    form_class = CursoForm
    template_name = "vat/curso/curso_form.html"

    def get_queryset(self):
        scoped_centros = _scoped_centros_ids(self.request.user)
        return Curso.objects.select_related("centro").filter(
            centro_id__in=scoped_centros
        )

    def form_valid(self, form):
        messages.success(self.request, "Curso actualizado exitosamente.")
        if self.request.GET.get("modal") == "1":
            self.object = form.save()
            return HttpResponse(
                "<script>"
                "if (window.parent && window.parent !== window) {"
                "window.parent.location.reload();"
                "} else {"
                f"window.location.href = '{self.get_success_url()}';"
                "}"
                "</script>"
            )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_embedded"] = self.request.GET.get("modal") == "1"
        context["base_template"] = (
            "vat/curso/curso_embedded_base.html"
            if context["is_embedded"]
            else "includes/main.html"
        )
        context["cancel_url"] = (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"
        )
        return context

    def get_success_url(self):
        return f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"


class CursoDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Curso
    template_name = "vat/curso/curso_confirm_delete.html"
    context_object_name = "curso"

    def get_queryset(self):
        scoped_centros = _scoped_centros_ids(self.request.user)
        return Curso.objects.select_related("centro").filter(
            centro_id__in=scoped_centros
        )

    def get_success_url(self):
        return f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"


class ComisionCursoCreateView(LoginRequiredMixin, CreateView):
    model = ComisionCurso
    form_class = ComisionCursoForm
    template_name = "vat/curso/comision_curso_form.html"

    def dispatch(self, request, *args, **kwargs):
        curso_id = request.GET.get("curso") or request.POST.get("curso")
        if curso_id:
            try:
                curso = Curso.objects.select_related("centro").get(pk=curso_id)
            except Curso.DoesNotExist as exc:
                raise PermissionDenied from exc
            if not can_user_access_centro(request.user, curso.centro):
                raise PermissionDenied
            self.curso = curso
        else:
            self.curso = None
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.curso:
            initial["curso"] = self.curso.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        )
        form.fields["curso"].queryset = Curso.objects.filter(
            centro_id__in=scoped_centros.values_list("id", flat=True)
        ).select_related("centro")
        ubicaciones_qs = InstitucionUbicacion.objects.filter(
            centro_id__in=scoped_centros.values_list("id", flat=True)
        ).select_related("localidad")
        if self.curso:
            ubicaciones_qs = ubicaciones_qs.filter(centro_id=self.curso.centro_id)
        form.fields["ubicacion"].queryset = ubicaciones_qs
        return form

    def form_valid(self, form):
        messages.success(self.request, "Comisión del curso creada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.curso.centro_id})}"
            "#cursos"
        )


class ComisionCursoDetailView(LoginRequiredMixin, DetailView):
    model = ComisionCurso
    template_name = "vat/oferta_institucional/comision_detail.html"
    context_object_name = "comision"

    def get_queryset(self):
        return _scoped_comisiones_curso_queryset(self.request.user).prefetch_related(
            "curso__voucher_parametrias"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comision = self.object
        cancel_url = (
            f"{reverse('vat_centro_detail', kwargs={'pk': comision.curso.centro_id})}"
            "#cursos"
        )
        horario_form = ComisionCursoHorarioForm(initial={"comision_curso": comision.id})
        horario_form.fields["comision_curso"].queryset = ComisionCurso.objects.filter(
            pk=comision.pk
        )
        context.update(
            {
                "comision_curso": comision,
                "cancel_url": cancel_url,
                "horario_form": horario_form,
                "ciudadano_rapido_form": CiudadanoInscripcionRapidaForm(
                    initial={"documento": "", "tipo_documento": "DNI"}
                ),
                "horarios": list(
                    ComisionHorario.objects.filter(
                        comision_curso=comision
                    ).select_related("dia_semana")
                ),
                "sesiones": list(
                    SesionComision.objects.filter(comision_curso=comision)
                    .select_related("horario__dia_semana")
                    .order_by("fecha", "horario__hora_desde")
                ),
                "inscripciones": list(
                    Inscripcion.objects.filter(comision_curso=comision)
                    .select_related("ciudadano", "programa")
                    .order_by("estado", "fecha_inscripcion")
                ),
                "estado_choices": Inscripcion.ESTADO_INSCRIPCION_CHOICES,
                "comision_tipo_titulo": "Comisión de Curso",
                "comision_back_url": cancel_url,
                "comision_subtitle": comision.curso.nombre,
                "comision_edit_url": reverse(
                    "vat_comision_curso_update", kwargs={"pk": comision.pk}
                ),
                "comision_delete_url": reverse(
                    "vat_comision_curso_delete", kwargs={"pk": comision.pk}
                ),
                "puede_editar_comision": self.request.user.has_perm(
                    "VAT.change_comisioncurso"
                ),
                "puede_eliminar_comision": self.request.user.has_perm(
                    "VAT.delete_comisioncurso"
                ),
                "unidad_label": "Curso",
                "unidad_valor": comision.curso.nombre,
                "unidad_sidebar_title": "Curso asociado",
                "unidad_detail_url": cancel_url,
                "unidad_detail_text": "Ver centro",
                "inscripcion_estado_url_name": "vat_inscripcion_curso_cambiar_estado",
                "asistencia_url_name": "vat_asistencia_sesion_curso",
                "horario_create_url_name": "vat_comision_curso_horario_create",
                "horario_create_query_param": "comision_curso",
                "horario_update_url_name": "vat_comision_curso_horario_update",
                "horario_delete_url_name": "vat_comision_curso_horario_delete",
                "inscripcion_rapida_url_name": "vat_inscripcion_rapida_comision_curso",
            }
        )
        return context


class InscripcionCursoCambiarEstadoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        inscripcion = get_object_or_404(
            Inscripcion.objects.select_related("comision_curso__curso__centro"),
            pk=pk,
            comision_curso__curso__centro_id__in=_scoped_centros_ids(request.user),
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
        return redirect("vat_comision_curso_detail", pk=inscripcion.comision_curso_id)


class InscripcionRapidaComisionCursoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        comision = get_object_or_404(
            _scoped_comisiones_curso_queryset(request.user),
            pk=request.POST.get("comision"),
        )
        if not comision.curso.programa_id:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "El curso debe tener un programa configurado para inscribir ciudadanos.",
                },
                status=400,
            )

        ciudadano_id = (request.POST.get("ciudadano_id") or "").strip()
        observaciones = (request.POST.get("observaciones") or "").strip()
        ciudadano_form = None

        if ciudadano_id:
            from ciudadanos.models import Ciudadano

            ciudadano = get_object_or_404(Ciudadano, pk=ciudadano_id)
        else:
            ciudadano_form = CiudadanoInscripcionRapidaForm(request.POST)
            if not ciudadano_form.is_valid():
                return JsonResponse(
                    {
                        "ok": False,
                        "message": "Errores en el formulario de ciudadano.",
                        "errors": ciudadano_form.errors,
                    },
                    status=400,
                )
            ciudadano = ciudadano_form.save(commit=False)
            ciudadano.creado_por = request.user
            ciudadano.modificado_por = request.user
            ciudadano.origen_dato = "manual"

        try:
            with transaction.atomic():
                if ciudadano_form is not None:
                    ciudadano.save()
                inscripcion = InscripcionService.crear_inscripcion(
                    ciudadano=ciudadano,
                    comision=comision,
                    programa=comision.curso.programa,
                    estado="inscripta",
                    origen_canal="backoffice",
                    observaciones=observaciones,
                    usuario=request.user,
                )
        except ValueError as exc:
            return JsonResponse({"ok": False, "message": str(exc)}, status=400)

        return JsonResponse(
            {
                "ok": True,
                "message": f"Inscripción creada para {inscripcion.ciudadano.nombre_completo}.",
                "inscripcion_id": inscripcion.pk,
            }
        )


class AsistenciaSesionCursoView(LoginRequiredMixin, TemplateView):
    template_name = "vat/oferta_institucional/asistencia_sesion.html"

    def get_sesion(self, sesion_pk):
        return get_object_or_404(
            SesionComision.objects.select_related(
                "comision_curso__curso__centro",
                "horario__dia_semana",
            ).filter(
                comision_curso__curso__centro_id__in=_scoped_centros_ids(
                    self.request.user
                )
            ),
            pk=sesion_pk,
        )

    def _inscripciones_activas(self, comision):
        return list(
            Inscripcion.objects.filter(
                comision_curso=comision,
                estado__in=["inscripta", "validada_presencial"],
            ).select_related("ciudadano")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sesion = self.get_sesion(self.kwargs["sesion_pk"])
        inscripciones = self._inscripciones_activas(sesion.comision_curso)
        asistencias_existentes = {
            a.inscripcion_id: a
            for a in AsistenciaSesion.objects.filter(
                sesion=sesion,
                inscripcion__in=[i.pk for i in inscripciones],
            )
        }
        filas = []
        for inscripcion in inscripciones:
            asistencia = asistencias_existentes.get(inscripcion.pk)
            filas.append(
                {
                    "inscripcion": inscripcion,
                    "presente": asistencia.presente if asistencia else None,
                    "observaciones": asistencia.observaciones if asistencia else "",
                }
            )
        context["sesion"] = sesion
        context["filas"] = filas
        context["ya_tomada"] = bool(asistencias_existentes)
        context["comision_detail_url"] = reverse(
            "vat_comision_curso_detail", kwargs={"pk": sesion.comision_curso_id}
        )
        context["comision_label"] = str(sesion.entidad_comision)
        return context

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        sesion = self.get_sesion(self.kwargs["sesion_pk"])
        inscripciones = self._inscripciones_activas(sesion.comision_curso)
        for inscripcion in inscripciones:
            presente = request.POST.get(f"presente_{inscripcion.pk}") == "1"
            observaciones = request.POST.get(f"obs_{inscripcion.pk}", "").strip()
            AsistenciaSesion.objects.update_or_create(
                sesion=sesion,
                inscripcion=inscripcion,
                defaults={
                    "presente": presente,
                    "observaciones": observaciones or None,
                    "registrado_por": request.user,
                },
            )
        if sesion.estado == "programada":
            sesion.estado = "realizada"
            sesion.save(update_fields=["estado"])
        messages.success(request, "Asistencia registrada exitosamente.")
        return redirect("vat_comision_curso_detail", pk=sesion.comision_curso_id)


class ComisionCursoHorarioCreateView(LoginRequiredMixin, CreateView):
    model = ComisionHorario
    form_class = ComisionCursoHorarioForm
    template_name = "vat/oferta_institucional/horario_form.html"

    def get_initial(self):
        initial = super().get_initial()
        comision_curso_id = self.request.GET.get("comision_curso")
        if (
            comision_curso_id
            and _scoped_comisiones_curso_queryset(self.request.user)
            .filter(pk=comision_curso_id)
            .exists()
        ):
            initial["comision_curso"] = comision_curso_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["comision_curso"].queryset = _scoped_comisiones_curso_queryset(
            self.request.user
        ).order_by("codigo_comision")
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        cantidad = SesionComisionService.generar_para_horario(self.object)
        if cantidad:
            messages.success(
                self.request, f"Horario creado. Se generaron {cantidad} sesiones."
            )
        else:
            messages.success(self.request, "Horario creado exitosamente.")
        return response

    def get_success_url(self):
        return reverse(
            "vat_comision_curso_detail", kwargs={"pk": self.object.comision_curso_id}
        )


class ComisionCursoHorarioUpdateView(LoginRequiredMixin, UpdateView):
    model = ComisionHorario
    form_class = ComisionCursoHorarioForm
    template_name = "vat/oferta_institucional/horario_form.html"

    def get_queryset(self):
        return ComisionHorario.objects.select_related(
            "comision_curso", "dia_semana"
        ).filter(
            comision_curso__curso__centro_id__in=_scoped_centros_ids(self.request.user)
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["comision_curso"].queryset = _scoped_comisiones_curso_queryset(
            self.request.user
        ).order_by("codigo_comision")
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        cantidad = SesionComisionService.regenerar_para_horario(self.object)
        messages.success(
            self.request, f"Horario actualizado. {cantidad} sesiones regeneradas."
        )
        return response

    def get_success_url(self):
        return reverse(
            "vat_comision_curso_detail", kwargs={"pk": self.object.comision_curso_id}
        )


class ComisionCursoHorarioDeleteView(LoginRequiredMixin, DeleteView):
    model = ComisionHorario
    template_name = "vat/oferta_institucional/horario_confirm_delete.html"
    context_object_name = "horario"

    def get_queryset(self):
        return ComisionHorario.objects.select_related(
            "comision_curso", "dia_semana"
        ).filter(
            comision_curso__curso__centro_id__in=_scoped_centros_ids(self.request.user)
        )

    def form_valid(self, form):
        SesionComisionService.eliminar_para_horario(self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "vat_comision_curso_detail", kwargs={"pk": self.object.comision_curso_id}
        )


class ComisionCursoUpdateView(LoginRequiredMixin, UpdateView):
    model = ComisionCurso
    form_class = ComisionCursoForm
    template_name = "vat/curso/comision_curso_form.html"

    def get_queryset(self):
        return _scoped_comisiones_curso_queryset(self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        )
        form.fields["curso"].queryset = Curso.objects.filter(
            centro_id__in=scoped_centros.values_list("id", flat=True)
        ).select_related("centro")
        form.fields["ubicacion"].queryset = InstitucionUbicacion.objects.filter(
            centro_id=self.object.curso.centro_id
        ).select_related("localidad")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Comisión del curso actualizada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.curso.centro_id})}"
            "#cursos"
        )


class ComisionCursoDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = ComisionCurso
    template_name = "vat/curso/comision_curso_confirm_delete.html"
    context_object_name = "comision_curso"

    def get_queryset(self):
        return _scoped_comisiones_curso_queryset(self.request.user)

    def get_success_url(self):
        return (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.curso.centro_id})}"
            "#cursos"
        )
