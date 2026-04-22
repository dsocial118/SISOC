from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from VAT.models import (
    Centro,
    ComisionCurso,
    Curso,
    InstitucionUbicacion,
    ModalidadCursada,
)
from core.models import Localidad, Municipio, Provincia


pytestmark = pytest.mark.django_db


def _create_vat_operational_state_context():
    provincia = Provincia.objects.create(nombre="Provincia Sync Soft Delete")
    municipio = Municipio.objects.create(
        nombre="Municipio Sync Soft Delete",
        provincia=provincia,
    )
    localidad = Localidad.objects.create(
        nombre="Localidad Sync Soft Delete",
        municipio=municipio,
    )
    modalidad = ModalidadCursada.objects.create(
        nombre="Modalidad Sync Soft Delete",
        activo=True,
    )
    centro = Centro.objects.create(
        nombre="Centro Sync Soft Delete",
        codigo="CFP-SYNC-1",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="1",
        numero=100,
        domicilio_actividad="Calle 1 100",
        telefono="221111111",
        celular="221111112",
        correo="centro-sync@vat.test",
        nombre_referente="Ana",
        apellido_referente="Perez",
        telefono_referente="221111113",
        correo_referente="referente-sync@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="CFP",
        situacion="Activa",
        activo=True,
    )
    ubicacion = InstitucionUbicacion.objects.create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="Calle 1 100",
        es_principal=True,
    )
    curso = Curso.objects.create(
        centro=centro,
        nombre="Curso Sync Soft Delete",
        modalidad=modalidad,
        estado="activo",
    )
    comision = ComisionCurso.objects.create(
        curso=curso,
        ubicacion=ubicacion,
        codigo_comision="SYNC-01",
        nombre="Comision Sync Soft Delete",
        cupo_total=30,
        fecha_inicio=date(2026, 4, 1),
        fecha_fin=date(2026, 4, 30),
        estado="activa",
    )
    return centro, curso, comision


def _mark_as_legacy_soft_deleted(instance):
    deleted_at = timezone.now()
    instance.__class__.all_objects.filter(pk=instance.pk).update(deleted_at=deleted_at)
    instance.deleted_at = deleted_at


def _reload_deleted(instance):
    return instance.__class__.all_objects.get(pk=instance.pk)


def test_sync_soft_deleted_operational_state_dry_run_reports_without_persisting():
    centro, curso, comision = _create_vat_operational_state_context()

    _mark_as_legacy_soft_deleted(centro)
    _mark_as_legacy_soft_deleted(curso)
    _mark_as_legacy_soft_deleted(comision)

    stdout = StringIO()

    call_command(
        "sync_soft_deleted_operational_state",
        "--dry-run",
        "--app-label",
        "VAT",
        stdout=stdout,
    )

    centro = _reload_deleted(centro)
    curso = _reload_deleted(curso)
    comision = _reload_deleted(comision)

    assert centro.activo is True
    assert curso.estado == "activo"
    assert comision.estado == "activa"

    output = stdout.getvalue()
    assert "VAT.Centro: 1 registro(s) -> {'activo': False}" in output
    assert "VAT.Curso: 1 registro(s) -> {'estado': 'cancelado'}" in output
    assert "VAT.ComisionCurso: 1 registro(s) -> {'estado': 'cerrada'}" in output
    assert "Detectados: 3 registro(s)." in output


def test_sync_soft_deleted_operational_state_updates_legacy_rows():
    centro, curso, comision = _create_vat_operational_state_context()

    _mark_as_legacy_soft_deleted(centro)
    _mark_as_legacy_soft_deleted(curso)
    _mark_as_legacy_soft_deleted(comision)

    stdout = StringIO()

    call_command(
        "sync_soft_deleted_operational_state",
        "--app-label",
        "VAT",
        stdout=stdout,
    )

    centro = _reload_deleted(centro)
    curso = _reload_deleted(curso)
    comision = _reload_deleted(comision)

    assert centro.activo is False
    assert curso.estado == "cancelado"
    assert comision.estado == "cerrada"

    output = stdout.getvalue()
    assert "VAT.Centro: 1 registro(s) -> {'activo': False}" in output
    assert "VAT.Curso: 1 registro(s) -> {'estado': 'cancelado'}" in output
    assert "VAT.ComisionCurso: 1 registro(s) -> {'estado': 'cerrada'}" in output
    assert "Sincronizados: 3 registro(s)." in output
