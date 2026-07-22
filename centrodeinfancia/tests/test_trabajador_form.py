from datetime import date

import pytest

from centrodeinfancia.forms import TrabajadorCDIForm
from centrodeinfancia.models import (
    CentroDeInfancia,
    NominaNacionalidad,
    NominaPais,
    Trabajador,
)

# CUIT con dígito verificador correcto.
CUIT_VALIDO = "20-44535030-4"


@pytest.fixture(name="catalogos")
def fixture_catalogos():
    """Los tests corren con TEST MIGRATE=False, así que las fixtures no se cargan."""

    NominaPais.objects.get_or_create(nombre="Argentina")
    NominaNacionalidad.objects.get_or_create(nombre="Argentino")


@pytest.fixture(name="centro")
def fixture_centro():
    return CentroDeInfancia.objects.create(nombre="CDI Test")


def datos_validos(**overrides):
    """Payload completo que pasa todas las validaciones del legajo."""

    datos = {
        "fecha_carga": "2026-07-01",
        "subcomponente": "cdi",
        "funcion_cdi": "educador_docente_sala",
        "sala_cdi": "2_anios",
        "registro_tipo": "alta",
        "nombre": "Julia",
        "apellido": "Méndez",
        "fecha_nacimiento": "1990-05-04",
        "tipo_documentacion": "dni_permanente",
        "dni": "30123456",
        "sexo_registral": "mujer",
        "cuit": CUIT_VALIDO,
        "pais_nacimiento": "Argentina",
        "nacionalidad_trabajador": "Argentino",
        "nivel_educativo": "superior_completo",
        "formacion_academica": "profesorado_nivel_inicial",
        "anos_trabajo_primera_infancia": "5",
        "tipo_contratacion": "relacion_dependencia",
        "carga_horaria_semanal": "40",
        "telefono": "4774-2015",
        "calle_contacto": "San Martín 1234",
        "grupo_pertenencia": ["ninguno"],
        "lenguajes": ["espanol_castellano"],
        "es_interprete": "no",
        "tiene_discapacidad": "no",
    }
    datos.update(overrides)
    return datos


# --- Caso feliz --------------------------------------------------------------


@pytest.mark.django_db
def test_alta_con_todos_los_campos_validos_guarda(catalogos, centro):
    form = TrabajadorCDIForm(data=datos_validos())

    assert form.is_valid(), form.errors
    trabajador = form.save(commit=False)
    trabajador.centro = centro
    trabajador.save()

    assert trabajador.pk
    assert trabajador.nombre == "Julia"
    assert trabajador.cuit == "20445350304"


# --- TC51: no se guarda un legajo incompleto ---------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "campo",
    [
        "fecha_carga",
        "subcomponente",
        "nombre",
        "apellido",
        "fecha_nacimiento",
        "tipo_documentacion",
        "dni",
        "sexo_registral",
        "cuit",
        "pais_nacimiento",
        "nacionalidad_trabajador",
        "nivel_educativo",
        "anos_trabajo_primera_infancia",
        "tipo_contratacion",
        "carga_horaria_semanal",
        "telefono",
        "calle_contacto",
        "grupo_pertenencia",
        "lenguajes",
        "es_interprete",
        "tiene_discapacidad",
    ],
)
def test_rechaza_campo_obligatorio_vacio(catalogos, campo):
    form = TrabajadorCDIForm(data=datos_validos(**{campo: ""}))

    assert not form.is_valid()
    assert campo in form.errors


# --- TC18 / TC19: nombre y apellido ------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre", "1234"),
        ("nombre", "%%%"),
        ("apellido", "%%%"),
        ("apellido", "1234"),
    ],
)
def test_rechaza_numeros_y_simbolos_en_nombre_y_apellido(catalogos, campo, valor):
    form = TrabajadorCDIForm(data=datos_validos(**{campo: valor}))

    assert not form.is_valid()
    assert campo in form.errors


@pytest.mark.django_db
def test_acepta_nombres_con_tildes_y_guiones(catalogos):
    form = TrabajadorCDIForm(
        data=datos_validos(nombre="José María", apellido="Sáenz-Peña")
    )

    assert form.is_valid(), form.errors


# --- TC20: fecha de nacimiento -----------------------------------------------


@pytest.mark.django_db
def test_rechaza_fecha_nacimiento_futura(catalogos):
    futuro = date(date.today().year + 24, 1, 1)
    form = TrabajadorCDIForm(data=datos_validos(fecha_nacimiento=futuro.isoformat()))

    assert not form.is_valid()
    assert "fecha_nacimiento" in form.errors


@pytest.mark.django_db
def test_rechaza_fecha_nacimiento_de_1880(catalogos):
    """TC20/TS04: 1/1/1880 daría 146 años, por encima del tope de 100."""

    form = TrabajadorCDIForm(data=datos_validos(fecha_nacimiento="1880-01-01"))

    assert not form.is_valid()
    assert "fecha_nacimiento" in form.errors


@pytest.mark.django_db
def test_acepta_trabajador_menor_de_edad(catalogos):
    """PM (punto 4): rango 0-100, 'la mayoría van a ser nenes'."""

    hoy = date.today()
    form = TrabajadorCDIForm(
        data=datos_validos(fecha_nacimiento=hoy.replace(year=hoy.year - 4).isoformat())
    )

    assert form.is_valid(), form.errors


# --- TC22: número de documento -----------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["3213214653", "123456"])
def test_rechaza_dni_fuera_de_rango(catalogos, valor):
    form = TrabajadorCDIForm(data=datos_validos(dni=valor))

    assert not form.is_valid()
    assert "dni" in form.errors


# --- TC23: CUIT ---------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "valor", ["00-00000000-0", "ABCDEF", "20a44535030b4", "1234"]
)
def test_rechaza_cuit_invalido(catalogos, valor):
    form = TrabajadorCDIForm(data=datos_validos(cuit=valor))

    assert not form.is_valid()
    assert "cuit" in form.errors


# --- TC25 / TC26: país y nacionalidad son desplegables ------------------------


@pytest.mark.django_db
def test_pais_y_nacionalidad_son_desplegables_del_catalogo(catalogos):
    form = TrabajadorCDIForm()

    paises = [valor for valor, _etiqueta in form.fields["pais_nacimiento"].choices]
    nacionalidades = [
        valor for valor, _etiqueta in form.fields["nacionalidad_trabajador"].choices
    ]

    assert "Argentina" in paises
    assert "Argentino" in nacionalidades


@pytest.mark.django_db
def test_rechaza_pais_fuera_del_catalogo(catalogos):
    form = TrabajadorCDIForm(data=datos_validos(pais_nacimiento="Atlántida"))

    assert not form.is_valid()
    assert "pais_nacimiento" in form.errors


# --- TC34: teléfono -----------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["1-02132-555555", "%%%%", "123"])
def test_rechaza_telefono_invalido(catalogos, valor):
    form = TrabajadorCDIForm(data=datos_validos(telefono=valor))

    assert not form.is_valid()
    assert "telefono" in form.errors


# --- TC50: número de CUD ------------------------------------------------------


@pytest.mark.django_db
def test_rechaza_numero_cud_no_numerico(catalogos):
    form = TrabajadorCDIForm(
        data=datos_validos(
            tiene_discapacidad="si",
            tipo_discapacidad=["motora"],
            recibe_apoyo_discapacidad="si",
            tiene_cud="si",
            numero_cud="hola",
        )
    )

    assert not form.is_valid()
    assert "numero_cud" in form.errors


@pytest.mark.django_db
def test_acepta_numero_cud_numerico(catalogos):
    form = TrabajadorCDIForm(
        data=datos_validos(
            tiene_discapacidad="si",
            tipo_discapacidad=["motora"],
            recibe_apoyo_discapacidad="si",
            tiene_cud="si",
            numero_cud="12345678",
        )
    )

    assert form.is_valid(), form.errors


# --- TC43: "Ninguno de los anteriores" es excluyente --------------------------


@pytest.mark.django_db
def test_grupo_pertenencia_no_combina_ninguno_con_otros(catalogos):
    form = TrabajadorCDIForm(
        data=datos_validos(grupo_pertenencia=["ninguno", "africano"])
    )

    assert not form.is_valid()
    assert "grupo_pertenencia" in form.errors


@pytest.mark.django_db
def test_grupo_pertenencia_acepta_varios_grupos_reales(catalogos):
    form = TrabajadorCDIForm(
        data=datos_validos(grupo_pertenencia=["africano", "asiatico"])
    )

    assert form.is_valid(), form.errors


# --- TC49: tiene_cud se limpia si no hay discapacidad -------------------------


@pytest.mark.django_db
def test_tiene_cud_se_limpia_si_no_hay_discapacidad(catalogos, centro):
    form = TrabajadorCDIForm(
        data=datos_validos(
            tiene_discapacidad="no",
            tiene_cud="si",
            numero_cud="12345678",
        )
    )

    assert form.is_valid(), form.errors
    trabajador = form.save(commit=False)
    trabajador.centro = centro
    trabajador.full_clean(exclude=["centro"])

    assert trabajador.tiene_cud is None
    assert trabajador.numero_cud is None


# --- TC13 / TC45: se elimina "No corresponde" ---------------------------------


@pytest.mark.django_db
def test_funcion_egp_no_ofrece_no_corresponde(catalogos):
    form = TrabajadorCDIForm()

    valores = [valor for valor, _etiqueta in form.fields["funcion_egp"].choices]

    assert "no_corresponde" not in valores


@pytest.mark.django_db
def test_es_interprete_no_ofrece_no_corresponde(catalogos):
    form = TrabajadorCDIForm()

    valores = [valor for valor, _etiqueta in form.fields["es_interprete"].choices]

    assert "no_corresponde" not in valores


# --- Campos condicionales: no se exigen cuando no aplican ---------------------


@pytest.mark.django_db
def test_subcomponente_egp_no_exige_campos_de_cdi(catalogos):
    form = TrabajadorCDIForm(
        data=datos_validos(
            subcomponente="egp",
            funcion_egp="coordinacion_general",
            funcion_cdi="",
            sala_cdi="",
        )
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_sin_discapacidad_no_exige_el_bloque_condicional(catalogos, centro):
    form = TrabajadorCDIForm(data=datos_validos(tiene_discapacidad="no"))

    assert form.is_valid(), form.errors
    trabajador = form.save(commit=False)
    trabajador.centro = centro
    trabajador.full_clean(exclude=["centro"])

    assert trabajador.tipo_discapacidad == []
    assert trabajador.numero_cud is None


@pytest.mark.django_db
def test_carga_horaria_no_supera_60(catalogos):
    form = TrabajadorCDIForm(data=datos_validos(carga_horaria_semanal="61"))

    assert not form.is_valid()
    assert "carga_horaria_semanal" in form.errors


# --- TC12 / TC17: campos nuevos de la spec (PFPI, UAF, tipo de registro) ------


@pytest.mark.django_db
def test_tipo_de_registro_es_obligatorio(catalogos):
    form = TrabajadorCDIForm(data=datos_validos(registro_tipo=""))

    assert not form.is_valid()
    assert "registro_tipo" in form.errors


@pytest.mark.django_db
def test_subcomponente_pfpi_guarda_funcion_pfpi(catalogos, centro):
    form = TrabajadorCDIForm(
        data=datos_validos(
            subcomponente="pfpi",
            funcion_pfpi="direccion",
            funcion_cdi="",
            sala_cdi="",
        )
    )

    assert form.is_valid(), form.errors
    trabajador = form.save(commit=False)
    trabajador.centro = centro
    trabajador.full_clean(exclude=["centro"])

    assert trabajador.funcion_pfpi == "direccion"


@pytest.mark.django_db
def test_subcomponente_uaf_guarda_funcion_uaf(catalogos, centro):
    form = TrabajadorCDIForm(
        data=datos_validos(
            subcomponente="uaf",
            funcion_uaf="coordinador_uaf",
            funcion_cdi="",
            sala_cdi="",
        )
    )

    assert form.is_valid(), form.errors
    trabajador = form.save(commit=False)
    trabajador.centro = centro
    trabajador.full_clean(exclude=["centro"])

    assert trabajador.funcion_uaf == "coordinador_uaf"


@pytest.mark.django_db
def test_funcion_pfpi_se_limpia_si_subcomponente_no_es_pfpi(catalogos, centro):
    # El modelo limpia la función que no corresponde al subcomponente elegido.
    form = TrabajadorCDIForm(
        data=datos_validos(subcomponente="cdi", funcion_pfpi="direccion")
    )

    assert form.is_valid(), form.errors
    trabajador = form.save(commit=False)
    trabajador.centro = centro
    trabajador.full_clean(exclude=["centro"])

    assert trabajador.funcion_pfpi is None


@pytest.mark.django_db
def test_fecha_actualizacion_es_optativa(catalogos):
    form = TrabajadorCDIForm(data=datos_validos(fecha_actualizacion=""))

    assert form.is_valid(), form.errors


# --- RENAPER: datos verificados se bloquean en la edición --------------------


@pytest.mark.django_db
def test_alta_no_bloquea_campos_sin_renaper(catalogos):
    form = TrabajadorCDIForm(data=datos_validos())

    assert form.fields["nombre"].disabled is False
    assert "readonly" not in form.fields["nombre"].widget.attrs


@pytest.mark.django_db
def test_alta_con_renaper_bloquea_campos_verificados(catalogos):
    form = TrabajadorCDIForm(
        data=datos_validos(),
        initial={"nombre": "Julia", "apellido": "Méndez", "dni": 30123456},
        campos_renaper=["nombre", "apellido", "dni"],
    )

    for campo in ("nombre", "apellido", "dni"):
        assert form.fields[campo].disabled is True
        assert form.fields[campo].required is True
        assert form.fields[campo].widget.attrs.get("data-renaper") == "1"
    assert form.fields["telefono"].disabled is False


@pytest.mark.django_db
def test_edicion_bloquea_campos_verificados_por_renaper(catalogos, centro):
    trabajador = Trabajador.objects.create(
        centro=centro,
        nombre="Julia",
        apellido="Méndez",
        dni=30123456,
        campos_verificados_renaper=["nombre", "apellido", "dni"],
    )

    form = TrabajadorCDIForm(instance=trabajador)

    for campo in ("nombre", "apellido", "dni"):
        assert form.fields[campo].disabled is True
    assert form.fields["telefono"].disabled is False


@pytest.mark.django_db
def test_edicion_ignora_intento_de_pisar_dato_renaper(catalogos, centro):
    """`disabled` en un ModelForm: el POST no puede sobrescribir el valor de RENAPER."""

    trabajador = Trabajador.objects.create(
        centro=centro,
        nombre="Julia",
        apellido="Méndez",
        dni=30123456,
        campos_verificados_renaper=["nombre"],
    )

    form = TrabajadorCDIForm(
        data=datos_validos(nombre="Adulterado"),
        instance=trabajador,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["nombre"] == "Julia"
