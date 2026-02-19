from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .forms import ComunicadoForm, ComunicadoAdjuntoFormSet
from .models import Comunicado, ComunicadoAdjunto, EstadoComunicado, TipoComunicado
from .permissions import (
    can_create_comunicado,
    can_edit_comunicado,
    can_publish_comunicado,
    can_archive_comunicado,
    can_delete_comunicado,
    can_manage_comunicados,
    can_toggle_destacado,
    require_create_permission,
    require_edit_permission,
    require_publish_permission,
    require_archive_permission,
    require_toggle_destacado_permission,
    es_tecnico,
    is_admin,
    get_comedores_del_usuario,
)


class ComunicadoListView(LoginRequiredMixin, ListView):
    """Vista de lista de comunicados publicados (accesible por todos)."""

    template_name = "comunicados/comunicado_list.html"
    context_object_name = "comunicados"
    paginate_by = 20

    def get_queryset(self):
        from django.utils import timezone

        estado = self.request.GET.get("estado", "publicado")

        queryset = Comunicado.objects.select_related(
            "usuario_creador"
        ).filter(
            tipo=TipoComunicado.INTERNO  # Solo comunicados internos en la grilla pública
        )

        if estado == "archivado":
            queryset = queryset.filter(estado=EstadoComunicado.ARCHIVADO)
        else:
            queryset = queryset.filter(estado=EstadoComunicado.PUBLICADO)
            # Excluir vencidos solo para publicados
            queryset = queryset.filter(
                Q(fecha_vencimiento__isnull=True) | Q(fecha_vencimiento__gt=timezone.now())
            )

        # Filtros
        titulo = self.request.GET.get("titulo")
        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)

        # Ordenar: destacados primero, luego por fecha de publicación
        return queryset.order_by("-destacado", "-fecha_publicacion")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_manage"] = can_manage_comunicados(self.request.user)
        ctx["filtro_titulo"] = self.request.GET.get("titulo", "")
        ctx["filtro_estado"] = self.request.GET.get("estado", "publicado")
        return ctx


class ComunicadoGestionListView(LoginRequiredMixin, ListView):
    """Vista de gestión de comunicados (solo usuarios con permisos)."""

    template_name = "comunicados/comunicado_gestion_list.html"
    context_object_name = "comunicados"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_comunicados(request.user):
            raise PermissionDenied("No tiene permisos para gestionar comunicados.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Comunicado.objects.select_related("usuario_creador")
        user = self.request.user

        # Si es técnico (no admin), solo ve comunicados externos de sus comedores
        if es_tecnico(user) and not is_admin(user):
            comedores_usuario = get_comedores_del_usuario(user)
            queryset = queryset.filter(
                tipo=TipoComunicado.EXTERNO,
                comedores__in=comedores_usuario
            ).distinct()

        # Filtros
        titulo = self.request.GET.get("titulo")
        estado = self.request.GET.get("estado")
        tipo = self.request.GET.get("tipo")

        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset.order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_create"] = can_create_comunicado(self.request.user)
        ctx["can_publish"] = can_publish_comunicado(self.request.user)
        ctx["can_archive"] = can_archive_comunicado(self.request.user)
        ctx["can_toggle_destacado"] = can_toggle_destacado(self.request.user)
        ctx["filtro_titulo"] = self.request.GET.get("titulo", "")
        ctx["filtro_estado"] = self.request.GET.get("estado", "")
        ctx["filtro_tipo"] = self.request.GET.get("tipo", "")
        ctx["estados"] = EstadoComunicado.choices
        ctx["tipos"] = TipoComunicado.choices
        ctx["es_tecnico"] = es_tecnico(self.request.user) and not is_admin(self.request.user)
        return ctx



class ComunicadoDetailView(LoginRequiredMixin, DetailView):
    """Vista de detalle de un comunicado."""

    model = Comunicado
    template_name = "comunicados/comunicado_detail.html"
    context_object_name = "comunicado"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_manage"] = can_manage_comunicados(self.request.user)
        ctx["can_edit"] = can_edit_comunicado(self.request.user, self.object)
        ctx["can_publish"] = can_publish_comunicado(self.request.user)
        ctx["can_archive"] = can_archive_comunicado(self.request.user)
        ctx["can_delete"] = can_delete_comunicado(self.request.user, self.object)
        return ctx


class ComunicadoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un comunicado."""

    model = Comunicado
    form_class = ComunicadoForm
    template_name = "comunicados/comunicado_form.html"
    success_url = reverse_lazy("comunicados_gestion")

    def dispatch(self, request, *args, **kwargs):
        require_create_permission(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["adjuntos_formset"] = ComunicadoAdjuntoFormSet(
                self.request.POST, self.request.FILES
            )
        else:
            ctx["adjuntos_formset"] = ComunicadoAdjuntoFormSet()
        ctx["titulo_pagina"] = "Crear Comunicado"
        ctx["is_edit"] = False
        ctx["es_tecnico"] = es_tecnico(self.request.user) and not is_admin(self.request.user)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        adjuntos_formset = ctx["adjuntos_formset"]

        form.instance.usuario_creador = self.request.user
        form.instance.estado = EstadoComunicado.BORRADOR

        if adjuntos_formset.is_valid():
            self.object = form.save()
            adjuntos_formset.instance = self.object
            adjuntos_formset.save()

            # Manejar relación con comedores para comunicados externos
            self._handle_comedores(form)

            # Manejar archivos múltiples del campo archivos_adjuntos
            archivos = self.request.FILES.getlist("archivos_adjuntos")
            for archivo in archivos:
                ComunicadoAdjunto.objects.create(
                    comunicado=self.object,
                    archivo=archivo,
                    nombre_original=archivo.name,
                )

            messages.success(self.request, "Comunicado creado correctamente.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(ctx)

    def _handle_comedores(self, form):
        """Maneja la asignación de comedores según el tipo de comunicado."""
        if self.object.tipo == TipoComunicado.EXTERNO:
            if form.cleaned_data.get('para_todos_comedores'):
                # Asignar todos los comedores según permisos del usuario
                comedores = get_comedores_del_usuario(self.request.user)
                self.object.comedores.set(comedores)
            # Si no es para_todos_comedores, los comedores ya se guardaron del form
        else:
            # Si es interno, limpiar comedores
            self.object.comedores.clear()
            self.object.para_todos_comedores = False
            self.object.save()


class ComunicadoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar un comunicado."""

    model = Comunicado
    form_class = ComunicadoForm
    template_name = "comunicados/comunicado_form.html"
    success_url = reverse_lazy("comunicados_gestion")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        require_edit_permission(request.user, self.object)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["adjuntos_formset"] = ComunicadoAdjuntoFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            ctx["adjuntos_formset"] = ComunicadoAdjuntoFormSet(instance=self.object)
        ctx["titulo_pagina"] = "Editar Comunicado"
        ctx["is_edit"] = True
        ctx["es_tecnico"] = es_tecnico(self.request.user) and not is_admin(self.request.user)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        adjuntos_formset = ctx["adjuntos_formset"]

        form.instance.usuario_ultima_modificacion = self.request.user

        if adjuntos_formset.is_valid():
            self.object = form.save()
            adjuntos_formset.save()

            # Manejar relación con comedores para comunicados externos
            self._handle_comedores(form)

            # Manejar archivos múltiples del campo archivos_adjuntos
            archivos = self.request.FILES.getlist("archivos_adjuntos")
            for archivo in archivos:
                ComunicadoAdjunto.objects.create(
                    comunicado=self.object,
                    archivo=archivo,
                    nombre_original=archivo.name,
                )

            messages.success(self.request, "Comunicado actualizado correctamente.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(ctx)

    def _handle_comedores(self, form):
        """Maneja la asignación de comedores según el tipo de comunicado."""
        if self.object.tipo == TipoComunicado.EXTERNO:
            if form.cleaned_data.get('para_todos_comedores'):
                # Asignar todos los comedores según permisos del usuario
                comedores = get_comedores_del_usuario(self.request.user)
                self.object.comedores.set(comedores)
            # Si no es para_todos_comedores, los comedores ya se guardaron del form
        else:
            # Si es interno, limpiar comedores
            self.object.comedores.clear()
            self.object.para_todos_comedores = False
            self.object.save()


class ComunicadoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un comunicado."""

    model = Comunicado
    template_name = "comunicados/comunicado_confirm_delete.html"
    success_url = reverse_lazy("comunicados_gestion")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_delete_comunicado(request.user, self.object):
            raise PermissionDenied("No tiene permisos para eliminar este comunicado.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Comunicado eliminado correctamente.")
        return super().form_valid(form)


class ComunicadoPublicarView(LoginRequiredMixin, View):
    """Vista para publicar un comunicado."""

    def post(self, request, pk):
        require_publish_permission(request.user)
        comunicado = get_object_or_404(Comunicado, pk=pk)

        if comunicado.estado == EstadoComunicado.PUBLICADO:
            messages.warning(request, "El comunicado ya está publicado.")
        elif comunicado.estado == EstadoComunicado.ARCHIVADO:
            messages.error(request, "No se puede publicar un comunicado archivado.")
        else:
            comunicado.publicar(request.user)
            messages.success(request, "Comunicado publicado correctamente.")

        return redirect("comunicados_gestion")


class ComunicadoArchivarView(LoginRequiredMixin, View):
    """Vista para archivar un comunicado."""

    def post(self, request, pk):
        require_archive_permission(request.user)
        comunicado = get_object_or_404(Comunicado, pk=pk)

        if comunicado.estado == EstadoComunicado.ARCHIVADO:
            messages.warning(request, "El comunicado ya está archivado.")
        else:
            comunicado.archivar(request.user)
            messages.success(request, "Comunicado archivado correctamente.")

        return redirect("comunicados_gestion")


class ComunicadoToggleDestacadoView(LoginRequiredMixin, View):
    """Vista para cambiar el estado destacado de un comunicado publicado."""

    def post(self, request, pk):
        require_toggle_destacado_permission(request.user)
        comunicado = get_object_or_404(Comunicado, pk=pk)

        if comunicado.estado != EstadoComunicado.PUBLICADO:
            messages.error(request, "Solo se puede modificar el destacado de comunicados publicados.")
        else:
            comunicado.destacado = not comunicado.destacado
            comunicado.usuario_ultima_modificacion = request.user
            comunicado.save()

            if comunicado.destacado:
                messages.success(request, "Comunicado marcado como destacado.")
            else:
                messages.success(request, "Comunicado desmarcado como destacado.")

        return redirect("comunicados_gestion")
