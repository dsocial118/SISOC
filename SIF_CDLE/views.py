from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
    TemplateView,
    FormView,
)
from Legajos.models import LegajosDerivaciones
from Legajos.forms import DerivacionesRechazoForm, LegajosDerivacionesForm
from django.db.models import Q
from .models import *
from Configuraciones.models import *
from .forms import *
from Usuarios.mixins import PermisosMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.db.models import Sum, F, ExpressionWrapper, IntegerField, Count, Max
import uuid
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings


# # Create your views here.
# derivaciones = LegajosDerivaciones.objects.filter(m2m_programas__nombr__iexact="CDLE")
# print(derivaciones)


class CDLEDerivacionesBuscarListView(TemplateView, PermisosMixin):
    permission_required = "Usuarios.programa_CDLE"
    template_name = "SIF_CDLE/derivaciones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = Legajos.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")

        if query:
            object_list = Legajos.objects.filter(
                Q(apellido__iexact=query) | Q(documento__iexact=query)
            ).distinct()
            if object_list and object_list.count() == 1:
                id = None
                for o in object_list:
                    pk = Legajos.objects.filter(id=o.id).first()
                return redirect("legajosderivaciones_historial", pk.id)

            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list
        return self.render_to_response(context)


class CDLEDerivacionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/derivaciones_bandeja_list.html"
    queryset = LegajosDerivaciones.objects.filter(fk_programa=settings.PROG_CDLE)

    def get_context_data(self, **kwargs):
        context = super(CDLEDerivacionesListView, self).get_context_data(**kwargs)

        model = self.queryset

        query = self.request.GET.get("busqueda")

        if query:
            object_list = LegajosDerivaciones.objects.filter(
                (
                    Q(fk_legajo__apellido__iexact=query)
                    | Q(fk_legajo__nombre__iexact=query)
                )
                & Q(fk_programa=settings.PROG_CDLE)
            ).distinct()
            context["object_list"] = object_list
            model = object_list
            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

        context["todas"] = model
        context["pendientes"] = model.filter(estado="Pendiente")
        context["aceptadas"] = model.filter(estado="Aceptada")
        context["rechazadas"] = model.filter(estado="Rechazada")
        context["enviadas"] = model.filter(fk_usuario=self.request.user)
        return context


class CDLEDerivacionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/derivaciones_detail.html"
    model = LegajosDerivaciones

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(
            pk=pk, fk_programa=settings.PROG_CDLE
        ).first()
        ivi = CDLE_IndiceIVI.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        resultado = (
            ivi.values("clave", "creado", "programa")
            .annotate(total=Sum("fk_criterios_ivi__puntaje"))
            .order_by("-creado")
        )
        context["pk"] = pk
        context["ivi"] = ivi
        context["resultado"] = resultado
        return context


class CDLEDerivacionesRechazo(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/derivaciones_rechazo.html"
    form_class = DerivacionesRechazoForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(
            pk=pk, fk_programa=settings.PROG_CDLE
        ).first()
        context["object"] = legajo
        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        base = LegajosDerivaciones.objects.get(pk=pk)
        base.motivo_rechazo = form.cleaned_data["motivo_rechazo"]
        base.obs_rechazo = form.cleaned_data["obs_rechazo"]
        base.estado = "Rechazada"
        base.fecha_rechazo = date.today()
        base.save()
        return HttpResponseRedirect(reverse("CDLE_derivaciones_listar"))

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("CDLE_derivaciones_listar")


class CDLEDerivacionesUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones
    template_name = "SIF_CDLE/derivaciones_form.html"
    form_class = LegajosDerivacionesForm
    success_message = "Derivación editada con éxito"

    def get_initial(self):
        initial = super().get_initial()
        initial["fk_usuario"] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(id=pk).first()
        context["legajo"] = Legajos.objects.filter(id=legajo.fk_legajo.id).first()
        return context

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs["pk"]
        return reverse("CDLE_derivaciones_ver", kwargs={"pk": pk})


class CDLEPreAdmisionesCreateView(PermisosMixin, CreateView, SuccessMessageMixin):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/preadmisiones_form.html"
    model = CDLE_PreAdmision
    form_class = CDLE_PreadmisionesForm
    success_message = "Preadmisión creada correctamente"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        familia_inversa = LegajoGrupoFamiliar.objects.filter(
            fk_legajo_1_id=legajo.fk_legajo_id
        )
        context["pk"] = pk
        context["legajo"] = legajo
        context["familia"] = familia
        context["familia_inversa"] = familia_inversa
        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        form.instance.estado = "En proceso"
        form.instance.vinculo1 = form.cleaned_data["vinculo1"]
        form.instance.vinculo2 = form.cleaned_data["vinculo2"]
        form.instance.vinculo3 = form.cleaned_data["vinculo3"]
        form.instance.vinculo4 = form.cleaned_data["vinculo4"]
        form.instance.vinculo5 = form.cleaned_data["vinculo5"]
        form.instance.creado_por_id = self.request.user.id

        self.object = form.save()

        base = LegajosDerivaciones.objects.get(pk=pk)
        base.estado = "Aceptada"
        base.save()

        # ---- Historial--------------
        legajo = LegajosDerivaciones.objects.filter(pk=pk).first()
        base = CDLE_Historial()
        base.fk_legajo_id = legajo.fk_legajo.id
        base.fk_legajo_derivacion_id = pk
        base.fk_preadmi_id = self.object.id
        base.movimiento = "ACEPTADO A PREADMISION"
        base.creado_por_id = self.request.user.id
        base.save()

        return HttpResponseRedirect(
            reverse("CDLE_preadmisiones_ver", args=[self.object.pk])
        )


class CDLEPreAdmisionesUpdateView(PermisosMixin, UpdateView, SuccessMessageMixin):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/preadmisiones_form.html"
    model = CDLE_PreAdmision
    form_class = CDLE_PreadmisionesForm
    success_message = "Preadmisión creada correctamente"

    def get_context_data(self, **kwargs):
        pk = CDLE_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        familia_inversa = LegajoGrupoFamiliar.objects.filter(
            fk_legajo_1_id=legajo.fk_legajo_id
        )

        context["pk"] = pk.fk_derivacion_id
        context["legajo"] = legajo
        context["familia"] = familia
        context["familia_inversa"] = familia_inversa
        return context

    def form_valid(self, form):
        pk = CDLE_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        form.instance.creado_por_id = pk.creado_por_id
        form.instance.vinculo1 = form.cleaned_data["vinculo1"]
        form.instance.vinculo2 = form.cleaned_data["vinculo2"]
        form.instance.vinculo3 = form.cleaned_data["vinculo3"]
        form.instance.vinculo4 = form.cleaned_data["vinculo4"]
        form.instance.vinculo5 = form.cleaned_data["vinculo5"]
        form.instance.estado = pk.estado
        form.instance.modificado_por_id = self.request.user.id
        self.object = form.save()

        return HttpResponseRedirect(
            reverse("CDLE_preadmisiones_ver", args=[self.object.pk])
        )


class CDLEPreAdmisionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/preadmisiones_detail.html"
    model = CDLE_PreAdmision

    def get_context_data(self, **kwargs):
        pk = CDLE_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        ivi = CDLE_IndiceIVI.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        ingreso = CDLE_IndiceIngreso.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        resultado = (
            ivi.filter(tipo="Ingreso")
            .values("clave", "creado", "programa")
            .annotate(total=Sum("fk_criterios_ivi__puntaje"))
            .order_by("-creado")
        )
        resultado_ingreso = (
            ingreso.filter(tipo="Ingreso")
            .values("clave", "creado", "programa")
            .annotate(total=Sum("fk_criterios_ingreso__puntaje"))
            .order_by("-creado")
        )
        context["ivi"] = ivi
        context["ingreso"] = ingreso
        context["criterios_total"] = ingreso.count()
        context["cant_combinables"] = ingreso.filter(
            fk_criterios_ingreso__tipo="Criterios combinables para el ingreso"
        ).count()
        context["cant_sociales"] = ingreso.filter(
            fk_criterios_ingreso__tipo="Criterios sociales para el ingreso"
        ).count()
        context["autonomos"] = ingreso.filter(
            fk_criterios_ingreso__tipo="Criteros autónomos de ingreso"
        ).all()
        context["resultado"] = resultado
        context["resultado_ingreso"] = resultado_ingreso
        context["legajo"] = legajo
        context["familia"] = familia
        return context

    def post(self, request, *args, **kwargs):
        if "finalizar_preadm" in request.POST:
            # Realiza la actualización del campo aquí
            objeto = self.get_object()
            objeto.estado = "Finalizada"
            objeto.ivi = "NO"
            objeto.indice_ingreso = "NO"
            objeto.admitido = "NO"
            objeto.save()

            # ---------HISTORIAL---------------------------------
            pk = self.kwargs["pk"]
            legajo = CDLE_PreAdmision.objects.filter(pk=pk).first()
            base = CDLE_Historial()
            base.fk_legajo_id = legajo.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
            base.fk_preadmi_id = pk
            base.movimiento = "FINALIZADO PREADMISION"
            base.creado_por_id = self.request.user.id
            base.save()
            # Redirige de nuevo a la vista de detalle actualizada
            return HttpResponseRedirect(self.request.path_info)


class CDLEPreAdmisionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/preadmisiones_list.html"
    model = CDLE_PreAdmision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pre_admi = CDLE_PreAdmision.objects.all()
        context["object"] = pre_admi
        return context


class CDLEPreAdmisionesBuscarListView(PermisosMixin, TemplateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/preadmisiones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = CDLE_PreAdmision.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            object_list = (
                CDLE_PreAdmision.objects.filter(
                    Q(fk_legajo__apellido__iexact=query)
                    | Q(fk_legajo__documento__iexact=query),
                    fk_derivacion__fk_programa_id=settings.PROG_CDLE,
                )
                .exclude(estado__in=["Rechazada", "Aceptada"])
                .distinct()
            )
            # object_list = Legajos.objects.filter(Q(apellido__iexact=query) | Q(documento__iexact=query))
            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list

        return self.render_to_response(context)


class CDLEPreAdmisionesDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = CDLE_PreAdmision
    template_name = "SIF_CDLE/preadmisiones_confirm_delete.html"
    success_url = reverse_lazy("CDLE_preadmisiones_listar")

    def form_valid(self, form):
        if self.object.estado != "En proceso":
            messages.error(
                self.request,
                "No es posible eliminar una solicitud en estado " + self.object.estado,
            )

            return redirect("CDLE_preadmisiones_ver", pk=int(self.object.id))

        if self.request.user.id != self.object.creado_por.id:
            print(self.request.user)
            print(self.object.creado_por)
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("CDLE_preadmisiones_ver", pk=int(self.object.id))

        else:
            self.object.delete()
            return redirect(self.success_url)


class CDLECriteriosIngresoCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/criterios_ingreso_form.html"
    model = Criterios_Ingreso
    form_class = criterios_Ingreso

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse("CDLE_criterios_ingreso_crear"))


class CDLEIndiceIngresoCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios_Ingreso
    template_name = "SIF_CDLE/indiceingreso_form.html"
    form_class = CDLE_IndiceIngresoForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        object = CDLE_PreAdmision.objects.filter(pk=pk).first()
        # object = Legajos.objects.filter(pk=pk).first()
        criterio = Criterios_Ingreso.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context["form2"] = CDLE_IndiceIngresoHistorialForm()
        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = CDLE_PreAdmision.objects.filter(pk=pk).first()
        clave = str(uuid.uuid4())
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_Ingreso.objects.aggregate(total=Sum("puntaje"))[
            "total"
        ]
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ingreso = Criterios_Ingreso.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ingreso.puntaje)
                base = CDLE_IndiceIngreso()
                base.fk_criterios_ingreso_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.tipo = "Ingreso"
                base.presencia = True
                base.programa = "CDLE"
                base.clave = clave
                base.save()

        # total_puntaje contiene la suma de los valores de F
        foto = CDLE_Foto_Ingreso()
        foto.observaciones = request.POST.get("observaciones", "")
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        # foto.crit_modificables = crit_modificables
        # foto.crit_presentes = crit_presentes
        foto.tipo = "Ingreso"
        foto.clave = clave
        foto.creado_por_id = self.request.user.id
        foto.save()

        preadmi.indice_ingreso = "SI"
        preadmi.save()

        # ---------HISTORIAL---------------------------------
        pk = self.kwargs["pk"]
        base = CDLE_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "CREACION INDICE INGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect("CDLE_indiceingreso_ver", preadmi.id)


class CDLEIndiceIngresoUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/indiceingreso_edit.html"
    model = CDLE_PreAdmision
    form_class = CDLE_IndiceIngresoForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        activos = CDLE_IndiceIngreso.objects.filter(fk_preadmi_id=pk)
        observaciones = CDLE_Foto_Ingreso.objects.filter(fk_preadmi_id=pk).first()

        context = super().get_context_data(**kwargs)
        context["object"] = CDLE_PreAdmision.objects.filter(pk=pk).first()
        context["activos"] = activos
        context["clave"] = observaciones.clave
        context["observaciones"] = observaciones.observaciones
        context["criterio"] = Criterios_Ingreso.objects.all()
        context["form2"] = CDLE_IndiceIngresoHistorialForm()
        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        preadmi = CDLE_PreAdmision.objects.filter(pk=pk).first()
        CDLE_foto = CDLE_Foto_Ingreso.objects.filter(fk_preadmi_id=pk).first()
        clave = CDLE_foto.clave
        indices_ingreso = CDLE_IndiceIngreso.objects.filter(clave=clave)
        # CDLE_foto.delete()
        indices_ingreso.delete()
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_Ingreso.objects.aggregate(total=Sum("puntaje"))[
            "total"
        ]
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ingreso = Criterios_Ingreso.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ingreso.puntaje)
                base = CDLE_IndiceIngreso()
                base.fk_criterios_ingreso_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.presencia = True
                base.tipo = "Ingreso"
                base.programa = "CDLE"
                base.clave = clave
                base.save()

        # total_puntaje contiene la suma de los valores de F
        foto = CDLE_Foto_Ingreso.objects.filter(clave=clave).first()
        foto.observaciones = request.POST.get("observaciones", "")
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        # foto.crit_modificables = crit_modificables
        # foto.crit_presentes = crit_presentes
        foto.tipo = "Ingreso"
        foto.clave = clave
        foto.modificado_por_id = self.request.user.id
        foto.save()

        # ---------HISTORIAL---------------------------------
        pk = self.kwargs["pk"]
        preadmi = CDLE_PreAdmision.objects.filter(pk=pk).first()
        base = CDLE_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "MODIFICACION INDICE INGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect("CDLE_indiceingreso_ver", preadmi.id)


class CDLEIndiceIngresoDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/indiceingreso_detail.html"
    model = CDLE_PreAdmision

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        criterio = CDLE_IndiceIngreso.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        object = CDLE_PreAdmision.objects.filter(pk=pk).first()
        foto_ingreso = CDLE_Foto_Ingreso.objects.filter(
            fk_preadmi_id=pk, tipo="Ingreso"
        ).first()

        context["object"] = object
        context["foto_ingreso"] = foto_ingreso
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(
            total=Sum("fk_criterios_ingreso__puntaje")
        )
        context["cantidad"] = criterio.count()
        context["cant_combinables"] = criterio.filter(
            fk_criterios_ingreso__tipo="Criterios combinables para el ingreso"
        ).count()
        context["cant_sociales"] = criterio.filter(
            fk_criterios_ingreso__tipo="Criterios sociales para el ingreso"
        ).count()
        context["mod_puntaje"] = criterio.filter(
            fk_criterios_ingreso__modificable__icontains="si"
        ).aggregate(total=Sum("fk_criterios_ingreso__puntaje"))
        context["ajustes"] = criterio.filter(
            fk_criterios_ingreso__tipo="Ajustes"
        ).count()
        # context['maximo'] = foto_ingreso.puntaje_max

        return context


# --------- CREAR IVI -------------------------------------


class CDLECriteriosIVICreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/criterios_ivi_form.html"
    model = Criterios_IVI
    form_class = criterios_IVI

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse("CDLE_criterios_ivi_crear"))


class CDLEIndiceIviCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios_IVI
    template_name = "SIF_CDLE/indiceivi_form.html"
    form_class = CDLE_IndiceIviForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        object = CDLE_PreAdmision.objects.filter(pk=pk).first()
        # object = Legajos.objects.filter(pk=pk).first()
        criterio = Criterios_IVI.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context["form2"] = CDLE_IndiceIviHistorialForm()
        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = CDLE_PreAdmision.objects.filter(pk=pk).first()
        clave = str(uuid.uuid4())
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum("puntaje"))["total"]
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = CDLE_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.tipo = "Ingreso"
                base.presencia = True
                base.programa = "CDLE"
                base.clave = clave
                base.save()

        # total_puntaje contiene la suma de los valores de F
        foto = CDLE_Foto_IVI()
        foto.observaciones = request.POST.get("observaciones", "")
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        # foto.crit_modificables = crit_modificables
        # foto.crit_presentes = crit_presentes
        foto.tipo = "Ingreso"
        foto.clave = clave
        foto.creado_por_id = self.request.user.id
        foto.save()

        preadmi.ivi = "SI"
        preadmi.save()

        # ---------HISTORIAL---------------------------------
        pk = self.kwargs["pk"]
        base = CDLE_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "CREACION IVI"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect("CDLE_indiceivi_ver", preadmi.id)


class CDLEIndiceIviUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/indiceivi_edit.html"
    model = CDLE_PreAdmision
    form_class = CDLE_IndiceIviForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        activos = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=pk)
        observaciones = CDLE_Foto_IVI.objects.filter(fk_preadmi_id=pk).first()

        context = super().get_context_data(**kwargs)
        context["object"] = CDLE_PreAdmision.objects.filter(pk=pk).first()
        context["activos"] = activos
        context["clave"] = observaciones.clave
        context["observaciones"] = observaciones.observaciones
        context["criterio"] = Criterios_IVI.objects.all()
        context["form2"] = CDLE_IndiceIviHistorialForm()
        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        preadmi = CDLE_PreAdmision.objects.filter(pk=pk).first()
        CDLE_foto = CDLE_Foto_IVI.objects.filter(fk_preadmi_id=pk).first()
        clave = CDLE_foto.clave
        indices_ivi = CDLE_IndiceIVI.objects.filter(clave=clave)
        # CDLE_foto.delete()
        indices_ivi.delete()
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum("puntaje"))["total"]
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = CDLE_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.presencia = True
                base.programa = "CDLE"
                base.tipo = "Ingreso"
                base.clave = clave
                base.save()

        # total_puntaje contiene la suma de los valores de F
        foto = CDLE_Foto_IVI.objects.filter(clave=clave).first()
        foto.observaciones = request.POST.get("observaciones", "")
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        # foto.crit_modificables = crit_modificables
        # foto.crit_presentes = crit_presentes
        # foto.tipo = "Ingreso"
        # foto.clave = clave
        foto.modificado_por_id = self.request.user.id
        foto.save()

        # ---------HISTORIAL---------------------------------
        pk = self.kwargs["pk"]
        preadmi = CDLE_PreAdmision.objects.filter(pk=pk).first()
        base = CDLE_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "MODIFICACION IVI"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect("CDLE_indiceivi_ver", preadmi.id)


class CDLEIndiceIviDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/indiceivi_detail.html"
    model = CDLE_PreAdmision

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        criterio = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        object = CDLE_PreAdmision.objects.filter(pk=pk).first()
        foto_ivi = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=pk, tipo="Ingreso"
        ).first()

        context["object"] = object
        context["foto_ivi"] = foto_ivi
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum("fk_criterios_ivi__puntaje"))
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(
            fk_criterios_ivi__modificable__icontains="si"
        ).count()
        context["mod_puntaje"] = criterio.filter(
            fk_criterios_ivi__modificable__icontains="si"
        ).aggregate(total=Sum("fk_criterios_ivi__puntaje"))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo="Ajustes").count()
        # context['maximo'] = foto_ivi.puntaje_max
        return context


class CDLEPreAdmisiones2DetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/preadmisiones_detail2.html"
    model = CDLE_PreAdmision


class CDLEPreAdmisiones3DetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/preadmisiones_detail3.html"
    model = CDLE_PreAdmision

    def get_context_data(self, **kwargs):
        pk = CDLE_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        criterio = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        criterio_ingreso = CDLE_IndiceIngreso.objects.filter(
            fk_preadmi_id=pk, tipo="Ingreso"
        )
        foto_ivi = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=pk, tipo="Ingreso"
        ).first()
        foto_ingreso = CDLE_Foto_Ingreso.objects.filter(
            fk_preadmi_id=pk, tipo="Ingreso"
        ).first()

        context["legajo"] = legajo
        context["familia"] = familia
        context["foto_ivi"] = foto_ivi
        context["foto_ingreso"] = foto_ingreso
        context["puntaje"] = foto_ivi.puntaje
        context["puntaje_ingreso"] = foto_ingreso.puntaje
        context["cantidad"] = criterio.count()
        context["cantidad_ingreso"] = criterio_ingreso.count()
        context["modificables"] = criterio.filter(
            fk_criterios_ivi__modificable__icontains="si"
        ).count()
        context["mod_puntaje"] = criterio.filter(
            fk_criterios_ivi__modificable__icontains="si"
        ).aggregate(total=Sum("fk_criterios_ivi__puntaje"))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo="Ajustes").count()
        context["maximo"] = foto_ivi.puntaje_max
        context["maximo_ingreso"] = foto_ingreso.puntaje_max
        context["criterios_total"] = criterio_ingreso.count()
        context["cant_combinables"] = criterio_ingreso.filter(
            fk_criterios_ingreso__tipo="Criterios combinables para el ingreso"
        ).count()
        context["cant_sociales"] = criterio_ingreso.filter(
            fk_criterios_ingreso__tipo="Criterios sociales para el ingreso"
        ).count()
        context["autonomos"] = criterio_ingreso.filter(
            fk_criterios_ingreso__tipo="Criteros autónomos de ingreso"
        ).all()
        return context

    def post(self, request, *args, **kwargs):
        if "admitir" in request.POST:
            preadmi = CDLE_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
            preadmi.admitido = "SI"
            preadmi.save()

            base1 = CDLE_Admision()
            base1.fk_preadmi_id = preadmi.pk
            base1.creado_por_id = self.request.user.id
            base1.save()
            redirigir = base1.pk

            # ---------HISTORIAL---------------------------------
            pk = self.kwargs["pk"]
            legajo = CDLE_PreAdmision.objects.filter(pk=pk).first()
            base = CDLE_Historial()
            base.fk_legajo_id = legajo.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
            base.fk_preadmi_id = pk
            base.fk_admision_id = redirigir
            base.movimiento = "ADMITIDO"
            base.creado_por_id = self.request.user.id
            base.save()

            # Redirige de nuevo a la vista de detalle actualizada
            return redirect("CDLE_asignado_admisiones_ver", redirigir)


class CDLEAdmisionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/adminsiones_list.html"
    model = CDLE_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        criterio = CDLE_IndiceIVI.objects.all()
        criterio_ingreso = CDLE_IndiceIngreso.objects.all()
        admi = CDLE_Admision.objects.all()
        foto = CDLE_Foto_IVI.objects.all()
        foto_ingreso = CDLE_Foto_Ingreso.objects.all()
        conteo = CDLE_IndiceIngreso.objects.values("fk_preadmi_id").annotate(
            total=Count("fk_preadmi_id")
        )

        context["conteo"] = conteo
        context["admi"] = admi
        context["foto"] = foto
        context["foto_ingreso"] = criterio_ingreso.aggregate(
            total=Count("fk_criterios_ingreso")
        )
        context["puntaje"] = criterio.aggregate(total=Sum("fk_criterios_ivi__puntaje"))
        context["puntaje_ingreso"] = criterio_ingreso.aggregate(
            total=Sum("fk_criterios_ingreso__puntaje")
        )
        return context


class CDLEAdmisionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = CDLE_Admision
    template_name = "SIF_CDLE/admisiones_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = CDLE_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        preadmi = CDLE_PreAdmision.objects.filter(pk=pk.fk_preadmi_id).first()
        criterio = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        foto_ivi = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=preadmi, tipo="Ingreso"
        ).first()

        context["foto_ivi"] = foto_ivi
        context["puntaje"] = foto_ivi.puntaje
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(
            fk_criterios_ivi__modificable__icontains="si"
        ).count()
        context["mod_puntaje"] = criterio.filter(
            fk_criterios_ivi__modificable__icontains="si"
        ).aggregate(total=Sum("fk_criterios_ivi__puntaje"))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo="Ajustes").count()
        context["maximo"] = foto_ivi.puntaje_max

        return context


class CDLEAsignadoAdmisionDetail(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/asignado_admisiones_detail.html"
    model = CDLE_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = CDLE_Admision.objects.filter(pk=self.kwargs["pk"]).first()

        preadmi = CDLE_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        criterio_ingreso = CDLE_IndiceIngreso.objects.filter(
            fk_preadmi_id=preadmi, tipo="Ingreso"
        )
        criterio2 = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=preadmi, tipo="Ingreso"
        ).first()
        observaciones_ingreso = CDLE_Foto_Ingreso.objects.filter(
            fk_preadmi_id=preadmi, tipo="Ingreso"
        ).first()
        observaciones2 = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=preadmi, tipo="Ingreso"
        ).first()
        intervenciones = CDLE_Intervenciones.objects.filter(
            fk_admision_id=admi.id
        ).all()
        intervenciones_last = CDLE_Intervenciones.objects.filter(
            fk_admision_id=admi.id
        ).last()
        foto_ivi_fin = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso"
        ).last()
        foto_ivi_inicio = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso"
        ).first()

        context["foto_ivi_fin"] = foto_ivi_fin
        context["foto_ivi_inicio"] = foto_ivi_inicio
        context["observaciones"] = observaciones
        context["observaciones_ingreso"] = observaciones_ingreso
        context["observaciones2"] = observaciones2
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum("fk_criterios_ivi__puntaje"))
        context["cant_ingreso"] = criterio_ingreso.count()
        context["puntaje2"] = criterio2.aggregate(
            total=Sum("fk_criterios_ivi__puntaje")
        )
        context["object"] = admi
        context["vo"] = self.object
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last

        return context


class CDLEInactivaAdmisionDetail(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/inactiva_admisiones_detail.html"
    model = CDLE_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = CDLE_Admision.objects.filter(pk=self.kwargs["pk"]).first()

        preadmi = CDLE_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Egreso")
        intervenciones = CDLE_Intervenciones.objects.filter(
            fk_admision_id=admi.id
        ).all()
        intervenciones_last = CDLE_Intervenciones.objects.filter(
            fk_admision_id=admi.id
        ).last()
        foto_ivi_fin = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=admi.fk_preadmi_id, tipo="Egreso"
        ).first()
        foto_ivi_inicio = CDLE_Foto_IVI.objects.filter(
            fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso"
        ).first()

        context["foto_ivi_fin"] = foto_ivi_fin
        context["foto_ivi_inicio"] = foto_ivi_inicio
        context["criterio"] = criterio
        context["object"] = admi
        context["vo"] = self.object
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last

        return context


class CDLEIntervencionesCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = CDLE_Intervenciones  # Debería ser el modelo CDLE_Intervenciones
    template_name = "SIF_CDLE/intervenciones_form.html"
    form_class = CDLE_IntervencionesForm

    def form_valid(self, form):
        form.instance.fk_admision_id = self.kwargs["pk"]
        form.instance.creado_por_id = self.request.user.id
        self.object = form.save()

        # --------- HISTORIAL ---------------------------------
        pk = self.kwargs["pk"]
        legajo = CDLE_Admision.objects.filter(pk=pk).first()
        base = CDLE_Historial()
        base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
        base.fk_preadmi_id = legajo.fk_preadmi.pk
        base.fk_admision_id = legajo.id  # Cambia a self.object.id
        base.movimiento = "INTERVENCION CREADA"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect("CDLE_intervencion_ver", pk=self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = CDLE_Admision.objects.get(
            pk=self.kwargs["pk"]
        )  # Obtén el objeto directamente
        context["form"] = self.get_form()  # Obtiene una instancia del formulario

        return context


class CDLEIntervencionesUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = CDLE_Intervenciones
    template_name = "SIF_CDLE/intervenciones_form.html"
    form_class = CDLE_IntervencionesForm

    def form_valid(self, form):
        pk = CDLE_Intervenciones.objects.filter(pk=self.kwargs["pk"]).first()
        admi = CDLE_Admision.objects.filter(id=pk.fk_admision.id).first()
        form.instance.fk_admision_id = admi.id
        form.instance.modificado_por_id = self.request.user.id
        self.object = form.save()

        # --------- HISTORIAL ---------------------------------
        pk = self.kwargs["pk"]
        pk = CDLE_Intervenciones.objects.filter(pk=pk).first()
        legajo = CDLE_Admision.objects.filter(pk=pk.fk_admision_id).first()
        base = CDLE_Historial()
        base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
        base.fk_preadmi_id = legajo.fk_preadmi.pk
        base.fk_admision_id = legajo.pk
        base.movimiento = "INTERVENCION MODIFICADA"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect("CDLE_intervencion_ver", self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = CDLE_Intervenciones.objects.filter(pk=self.kwargs["pk"]).first()
        admi = CDLE_Admision.objects.filter(id=pk.fk_admision.id).first()

        context["object"] = admi

        return context


class CDLEIntervencionesLegajosListView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/intervenciones_legajo_list.html"
    model = CDLE_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = CDLE_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        intervenciones = CDLE_Intervenciones.objects.filter(
            fk_admision_id=admi.id
        ).all()
        intervenciones_last = CDLE_Intervenciones.objects.filter(
            fk_admision_id=admi.id
        ).last()
        preadmi = CDLE_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones = CDLE_Foto_IVI.objects.filter(
            clave=criterio.first().clave, tipo="Ingreso"
        ).first()
        criterio2 = CDLE_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones2 = CDLE_Foto_IVI.objects.filter(
            clave=criterio2.last().clave, tipo="Ingreso"
        ).first()

        context["object"] = admi
        context["intervenciones"] = intervenciones
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last

        context["puntaje"] = criterio.aggregate(total=Sum("fk_criterios_ivi__puntaje"))
        context["observaciones"] = observaciones
        context["observaciones2"] = observaciones2
        context["puntaje2"] = criterio2.aggregate(
            total=Sum("fk_criterios_ivi__puntaje")
        )

        return context


class CDLEIntervencionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/intervenciones_list.html"
    model = CDLE_Intervenciones

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        intervenciones = CDLE_Intervenciones.objects.all()
        context["intervenciones"] = intervenciones
        return context


class CDLEIntervencionesDetail(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/intervencion_detail.html"
    model = CDLE_Intervenciones


class CDLEOpcionesResponsablesCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/intervenciones_resposables.html"
    model = OpcionesResponsables
    form_class = CDLE_OpcionesResponsablesForm

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse("CDLE_OpcionesResponsables"))


class CDLEIntervencionesDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = CDLE_Intervenciones
    template_name = "SIF_CDLE/intervenciones_confirm_delete.html"
    success_url = reverse_lazy("CDLE_intervenciones_listar")

    def form_valid(self, form):

        if self.request.user.id != self.object.creado_por.id:
            print(self.request.user)
            print(self.object.creado_por)
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("CDLE_preadmisiones_ver", pk=int(self.object.id))

        else:
            self.object.delete()
            return redirect(self.success_url)


class CDLEAdmisionesBuscarListView(PermisosMixin, TemplateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_CDLE/admisiones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = CDLE_PreAdmision.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            object_list = (
                CDLE_Admision.objects.filter(
                    Q(fk_preadmi__fk_legajo__apellido__iexact=query)
                    | Q(fk_preadmi__fk_legajo__documento__iexact=query),
                    fk_preadmi__fk_derivacion__fk_programa_id=settings.PROG_CDLE,
                )
                .exclude(estado__in=["Rechazada", "Aceptada"])
                .distinct()
            )
            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list

        return self.render_to_response(context)


class CDLEIndiceIviEgresoCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Legajos
    template_name = "SIF_CDLE/indiceivi_form_egreso.html"
    form_class = CDLE_IndiceIviForm
    success_url = reverse_lazy("legajos_listar")

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        admi = CDLE_Admision.objects.filter(pk=pk).first()
        object = Legajos.objects.filter(pk=admi.fk_preadmi.fk_legajo.id).first()
        criterio = Criterios_IVI.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context["form2"] = CDLE_IndiceIviHistorialForm()
        context["admi"] = admi
        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        admi = CDLE_Admision.objects.filter(pk=pk).first()
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = CDLE_PreAdmision.objects.filter(
            fk_legajo_id=admi.fk_preadmi.fk_legajo.id
        ).first()
        foto_ivi = CDLE_Foto_IVI.objects.filter(fk_preadmi_id=preadmi.id).first()
        clave = foto_ivi.clave
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum("puntaje"))["total"]
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = CDLE_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = admi.fk_preadmi.fk_legajo.id
                base.fk_preadmi_id = preadmi.id
                base.tipo = "Egreso"
                base.presencia = True
                base.programa = "CDLE"
                base.clave = clave
                base.save()

        # total_puntaje contiene la suma de los valores de F
        foto = CDLE_Foto_IVI()
        foto.observaciones = request.POST.get("observaciones", "")
        foto.fk_preadmi_id = preadmi.id
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        # foto.crit_modificables = crit_modificables
        # foto.crit_presentes = crit_presentes
        foto.tipo = "Egreso"
        foto.clave = clave
        foto.creado_por_id = self.request.user.id
        foto.save()

        admi.estado = "Inactiva"
        admi.modificado_por_id = self.request.user.id
        admi.save()

        # ---------HISTORIAL---------------------------------
        pk = self.kwargs["pk"]
        legajo = admi.fk_preadmi
        base = CDLE_Historial()
        base.fk_legajo_id = legajo.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
        base.fk_preadmi_id = legajo.id
        base.movimiento = "IVI EGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect("CDLE_admisiones_listar")
