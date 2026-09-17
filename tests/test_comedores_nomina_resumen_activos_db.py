"""Resumen de nómina: todos los datos cuentan asistentes activos (issue #2507).

Situación previa:
 - el legajo mostraba "Asistentes" con el total de registros, sin discriminar
   estado;
 - el detalle mostraba "Asistentes" solo activos, pero "Género" con el total;
 - no había forma de ver los dados de baja.

`cantidad_total` sigue siendo el total real de registros a propósito: la API lo
usa como `count` de paginación.
"""

import pytest

from ciudadanos.models import Ciudadano, Sexo
from comedores.models import Comedor, Nomina
from comedores.services.comedor_service import ComedorService

pytestmark = pytest.mark.django_db


@pytest.fixture(name="sexos")
def sexos_fixture():
    return {
        nombre: Sexo.objects.get_or_create(sexo=nombre)[0]
        for nombre in ("Masculino", "Femenino", "X")
    }


def _ciudadano(sexo, documento):
    return Ciudadano.objects.create(
        nombre="N", apellido="A", documento=documento, sexo=sexo
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
    from comedores.views.comedor import _build_nomina_metrics

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

    metrics = _build_nomina_metrics(resumen["total"], resumen["rangos"])

    assert metrics["nomina_asistentes"] == 2, "Asistentes debe contar solo activos"
    assert metrics["nomina_bajas"] == 1
    assert resumen["total"] == 4, "el total de registros no cambia"


def test_las_metricas_toleran_un_resumen_vacio():
    from comedores.views.comedor import _build_nomina_metrics

    metrics = _build_nomina_metrics(0, {})

    assert metrics["nomina_asistentes"] == 0
    assert metrics["nomina_bajas"] == 0


def test_el_legajo_renderiza_la_tarjeta_de_bajas():
    """La tarjeta nueva tiene que llegar al HTML con su par de colores."""
    from pathlib import Path

    html = Path("comedores/templates/comedor/comedor_detail.html").read_text(
        encoding="utf-8"
    )
    seccion = html.split("<!-- Nomina-->", 1)[1].split("<!-- /Nomina-->", 1)[0]

    assert "Dados de baja" in seccion
    assert "{{ nomina_bajas|default:0 }}" in seccion
    # "Asistentes" ya no usa el total de registros.
    assert "{{ nomina_asistentes|default:0 }}" in seccion
    assert "{{ nomina_total|default:0 }}" not in seccion

    for hoja in ("comedor_detail.css", "nuevo_comedor.css"):
        css = Path(f"static/custom/css/{hoja}").read_text(encoding="utf-8")
        assert ".bg-gris {" in css, f"{hoja} sin .bg-gris"
        assert ".bg-gris-75 {" in css, f"{hoja} sin .bg-gris-75"
