from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from users.models import Profile

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)


def _create_user_with_permission(username, provincia=None, es_provincial=False):
    user = User.objects.create_user(username=username, password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = es_provincial
    profile.provincia = provincia
    profile.save()
    return user


@pytest.mark.django_db
def test_reporter_provincias_paginates_results_and_preserves_filters(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = _create_user_with_permission("reporter", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="CREADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")

    for index in range(13):
        expediente = Expediente.objects.create(
            usuario_provincia=user,
            estado=estado_expediente,
            numero_expediente=f"EXP-{index:03d}",
        )
        ciudadano = Ciudadano.objects.create(
            apellido=f"Apellido {index}",
            nombre=f"Nombre {index}",
            documento=20000000 + index,
        )
        ExpedienteCiudadano.objects.create(
            expediente=expediente,
            ciudadano=ciudadano,
            estado=estado_legajo,
            revision_tecnico="APROBADO",
        )

    client.force_login(user)
    response = client.get(
        reverse("reporter_provincias"),
        {
            "revision_tecnico": "APROBADO",
            "resultado_sintys": "",
            "documento_persona": "",
            "page": 2,
        },
    )

    assert response.status_code == 200
    assert response.context["page_obj"].number == 2
    assert response.context["page_obj"].paginator.count == 13
    assert len(response.context["ultimos_casos"]) == 1
    assert response.context["current_querystring"] == "revision_tecnico=APROBADO"
    assert response.context["detalle_desde"] == 13
    assert response.context["detalle_hasta"] == 13
    assert response.context["metricas_principales"][1]["value"] == "100,0%"


@pytest.mark.django_db
def test_reporter_provincias_clasifica_aprobados_por_rol(client):
    """El reporte clasifica los legajos APROBADOS por rol/edad en categorías
    mutuamente excluyentes cuyos subtotales suman el total de aprobados."""
    provincia = Provincia.objects.create(nombre="Mendoza Clasif")
    user = _create_user_with_permission("reporter-clasif", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="ARCHIVO_CARGADO_CLASIF")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
        numero_expediente="EXP-CLASIF-001",
    )

    casos = [
        # (documento, rol, fecha_nacimiento, revision_tecnico)
        (41000001, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(1990, 1, 1), "APROBADO"),
        (41000002, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(1985, 5, 5), "APROBADO"),
        (
            41000003,
            ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE,
            date(1980, 3, 3),
            "APROBADO",
        ),
        (41000004, ExpedienteCiudadano.ROLE_RESPONSABLE, date(1975, 7, 7), "APROBADO"),
        # Menor de edad: cae en "menor" aunque su rol sea beneficiario.
        (41000005, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(2015, 2, 2), "APROBADO"),
        # No aprobado: excluido del conteo.
        (
            41000006,
            ExpedienteCiudadano.ROLE_BENEFICIARIO,
            date(1992, 9, 9),
            "PENDIENTE",
        ),
    ]
    for documento, rol, fnac, revision in casos:
        ciudadano = Ciudadano.objects.create(
            apellido="Test",
            nombre=f"C{documento}",
            documento=documento,
            fecha_nacimiento=fnac,
            provincia=provincia,
        )
        ExpedienteCiudadano.objects.create(
            expediente=expediente,
            ciudadano=ciudadano,
            estado=estado_legajo,
            rol=rol,
            revision_tecnico=revision,
        )

    client.force_login(user)
    response = client.get(reverse("reporter_provincias"))

    assert response.status_code == 200
    clasificacion = response.context["clasificacion_aprobados"]
    counts = {item["code"]: item["count"] for item in clasificacion["items"]}

    assert counts == {
        "beneficiario": 2,
        "doble_rol": 1,
        "responsable": 1,
        "menor": 1,
    }
    assert clasificacion["total"] == 5  # los 5 aprobados, el PENDIENTE no cuenta
    assert sum(counts.values()) == clasificacion["total"]

    content = response.content.decode()
    assert "Clasificación por rol" in content
    assert "Beneficiario únicamente" in content


@pytest.mark.django_db
def test_reporter_provincias_renders_redesigned_sections(client):
    provincia = Provincia.objects.create(nombre="Jujuy")
    user = _create_user_with_permission("reporter-render", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="EN_PROCESO")
    estado_legajo = EstadoLegajo.objects.create(nombre="REVISION")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
        numero_expediente="EXP-RENDER-001",
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Ana",
        documento=30111222,
    )
    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )

    client.force_login(user)
    response = client.get(reverse("reporter_provincias"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Panorama general de legajos por provincia" in content
    assert "Detalle paginado" in content
    assert "reporterQuickSearch" in content
    assert "custom/js/reporter_provincias.js" in content
