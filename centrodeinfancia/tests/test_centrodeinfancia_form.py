from datetime import date

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from centrodeinfancia.forms import CentroDeInfanciaForm
from centrodeinfancia.models import (
    CentroDeInfancia,
    DepartamentoIpi,
    OfertaServicio,
)
from core.models import Localidad, Municipio, Provincia
from users.models import Profile

# CUIT real, con dígito verificador correcto. Ojo: el "30-12345678-9" que la planilla
# de QA usa como caso válido NO lo es (su DV real es 1), así que el form lo rechaza.
CUIT_VALIDO = "20-44535030-4"


@pytest.fixture(name="ubicacion")
def fixture_ubicacion():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    departamento = DepartamentoIpi.objects.create(
        codigo_departamento="06515",
        provincia=provincia,
        nombre="Moreno",
        decil_ipi=3,
    )
    municipio = Municipio.objects.create(nombre="Moreno", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Paso del Rey", municipio=municipio)
    return {
        "provincia": provincia,
        "departamento": departamento,
        "municipio": municipio,
        "localidad": localidad,
    }


@pytest.fixture(name="servicio")
def fixture_servicio():
    servicio, _ = OfertaServicio.objects.get_or_create(
        codigo="multiedad",
        defaults={"orden": 5},
    )
    return servicio


def datos_validos(ubicacion, servicio, **overrides):
    """Payload completo que pasa todas las validaciones del alta."""

    datos = {
        "nombre": "PULGARCITO",
        "organizacion": "Medicos sin fronteras",
        "cuit_organizacion_gestiona": CUIT_VALIDO,
        "ambito": "urbano",
        "telefono": "4774-2015",
        "mail": "contacto@cdi.com",
        "fecha_inicio": "1995",
        "provincia": str(ubicacion["provincia"].pk),
        "departamento": str(ubicacion["departamento"].pk),
        "municipio": str(ubicacion["municipio"].pk),
        "localidad": str(ubicacion["localidad"].pk),
        "codigo_postal": "1742",
        "calle": "San Martín",
        "numero": "1234",
        "meses_funcionamiento": ["enero", "febrero"],
        "tipo_jornada": "simple_single_shift",
        "oferta_servicios": [str(servicio.pk)],
        "modalidad_gestion": "gobierno_municipal",
        "nombre_referente": "Ana",
        "apellido_referente": "Pérez",
        "email_referente": "ana.perez@cdi.com",
        "telefono_referente": "4774-2015",
    }
    datos.update(overrides)
    return datos


@pytest.fixture(name="user")
def fixture_user():
    return User.objects.create_user(username="user-cdi", password="test1234")


def construir_form(datos, user=None, **kwargs):
    kwargs.setdefault("lock_provincia_from_user", False)
    return CentroDeInfanciaForm(data=datos, user=user, **kwargs)


# --- Alta completa (caso feliz, no-regresión) --------------------------------


@pytest.mark.django_db
def test_alta_con_todos_los_campos_validos_guarda(user, ubicacion, servicio):
    form = construir_form(datos_validos(ubicacion, servicio), user=user)

    assert form.is_valid(), form.errors
    centro = form.save()

    assert centro.pk
    assert centro.provincia == ubicacion["provincia"]
    assert centro.cuit_organizacion_gestiona == "20445350304"
    assert centro.fecha_inicio == date(1995, 1, 1)
    assert centro.codigo_postal == 1742
    # TC20/TS02: la selección de Servicios se persiste tal cual.
    assert list(centro.oferta_servicios.values_list("codigo", flat=True)) == [
        "multiedad"
    ]


# --- BUG-01 / BUG-02: campos obligatorios en el alta -------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "campo",
    [
        "nombre",
        "organizacion",
        "cuit_organizacion_gestiona",
        "ambito",
        "telefono",
        "mail",
        "fecha_inicio",
        "provincia",
        "departamento",
        "municipio",
        "localidad",
        "codigo_postal",
        "calle",
        "numero",
        "meses_funcionamiento",
        "tipo_jornada",
        "oferta_servicios",
        "modalidad_gestion",
        "nombre_referente",
        "apellido_referente",
        "email_referente",
        "telefono_referente",
    ],
)
def test_alta_rechaza_campo_obligatorio_vacio(user, ubicacion, servicio, campo):
    form = construir_form(
        datos_validos(ubicacion, servicio, **{campo: ""}),
        user=user,
    )

    assert not form.is_valid()
    assert campo in form.errors


@pytest.mark.django_db
def test_alta_sin_provincia_no_crea_registro_huerfano(user, servicio, ubicacion):
    """BUG-01: sin provincia el CDI se guardaba y quedaba invisible (404 al redirigir)."""

    form = construir_form(
        datos_validos(ubicacion, servicio, provincia=""),
        user=user,
    )

    assert not form.is_valid()
    assert "provincia" in form.errors
    assert CentroDeInfancia.objects.count() == 0


# --- BUG-04: campos de texto rechazan números y símbolos ---------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre", "12345"),
        ("nombre", "%%%%"),
        ("organizacion", "12345"),
        ("organizacion", "@@@@"),
        ("nombre_referente", "1234"),
        ("apellido_referente", "%%%"),
    ],
)
def test_rechaza_numeros_y_simbolos_en_campos_de_texto(
    user, ubicacion, servicio, campo, valor
):
    form = construir_form(
        datos_validos(ubicacion, servicio, **{campo: valor}),
        user=user,
    )

    assert not form.is_valid()
    assert campo in form.errors


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["Pérez", "De la Cruz", "O'Higgins", "Sáenz-Peña"])
def test_acepta_nombres_con_tildes_apostrofes_y_guiones(
    user, ubicacion, servicio, valor
):
    form = construir_form(
        datos_validos(ubicacion, servicio, apellido_referente=valor),
        user=user,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["apellido_referente"] == valor


# --- BUG-05: CUIT ------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "valor",
    [
        "00-00000000-0",  # TC03/TS03: CUIT nulo, antes se guardaba como válido
        "ABCDEF",  # TC03/TS04
        "1234",  # TC03/TS02
        "30-12345678-9",  # dígito verificador incorrecto (el real es 1)
    ],
)
def test_rechaza_cuit_invalido(user, ubicacion, servicio, valor):
    form = construir_form(
        datos_validos(ubicacion, servicio, cuit_organizacion_gestiona=valor),
        user=user,
    )

    assert not form.is_valid()
    assert "cuit_organizacion_gestiona" in form.errors


@pytest.mark.django_db
def test_acepta_cuit_valido_y_lo_normaliza(user, ubicacion, servicio):
    form = construir_form(datos_validos(ubicacion, servicio), user=user)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["cuit_organizacion_gestiona"] == "20445350304"


# --- BUG-06: teléfono --------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("campo", ["telefono", "telefono_referente"])
@pytest.mark.parametrize("valor", ["1-02132-555555", "%%%%", "11-ABCD-1234", "123"])
def test_rechaza_telefono_invalido(user, ubicacion, servicio, campo, valor):
    form = construir_form(
        datos_validos(ubicacion, servicio, **{campo: valor}),
        user=user,
    )

    assert not form.is_valid()
    assert campo in form.errors


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["4774-2015", "1122334455", "011-4774-2015"])
def test_acepta_telefono_valido(user, ubicacion, servicio, valor):
    form = construir_form(
        datos_validos(ubicacion, servicio, telefono=valor),
        user=user,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["telefono"] == valor


# --- BUG-07: código postal ---------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["35689610", "123", "99999"])
def test_rechaza_codigo_postal_fuera_de_rango(user, ubicacion, servicio, valor):
    form = construir_form(
        datos_validos(ubicacion, servicio, codigo_postal=valor),
        user=user,
    )

    assert not form.is_valid()
    assert "codigo_postal" in form.errors


# --- BUG-08: latitud / longitud (optativas, con rango argentino) -------------


@pytest.mark.django_db
def test_coordenadas_son_optativas(user, ubicacion, servicio):
    form = construir_form(
        datos_validos(ubicacion, servicio, latitud="", longitud=""),
        user=user,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["latitud"] is None
    assert form.cleaned_data["longitud"] is None


@pytest.mark.django_db
def test_acepta_coordenadas_argentinas(user, ubicacion, servicio):
    form = construir_form(
        datos_validos(ubicacion, servicio, latitud="-34.60879", longitud="-58.39347"),
        user=user,
    )

    assert form.is_valid(), form.errors
    centro = form.save()

    centro.refresh_from_db()
    assert str(centro.latitud) == "-34.608790"
    assert str(centro.longitud) == "-58.393470"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("latitud", "34.60879"),  # TC16/TS03: positiva, fuera de Argentina
        ("latitud", "ABC"),  # TC16/TS02
        ("longitud", "58.39347"),  # TC17/TS03
        ("longitud", "ABC"),  # TC17/TS02
    ],
)
def test_rechaza_coordenadas_invalidas(user, ubicacion, servicio, campo, valor):
    form = construir_form(
        datos_validos(ubicacion, servicio, **{campo: valor}),
        user=user,
    )

    assert not form.is_valid()
    assert campo in form.errors


# --- BUG-12: año de inicio ---------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "valor",
    [
        "01/01/2000",  # TC07/TS02: fecha completa
        "2050",  # TC07/TS03: año futuro
        "1889",  # anterior al mínimo
        "95",  # menos de 4 dígitos
    ],
)
def test_rechaza_anio_inicio_invalido(user, ubicacion, servicio, valor):
    form = construir_form(
        datos_validos(ubicacion, servicio, fecha_inicio=valor),
        user=user,
    )

    assert not form.is_valid()
    assert "fecha_inicio" in form.errors


@pytest.mark.django_db
def test_acepta_anio_inicio_valido(user, ubicacion, servicio):
    form = construir_form(datos_validos(ubicacion, servicio), user=user)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["fecha_inicio"] == date(1995, 1, 1)


@pytest.mark.django_db
def test_edicion_precarga_solo_el_anio(ubicacion):
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Fecha",
        fecha_inicio=date(2024, 5, 4),
    )

    form = CentroDeInfanciaForm(instance=centro)

    assert form.fields["fecha_inicio"].widget.input_type == "number"
    assert 'value="2024"' in str(form["fecha_inicio"])


# --- Ámbito: obligatorio, sin default "Sin información" ----------------------


@pytest.mark.django_db
def test_ambito_no_ofrece_sin_informacion_ni_viene_preseleccionado():
    form = CentroDeInfanciaForm()

    valores = [valor for valor, _etiqueta in form.fields["ambito"].choices]

    assert "sin_informacion" not in valores
    assert valores[0] == ""
    assert not form.initial.get("ambito")


@pytest.mark.django_db
def test_ambito_no_se_completa_solo_al_guardar(user, ubicacion, servicio):
    form = construir_form(
        datos_validos(ubicacion, servicio, ambito="urbano"),
        user=user,
    )

    assert form.is_valid(), form.errors
    assert form.save().ambito == "urbano"


@pytest.mark.django_db
def test_edicion_de_centro_con_ambito_sin_informacion_obliga_a_elegir(user, ubicacion):
    """Los CDIs viejos quedaron en 'sin_informacion': hay que forzar una elección."""

    centro = CentroDeInfancia.objects.create(
        nombre="CDI Viejo",
        ambito="sin_informacion",
    )

    form = CentroDeInfanciaForm(instance=centro, user=user)

    assert not form.initial.get("ambito")


# --- Email (no-regresión: QA lo dio por aprobado) ----------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("campo", ["mail", "email_referente"])
@pytest.mark.parametrize("valor", ["contacto.cdi", "contacto@cdi"])
def test_rechaza_email_invalido(user, ubicacion, servicio, campo, valor):
    form = construir_form(
        datos_validos(ubicacion, servicio, **{campo: valor}),
        user=user,
    )

    assert not form.is_valid()
    assert campo in form.errors


# --- Edición: los obligatorios rigen igual que en el alta --------------------


@pytest.mark.django_db
def test_edicion_exige_todos_los_campos_obligatorios(user, ubicacion, servicio):
    """Decisión de producto: no se guarda un alta ni una edición incompleta."""

    centro = CentroDeInfancia.objects.create(nombre="CDI Incompleto")

    form = CentroDeInfanciaForm(
        data={"nombre": "CDI Incompleto"},
        instance=centro,
        user=user,
        lock_provincia_from_user=False,
    )

    assert not form.is_valid()
    for campo in ("provincia", "mail", "cuit_organizacion_gestiona", "ambito"):
        assert form.errors[campo] == ["Este campo es obligatorio."]


@pytest.mark.django_db
def test_edicion_guarda_si_se_completan_todos_los_campos(user, ubicacion, servicio):
    centro = CentroDeInfancia.objects.create(nombre="CDI Incompleto")

    form = CentroDeInfanciaForm(
        data=datos_validos(ubicacion, servicio, nombre="CDI Completo"),
        instance=centro,
        user=user,
        lock_provincia_from_user=False,
    )

    assert form.is_valid(), form.errors
    centro = form.save()

    assert centro.nombre == "CDI Completo"
    assert centro.provincia == ubicacion["provincia"]


@pytest.mark.django_db
def test_edicion_no_permite_vaciar_un_campo_ya_cargado(user, ubicacion, servicio):
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Con Datos",
        telefono="4774-2015",
        provincia=ubicacion["provincia"],
    )

    form = CentroDeInfanciaForm(
        data=datos_validos(ubicacion, servicio, telefono="", provincia=""),
        instance=centro,
        user=user,
        lock_provincia_from_user=False,
    )

    assert not form.is_valid()
    assert form.errors["telefono"] == ["Este campo es obligatorio."]
    assert form.errors["provincia"] == ["Este campo es obligatorio."]


@pytest.mark.django_db
def test_edicion_muestra_errores_en_la_vista(client, ubicacion):
    user = User.objects.create_superuser(
        username="super-cdi-edicion",
        email="super-cdi-edicion@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Edicion",
        telefono="4774-2015",
    )

    response = client.post(
        reverse("centrodeinfancia_editar", kwargs={"pk": centro.pk}),
        {"nombre": centro.nombre, "telefono": ""},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["telefono"] == ["Este campo es obligatorio."]


# --- Provincia bloqueada por perfil del usuario (no-regresión) ---------------


@pytest.mark.django_db
def test_alta_bloquea_provincia_si_usuario_tiene_provincia(ubicacion, servicio):
    user = User.objects.create_user(username="user-provincia", password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = ubicacion["provincia"]
    profile.save()

    form = CentroDeInfanciaForm(
        data=datos_validos(ubicacion, servicio),
        user=user,
        lock_provincia_from_user=True,
    )

    assert form.fields["provincia"].disabled is True
    assert form.is_valid(), form.errors
    assert form.cleaned_data["provincia"] == ubicacion["provincia"]


@pytest.mark.django_db
def test_alta_no_bloquea_provincia_si_usuario_no_tiene_provincia(ubicacion, servicio):
    user = User.objects.create_user(username="user-sin-provincia", password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = None
    profile.save()

    form = CentroDeInfanciaForm(
        data=datos_validos(ubicacion, servicio),
        user=user,
        lock_provincia_from_user=True,
    )

    assert form.fields["provincia"].disabled is False
    assert form.is_valid(), form.errors
    assert form.cleaned_data["provincia"] == ubicacion["provincia"]


# --- Ubicación: coherencia departamento / provincia (no-regresión) ----------


@pytest.mark.django_db
def test_form_filtra_departamentos_por_provincia(ubicacion):
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    DepartamentoIpi.objects.create(
        codigo_departamento="82001",
        provincia=provincia_sf,
        nombre="Rosario",
    )

    form = CentroDeInfanciaForm(
        data={"nombre": "CDI Norte", "provincia": ubicacion["provincia"].id}
    )

    departamento_ids = set(
        form.fields["departamento"].queryset.values_list("id", flat=True)
    )

    assert departamento_ids == {ubicacion["departamento"].id}


@pytest.mark.django_db
def test_form_rechaza_departamento_que_no_pertenece_a_la_provincia(ubicacion):
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    departamento_sf = DepartamentoIpi.objects.create(
        codigo_departamento="82001",
        provincia=provincia_sf,
        nombre="Rosario",
    )

    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Invalido",
            "provincia": ubicacion["provincia"].id,
            "departamento": departamento_sf.id,
        }
    )

    assert not form.is_valid()
    assert "departamento" in form.errors


# --- Decil IPI: automático y no editable (no-regresión) ----------------------


@pytest.mark.django_db
def test_decil_ipi_es_automatico_y_no_editable(ubicacion):
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Centro",
        provincia=ubicacion["provincia"],
        departamento=ubicacion["departamento"],
    )

    form = CentroDeInfanciaForm(instance=centro)

    assert form.fields["decil_ipi"].disabled is True
    assert form.fields["decil_ipi"].initial == "3"


@pytest.mark.django_db
def test_decil_ipi_se_muestra_en_post_invalido(ubicacion):
    form = CentroDeInfanciaForm(
        data={
            "nombre": "",
            "provincia": ubicacion["provincia"].id,
            "departamento": ubicacion["departamento"].id,
        }
    )

    assert not form.is_valid()
    assert form.fields["decil_ipi"].initial == "3"


# --- Horarios y jornada (no-regresión) --------------------------------------


@pytest.mark.django_db
def test_guarda_horarios_de_los_dias_seleccionados(user, ubicacion, servicio):
    form = construir_form(
        datos_validos(
            ubicacion,
            servicio,
            dias_funcionamiento=["lunes", "martes"],
            horario_lunes_apertura="08:00",
            horario_lunes_cierre="12:00",
            horario_martes_apertura="08:00",
            horario_martes_cierre="12:00",
        ),
        user=user,
    )

    assert form.is_valid(), form.errors
    centro = form.save()

    assert list(
        centro.horarios_funcionamiento.order_by("dia").values_list("dia", flat=True)
    ) == ["lunes", "martes"]


@pytest.mark.django_db
def test_rechaza_horarios_de_dias_no_seleccionados(user, ubicacion, servicio):
    form = construir_form(
        datos_validos(
            ubicacion,
            servicio,
            dias_funcionamiento=["lunes"],
            horario_martes_apertura="08:00",
            horario_martes_cierre="12:00",
        ),
        user=user,
    )

    assert not form.is_valid()
    assert "horario_martes_cierre" in form.errors


@pytest.mark.django_db
def test_jornada_otros_con_texto_asociado_guarda(user, ubicacion, servicio):
    form = construir_form(
        datos_validos(
            ubicacion,
            servicio,
            tipo_jornada="other",
            tipo_jornada_otra="Reducida",
        ),
        user=user,
    )

    assert form.is_valid(), form.errors
    assert form.save().tipo_jornada_otra == "Reducida"


# --- Widgets -----------------------------------------------------------------


@pytest.mark.django_db
def test_form_no_publica_pattern_html_incompatible_para_cuit():
    form = CentroDeInfanciaForm()

    cuit_attrs = form.fields["cuit_organizacion_gestiona"].widget.attrs

    assert cuit_attrs["inputmode"] == "numeric"
    assert "pattern" not in cuit_attrs
