"""Regla: una persona sólo puede tener una nómina CDI vigente a la vez.

Vigente = estado Activo o Pendiente y registro no dado de baja. El impedimento
nunca debe exponer cuál es el otro centro involucrado.
"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.forms import NominaCentroInfanciaForm
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.services import (
    MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO,
    MOTIVO_NOMINA_DUPLICADA_MISMO_CENTRO,
    MOTIVO_NOMINA_VIGENTE_OTRO_CENTRO,
    CentroDeInfanciaService,
    tiene_nomina_cdi_vigente_en_otro_centro,
)
from centrodeinfancia.tests.test_destinatario_form import datos_validos
from centrodeinfancia.views import NominaCentroInfanciaCreateView
from core.models import Provincia

NOMBRE_CENTRO_A_OCULTAR = "CDI Confidencial Vigencia"


@pytest.fixture
def provincia():
    return Provincia.objects.create(nombre="Santa Fe")


@pytest.fixture
def centro_destino(provincia):
    return CentroDeInfancia.objects.create(
        nombre="CDI Vigencia Destino", provincia=provincia
    )


@pytest.fixture
def centro_origen(provincia):
    return CentroDeInfancia.objects.create(
        nombre=NOMBRE_CENTRO_A_OCULTAR, provincia=provincia
    )


@pytest.fixture
def ciudadano():
    return Ciudadano.objects.create(
        apellido="Torres",
        nombre="Luca",
        fecha_nacimiento=date(2021, 7, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=45123456,
    )


class _FormStub:
    """Sustituto mínimo del ModelForm: sólo aporta `save(commit=False)`."""

    def __init__(self, **attrs):
        self._attrs = attrs

    def save(self, commit=False):
        assert commit is False
        return NominaCentroInfancia(**self._attrs)


def _crear_nomina(centro, ciudadano, estado):
    return NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        estado=estado,
        dni=ciudadano.documento,
        apellido=ciudadano.apellido,
        nombre=ciudadano.nombre,
        fecha_nacimiento=ciudadano.fecha_nacimiento,
    )


def _intentar_alta(centro, ciudadano, estado=NominaCentroInfancia.ESTADO_ACTIVO):
    with transaction.atomic():
        return NominaCentroInfanciaCreateView._crear_nomina_con_bloqueo(  # pylint: disable=protected-access
            centro=centro,
            ciudadano=ciudadano,
            form=_FormStub(estado=estado),
        )


# ─────────────────────────────────────────────────────────
# Alta: helper de vigencia
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_permite_alta_sin_nomina_vigente(centro_destino, ciudadano):
    creado, motivo = _intentar_alta(centro_destino, ciudadano)

    assert creado is True
    assert motivo is None
    assert NominaCentroInfancia.objects.filter(centro=centro_destino).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "estado_vigente",
    [NominaCentroInfancia.ESTADO_ACTIVO, NominaCentroInfancia.ESTADO_PENDIENTE],
)
def test_bloquea_alta_si_hay_vigencia_en_otro_centro(
    centro_origen, centro_destino, ciudadano, estado_vigente
):
    _crear_nomina(centro_origen, ciudadano, estado_vigente)

    creado, motivo = _intentar_alta(centro_destino, ciudadano)

    assert creado is False
    assert motivo == MOTIVO_NOMINA_VIGENTE_OTRO_CENTRO
    assert not NominaCentroInfancia.objects.filter(centro=centro_destino).exists()
    # El registro de origen queda intacto.
    assert NominaCentroInfancia.objects.get(centro=centro_origen).estado == (
        estado_vigente
    )


@pytest.mark.django_db
def test_permite_alta_si_los_registros_previos_estan_en_baja(
    centro_origen, centro_destino, ciudadano
):
    _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_BAJA)

    creado, motivo = _intentar_alta(centro_destino, ciudadano)

    assert creado is True
    assert motivo is None


@pytest.mark.django_db
def test_permite_alta_si_el_registro_previo_fue_dado_de_baja_logicamente(
    centro_origen, centro_destino, ciudadano
):
    nomina = _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO)
    nomina.delete()

    creado, motivo = _intentar_alta(centro_destino, ciudadano)

    assert creado is True
    assert motivo is None


@pytest.mark.django_db
def test_conserva_el_bloqueo_de_duplicado_en_el_mismo_centro(centro_destino, ciudadano):
    _crear_nomina(centro_destino, ciudadano, NominaCentroInfancia.ESTADO_BAJA)

    creado, motivo = _intentar_alta(centro_destino, ciudadano)

    assert creado is False
    assert motivo == MOTIVO_NOMINA_DUPLICADA_MISMO_CENTRO


@pytest.mark.django_db
def test_helper_de_vigencia_ignora_el_propio_centro(centro_origen, ciudadano):
    _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO)

    assert (
        tiene_nomina_cdi_vigente_en_otro_centro(ciudadano.pk, centro_origen.pk) is False
    )


# ─────────────────────────────────────────────────────────
# Alta simultánea
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_alta_toma_el_lock_de_fila_del_ciudadano(centro_destino, ciudadano, mocker):
    """El lock sobre el ciudadano es lo que serializa altas en centros distintos.

    En SQLite `select_for_update` es un no-op, así que se verifica que el lock se
    pida; el bloqueo efectivo lo aporta InnoDB en MySQL.
    """
    bloqueo = mocker.patch("centrodeinfancia.views.bloquear_ciudadano_para_nomina_cdi")
    chequeo = mocker.patch(
        "centrodeinfancia.views.tiene_nomina_cdi_vigente_en_otro_centro",
        return_value=False,
    )

    _intentar_alta(centro_destino, ciudadano)

    bloqueo.assert_called_once_with(ciudadano.pk)
    # `bloquear=True`: bajo REPEATABLE READ una lectura común podría usar un
    # snapshot anterior al lock y no ver un alta concurrente ya commiteada.
    assert chequeo.call_args.kwargs["bloquear"] is True


@pytest.mark.django_db(transaction=True)
def test_altas_simultaneas_no_generan_dos_registros_vigentes(provincia):
    """Dos altas del mismo destinatario en centros distintos: sólo una prospera."""
    centro_1 = CentroDeInfancia.objects.create(nombre="CDI Race 1", provincia=provincia)
    centro_2 = CentroDeInfancia.objects.create(nombre="CDI Race 2", provincia=provincia)
    persona = Ciudadano.objects.create(
        apellido="Race",
        nombre="Roman",
        fecha_nacimiento=date(2021, 1, 5),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=46999888,
    )

    creado_1, _ = _intentar_alta(centro_1, persona)
    creado_2, motivo_2 = _intentar_alta(centro_2, persona)

    assert creado_1 is True
    assert creado_2 is False
    assert motivo_2 == MOTIVO_NOMINA_VIGENTE_OTRO_CENTRO
    assert (
        NominaCentroInfancia.objects.filter(
            ciudadano=persona,
            estado__in=[
                NominaCentroInfancia.ESTADO_ACTIVO,
                NominaCentroInfancia.ESTADO_PENDIENTE,
            ],
        ).count()
        == 1
    )


# ─────────────────────────────────────────────────────────
# Alta vía vista: mensaje neutro
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_alta_via_vista_informa_sin_exponer_el_otro_centro(
    client, centro_origen, centro_destino, ciudadano
):
    _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO)
    user = User.objects.create_superuser(
        username="super-cdi-vigencia",
        email="super-cdi-vigencia@example.com",
        password="test1234",
    )
    client.force_login(user)

    response = client.post(
        reverse("centrodeinfancia_nomina_crear", kwargs={"pk": centro_destino.pk}),
        data=datos_validos(
            centro_destino,
            ciudadano_id=ciudadano.id,
            estado=NominaCentroInfancia.ESTADO_ACTIVO,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento="2021-07-01",
            sexo="Masculino",
        ),
    )
    contenido = response.content.decode()

    assert response.status_code == 200
    assert not NominaCentroInfancia.objects.filter(centro=centro_destino).exists()
    assert MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO in contenido
    assert NOMBRE_CENTRO_A_OCULTAR not in contenido
    # Tampoco se filtra el identificador: ningún enlace apunta al centro de origen.
    assert (
        reverse("centrodeinfancia_nomina_ver", kwargs={"pk": centro_origen.pk})
        not in contenido
    )


# ─────────────────────────────────────────────────────────
# Edición: no se puede reactivar para saltear la regla
# ─────────────────────────────────────────────────────────


def _datos_edicion(nomina, estado):
    return {
        "estado": estado,
        "dni": nomina.dni,
        "apellido": nomina.apellido,
        "nombre": nomina.nombre,
        "fecha_nacimiento": "2021-07-01",
    }


@pytest.mark.django_db
def test_edicion_no_permite_reactivar_si_hay_vigencia_en_otro_centro(
    centro_origen, centro_destino, ciudadano
):
    _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO)
    nomina_baja = _crear_nomina(
        centro_destino, ciudadano, NominaCentroInfancia.ESTADO_BAJA
    )

    form = NominaCentroInfanciaForm(
        data=_datos_edicion(nomina_baja, NominaCentroInfancia.ESTADO_ACTIVO),
        instance=nomina_baja,
    )

    assert form.is_valid() is False
    assert form.errors["__all__"] == [MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO]
    assert NOMBRE_CENTRO_A_OCULTAR not in str(form.errors)
    nomina_baja.refresh_from_db()
    assert nomina_baja.estado == NominaCentroInfancia.ESTADO_BAJA


@pytest.mark.django_db
def test_edicion_permite_reactivar_si_no_hay_vigencia_en_otro_centro(
    centro_origen, centro_destino, ciudadano
):
    _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_BAJA)
    nomina_baja = _crear_nomina(
        centro_destino, ciudadano, NominaCentroInfancia.ESTADO_BAJA
    )

    form = NominaCentroInfanciaForm(
        data=_datos_edicion(nomina_baja, NominaCentroInfancia.ESTADO_ACTIVO),
        instance=nomina_baja,
    )

    assert form.is_valid() is True, form.errors


@pytest.mark.django_db
def test_edicion_de_una_ficha_ya_vigente_no_queda_bloqueada(
    centro_origen, centro_destino, ciudadano
):
    """Duplicados históricos: fuera de alcance, pero deben seguir siendo editables."""
    _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO)
    nomina_vigente = _crear_nomina(
        centro_destino, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO
    )

    form = NominaCentroInfanciaForm(
        data=_datos_edicion(nomina_vigente, NominaCentroInfancia.ESTADO_PENDIENTE),
        instance=nomina_vigente,
    )

    assert form.is_valid() is True, form.errors


@pytest.mark.django_db
def test_edicion_ajax_rechaza_la_reactivacion(
    client, centro_origen, centro_destino, ciudadano
):
    _crear_nomina(centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO)
    nomina_baja = _crear_nomina(
        centro_destino, ciudadano, NominaCentroInfancia.ESTADO_BAJA
    )
    user = User.objects.create_superuser(
        username="super-cdi-edicion",
        email="super-cdi-edicion@example.com",
        password="test1234",
    )
    client.force_login(user)

    response = client.post(
        reverse("centrodeinfancia_nomina_editar_ajax", kwargs={"pk": nomina_baja.pk}),
        data=_datos_edicion(nomina_baja, NominaCentroInfancia.ESTADO_ACTIVO),
    )
    data = response.json()

    assert data["success"] is False
    assert data["errors"]["__all__"] == [MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO]
    assert NOMBRE_CENTRO_A_OCULTAR not in response.content.decode()
    nomina_baja.refresh_from_db()
    assert nomina_baja.estado == NominaCentroInfancia.ESTADO_BAJA


# ─────────────────────────────────────────────────────────
# Derivación
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_derivacion_bloquea_si_hay_vigencia_en_un_tercer_centro(
    provincia, centro_origen, centro_destino, ciudadano
):
    tercero = CentroDeInfancia.objects.create(
        nombre="CDI Vigencia Tercero", provincia=provincia
    )
    nomina_origen = _crear_nomina(
        centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO
    )
    _crear_nomina(tercero, ciudadano, NominaCentroInfancia.ESTADO_PENDIENTE)
    usuario = User.objects.create_superuser(
        username="super-cdi-derivacion",
        email="super-cdi-derivacion@example.com",
        password="test1234",
    )

    ok, msg = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina_origen.pk,
        centro_destino_pk=centro_destino.pk,
        usuario=usuario,
    )

    assert ok is False
    assert msg == MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO
    assert "Tercero" not in msg
    nomina_origen.refresh_from_db()
    assert nomina_origen.estado == NominaCentroInfancia.ESTADO_ACTIVO
    assert not NominaCentroInfancia.objects.filter(centro=centro_destino).exists()


@pytest.mark.django_db
def test_derivacion_permite_recrear_pendiente_en_destino(
    centro_origen, centro_destino, ciudadano
):
    """El flujo de derivación sigue funcionando: origen a Baja, destino Pendiente."""
    nomina_origen = _crear_nomina(
        centro_origen, ciudadano, NominaCentroInfancia.ESTADO_ACTIVO
    )
    usuario = User.objects.create_superuser(
        username="super-cdi-derivacion-ok",
        email="super-cdi-derivacion-ok@example.com",
        password="test1234",
    )

    ok, _ = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina_origen.pk,
        centro_destino_pk=centro_destino.pk,
        usuario=usuario,
    )

    assert ok is True
    nomina_origen.refresh_from_db()
    assert nomina_origen.estado == NominaCentroInfancia.ESTADO_BAJA
    assert NominaCentroInfancia.objects.get(centro=centro_destino).estado == (
        NominaCentroInfancia.ESTADO_PENDIENTE
    )
