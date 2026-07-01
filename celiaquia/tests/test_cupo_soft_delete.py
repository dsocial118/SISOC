"""Prevención: soft-borrar un titular con cupo libera el cupo (usados) y
restaurarlo lo vuelve a contar. Evita el descuadre de ProvinciaCupo.usados."""

import pytest
from django.contrib.auth.models import User

from ciudadanos.models import Ciudadano
from core.models import Provincia
from celiaquia.models import (
    EstadoCupo,
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    ProvinciaCupo,
    ResultadoSintys,
    RevisionTecnico,
)
from celiaquia.services.cupo_service import CupoService


def _usados(provincia):
    return ProvinciaCupo.objects.get(provincia=provincia).usados


def _titular(exp, est_leg, provincia, documento):
    ciudadano = Ciudadano.objects.create(
        apellido="Ape", nombre=f"N{documento}", documento=documento, provincia=provincia
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=exp,
        ciudadano=ciudadano,
        estado=est_leg,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
        revision_tecnico=RevisionTecnico.APROBADO,
        resultado_sintys=ResultadoSintys.MATCH,
    )
    CupoService.reservar_slot(legajo=legajo, usuario=None)
    legajo.refresh_from_db()
    return legajo


@pytest.mark.django_db
def test_soft_delete_titular_libera_cupo_y_restore_lo_recupera():
    prov = Provincia.objects.create(nombre="Testlandia")
    ProvinciaCupo.objects.create(provincia=prov, total_asignado=5, usados=0)
    user = User.objects.create_superuser("cupo-sd", password="x")
    exp = Expediente.objects.create(
        usuario_provincia=user,
        estado=EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO"),
    )
    est_leg = EstadoLegajo.objects.create(nombre="VALIDO")

    legajo = _titular(exp, est_leg, prov, 30000001)
    assert legajo.estado_cupo == EstadoCupo.DENTRO
    assert _usados(prov) == 1

    # Soft-delete del titular -> libera el cupo
    legajo.delete(user=user)
    assert _usados(prov) == 0  # antes quedaba en 1 (descuadre)

    # Restore -> vuelve a contar
    legajo.restore(user=user)
    assert _usados(prov) == 1


@pytest.mark.django_db
def test_delete_expediente_en_cascada_libera_cupo_de_sus_titulares():
    prov = Provincia.objects.create(nombre="Cascadia")
    ProvinciaCupo.objects.create(provincia=prov, total_asignado=5, usados=0)
    user = User.objects.create_superuser("cupo-casc", password="x")
    exp = Expediente.objects.create(
        usuario_provincia=user,
        estado=EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO"),
    )
    est_leg = EstadoLegajo.objects.create(nombre="VALIDO")

    _titular(exp, est_leg, prov, 30000002)
    _titular(exp, est_leg, prov, 30000003)
    assert _usados(prov) == 2

    # Borrar el expediente en cascada libera el cupo de ambos titulares
    exp.delete(user=user)
    assert _usados(prov) == 0
