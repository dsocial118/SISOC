"""Regresión del 500 en el detalle de un relevamiento (producción, 6/9).

MySQL rechaza un ``ORDER BY`` cuando el ancho de una sola fila no entra en el
sort buffer (error 1038 "Out of sort memory"), **aunque la tabla esté vacía**:
decide por el ancho, no por la cantidad de filas. La consulta de casos
arrastraba el JSON del instrumento y el relevamiento entero por
``select_related``. SQLite no tiene sort buffer, así que esto no se puede
reproducir acá: lo que se verifica es que las consultas queden angostas.
"""

import datetime

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from core.models import Localidad, Municipio, Provincia
from datacalle.models import Encuesta, Relevamiento
from datacalle.services import get_encuestas_para_listado, get_encuestas_queryset


@pytest.fixture
def escenario(db):
    provincia = Provincia.objects.create(nombre="Córdoba")
    municipio = Municipio.objects.create(nombre="Córdoba Capital", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    relevamiento = Relevamiento.objects.create(
        denominacion="Operativo",
        provincia=provincia,
        municipio=municipio,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 15),
        fecha_fin=datetime.date(2026, 9, 19),
    )
    relevamiento.localidades.add(localidad)
    return relevamiento


def _usuario(username="coord_repro"):
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="datacalle",
            codename__in=["view_relevamiento", "view_encuesta"],
        )
    )
    return user


@pytest.mark.django_db
def test_el_listado_de_casos_no_arrastra_el_json_ni_el_relevamiento(escenario):
    sql = str(get_encuestas_para_listado(escenario).query)

    assert "respuestas" not in sql, "el JSON del instrumento engorda el ORDER BY"
    assert "datacalle_relevamiento" not in sql, "no hace falta el join"
    assert "ORDER BY" in sql


@pytest.mark.django_db
def test_el_queryset_completo_no_hace_select_related(escenario):
    """Los serializers usan los ids locales; el join sólo ensancha la fila."""
    sql = str(get_encuestas_queryset(escenario).query)

    assert "respuestas" in sql
    assert "INNER JOIN" not in sql
    assert "LEFT OUTER JOIN" not in sql


@pytest.mark.django_db
def test_detalle_del_operativo_sin_casos_responde_200(client, escenario):
    """El 500 de producción aparecía con la tabla de casos vacía."""
    client.force_login(_usuario())

    respuesta = client.get(f"/datacalle/relevamientos/{escenario.pk}/")

    assert respuesta.status_code == 200
    assert "Todavía no llegaron casos" in respuesta.content.decode()


@pytest.mark.django_db
def test_detalle_del_operativo_con_casos_responde_200(client, escenario):
    Encuesta.objects.create(
        relevamiento=escenario,
        estado=Encuesta.Estado.COMPLETA,
        codigo_entrevistado="ABCD01011990",
        respuestas={"codigoEntrevistado": "ABCD01011990", "realizaEntrevista": "si"},
    )
    client.force_login(_usuario("coord_con_casos"))

    respuesta = client.get(f"/datacalle/relevamientos/{escenario.pk}/")

    assert respuesta.status_code == 200
    assert "ABCD01011990" in respuesta.content.decode()
