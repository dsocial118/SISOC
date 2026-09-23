"""Resumen de nómina: todos los datos cuentan asistentes activos (issue #2507).

Situación previa:
 - el legajo mostraba "Asistentes" con el total de registros, sin discriminar
   estado;
 - el detalle mostraba "Asistentes" solo activos, pero "Género" con el total;
 - no había forma de ver los dados de baja.

`cantidad_total` sigue siendo el total real de registros a propósito: la API lo
usa como `count` de paginación.
"""

from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from ciudadanos.models import Ciudadano, Sexo
from comedores.models import Comedor, Nomina, Programas
from comedores.services.comedor_service import ComedorService
from comedores.views.comedor import _build_nomina_metrics

pytestmark = pytest.mark.django_db


@pytest.fixture(name="sexos")
def sexos_fixture():
    return {
        nombre: Sexo.objects.get_or_create(sexo=nombre)[0]
        for nombre in ("Masculino", "Femenino", "X")
    }


def _ciudadano(sexo, documento, fecha_nacimiento=None):
    return Ciudadano.objects.create(
        nombre="N",
        apellido="A",
        documento=documento,
        sexo=sexo,
        fecha_nacimiento=fecha_nacimiento,
    )


def _comedor():
    return Comedor.objects.create(nombre=f"Comedor {Comedor.objects.count() + 1}")


def _armar_nomina(comedor, sexos, filas):
    """`filas` es una lista de (sexo, estado)."""
    for indice, (sexo, estado) in enumerate(filas, start=1):
        Nomina.objects.create(
            comedor=comedor,
            admision=None,
            ciudadano=_ciudadano(sexos[sexo], f"{comedor.id}{indice:05d}"),
            estado=estado,
        )


def _resumen(comedor):
    (
        _page,
        hombres,
        mujeres,
        no_binarios,
        espera,
        total,
        rangos,
    ) = ComedorService.get_nomina_detail_by_comedor(comedor.id, page=1, per_page=1)
    return {
        "hombres": hombres,
        "mujeres": mujeres,
        "no_binarios": no_binarios,
        "espera": espera,
        "total": total,
        "rangos": rangos,
    }


def test_genero_cuenta_solo_activos(sexos):
    """Era el bug del detalle: Género traía el total de registros."""
    comedor = _comedor()
    _armar_nomina(
        comedor,
        sexos,
        [
            ("Masculino", Nomina.ESTADO_ACTIVO),
            ("Masculino", Nomina.ESTADO_BAJA),
            ("Femenino", Nomina.ESTADO_ACTIVO),
            ("Femenino", Nomina.ESTADO_ESPERA),
            ("X", Nomina.ESTADO_ACTIVO),
            ("X", Nomina.ESTADO_BAJA),
        ],
    )

    resumen = _resumen(comedor)

    assert resumen["hombres"] == 1
    assert resumen["mujeres"] == 1
    assert resumen["no_binarios"] == 1


def test_cantidad_activos_no_incluye_espera_ni_baja(sexos):
    comedor = _comedor()
    _armar_nomina(
        comedor,
        sexos,
        [
            ("Masculino", Nomina.ESTADO_ACTIVO),
            ("Femenino", Nomina.ESTADO_ACTIVO),
            ("Masculino", Nomina.ESTADO_ESPERA),
            ("Femenino", Nomina.ESTADO_BAJA),
            ("X", Nomina.ESTADO_BAJA),
        ],
    )

    resumen = _resumen(comedor)

    assert resumen["rangos"]["cantidad_activos"] == 2
    assert resumen["espera"] == 1
    assert resumen["rangos"]["baja"] == 2


def test_el_resumen_expone_espera_y_baja(sexos):
    """El legajo los necesita sin cambiar la forma de la tupla del servicio."""
    comedor = _comedor()
    _armar_nomina(
        comedor,
        sexos,
        [("Masculino", Nomina.ESTADO_ESPERA), ("Femenino", Nomina.ESTADO_BAJA)],
    )

    rangos = _resumen(comedor)["rangos"]

    assert rangos["espera"] == 1
    assert rangos["baja"] == 1


def test_cantidad_total_sigue_siendo_el_total_de_registros(sexos):
    """La API la usa como `count` de paginación: no debe filtrar por estado."""
    comedor = _comedor()
    _armar_nomina(
        comedor,
        sexos,
        [
            ("Masculino", Nomina.ESTADO_ACTIVO),
            ("Femenino", Nomina.ESTADO_ESPERA),
            ("X", Nomina.ESTADO_BAJA),
        ],
    )

    assert _resumen(comedor)["total"] == 3


def test_una_nomina_sin_activos_da_cero_en_todo(sexos):
    comedor = _comedor()
    _armar_nomina(
        comedor,
        sexos,
        [("Masculino", Nomina.ESTADO_BAJA), ("Femenino", Nomina.ESTADO_BAJA)],
    )

    resumen = _resumen(comedor)

    assert resumen["hombres"] == 0
    assert resumen["mujeres"] == 0
    assert resumen["rangos"]["cantidad_activos"] == 0
    assert resumen["rangos"]["baja"] == 2


# --- El legajo -----------------------------------------------------------


def test_el_legajo_muestra_activos_y_bajas(sexos):
    """ "Asistentes" del legajo ya no cuenta inactivos, y se agregan las bajas."""
    comedor = _comedor()
    _armar_nomina(
        comedor,
        sexos,
        [
            ("Masculino", Nomina.ESTADO_ACTIVO),
            ("Femenino", Nomina.ESTADO_ACTIVO),
            ("X", Nomina.ESTADO_ESPERA),
            ("Masculino", Nomina.ESTADO_BAJA),
        ],
    )
    resumen = _resumen(comedor)

    metrics = _build_nomina_metrics(resumen["rangos"])

    assert metrics["nomina_asistentes"] == 2, "Asistentes debe contar solo activos"
    assert metrics["nomina_bajas"] == 1
    assert resumen["total"] == 4, "el total de registros no cambia"


def test_el_grafico_de_edades_del_legajo_se_calcula_sobre_activos(sexos):
    """Espera y baja no cuentan como "Sin dato" ni achican los porcentajes."""
    comedor = _comedor()
    hoy = timezone.now().date()
    adulto = date(hoy.year - 30, hoy.month, 1)
    filas = [
        (adulto, Nomina.ESTADO_ACTIVO),
        (adulto, Nomina.ESTADO_ACTIVO),
        (adulto, Nomina.ESTADO_ACTIVO),
        (None, Nomina.ESTADO_ACTIVO),
        (adulto, Nomina.ESTADO_ESPERA),
        (adulto, Nomina.ESTADO_BAJA),
    ]
    for indice, (fecha_nacimiento, estado) in enumerate(filas, start=1):
        Nomina.objects.create(
            comedor=comedor,
            admision=None,
            ciudadano=_ciudadano(
                sexos["Femenino"], f"{comedor.id}{indice:05d}", fecha_nacimiento
            ),
            estado=estado,
        )

    metrics = _build_nomina_metrics(_resumen(comedor)["rangos"])

    # 4 activos: 3 adultos y 1 sin fecha de nacimiento. Antes se dividía por los
    # 6 registros y daba 50% / 50%.
    assert metrics["nomina_pct_adultos"] == 75
    assert metrics["nomina_pct_sin_dato"] == 25


def test_las_metricas_toleran_un_resumen_vacio():
    metrics = _build_nomina_metrics({})

    assert metrics["nomina_asistentes"] == 0
    assert metrics["nomina_bajas"] == 0
    assert metrics["nomina_pct_sin_dato"] == 0


def test_el_legajo_renderiza_asistentes_activos_y_bajas(
    sexos, client, django_user_model
):
    user = django_user_model.objects.create_superuser(
        username="nomina_legajo_admin",
        password="testpass",
        email="nomina-legajo@example.com",
    )
    client.force_login(user)
    programa = Programas.objects.create(
        nombre="Programa nomina directa", usa_admision_para_nomina=False
    )
    comedor = Comedor.objects.create(nombre="Comedor legajo", programa=programa)
    _armar_nomina(
        comedor,
        sexos,
        [
            ("Masculino", Nomina.ESTADO_ACTIVO),
            ("Femenino", Nomina.ESTADO_ACTIVO),
            ("X", Nomina.ESTADO_ESPERA),
            ("Masculino", Nomina.ESTADO_BAJA),
            ("Femenino", Nomina.ESTADO_BAJA),
        ],
    )

    response = client.get(reverse("comedor_detalle", kwargs={"pk": comedor.id}))

    assert response.status_code == 200
    assert response.context["nomina_asistentes"] == 2
    assert response.context["nomina_bajas"] == 2
    assert "Dados de baja" in response.content.decode()
