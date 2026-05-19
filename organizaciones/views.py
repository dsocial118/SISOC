from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.forms import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from core.pagination import NoCountPaginator, build_no_count_page_range
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from iam.services import user_has_permission_code

from organizaciones.forms import OrganizacionForm, FirmanteForm, AvalForm
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
    SubtipoEntidad,
    Firmante,
    Aval,
    RolFirmante,
)

ORGANIZACION_LIST_ONLY_FIELDS = (
    "id",
    "nombre",
    "cuit",
    "telefono",
    "email",
    "tipo_entidad",
    "tipo_entidad__nombre",
    "subtipo_entidad",
    "subtipo_entidad__nombre",
)


def _build_organizacion_list_base_queryset():
    return Organizacion.objects.only(*ORGANIZACION_LIST_ONLY_FIELDS).order_by("-id")


def _build_organizacion_row_queryset():
    return (
        Organizacion.objects.select_related("tipo_entidad", "subtipo_entidad")
        .annotate(comedores_count=Count("comedor"))
        .only(*ORGANIZACION_LIST_ONLY_FIELDS)
        .order_by("-id")
    )


def _apply_organizacion_search(queryset, query):
    busqueda = (query or "").strip()
    if not busqueda:
        return queryset

    if busqueda.isdigit():
        numeric_value = int(busqueda)
        return queryset.filter(
            Q(cuit=numeric_value) | Q(telefono=numeric_value) | Q(pk=numeric_value)
        )

    return queryset.filter(Q(nombre__icontains=busqueda) | Q(email__icontains=busqueda))


def _puede_ver_todas_las_organizaciones(user):
    return user.is_superuser or user_has_permission_code(
        user, "organizaciones.view_organizacion"
    )


def _filtrar_organizaciones_por_dupla(queryset, user):
    if _puede_ver_todas_las_organizaciones(user):
        return queryset
    if not user.is_authenticated:
        return queryset.none()
    return queryset.filter(
        Q(comedor__dupla__abogado=user) | Q(comedor__dupla__tecnico=user)
    ).distinct()


def _build_organizacion_list_queryset(query, user=None):
    queryset = _apply_organizacion_search(
        _build_organizacion_list_base_queryset(), query
    )
    return _filtrar_organizaciones_por_dupla(queryset, user) if user else queryset


def _hydrate_organizaciones_page(page_ids):
    organizaciones_by_id = {
        organizacion.pk: organizacion
        for organizacion in _build_organizacion_row_queryset().filter(pk__in=page_ids)
    }
    return [organizaciones_by_id[pk] for pk in page_ids if pk in organizaciones_by_id]


def _categoria_documental_organizacion(organizacion):
    textos = " ".join(
        str(valor or "")
        for valor in (
            getattr(getattr(organizacion, "tipo_entidad", None), "nombre", ""),
            getattr(getattr(organizacion, "subtipo_entidad", None), "nombre", ""),
        )
    ).lower()
    if "ecles" in textos or "culto" in textos:
        return DocumentacionOrganizacion.CATEGORIA_ECLESIASTICA
    if "base" in textos or "hecho" in textos:
        return DocumentacionOrganizacion.CATEGORIA_BASE
    return DocumentacionOrganizacion.CATEGORIA_PERSONERIA


def _build_documentacion_organizacion_rows(organizacion):
    categoria = _categoria_documental_organizacion(organizacion)
    documentaciones = DocumentacionOrganizacion.objects.filter(categoria=categoria)
    archivos = (
        ArchivoOrganizacion.objects.filter(
            organizacion=organizacion, documentacion__categoria=categoria
        )
        .select_related("documentacion")
        .order_by("documentacion_id", "-creado", "-id")
    )
    archivos_por_doc = {}
    for archivo in archivos:
        archivos_por_doc.setdefault(archivo.documentacion_id, []).append(archivo)

    rows = []
    for documentacion in documentaciones:
        versiones = archivos_por_doc.get(documentacion.id, [])
        vigente = versiones[0] if versiones else None
        rows.append(
            {
                "documentacion": documentacion,
                "archivo": vigente,
                "historial": versiones[1:],
            }
        )
    return rows


def _build_documentacion_organizacion_row(organizacion, documentacion):
    archivos = list(
        ArchivoOrganizacion.objects.filter(
            organizacion=organizacion, documentacion=documentacion
        )
        .select_related("documentacion")
        .order_by("-creado", "-id")
    )
    return {
        "documentacion": documentacion,
        "archivo": archivos[0] if archivos else None,
        "historial": archivos[1:],
    }


def _render_documentacion_organizacion_row(request, organizacion, documentacion):
    row = _build_documentacion_organizacion_row(organizacion, documentacion)
    return render_to_string(
        "organizaciones/partials/documentacion_organizacion_row.html",
        {
            "row": row,
            "organizacion": organizacion,
            "puede_validar_documentacion_organizacion": (
                _puede_validar_documentacion_organizacion(request.user, organizacion)
            ),
            "puede_enviar_documentacion_organizacion": (
                _puede_enviar_documentacion_organizacion(request.user, organizacion)
            ),
        },
        request=request,
    )


def _usuario_en_dupla_organizacion(user, organizacion, lookup):
    if not user.is_authenticated or not organizacion:
        return False
    return (
        Organizacion.objects.filter(pk=organizacion.pk)
        .filter(**{lookup: user})
        .exists()
    )


def _puede_validar_documentacion_organizacion(user, organizacion=None):
    if user.is_superuser:
        return True
    return _usuario_en_dupla_organizacion(user, organizacion, "comedor__dupla__abogado")


def _puede_enviar_documentacion_organizacion(user, organizacion=None):
    if user.is_superuser:
        return True
    return _usuario_en_dupla_organizacion(user, organizacion, "comedor__dupla__tecnico")


def _puede_modificar_documentacion_organizacion(user, organizacion=None):
    return _puede_validar_documentacion_organizacion(
        user, organizacion
    ) or _puede_enviar_documentacion_organizacion(user, organizacion)


def _validar_cambio_estado_documento_organizacion(user, archivo, estado):
    puede_validar = _puede_validar_documentacion_organizacion(
        user, archivo.organizacion
    )
    puede_enviar = _puede_enviar_documentacion_organizacion(user, archivo.organizacion)

    if estado in {
        ArchivoOrganizacion.ESTADO_ACEPTADO,
        ArchivoOrganizacion.ESTADO_RECTIFICAR,
    }:
        if puede_validar and archivo.estado == ArchivoOrganizacion.ESTADO_A_VALIDAR:
            return None
        return "El abogado solo puede validar documentos en estado A Validar Abogado."

    if estado == ArchivoOrganizacion.ESTADO_A_VALIDAR:
        if puede_validar and archivo.estado == ArchivoOrganizacion.ESTADO_A_VALIDAR:
            return None
        if puede_enviar and archivo.estado not in {
            ArchivoOrganizacion.ESTADO_A_VALIDAR,
            ArchivoOrganizacion.ESTADO_ACEPTADO,
        }:
            return None
        if puede_enviar:
            return "El documento no esta disponible para envio tecnico."
        if puede_validar:
            return (
                "El abogado solo puede validar documentos en estado A Validar Abogado."
            )

    if puede_enviar:
        return "El tecnico solo puede enviar documentos a validar."
    if puede_validar:
        return "El abogado solo puede validar documentos en estado A Validar Abogado."
    return "Sin permisos para modificar este documento."


class OrganizacionListView(LoginRequiredMixin, ListView):
    model = Organizacion
    template_name = "organizacion_list.html"
    context_object_name = "organizaciones"
    paginate_by = 10

    def get_queryset(self):
        return _build_organizacion_list_queryset(
            self.request.GET.get("busqueda"), self.request.user
        )

    def paginate_queryset(self, queryset, page_size):
        paginator = NoCountPaginator(queryset.values_list("pk", flat=True), page_size)
        page_obj = paginator.get_page(self.request.GET.get(self.page_kwarg))
        object_list = _hydrate_organizaciones_page(page_obj.object_list)
        page_obj.object_list = object_list
        return paginator, page_obj, object_list, page_obj.has_other_pages()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        context["puede_crear_organizacion"] = _puede_ver_todas_las_organizaciones(
            self.request.user
        )
        context["puede_gestionar_organizaciones"] = _puede_ver_todas_las_organizaciones(
            self.request.user
        )
        page_obj = context.get("page_obj")
        if page_obj and getattr(page_obj.paginator, "count", None) is None:
            context["page_range"] = build_no_count_page_range(page_obj)
        return context


class FirmanteCreateView(LoginRequiredMixin, CreateView):
    model = Firmante
    form_class = FirmanteForm
    template_name = "firmante_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizacion_pk = (
            self.kwargs.get("organizacion_pk")
            or self.kwargs.get("pk")
            or self.request.GET.get("organizacion")
            or self.request.POST.get("organizacion")
        )

        context["organizacion_pk"] = organizacion_pk
        context["hidden_fields_send"] = [
            {"name": "organizacion_id", "value": organizacion_pk}
        ]
        # botones/breadcrumbs que usan las plantillas
        context["back_button"] = {
            "url": reverse("organizacion_detalle", kwargs={"pk": organizacion_pk}),
            "label": "Volver",
        }
        context["action_buttons"] = [{"label": "Guardar", "type": "submit"}]
        context["breadcrumb_items"] = []
        context["guardar_otro_send"] = True
        return context

    def get_allowed_roles_queryset(self, organizacion):
        """
        Devuelve queryset de RolFirmante filtrado según el tipo de entidad de la organización.
        """
        if not organizacion or not organizacion.tipo_entidad:
            return RolFirmante.objects.none()

        tipo = organizacion.tipo_entidad.nombre.strip().lower()
        mapping = {
            "personería jurídica": ["Presidente", "Tesorero", "Secretario"],
            "personería jurídica eclesiástica": [
                "Obispo",
                "Apoderado 1",
                "Apoderado 2",
            ],
            "asociación de hecho": ["Firmante 1", "Firmante 2", "Firmante 3"],
        }

        # buscar nombres permitidos según el tipo (case-insensitive)
        allowed = []
        for key, names in mapping.items():
            if key == tipo:
                allowed = names
                break

        if not allowed:
            # fallback: mostrar todos o ninguno según se prefiera; aquí mostramos todos por compatibilidad
            return RolFirmante.objects.all()
        return RolFirmante.objects.filter(nombre__in=allowed)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # obtener la organización (puede venir por kwargs o GET/POST)
        organizacion_pk = (
            self.kwargs.get("organizacion_pk")
            or self.kwargs.get("pk")
            or self.request.GET.get("organizacion")
            or self.request.POST.get("organizacion")
        )
        organizacion = None
        if organizacion_pk:
            try:
                organizacion = Organizacion.objects.select_related("tipo_entidad").get(
                    pk=organizacion_pk
                )
            except Organizacion.DoesNotExist:
                organizacion = None

        form.fields["rol"].queryset = self.get_allowed_roles_queryset(organizacion)
        return form

    def form_valid(self, form):
        organizacion_pk = (
            self.kwargs.get("organizacion_id")
            or self.request.POST.get("organizacion_id")
            or self.request.GET.get("organizacion_id")
        )
        if not organizacion_pk:
            messages.error(self.request, "Falta el id de la organización.")
            return self.form_invalid(form)

        rol = form.cleaned_data.get("rol")
        if rol:
            exists = Firmante.objects.filter(
                organizacion_id=organizacion_pk, rol=rol
            ).exists()
            if exists:
                form.add_error(
                    "rol", "Ya existe un firmante con ese rol para esta organización."
                )
                return self.form_invalid(form)
        # asignar FK y guardar
        form.instance.organizacion_id = organizacion_pk
        self.object = form.save()
        if "guardar_otro" in self.request.POST:
            return HttpResponseRedirect(self.get_success_url_add_new())
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
        )

    def get_success_url_add_new(self):
        return reverse(
            "firmante_crear", kwargs={"organizacion_pk": self.object.organizacion.pk}
        )


class AvalCreateView(LoginRequiredMixin, CreateView):
    model = Aval
    form_class = AvalForm
    template_name = "aval_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizacion_pk = (
            self.kwargs.get("organizacion_pk")
            or self.kwargs.get("pk")
            or self.request.GET.get("organizacion")
            or self.request.POST.get("organizacion")
        )

        context["organizacion_pk"] = organizacion_pk
        context["hidden_fields_send"] = [
            {"name": "organizacion_id", "value": organizacion_pk}
        ]
        # botones/breadcrumbs que usan las plantillas
        context["back_button"] = {
            "url": reverse("organizacion_detalle", kwargs={"pk": organizacion_pk}),
            "label": "Volver",
        }
        context["action_buttons"] = [{"label": "Guardar", "type": "submit"}]
        context["breadcrumb_items"] = []
        context["guardar_otro_send"] = True
        return context

    def form_valid(self, form):
        organizacion_pk = (
            self.kwargs.get("organizacion_id")
            or self.request.POST.get("organizacion_id")
            or self.request.GET.get("organizacion_id")
        )
        if not organizacion_pk:
            messages.error(self.request, "Falta el id de la organización.")
            return self.form_invalid(form)

        form.instance.organizacion_id = organizacion_pk
        self.object = form.save()
        if "guardar_otro" in self.request.POST:
            return HttpResponseRedirect(self.get_success_url_add_new())
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "organizacion_detalle",
            kwargs={"pk": self.object.organizacion.pk},
        )

    def get_success_url_add_new(self):
        return reverse(
            "aval_crear", kwargs={"organizacion_pk": self.object.organizacion.pk}
        )


class OrganizacionCreateView(LoginRequiredMixin, CreateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cuil_check_ajax_url"] = reverse("organizacion_cuil_check_ajax")
        context["organizacion_pk"] = None
        return context

    def form_valid(self, form):
        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})


class FirmanteUpdateView(LoginRequiredMixin, UpdateView):
    model = Firmante
    form_class = FirmanteForm
    template_name = "firmante_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["guardar_otro_send"] = False
        return context

    def form_valid(self, form):
        organizacion = getattr(self.object, "organizacion", None)
        organizacion_pk = (
            organizacion.pk
            if organizacion
            else (
                self.request.POST.get("organizacion_id")
                or self.request.GET.get("organizacion_id")
            )
        )

        # validar que no exista otro firmante con el mismo rol en la misma organización
        rol = form.cleaned_data.get("rol")
        if rol:
            exists = (
                Firmante.objects.filter(organizacion_id=organizacion_pk, rol=rol)
                .exclude(pk=self.object.pk)
                .exists()
            )
            if exists:
                form.add_error(
                    "rol", "Ya existe un firmante con ese rol para esta organización."
                )
                return self.form_invalid(form)

        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse(
            "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
        )


class AvalUpdateView(LoginRequiredMixin, UpdateView):
    model = Aval
    form_class = AvalForm
    template_name = "aval_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["guardar_otro_send"] = False
        return context

    def form_valid(self, form):
        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse(
            "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
        )


class FirmanteDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Firmante
    template_name = "firmante_confirm_delete.html"
    context_object_name = "firmante"
    success_message = "Firmante dado de baja correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {
                "url": reverse(
                    "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
                ),
                "label": "Detalle de Organización",
            },
            {"url": "", "label": "Confirmar Eliminación"},
        ]
        context["delete_message"] = (
            f"¿Está seguro que desea dar de baja al firmante {self.object.nombre}"
        )
        context["cancel_url"] = reverse(
            "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
        )
        return context

    def get_success_url(self):
        return reverse(
            "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
        )


class AvalDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Aval
    template_name = "aval_confirm_delete.html"
    context_object_name = "aval"
    success_message = "Aval dado de baja correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {
                "url": reverse(
                    "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
                ),
                "label": "Detalle de Organización",
            },
            {"url": "", "label": "Confirmar Eliminación"},
        ]
        context["delete_message"] = (
            f"¿Está seguro que desea dar de baja el aval {self.object.nombre}"
        )
        context["cancel_url"] = reverse(
            "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
        )
        return context

    def get_success_url(self):
        return reverse(
            "organizacion_detalle", kwargs={"pk": self.object.organizacion.pk}
        )


class OrganizacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Organizacion
    form_class = OrganizacionForm
    template_name = "organizacion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cuil_check_ajax_url"] = reverse("organizacion_cuil_check_ajax")
        context["organizacion_pk"] = self.object.pk
        return context

    def form_valid(self, form):
        if form.is_valid():
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.object.pk})


class OrganizacionDetailView(LoginRequiredMixin, DetailView):
    model = Organizacion
    template_name = "organizacion_detail.html"
    context_object_name = "organizacion"

    def get_queryset(self):
        return _filtrar_organizaciones_por_dupla(
            super().get_queryset(), self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["firmantes"] = self.object.firmantes.select_related("rol")
        context["avales_data"] = self.object.avales.all()

        # Obtener comedores asociados a la organización
        comedores = self.object.comedor_set.select_related(
            "tipocomedor", "provincia", "municipio", "localidad", "referente"
        ).all()
        context["comedores"] = comedores
        context["comedores_count"] = comedores.count()

        context["table_headers"] = [
            {"title": "Nombre"},
            {"title": "Rol"},
            {"title": "CUIT"},
        ]

        context["table_fields"] = [
            {"name": "nombre"},
            {"name": "rol"},
            {"name": "cuit"},
        ]

        context["actions"] = [
            {"url_name": "firmante_editar", "label": "Editar", "type": "primary"},
            {"url_name": "firmante_eliminar", "label": "Eliminar", "type": "danger"},
        ]

        context["show_actions"] = True

        context["data_items"] = [
            {"label": "Nombre", "value": self.object.nombre},
            {"label": "CUIT", "value": self.object.cuit},
            {"label": "Teléfono", "value": self.object.telefono},
            {"label": "Email", "value": self.object.email},
            {
                "label": "Tipo de Entidad",
                "value": (
                    self.object.tipo_entidad.nombre if self.object.tipo_entidad else ""
                ),
            },
            {
                "label": "Subtipo de Entidad",
                "value": (
                    self.object.subtipo_entidad.nombre
                    if self.object.subtipo_entidad
                    else ""
                ),
            },
            {"label": "Domicilio", "value": self.object.domicilio},
            {"label": "Localidad", "value": self.object.localidad},
            {"label": "Provincia", "value": self.object.provincia},
            {"label": "Partido", "value": self.object.partido},
            {"label": "Fecha de vencimiento", "value": self.object.fecha_vencimiento},
        ]

        context["table_headers_avales"] = [
            {"title": "Nombre"},
            {"title": "CUIT"},
        ]
        context["actions_firmantes"] = [
            {"url_name": "firmante_editar", "label": "Editar", "type": "primary"},
            {"url_name": "firmante_eliminar", "label": "Eliminar", "type": "danger"},
        ]
        context["table_fields_avales"] = [
            {"name": "nombre"},
            {"name": "cuit"},
        ]
        context["actions_avales"] = [
            {"url_name": "aval_editar", "label": "Editar", "type": "primary"},
            {"url_name": "aval_eliminar", "label": "Eliminar", "type": "danger"},
        ]
        tipo_entidad = getattr(self.object, "tipo_entidad", None)
        context["tipo_entidad"] = tipo_entidad
        context["avales"] = bool(
            tipo_entidad
            and getattr(tipo_entidad, "nombre", "") == "Asociación de hecho"
        )

        context["documentacion_organizacion"] = _build_documentacion_organizacion_rows(
            self.object
        )
        context["documentacion_organizacion_categoria"] = dict(
            DocumentacionOrganizacion.CATEGORIAS
        ).get(_categoria_documental_organizacion(self.object))
        context["puede_validar_documentacion_organizacion"] = (
            _puede_validar_documentacion_organizacion(self.request.user, self.object)
        )
        context["puede_enviar_documentacion_organizacion"] = (
            _puede_enviar_documentacion_organizacion(self.request.user, self.object)
        )
        context["puede_gestionar_organizaciones"] = _puede_ver_todas_las_organizaciones(
            self.request.user
        )

        return context


@login_required
def historial_documento_organizacion(request, organizacion_id, documentacion_id):
    organizacion = get_object_or_404(
        _filtrar_organizaciones_por_dupla(Organizacion.objects.all(), request.user),
        pk=organizacion_id,
    )
    documentacion = get_object_or_404(DocumentacionOrganizacion, pk=documentacion_id)
    archivos = ArchivoOrganizacion.objects.filter(
        organizacion=organizacion, documentacion=documentacion
    ).order_by("-creado", "-id")

    return render(
        request,
        "organizaciones/documentacion_historial.html",
        {
            "organizacion": organizacion,
            "documentacion": documentacion,
            "archivos": archivos,
        },
    )


@login_required
@require_POST
def subir_documento_organizacion(request, organizacion_id, documentacion_id):
    organizacion = get_object_or_404(Organizacion, pk=organizacion_id)
    documentacion = get_object_or_404(DocumentacionOrganizacion, pk=documentacion_id)
    if not _puede_enviar_documentacion_organizacion(request.user, organizacion):
        return JsonResponse(
            {"success": False, "error": "Sin permisos para cargar este documento."},
            status=403,
        )

    archivo = request.FILES.get("archivo")
    if not archivo:
        return JsonResponse(
            {"success": False, "error": "Debe adjuntar un archivo."}, status=400
        )

    fecha_vencimiento = request.POST.get("fecha_vencimiento") or None
    if fecha_vencimiento:
        fecha_vencimiento = parse_date(fecha_vencimiento)
        if fecha_vencimiento is None:
            return JsonResponse(
                {"success": False, "error": "Fecha de vencimiento invalida."},
                status=400,
            )

    archivo_actual = (
        ArchivoOrganizacion.objects.filter(
            organizacion=organizacion, documentacion=documentacion
        )
        .order_by("-creado", "-id")
        .first()
    )
    if archivo_actual and archivo_actual.estado != ArchivoOrganizacion.ESTADO_ACEPTADO:
        archivo_actual.archivo = archivo
        archivo_actual.fecha_vencimiento = fecha_vencimiento
        archivo_actual.estado = ArchivoOrganizacion.ESTADO_ADJUNTO
        archivo_actual.observaciones = ""
        archivo_actual.numero_gde = None
        archivo_actual.creado = timezone.now()
        archivo_actual.creado_por = request.user
        archivo_actual.modificado_por = request.user
        archivo_actual.save(
            update_fields=[
                "archivo",
                "fecha_vencimiento",
                "estado",
                "observaciones",
                "numero_gde",
                "creado",
                "creado_por",
                "modificado_por",
                "modificado",
            ]
        )
    else:
        ArchivoOrganizacion.objects.create(
            organizacion=organizacion,
            documentacion=documentacion,
            archivo=archivo,
            fecha_vencimiento=fecha_vencimiento,
            estado=ArchivoOrganizacion.ESTADO_ADJUNTO,
            creado_por=request.user,
            modificado_por=request.user,
        )
    return JsonResponse(
        {
            "success": True,
            "html": _render_documentacion_organizacion_row(
                request, organizacion, documentacion
            ),
            "row_id": documentacion.id,
        }
    )


@login_required
@require_POST
def actualizar_estado_documento_organizacion(request, archivo_id):
    archivo = get_object_or_404(
        ArchivoOrganizacion.objects.select_related("organizacion", "documentacion"),
        pk=archivo_id,
    )
    estado = request.POST.get("estado")
    estados_validos = {choice[0] for choice in ArchivoOrganizacion.ESTADOS}
    if estado not in estados_validos:
        return JsonResponse({"success": False, "error": "Estado invalido."}, status=400)
    error_permiso = _validar_cambio_estado_documento_organizacion(
        request.user, archivo, estado
    )
    if error_permiso:
        return JsonResponse(
            {"success": False, "error": error_permiso},
            status=403,
        )

    observaciones = (request.POST.get("observaciones") or "").strip()
    if (
        estado == ArchivoOrganizacion.ESTADO_RECTIFICAR
        and _puede_validar_documentacion_organizacion(
            request.user, archivo.organizacion
        )
        and not observaciones
    ):
        return JsonResponse(
            {"success": False, "error": "Debe indicar observaciones."},
            status=400,
        )

    archivo.estado = estado
    archivo.observaciones = (
        observaciones if estado == ArchivoOrganizacion.ESTADO_RECTIFICAR else ""
    )
    archivo.modificado_por = request.user
    archivo.save(
        update_fields=["estado", "observaciones", "modificado_por", "modificado"]
    )
    return JsonResponse(
        {
            "success": True,
            "estado": archivo.estado,
            "html": _render_documentacion_organizacion_row(
                request, archivo.organizacion, archivo.documentacion
            ),
            "row_id": archivo.documentacion_id,
        }
    )


@login_required
@require_POST
def actualizar_gde_documento_organizacion(request, archivo_id):
    archivo = get_object_or_404(
        ArchivoOrganizacion.objects.select_related("organizacion", "documentacion"),
        pk=archivo_id,
    )
    if not _puede_modificar_documentacion_organizacion(
        request.user, archivo.organizacion
    ):
        return JsonResponse(
            {"success": False, "error": "Sin permisos para modificar este documento."},
            status=403,
        )
    archivo.numero_gde = (request.POST.get("numero_gde") or "").strip() or None
    archivo.modificado_por = request.user
    archivo.save(update_fields=["numero_gde", "modificado_por", "modificado"])
    return JsonResponse(
        {
            "success": True,
            "numero_gde": archivo.numero_gde,
            "html": _render_documentacion_organizacion_row(
                request, archivo.organizacion, archivo.documentacion
            ),
            "row_id": archivo.documentacion_id,
        }
    )


@login_required
@require_POST
def actualizar_vencimiento_documento_organizacion(request, archivo_id):
    archivo = get_object_or_404(
        ArchivoOrganizacion.objects.select_related("organizacion", "documentacion"),
        pk=archivo_id,
    )
    if not _puede_modificar_documentacion_organizacion(
        request.user, archivo.organizacion
    ):
        return JsonResponse(
            {"success": False, "error": "Sin permisos para modificar este documento."},
            status=403,
        )
    fecha_vencimiento = (request.POST.get("fecha_vencimiento") or "").strip()
    fecha_parseada = parse_date(fecha_vencimiento) if fecha_vencimiento else None
    if fecha_vencimiento and fecha_parseada is None:
        return JsonResponse(
            {"success": False, "error": "Fecha de vencimiento invalida."},
            status=400,
        )

    archivo.fecha_vencimiento = fecha_parseada
    archivo.modificado_por = request.user
    archivo.save(update_fields=["fecha_vencimiento", "modificado_por", "modificado"])
    return JsonResponse(
        {
            "success": True,
            "fecha_vencimiento": (
                archivo.fecha_vencimiento.isoformat()
                if archivo.fecha_vencimiento
                else ""
            ),
            "html": _render_documentacion_organizacion_row(
                request, archivo.organizacion, archivo.documentacion
            ),
            "row_id": archivo.documentacion_id,
        }
    )


class OrganizacionDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Organizacion
    template_name = "organizacion_confirm_delete.html"
    context_object_name = "organizacion"
    success_url = reverse_lazy("organizaciones")
    success_message = "Organización dada de baja correctamente."

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            if hasattr(self.object, "restore") and hasattr(self.object, "deleted_at"):
                self.object.delete(
                    user=(
                        request.user
                        if getattr(request.user, "is_authenticated", False)
                        else None
                    ),
                    cascade=True,
                )
            else:
                self.object.delete()
            messages.success(
                request,
                f"La organización {self.object.nombre} fue dada de baja correctamente.",
            )
            return HttpResponseRedirect(self.success_url)
        except ValidationError as e:
            messages.error(request, e.message)
            return self.render_to_response(self.get_context_data(object=self.object))


@login_required
def sub_tipo_entidad_ajax(request):
    tipo_entidad_id = request.GET.get("tipo_entidad")
    if tipo_entidad_id:
        subtipo_entidades = SubtipoEntidad.objects.filter(
            tipo_entidad_id=tipo_entidad_id
        ).order_by("nombre")
    else:
        subtipo_entidades = SubtipoEntidad.objects.none()

    data = [{"id": subtipo.id, "text": subtipo.nombre} for subtipo in subtipo_entidades]
    return JsonResponse(data, safe=False)


@login_required
def cuil_check_ajax(request):
    """
    Devuelve las organizaciones activas que ya tienen el CUIL ingresado.
    Parámetro opcional `exclude` para ignorar la org que se está editando.
    """
    cuil_raw = request.GET.get("cuil", "").strip()
    exclude_pk = request.GET.get("exclude", "").strip()

    if not cuil_raw or not cuil_raw.isdigit():
        return JsonResponse({"organizaciones": []})

    cuil = int(cuil_raw)
    qs = Organizacion.objects.filter(cuit=cuil).select_related(
        "tipo_entidad", "subtipo_entidad", "provincia", "municipio", "localidad"
    )
    if exclude_pk and exclude_pk.isdigit():
        qs = qs.exclude(pk=int(exclude_pk))

    data = [
        {
            "id": org.pk,
            "nombre": org.nombre,
            "cuit": org.cuit,
            "telefono": str(org.telefono) if org.telefono is not None else "",
            "email": org.email or "",
            "tipo_entidad": org.tipo_entidad.nombre if org.tipo_entidad else "",
            "subtipo_entidad": (
                org.subtipo_entidad.nombre if org.subtipo_entidad else ""
            ),
            "domicilio": org.domicilio or "",
            "provincia": str(org.provincia) if org.provincia else "",
            "municipio": str(org.municipio) if org.municipio else "",
            "localidad": str(org.localidad) if org.localidad else "",
        }
        for org in qs
    ]
    return JsonResponse({"organizaciones": data})


@login_required
def organizaciones_ajax(request):
    """
    Vista AJAX para filtrar organizaciones en tiempo real.
    Retorna HTML renderizado de las filas de la tabla y paginación.
    """
    busqueda = request.GET.get("busqueda", "").strip()
    paginator = NoCountPaginator(
        _build_organizacion_list_queryset(busqueda, request.user).values_list(
            "pk", flat=True
        ),
        10,
    )
    page_obj = paginator.get_page(request.GET.get("page", 1))
    page_obj.object_list = _hydrate_organizaciones_page(page_obj.object_list)

    table_html = render_to_string(
        "organizaciones/partials/organizacion_rows.html",
        {
            "organizaciones": page_obj.object_list,
            "puede_gestionar_organizaciones": _puede_ver_todas_las_organizaciones(
                request.user
            ),
        },
        request=request,
    )

    pagination_html = render_to_string(
        "components/pagination.html",
        {
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
            "page_range": build_no_count_page_range(page_obj),
            "query": busqueda,
            "prev_text": "Volver",
            "next_text": "Continuar",
        },
        request=request,
    )

    return JsonResponse(
        {
            "html": table_html,
            "pagination_html": pagination_html,
            "count": paginator.count,
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_previous": page_obj.has_previous(),
            "has_next": page_obj.has_next(),
        }
    )
