from copy import deepcopy
from datetime import date, timedelta
import time
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core import signing
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.tests.test_destinatario_form import datos_validos

pytestmark = pytest.mark.django_db


@pytest.fixture
def alta(client):
    user = User.objects.create_superuser("renaper-alta", "", "test1234")
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI RENAPER")
    data = datos_validos(
        centro, fecha_nacimiento=(date.today() - timedelta(days=730)).isoformat()
    )
    result = {
        "success": True,
        "data": {
            "documento": int(data["dni"]),
            "apellido": data["apellido"],
            "nombre": data["nombre"],
            "fecha_nacimiento": date.fromisoformat(data["fecha_nacimiento"]),
            "sexo": None,
        },
        "datos_api": {"dato_privado": "RAW_RENAPER_NO_PUBLICAR"},
    }
    url = reverse("centrodeinfancia_nomina_crear", kwargs={"pk": centro.pk})
    with patch(
        "centrodeinfancia.views.obtener_datos_ciudadano_desde_renaper",
        return_value=result,
    ) as consultar:
        response = client.get(url, {"query": data["dni"]})
    assert response.status_code == 200
    consultar.assert_called_once_with(data["dni"])
    token = response.context["renaper_prefill_token"]
    assert 'name="renaper_prefill_token"' in response.content.decode()
    payload = signing.loads(token, salt="centrodeinfancia.nomina.renaper_prefill")
    assert set(payload) == {"centro_id", "user_id", "values"}
    assert set(payload["values"]) == {"dni", "apellido", "nombre", "fecha_nacimiento"}
    assert "RAW_RENAPER_NO_PUBLICAR" not in response.content.decode()
    with patch(
        "centrodeinfancia.views.obtener_datos_ciudadano_desde_renaper",
        return_value=result,
    ):
        yield url, data, token, result


def test_alta_token_valido_marca_validacion(client, alta):
    url, data, token, result = alta
    result = deepcopy(result)
    result["datos_api"] = {"respuesta_nueva": True}
    with patch(
        "centrodeinfancia.views.obtener_datos_ciudadano_desde_renaper",
        return_value=result,
    ) as consultar:
        response = client.post(url, {**data, "renaper_prefill_token": token})
    consultar.assert_called_once_with(data["dni"])
    assert response.status_code == 302
    ciudadano = Ciudadano.objects.get(documento=data["dni"])
    assert ciudadano.estado_validacion_renaper == Ciudadano.RENAPER_VALIDADO
    assert ciudadano.fecha_validacion_renaper is not None
    assert ciudadano.datos_renaper == result["datos_api"]
    assert ciudadano.origen_dato == "renaper"
    assert NominaCentroInfancia.objects.get().ciudadano == ciudadano
    assert Ciudadano.objects.count() == 1  # No se crean responsables legales.


@pytest.mark.parametrize(
    "caso", ["sin_token", "alterado", "otro_cdi", "otro_usuario", "vencido"]
)
def test_alta_no_confia_en_origen_del_post(client, alta, caso):
    url, data, token, _ = alta
    if caso == "sin_token":
        token = ""
    elif caso == "alterado":
        token += "alterado"
    elif caso == "otro_cdi":
        otro = CentroDeInfancia.objects.create(nombre="Otro CDI")
        url = reverse("centrodeinfancia_nomina_crear", kwargs={"pk": otro.pk})
        data = datos_validos(otro, fecha_nacimiento=data["fecha_nacimiento"])
    elif caso == "otro_usuario":
        otro = User.objects.create_superuser("otro-renaper", "", "test1234")
        client.force_login(otro)
    if caso == "vencido":
        with patch("django.core.signing.time.time", return_value=time.time() + 901):
            response = client.post(
                url, {**data, "origen_dato": "renaper", "renaper_prefill_token": token}
            )
    else:
        response = client.post(
            url, {**data, "origen_dato": "renaper", "renaper_prefill_token": token}
        )
    assert response.status_code == 302
    ciudadano = Ciudadano.objects.get(documento=data["dni"])
    assert ciudadano.estado_validacion_renaper == Ciudadano.RENAPER_NO_CONSULTADO
    assert ciudadano.fecha_validacion_renaper is None
    assert ciudadano.datos_renaper is None
    assert ciudadano.origen_dato == "manual"


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("dni", "55555555"),
        ("apellido", "Otro"),
        ("nombre", "Otra"),
        ("fecha_nacimiento", (date.today() - timedelta(days=800)).isoformat()),
    ],
)
def test_token_no_valida_identidad_modificada(client, alta, campo, valor):
    url, data, token, _ = alta
    response = client.post(url, {**data, campo: valor, "renaper_prefill_token": token})
    assert response.status_code == 302
    ciudadano = Ciudadano.objects.get(
        documento=valor if campo == "dni" else data["dni"]
    )
    assert ciudadano.estado_validacion_renaper == Ciudadano.RENAPER_NO_CONSULTADO
    assert ciudadano.origen_dato == "manual"


@pytest.mark.parametrize("seleccionado", [True, False])
@pytest.mark.parametrize(
    "estado", [Ciudadano.RENAPER_NO_CONSULTADO, Ciudadano.RENAPER_NO_VALIDADO]
)
def test_alta_no_modifica_ciudadano_local(client, alta, seleccionado, estado):
    url, data, token, _ = alta
    ciudadano = Ciudadano.objects.create(
        documento=data["dni"],
        apellido=data["apellido"],
        nombre=data["nombre"],
        fecha_nacimiento=data["fecha_nacimiento"],
        estado_validacion_renaper=estado,
        datos_renaper={"previo": True},
    )
    previo = deepcopy(Ciudadano.objects.filter(pk=ciudadano.pk).values().get())
    if seleccionado:
        data["ciudadano_id"] = ciudadano.pk
    response = client.post(url, {**data, "renaper_prefill_token": token})
    assert response.status_code == 302
    assert Ciudadano.objects.filter(pk=ciudadano.pk).values().get() == previo


def test_post_invalido_conserva_token_sin_reconsultar(client, alta):
    url, data, token, _ = alta
    with patch(
        "centrodeinfancia.views.obtener_datos_ciudadano_desde_renaper"
    ) as consultar:
        response = client.post(
            url, {**data, "nombre": "", "renaper_prefill_token": token}
        )
    assert response.status_code == 200
    assert response.context["renaper_prefill_token"] == token
    consultar.assert_not_called()
    assert not Ciudadano.objects.exists()


@pytest.mark.parametrize("caso", ["error", "excepcion", "dni", "nombre", "fecha"])
def test_reconsulta_fallida_o_distinta_deja_alta_manual(client, alta, caso):
    url, data, token, result = alta
    result = deepcopy(result)
    if caso == "error":
        result = {"success": False, "error_type": "timeout"}
    elif caso == "dni":
        result["data"]["documento"] = 99999999
    elif caso == "nombre":
        result["data"]["nombre"] = "Otra persona"
    elif caso == "fecha":
        result["data"]["fecha_nacimiento"] = "2000-01-01"
    with patch(
        "centrodeinfancia.views.obtener_datos_ciudadano_desde_renaper",
        return_value=result,
        side_effect=TimeoutError() if caso == "excepcion" else None,
    ) as consultar:
        response = client.post(url, {**data, "renaper_prefill_token": token})
    consultar.assert_called_once_with(data["dni"])
    assert response.status_code == 302
    ciudadano = Ciudadano.objects.get(documento=data["dni"])
    assert ciudadano.estado_validacion_renaper == Ciudadano.RENAPER_NO_CONSULTADO
    assert ciudadano.origen_dato == "manual"
    assert ciudadano.datos_renaper is None
