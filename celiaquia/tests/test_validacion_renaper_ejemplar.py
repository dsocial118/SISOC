"""Tests del dato de ejemplar del DNI que RENAPER informa en el payload crudo.

Dos niveles:

- `_extraer_datos_ejemplar_dni` y sus helpers son funciones puras sobre el dict
  de respuesta, así que se ejercitan sin DB ni red: lo que importa es qué hacen
  con un payload incompleto, con placeholders y con formatos de fecha
  inesperados.
- El wiring de `ValidacionRenaperView` (la clave en el JSON y las claves de
  observabilidad en el log) sí necesita DB, porque el valor de este cambio
  depende de que el dato llegue efectivamente al modal y de que la cobertura
  sea medible en producción.

Las fechas de vencimiento se construyen relativas a hoy a propósito: una fecha
literal futura convertiría estos tests en falsos positivos al pasar esa fecha.
"""

import logging
from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)
from celiaquia.views.validacion_renaper import (
    _ejemplar_esta_vencido,
    _extraer_datos_ejemplar_dni,
    _log_datos_ejemplar,
)
from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia, Sexo

FORMATO_RENAPER = "%d/%m/%Y"


def _resultado(**datos_api):
    return {"success": True, "data": {}, "datos_api": datos_api}


def _fecha_vigente():
    return (timezone.localdate() + timedelta(days=365)).strftime(FORMATO_RENAPER)


def _fecha_pasada():
    return (timezone.localdate() - timedelta(days=1)).strftime(FORMATO_RENAPER)


# --------------------------------------------------------------------------- #
# Extracción del dato (función pura)
# --------------------------------------------------------------------------- #


def test_extrae_emision_vencimiento_y_ejemplar():
    """Formato real del servicio, medido en producción: fechas en dd/mm/aaaa y
    ejemplar como letra. Se muestran tal cual llegan."""
    vencimiento = _fecha_vigente()
    resultado = _resultado(
        emision="31/05/2019",
        vencimiento=vencimiento,
        ejemplar="b",
        nombres="Ana",
    )

    assert _extraer_datos_ejemplar_dni(resultado) == {
        "emision": "31/05/2019",
        "vencimiento": vencimiento,
        "ejemplar": "B",
        "vencido": False,
    }


def test_fecha_iso_se_convierte_a_formato_local():
    """RENAPER hoy manda dd/mm/aaaa, pero el conversor ISO se conserva por si el
    servicio cambia: una fecha ISO no debe llegar cruda a la pantalla."""
    resultado = _resultado(emision="2019-04-15", ejemplar="A")

    assert _extraer_datos_ejemplar_dni(resultado)["emision"] == "15/04/2019"


def test_sin_datos_de_ejemplar_devuelve_none():
    """El bloque es informativo: si RENAPER no informa nada, no ocupa lugar."""
    assert _extraer_datos_ejemplar_dni(_resultado(nombres="Ana")) is None


@pytest.mark.parametrize("placeholder", ["", "  ", "0", "-", "N/A", "null"])
def test_placeholders_se_tratan_como_ausencia(placeholder):
    resultado = _resultado(
        emision=placeholder, vencimiento=placeholder, ejemplar=placeholder
    )

    assert _extraer_datos_ejemplar_dni(resultado) is None


def test_payload_parcial_conserva_lo_que_vino():
    resultado = _resultado(emision="2019-04-15", vencimiento="0", ejemplar=None)

    assert _extraer_datos_ejemplar_dni(resultado) == {
        "emision": "15/04/2019",
        "vencimiento": None,
        "ejemplar": None,
        "vencido": None,
    }


def test_fecha_en_formato_inesperado_se_muestra_tal_cual():
    """Ante un formato que no se reconoce se prefiere mostrar el valor crudo
    antes que ocultarlo."""
    resultado = _extraer_datos_ejemplar_dni(_resultado(emision="ABR-2019"))

    assert resultado["emision"] == "ABR-2019"


@pytest.mark.parametrize("datos_api", [None, "texto", [], 42])
def test_payload_crudo_ausente_o_invalido_no_rompe(datos_api):
    assert (
        _extraer_datos_ejemplar_dni({"success": True, "datos_api": datos_api}) is None
    )
    assert _extraer_datos_ejemplar_dni({"success": True}) is None


# --------------------------------------------------------------------------- #
# Vencimiento
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("vencimiento", "esperado"),
    [
        ("20/09/2026", True),  # el día anterior a `hoy`
        ("21/09/2026", False),  # `hoy`: todavía vigente
        ("22/09/2026", False),  # el día siguiente
        ("2026-09-20", True),  # ISO, por si el servicio cambia de formato
        ("ABR-2019", None),  # formato desconocido: no se afirma nada
        ("", None),
        (None, None),
    ],
)
def test_ejemplar_esta_vencido(vencimiento, esperado):
    """`hoy` se pasa explícito para que el test no dependa del reloj."""
    assert _ejemplar_esta_vencido(vencimiento, hoy=date(2026, 9, 21)) is esperado


def test_dni_vencido_se_marca_como_vencido():
    resultado = _extraer_datos_ejemplar_dni(
        _resultado(emision="31/05/2019", vencimiento=_fecha_pasada(), ejemplar="C")
    )

    assert resultado["vencido"] is True


def test_fecha_de_vencimiento_ilegible_no_afirma_vigencia():
    """None y False son distintos: ante un formato desconocido la UI no debe
    decir ni que está vigente ni que está vencido."""
    resultado = _extraer_datos_ejemplar_dni(
        _resultado(vencimiento="vence pronto", ejemplar="A")
    )

    assert resultado["vencido"] is None


# --------------------------------------------------------------------------- #
# Claves de observabilidad
# --------------------------------------------------------------------------- #


def test_log_no_incluye_vencido_entre_los_campos_informados():
    """`campos_ejemplar` mide qué datos informó el servicio. `vencido` es
    derivado nuestro, no un campo de RENAPER, y no debe contarse ahí."""
    datos = {
        "emision": "31/05/2019",
        "vencimiento": None,
        "ejemplar": "B",
        "vencido": True,
    }

    assert _log_datos_ejemplar(datos) == {
        "ejemplar_disponible": True,
        "campos_ejemplar": ["ejemplar", "emision"],
        "ejemplar_vencido": True,
    }


def test_log_sin_datos_de_ejemplar():
    assert _log_datos_ejemplar(None) == {
        "ejemplar_disponible": False,
        "campos_ejemplar": [],
        "ejemplar_vencido": None,
    }


# --------------------------------------------------------------------------- #
# Wiring de la vista: el dato tiene que llegar al modal y ser medible
# --------------------------------------------------------------------------- #


def _grant(user, codename, model, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


def _coordinador(username):
    """Coordinador y no técnico: al técnico además se le exige estar asignado."""
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_coordinadorceliaquia", User, name="Coordinador Celiaquia")
    return user


def _legajo(documento):
    provincia = Provincia.objects.create(nombre=f"Prov {documento}")
    municipio = Municipio.objects.create(nombre=f"Mun {documento}", provincia=provincia)
    localidad = Localidad.objects.create(nombre=f"Loc {documento}", municipio=municipio)
    sexo, _ = Sexo.objects.get_or_create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        documento=documento,
        fecha_nacimiento=date(1990, 1, 1),
        sexo=sexo,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    expediente = Expediente.objects.create(
        usuario_provincia=User.objects.create_user(
            username=f"prov-{documento}", password="pass"
        ),
        estado=EstadoExpediente.objects.create(nombre=f"EXP_{documento}"),
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=EstadoLegajo.objects.create(nombre=f"LEG_{documento}"),
    )


def _respuesta_renaper(**datos_api):
    return {
        "success": True,
        "data": {"dni": 30111222, "apellido": "PEREZ", "nombre": "JUAN"},
        "datos_api": {"apellido": "PEREZ", "nombres": "JUAN", **datos_api},
    }


def _validar(client, legajo):
    return client.post(
        reverse("legajo_validar_renaper", args=[legajo.expediente.pk, legajo.pk])
    )


def _log_result_ready(caplog):
    return next(
        r for r in caplog.records if r.getMessage() == "renaper.validation.result_ready"
    )


@pytest.mark.django_db
def test_vista_expone_datos_ejemplar_y_registra_cobertura(client, monkeypatch, caplog):
    legajo = _legajo(30111222)
    vencimiento = _fecha_pasada()
    monkeypatch.setattr(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        lambda *args, **kwargs: _respuesta_renaper(
            emision="31/05/2019", vencimiento=vencimiento, ejemplar="b"
        ),
    )
    client.force_login(_coordinador("coord-ejemplar"))

    with caplog.at_level(logging.INFO):
        response = _validar(client, legajo)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["datos_ejemplar"] == {
        "emision": "31/05/2019",
        "vencimiento": vencimiento,
        "ejemplar": "B",
        "vencido": True,
    }

    registro = _log_result_ready(caplog)
    assert registro.data["ejemplar_disponible"] is True
    assert registro.data["campos_ejemplar"] == ["ejemplar", "emision", "vencimiento"]
    assert registro.data["ejemplar_vencido"] is True


@pytest.mark.django_db
def test_vista_sin_datos_de_ejemplar_no_rompe_la_validacion(
    client, monkeypatch, caplog
):
    """La validación tiene que seguir funcionando igual si el servicio no manda
    ninguno de los tres campos."""
    legajo = _legajo(30111333)
    monkeypatch.setattr(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        lambda *args, **kwargs: _respuesta_renaper(),
    )
    client.force_login(_coordinador("coord-sin-ejemplar"))

    with caplog.at_level(logging.INFO):
        response = _validar(client, legajo)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["datos_ejemplar"] is None
    assert payload["datos_renaper"]

    registro = _log_result_ready(caplog)
    assert registro.data["ejemplar_disponible"] is False
    assert registro.data["campos_ejemplar"] == []
    assert registro.data["ejemplar_vencido"] is None
