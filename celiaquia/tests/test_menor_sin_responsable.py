"""Tests: un menor no puede quedar sin adulto responsable en el expediente.

La relacion familiar vive en ``ciudadanos.GrupoFamiliar`` y cuelga del
ciudadano, no del legajo: al dar de baja el legajo del responsable el vinculo
sobrevive y el menor queda sin responsable *dentro del expediente*. Se cubre:

- deteccion del menor huerfano (servicio),
- aviso (no bloqueo) al eliminar el legajo del responsable,
- bloqueo del envio, tanto en el service como en la vista.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.urls import reverse

from ciudadanos.models import Ciudadano, GrupoFamiliar
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)
from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.services.validacion_edad_service import ValidacionEdadService


def _hace_anios(anios):
    hoy = date.today()
    return date(hoy.year - anios, 1, 1)


def _usuario(username):
    user = User.objects.create_user(username=username, password="pass")
    content_type = ContentType.objects.get_for_model(Expediente)
    perm, _ = Permission.objects.get_or_create(
        codename="view_expediente",
        content_type=content_type,
        defaults={"name": "view_expediente"},
    )
    user.user_permissions.add(perm)
    return user


def _ciudadano(documento, edad, nombre="Test"):
    return Ciudadano.objects.create(
        apellido="QaMenor",
        nombre=nombre,
        fecha_nacimiento=_hace_anios(edad),
        documento=documento,
    )


def _legajo(expediente, ciudadano, rol, con_archivos=True):
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        rol=rol,
    )
    if con_archivos:
        # Los tres slots cubren cualquier combinacion de archivos requeridos.
        legajo.archivo1 = "celiaquia/qa-1.pdf"
        legajo.archivo2 = "celiaquia/qa-2.pdf"
        legajo.archivo3 = "celiaquia/qa-3.pdf"
        legajo.save()
    return legajo


@pytest.fixture
def grupo_familiar(db):
    """Expediente EN_ESPERA con un responsable adulto y su hijo menor."""
    user = _usuario("qa-menor-resp")
    estado, _ = EstadoExpediente.objects.get_or_create(nombre="EN_ESPERA")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)

    adulto = _ciudadano("20111111110", 40, nombre="Adulto")
    menor = _ciudadano("20222222220", 10, nombre="Menor")
    GrupoFamiliar.objects.create(
        ciudadano_1=adulto,
        ciudadano_2=menor,
        vinculo=GrupoFamiliar.RELACION_PADRE,
        conviven=True,
        cuidador_principal=True,
    )

    legajo_adulto = _legajo(expediente, adulto, ExpedienteCiudadano.ROLE_RESPONSABLE)
    legajo_menor = _legajo(expediente, menor, ExpedienteCiudadano.ROLE_BENEFICIARIO)
    return {
        "user": user,
        "expediente": expediente,
        "legajo_adulto": legajo_adulto,
        "legajo_menor": legajo_menor,
    }


@pytest.mark.django_db
def test_menor_con_responsable_no_es_huerfano(grupo_familiar):
    assert (
        ValidacionEdadService.menores_sin_responsable(grupo_familiar["expediente"])
        == []
    )


@pytest.mark.django_db
def test_menor_queda_huerfano_al_eliminar_al_responsable(grupo_familiar):
    grupo_familiar["legajo_adulto"].delete()

    huerfanos = ValidacionEdadService.menores_sin_responsable(
        grupo_familiar["expediente"]
    )
    assert [leg.pk for leg in huerfanos] == [grupo_familiar["legajo_menor"].pk]


@pytest.mark.django_db
def test_beneficiario_adulto_sin_responsable_no_se_marca(db):
    user = _usuario("qa-menor-adulto")
    estado, _ = EstadoExpediente.objects.get_or_create(nombre="EN_ESPERA")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)
    _legajo(
        expediente,
        _ciudadano("20333333330", 45, nombre="Solo"),
        ExpedienteCiudadano.ROLE_BENEFICIARIO,
    )

    assert ValidacionEdadService.menores_sin_responsable(expediente) == []


@pytest.mark.django_db
def test_sin_fecha_de_nacimiento_no_bloquea(db):
    user = _usuario("qa-menor-sinfecha")
    estado, _ = EstadoExpediente.objects.get_or_create(nombre="EN_ESPERA")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)
    ciudadano = Ciudadano.objects.create(
        apellido="QaMenor", nombre="SinFecha", documento="20444444440"
    )
    _legajo(expediente, ciudadano, ExpedienteCiudadano.ROLE_BENEFICIARIO)

    assert ValidacionEdadService.menores_sin_responsable(expediente) == []


@pytest.mark.django_db
def test_advertencia_al_eliminar_al_responsable(grupo_familiar):
    aviso = ValidacionEdadService.advertencia_por_eliminacion(
        grupo_familiar["legajo_adulto"]
    )

    assert aviso is not None
    assert aviso["legajo_ids"] == [grupo_familiar["legajo_menor"].pk]
    assert "adulto responsable" in aviso["mensaje"]


@pytest.mark.django_db
def test_sin_advertencia_al_eliminar_al_menor(grupo_familiar):
    assert (
        ValidacionEdadService.advertencia_por_eliminacion(
            grupo_familiar["legajo_menor"]
        )
        is None
    )


@pytest.mark.django_db
def test_confirmar_envio_bloquea_al_menor_huerfano(grupo_familiar):
    grupo_familiar["legajo_adulto"].delete()

    with pytest.raises(ValidationError) as exc:
        ExpedienteService.confirmar_envio(
            grupo_familiar["expediente"], grupo_familiar["user"]
        )

    assert "adulto" in "; ".join(exc.value.messages)
    grupo_familiar["expediente"].refresh_from_db()
    assert grupo_familiar["expediente"].estado.nombre == "EN_ESPERA"


@pytest.mark.django_db
def test_confirmar_envio_ok_con_responsable(grupo_familiar):
    ExpedienteService.confirmar_envio(
        grupo_familiar["expediente"], grupo_familiar["user"]
    )

    grupo_familiar["expediente"].refresh_from_db()
    assert grupo_familiar["expediente"].estado.nombre == "CONFIRMACION_DE_ENVIO"


@pytest.mark.django_db
def test_vista_confirmar_envio_devuelve_400_y_no_envia(client, grupo_familiar):
    grupo_familiar["legajo_adulto"].delete()
    client.force_login(grupo_familiar["user"])

    response = client.post(
        reverse("expediente_confirm", args=[grupo_familiar["expediente"].pk]),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["menores_sin_responsable_ids"] == [grupo_familiar["legajo_menor"].pk]
    grupo_familiar["expediente"].refresh_from_db()
    assert grupo_familiar["expediente"].estado.nombre == "EN_ESPERA"


@pytest.mark.django_db
def test_eliminar_al_responsable_no_se_bloquea(client, grupo_familiar):
    """La baja se permite: se avisa, y el bloqueo llega recien en el envio."""
    grupo_familiar["user"].is_superuser = True
    grupo_familiar["user"].save()
    client.force_login(grupo_familiar["user"])

    response = client.post(
        reverse(
            "legajo_revisar",
            args=[
                grupo_familiar["expediente"].pk,
                grupo_familiar["legajo_adulto"].pk,
            ],
        ),
        data={"accion": "ELIMINAR"},
    )

    assert response.status_code == 200
    assert response.json().get("success") is True
    assert not ExpedienteCiudadano.objects.filter(
        pk=grupo_familiar["legajo_adulto"].pk
    ).exists()


@pytest.mark.django_db
def test_preview_de_eliminacion_incluye_el_aviso(client, grupo_familiar):
    grupo_familiar["user"].is_superuser = True
    grupo_familiar["user"].save()
    client.force_login(grupo_familiar["user"])

    response = client.post(
        reverse(
            "legajo_revisar",
            args=[
                grupo_familiar["expediente"].pk,
                grupo_familiar["legajo_adulto"].pk,
            ],
        ),
        data={"accion": "ELIMINAR", "preview": "1"},
    )

    assert response.status_code == 200
    aviso = response.json().get("menores_sin_responsable")
    assert aviso is not None
    assert aviso["legajo_ids"] == [grupo_familiar["legajo_menor"].pk]
