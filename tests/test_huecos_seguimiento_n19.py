"""Tests de los huecos del contrato E2 cerrados en N19.

Cubre los 8 puntos: campos de capacitación, motivo aprobado != declarado,
``menu.receta`` como lista, cantidades presencial/vianda del día, fotos del
seguimiento, ``norecibio_porque``/``nosencilla_porque`` como texto, motivo de
funcionamiento y bloque ``comedor`` en el PATCH de seguimiento.
"""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor, ImagenComedor
from core.models import Provincia
from relevamientos.models import ItemRecetaSeguimiento, PrimerSeguimiento, Relevamiento
from users.models import TerritorialComedorProvincia

SEGUIMIENTO_URL = "/api/relevamiento/primer-seguimiento"


def _png_upload(name="foto.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def _token_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _escenario(nombre):
    """Territorial + comedor + relevamiento asignado + seguimiento."""
    provincia = Provincia.objects.create(nombre=f"Prov {nombre}")
    comedor = Comedor.objects.create(nombre=f"Comedor {nombre}", provincia=provincia)
    user = get_user_model().objects.create_user(
        username=f"terr_{nombre}",
        email=f"terr_{nombre}@example.com",
        password="testpass123",
    )
    user.profile.es_territorial_comedor = True
    user.profile.save(update_fields=["es_territorial_comedor"])
    TerritorialComedorProvincia.objects.create(
        profile=user.profile, provincia=provincia
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor, estado="Visita pendiente", territorial_user=user
    )
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )
    return user, comedor, relevamiento, seguimiento


# --------------------------------------------------------------------------- #
# 1. Capacitación: año / quién la dictó / temas de interés
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_capacitacion_anio_quien_y_temas_se_persisten():
    user, _, _, seguimiento = _escenario("capacitacion")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "tareas_capacitacion": "Sí",
            "tareas_capacitacion_anio": "2025",
            "tareas_capacitacion_dictada_por": "Ministerio de Salud",
            "tareas_capacitacion_temas_interes": "Manipulación de alimentos y RCP",
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    tareas = seguimiento.tareas_comedor
    assert tareas.tareas_capacitacion_anio == 2025
    assert tareas.tareas_capacitacion_dictada_por == "Ministerio de Salud"
    assert tareas.tareas_capacitacion_temas_interes == (
        "Manipulación de alimentos y RCP"
    )


@pytest.mark.django_db
def test_capacitacion_anio_fuera_de_rango_devuelve_400():
    user, _, _, seguimiento = _escenario("capacitacion_rango")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {"sisoc_id": seguimiento.id, "tareas_capacitacion_anio": 1200},
        format="json",
    )

    assert response.status_code == 400


# --------------------------------------------------------------------------- #
# 2. Motivo cuando lo aprobado difiere de lo declarado
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_motivo_diferencia_aprobado_declarado_se_persiste():
    user, _, _, seguimiento = _escenario("motivo_dif")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "motivo_diferencia_aprobado_declarado": "Declaran 200, aprobado 150.",
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.motivo_diferencia_aprobado_declarado == (
        "Declaran 200, aprobado 150."
    )


# --------------------------------------------------------------------------- #
# 3. menu.receta como lista de N ingredientes
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_menu_receta_acepta_lista_de_ingredientes():
    user, _, _, seguimiento = _escenario("receta_lista")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "menu": {
                "id_menu": "menu-1",
                "receta": [
                    {
                        "id_item_receta": "ing-1",
                        "ingrediente": "Fideos",
                        "unidad_medida": "kg",
                        "cantidad_medida": "3",
                    },
                    {
                        "id_item_receta": "ing-2",
                        "ingrediente": "Salsa",
                        "unidad_medida": "l",
                        "cantidad_medida": "2",
                    },
                ],
            },
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    items = ItemRecetaSeguimiento.objects.filter(menu=seguimiento.menu)
    assert items.count() == 2
    assert set(items.values_list("ingrediente", flat=True)) == {"Fideos", "Salsa"}


@pytest.mark.django_db
def test_menu_receta_con_ids_estables_no_duplica_en_reintentos():
    user, _, _, seguimiento = _escenario("receta_dedup")
    payload = {
        "sisoc_id": seguimiento.id,
        "menu": {
            "id_menu": "menu-dedup",
            "receta": [
                {
                    "id_item_receta": "ing-dedup-1",
                    "ingrediente": "Arroz",
                    "unidad_medida": "kg",
                    "cantidad_medida": "5",
                }
            ],
        },
    }
    client = _token_client(user)

    assert client.patch(SEGUIMIENTO_URL, payload, format="json").status_code == 200
    assert client.patch(SEGUIMIENTO_URL, payload, format="json").status_code == 200

    seguimiento.refresh_from_db()
    assert ItemRecetaSeguimiento.objects.filter(menu=seguimiento.menu).count() == 1


@pytest.mark.django_db
def test_menu_receta_sigue_aceptando_un_objeto():
    user, _, _, seguimiento = _escenario("receta_objeto")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "menu": {
                "id_menu": "menu-obj",
                "receta": {"id_item_receta": "ing-obj", "ingrediente": "Pan"},
            },
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert ItemRecetaSeguimiento.objects.filter(menu=seguimiento.menu).count() == 1


# --------------------------------------------------------------------------- #
# 4. Cantidades presencial / vianda del día
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_cantidades_presencial_y_vianda_del_dia_se_persisten():
    user, _, _, seguimiento = _escenario("cantidades_dia")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "cantidad_presencial_dia": "120",
            "cantidad_vianda_dia": 35,
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.menu.cantidad_presencial_dia == 120
    assert seguimiento.menu.cantidad_vianda_dia == 35


# --------------------------------------------------------------------------- #
# 5. Fotos del seguimiento
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_foto_se_asocia_al_seguimiento():
    user, comedor, _, seguimiento = _escenario("foto_seg")

    response = _token_client(user).post(
        f"/api/territorial/comedores/{comedor.id}/imagenes/",
        {"imagen": _png_upload(), "seguimiento_id": seguimiento.id},
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data["imagenes"][0]["seguimiento"] == seguimiento.id
    assert ImagenComedor.objects.filter(seguimiento=seguimiento).count() == 1


@pytest.mark.django_db
def test_foto_rechaza_relevamiento_y_seguimiento_juntos():
    user, comedor, relevamiento, seguimiento = _escenario("foto_ambos")

    response = _token_client(user).post(
        f"/api/territorial/comedores/{comedor.id}/imagenes/",
        {
            "imagen": _png_upload(),
            "sisoc_id": relevamiento.id,
            "seguimiento_id": seguimiento.id,
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert ImagenComedor.objects.filter(comedor=comedor).count() == 0


@pytest.mark.django_db
def test_foto_rechaza_seguimiento_de_otro_comedor():
    user, comedor, _, _ = _escenario("foto_propio")
    _, _, _, seguimiento_ajeno = _escenario("foto_ajeno")

    response = _token_client(user).post(
        f"/api/territorial/comedores/{comedor.id}/imagenes/",
        {"imagen": _png_upload(), "seguimiento_id": seguimiento_ajeno.id},
        format="multipart",
    )

    assert response.status_code == 400
    assert ImagenComedor.objects.filter(comedor=comedor).count() == 0


# --------------------------------------------------------------------------- #
# 6. norecibio_porque / nosencilla_porque como texto
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_porques_de_rendicion_aceptan_texto():
    user, _, _, seguimiento = _escenario("porques")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "id_rendicion": "rend-1",
            "recibio_capacitacion": "N",
            "norecibio_porque": "No estaba notificada la fecha",
            "sencilla_plataforma": "N",
            "nosencilla_porque": "La carga de comprobantes falla",
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    rendicion = seguimiento.rendicion_cuentas
    assert rendicion.norecibio_porque == "No estaba notificada la fecha"
    assert rendicion.nosencilla_porque == "La carga de comprobantes falla"


# --------------------------------------------------------------------------- #
# 7. Motivo del encabezado FUNCIONAMIENTO
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_funcionamiento_motivo_se_persiste_en_su_bloque():
    user, _, _, seguimiento = _escenario("func_motivo")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "funcionamiento": "Cerrado",
            "funcionamiento_motivo": "Refacciones en la cocina",
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.funcionamiento.funcionamiento == "Cerrado"
    assert seguimiento.funcionamiento.funcionamiento_motivo == (
        "Refacciones en la cocina"
    )


# --------------------------------------------------------------------------- #
# 8. Bloque comedor en el PATCH de seguimiento
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_bloque_comedor_actualiza_domicilio_desde_el_seguimiento():
    user, comedor, _, seguimiento = _escenario("comedor_block")

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": seguimiento.id,
            "comedor": {
                "calle": "Av. Siempre Viva",
                "numero": "742",
                "barrio": "Centro",
            },
        },
        format="json",
    )

    assert response.status_code == 200
    comedor.refresh_from_db()
    assert comedor.calle == "Av. Siempre Viva"
    assert comedor.numero == 742
    assert comedor.barrio == "Centro"
