from datetime import date

import pytest
from django.core.exceptions import ValidationError

from centrodeinfancia.models import CentroDeInfancia, Trabajador


def _trabajador(**kwargs):
    centro = CentroDeInfancia.objects.create(nombre="CDI Test")
    defaults = {"centro": centro, "nombre": "Ana", "apellido": "Lopez"}
    defaults.update(kwargs)
    return Trabajador(**defaults)


# ─── clean(): funciones condicionales por subcomponente ────────────────────


@pytest.mark.django_db
def test_clean_borra_funcion_egp_cuando_subcomponente_no_es_egp():
    t = _trabajador(subcomponente="cdi", funcion_egp="coordinacion_general")
    t.full_clean()
    assert t.funcion_egp is None


@pytest.mark.django_db
def test_clean_preserva_funcion_egp_cuando_subcomponente_es_egp():
    t = _trabajador(subcomponente="egp", funcion_egp="coordinacion_general")
    t.full_clean()
    assert t.funcion_egp == "coordinacion_general"


@pytest.mark.django_db
def test_clean_borra_funcion_cdi_cuando_subcomponente_no_es_cdi():
    t = _trabajador(subcomponente="egp", funcion_cdi="educador_docente_sala")
    t.full_clean()
    assert t.funcion_cdi is None


@pytest.mark.django_db
def test_clean_preserva_funcion_cdi_cuando_subcomponente_es_cdi():
    t = _trabajador(subcomponente="cdi", funcion_cdi="auxiliar_sala")
    t.full_clean()
    assert t.funcion_cdi == "auxiliar_sala"


# ─── clean(): formación condicional por nivel educativo ────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    "nivel",
    [
        "nunca",
        "primario_completo",
        "secundario_incompleto",
        "secundario_en_curso",
    ],
)
def test_clean_borra_formacion_cuando_nivel_no_habilita(nivel):
    t = _trabajador(nivel_educativo=nivel, formacion_academica="psicologia")
    t.full_clean()
    assert t.formacion_academica is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "nivel",
    [
        "secundario_completo",
        "superior_incompleto",
        "superior_en_curso",
        "superior_completo",
    ],
)
def test_clean_preserva_formacion_cuando_nivel_habilita(nivel):
    t = _trabajador(nivel_educativo=nivel, formacion_academica="psicologia")
    t.full_clean()
    assert t.formacion_academica == "psicologia"


# ─── clean(): pueblo originario condicional ────────────────────────────────


@pytest.mark.django_db
def test_clean_borra_pueblo_originario_si_no_es_indigena():
    t = _trabajador(
        grupo_pertenencia=["africano"],
        pueblo_originario="mapuche",
    )
    t.full_clean()
    assert t.pueblo_originario is None


@pytest.mark.django_db
def test_clean_preserva_pueblo_originario_si_es_indigena():
    t = _trabajador(
        grupo_pertenencia=["indigena"],
        pueblo_originario="mapuche",
    )
    t.full_clean()
    assert t.pueblo_originario == "mapuche"


# ─── clean(): discapacidad condicional ────────────────────────────────────


@pytest.mark.django_db
def test_clean_borra_tipo_y_apoyo_discapacidad_si_no_tiene():
    t = _trabajador(
        tiene_discapacidad="no",
        tipo_discapacidad=["visual"],
        recibe_apoyo_discapacidad="si",
    )
    t.full_clean()
    assert t.tipo_discapacidad == []
    assert t.recibe_apoyo_discapacidad is None


@pytest.mark.django_db
def test_clean_preserva_tipo_discapacidad_si_tiene():
    t = _trabajador(
        tiene_discapacidad="si",
        tipo_discapacidad=["visual", "auditiva"],
        recibe_apoyo_discapacidad="si",
    )
    t.full_clean()
    assert t.tipo_discapacidad == ["visual", "auditiva"]


@pytest.mark.django_db
def test_clean_borra_numero_cud_si_no_tiene_cud():
    t = _trabajador(tiene_discapacidad="si", tiene_cud="no", numero_cud="12345")
    t.full_clean()
    assert t.numero_cud is None


@pytest.mark.django_db
def test_clean_preserva_numero_cud_si_tiene_cud():
    t = _trabajador(tiene_discapacidad="si", tiene_cud="si", numero_cud="12345")
    t.full_clean()
    assert t.numero_cud == "12345"


@pytest.mark.django_db
def test_clean_borra_cud_si_no_tiene_discapacidad():
    # El bloque "¿Tiene CUD?" solo se muestra si hay discapacidad (TC49).
    t = _trabajador(tiene_discapacidad="no", tiene_cud="si", numero_cud="12345")
    t.full_clean()
    assert t.tiene_cud is None
    assert t.numero_cud is None


# ─── clean(): validación multiselect ───────────────────────────────────────


@pytest.mark.django_db
def test_clean_rechaza_capacitacion_invalida():
    t = _trabajador(capacitaciones_certificadas=["valor_inexistente"])
    with pytest.raises(ValidationError):
        t.full_clean()


@pytest.mark.django_db
def test_clean_acepta_capacitaciones_validas():
    t = _trabajador(capacitaciones_certificadas=["juego", "lactancia"])
    t.full_clean()
    assert t.capacitaciones_certificadas == ["juego", "lactancia"]


# ─── propiedad edad ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_edad_calcula_correctamente():
    hoy = date.today()
    nac = date(hoy.year - 30, hoy.month, hoy.day)
    t = _trabajador(fecha_nacimiento=nac)
    assert t.edad == 30


@pytest.mark.django_db
def test_edad_es_none_sin_fecha_nacimiento():
    t = _trabajador()
    assert t.edad is None


# ─── propiedades *_display de multiselect ──────────────────────────────────


@pytest.mark.django_db
def test_display_multiselect_traduce_claves_a_etiquetas():
    t = _trabajador(
        capacitaciones_certificadas=["juego", "lactancia"],
        lenguajes=["espanol_castellano", "lsa"],
        tipo_discapacidad=["motora"],
    )
    assert t.capacitaciones_certificadas_display == ["Juego", "Lactancia"]
    assert t.lenguajes_display == [
        "Español / Castellano",
        "Lengua de Señas de Argentina (LSA)",
    ]
    assert t.tipo_discapacidad_display == ["Motora"]


@pytest.mark.django_db
def test_display_multiselect_vacio_devuelve_lista_vacia():
    t = _trabajador()
    assert t.grupo_pertenencia_display == []
    assert t.lenguajes_display == []
