"""Tests for tests."""

from importlib import import_module
from unittest import mock
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from admisiones.models.admisiones import Admision
from ciudadanos.models import Ciudadano
from comedores.models import (
    ActividadColaboradorEspacio,
    AuditColaboradorEspacio,
    ColaboradorEspacio,
    Comedor,
    HistorialValidacion,
    Nomina,
)
from comedores.services.comedor_service import ComedorService
from comedores.services.validacion_service import ValidacionService
from comedores.views import ComedorDetailView, NominaImportarView
from core.models import Sexo
from organizaciones.models import Aval, Firmante, Organizacion, RolFirmante
from relevamientos.models import Relevamiento


def _build_schema_editor(constraint_names):
    cursor_context = mock.MagicMock()
    cursor_context.__enter__.return_value = mock.sentinel.cursor
    connection = mock.MagicMock()
    connection.cursor.return_value = cursor_context
    connection.introspection.get_constraints.return_value = {
        name: {} for name in constraint_names
    }
    return mock.MagicMock(connection=connection)


def _build_migration_apps():
    fake_model = SimpleNamespace(_meta=SimpleNamespace(db_table="audit_table"))
    return SimpleNamespace(get_model=lambda app_label, model_name: fake_model)


def test_audit_colaborador_espacio_migration_renames_old_index_if_present():
    migration_module = import_module(
        "comedores.migrations."
        "0033_rename_comedores_a_comedor_89ef7d_idx_"
        "comedores_a_comedor_4b1714_idx_and_more"
    )
    schema_editor = _build_schema_editor({"comedores_a_comedor_89ef7d_idx"})

    migration_module._sync_audit_index_names(
        _build_migration_apps(),
        schema_editor,
        [
            (
                "comedores_a_comedor_89ef7d_idx",
                "comedores_a_comedor_4b1714_idx",
                ["comedor", "changed_at"],
            )
        ],
    )

    schema_editor.rename_index.assert_called_once()
    schema_editor.add_index.assert_not_called()
    _, old_index, new_index = schema_editor.rename_index.call_args.args
    assert old_index.name == "comedores_a_comedor_89ef7d_idx"
    assert new_index.name == "comedores_a_comedor_4b1714_idx"
    assert new_index.fields == ["comedor", "changed_at"]


def test_audit_colaborador_espacio_migration_skips_when_new_index_exists():
    migration_module = import_module(
        "comedores.migrations."
        "0033_rename_comedores_a_comedor_89ef7d_idx_"
        "comedores_a_comedor_4b1714_idx_and_more"
    )
    schema_editor = _build_schema_editor({"comedores_a_comedor_4b1714_idx"})

    migration_module._sync_audit_index_names(
        _build_migration_apps(),
        schema_editor,
        [
            (
                "comedores_a_comedor_89ef7d_idx",
                "comedores_a_comedor_4b1714_idx",
                ["comedor", "changed_at"],
            )
        ],
    )

    schema_editor.rename_index.assert_not_called()
    schema_editor.add_index.assert_not_called()


def test_audit_colaborador_espacio_migration_creates_index_if_missing():
    migration_module = import_module(
        "comedores.migrations."
        "0033_rename_comedores_a_comedor_89ef7d_idx_"
        "comedores_a_comedor_4b1714_idx_and_more"
    )
    schema_editor = _build_schema_editor(set())

    migration_module._sync_audit_index_names(
        _build_migration_apps(),
        schema_editor,
        [
            (
                "comedores_a_comedor_89ef7d_idx",
                "comedores_a_comedor_4b1714_idx",
                ["comedor", "changed_at"],
            )
        ],
    )

    schema_editor.rename_index.assert_not_called()
    schema_editor.add_index.assert_called_once()
    _, created_index = schema_editor.add_index.call_args.args
    assert created_index.name == "comedores_a_comedor_4b1714_idx"
    assert created_index.fields == ["comedor", "changed_at"]


# Tests for ComedorDetailView (HTML)
@pytest.mark.django_db
def test_comedor_detail_view_get_context(client_logged_fixture, comedor_fixture):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(url)
    body = response.content.decode()
    assert response.status_code == 200
    for key in [
        "relevamientos",
        "observaciones",
        "count_relevamientos",
        "count_beneficiarios",
        "presupuesto_desayuno",
        "presupuesto_almuerzo",
        "presupuesto_merienda",
        "presupuesto_cena",
        "monto_prestacion_mensual",
        "imagenes",
        "comedor_categoria",
        "rendicion_cuentas_final_activo",
        "admision",
    ]:
        assert key in response.context

    assert "GESTIONAR_API_KEY" not in response.context
    assert "GESTIONAR_API_CREAR_COMEDOR" not in response.context
    assert "nuevo_comedor_detalle" not in body
    assert "comedores_nuevo/" not in body
    assert reverse("relevamientos", kwargs={"comedor_pk": comedor.pk}) in body
    assert (
        reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor.pk}) not in body
    )


@pytest.mark.django_db
def test_comedor_detail_view_renderiza_card_colaboradores(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    client = client_logged_fixture
    comedor = comedor_fixture
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_presupuestos",
        lambda *args, **kwargs: (10, 1, 2, 3, 4, 5),
    )
    comedor.colaboradores_espacio_optimized = [
        SimpleNamespace(
            apellido="Perez",
            nombre="Ana",
            dni=30111222,
            cuil_cuit="27301112228",
            sexo_display="Femenino",
            get_genero_display="Mujer",
            codigo_telefono="11",
            numero_telefono="01144445555",
            fecha_alta="2026-03-26",
            fecha_baja=None,
            actividades=SimpleNamespace(
                all=lambda: [
                    SimpleNamespace(nombre="Compras"),
                    SimpleNamespace(nombre="Limpieza"),
                ]
            ),
        )
    ]
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode()
    assert "Colaboradores del espacio" in content
    assert "Perez, Ana" in content
    assert "27301112228" in content
    assert "Compras" in content
    assert "Limpieza" in content


@pytest.mark.django_db
def test_colaborador_espacio_crear_requiere_permiso(comedor_fixture, monkeypatch):
    client = Client()
    user = get_user_model().objects.create_user(
        username="sin_permiso_colaborador",
        password="testpass",
    )
    client.force_login(user)
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )

    response = client.get(
        reverse("colaborador_espacio_crear", kwargs={"pk": comedor_fixture.pk})
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_colaborador_espacio_crear_get_con_ciudadano_existente(
    comedor_fixture, monkeypatch
):
    client = Client()
    user = get_user_model().objects.create_superuser(
        username="admin_colaborador_get",
        email="admin-colab-get@example.com",
        password="testpass",
    )
    client.force_login(user)
    sexo = Sexo.objects.create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        fecha_nacimiento="1990-01-10",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111222,
        sexo=sexo,
        cuil_cuit="20301112229",
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )

    response = client.get(
        reverse("colaborador_espacio_crear", kwargs={"pk": comedor_fixture.pk}),
        {"query": str(ciudadano.documento)},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "Ciudadano encontrado en SISOC" in content
    assert "Perez" in content
    assert "20301112229" in content


@pytest.mark.django_db
def test_colaborador_espacio_crear_post_con_ciudadano_existente(
    comedor_fixture, monkeypatch
):
    client = Client()
    user = get_user_model().objects.create_superuser(
        username="admin_colaborador_post",
        email="admin-colab-post@example.com",
        password="testpass",
    )
    client.force_login(user)
    sexo = Sexo.objects.create(sexo="Femenino")
    ciudadano = Ciudadano.objects.create(
        apellido="Gomez",
        nombre="Ana",
        fecha_nacimiento="1992-05-03",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=28999111,
        sexo=sexo,
        cuil_cuit="27289991116",
    )
    actividad = ActividadColaboradorEspacio.objects.create(
        alias="COM",
        nombre="Compras test",
        orden=99,
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )

    response = client.post(
        reverse("colaborador_espacio_crear", kwargs={"pk": comedor_fixture.pk}),
        {
            "ciudadano_id": ciudadano.id,
            "genero": ColaboradorEspacio.GeneroChoices.MUJER,
            "codigo_telefono": "11",
            "numero_telefono": "01155556666",
            "fecha_alta": "2026-03-26",
            "fecha_baja": "",
            "actividades": [actividad.id],
        },
    )

    assert response.status_code == 302
    colaborador = ColaboradorEspacio.objects.get(
        comedor=comedor_fixture,
        ciudadano=ciudadano,
    )
    assert colaborador.codigo_telefono == "11"
    assert colaborador.numero_telefono == "01155556666"
    assert list(colaborador.actividades.values_list("nombre", flat=True)) == [
        "Compras test"
    ]


@pytest.mark.django_db
def test_colaborador_espacio_crear_post_desde_renaper(comedor_fixture, monkeypatch):
    client = Client()
    user = get_user_model().objects.create_superuser(
        username="admin_colaborador_renaper",
        email="admin-colab-renaper@example.com",
        password="testpass",
    )
    client.force_login(user)
    sexo = Sexo.objects.create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        apellido="Lopez",
        nombre="Mario",
        fecha_nacimiento="1988-08-08",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=33444555,
        sexo=sexo,
        cuil_cuit="20334445551",
    )
    actividad = ActividadColaboradorEspacio.objects.create(
        alias="MAN",
        nombre="Mantenimiento test",
        orden=100,
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.crear_ciudadano_desde_renaper",
        lambda dni, user=None: {
            "success": True,
            "ciudadano": ciudadano,
            "created": True,
            "message": "Ciudadano creado automáticamente con datos de RENAPER.",
        },
    )

    response = client.post(
        reverse("colaborador_espacio_crear", kwargs={"pk": comedor_fixture.pk}),
        {
            "dni": "33444555",
            "genero": ColaboradorEspacio.GeneroChoices.VARON,
            "codigo_telefono": "221",
            "numero_telefono": "099998887",
            "fecha_alta": "2026-03-26",
            "fecha_baja": "",
            "actividades": [actividad.id],
        },
    )

    assert response.status_code == 302
    colaborador = ColaboradorEspacio.objects.get(
        comedor=comedor_fixture,
        ciudadano=ciudadano,
    )
    assert colaborador.genero == ColaboradorEspacio.GeneroChoices.VARON


@pytest.mark.django_db
def test_colaborador_espacio_editar_actualiza_datos(comedor_fixture, monkeypatch):
    client = Client()
    user = get_user_model().objects.create_superuser(
        username="admin_colaborador_edit",
        email="admin-colab-edit@example.com",
        password="testpass",
    )
    client.force_login(user)
    sexo = Sexo.objects.create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        apellido="Suarez",
        nombre="Luis",
        fecha_nacimiento="1991-03-03",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111999,
        sexo=sexo,
        cuil_cuit="20301119993",
    )
    actividad_1 = ActividadColaboradorEspacio.objects.create(
        alias="COM",
        nombre="Compras edit",
        orden=101,
    )
    actividad_2 = ActividadColaboradorEspacio.objects.create(
        alias="MAN",
        nombre="Mantenimiento edit",
        orden=102,
    )
    colaborador = ColaboradorEspacio.objects.create(
        comedor=comedor_fixture,
        ciudadano=ciudadano,
        genero=ColaboradorEspacio.GeneroChoices.VARON,
        codigo_telefono="11",
        numero_telefono="123456",
        fecha_alta="2026-03-01",
    )
    colaborador.actividades.set([actividad_1])
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )

    response = client.post(
        reverse(
            "colaborador_espacio_editar",
            kwargs={"pk": comedor_fixture.pk, "pk2": colaborador.pk},
        ),
        {
            "ciudadano_id": ciudadano.id,
            "genero": ColaboradorEspacio.GeneroChoices.NO_DECLARA,
            "codigo_telefono": "221",
            "numero_telefono": "987654",
            "fecha_alta": "2026-03-02",
            "fecha_baja": "",
            "actividades": [actividad_2.id],
        },
    )

    assert response.status_code == 302
    colaborador.refresh_from_db()
    assert colaborador.genero == ColaboradorEspacio.GeneroChoices.NO_DECLARA
    assert colaborador.codigo_telefono == "221"
    assert colaborador.numero_telefono == "987654"
    assert list(colaborador.actividades.values_list("nombre", flat=True)) == [
        "Mantenimiento edit"
    ]


@pytest.mark.django_db
def test_colaborador_espacio_eliminar_hace_baja_logica(comedor_fixture, monkeypatch):
    client = Client()
    user = get_user_model().objects.create_superuser(
        username="admin_colaborador_delete",
        email="admin-colab-delete@example.com",
        password="testpass",
    )
    client.force_login(user)
    sexo = Sexo.objects.create(sexo="Femenino")
    ciudadano = Ciudadano.objects.create(
        apellido="Diaz",
        nombre="Laura",
        fecha_nacimiento="1995-06-06",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=32111999,
        sexo=sexo,
        cuil_cuit="27321119996",
    )
    colaborador = ColaboradorEspacio.objects.create(
        comedor=comedor_fixture,
        ciudadano=ciudadano,
        genero=ColaboradorEspacio.GeneroChoices.MUJER,
        fecha_alta="2026-03-01",
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )

    response = client.post(
        reverse(
            "colaborador_espacio_eliminar",
            kwargs={"pk": comedor_fixture.pk, "pk2": colaborador.pk},
        )
    )

    assert response.status_code == 302
    colaborador.refresh_from_db()
    assert colaborador.fecha_baja is not None
    assert ColaboradorEspacio.objects.filter(pk=colaborador.pk).exists()
    audit = AuditColaboradorEspacio.objects.filter(
        colaborador=colaborador, accion=AuditColaboradorEspacio.ACCION_DELETE
    ).first()
    assert audit is not None
    assert audit.snapshot_antes["fecha_baja"] is None
    assert audit.snapshot_despues["fecha_baja"] is not None


@pytest.mark.django_db
def test_colaborador_espacio_permite_reingreso_historico(comedor_fixture, monkeypatch):
    client = Client()
    user = get_user_model().objects.create_superuser(
        username="admin_colaborador_reingreso",
        email="admin-colab-reingreso@example.com",
        password="testpass",
    )
    client.force_login(user)
    sexo = Sexo.objects.create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        apellido="Martinez",
        nombre="Raul",
        fecha_nacimiento="1989-04-04",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111888,
        sexo=sexo,
        cuil_cuit="20301118882",
    )
    actividad = ActividadColaboradorEspacio.objects.create(
        alias="COM",
        nombre="Compras reingreso",
        orden=103,
    )
    historial = ColaboradorEspacio.objects.create(
        comedor=comedor_fixture,
        ciudadano=ciudadano,
        genero=ColaboradorEspacio.GeneroChoices.VARON,
        fecha_alta="2025-01-01",
        fecha_baja="2025-06-01",
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )

    response = client.post(
        reverse("colaborador_espacio_crear", kwargs={"pk": comedor_fixture.pk}),
        {
            "ciudadano_id": ciudadano.id,
            "genero": ColaboradorEspacio.GeneroChoices.VARON,
            "codigo_telefono": "11",
            "numero_telefono": "11112222",
            "fecha_alta": "2026-03-26",
            "fecha_baja": "",
            "actividades": [actividad.id],
        },
    )

    assert response.status_code == 302
    assert (
        ColaboradorEspacio.objects.filter(
            comedor=comedor_fixture,
            ciudadano=ciudadano,
        ).count()
        == 2
    )
    nuevo = ColaboradorEspacio.objects.exclude(pk=historial.pk).get()
    assert nuevo.fecha_baja is None
    audit = AuditColaboradorEspacio.objects.filter(
        colaborador=nuevo, accion=AuditColaboradorEspacio.ACCION_CREATE
    ).first()
    assert audit is not None
    assert audit.metadata["source"] == "sisoc"


@pytest.mark.django_db
def test_colaborador_espacio_editar_registra_auditoria(comedor_fixture, monkeypatch):
    client = Client()
    user = get_user_model().objects.create_superuser(
        username="admin_colaborador_audit_update",
        email="admin-colab-audit-update@example.com",
        password="testpass",
    )
    client.force_login(user)
    sexo = Sexo.objects.create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        apellido="Ramos",
        nombre="Pablo",
        fecha_nacimiento="1991-09-09",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30999111,
        sexo=sexo,
        cuil_cuit="20309991116",
    )
    actividad_1 = ActividadColaboradorEspacio.objects.create(
        alias="COM",
        nombre="Actividad audit 1",
        orden=104,
    )
    actividad_2 = ActividadColaboradorEspacio.objects.create(
        alias="MAN",
        nombre="Actividad audit 2",
        orden=105,
    )
    colaborador = ColaboradorEspacio.objects.create(
        comedor=comedor_fixture,
        ciudadano=ciudadano,
        genero=ColaboradorEspacio.GeneroChoices.VARON,
        codigo_telefono="11",
        numero_telefono="123123",
        fecha_alta="2026-03-01",
    )
    colaborador.actividades.set([actividad_1])
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_scoped_comedor_or_404",
        lambda pk, user: comedor_fixture,
    )

    response = client.post(
        reverse(
            "colaborador_espacio_editar",
            kwargs={"pk": comedor_fixture.pk, "pk2": colaborador.pk},
        ),
        {
            "ciudadano_id": ciudadano.id,
            "genero": ColaboradorEspacio.GeneroChoices.NO_DECLARA,
            "codigo_telefono": "221",
            "numero_telefono": "456456",
            "fecha_alta": "2026-03-02",
            "fecha_baja": "",
            "actividades": [actividad_2.id],
        },
    )

    assert response.status_code == 302
    audit = AuditColaboradorEspacio.objects.filter(
        colaborador=colaborador, accion=AuditColaboradorEspacio.ACCION_UPDATE
    ).first()
    assert audit is not None
    assert audit.snapshot_antes["codigo_telefono"] == "11"
    assert audit.snapshot_despues["codigo_telefono"] == "221"
    assert audit.snapshot_antes["actividades"] == ["Actividad audit 1"]
    assert audit.snapshot_despues["actividades"] == ["Actividad audit 2"]


@pytest.mark.django_db
def test_crear_ciudadano_desde_renaper_normaliza_foreign_keys(monkeypatch):
    sexo = Sexo.objects.create(sexo="Masculino")
    monkeypatch.setattr(
        "comedores.services.comedor_service.impl.consultar_datos_renaper",
        lambda dni, sexo_value: {
            "success": True,
            "data": {
                "apellido": "Perez",
                "nombre": "Juan",
                "fecha_nacimiento": "1990-01-10",
                "dni": dni,
                "sexo": sexo.pk,
                "cuil": 20301112229,
                "tipo_documento": Ciudadano.DOCUMENTO_DNI,
            },
            "datos_api": {},
        },
    )

    result = ComedorService.crear_ciudadano_desde_renaper("30111222")

    assert result["success"] is True
    assert result["created"] is True
    assert result["ciudadano"].sexo_id == sexo.pk
    assert result["ciudadano"].documento == 30111222


@pytest.mark.django_db
def test_comedor_detail_view_post_new_relevamiento(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"territorial": "1"})

    assert response.status_code == 302
    assert response.url == reverse("relevamientos", kwargs={"comedor_pk": comedor.pk})


def test_comedor_detail_view_responsables_usa_datos_de_organizacion(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    organizacion = Organizacion.objects.create(
        nombre="Asociacion Comedor Norte",
        cuit=20333444556,
        email="org@example.com",
        telefono=1144556677,
    )
    rol = RolFirmante.objects.create(nombre="Presidenta")
    Firmante.objects.create(
        organizacion=organizacion,
        nombre="Ana Perez",
        cuit=27111222333,
        rol=rol,
    )
    Firmante.objects.create(
        organizacion=organizacion,
        nombre="Luis Gomez",
        cuit=20222333444,
    )
    Aval.objects.create(
        organizacion=organizacion,
        nombre="Carlos Aval",
        cuit=20999888777,
    )
    comedor.organizacion = organizacion
    comedor.save(update_fields=["organizacion"])

    response = client.get(reverse("comedor_detalle", kwargs={"pk": comedor.pk}))
    body = response.content.decode()

    assert response.status_code == 200
    assert "Asociacion Comedor Norte" in body
    assert "org@example.com" in body
    assert "1144556677" in body
    assert "Firmantes" in body
    assert "Presidenta: Ana Perez 27111222333" in body
    assert "Luis Gomez 20222333444" in body
    assert "Avales" in body
    assert "Aval 1" in body
    assert "Carlos Aval 20999888777" in body
    assert "Responsable 1" not in body
    assert "Responsable 2" not in body
    assert "Responsable de la tarjeta del cobro" not in body
    assert "<strong>Aval 2:</strong>" not in body


@pytest.mark.django_db
def test_comedor_detail_view_responsables_oculta_datos_y_bloques_vacios(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    organizacion = Organizacion.objects.create(
        nombre="Organizacion Minima",
        cuit=20123456789,
        email="",
        telefono=None,
        subtipo_entidad=None,
    )
    comedor.organizacion = organizacion
    comedor.save(update_fields=["organizacion"])

    response = client.get(reverse("comedor_detalle", kwargs={"pk": comedor.pk}))
    body = response.content.decode()

    assert response.status_code == 200
    assert "Organizacion Minima" in body
    assert ">Email:</strong>" not in body
    assert ">Telefono:</strong>" not in body
    assert ">Subtipo de entidad:</strong>" not in body
    assert "Firmantes" not in body
    assert "Avales" not in body


@pytest.mark.django_db
def test_comedor_detalle_legacy_redirect(client_logged_fixture, comedor_fixture):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("nuevo_comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(url)
    assert response.status_code == 301
    assert response.headers["Location"] == reverse(
        "comedor_detalle", kwargs={"pk": comedor.pk}
    )


@pytest.mark.django_db
def test_comedor_detalle_legacy_redirect_preserva_query_string(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("nuevo_comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(f"{url}?admision_id=99")
    assert response.status_code == 301
    assert response.headers["Location"] == (
        f"{reverse('comedor_detalle', kwargs={'pk': comedor.pk})}?admision_id=99"
    )


@pytest.mark.django_db
def test_validar_comedor_rollback_on_historial_error(monkeypatch):
    user_model = get_user_model()
    user = user_model.objects.create_superuser(
        username="validator",
        email="validator@example.com",
        password="strong-password",
    )
    comedor = Comedor.objects.create(nombre="Comedor Atomic Test")

    def _raise_integrity_error(*args, **kwargs):
        raise IntegrityError("boom")

    monkeypatch.setattr(
        "comedores.models.HistorialValidacion.objects.create",
        _raise_integrity_error,
    )

    with pytest.raises(IntegrityError):
        ValidacionService.validar_comedor(
            comedor_id=comedor.pk,
            user=user,
            accion="validar",
            comentario="comentario de prueba",
        )

    comedor.refresh_from_db()
    assert comedor.estado_validacion == "Pendiente"
    assert comedor.fecha_validado is None


@pytest.mark.django_db
def test_get_relaciones_optimizadas_escapes_historial_comment():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="historial-user",
        email="historial@example.com",
        password="complex-pass",
    )
    comedor = Comedor.objects.create(nombre="Comedor Sanitized")
    HistorialValidacion.objects.create(
        comedor=comedor,
        usuario=user,
        estado_validacion="Validado",
        comentario="<script>alert('xss')</script>",
    )

    view = ComedorDetailView()
    view.request = RequestFactory().get("/comedores/1/")
    view.object = comedor

    relaciones = view.get_relaciones_optimizadas()
    comentario_cell = relaciones["validaciones_items"][0]["cells"][4]["content"]
    estado_cell = relaciones["validaciones_items"][0]["cells"][2]["content"]

    assert comentario_cell == escape("<script>alert('xss')</script>")
    assert str(estado_cell) == '<span class="badge bg-success">Validado</span>'


@pytest.mark.django_db
def test_comedor_detail_view_post_redirects_on_other(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"foo": "bar"})
    assert response.status_code == 302
    assert reverse("comedor_detalle", kwargs={"pk": comedor.pk}) in response.url


@pytest.mark.django_db
def test_comedor_detail_view_post_legacy_relevamiento_redirects_a_relevamientos(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"territorial": "1"}, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("relevamientos", kwargs={"comedor_pk": comedor.pk}), 302)
    ]
    assert (
        "La gestión de relevamientos ya no se realiza desde este legajo."
        in response.content.decode()
    )


# Tests for AJAX endpoint (if present)
@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_crear(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba la creación de un nuevo relevamiento vía AJAX.
    Verifica que:
    1. Se invoque al servicio correcto
    2. Se retorne la URL de redirección adecuada
    3. El código de estado sea 200
    """
    # Mock del servicio de relevamiento para evitar llamadas reales durante el test
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 999
    relevamiento_mock.comedor = mock.Mock()
    relevamiento_mock.comedor.pk = comedor_fixture.pk

    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente",
        mock.Mock(return_value=relevamiento_mock),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "url" in json_response
    # Verificar que la URL tenga el formato correcto con los IDs esperados
    expected_url = (
        f"/comedores/{comedor_fixture.pk}/relevamiento/{relevamiento_mock.pk}"
    )
    assert json_response["url"] == expected_url


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_crear_exige_territorial(
    client_logged_fixture, comedor_fixture
):
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    response = client_logged_fixture.post(
        url,
        {
            "tipo_relevamiento": "relevamiento_inicial",
            "territorial": "",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 400
    assert "territorial" in response.json()["error"].lower()


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_crea_primer_seguimiento(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 1001
    relevamiento_mock.comedor = mock.Mock()
    relevamiento_mock.comedor.pk = comedor_fixture.pk
    seguimiento_mock = mock.Mock()
    seguimiento_mock.id_relevamiento = relevamiento_mock
    create_mock = mock.Mock(return_value=seguimiento_mock)

    monkeypatch.setattr(
        "comedores.views.relevamientos.PrimerSeguimientoService.create_asignado",
        create_mock,
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    response = client_logged_fixture.post(
        url,
        {
            "tipo_relevamiento": "primer_seguimiento",
            "territorial": '{"gestionar_uid":"uid-1","nombre":"Territorial Norte"}',
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 200
    assert response.json()["url"] == (
        f"/comedores/{comedor_fixture.pk}/relevamiento/{relevamiento_mock.pk}"
    )
    create_mock.assert_called_once()


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_rechaza_segundo_seguimiento(
    client_logged_fixture, comedor_fixture
):
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    response = client_logged_fixture.post(
        url,
        {
            "tipo_relevamiento": "segundo_seguimiento",
            "territorial": '{"gestionar_uid":"uid-1","nombre":"Territorial Norte"}',
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 400
    assert "Segundo seguimiento" in response.json()["error"]


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_editar(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba la edición de un relevamiento vía AJAX.
    Verifica que:
    1. Se invoque al servicio correcto
    2. Se retorne la URL de redirección adecuada
    3. El código de estado sea 200
    """
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 1000
    relevamiento_mock.comedor = mock.Mock()
    relevamiento_mock.comedor.pk = comedor_fixture.pk

    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.update_territorial",
        mock.Mock(return_value=relevamiento_mock),
    )
    monkeypatch.setattr(
        "comedores.views.relevamientos.get_object_or_404",
        mock.Mock(return_value=relevamiento_mock),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial_editar": "1",
        "relevamiento_id": "1000",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "url" in json_response
    # Verificar que la URL tenga el formato correcto con los IDs esperados
    expected_url = (
        f"/comedores/{comedor_fixture.pk}/relevamiento/{relevamiento_mock.pk}"
    )
    assert json_response["url"] == expected_url


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_editar_rechaza_payload_vacio(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    monkeypatch.setattr(
        "relevamientos.tasks.AsyncSendRelevamientoToGestionar.start", lambda self: None
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor_fixture,
        estado="Pendiente",
    )
    user_model = get_user_model()
    user_instance = user_model.objects.get(
        pk=client_logged_fixture.session["_auth_user_id"]
    )
    user_instance.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="relevamientos",
            codename="change_relevamiento",
        )
    )
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})

    response = client_logged_fixture.post(
        url,
        {"territorial_editar": "", "relevamiento_id": str(relevamiento.pk)},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    relevamiento.refresh_from_db()

    assert response.status_code == 400
    assert "error" in response.json()
    assert relevamiento.estado == "Pendiente"
    assert relevamiento.territorial_uid is None
    assert relevamiento.territorial_nombre is None


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_editar_sin_permiso_devuelve_403(
    comedor_fixture, monkeypatch
):
    monkeypatch.setattr(
        "relevamientos.tasks.AsyncSendRelevamientoToGestionar.start", lambda self: None
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor_fixture,
        estado="Pendiente",
    )
    user_model = get_user_model()
    user_instance = user_model.objects.create_user(
        username="sin_permiso_editar_relevamiento",
        password="testpass",
    )
    for group_name in [
        "Comedores Ver",
        "Comedores Relevamiento Ver",
        "Comedores Relevamiento Crear",
        "Comedores Relevamiento Detalle",
    ]:
        group, _ = Group.objects.get_or_create(name=group_name)
        user_instance.groups.add(group)
    user_instance.save()
    client = Client()
    client.login(username=user_instance.username, password="testpass")

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    territorial_json = '{"gestionar_uid":"uid-1","nombre":"Territorial Norte"}'
    response = client.post(
        url,
        {
            "territorial_editar": territorial_json,
            "relevamiento_id": str(relevamiento.pk),
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    relevamiento.refresh_from_db()

    assert response.status_code == 403
    assert "error" in response.json()
    assert relevamiento.estado == "Pendiente"
    assert relevamiento.territorial_uid is None
    assert relevamiento.territorial_nombre is None


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_editar_rechaza_estado_no_pendiente(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    monkeypatch.setattr(
        "relevamientos.tasks.AsyncSendRelevamientoToGestionar.start", lambda self: None
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor_fixture,
        estado="Finalizado",
    )
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})

    response = client_logged_fixture.post(
        url,
        {
            "territorial_editar": '{"gestionar_uid":"uid-1","nombre":"Territorial Norte"}',
            "relevamiento_id": str(relevamiento.pk),
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    relevamiento.refresh_from_db()

    assert response.status_code == 400
    assert "error" in response.json()
    assert relevamiento.estado == "Finalizado"
    assert relevamiento.territorial_uid is None
    assert relevamiento.territorial_nombre is None


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_editar_rechaza_json_no_objeto(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    monkeypatch.setattr(
        "relevamientos.tasks.AsyncSendRelevamientoToGestionar.start", lambda self: None
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor_fixture,
        estado="Pendiente",
    )
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})

    response = client_logged_fixture.post(
        url,
        {"territorial_editar": "[]", "relevamiento_id": str(relevamiento.pk)},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    relevamiento.refresh_from_db()

    assert response.status_code == 400
    assert "error" in response.json()
    assert relevamiento.estado == "Pendiente"
    assert relevamiento.territorial_uid is None
    assert relevamiento.territorial_nombre is None


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_accion_invalida(
    client_logged_fixture, comedor_fixture
):
    """
    Prueba que una acción inválida retorne un error.
    """
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {"accion_invalida": "1"}
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 400
    json_response = response.json()
    assert "error" in json_response
    assert "Acción no reconocida" in json_response["error"]


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_error(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba el manejo de errores durante la creación/edición.
    """
    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente",
        mock.Mock(side_effect=Exception("Error inesperado")),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 500
    json_response = response.json()
    assert "error" in json_response
    assert "Error interno" in json_response["error"]


@pytest.mark.django_db
def test_borrar_foto_legajo_elimina_archivo_y_campo(tmp_path, monkeypatch):
    fs = FileSystemStorage(location=tmp_path)
    with override_settings(MEDIA_ROOT=tmp_path):
        monkeypatch.setattr(
            "comedores.services.comedor_service.impl.default_storage", fs
        )
        archivo = SimpleUploadedFile(
            "test.jpg", b"contenido", content_type="image/jpeg"
        )
        comedor = Comedor.objects.create(nombre="Prueba", foto_legajo=archivo)
        ruta = comedor.foto_legajo.name
        assert fs.exists(ruta)

        ComedorService.delete_legajo_photo({"foto_legajo_borrar": "1"}, comedor)
        comedor.refresh_from_db()

        assert not comedor.foto_legajo
        assert not fs.exists(ruta)


# ---------------------------------------------------------------------------
# Fixtures para tests de nómina
# ---------------------------------------------------------------------------


@pytest.fixture
def client_nomina_fixture(db):
    """Cliente autenticado con permisos de nómina."""
    user_model = get_user_model()
    user = user_model.objects.create_user(username="nomina_user", password="testpass")
    for group_name in [
        "Comedores Nomina Ver",
        "Comedores Nomina Crear",
        "Comedores Nomina Editar",
        "Comedores Nomina Borrar",
    ]:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    client = Client()
    client.login(username="nomina_user", password="testpass")
    return client


@pytest.fixture
def admision_fixture(db):
    """Comedor + Admisión activa mínima para tests de nómina."""
    comedor = Comedor.objects.create(nombre="Comedor Test Nómina")
    admision = Admision.objects.create(comedor=comedor)
    return admision


@pytest.fixture
def ciudadano_fixture(db):
    """Ciudadano mínimo para tests de nómina."""
    from datetime import date

    return Ciudadano.objects.create(
        nombre="Juan",
        apellido="Test",
        fecha_nacimiento=date(1990, 1, 1),
    )


# ---------------------------------------------------------------------------
# Tests de servicios
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_agregar_ciudadano_a_nomina_caso_feliz(admision_fixture, ciudadano_fixture):
    """Agrega un ciudadano a la nómina de una admisión correctamente."""
    ok, _msg = ComedorService.agregar_ciudadano_a_nomina(
        admision_id=admision_fixture.pk,
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        estado=Nomina.ESTADO_ACTIVO,
    )

    assert ok is True
    assert Nomina.objects.filter(
        admision=admision_fixture, ciudadano=ciudadano_fixture
    ).exists()


@pytest.mark.django_db
def test_agregar_ciudadano_ya_en_nomina(admision_fixture, ciudadano_fixture):
    """Retorna False si el ciudadano ya está en la nómina de esa admisión."""
    Nomina.objects.create(
        admision=admision_fixture,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, msg = ComedorService.agregar_ciudadano_a_nomina(
        admision_id=admision_fixture.pk,
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
    )

    assert ok is False
    assert "ya está en la nómina" in msg


@pytest.mark.django_db
def test_agregar_ciudadano_en_revision_no_ingresa_a_nomina(
    admision_fixture, ciudadano_fixture
):
    """No permite sumar a nómina ciudadanos pendientes de revisión de identidad."""
    ciudadano_fixture.tipo_registro_identidad = Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO
    ciudadano_fixture.requiere_revision_manual = True
    ciudadano_fixture.documento = 30111222
    ciudadano_fixture.save(
        update_fields=[
            "tipo_registro_identidad",
            "requiere_revision_manual",
            "documento",
        ]
    )

    ok, msg = ComedorService.agregar_ciudadano_a_nomina(
        admision_id=admision_fixture.pk,
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        estado=Nomina.ESTADO_ACTIVO,
    )

    assert ok is False
    assert "pendiente de revisión" in msg
    assert not Nomina.objects.filter(
        admision=admision_fixture, ciudadano=ciudadano_fixture
    ).exists()


@pytest.mark.django_db
def test_agregar_ciudadano_revisado_manualmente_ingresa_a_nomina(
    admision_fixture, ciudadano_fixture
):
    """Permite sumar a nómina ciudadanos cuya revisión manual ya fue cerrada."""
    ciudadano_fixture.tipo_registro_identidad = Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO
    ciudadano_fixture.requiere_revision_manual = False
    ciudadano_fixture.documento = 30111223
    ciudadano_fixture.save(
        update_fields=[
            "tipo_registro_identidad",
            "requiere_revision_manual",
            "documento",
        ]
    )

    ok, _msg = ComedorService.agregar_ciudadano_a_nomina(
        admision_id=admision_fixture.pk,
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        estado=Nomina.ESTADO_ACTIVO,
    )

    assert ok is True
    assert Nomina.objects.filter(
        admision=admision_fixture, ciudadano=ciudadano_fixture
    ).exists()


@pytest.mark.django_db
def test_nomina_muestra_estandar_y_no_validado_revisado_con_mismo_dni(
    admision_fixture,
):
    """La nómina debe conservar registros distintos aunque compartan DNI."""
    from datetime import date

    documento = 30111230
    estandar = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Estandar",
        fecha_nacimiento=date(1990, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=documento,
    )
    no_validado = Ciudadano.objects.create(
        nombre="Beto",
        apellido="NoValidado",
        fecha_nacimiento=date(1991, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=documento,
        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
        motivo_no_validacion_renaper=Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
    )
    no_validado.requiere_revision_manual = False
    no_validado.save(update_fields=["requiere_revision_manual"])

    Nomina.objects.create(
        admision=admision_fixture,
        ciudadano=estandar,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, msg = ComedorService.agregar_ciudadano_a_nomina(
        admision_id=admision_fixture.pk,
        ciudadano_id=no_validado.pk,
        user=mock.Mock(),
        estado=Nomina.ESTADO_ESPERA,
    )

    page_obj, *_ = ComedorService.get_nomina_detail(
        admision_fixture.pk, dni_query=str(documento)
    )
    ciudadano_ids = {nomina.ciudadano_id for nomina in page_obj.object_list}

    assert ok is True, msg
    assert ciudadano_ids == {estandar.pk, no_validado.pk}


@pytest.mark.django_db
def test_importar_nomina_ultimo_convenio_caso_feliz(ciudadano_fixture):
    """Copia los registros de nómina de la admisión anterior a la actual."""
    comedor = Comedor.objects.create(nombre="Comedor Importar")
    admision_anterior = Admision.objects.create(comedor=comedor)
    admision_actual = Admision.objects.create(comedor=comedor)
    Nomina.objects.create(
        admision=admision_anterior,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_actual.pk,
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert cantidad == 1
    assert Nomina.objects.filter(
        admision=admision_actual, ciudadano=ciudadano_fixture
    ).exists()
    # El registro importado queda en ACTIVO
    nomina_importada = Nomina.objects.get(admision=admision_actual)
    assert nomina_importada.estado == Nomina.ESTADO_ACTIVO


@pytest.mark.django_db
def test_importar_nomina_sin_convenio_anterior_con_nomina():
    """Retorna False si no hay admisión anterior con nómina."""
    comedor = Comedor.objects.create(nombre="Comedor Sin Anterior")
    admision_actual = Admision.objects.create(comedor=comedor)

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_actual.pk,
        comedor_id=comedor.pk,
    )

    assert ok is False
    assert cantidad == 0


@pytest.mark.django_db
def test_importar_nomina_evita_duplicados(ciudadano_fixture):
    """No duplica personas que ya están en la nómina destino."""
    comedor = Comedor.objects.create(nombre="Comedor Duplicados")
    admision_anterior = Admision.objects.create(comedor=comedor)
    admision_actual = Admision.objects.create(comedor=comedor)
    # El ciudadano está en ambas admisiones
    Nomina.objects.create(
        admision=admision_anterior,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )
    Nomina.objects.create(
        admision=admision_actual,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_actual.pk,
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert cantidad == 0  # nada nuevo importado
    assert Nomina.objects.filter(admision=admision_actual).count() == 1


@pytest.mark.django_db
def test_importar_nomina_toma_admision_anterior_y_no_una_posterior():
    """Importa desde la admisión anterior real, no desde una más nueva."""
    from datetime import date

    comedor = Comedor.objects.create(nombre="Comedor Orden")
    admision_vieja = Admision.objects.create(comedor=comedor)
    admision_destino = Admision.objects.create(comedor=comedor)
    admision_mas_nueva = Admision.objects.create(comedor=comedor)

    ciudadano_viejo = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Vieja",
        fecha_nacimiento=date(1990, 1, 1),
    )
    ciudadano_nuevo = Ciudadano.objects.create(
        nombre="Beto",
        apellido="Nuevo",
        fecha_nacimiento=date(1991, 1, 1),
    )
    Nomina.objects.create(admision=admision_vieja, ciudadano=ciudadano_viejo)
    Nomina.objects.create(admision=admision_mas_nueva, ciudadano=ciudadano_nuevo)

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_destino.pk,
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert cantidad == 1
    assert Nomina.objects.filter(
        admision=admision_destino, ciudadano=ciudadano_viejo
    ).exists()
    assert not Nomina.objects.filter(
        admision=admision_destino, ciudadano=ciudadano_nuevo
    ).exists()


@pytest.mark.django_db
def test_importar_nomina_falla_si_admision_no_corresponde_al_comedor():
    """Retorna error si la admisión destino no pertenece al comedor recibido."""
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    admision_b = Admision.objects.create(comedor=comedor_b)

    ok, msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_b.pk,
        comedor_id=comedor_a.pk,
    )

    assert ok is False
    assert "no corresponde al comedor" in msg
    assert cantidad == 0


# ---------------------------------------------------------------------------
# Tests de vistas
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nomina_detail_view_responde_ok(client_nomina_fixture, admision_fixture):
    """NominaDetailView responde 200 y tiene las claves de contexto esperadas."""
    comedor = admision_fixture.comedor
    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_fixture.pk},
    )
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    for key in ["nomina", "cantidad_nomina", "object", "admision_pk"]:
        assert key in response.context


@pytest.mark.django_db
def test_nomina_create_view_muestra_ciudadano_en_revision_sin_accion_agregar(
    client_nomina_fixture, admision_fixture, ciudadano_fixture
):
    """La búsqueda muestra el caso en revisión, pero no ofrece agregarlo."""
    ciudadano_fixture.tipo_registro_identidad = Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO
    ciudadano_fixture.requiere_revision_manual = True
    ciudadano_fixture.documento = 30111224
    ciudadano_fixture.save(
        update_fields=[
            "tipo_registro_identidad",
            "requiere_revision_manual",
            "documento",
        ]
    )
    comedor = admision_fixture.comedor
    url = reverse(
        "nomina_crear",
        kwargs={"pk": comedor.pk, "admision_pk": admision_fixture.pk},
    )

    response = client_nomina_fixture.get(url, {"query": "30111224"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Revisión pendiente" in content
    assert f'data-ciudadano-id="{ciudadano_fixture.pk}"' not in content


@pytest.mark.django_db
def test_nomina_detail_view_filtra_por_dni_en_toda_la_nomina(
    client_nomina_fixture, admision_fixture
):
    """El filtro por DNI debe aplicarse antes de paginar, no solo sobre la página actual."""
    from datetime import date

    ciudadano_objetivo = Ciudadano.objects.create(
        nombre="Persona",
        apellido="Objetivo",
        documento=12345678,
        fecha_nacimiento=date(1990, 1, 1),
    )
    Nomina.objects.create(
        admision=admision_fixture,
        ciudadano=ciudadano_objetivo,
        estado=Nomina.ESTADO_ACTIVO,
    )

    # Crea 100 registros más nuevos para forzar que el objetivo quede fuera de la página 1.
    for idx in range(100):
        ciudadano = Ciudadano.objects.create(
            nombre=f"Persona{idx}",
            apellido=f"Apellido{idx}",
            documento=30000000 + idx,
            fecha_nacimiento=date(1990, 1, 1),
        )
        Nomina.objects.create(
            admision=admision_fixture,
            ciudadano=ciudadano,
            estado=Nomina.ESTADO_ACTIVO,
        )

    comedor = admision_fixture.comedor
    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_fixture.pk},
    )

    response_sin_filtro = client_nomina_fixture.get(url, {"page": 1})
    assert response_sin_filtro.status_code == 200
    assert "12345678" not in response_sin_filtro.content.decode()

    response_filtrada = client_nomina_fixture.get(url, {"page": 1, "dni": "12345678"})
    assert response_filtrada.status_code == 200
    assert "12345678" in response_filtrada.content.decode()
    assert response_filtrada.context["nomina"].paginator.count == 1


@pytest.mark.django_db
def test_get_nomina_detail_desempata_por_id_para_paginacion_estable(
    admision_fixture,
):
    """Cuando varias filas comparten fecha, la paginacion debe usar un desempate estable."""
    from datetime import date

    created_ids = []
    for idx in range(101):
        ciudadano = Ciudadano.objects.create(
            nombre=f"Persona{idx}",
            apellido=f"Empate{idx}",
            documento=41000000 + idx,
            fecha_nacimiento=date(1990, 1, 1),
        )
        nomina = Nomina.objects.create(
            admision=admision_fixture,
            ciudadano=ciudadano,
            estado=Nomina.ESTADO_ACTIVO,
        )
        created_ids.append(nomina.id)

    fecha_empate = timezone.now().replace(microsecond=0)
    Nomina.objects.filter(admision=admision_fixture).update(fecha=fecha_empate)

    page_1, *_ = ComedorService.get_nomina_detail(admision_fixture.pk, page=1)
    page_2, *_ = ComedorService.get_nomina_detail(admision_fixture.pk, page=2)

    orden_esperado = sorted(created_ids, reverse=True)
    page_1_ids = [nomina.id for nomina in page_1.object_list]
    page_2_ids = [nomina.id for nomina in page_2.object_list]

    assert page_1_ids == orden_esperado[:100]
    assert page_2_ids == orden_esperado[100:]


@pytest.mark.django_db
def test_nomina_detail_view_prioriza_bajas_al_final(
    client_nomina_fixture,
    admision_fixture,
):
    """La nómina debe mostrar las bajas al final, aunque sean más nuevas."""
    from datetime import date, timedelta

    fecha_base = timezone.now().replace(microsecond=0)
    registros = []
    for nombre, apellido, documento, estado, offset in (
        ("Ana", "Activa", 40111222, Nomina.ESTADO_ACTIVO, -2),
        ("Beto", "Espera", 40111223, Nomina.ESTADO_ESPERA, -1),
        ("Carla", "Baja", 40111224, Nomina.ESTADO_BAJA, 0),
    ):
        ciudadano = Ciudadano.objects.create(
            nombre=nombre,
            apellido=apellido,
            documento=documento,
            fecha_nacimiento=date(1990, 1, 1),
        )
        nomina = Nomina.objects.create(
            admision=admision_fixture,
            ciudadano=ciudadano,
            estado=estado,
        )
        Nomina.objects.filter(pk=nomina.pk).update(
            fecha=fecha_base + timedelta(days=offset)
        )
        nomina.refresh_from_db()
        registros.append(nomina)

    comedor = admision_fixture.comedor
    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_fixture.pk},
    )
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    assert list(response.context["nomina"].object_list) == registros


@pytest.mark.django_db
def test_nomina_detail_view_cantidad_nomina_cuenta_solo_activos(
    client_nomina_fixture,
    admision_fixture,
):
    """La tarjeta de asistentes debe contar solo los registros activos."""
    from datetime import date

    for idx, estado in enumerate(
        [Nomina.ESTADO_ACTIVO, Nomina.ESTADO_ESPERA, Nomina.ESTADO_BAJA]
    ):
        ciudadano = Ciudadano.objects.create(
            nombre=f"Persona{idx}",
            apellido=f"Apellido{idx}",
            documento=40111300 + idx,
            fecha_nacimiento=date(1990, 1, 1),
        )
        Nomina.objects.create(
            admision=admision_fixture,
            ciudadano=ciudadano,
            estado=estado,
        )

    comedor = admision_fixture.comedor
    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_fixture.pk},
    )
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    assert response.context["cantidad_nomina"] == 1
    assert response.context["nomina"].paginator.count == 3


@pytest.mark.django_db
def test_nomina_detail_view_404_si_admision_no_corresponde(client_nomina_fixture):
    """Retorna 404 si la admisión no pertenece al comedor de la URL."""
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    admision_b = Admision.objects.create(comedor=comedor_b)

    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor_a.pk, "admision_pk": admision_b.pk},
    )
    response = client_nomina_fixture.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_nomina_importar_view_redirige(
    client_nomina_fixture, admision_fixture, ciudadano_fixture
):
    """POST a NominaImportarView redirige a nomina_ver."""
    comedor = admision_fixture.comedor
    admision_nueva = Admision.objects.create(comedor=comedor)
    # Hay nómina en la admisión anterior para poder importar
    Nomina.objects.create(
        admision=admision_fixture,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    url = reverse(
        "nomina_importar",
        kwargs={"pk": comedor.pk, "admision_pk": admision_nueva.pk},
    )
    response = client_nomina_fixture.post(url)

    assert response.status_code == 302
    expected_redirect = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_nueva.pk},
    )
    assert expected_redirect in response.url


@pytest.mark.django_db
def test_nomina_importar_view_404_si_admision_no_corresponde(client_nomina_fixture):
    """Retorna 404 si la admisión no corresponde al comedor en la URL."""
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    admision_b = Admision.objects.create(comedor=comedor_b)

    url = reverse(
        "nomina_importar",
        kwargs={"pk": comedor_a.pk, "admision_pk": admision_b.pk},
    )
    response = client_nomina_fixture.post(url)
    assert response.status_code == 404


def test_comedores_views_exporta_nomina_importar_view():
    """`comedores.views` expone NominaImportarView para imports de URLs."""
    assert NominaImportarView.__name__ == "NominaImportarView"


# ---------------------------------------------------------------------------
# Tests — nómina directa (programas 3/4, sin admisión)
# ---------------------------------------------------------------------------

import csv
import io
from django.core.management import call_command

from comedores.models import Programas
from comedores.views import (
    NominaDirectaDetailView,
    NominaDirectaCreateView,
    NominaDirectaDeleteView,
)


def _programa(pk, nombre):
    """Crea (o recupera) un Programas con ID exacto."""
    prog, _ = Programas.objects.get_or_create(
        id=pk,
        defaults={
            "nombre": nombre,
            "usa_admision_para_nomina": pk not in (3, 4),
        },
    )
    cambios = []
    if prog.nombre != nombre:
        prog.nombre = nombre
        cambios.append("nombre")
    usa_admision_para_nomina = pk not in (3, 4)
    if prog.usa_admision_para_nomina != usa_admision_para_nomina:
        prog.usa_admision_para_nomina = usa_admision_para_nomina
        cambios.append("usa_admision_para_nomina")
    if cambios:
        prog.save(update_fields=cambios)
    return prog


# ---------------------------------------------------------------------------
# Service — agregar ciudadano a nómina directa (prog 3/4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_agregar_ciudadano_a_nomina_directa_caso_feliz(ciudadano_fixture):
    """Agrega ciudadano a nómina directa de un comedor 3/4 (sin admisión)."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Prog 3", programa=prog)

    ok, _msg = ComedorService.agregar_ciudadano_a_nomina(
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert Nomina.objects.filter(
        comedor=comedor, ciudadano=ciudadano_fixture, admision__isnull=True
    ).exists()


@pytest.mark.django_db
def test_agregar_ciudadano_ya_en_nomina_directa(ciudadano_fixture):
    """Retorna False si el ciudadano ya está en la nómina directa del comedor."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Prog 4", programa=prog)
    Nomina.objects.create(
        comedor=comedor,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, msg = ComedorService.agregar_ciudadano_a_nomina(
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        comedor_id=comedor.pk,
    )

    assert ok is False
    assert "ya está en la nómina" in msg


@pytest.mark.django_db
def test_get_nomina_detail_by_comedor_solo_devuelve_nominas_directas(ciudadano_fixture):
    """get_nomina_detail_by_comedor solo incluye nóminas con admision=null del comedor."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Detail", programa=prog)
    comedor_otro = Comedor.objects.create(nombre="Comedor Otro", programa=prog)
    admision = Admision.objects.create(comedor=comedor)

    # Nómina directa del comedor (debe aparecer)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )
    # Nómina vía admisión del mismo comedor (no debe aparecer)
    Nomina.objects.create(
        admision=admision, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )
    # Nómina directa de otro comedor (no debe aparecer)
    Nomina.objects.create(
        comedor=comedor_otro, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    _, *_, total, _ = ComedorService.get_nomina_detail_by_comedor(comedor.pk)

    assert total == 1


# ---------------------------------------------------------------------------
# Signal — no debe reasignar nóminas directas en programas 3/4
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_signal_no_reasigna_nominas_directas_al_crear_admision_prog3(
    ciudadano_fixture,
):
    """Los programas 3/4 conservan la nómina directa aunque exista una admisión accidental."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Signal P3", programa=prog)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    admision = Admision.objects.create(comedor=comedor)

    nomina = Nomina.objects.get(ciudadano=ciudadano_fixture)
    assert admision.comedor_id == comedor.pk
    assert nomina.admision_id is None
    assert nomina.comedor_id == comedor.pk


@pytest.mark.django_db
def test_signal_no_reasigna_nominas_directas_al_crear_admision_prog4(
    ciudadano_fixture,
):
    """Los programas 3/4 conservan la nómina directa aunque exista una admisión accidental."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Signal P4", programa=prog)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    admision = Admision.objects.create(comedor=comedor)

    nomina = Nomina.objects.get(ciudadano=ciudadano_fixture)
    assert admision.comedor_id == comedor.pk
    assert nomina.admision_id is None
    assert nomina.comedor_id == comedor.pk


@pytest.mark.django_db
def test_signal_asigna_nominas_a_admision_si_programa_2(ciudadano_fixture):
    """Al crear admisión en programa 2, la nómina pasa al flujo por admisión."""
    prog = _programa(2, "Alimentar comunidad")
    comedor = Comedor.objects.create(nombre="Comedor Signal P2", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    admision = Admision.objects.create(comedor=comedor)

    nomina.refresh_from_db()
    assert nomina.admision_id == admision.pk
    assert nomina.comedor_id is None


@pytest.mark.django_db
def test_signal_no_asigna_en_update_de_admision(ciudadano_fixture):
    """El signal solo corre al crear admisión, no al actualizarla."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Signal Update", programa=prog)
    admision = Admision.objects.create(comedor=comedor)

    # Nómina directa creada DESPUÉS de la admisión
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    # Update de admisión no debe disparar el signal
    admision.save()

    nomina.refresh_from_db()
    assert nomina.comedor_id == comedor.pk  # sigue sin asignarse
    assert nomina.admision_id is None


# ---------------------------------------------------------------------------
# Vistas — NominaDirecta* (prog 3/4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nomina_directa_detail_view_responde_ok(client_nomina_fixture):
    """NominaDirectaDetailView responde 200 con contexto correcto."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Vista P3", programa=prog)

    url = reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    for key in ["nomina", "cantidad_nomina", "object", "admision_pk"]:
        assert key in response.context
    assert response.context["admision_pk"] is None
    assert response.context["object"].pk == comedor.pk


@pytest.mark.django_db
def test_nomina_directa_detail_view_muestra_solo_nominas_directas(
    client_nomina_fixture, ciudadano_fixture
):
    """NominaDirectaDetailView muestra solo nóminas directas del comedor (admision=null)."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Vista P4", programa=prog)
    admision = Admision.objects.create(comedor=comedor)
    # Nómina directa (debe aparecer)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )
    # Nómina vía admisión (no debe aparecer)
    Nomina.objects.create(
        admision=admision, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    assert response.context["cantidad_nomina"] == 1


@pytest.mark.django_db
def test_nomina_directa_detail_view_404_comedor_inexistente(client_nomina_fixture):
    """Retorna 404 si el comedor no existe."""
    url = reverse("nomina_directa_ver", kwargs={"pk": 99999})
    response = client_nomina_fixture.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_nomina_directa_detail_view_404_para_programa_con_admision(
    client_nomina_fixture,
):
    """La nómina directa solo aplica a programas 3/4."""
    prog = _programa(2, "Alimentar comunidad")
    comedor = Comedor.objects.create(nombre="Comedor Vista P2", programa=prog)

    url = reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_nomina_directa_delete_view_muestra_cancelacion_directa(
    client_nomina_fixture, ciudadano_fixture
):
    """La confirmación de baja directa debe volver a la nómina directa."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Borrado", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_directa_borrar", kwargs={"pk": comedor.pk, "pk2": nomina.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    assert (
        reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
        in response.content.decode()
    )


@pytest.mark.django_db
def test_nomina_editar_ajax_funciona_con_nomina_directa(
    client_nomina_fixture, ciudadano_fixture
):
    """nomina_editar_ajax acepta nóminas directas (comedor FK, sin admision)."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Ajax", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_editar_ajax", kwargs={"pk": nomina.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_nomina_cambiar_estado_funciona_con_nomina_directa(
    client_nomina_fixture, ciudadano_fixture
):
    """nomina_cambiar_estado acepta nóminas directas y cambia el estado."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Estado", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_cambiar_estado", kwargs={"pk": nomina.pk})
    response = client_nomina_fixture.post(url, {"estado": Nomina.ESTADO_ESPERA})

    assert response.status_code == 200
    nomina.refresh_from_db()
    assert nomina.estado == Nomina.ESTADO_ESPERA


@pytest.mark.django_db
def test_comedor_detail_view_muestra_nomina_directa_para_programa_sin_admision(
    ciudadano_fixture,
):
    """El detalle del comedor debe enlazar a la nómina directa cuando no usa admisión."""
    from django.test import RequestFactory

    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Directo", programa=prog)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    view = ComedorDetailView()
    view.request = RequestFactory().get(f"/comedores/{comedor.pk}")
    view.object = comedor

    context = view.get_context_data()

    assert context["nomina_total"] == 1
    assert context["selected_admision_id"] is None


@pytest.mark.django_db
def test_flujo_integrado_comedor_sin_admision_muestra_y_abre_nomina_directa(
    client_logged_fixture, client_nomina_fixture, ciudadano_fixture, monkeypatch
):
    """Cubre el flujo real: detalle del comedor + acceso a la nómina directa."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Integrado", programa=prog)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )
    monkeypatch.setattr(
        "comedores.views.comedor.ComedorService.get_comedor_detail_object",
        lambda pk, user=None: comedor,
    )

    detalle_url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    detalle_response = client_logged_fixture.get(detalle_url)

    assert detalle_response.status_code == 200
    detalle_body = detalle_response.content.decode()
    assert detalle_response.context["selected_admision_id"] is None
    assert (
        detalle_response.context["comedor"].programa.usa_admision_para_nomina is False
    )
    assert detalle_response.context["nomina_total"] == 1
    assert reverse("nomina_directa_ver", kwargs={"pk": comedor.pk}) in detalle_body
    assert "Este comedor usa nómina directa y no depende de admisiones." in detalle_body

    nomina_directa_url = reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
    nomina_directa_response = client_nomina_fixture.get(nomina_directa_url)

    assert nomina_directa_response.status_code == 200
    assert nomina_directa_response.context["admision_pk"] is None
    assert nomina_directa_response.context["cantidad_nomina"] == 1
    assert nomina_directa_response.context["object"].pk == comedor.pk


# ---------------------------------------------------------------------------
# Management command — recuperar_nominas_csv
# ---------------------------------------------------------------------------


def _csv_content(rows):
    """Genera contenido CSV con el header del backup real (9 columnas)."""
    header = "id,ciudadano_id,comedor_id,fecha,estado,observaciones,deleted_at,deleted_by_id,admision_id_sugerida"
    lines = [header] + [
        ",".join(
            [
                str(r["id"]),
                str(r["ciudadano_id"]),
                str(r["comedor_id"]),
                "2025-12-16 11:37:56",
                "activo",
                "",  # observaciones
                "",  # deleted_at
                "",  # deleted_by_id
                str(r.get("admision_id_sugerida", "")),
            ]
        )
        for r in rows
    ]
    return "\n".join(lines)


@pytest.mark.django_db
def test_recuperar_nominas_csv_asigna_comedor_prog34(tmp_path, ciudadano_fixture):
    """Para prog 3/4, asigna comedor_id y deja admision=null."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor CSV P3", programa=prog)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina.refresh_from_db()
    assert nomina.comedor_id == comedor.pk
    assert nomina.admision_id is None


@pytest.mark.django_db
def test_recuperar_nominas_csv_asigna_admision_prog2(tmp_path, ciudadano_fixture):
    """Para prog 2, asigna comedor_id y admision_id desde admision_id_sugerida."""
    prog = _programa(2, "Alimentar comunidad")
    comedor = Comedor.objects.create(nombre="Comedor CSV P2", programa=prog)
    admision = Admision.objects.create(comedor=comedor)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                    "admision_id_sugerida": admision.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina.refresh_from_db()
    assert nomina.comedor_id == comedor.pk
    assert nomina.admision_id == admision.pk


@pytest.mark.django_db
def test_recuperar_nominas_csv_dry_run_no_modifica(tmp_path, ciudadano_fixture):
    """Con --dry-run, no se aplica ningún cambio a la BD."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor DryRun", programa=prog)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file), "--dry-run")

    nomina.refresh_from_db()
    assert nomina.comedor_id is None  # sin cambios


@pytest.mark.django_db
def test_recuperar_nominas_csv_omite_comedor_no_encontrado(tmp_path, ciudadano_fixture):
    """Si el comedor_id del CSV no existe en la BD, la nómina queda sin cambios."""
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": 99999,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina.refresh_from_db()
    assert nomina.comedor_id is None


@pytest.mark.django_db
def test_recuperar_nominas_csv_incluye_soft_deleted(tmp_path, ciudadano_fixture):
    """El command procesa también las nóminas soft-deleted (all_objects)."""
    from django.utils import timezone

    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor SoftDel", programa=prog)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_BAJA,
        deleted_at=timezone.now(),
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina_actualizada = Nomina.all_objects.get(pk=nomina.pk)
    assert nomina_actualizada.comedor_id == comedor.pk


def test_comedores_views_exporta_vistas_directas():
    """comedores.views expone las tres vistas de nómina directa."""
    assert NominaDirectaDetailView.__name__ == "NominaDirectaDetailView"
    assert NominaDirectaCreateView.__name__ == "NominaDirectaCreateView"
    assert NominaDirectaDeleteView.__name__ == "NominaDirectaDeleteView"
