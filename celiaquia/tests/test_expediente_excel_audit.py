"""Tests de auditoria del Excel masivo en expedientes de Celiaquia."""

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from celiaquia.models import AsignacionTecnico, EstadoExpediente, Expediente
from celiaquia.services.expediente_service import ExpedienteService
from core.models import Provincia
from users.models import Profile


def _permission(app_label, codename):
    try:
        return Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
    except Permission.DoesNotExist:
        content_type = ContentType.objects.get(app_label="auth", model="user")
        return Permission.objects.create(
            content_type=content_type,
            codename=codename,
            name=codename,
        )


def _grant(user, app_label, codename):
    user.user_permissions.add(_permission(app_label, codename))


def _user(username, *, superuser=False, coord=False, tecnico=False, provincial=False):
    user = User.objects.create_user(
        username=username,
        password="pass",
        first_name=username.title(),
    )
    user.is_superuser = superuser
    user.save(update_fields=["is_superuser"])

    if not superuser:
        _grant(user, "celiaquia", "view_expediente")
    if coord:
        _grant(user, "auth", "role_coordinadorceliaquia")
    if tecnico:
        _grant(user, "auth", "role_tecnicoceliaquia")
    if provincial:
        provincia = Provincia.objects.create(nombre=f"Provincia {username}")
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.es_usuario_provincial = True
        profile.provincia = provincia
        profile.save()
    return user


def _estado(nombre="CREADO"):
    return EstadoExpediente.objects.create(nombre=nombre)


def _excel_upload(name="carga.xlsx", content=b"excel-bytes"):
    return SimpleUploadedFile(
        name,
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _expediente_con_excel(settings, tmp_path, usuario, *, estado_nombre="CREADO"):
    settings.MEDIA_ROOT = tmp_path
    expediente = Expediente.objects.create(
        usuario_provincia=usuario,
        estado=_estado(estado_nombre),
        excel_masivo_cargado_por=usuario,
        excel_masivo_cargado_en=timezone.now(),
    )
    expediente.excel_masivo.save(
        "carga_original.xlsx", ContentFile(b"excel-original"), save=True
    )
    return expediente


@pytest.mark.django_db
def test_admin_y_coordinador_ven_auditoria_y_descargan_excel(
    client, settings, tmp_path
):
    provincia = _user("provincial", provincial=True)
    admin = _user("admin", superuser=True)
    coordinador = _user("coord", coord=True)
    expediente = _expediente_con_excel(settings, tmp_path, provincia)
    expediente.excel_masivo_procesado_por = coordinador
    expediente.excel_masivo_procesado_en = timezone.now()
    expediente.save(
        update_fields=[
            "excel_masivo_procesado_por",
            "excel_masivo_procesado_en",
        ]
    )

    for viewer in (admin, coordinador):
        client.force_login(viewer)
        detail = client.get(reverse("expediente_detail", args=[expediente.pk]))
        assert detail.status_code == 200
        content = detail.content.decode()
        assert "Descargar Excel Provincia" in content
        assert "Excel original" in content
        assert "carga_original.xlsx" in content
        assert "Cargado por" in content
        assert "Procesado por" in content

        listing = client.get(reverse("expediente_list"))
        assert listing.status_code == 200
        assert "Excel original" in listing.content.decode()

        download = client.get(
            reverse("expediente_excel_masivo_descargar", args=[expediente.pk])
        )
        assert download.status_code == 200
        assert "carga_original.xlsx" in download.headers["Content-Disposition"]
        assert b"".join(download.streaming_content) == b"excel-original"


@pytest.mark.django_db
def test_provincia_no_ve_auditoria_excel_y_no_descarga(client, settings, tmp_path):
    provincia = _user("provincia", provincial=True)
    expediente = _expediente_con_excel(settings, tmp_path, provincia)

    client.force_login(provincia)
    detail = client.get(reverse("expediente_detail", args=[expediente.pk]))
    assert detail.status_code == 200
    content = detail.content.decode()
    assert "Descargar Excel Provincia" not in content
    assert "Excel original" not in content

    listing = client.get(reverse("expediente_list"))
    assert listing.status_code == 200
    assert "Excel original" not in listing.content.decode()

    download = client.get(
        reverse("expediente_excel_masivo_descargar", args=[expediente.pk])
    )
    assert download.status_code == 403


@pytest.mark.django_db
def test_tecnico_no_descarga_excel_masivo(client, settings, tmp_path):
    provincia = _user("provincia-tec", provincial=True)
    tecnico = _user("tecnico", tecnico=True)
    expediente = _expediente_con_excel(settings, tmp_path, provincia)
    AsignacionTecnico.objects.create(expediente=expediente, tecnico=tecnico)

    client.force_login(tecnico)
    download = client.get(
        reverse("expediente_excel_masivo_descargar", args=[expediente.pk])
    )
    assert download.status_code == 403


@pytest.mark.django_db
def test_create_expediente_registra_usuario_y_fecha_de_carga(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    usuario = _user("creador", provincial=True)

    before = timezone.now()
    expediente = ExpedienteService.create_expediente(
        usuario_provincia=usuario,
        datos_metadatos={"numero_expediente": "EXP-1", "observaciones": "obs"},
        excel_masivo=_excel_upload(),
    )

    assert expediente.excel_masivo_cargado_por == usuario
    assert expediente.excel_masivo_cargado_en >= before
    assert expediente.excel_masivo_procesado_por is None
    assert expediente.excel_masivo_procesado_en is None


@pytest.mark.django_db
def test_procesar_expediente_registra_usuario_y_fecha_de_procesamiento(
    monkeypatch, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    provincia = _user("prov-procesa", provincial=True)
    expediente = _expediente_con_excel(settings, tmp_path, provincia)

    monkeypatch.setattr(
        "celiaquia.services.expediente_service.ImportacionService.importar_legajos_desde_excel",
        lambda *_args, **_kwargs: {
            "validos": 0,
            "errores": 0,
            "excluidos_count": 0,
            "excluidos": [],
        },
    )

    before = timezone.now()
    ExpedienteService.procesar_expediente(expediente, provincia)

    expediente.refresh_from_db()
    assert expediente.excel_masivo_procesado_por == provincia
    assert expediente.excel_masivo_procesado_en >= before


@pytest.mark.django_db
def test_reemplazar_excel_actualiza_carga_y_limpia_procesamiento(
    client, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    provincia = _user("prov-reemplaza", provincial=True)
    editor = _user("editor", superuser=True)
    expediente = _expediente_con_excel(settings, tmp_path, provincia)
    expediente.excel_masivo_procesado_por = provincia
    expediente.excel_masivo_procesado_en = timezone.now()
    expediente.save(
        update_fields=[
            "excel_masivo_procesado_por",
            "excel_masivo_procesado_en",
        ]
    )

    client.force_login(editor)
    response = client.post(
        reverse("expediente_update", args=[expediente.pk]),
        data={
            "numero_expediente": "EXP-REEMPLAZO",
            "observaciones": "archivo nuevo",
            "excel_masivo": _excel_upload("nuevo.xlsx", b"nuevo-excel"),
        },
    )

    assert response.status_code == 302
    expediente.refresh_from_db()
    assert expediente.excel_masivo_cargado_por == editor
    assert expediente.excel_masivo_cargado_en is not None
    assert expediente.excel_masivo_procesado_por is None
    assert expediente.excel_masivo_procesado_en is None
    assert expediente.excel_masivo.name.endswith("nuevo.xlsx")
