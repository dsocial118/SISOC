"""Tipo de documento (DNI / Pasaporte) en la carga manual de inscriptos.

REQ #2455. El número de pasaporte es alfanumérico y `Ciudadano.documento` es
numérico (lo usan como int decenas de módulos fuera de VAT), así que se guarda
en `documento_pasaporte`. La unicidad funcional sigue apoyada en
`documento_unico_key`, que ya combinaba tipo + número.
"""

import pytest
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from ciudadanos.models import Ciudadano
from VAT.forms import CiudadanoInscripcionRapidaForm


def _datos(**overrides):
    datos = {
        "apellido": "Pérez",
        "nombre": "Ana",
        "fecha_nacimiento": "2000-01-01",
        "tipo_documento": Ciudadano.DOCUMENTO_DNI,
        "documento": "30111222",
    }
    datos.update(overrides)
    return datos


@pytest.mark.django_db
def test_alta_con_dni_guarda_en_documento():
    form = CiudadanoInscripcionRapidaForm(_datos())

    assert form.is_valid(), form.errors
    ciudadano = form.save()

    assert ciudadano.documento == 30111222
    assert ciudadano.documento_pasaporte is None
    assert ciudadano.documento_unico_key == "DNI_30111222"


@pytest.mark.django_db
def test_alta_con_pasaporte_normaliza_y_guarda_en_campo_alfanumerico():
    form = CiudadanoInscripcionRapidaForm(
        _datos(tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE, documento=" ab123456 ")
    )

    assert form.is_valid(), form.errors
    ciudadano = form.save()

    assert ciudadano.documento_pasaporte == "AB123456"
    assert ciudadano.documento is None
    assert ciudadano.documento_unico_key == "PASAPORTE_AB123456"
    assert ciudadano.numero_documento == "AB123456"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "tipo_documento,documento",
    [
        (Ciudadano.DOCUMENTO_DNI, "123456"),
        (Ciudadano.DOCUMENTO_DNI, "123456789"),
        (Ciudadano.DOCUMENTO_DNI, "30.111.222"),
        (Ciudadano.DOCUMENTO_DNI, "AB123456"),
        (Ciudadano.DOCUMENTO_PASAPORTE, "AB12"),
        (Ciudadano.DOCUMENTO_PASAPORTE, "A" * 16),
        (Ciudadano.DOCUMENTO_PASAPORTE, "AB-12345"),
    ],
)
def test_formato_invalido_por_tipo_es_rechazado(tipo_documento, documento):
    form = CiudadanoInscripcionRapidaForm(
        _datos(tipo_documento=tipo_documento, documento=documento)
    )

    assert not form.is_valid()
    assert "documento" in form.errors


@pytest.mark.django_db
def test_mismo_numero_con_distinto_tipo_no_colisiona():
    CiudadanoInscripcionRapidaForm(_datos()).save()

    form = CiudadanoInscripcionRapidaForm(
        _datos(tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE, documento="30111222")
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_duplicado_informa_el_legajo_en_conflicto():
    existente = CiudadanoInscripcionRapidaForm(_datos()).save()

    form = CiudadanoInscripcionRapidaForm(_datos())

    assert not form.is_valid()
    assert f"legajo #{existente.pk}" in " ".join(form.errors["documento"])


@pytest.mark.django_db
def test_duplicado_detecta_legajos_borrados_logicamente():
    """documento_unico_key es unique a nivel base y alcanza a los borrados
    lógicamente: sin mirar all_objects el alta reventaría con IntegrityError."""
    existente = CiudadanoInscripcionRapidaForm(_datos()).save()
    existente.delete()

    form = CiudadanoInscripcionRapidaForm(_datos())

    assert not form.is_valid()
    assert "documento" in form.errors


@pytest.mark.django_db
def test_tipo_documento_no_se_puede_modificar_despues_del_alta():
    ciudadano = CiudadanoInscripcionRapidaForm(_datos()).save()

    recargado = Ciudadano.objects.get(pk=ciudadano.pk)
    recargado.tipo_documento = Ciudadano.DOCUMENTO_PASAPORTE

    with pytest.raises(ValidationError):
        recargado.save()


@pytest.mark.django_db
def test_tipo_documento_no_se_puede_modificar_en_la_misma_instancia_en_memoria():
    """El guard también debe cubrir una instancia creada y guardada que se
    reutiliza en el mismo proceso, sin pasar por from_db() otra vez."""
    ciudadano = CiudadanoInscripcionRapidaForm(_datos()).save()

    ciudadano.tipo_documento = Ciudadano.DOCUMENTO_PASAPORTE

    with pytest.raises(ValidationError):
        ciudadano.save()


@pytest.mark.django_db
def test_editar_otros_campos_sigue_funcionando():
    ciudadano = CiudadanoInscripcionRapidaForm(_datos()).save()

    recargado = Ciudadano.objects.get(pk=ciudadano.pk)
    recargado.nombre = "Ana María"
    recargado.save()

    recargado.refresh_from_db()
    assert recargado.nombre == "Ana María"


@pytest.mark.django_db
def test_pasaporte_historico_en_documento_conserva_su_clave_unica():
    """Antes de documento_pasaporte, un pasaporte se guardaba en `documento`.
    Esos registros deben mantener su documento_unico_key al volver a guardarse."""
    ciudadano = Ciudadano.objects.create(
        apellido="Gómez",
        nombre="Luis",
        tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE,
        documento=44555666,
    )

    assert ciudadano.documento_unico_key == "PASAPORTE_44555666"

    ciudadano.nombre = "Luis Alberto"
    ciudadano.save()
    ciudadano.refresh_from_db()

    assert ciudadano.documento_unico_key == "PASAPORTE_44555666"


def _cliente_con_permiso_de_lectura():
    user = User.objects.create_user(username="buscador-doc", password="test1234")
    user.user_permissions.add(Permission.objects.get(codename="view_ciudadano"))
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_busqueda_por_pasaporte_encuentra_al_inscripto():
    CiudadanoInscripcionRapidaForm(
        _datos(tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE, documento="AB123456")
    ).save()
    client = _cliente_con_permiso_de_lectura()

    response = client.get(
        reverse("api_buscar_ciudadanos"),
        {"q": "ab1234", "tipo_documento": Ciudadano.DOCUMENTO_PASAPORTE},
    )

    resultados = response.json()["results"]
    assert len(resultados) == 1
    assert "Pasaporte AB123456" in resultados[0]["text"]


@pytest.mark.django_db
def test_busqueda_por_pasaporte_no_devuelve_titulares_de_dni():
    CiudadanoInscripcionRapidaForm(_datos(documento="30111222")).save()
    client = _cliente_con_permiso_de_lectura()

    response = client.get(
        reverse("api_buscar_ciudadanos"),
        {"q": "30111222", "tipo_documento": Ciudadano.DOCUMENTO_PASAPORTE},
    )

    assert response.json()["results"] == []


@pytest.mark.django_db
def test_busqueda_sin_tipo_documento_conserva_el_comportamiento_previo():
    """Otras vistas (ej. grupofamiliar_form) llaman al endpoint sin el
    parámetro nuevo: la búsqueda por DNI debe seguir funcionando igual."""
    CiudadanoInscripcionRapidaForm(_datos(documento="30111222")).save()
    client = _cliente_con_permiso_de_lectura()

    response = client.get(reverse("api_buscar_ciudadanos"), {"q": "30111222"})

    resultados = response.json()["results"]
    assert len(resultados) == 1
    assert "30111222" in resultados[0]["text"]
