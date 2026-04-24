from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.test import RequestFactory


pytestmark = pytest.mark.django_db
User = get_user_model()


def _assign_base_admisiones_permissions(user):
    permission_codes = (
        "comedores.view_comedor",
        "admisiones.view_admision",
        "acompanamientos.view_informacionrelevante",
    )
    permissions = []
    for permission_code in permission_codes:
        app_label, codename = permission_code.split(".", 1)
        permissions.append(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
    user.user_permissions.add(*permissions)


def _ensure_auth_role_permission(codename, name):
    group_content_type = ContentType.objects.get_for_model(Group)
    permission, _ = Permission.objects.get_or_create(
        content_type=group_content_type,
        codename=codename,
        defaults={"name": name},
    )
    return permission


def _build_template_context(estado_admision="documentacion_en_proceso"):
    doc = SimpleNamespace(
        row_id="1",
        es_personalizado=False,
        documentacion_id=1,
        archivo_id=1,
        estado="A Validar Abogado",
        estado_valor="A Validar Abogado",
        nombre="DNI",
        obligatorio=True,
        archivo_url="/media/dummy.pdf",
        id=1,
        numero_gde=None,
        observaciones=None,
    )
    admision = SimpleNamespace(
        id=99,
        enviada_a_archivo=False,
        estado_admision=estado_admision,
        estado=SimpleNamespace(nombre="En Proceso"),
    )
    return {"doc": doc, "admision": admision}


def test_documento_row_muestra_selector_para_abogado_dupla():
    abogado = User.objects.create_user(username="abogado_tpl", password="test")
    _assign_base_admisiones_permissions(abogado)
    role_abogado = _ensure_auth_role_permission(
        codename="role_abogado_dupla",
        name="Abogado Dupla",
    )
    abogado.user_permissions.add(role_abogado)

    request = RequestFactory().get("/")
    request.user = abogado

    html = render_to_string(
        "admisiones/includes/documento_row.html",
        _build_template_context(),
        request=request,
    )

    assert 'data-documento-id="1"' in html
    assert '<option value="Aceptado">Aceptado</option>' in html
    assert '<option value="Rectificar">Rectificar</option>' in html


def test_documento_row_no_muestra_selector_para_usuario_sin_rol_abogado():
    tecnico = User.objects.create_user(username="tecnico_tpl", password="test")
    _assign_base_admisiones_permissions(tecnico)
    role_tecnico = _ensure_auth_role_permission(
        codename="role_tecnico_comedor",
        name="Tecnico Comedor",
    )
    tecnico.user_permissions.add(role_tecnico)

    request = RequestFactory().get("/")
    request.user = tecnico

    html = render_to_string(
        "admisiones/includes/documento_row.html",
        _build_template_context(),
        request=request,
    )

    assert '<span class="badge bg-primary">A Validar Abogado</span>' in html
    assert 'data-documento-id="1"' not in html


def test_documento_row_muestra_boton_eliminar_en_estado_previo_a_finalizado():
    tecnico = User.objects.create_user(username="tecnico_btn_visible", password="test")
    _assign_base_admisiones_permissions(tecnico)

    request = RequestFactory().get("/")
    request.user = tecnico

    html = render_to_string(
        "admisiones/includes/documento_row.html",
        _build_template_context(estado_admision="informe_tecnico_en_proceso"),
        request=request,
    )

    assert "confirmarEliminar" in html


def test_documento_row_oculta_boton_eliminar_en_informe_tecnico_finalizado():
    tecnico = User.objects.create_user(username="tecnico_btn_oculto", password="test")
    _assign_base_admisiones_permissions(tecnico)

    request = RequestFactory().get("/")
    request.user = tecnico

    html = render_to_string(
        "admisiones/includes/documento_row.html",
        _build_template_context(estado_admision="informe_tecnico_finalizado"),
        request=request,
    )

    assert "confirmarEliminar" not in html
