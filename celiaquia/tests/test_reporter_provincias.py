import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from users.models import Profile

from celiaquia.models import EstadoExpediente, EstadoLegajo, Expediente, ExpedienteCiudadano


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
