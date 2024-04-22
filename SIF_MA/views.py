from django.views.generic import CreateView,ListView,DetailView,UpdateView,DeleteView,TemplateView, FormView
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
#derivaciones = LegajosDerivaciones.objects.filter(m2m_programas__nombr__iexact="MA")
#print(derivaciones)

class MADerivacionesBuscarListView(TemplateView, PermisosMixin):
    permission_required = "Usuarios.programa_MA"
    template_name = "SIF_MA/derivaciones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = Legajos.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")

        if query:
            object_list = Legajos.objects.filter(Q(apellido__iexact=query) | Q(documento__iexact=query)).distinct()
            if object_list and object_list.count() == 1:
                id = None
                for o in object_list:
                    pk = Legajos.objects.filter(id = o.id).first()
                return redirect("legajosderivaciones_historial", pk.id)

            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list
        return self.render_to_response(context)


class MADerivacionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/derivaciones_bandeja_list.html"
    queryset = LegajosDerivaciones.objects.filter(fk_programa=settings.PROG_MA)

    def get_context_data(self, **kwargs):
        context = super(MADerivacionesListView, self).get_context_data(**kwargs)

        model = LegajosDerivaciones.objects.filter(fk_programa=settings.PROG_MA)

        context["todas"] = model
        context["pendientes"] = model.filter(estado="Pendiente")
        context["aceptadas"] = model.filter(estado="Aceptada")
        context["rechazadas"] = model.filter(estado="Rechazada")
        context["enviadas"] = model.filter(fk_usuario=self.request.user)
        return context

class MADerivacionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/derivaciones_detail.html"
    model = LegajosDerivaciones

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk, fk_programa=settings.PROG_MA).first()
        ivi = MA_IndiceIVI.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        resultado = ivi.values('clave', 'creado', 'programa').annotate(total=Sum('fk_criterios_ivi__puntaje')).order_by('-creado')
        context["pk"] = pk
        context["ivi"] = ivi
        context["resultado"] = resultado
        return context

class MADerivacionesRechazo(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/derivaciones_rechazo.html"
    form_class = DerivacionesRechazoForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk, fk_programa=settings.PROG_MA).first()
        context["object"] = legajo
        return context
    
    def form_valid(self, form):
        pk = self.kwargs["pk"]
        base = LegajosDerivaciones.objects.get(pk=pk)
        base.motivo_rechazo = form.cleaned_data['motivo_rechazo']
        base.obs_rechazo = form.cleaned_data['obs_rechazo']
        base.estado = "Rechazada"
        base.fecha_rechazo = date.today()
        base.save() 
        return HttpResponseRedirect(reverse('MA_derivaciones_listar'))
    
    def form_invalid(self, form):
        return super().form_invalid(form)   
    
    def get_success_url(self):
        return reverse('MA_derivaciones_listar')
    
class MADerivacionesUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones
    template_name = "SIF_MA/derivaciones_form.html"
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
        pk = self.kwargs['pk']
        return reverse('MA_derivaciones_ver', kwargs={'pk': pk})

class MAPreAdmisionesCreateView(PermisosMixin,CreateView, SuccessMessageMixin):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/preadmisiones_form.html"
    model = MA_PreAdmision
    form_class = MA_PreadmisionesForm
    success_message = "Preadmisión creada correctamente"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        familia_inversa = LegajoGrupoFamiliar.objects.filter(fk_legajo_1_id=legajo.fk_legajo_id)
        context["pk"] = pk
        context["legajo"] = legajo
        context["familia"] = familia
        context["familia_inversa"] = familia_inversa
        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        form.instance.estado = 'En proceso'
        form.instance.vinculo1 = form.cleaned_data['vinculo1']
        form.instance.vinculo2 = form.cleaned_data['vinculo2']
        form.instance.vinculo3 = form.cleaned_data['vinculo3']
        form.instance.vinculo4 = form.cleaned_data['vinculo4']
        form.instance.vinculo5 = form.cleaned_data['vinculo5']
        form.instance.creado_por_id = self.request.user.id

        self.object = form.save()

        base = LegajosDerivaciones.objects.get(pk=pk)
        base.estado = "Aceptada"
        base.save() 
        
        #---- Historial--------------
        legajo = LegajosDerivaciones.objects.filter(pk=pk).first()
        base = MA_Historial()
        base.fk_legajo_id = legajo.fk_legajo.id
        base.fk_legajo_derivacion_id = pk
        base.fk_preadmi_id = self.object.id
        base.movimiento = "ACEPTADO A PREADMISION"
        base.creado_por_id = self.request.user.id
        base.save()

        return HttpResponseRedirect(reverse('MA_preadmisiones_ver', args=[self.object.pk]))

class MAPreAdmisionesUpdateView(PermisosMixin,UpdateView, SuccessMessageMixin):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/preadmisiones_form.html"
    model = MA_PreAdmision
    form_class = MA_PreadmisionesForm
    success_message = "Preadmisión creada correctamente"

    def get_context_data(self, **kwargs):
        pk = MA_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        familia_inversa = LegajoGrupoFamiliar.objects.filter(fk_legajo_1_id=legajo.fk_legajo_id)

        context["pk"] = pk.fk_derivacion_id
        context["legajo"] = legajo
        context["familia"] = familia
        context["familia_inversa"] = familia_inversa
        return context

    def form_valid(self, form):
        pk = MA_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        form.instance.creado_por_id = pk.creado_por_id
        form.instance.vinculo1 = form.cleaned_data['vinculo1']
        form.instance.vinculo2 = form.cleaned_data['vinculo2']
        form.instance.vinculo3 = form.cleaned_data['vinculo3']
        form.instance.vinculo4 = form.cleaned_data['vinculo4']
        form.instance.vinculo5 = form.cleaned_data['vinculo5']
        form.instance.estado = pk.estado
        form.instance.modificado_por_id = self.request.user.id
        self.object = form.save()

        return HttpResponseRedirect(reverse('MA_preadmisiones_ver', args=[self.object.pk]))

class MAPreAdmisionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/preadmisiones_detail.html"
    model = MA_PreAdmision

    def get_context_data(self, **kwargs):
        pk = MA_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        ivi = MA_IndiceIVI.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        ingreso = MA_IndiceIngreso.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        resultado = ivi.values('clave', 'creado', 'programa').annotate(total=Sum('fk_criterios_ivi__puntaje')).order_by('-creado')
        resultado_ingreso = ingreso.values('clave', 'creado', 'programa').annotate(total=Sum('fk_criterios_ingreso__puntaje')).order_by('-creado')
        context["ivi"] = ivi
        context["ingreso"] = ingreso
        context['criterios_total'] = ingreso.count()
        context["cant_combinables"] = ingreso.filter(fk_criterios_ingreso__tipo='Criterios combinables para el ingreso').count()
        context["cant_sociales"] = ingreso.filter(fk_criterios_ingreso__tipo='Criterios sociales para el ingreso').count() 
        context["autonomos"] = ingreso.filter(fk_criterios_ingreso__tipo='Criteros autónomos de ingreso').all()
        context["resultado"] = resultado
        context["resultado_ingreso"] = resultado_ingreso
        context["legajo"] = legajo
        context["familia"] = familia
        return context
    
    def post(self, request, *args, **kwargs):
        if 'finalizar_preadm' in request.POST:
            # Realiza la actualización del campo aquí
            objeto = self.get_object()
            objeto.estado = 'Finalizada'
            objeto.ivi = "NO"
            objeto.indice_ingreso = "NO"
            objeto.admitido = "NO"
            objeto.save()

            #---------HISTORIAL---------------------------------
            pk=self.kwargs["pk"]
            legajo = MA_PreAdmision.objects.filter(pk=pk).first()
            base = MA_Historial()
            base.fk_legajo_id = legajo.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
            base.fk_preadmi_id = pk
            base.movimiento = "FINALIZADO PREADMISION"
            base.creado_por_id = self.request.user.id
            base.save()
            # Redirige de nuevo a la vista de detalle actualizada
            return HttpResponseRedirect(self.request.path_info)

class MAPreAdmisionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/preadmisiones_list.html"
    model = MA_PreAdmision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pre_admi = MA_PreAdmision.objects.all()
        context["object"] = pre_admi
        return context

class MAPreAdmisionesBuscarListView(PermisosMixin, TemplateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/preadmisiones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = MA_PreAdmision.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            object_list = MA_PreAdmision.objects.filter(Q(fk_legajo__apellido__iexact=query) | Q(fk_legajo__documento__iexact=query), fk_derivacion__fk_programa_id=25).exclude(estado__in=['Rechazada','Aceptada']).distinct()
            #object_list = Legajos.objects.filter(Q(apellido__iexact=query) | Q(documento__iexact=query))
            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list

        return self.render_to_response(context)

class MAPreAdmisionesDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = MA_PreAdmision
    template_name = "SIF_MA/preadmisiones_confirm_delete.html"
    success_url = reverse_lazy("MA_preadmisiones_listar")

    def form_valid(self, form):
        if self.object.estado != "En proceso":
            messages.error(
                self.request,
                "No es posible eliminar una solicitud en estado " + self.object.estado,
            )

            return redirect("MA_preadmisiones_ver", pk=int(self.object.id))

        if self.request.user.id != self.object.creado_por.id:
            print(self.request.user)
            print(self.object.creado_por)
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("MA_preadmisiones_ver", pk=int(self.object.id))

        else:
            self.object.delete()
            return redirect(self.success_url)

class MACriteriosIngresoCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/criterios_ingreso_form.html"
    model = Criterios_Ingreso
    form_class = criterios_Ingreso

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse('MA_criterios_ingreso_crear'))
    
class MAIndiceIngresoCreateView (PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios_Ingreso
    template_name = "SIF_MA/indiceingreso_form.html"
    form_class = MA_IndiceIngresoForm    
    
    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        object = MA_PreAdmision.objects.filter(pk=pk).first()
        #object = Legajos.objects.filter(pk=pk).first()
        criterio = Criterios_Ingreso.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context['form2'] = MA_IndiceIngresoHistorialForm()
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = MA_PreAdmision.objects.filter(pk=pk).first()
        clave = str(uuid.uuid4())
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_Ingreso.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ingreso = Criterios_Ingreso.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ingreso.puntaje)
                base = MA_IndiceIngreso()
                base.fk_criterios_ingreso_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.tipo = "Ingreso"
                base.presencia = True
                base.programa = "MA"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = MA_Foto_Ingreso()
        foto.observaciones = request.POST.get('observaciones', '')
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        #foto.crit_modificables = crit_modificables
        #foto.crit_presentes = crit_presentes
        foto.tipo = "Ingreso"
        foto.clave = clave
        foto.creado_por_id = self.request.user.id
        foto.save()

        preadmi.indice_ingreso = "SI"
        preadmi.save()

        #---------HISTORIAL---------------------------------
        pk=self.kwargs["pk"]
        base = MA_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "CREACION INDICE INGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('MA_indiceingreso_ver', preadmi.id)

class MAIndiceIngresoUpdateView (PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/indiceingreso_edit.html"
    model = MA_PreAdmision
    form_class = MA_IndiceIngresoForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        activos = MA_IndiceIngreso.objects.filter(fk_preadmi_id=pk)
        observaciones = MA_Foto_Ingreso.objects.filter(fk_preadmi_id=pk).first()

        context = super().get_context_data(**kwargs)
        context["object"] = MA_PreAdmision.objects.filter(pk=pk).first()
        context["activos"] = activos
        context["clave"] = observaciones.clave
        context["observaciones"] = observaciones.observaciones
        context["criterio"] = Criterios_Ingreso.objects.all()
        context['form2'] = MA_IndiceIngresoHistorialForm()
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        preadmi = MA_PreAdmision.objects.filter(pk=pk).first()
        MA_foto = MA_Foto_IVI.objects.filter(fk_preadmi_id=pk).first()
        clave = MA_foto.clave
        indices_ingreso = MA_IndiceIngreso.objects.filter(clave=clave)
        #MA_foto.delete()
        indices_ingreso.delete()
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_Ingreso.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ingreso = Criterios_Ingreso.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ingreso.puntaje)
                base = MA_IndiceIVI()
                base.fk_criterios_ingreso_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.presencia = True
                base.programa = "MA"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = MA_Foto_Ingreso.objects.filter(clave=clave).first()
        foto.observaciones = request.POST.get('observaciones', '')
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        #foto.crit_modificables = crit_modificables
        #foto.crit_presentes = crit_presentes
        #foto.tipo = "Ingreso"
        #foto.clave = clave
        foto.modificado_por_id = self.request.user.id
        foto.save()

        #---------HISTORIAL---------------------------------
        pk=self.kwargs["pk"]
        preadmi = MA_PreAdmision.objects.filter(pk=pk).first()
        base = MA_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "MODIFICACION INDICE INGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('MA_indiceingreso_ver', preadmi.id)
    
class MAIndiceIngresoDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/indiceingreso_detail.html"
    model = MA_PreAdmision

    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        criterio = MA_IndiceIngreso.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        object = MA_PreAdmision.objects.filter(pk=pk).first()
        foto_ingreso = MA_Foto_Ingreso.objects.filter(fk_preadmi_id=pk, tipo="Ingreso").first()

        context["object"] = object
        context["foto_ingreso"] = foto_ingreso
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ingreso__puntaje'))
        context["cantidad"] = criterio.count()
        context["cant_combinables"] = criterio.filter(fk_criterios_ingreso__tipo='Criterios combinables para el ingreso').count()
        context["cant_sociales"] = criterio.filter(fk_criterios_ingreso__tipo='Criterios sociales para el ingreso').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ingreso__modificable='SI').aggregate(total=Sum('fk_criterios_ingreso__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ingreso__tipo='Ajustes').count()
        #context['maximo'] = foto_ingreso.puntaje_max
        return context
    
#--------- CREAR IVI -------------------------------------

class MACriteriosIVICreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/criterios_ivi_form.html"
    model = Criterios_IVI
    form_class = criterios_IVI

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse('MA_criterios_ivi_crear'))

 
class MAIndiceIviCreateView (PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios_IVI
    template_name = "SIF_MA/indiceivi_form.html"
    form_class = MA_IndiceIviForm    
    
    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        object = MA_PreAdmision.objects.filter(pk=pk).first()
        #object = Legajos.objects.filter(pk=pk).first()
        criterio = Criterios_IVI.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context['form2'] = MA_IndiceIviHistorialForm()
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = MA_PreAdmision.objects.filter(pk=pk).first()
        clave = str(uuid.uuid4())
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = MA_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.tipo = "Ingreso"
                base.presencia = True
                base.programa = "MA"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = MA_Foto_IVI()
        foto.observaciones = request.POST.get('observaciones', '')
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        #foto.crit_modificables = crit_modificables
        #foto.crit_presentes = crit_presentes
        foto.tipo = "Ingreso"
        foto.clave = clave
        foto.creado_por_id = self.request.user.id
        foto.save()

        preadmi.ivi = "SI"
        preadmi.save()

        #---------HISTORIAL---------------------------------
        pk=self.kwargs["pk"]
        base = MA_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "CREACION IVI"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('MA_indiceivi_ver', preadmi.id)


class MAIndiceIviUpdateView (PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/indiceivi_edit.html"
    model = MA_PreAdmision
    form_class = MA_IndiceIviForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        activos = MA_IndiceIVI.objects.filter(fk_preadmi_id=pk)
        observaciones = MA_Foto_IVI.objects.filter(fk_preadmi_id=pk).first()

        context = super().get_context_data(**kwargs)
        context["object"] = MA_PreAdmision.objects.filter(pk=pk).first()
        context["activos"] = activos
        context["clave"] = observaciones.clave
        context["observaciones"] = observaciones.observaciones
        context["criterio"] = Criterios_IVI.objects.all()
        context['form2'] = MA_IndiceIviHistorialForm()
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        preadmi = MA_PreAdmision.objects.filter(pk=pk).first()
        MA_foto = MA_Foto_IVI.objects.filter(fk_preadmi_id=pk).first()
        clave = MA_foto.clave
        indices_ivi = MA_IndiceIVI.objects.filter(clave=clave)
        #MA_foto.delete()
        indices_ivi.delete()
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = MA_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.presencia = True
                base.programa = "MA"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = MA_Foto_IVI.objects.filter(clave=clave).first()
        foto.observaciones = request.POST.get('observaciones', '')
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        #foto.crit_modificables = crit_modificables
        #foto.crit_presentes = crit_presentes
        #foto.tipo = "Ingreso"
        #foto.clave = clave
        foto.modificado_por_id = self.request.user.id
        foto.save()

        #---------HISTORIAL---------------------------------
        pk=self.kwargs["pk"]
        preadmi = MA_PreAdmision.objects.filter(pk=pk).first()
        base = MA_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "MODIFICACION IVI"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('MA_indiceivi_ver', preadmi.id)
    
    
class MAIndiceIviDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/indiceivi_detail.html"
    model = MA_PreAdmision

    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        criterio = MA_IndiceIVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        object = MA_PreAdmision.objects.filter(pk=pk).first()
        foto_ivi = MA_Foto_IVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso").first()

        context["object"] = object
        context["foto_ivi"] = foto_ivi
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable='Si').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable='Si').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        #context['maximo'] = foto_ivi.puntaje_max
        return context
    
class MAPreAdmisiones3DetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/preadmisiones_detail3.html"
    model = MA_PreAdmision

    def get_context_data(self, **kwargs):
        pk = MA_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        criterio = MA_IndiceIVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        criterio_ingreso = MA_IndiceIngreso.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        foto_ivi = MA_Foto_IVI.objects.filter(fk_preadmi_id= pk, tipo="Ingreso").first()
        foto_ingreso = MA_Foto_Ingreso.objects.filter(fk_preadmi_id= pk, tipo="Ingreso").first()

        context["legajo"] = legajo
        context["familia"] = familia
        context["foto_ivi"] = foto_ivi
        context["foto_ingreso"] = foto_ingreso
        context["puntaje"] = foto_ivi.puntaje
        context["puntaje_ingreso"] = foto_ingreso.puntaje
        context["cantidad"] = criterio.count()
        context["cantidad_ingreso"] = criterio_ingreso.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable='SI').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable='SI').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        context['maximo'] = foto_ivi.puntaje_max
        context['maximo_ingreso'] = foto_ingreso.puntaje_max
        context['criterios_total'] = criterio_ingreso.count()
        context["cant_combinables"] = criterio_ingreso.filter(fk_criterios_ingreso__tipo='Criterios combinables para el ingreso').count()
        context["cant_sociales"] = criterio_ingreso.filter(fk_criterios_ingreso__tipo='Criterios sociales para el ingreso').count() 
        context["autonomos"] = criterio_ingreso.filter(fk_criterios_ingreso__tipo='Criteros autónomos de ingreso').all()
        return context
    
    def post(self, request, *args, **kwargs):
        if 'admitir' in request.POST:
            preadmi = MA_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
            preadmi.admitido = "SI"
            preadmi.save()

            base1 = MA_Admision()
            base1.fk_preadmi_id = preadmi.pk
            base1.creado_por_id = self.request.user.id
            base1.save()
            redirigir = base1.pk

            #---------HISTORIAL---------------------------------
            pk=self.kwargs["pk"]
            legajo = MA_PreAdmision.objects.filter(pk=pk).first()
            base = MA_Historial()
            base.fk_legajo_id = legajo.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
            base.fk_preadmi_id = pk
            base.fk_admision_id = redirigir
            base.movimiento = "ADMITIDO"
            base.creado_por_id = self.request.user.id
            base.save()

            # Redirige de nuevo a la vista de detalle actualizada
            return redirect('MA_asignado_admisiones_ver', redirigir)

class MAAdmisionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/adminsiones_list.html"
    model = MA_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        criterio = MA_IndiceIVI.objects.all()
        criterio_ingreso = MA_IndiceIngreso.objects.all()
        admi = MA_Admision.objects.all()
        foto = MA_Foto_IVI.objects.all()
        foto_ingreso = MA_Foto_Ingreso.objects.all()
        conteo = MA_IndiceIngreso.objects.values('fk_preadmi_id').annotate(total=Count('fk_preadmi_id'))

        context ["conteo"] = conteo
        context["admi"] = admi
        context["foto"] = foto
        context["foto_ingreso"] = criterio_ingreso.aggregate(total=Count('fk_criterios_ingreso'))
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["puntaje_ingreso"] = criterio_ingreso.aggregate(total=Sum('fk_criterios_ingreso__puntaje'))
        return context

class MAAdmisionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = MA_Admision
    template_name = 'SIF_MA/admisiones_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = MA_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        preadmi = MA_PreAdmision.objects.filter(pk=pk.fk_preadmi_id).first()
        criterio = MA_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        foto_ivi = MA_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()

        context["foto_ivi"] = foto_ivi
        context["puntaje"] = foto_ivi.puntaje
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable='SI').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable='SI').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        context['maximo'] = foto_ivi.puntaje_max
        
        return context


class MAAsignadoAdmisionDetail(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/asignado_admisiones_detail.html"
    model = MA_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = MA_Admision.objects.filter(pk=self.kwargs["pk"]).first()

        preadmi = MA_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = MA_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        criterio_ingreso = MA_IndiceIngreso.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        criterio2 = MA_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones = MA_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()
        observaciones_ingreso = MA_Foto_Ingreso.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()
        observaciones2 = MA_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()
        intervenciones = MA_Intervenciones.objects.filter(fk_admision_id=admi.id).all()
        intervenciones_last = MA_Intervenciones.objects.filter(fk_admision_id=admi.id).last()
        foto_ivi_fin = MA_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso").last()
        foto_ivi_inicio = MA_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso").first()

        context["foto_ivi_fin"] = foto_ivi_fin
        context["foto_ivi_inicio"] = foto_ivi_inicio
        context["observaciones"] = observaciones
        context["observaciones_ingreso"] = observaciones_ingreso
        context["observaciones2"] = observaciones2
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["cant_ingreso"] = criterio_ingreso.count()
        context["puntaje2"] = criterio2.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["object"] = admi
        context["vo"] = self.object
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last
        
        return context

class MAInactivaAdmisionDetail(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/inactiva_admisiones_detail.html"
    model = MA_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = MA_Admision.objects.filter(pk=self.kwargs["pk"]).first()

        preadmi = MA_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = MA_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Egreso")
        intervenciones = MA_Intervenciones.objects.filter(fk_admision_id=admi.id).all()
        intervenciones_last = MA_Intervenciones.objects.filter(fk_admision_id=admi.id).last()
        foto_ivi_fin = MA_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Egreso").first()
        foto_ivi_inicio = MA_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso").first()

        
        context["foto_ivi_fin"] = foto_ivi_fin
        context["foto_ivi_inicio"] = foto_ivi_inicio
        context["criterio"] = criterio
        context["object"] = admi
        context["vo"] = self.object
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last
        
        return context



class MAIntervencionesCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = MA_Intervenciones  # Debería ser el modelo MA_Intervenciones
    template_name = "SIF_MA/intervenciones_form.html"
    form_class = MA_IntervencionesForm

    def form_valid(self, form):
        form.instance.fk_admision_id = self.kwargs["pk"]
        form.instance.creado_por_id = self.request.user.id
        self.object = form.save()
        
        # --------- HISTORIAL ---------------------------------
        pk = self.kwargs["pk"]
        legajo = MA_Admision.objects.filter(pk=pk).first()
        base = MA_Historial()
        base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
        base.fk_preadmi_id = legajo.fk_preadmi.pk
        base.fk_admision_id = legajo.id  # Cambia a self.object.id
        base.movimiento = "INTERVENCION CREADA"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('MA_intervencion_ver', pk=self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = MA_Admision.objects.get(pk=self.kwargs["pk"])  # Obtén el objeto directamente
        context["form"] = self.get_form()  # Obtiene una instancia del formulario

        return context
    
class MAIntervencionesUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = MA_Intervenciones
    template_name = "SIF_MA/intervenciones_form.html"
    form_class = MA_IntervencionesForm

    def form_valid(self, form):
            pk = MA_Intervenciones.objects.filter(pk=self.kwargs["pk"]).first()
            admi = MA_Admision.objects.filter(id=pk.fk_admision.id).first()
            form.instance.fk_admision_id = admi.id
            form.instance.modificado_por_id = self.request.user.id
            self.object = form.save()
        
            # --------- HISTORIAL ---------------------------------
            pk = self.kwargs["pk"]
            pk = MA_Intervenciones.objects.filter(pk=pk).first()
            legajo = MA_Admision.objects.filter(pk=pk.fk_admision_id).first()
            base = MA_Historial()
            base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
            base.fk_preadmi_id = legajo.fk_preadmi.pk
            base.fk_admision_id = legajo.pk
            base.movimiento = "INTERVENCION MODIFICADA"
            base.creado_por_id = self.request.user.id
            base.save()

            return redirect('MA_intervencion_ver', self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = MA_Intervenciones.objects.filter(pk=self.kwargs["pk"]).first()
        admi = MA_Admision.objects.filter(id=pk.fk_admision.id).first()

        context["object"] = admi

        return context

class MAIntervencionesLegajosListView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/intervenciones_legajo_list.html"
    model = MA_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = MA_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        intervenciones = MA_Intervenciones.objects.filter(fk_admision_id=admi.id).all()
        intervenciones_last = MA_Intervenciones.objects.filter(fk_admision_id=admi.id).last()
        preadmi = MA_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = MA_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones = MA_Foto_IVI.objects.filter(clave=criterio.first().clave, tipo="Ingreso").first()
        criterio2 = MA_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones2 = MA_Foto_IVI.objects.filter(clave=criterio2.last().clave, tipo="Ingreso").first()

        context["object"] = admi
        context["intervenciones"] = intervenciones
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last

        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["observaciones"] = observaciones
        context["observaciones2"] = observaciones2
        context["puntaje2"] = criterio2.aggregate(total=Sum('fk_criterios_ivi__puntaje'))

        return context
    
class MAIntervencionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/intervenciones_list.html"
    model = MA_Intervenciones

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        intervenciones = MA_Intervenciones.objects.all()
        context["intervenciones"] = intervenciones
        return context

class MAIntervencionesDetail (PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/intervencion_detail.html"
    model = MA_Intervenciones

class MAOpcionesResponsablesCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/intervenciones_resposables.html"
    model = OpcionesResponsables
    form_class = MA_OpcionesResponsablesForm

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse('MA_OpcionesResponsables'))

class MAIntervencionesDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = MA_Intervenciones
    template_name = "SIF_MA/intervenciones_confirm_delete.html"
    success_url = reverse_lazy("MA_intervenciones_listar")

    def form_valid(self, form):

        if self.request.user.id != self.object.creado_por.id:
            print(self.request.user)
            print(self.object.creado_por)
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("MA_preadmisiones_ver", pk=int(self.object.id))

        else:
            self.object.delete()
            return redirect(self.success_url)
        

class MAAdmisionesBuscarListView(PermisosMixin, TemplateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_MA/admisiones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = MA_PreAdmision.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            object_list = MA_Admision.objects.filter(Q(fk_preadmi__fk_legajo__apellido__iexact=query) | Q(fk_preadmi__fk_legajo__documento__iexact=query), fk_preadmi__fk_derivacion__fk_programa_id=25).exclude(estado__in=['Rechazada','Aceptada']).distinct()
            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list

        return self.render_to_response(context)
    
class MAIndiceIviEgresoCreateView (PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Legajos
    template_name = "SIF_MA/indiceivi_form_egreso.html"
    form_class = MA_IndiceIviForm
    success_url = reverse_lazy("legajos_listar")
    
    
    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        admi = MA_Admision.objects.filter(pk=pk).first()
        object = Legajos.objects.filter(pk=admi.fk_preadmi.fk_legajo.id).first()
        criterio = Criterios_IVI.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context['form2'] = MA_IndiceIviHistorialForm()
        context['admi'] = admi
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        admi = MA_Admision.objects.filter(pk=pk).first()
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = MA_PreAdmision.objects.filter(fk_legajo_id=admi.fk_preadmi.fk_legajo.id).first()
        foto_ivi = MA_Foto_IVI.objects.filter(fk_preadmi_id=preadmi.id).first()
        clave = foto_ivi.clave
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = MA_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = admi.fk_preadmi.fk_legajo.id
                base.fk_preadmi_id = preadmi.id
                base.tipo = "Egreso"
                base.presencia = True
                base.programa = "MA"
                base.clave = clave
                base.save()

        # total_puntaje contiene la suma de los valores de F
        foto = MA_Foto_IVI()
        foto.observaciones = request.POST.get('observaciones', '')
        foto.fk_preadmi_id = preadmi.id
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        #foto.crit_modificables = crit_modificables
        #foto.crit_presentes = crit_presentes
        foto.tipo = "Egreso"
        foto.clave = clave
        foto.creado_por_id = self.request.user.id
        foto.save()

        admi.estado = "Inactiva"
        admi.modificado_por_id = self.request.user.id
        admi.save()

        #---------HISTORIAL---------------------------------
        pk=self.kwargs["pk"]
        legajo = admi.fk_preadmi
        base = MA_Historial()
        base.fk_legajo_id = legajo.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
        base.fk_preadmi_id = legajo.id
        base.movimiento = "IVI EGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('MA_admisiones_listar')