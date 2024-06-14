from django.views.generic import CreateView,ListView,DetailView,UpdateView,DeleteView,TemplateView, FormView
from Legajos.models import LegajosDerivaciones
from Legajos.forms import DerivacionesRechazoForm
from django.db.models import Q
from .models import *
from Configuraciones.models import *
from .forms import *
from Usuarios.mixins import PermisosMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.db.models import Sum, F, ExpressionWrapper, IntegerField
import uuid
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from SIF_CDLE.models import Criterios_Ingreso


# # Create your views here.
#derivaciones = LegajosDerivaciones.objects.filter(m2m_programas__nombr__iexact="PDV")
#print(derivaciones)

class PDVDerivacionesBuscarListView(TemplateView, PermisosMixin):
    permission_required = "Usuarios.programa_PDV"
    template_name = "SIF_PDV/derivaciones_buscar.html"

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


class PDVDerivacionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/derivaciones_bandeja_list.html"
    queryset = LegajosDerivaciones.objects.filter(fk_programa=settings.PROG_PDV)

    def get_context_data(self, **kwargs):
        context = super(PDVDerivacionesListView, self).get_context_data(**kwargs)

        model = self.queryset

        query = self.request.GET.get("busqueda")

        if query:
            object_list = LegajosDerivaciones.objects.filter((Q(fk_legajo__apellido__iexact=query) | Q(fk_legajo__nombre__iexact=query)) & Q(fk_programa=settings.PROG_PDV)).distinct()
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

class PDVDerivacionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/derivaciones_detail.html"
    model = LegajosDerivaciones

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk, fk_programa=settings.PROG_PDV).first()
        ivi = PDV_IndiceIVI.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        resultado = ivi.values('clave', 'creado', 'programa').annotate(total=Sum('fk_criterios_ivi__puntaje')).order_by('-creado')
        context["pk"] = pk
        context["ivi"] = ivi
        context["resultado"] = resultado
        return context

class PDVDerivacionesRechazo(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/derivaciones_rechazo.html"
    form_class = DerivacionesRechazoForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk, fk_programa=settings.PROG_PDV).first()
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
        return HttpResponseRedirect(reverse('PDV_derivaciones_listar'))
    
    def form_invalid(self, form):
        return super().form_invalid(form)   
    
    def get_success_url(self):
        return reverse('PDV_derivaciones_listar')

class PDVPreAdmisionesCreateView(PermisosMixin,CreateView, SuccessMessageMixin):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_form.html"
    model = PDV_PreAdmision
    form_class = PDV_PreadmisionesForm
    success_message = "Preadmisión creada correctamente"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        familia_inversa = LegajoGrupoFamiliar.objects.filter(fk_legajo_1_id=legajo.fk_legajo_id)
        centros = Vacantes.objects.filter(fk_programa_id=settings.PROG_PDV)
        context["pk"] = pk
        context["legajo"] = legajo
        context["familia"] = familia
        context["familia_inversa"] = familia_inversa
        context["centros"] = centros
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

        sala = form.cleaned_data['sala_postula']
        taller = form.cleaned_data['taller_postula']

        if sala == 'Bebés' and taller == 'Mañana':
            form.instance.sala_short = 'manianabb'
        elif sala == 'Bebés' and taller == 'Tarde':
            form.instance.sala_short = 'tardebb'
        elif sala == 'Sala de 2' and taller == 'Mañana':
            form.instance.sala_short = 'maniana2'
        elif sala == 'Sala de 2' and taller == 'Tarde':
            form.instance.sala_short = 'tarde2'
        elif sala == 'Sala de 3' and taller == 'Mañana':
            form.instance.sala_short = 'maniana3'
        elif sala == 'Sala de 3' and taller == 'Tarde':
            form.instance.sala_short = 'tarde3'
        self.object = form.save()

        base = LegajosDerivaciones.objects.get(pk=pk)
        base.estado = "Aceptada"
        base.save() 
        
        #---- Historial--------------
        legajo = LegajosDerivaciones.objects.filter(pk=pk).first()
        base = PDV_Historial()
        base.fk_legajo_id = legajo.fk_legajo.id
        base.fk_legajo_derivacion_id = pk
        base.fk_preadmi_id = self.object.id
        base.movimiento = "ACEPTADO A PREADMISION"
        base.creado_por_id = self.request.user.id
        base.save()

        return HttpResponseRedirect(reverse('PDV_preadmisiones_ver', args=[self.object.pk]))

class PDVPreAdmisionesUpdateView(PermisosMixin,UpdateView, SuccessMessageMixin):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_form.html"
    model = PDV_PreAdmision
    form_class = PDV_PreadmisionesForm
    success_message = "Preadmisión creada correctamente"

    def get_context_data(self, **kwargs):
        pk = PDV_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        familia_inversa = LegajoGrupoFamiliar.objects.filter(fk_legajo_1_id=legajo.fk_legajo_id)
        centros = Vacantes.objects.filter(fk_programa_id=settings.PROG_PDV)

        context["pk"] = pk.fk_derivacion_id
        context["legajo"] = legajo
        context["familia"] = familia
        context["familia_inversa"] = familia_inversa
        context["centros"] = centros
        return context

    def form_valid(self, form):
        pk = PDV_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        form.instance.creado_por_id = pk.creado_por_id
        form.instance.vinculo1 = form.cleaned_data['vinculo1']
        form.instance.vinculo2 = form.cleaned_data['vinculo2']
        form.instance.vinculo3 = form.cleaned_data['vinculo3']
        form.instance.vinculo4 = form.cleaned_data['vinculo4']
        form.instance.vinculo5 = form.cleaned_data['vinculo5']
        form.instance.estado = pk.estado
        form.instance.modificado_por_id = self.request.user.id
        sala = form.cleaned_data['sala_postula']
        taller = form.cleaned_data['taller_postula']
        if sala == 'Bebés' and taller == 'Mañana':
            form.instance.sala_short = 'manianabb'
        elif sala == 'Bebés' and taller == 'Tarde':
            form.instance.sala_short = 'tardebb'
        elif sala == 'Sala de 2' and taller == 'Mañana':
            form.instance.sala_short = 'maniana2'
        elif sala == 'Sala de 2' and taller == 'Tarde':
            form.instance.sala_short = 'tarde2'
        elif sala == 'Sala de 3' and taller == 'Mañana':
            form.instance.sala_short = 'maniana3'
        elif sala == 'Sala de 3' and taller == 'Tarde':
            form.instance.sala_short = 'tarde3'
        self.object = form.save()

        return HttpResponseRedirect(reverse('PDV_preadmisiones_ver', args=[self.object.pk]))

class PDVPreAdmisionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_detail.html"
    model = PDV_PreAdmision

    def get_context_data(self, **kwargs):
        pk = PDV_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        ivi = PDV_IndiceIVI.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        ingreso = PDV_IndiceIngreso.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        resultado = ivi.filter(tipo='Ingreso').values('clave', 'creado', 'programa').annotate(total=Sum('fk_criterios_ivi__puntaje')).order_by('-creado')
        resultado_ingreso = ingreso.filter(tipo='Ingreso').values('clave', 'creado', 'programa').annotate(total=Sum('fk_criterios_ingreso__puntaje')).order_by('-creado')
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
            legajo = PDV_PreAdmision.objects.filter(pk=pk).first()
            base = PDV_Historial()
            base.fk_legajo_id = legajo.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
            base.fk_preadmi_id = pk
            base.movimiento = "FINALIZADO PREADMISION"
            base.creado_por_id = self.request.user.id
            base.save()
            # Redirige de nuevo a la vista de detalle actualizada
            return HttpResponseRedirect(self.request.path_info)

            

            


            # Redirige de nuevo a la vista de detalle actualizada
            return HttpResponseRedirect(self.request.path_info)
        

        


class PDVPreAdmisionesDetailView2(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_detail2.html"
    model = PDV_PreAdmision

    def get_context_data(self, **kwargs):
        pk = PDV_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        ivi = PDV_IndiceIVI.objects.filter(fk_legajo_id=legajo.fk_legajo_id)
        foto_ivi = PDV_Foto_IVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso").first()

       
        context["foto_ivi"] = foto_ivi
        resultado = ivi.values('clave', 'creado', 'programa').annotate(total=Sum('fk_criterios_ivi__puntaje')).order_by('-creado')
        context["ivi"] = ivi
        context["resultado"] = resultado
        context["legajo"] = legajo
        context["familia"] = familia

        return context
    
    def post(self, request, *args, **kwargs):
        if 'finalizar_preadm' in request.POST:
            # Realiza la actualización del campo aquí
            objeto = self.get_object()
            objeto.estado = 'Finalizada'
            objeto.ivi = "NO"
            objeto.admitido = "NO"
            objeto.save()
            # Obtén el valor de autovaloracion y almacénalo en una variable de sesión
            respuesta_autovaloracion = request.POST.get('autovaloracion', '')
            request.session['respuesta_autovaloracion'] = respuesta_autovaloracion
            #---------HISTORIAL---------------------------------
            pk=self.kwargs["pk"]
            legajo = PDV_PreAdmision.objects.filter(pk=pk).first()
            base = PDV_Historial()
            base.fk_legajo_id = legajo.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
            base.fk_preadmi_id = pk
            base.movimiento = "FINALIZADO PREADMISION"
            base.creado_por_id = self.request.user.id
            base.save()


            # Redirige de nuevo a la vista de detalle actualizada
            return HttpResponseRedirect(self.request.path_info)
            

class PDVPreAdmisionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_list.html"
    model = PDV_PreAdmision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pre_admi = PDV_PreAdmision.objects.all()
        context["object"] = pre_admi
        return context

class PDVPreAdmisionesBuscarListView(PermisosMixin, TemplateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = PDV_PreAdmision.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            object_list = PDV_PreAdmision.objects.filter(Q(fk_legajo__apellido__iexact=query) | Q(fk_legajo__documento__iexact=query), fk_derivacion__fk_programa_id=settings.PROG_PDV).exclude(estado__in=['Rechazada','Aceptada']).distinct()
            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list

        return self.render_to_response(context)

class PDVPreAdmisionesDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = PDV_PreAdmision
    template_name = "SIF_PDV/preadmisiones_confirm_delete.html"
    success_url = reverse_lazy("PDV_preadmisiones_listar")

    def form_valid(self, form):
        if self.object.estado != "En proceso":
            messages.error(
                self.request,
                "No es posible eliminar una solicitud en estado " + self.object.estado,
            )

            return redirect("PDV_preadmisiones_ver", pk=int(self.object.id))

        if self.request.user.id != self.object.creado_por.id:
            print(self.request.user)
            print(self.object.creado_por)
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("PDV_preadmisiones_ver", pk=int(self.object.id))

        else:
            self.object.delete()
            return redirect(self.success_url)
        
class PDVCriteriosIngresoCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/criterios_ingreso_form.html"
    model = Criterios_Ingreso
    form_class = criterios_Ingreso

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse('PDV_criterios_ingreso_crear'))
    
class PDVIndiceIngresoCreateView (PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios_Ingreso
    template_name = "SIF_PDV/indiceingreso_form.html"
    form_class = PDV_IndiceIngresoForm    
    
    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        object = PDV_PreAdmision.objects.filter(pk=pk).first()
        #object = Legajos.objects.filter(pk=pk).first()
        criterio = Criterios_Ingreso.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context['form2'] = PDV_IndiceIngresoHistorialForm()
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = PDV_PreAdmision.objects.filter(pk=pk).first()
        clave = str(uuid.uuid4())
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_Ingreso.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ingreso = Criterios_Ingreso.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ingreso.puntaje)
                base = PDV_IndiceIngreso()
                base.fk_criterios_ingreso_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.tipo = "Ingreso"
                base.presencia = True
                base.programa = "PDV"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = PDV_Foto_Ingreso()
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
        base = PDV_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "CREACION INDICE INGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('PDV_indiceingreso_ver', preadmi.id)

class PDVIndiceIngresoUpdateView (PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/indiceingreso_edit.html"
    model = PDV_PreAdmision
    form_class = PDV_IndiceIngresoForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        activos = PDV_IndiceIngreso.objects.filter(fk_preadmi_id=pk)
        observaciones = PDV_Foto_Ingreso.objects.filter(fk_preadmi_id=pk).first()

        context = super().get_context_data(**kwargs)
        context["object"] = PDV_PreAdmision.objects.filter(pk=pk).first()
        context["activos"] = activos
        context["clave"] = observaciones.clave
        context["observaciones"] = observaciones.observaciones
        context["criterio"] = Criterios_Ingreso.objects.all()
        context['form2'] = PDV_IndiceIngresoHistorialForm()
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        preadmi = PDV_PreAdmision.objects.filter(pk=pk).first()
        PDV_foto = PDV_Foto_Ingreso.objects.filter(fk_preadmi_id=pk).first()
        clave = PDV_foto.clave
        indices_ingreso = PDV_IndiceIngreso.objects.filter(clave=clave)
        #PDV_foto.delete()
        indices_ingreso.delete()
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_Ingreso.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ingreso = Criterios_Ingreso.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ingreso.puntaje)
                base = PDV_IndiceIngreso()
                base.fk_criterios_ingreso_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.presencia = True
                base.tipo = "Ingreso"
                base.programa = "PDV"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = PDV_Foto_Ingreso.objects.filter(clave=clave).first()
        foto.observaciones = request.POST.get('observaciones', '')
        foto.fk_preadmi_id = pk
        foto.fk_legajo_id = preadmi.fk_legajo_id
        foto.puntaje = total_puntaje
        foto.puntaje_max = puntaje_maximo
        #foto.crit_modificables = crit_modificables
        #foto.crit_presentes = crit_presentes
        foto.tipo = "Ingreso"
        foto.clave = clave
        foto.modificado_por_id = self.request.user.id
        foto.save()

        #---------HISTORIAL---------------------------------
        pk=self.kwargs["pk"]
        preadmi = PDV_PreAdmision.objects.filter(pk=pk).first()
        base = PDV_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "MODIFICACION INDICE INGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('PDV_indiceingreso_ver', preadmi.id)
    
class PDVIndiceIngresoDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/indiceingreso_detail.html"
    model = PDV_PreAdmision

    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        criterio = PDV_IndiceIngreso.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        object = PDV_PreAdmision.objects.filter(pk=pk).first()
        foto_ingreso = PDV_Foto_Ingreso.objects.filter(fk_preadmi_id=pk, tipo="Ingreso").first()
        

        context["object"] = object
        context["foto_ingreso"] = foto_ingreso
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ingreso__puntaje'))
        context["cantidad"] = criterio.count()
        context["cant_combinables"] = criterio.filter(fk_criterios_ingreso__tipo='Criterios combinables para el ingreso').count()
        context["cant_sociales"] = criterio.filter(fk_criterios_ingreso__tipo='Criterios sociales para el ingreso').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ingreso__modificable__icontains='si').aggregate(total=Sum('fk_criterios_ingreso__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ingreso__tipo='Ajustes').count()
        #context['maximo'] = foto_ingreso.puntaje_max
       
        return context

#--------- CREAR IVI -------------------------------------

class PDVCriteriosIVICreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/criterios_ivi_form.html"
    model = Criterios_IVI
    form_class = criterios_IVI

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse('PDV_criterios_ivi_crear'))

 
class PDVIndiceIviCreateView (PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Criterios_IVI
    template_name = "SIF_PDV/indiceivi_form.html"
    form_class = PDV_IndiceIviForm    
    
    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        object = PDV_PreAdmision.objects.filter(pk=pk).first()
        #object = Legajos.objects.filter(pk=pk).first()
        criterio = Criterios_IVI.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context['form2'] = PDV_IndiceIviHistorialForm()
        context['CHOICE_CONCEPTIVO'] = CHOICE_CONCEPTIVO
        context['CHOICE_CALIFICAR'] = CHOICE_CALIFICAR
        context['CHOICE_VALORACION'] = CHOICE_VALORACION
        context['CHOICE_GESTION'] = CHOICE_GESTION
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = PDV_PreAdmision.objects.filter(pk=pk).first()
        clave = str(uuid.uuid4())
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = PDV_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.tipo = "Ingreso"
                base.presencia = True
                base.programa = "PDV"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = PDV_Foto_IVI()
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
        base = PDV_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "CREACION IVI"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('PDV_indiceivi_ver', preadmi.id)


class PDVIndiceIviUpdateView (PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/indiceivi_edit.html"
    model = PDV_PreAdmision
    form_class = PDV_IndiceIviForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        activos = PDV_IndiceIVI.objects.filter(fk_preadmi_id=pk)
        observaciones = PDV_Foto_IVI.objects.filter(fk_preadmi_id=pk).first()

        context = super().get_context_data(**kwargs)
        context["object"] = PDV_PreAdmision.objects.filter(pk=pk).first()
        context["activos"] = activos
        context["clave"] = observaciones.clave
        context["observaciones"] = observaciones.observaciones
        context["criterio"] = Criterios_IVI.objects.all()
        context['form2'] = PDV_IndiceIviHistorialForm()
        context['CHOICE_CONCEPTIVO'] = CHOICE_CONCEPTIVO
        context['CHOICE_CALIFICAR'] = CHOICE_CALIFICAR
        context['CHOICE_VALORACION'] = CHOICE_VALORACION
        context['CHOICE_GESTION'] = CHOICE_GESTION
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        preadmi = PDV_PreAdmision.objects.filter(pk=pk).first()
        PDV_foto = PDV_Foto_IVI.objects.filter(fk_preadmi_id=pk).first()
        clave = PDV_foto.clave
        indices_ivi = PDV_IndiceIVI.objects.filter(clave=clave)
        #PDV_foto.delete()
        indices_ivi.delete()
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = PDV_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = preadmi.fk_legajo_id
                base.fk_preadmi_id = pk
                base.presencia = True
                base.programa = "PDV"
                base.tipo = "Ingreso"
                base.clave = clave
                base.save()
        
        # total_puntaje contiene la suma de los valores de F
        foto = PDV_Foto_IVI.objects.filter(clave=clave).first()
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
        preadmi = PDV_PreAdmision.objects.filter(pk=pk).first()
        base = PDV_Historial()
        base.fk_legajo_id = preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = preadmi.fk_derivacion_id
        base.fk_preadmi_id = preadmi.id
        base.movimiento = "MODIFICACION IVI"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('PDV_indiceivi_ver', preadmi.id)
    
    
class PDVIndiceIviDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/indiceivi_detail.html"
    model = PDV_PreAdmision

    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        object = PDV_PreAdmision.objects.filter(pk=pk).first()
        foto_ivi = PDV_Foto_IVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso").first()

        context["object"] = object
        context["foto_ivi"] = foto_ivi
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable__icontains='si').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable__icontains='si').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        #context['maximo'] = foto_ivi.puntaje_max
        return context

class PDVPreAdmisiones2DetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_detail2.html"
    model = PDV_PreAdmision  
    
class PDVPreAdmisiones3DetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/preadmisiones_detail3.html"
    model = PDV_PreAdmision

    def get_context_data(self, **kwargs):
        pk = PDV_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(pk=pk.fk_derivacion_id).first()
        familia = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo.fk_legajo_id)
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=pk, tipo="Ingreso")
        foto_ivi = PDV_Foto_IVI.objects.filter(fk_preadmi_id= pk, tipo="Ingreso").first()

        context["legajo"] = legajo
        context["familia"] = familia
        context["foto_ivi"] = foto_ivi
        context["puntaje"] = foto_ivi.puntaje
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        context['maximo'] = foto_ivi.puntaje_max
        return context
    
    def post(self, request, *args, **kwargs):
        if 'admitir' in request.POST:
            preadmi = PDV_PreAdmision.objects.filter(pk=self.kwargs["pk"]).first()
            preadmi.admitido = "SI"
            preadmi.save()

            base1 = PDV_Admision()
            base1.fk_preadmi_id = preadmi.pk
            base1.estado_vacante = "Lista de espera"
            base1.creado_por_id = self.request.user.id
            base1.save()
            redirigir = base1.pk

            #---------HISTORIAL---------------------------------
            pk=self.kwargs["pk"]
            legajo = PDV_PreAdmision.objects.filter(pk=pk).first()
            base = PDV_Historial()
            base.fk_legajo_id = legajo.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
            base.fk_preadmi_id = pk
            base.fk_admision_id = redirigir
            base.movimiento = "ADMITIDO"
            base.creado_por_id = self.request.user.id
            base.save()

            # Redirige de nuevo a la vista de detalle actualizada
            return redirect('PDV_admisiones_ver', redirigir)

class PDVAdmisionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/adminsiones_list.html"
    model = PDV_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        criterio = PDV_IndiceIVI.objects.all()
        admi = PDV_Admision.objects.all()
        foto = PDV_Foto_IVI.objects.all()

        context["admi"] = admi
        context["foto"] = foto
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        return context

class PDVAdmisionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = PDV_Admision
    template_name = 'SIF_PDV/admisiones_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = PDV_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        preadmi = PDV_PreAdmision.objects.filter(pk=pk.fk_preadmi_id).first()
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        foto_ivi = PDV_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()

        context["foto_ivi"] = foto_ivi
        context["puntaje"] = foto_ivi.puntaje
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        context['maximo'] = foto_ivi.puntaje_max
        
        return context

class PDVVacantesAdmision(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = PDV_Admision
    template_name = "SIF_PDV/vacantes_form.html"
    form_class = PDV_VacantesOtorgadasForm

    def form_valid(self, form):
        fk_organismo2 = form.cleaned_data['fk_organismo2']
        fk_organismo = form.cleaned_data['fk_organismo']
        turno = form.cleaned_data['turno']
        # if sala == 'Bebe' and turno == 'Mañana':
        #     form.instance.salashort = 'manianabb'
        # elif sala == 'Bebe' and turno == 'Tarde':
        #     form.instance.salashort = 'tardebb'
        # elif sala == '2' and turno == 'Mañana':
        #     form.instance.salashort = 'maniana2'
        # elif sala == '2' and turno == 'Tarde':
        #     form.instance.salashort = 'tarde2'
        # elif sala == '3' and turno == 'Mañana':
        #     form.instance.salashort = 'maniana3'
        # elif sala == '3' and turno == 'Tarde':
        #     form.instance.salashort = 'tarde3'
        self.object = form.save()
    
        base1 = PDV_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        base1.estado_vacante = "Finalizada"
        base1.save()
        
        # --------- HISTORIAL ---------------------------------
        pk = self.kwargs["pk"]
        legajo = PDV_Admision.objects.filter(pk=pk).first()
        base = PDV_Historial()
        base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
        base.fk_preadmi_id = legajo.fk_preadmi.pk
        base.fk_admision_id = pk
        base.movimiento = "VACANTE OTORGADA"
        base.creado_por_id = self.request.user.id
        base.save()
        
        return redirect('PDV_asignado_admisiones_ver', legajo.pk)

    def form_invalid(self, form):
        errors = form.errors
        print(errors)
        return super().form_invalid(form) 
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = PDV_Admision.objects.filter(pk=self.kwargs["pk"]).first()

        preadmi = PDV_PreAdmision.objects.filter(pk=pk.fk_preadmi_id).first()
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        foto_ivi = PDV_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()

        context["object"] = pk
        context["foto_ivi"] = foto_ivi
        context["puntaje"] = foto_ivi.puntaje
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        context['maximo'] = foto_ivi.puntaje_max
        
        return context

class PDVVacantesAdmisionCambio(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = PDV_Admision
    template_name = "SIF_PDV/vacantes_form_cambio.html"
    form_class = PDV_VacantesOtorgadasForm

    def form_valid(self, form):
        if form.cleaned_data['fecha_egreso'] == None:
            messages.error(self.request, 'El campo fecha de egreso es requerido.')
            return super().form_invalid(form) 
        else:
            form.evento = "CambioVacante"
            # sala = form.cleaned_data['sala']
            fk_organismo2 = form.cleaned_data['fk_organismo2']
            fk_organismo = form.cleaned_data['fk_organismo']
            turno = form.cleaned_data['turno']
            

            # if sala == 'Bebe' and turno == 'Mañana':
            #     form.instance.salashort = 'manianabb'
            # elif sala == 'Bebe' and turno == 'Tarde':
            #     form.instance.salashort = 'tardebb'
            # elif sala == '2' and turno == 'Mañana':
            #     form.instance.salashort = 'maniana2'
            # elif sala == '2' and turno == 'Tarde':
            #     form.instance.salashort = 'tarde2'
            # elif sala == '3' and turno == 'Mañana':
            #     form.instance.salashort = 'maniana3'
            # elif sala == '3' and turno == 'Tarde':
            #     form.instance.salashort = 'tarde3'
            self.object = form.save()

        
            # --------- HISTORIAL ---------------------------------
            pk = self.kwargs["pk"]
            legajo = PDV_Admision.objects.filter(pk=pk).first()
            base = PDV_Historial()
            base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
            base.fk_preadmi_id = legajo.fk_preadmi.pk
            base.fk_admision_id = pk
            base.movimiento = "CAMBIO VACANTE"
            base.creado_por_id = self.request.user.id
            base.save()

        return redirect('PDV_asignado_admisiones_ver', legajo.id)
    
    def form_invalid(self, form):
        errors = form.errors
        #print(errors)
        messages.error(self.request, errors)
        return super().form_invalid(form) 
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = PDV_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        vacante_otorgada = PDV_VacantesOtorgadas.objects.filter(fk_admision_id=self.kwargs["pk"]).first()

        preadmi = PDV_PreAdmision.objects.filter(pk=pk.fk_preadmi_id).first()
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        foto_ivi = PDV_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()

        context["object"] = pk
        context["observaciones"] = foto_ivi
        context["puntaje"] = foto_ivi.puntaje
        context["cantidad"] = criterio.count()
        context["modificables"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').count()
        context["mod_puntaje"] = criterio.filter(fk_criterios_ivi__modificable__iexact='SI').aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["ajustes"] = criterio.filter(fk_criterios_ivi__tipo='Ajustes').count()
        context['maximo'] = foto_ivi.puntaje_max
        context["vo"] = vacante_otorgada
        
        return context

class PDVAsignadoAdmisionDetail(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/asignado_admisiones_detail.html"
    model = PDV_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = PDV_Admision.objects.filter(pk=self.kwargs["pk"]).first()

        preadmi = PDV_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        criterio2 = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones = PDV_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()
        observaciones2 = PDV_Foto_IVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso").first()
        lastVO = PDV_VacantesOtorgadas.objects.filter(fk_admision_id=admi.id).last()
        movimientosVO =  PDV_VacantesOtorgadas.objects.filter(fk_admision_id=admi.id).all()
        intervenciones = PDV_Intervenciones.objects.filter(fk_admision_id=admi.id).all()
        intervenciones_last = PDV_Intervenciones.objects.filter(fk_admision_id=admi.id).last()
        foto_ivi_fin = PDV_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso").last()
        foto_ivi_inicio = PDV_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso").first()

        context["foto_ivi_fin"] = foto_ivi_fin
        context["foto_ivi_inicio"] = foto_ivi_inicio
        context["observaciones"] = observaciones
        context["observaciones2"] = observaciones2
        context["criterio"] = criterio
        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["puntaje2"] = criterio2.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["object"] = admi
        context["vo"] = self.object
        context["lastvo"] = lastVO
        context["movimientosVO"] = movimientosVO
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last
        
        return context

class PDVInactivaAdmisionDetail(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/inactiva_admisiones_detail.html"
    model = PDV_Admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = PDV_Admision.objects.filter(pk=self.kwargs["pk"]).first()

        preadmi = PDV_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Egreso")
        lastVO = PDV_VacantesOtorgadas.objects.filter(fk_admision_id=admi.id).last()
        movimientosVO =  PDV_VacantesOtorgadas.objects.filter(fk_admision_id=admi.id).all()
        intervenciones = PDV_Intervenciones.objects.filter(fk_admision_id=admi.id).all()
        intervenciones_last = PDV_Intervenciones.objects.filter(fk_admision_id=admi.id).last()
        foto_ivi_fin = PDV_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Egreso").first()
        foto_ivi_inicio = PDV_Foto_IVI.objects.filter(fk_preadmi_id=admi.fk_preadmi_id, tipo="Ingreso").first()

        
        context["foto_ivi_fin"] = foto_ivi_fin
        context["foto_ivi_inicio"] = foto_ivi_inicio
        context["criterio"] = criterio
        context["object"] = admi
        context["vo"] = self.object
        context["lastvo"] = lastVO
        context["movimientosVO"] = movimientosVO
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last
        
        return context


class PDVVacantesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    model = Vacantes
    template_name = 'SIF_PDV/vacantes_list.html'
    context_object_name = 'organizaciones'
    
    
    def get_queryset(self):
        # org = Vacantes.objects.values_list('fk_organismo', flat=True).distinct()
        # organizaciones = Organismos.objects.filter(id__in=org)
        organizaciones = Vacantes.objects.values_list('fk_organismo', flat=True).distinct()
        organizaciones = Organismos.objects.filter(id__in=organizaciones)
        data = []

        for organizacion in organizaciones:
            organizacion_data = {'organizacion': organizacion}

            # Calcular la cantidad de vacantes por sala agrupadas
            for sala_group in [['manianabb', 'tardebb'], ['maniana2', 'tarde2'], ['maniana3', 'tarde3']]:
                total_vacantes = Vacantes.objects.filter(fk_organismo=organizacion).aggregate(
                    total=Sum(F(sala_group[0]) + F(sala_group[1]))
                )['total'] or 0

                asignadas = PDV_VacantesOtorgadas.objects.filter(
                    fk_organismo__nombre=organizacion,
                    salashort__in=sala_group
                ).count()

                disponibles = PDV_Admision.objects.filter(
                    fk_preadmi__centro_postula__nombre=organizacion,
                    fk_preadmi__sala_short__in=sala_group,
                    estado_vacante='Lista de espera'
                ).count()

                organizacion_data['_'.join(sala_group) + '_total'] = total_vacantes
                organizacion_data['_'.join(sala_group) + '_asignadas'] = asignadas
                organizacion_data['_'.join(sala_group) + '_disponibles'] = disponibles

            # Calcular los totales de vacantes, asignadas y disponibles por organización
            total_vacantes_org = sum([organizacion_data['_'.join(sala_group) + '_total'] for sala_group in [['manianabb', 'tardebb'], ['maniana2', 'tarde2'], ['maniana3', 'tarde3']]])
            total_asignadas_org = sum([organizacion_data['_'.join(sala_group) + '_asignadas'] for sala_group in [['manianabb', 'tardebb'], ['maniana2', 'tarde2'], ['maniana3', 'tarde3']]])
            total_disponibles_org = sum([organizacion_data['_'.join(sala_group) + '_disponibles'] for sala_group in [['manianabb', 'tardebb'], ['maniana2', 'tarde2'], ['maniana3', 'tarde3']]])

            organizacion_data['total_vacantes'] = total_vacantes_org
            organizacion_data['total_asignadas'] = total_asignadas_org
            organizacion_data['total_disponibles'] = total_disponibles_org

            data.append(organizacion_data)

        return data
    
    #def get_context_data(self, **kwargs):
    #    context = super().get_context_data(**kwargs)
    #    context['organizaciones'] = self.get_queryset()
    #    print(context)
    #    return context

class PDVVacantesDetailView (PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/vacantes_detail.html"
    model = Vacantes
    

class PDVIntervencionesCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = PDV_Intervenciones  # Debería ser el modelo PDV_Intervenciones
    template_name = "SIF_PDV/intervenciones_form.html"
    form_class = PDV_IntervencionesForm

    def form_valid(self, form):
        form.instance.fk_admision_id = self.kwargs["pk"]
        form.instance.creado_por_id = self.request.user.id
        self.object = form.save()
        
        # --------- HISTORIAL ---------------------------------
        pk = self.kwargs["pk"]
        legajo = PDV_Admision.objects.filter(pk=pk).first()
        base = PDV_Historial()
        base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
        base.fk_preadmi_id = legajo.fk_preadmi.pk
        base.fk_admision_id = legajo.id  # Cambia a self.object.id
        base.movimiento = "INTERVENCION CREADA"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('PDV_intervencion_ver', pk=self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = PDV_Admision.objects.get(pk=self.kwargs["pk"])  # Obtén el objeto directamente
        context["form"] = self.get_form()  # Obtiene una instancia del formulario

        return context
    
class PDVIntervencionesUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = PDV_Intervenciones
    template_name = "SIF_PDV/intervenciones_form.html"
    form_class = PDV_IntervencionesForm

    def form_valid(self, form):
            pk = PDV_Intervenciones.objects.filter(pk=self.kwargs["pk"]).first()
            admi = PDV_Admision.objects.filter(id=pk.fk_admision.id).first()
            form.instance.fk_admision_id = admi.id
            form.instance.modificado_por_id = self.request.user.id
            self.object = form.save()
        
            # --------- HISTORIAL ---------------------------------
            pk = self.kwargs["pk"]
            pk = PDV_Intervenciones.objects.filter(pk=pk).first()
            legajo = PDV_Admision.objects.filter(pk=pk.fk_admision_id).first()
            base = PDV_Historial()
            base.fk_legajo_id = legajo.fk_preadmi.fk_legajo.id
            base.fk_legajo_derivacion_id = legajo.fk_preadmi.fk_derivacion_id
            base.fk_preadmi_id = legajo.fk_preadmi.pk
            base.fk_admision_id = legajo.pk
            base.movimiento = "INTERVENCION MODIFICADA"
            base.creado_por_id = self.request.user.id
            base.save()

            return redirect('PDV_intervencion_ver', self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = PDV_Intervenciones.objects.filter(pk=self.kwargs["pk"]).first()
        admi = PDV_Admision.objects.filter(id=pk.fk_admision.id).first()

        context["object"] = admi

        return context

class PDVIntervencionesLegajosListView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/intervenciones_legajo_list.html"
    model = PDV_Admision
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admi = PDV_Admision.objects.filter(pk=self.kwargs["pk"]).first()
        lastVO = PDV_VacantesOtorgadas.objects.filter(fk_admision_id=admi.id).last()
        intervenciones = PDV_Intervenciones.objects.filter(fk_admision_id=admi.id).all()
        intervenciones_last = PDV_Intervenciones.objects.filter(fk_admision_id=admi.id).last()
        preadmi = PDV_PreAdmision.objects.filter(pk=admi.fk_preadmi_id).first()
        criterio = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones = PDV_Foto_IVI.objects.filter(clave=criterio.first().clave, tipo="Ingreso").first()
        criterio2 = PDV_IndiceIVI.objects.filter(fk_preadmi_id=preadmi, tipo="Ingreso")
        observaciones2 = PDV_Foto_IVI.objects.filter(clave=criterio2.last().clave, tipo="Ingreso").first()

        context["object"] = admi
        context["lastvo"] = lastVO
        context["intervenciones"] = intervenciones
        context["intervenciones_count"] = intervenciones.count()
        context["intervenciones_last"] = intervenciones_last

        context["puntaje"] = criterio.aggregate(total=Sum('fk_criterios_ivi__puntaje'))
        context["observaciones"] = observaciones
        context["observaciones2"] = observaciones2
        context["puntaje2"] = criterio2.aggregate(total=Sum('fk_criterios_ivi__puntaje'))

        return context
    
class PDVIntervencionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/intervenciones_list.html"
    model = PDV_Intervenciones

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        intervenciones = PDV_Intervenciones.objects.all()
        context["intervenciones"] = intervenciones
        return context

class PDVIntervencionesDetail (PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/intervencion_detail.html"
    model = PDV_Intervenciones

class PDVOpcionesResponsablesCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/intervenciones_resposables.html"
    model = OpcionesResponsables
    form_class = PDV_OpcionesResponsablesForm

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse('PDV_OpcionesResponsables'))

class PDVIntervencionesDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = PDV_Intervenciones
    template_name = "SIF_PDV/intervenciones_confirm_delete.html"
    success_url = reverse_lazy("PDV_intervenciones_listar")

    def form_valid(self, form):

        if self.request.user.id != self.object.creado_por.id:
            print(self.request.user)
            print(self.object.creado_por)
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("PDV_preadmisiones_ver", pk=int(self.object.id))

        else:
            self.object.delete()
            return redirect(self.success_url)
        

class PDVAdmisionesBuscarListView(PermisosMixin, TemplateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "SIF_PDV/admisiones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = PDV_PreAdmision.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            object_list = PDV_Admision.objects.filter(Q(fk_preadmi__fk_legajo__apellido__iexact=query) | Q(fk_preadmi__fk_legajo__documento__iexact=query), fk_preadmi__fk_derivacion__fk_programa_id=settings.PROG_PDV).exclude(estado__in=['Rechazada','Aceptada']).distinct()
            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list

        return self.render_to_response(context)
    
class PDVIndiceIviEgresoCreateView (PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Legajos
    template_name = "SIF_PDV/indiceivi_form_egreso.html"
    form_class = PDV_IndiceIviForm
    success_url = reverse_lazy("legajos_listar")
    
    
    def get_context_data(self, **kwargs):
        pk=self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        admi = PDV_Admision.objects.filter(pk=pk).first()
        object = Legajos.objects.filter(pk=admi.fk_preadmi.fk_legajo.id).first()
        criterio = Criterios_IVI.objects.all()
        context["object"] = object
        context["criterio"] = criterio
        context['form2'] = PDV_IndiceIviHistorialForm()
        return context
    
    def post(self, request, *args, **kwargs):
        pk=self.kwargs["pk"]
        admi = PDV_Admision.objects.filter(pk=pk).first()
        # Genera una clave única utilizando uuid4 (versión aleatoria)
        preadmi = PDV_PreAdmision.objects.filter(fk_legajo_id=admi.fk_preadmi.fk_legajo.id).first()
        foto_ivi = PDV_Foto_IVI.objects.filter(fk_preadmi_id=preadmi.id).first()
        clave = foto_ivi.clave
        nombres_campos = request.POST.keys()
        puntaje_maximo = Criterios_IVI.objects.aggregate(total=Sum('puntaje'))['total']
        total_puntaje = 0
        for f in nombres_campos:
            if f.isdigit():
                criterio_ivi = Criterios_IVI.objects.filter(id=f).first()
                # Sumar el valor de f al total_puntaje
                total_puntaje += int(criterio_ivi.puntaje)
                base = PDV_IndiceIVI()
                base.fk_criterios_ivi_id = f
                base.fk_legajo_id = admi.fk_preadmi.fk_legajo.id
                base.fk_preadmi_id = preadmi.id
                base.tipo = "Egreso"
                base.presencia = True
                base.programa = "PDV"
                base.clave = clave
                base.save()

        # total_puntaje contiene la suma de los valores de F
        foto = PDV_Foto_IVI()
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
        base = PDV_Historial()
        base.fk_legajo_id = legajo.fk_legajo.id
        base.fk_legajo_derivacion_id = legajo.fk_derivacion_id
        base.fk_preadmi_id = legajo.id
        base.movimiento = "IVI EGRESO"
        base.creado_por_id = self.request.user.id
        base.save()

        return redirect('PDV_admisiones_listar')