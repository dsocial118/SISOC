"""Buscadores homogeneos: filtros combinables en todos los listados.

Cubre las pantallas que se migraron al componente de filtros combinables,
verificando que ademas de renderizar la UI el filtro efectivamente filtra y que
la busqueda que cada listado ya tenia sigue funcionando.
"""

import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _filtros(items):
    return json.dumps({"logic": "AND", "items": items})


@pytest.fixture
def admin(client):
    usuario = User.objects.create_superuser("admin_busc", "b@b.com", "test")
    client.force_login(usuario)
    return usuario


LISTADOS_MIGRADOS = [
    "importarexpedientes_list",
    "centrodeinfancia",
    "vpsl_itinerario_list",
    "vpsl_sede_list",
    "vat_modalidadcursada_list",
    "vat_planversioncurricular_list",
]


@pytest.mark.parametrize("nombre_url", LISTADOS_MIGRADOS)
def test_el_listado_expone_el_buscador_de_filtros_combinables(
    client, admin, nombre_url
):
    response = client.get(reverse(nombre_url))
    contenido = response.content.decode()

    assert response.status_code == 200
    assert response.context["filters_mode"] is True
    assert response.context["filters_config"]["fields"]
    assert "poncho-filter-row-template" in contenido
    assert "filters-config-json" in contenido


@pytest.mark.parametrize("nombre_url", LISTADOS_MIGRADOS)
def test_la_config_declara_campos_con_tipo_y_operadores(client, admin, nombre_url):
    config = client.get(reverse(nombre_url)).context["filters_config"]

    assert config["defaultField"]
    for field in config["fields"]:
        assert field["name"] and field["label"] and field["type"]
        assert config["operators"].get(field["type"]), field


def test_modalidad_cursada_filtra_por_nombre(client, admin):
    from VAT.models import ModalidadCursada

    buscada = ModalidadCursada.objects.create(nombre="Presencial intensiva")
    ModalidadCursada.objects.create(nombre="Virtual")

    response = client.get(
        reverse("vat_modalidadcursada_list"),
        {
            "filters": _filtros(
                [{"field": "nombre", "op": "contains", "value": "inten"}]
            )
        },
    )

    assert [m.pk for m in response.context["modalidades"]] == [buscada.pk]


def test_modalidad_cursada_ya_no_arrastra_la_busqueda_vieja(client, admin):
    """El buscador simple era decorativo: la vista nunca aplicaba `busqueda`.

    Al migrar a filtros combinables se removio, porque ya no hay input que lo
    dispare: el parametro no tiene que alterar el listado.
    """

    from VAT.models import ModalidadCursada

    ModalidadCursada.objects.create(nombre="Semipresencial")
    ModalidadCursada.objects.create(nombre="Virtual")

    response = client.get(reverse("vat_modalidadcursada_list"), {"busqueda": "Semi"})

    assert response.context["modalidades"].count() == 2


def test_sede_vpsl_combina_dos_filtros(client, admin):
    from ver_para_ser_libre.models import SedeVPSL

    objetivo = SedeVPSL.objects.create(
        nombre="Escuela Norte", jurisdiccion="Chaco", localidad="Resistencia"
    )
    SedeVPSL.objects.create(
        nombre="Escuela Norte", jurisdiccion="Salta", localidad="Salta"
    )
    SedeVPSL.objects.create(
        nombre="Otra", jurisdiccion="Chaco", localidad="Resistencia"
    )

    response = client.get(
        reverse("vpsl_sede_list"),
        {
            "filters": _filtros(
                [
                    {"field": "nombre", "op": "contains", "value": "Norte"},
                    {"field": "jurisdiccion", "op": "eq", "value": "Chaco"},
                ]
            )
        },
    )

    assert [s.pk for s in response.context["sedes"]] == [objetivo.pk]


def test_sede_vpsl_busca_por_domicilio_con_el_filtro_combinable(client, admin):
    """El texto libre se reemplazo por el filtro combinable sobre el mismo campo."""

    from ver_para_ser_libre.models import SedeVPSL

    objetivo = SedeVPSL.objects.create(nombre="Sede Uno", domicilio="Calle Falsa 123")
    SedeVPSL.objects.create(nombre="Sede Dos", domicilio="Otra")

    response = client.get(
        reverse("vpsl_sede_list"),
        {
            "filters": _filtros(
                [{"field": "domicilio", "op": "contains", "value": "Falsa"}]
            )
        },
    )

    assert [s.pk for s in response.context["sedes"]] == [objetivo.pk]


def test_centro_de_infancia_filtra_por_organizacion(client, admin):
    from centrodeinfancia.models import CentroDeInfancia

    objetivo = CentroDeInfancia.objects.create(
        nombre="CDI Uno", organizacion="Fundación Alfa"
    )
    CentroDeInfancia.objects.create(nombre="CDI Dos", organizacion="Fundación Beta")

    response = client.get(
        reverse("centrodeinfancia"),
        {
            "filters": _filtros(
                [{"field": "organizacion", "op": "contains", "value": "Alfa"}]
            )
        },
    )

    assert [c.pk for c in response.context["centros"]] == [objetivo.pk]


def test_importar_expedientes_filtra_por_usuario(client, admin):
    from importarexpediente.models import ArchivosImportados

    otro = User.objects.create_user("carga_masiva", password="x")
    objetivo = ArchivosImportados.objects.create(archivo="uno.csv", usuario=otro)
    ArchivosImportados.objects.create(archivo="dos.csv", usuario=admin)

    response = client.get(
        reverse("importarexpedientes_list"),
        {
            "filters": _filtros(
                [{"field": "usuario", "op": "contains", "value": "carga_masiva"}]
            )
        },
    )

    assert [a.pk for a in response.context["archivos_importados"]] == [objetivo.pk]


def test_plan_curricular_conserva_sus_filtros_propios(client, admin):
    """Los filtros de titulo/activo del listado siguen conviviendo con los combinables."""

    from VAT.models import ModalidadCursada, PlanVersionCurricular, Sector

    sector = Sector.objects.create(nombre="Industria")
    modalidad = ModalidadCursada.objects.create(nombre="Presencial")
    activo = PlanVersionCurricular.objects.create(
        nombre="Plan activo", sector=sector, modalidad_cursada=modalidad, activo=True
    )
    PlanVersionCurricular.objects.create(
        nombre="Plan inactivo",
        sector=sector,
        modalidad_cursada=modalidad,
        activo=False,
    )

    response = client.get(reverse("vat_planversioncurricular_list"), {"activo": "true"})

    assert [p.pk for p in response.context["planes"]] == [activo.pk]


def test_plan_curricular_filtra_por_campo_combinable(client, admin):
    from VAT.models import ModalidadCursada, PlanVersionCurricular, Sector

    sector = Sector.objects.create(nombre="Industria")
    modalidad = ModalidadCursada.objects.create(nombre="Presencial")
    objetivo = PlanVersionCurricular.objects.create(
        nombre="Electricidad", sector=sector, modalidad_cursada=modalidad
    )
    PlanVersionCurricular.objects.create(
        nombre="Gastronomía", sector=sector, modalidad_cursada=modalidad
    )

    response = client.get(
        reverse("vat_planversioncurricular_list"),
        {
            "filters": _filtros(
                [{"field": "nombre", "op": "contains", "value": "Electri"}]
            )
        },
    )

    assert [p.pk for p in response.context["planes"]] == [objetivo.pk]


def test_itinerarios_conserva_su_busqueda_libre_y_su_panel(client, admin):
    """Unica pantalla donde el buscador propio del modulo sigue vivo.

    Su logica no es expresable con el engine (OR entre siete campos, mapeo de
    estado por texto, provincia segun permisos), asi que se mantiene y viaja en
    el mismo submit que los filtros combinables.
    """

    contenido = client.get(reverse("vpsl_itinerario_list")).content.decode()

    assert 'name="busqueda"' in contenido
    assert 'form="filters-form"' in contenido
    assert "poncho-filter-row-template" in contenido
