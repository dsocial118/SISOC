import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from comedores.models import Comedor, CursoAppMobile, Programas
from core.models import Provincia
from pwa.api_views import CursoAppMobilePWAViewSet
from users.models import AccesoComedorPWA


pytestmark = pytest.mark.django_db


def _create_representante(*, comedor, username="rep_formacion"):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    return user


def _create_comedor(programa_nombre):
    provincia = Provincia.objects.create(nombre=f"Provincia {programa_nombre}")
    programa = Programas.objects.create(nombre=programa_nombre)
    return Comedor.objects.create(
        nombre=f"Espacio {programa_nombre}",
        provincia=provincia,
        programa=programa,
    )


def _formacion_url(comedor):
    return f"/api/pwa/espacios/{comedor.id}/formacion/cursos/"


def _get_formacion_response(*, user, comedor):
    request = APIRequestFactory().get(_formacion_url(comedor))
    force_authenticate(request, user=user)
    view = CursoAppMobilePWAViewSet.as_view({"get": "list"})
    return view(request, comedor_id=comedor.id)


def test_formacion_pwa_filtra_cursos_para_pnud():
    comedor = _create_comedor("PNUD - SECOS")
    representante = _create_representante(comedor=comedor)

    CursoAppMobile.objects.create(
        nombre="Curso PNUD",
        link="https://example.com/pnud",
        programa_objetivo=CursoAppMobile.PROGRAMA_PNUD,
        orden=1,
    )
    CursoAppMobile.objects.create(
        nombre="Curso Ambos",
        link="https://example.com/ambos",
        programa_objetivo=CursoAppMobile.PROGRAMA_AMBOS,
        orden=2,
    )
    CursoAppMobile.objects.create(
        nombre="Curso Alimentar",
        link="https://example.com/alimentar",
        programa_objetivo=CursoAppMobile.PROGRAMA_ALIMENTAR,
        orden=3,
    )
    CursoAppMobile.objects.create(
        nombre="Curso Inactivo",
        link="https://example.com/inactivo",
        programa_objetivo=CursoAppMobile.PROGRAMA_PNUD,
        activo=False,
    )

    response = _get_formacion_response(user=representante, comedor=comedor)

    assert response.status_code == 200
    assert [item["nombre"] for item in response.data["results"]] == [
        "Curso PNUD",
        "Curso Ambos",
    ]


def test_formacion_pwa_filtra_cursos_para_alimentar_comunidad():
    comedor = _create_comedor("Alimentar Comunidad")
    representante = _create_representante(comedor=comedor, username="rep_alimentar")

    CursoAppMobile.objects.create(
        nombre="Curso PNUD",
        link="https://example.com/pnud",
        programa_objetivo=CursoAppMobile.PROGRAMA_PNUD,
        orden=1,
    )
    CursoAppMobile.objects.create(
        nombre="Curso Alimentar",
        link="https://example.com/alimentar",
        programa_objetivo=CursoAppMobile.PROGRAMA_ALIMENTAR,
        orden=2,
    )
    CursoAppMobile.objects.create(
        nombre="Curso Ambos",
        link="https://example.com/ambos",
        programa_objetivo=CursoAppMobile.PROGRAMA_AMBOS,
        orden=3,
    )

    response = _get_formacion_response(user=representante, comedor=comedor)

    assert response.status_code == 200
    assert [item["nombre"] for item in response.data["results"]] == [
        "Curso Alimentar",
        "Curso Ambos",
    ]


def test_formacion_pwa_devuelve_vacio_para_programa_no_soportado():
    comedor = _create_comedor("Otro Programa")
    representante = _create_representante(comedor=comedor, username="rep_otro")
    CursoAppMobile.objects.create(
        nombre="Curso Ambos",
        link="https://example.com/ambos",
        programa_objetivo=CursoAppMobile.PROGRAMA_AMBOS,
    )

    response = _get_formacion_response(user=representante, comedor=comedor)

    assert response.status_code == 200
    assert response.data["results"] == []
