import pytest
from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.test import RequestFactory

from core.constants import UserGroups
from core.models import Provincia
from centrodefamilia.access import (
    puede_generar_usuario_cdf,
    puede_ver_usuarios_cdf,
)
from centrodefamilia.models import AccesoCDF, Centro
from centrodefamilia.views.generar_usuario import GenerarUsuarioCDFView
from users.models import Profile
from users.services_generate_user import (
    DatosUsuarioDelegado,
    generar_usuario_delegado,
)

GRUPO = UserGroups.CDF_REFERENTE_CENTRO


@pytest.fixture(autouse=True)
def _grupo_cdf_referente(db):
    """Las data migrations no corren en tests (TEST MIGRATE=False)."""
    Group.objects.get_or_create(name=GRUPO)


def _provincial(username, provincia, *, con_grupo_delegable=True):
    user = User.objects.create_user(username=username, password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    if con_grupo_delegable:
        grupo = Group.objects.get(name=GRUPO)
        profile.grupos_asignables.add(grupo)
    return user


def _vinculo(centro, actor):
    return lambda nuevo: AccesoCDF.objects.create(
        user=nuevo, centro=centro, creado_por=actor
    )


def _centro(nombre, provincia):
    return Centro.objects.create(
        nombre=nombre,
        provincia=provincia,
        tipo="faro",
        codigo=nombre[:20],
        domicilio_actividad="Dirección de prueba",
        telefono="123",
        celular="456",
        correo="centro@test.com",
        nombre_referente="Ref",
        apellido_referente="Ente",
        telefono_referente="789",
        correo_referente="ref@test.com",
    )


# --------------------------- Service ---------------------------------------


@pytest.mark.django_db
def test_service_crea_usuario_grupo_acceso_y_password(settings):
    settings.DOMINIO = "http://testserver"
    provincia = Provincia.objects.create(nombre="Buenos Aires CDF")
    centro = _centro("CDF 1", provincia)
    actor = _provincial("prov-cdf-1", provincia)

    resultado = generar_usuario_delegado(
        actor=actor,
        datos=DatosUsuarioDelegado(
            first_name="Ana", last_name="Gomez", email="ana.cdf@example.com"
        ),
        grupo_nombre=GRUPO,
        vinculo_callback=_vinculo(centro, actor),
    )

    nuevo = resultado["user"]
    assert nuevo.groups.filter(name=GRUPO).exists()
    assert nuevo.is_staff is True
    assert AccesoCDF.objects.filter(user=nuevo, centro=centro, activo=True).exists()
    assert nuevo.profile.must_change_password is True
    assert nuevo.profile.temporary_password_plaintext == resultado["password"]
    assert resultado["email_enviado"] is True
    assert len(mail.outbox) == 1
    assert "ana.cdf@example.com" in mail.outbox[0].to


@pytest.mark.django_db
def test_service_rechaza_actor_sin_grupo_delegable():
    provincia = Provincia.objects.create(nombre="Cordoba CDF")
    centro = _centro("CDF 2", provincia)
    actor = _provincial("prov-cdf-2", provincia, con_grupo_delegable=False)

    with pytest.raises(ValidationError):
        generar_usuario_delegado(
            actor=actor,
            datos=DatosUsuarioDelegado(
                first_name="X", last_name="Y", email="x.cdf@example.com"
            ),
            grupo_nombre=GRUPO,
            vinculo_callback=_vinculo(centro, actor),
        )
    assert not User.objects.filter(email__iexact="x.cdf@example.com").exists()


@pytest.mark.django_db
def test_service_respeta_limite():
    provincia = Provincia.objects.create(nombre="Mendoza CDF")
    centro = _centro("CDF 3", provincia)
    actor = _provincial("prov-cdf-3", provincia)

    with pytest.raises(ValidationError):
        generar_usuario_delegado(
            actor=actor,
            datos=DatosUsuarioDelegado(
                first_name="X", last_name="Y", email="lim.cdf@example.com"
            ),
            grupo_nombre=GRUPO,
            vinculo_callback=_vinculo(centro, actor),
            limite_check=lambda: False,
        )


@pytest.mark.django_db
def test_service_rechaza_email_duplicado():
    provincia = Provincia.objects.create(nombre="Salta CDF")
    centro = _centro("CDF 4", provincia)
    actor = _provincial("prov-cdf-4", provincia)
    User.objects.create_user(username="existente-cdf", email="dup.cdf@example.com")

    with pytest.raises(ValidationError):
        generar_usuario_delegado(
            actor=actor,
            datos=DatosUsuarioDelegado(
                first_name="X", last_name="Y", email="dup.cdf@example.com"
            ),
            grupo_nombre=GRUPO,
            vinculo_callback=_vinculo(centro, actor),
        )


# --------------------------- Acceso / botón --------------------------------


@pytest.mark.django_db
def test_puede_generar_solo_misma_provincia_y_grupo():
    prov_a = Provincia.objects.create(nombre="La Pampa CDF")
    prov_b = Provincia.objects.create(nombre="Neuquen CDF")
    centro_a = _centro("CDF A", prov_a)

    actor_ok = _provincial("prov-cdf-ok", prov_a)
    actor_otra_prov = _provincial("prov-cdf-otra", prov_b)
    actor_sin_grupo = _provincial("prov-cdf-sg", prov_a, con_grupo_delegable=False)

    assert puede_generar_usuario_cdf(actor_ok, centro_a) is True
    assert puede_generar_usuario_cdf(actor_otra_prov, centro_a) is False
    assert puede_generar_usuario_cdf(actor_sin_grupo, centro_a) is False


@pytest.mark.django_db
def test_puede_generar_falso_si_cupo_lleno():
    provincia = Provincia.objects.create(nombre="Chaco CDF")
    centro = _centro("CDF Cupo", provincia)
    actor = _provincial("prov-cdf-cupo", provincia)

    for i in range(AccesoCDF.LIMITE_USUARIOS_POR_CENTRO):
        usuario = User.objects.create_user(username=f"ref-cdf-{i}")
        AccesoCDF.objects.create(user=usuario, centro=centro, creado_por=actor)

    assert puede_generar_usuario_cdf(actor, centro) is False


# --------------------------- Vista -----------------------------------------


def _post_request(path, data, user):
    request = RequestFactory().post(path, data=data)
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    request.csp_nonce = "test-nonce"
    return request


@pytest.mark.django_db
def test_vista_genera_usuario_y_muestra_credenciales(settings):
    settings.DOMINIO = "http://testserver"
    provincia = Provincia.objects.create(nombre="San Juan CDF")
    centro = _centro("CDF Vista", provincia)
    # sobrescribir datos del referente para precargar
    Centro.objects.filter(pk=centro.pk).update(
        nombre_referente="Lia",
        apellido_referente="Paz",
        correo_referente="lia.cdf@example.com",
    )
    centro.refresh_from_db()
    actor = _provincial("prov-cdf-vista", provincia)

    request = _post_request(
        f"/centros/{centro.pk}/generar-usuario/",
        {"first_name": "Lia", "last_name": "Paz", "email": "lia.cdf@example.com"},
        actor,
    )
    response = GenerarUsuarioCDFView.as_view()(request, pk=centro.pk)

    assert response.status_code == 200
    nuevo = User.objects.get(email__iexact="lia.cdf@example.com")
    assert nuevo.groups.filter(name=GRUPO).exists()
    assert AccesoCDF.objects.filter(user=nuevo, centro=centro).exists()
    assert response.template_name == "centros/usuario_cdf_generado.html"
    assert response.context_data["usuario"].pk == nuevo.pk
    assert (
        response.context_data["password"] == nuevo.profile.temporary_password_plaintext
    )


@pytest.mark.django_db
def test_vista_prohibida_para_otra_provincia():
    prov_a = Provincia.objects.create(nombre="Jujuy CDF")
    prov_b = Provincia.objects.create(nombre="Misiones CDF")
    centro = _centro("CDF Juj", prov_a)
    actor = _provincial("prov-cdf-no", prov_b)

    request = _post_request(
        f"/centros/{centro.pk}/generar-usuario/",
        {"first_name": "A", "last_name": "B", "email": "ab.cdf@example.com"},
        actor,
    )
    with pytest.raises(PermissionDenied):
        GenerarUsuarioCDFView.as_view()(request, pk=centro.pk)
    assert not User.objects.filter(email__iexact="ab.cdf@example.com").exists()


# --------------------------- puede_ver_usuarios_cdf ------------------------


def _referente_cdf(username, centro):
    user = User.objects.create_user(username=username, password="test1234")
    Profile.objects.get_or_create(user=user)
    AccesoCDF.objects.create(user=user, centro=centro)
    return user


@pytest.mark.django_db
def test_puede_ver_usuarios_cdf_solo_referente_o_superadmin():
    provincia = Provincia.objects.create(nombre="Rio Negro CDF")
    centro = _centro("CDF Ver", provincia)
    otro_centro = _centro("CDF Otro", provincia)

    referente = _referente_cdf("ref-cdf-ver", centro)
    referente_otro = _referente_cdf("ref-cdf-otro", otro_centro)
    provincial = _provincial("prov-cdf-ver", provincia)
    superadmin = User.objects.create_superuser(
        username="su-cdf-ver", email="su-cdf@example.com", password="test1234"
    )

    assert puede_ver_usuarios_cdf(referente, centro) is True
    assert puede_ver_usuarios_cdf(superadmin, centro) is True
    assert puede_ver_usuarios_cdf(provincial, centro) is False
    assert puede_ver_usuarios_cdf(referente_otro, centro) is False


@pytest.mark.django_db
def test_puede_ver_usuarios_cdf_falso_si_acceso_inactivo():
    provincia = Provincia.objects.create(nombre="Santa Cruz CDF")
    centro = _centro("CDF Baja", provincia)
    user = User.objects.create_user(username="ref-cdf-baja")
    Profile.objects.get_or_create(user=user)
    AccesoCDF.objects.create(user=user, centro=centro, activo=False)

    assert puede_ver_usuarios_cdf(user, centro) is False


# --------------------------- Precarga --------------------------------------


@pytest.mark.django_db
def test_initial_precarga_solo_el_primer_usuario():
    provincia = Provincia.objects.create(nombre="Catamarca CDF")
    centro = _centro("CDF Pre", provincia)
    Centro.objects.filter(pk=centro.pk).update(
        nombre_referente="Lia",
        apellido_referente="Paz",
        correo_referente="lia.pre@example.com",
    )
    centro.refresh_from_db()

    primero = GenerarUsuarioCDFView()
    primero.centro = centro
    assert primero.get_initial() == {
        "first_name": "Lia",
        "last_name": "Paz",
        "email": "lia.pre@example.com",
    }

    usuario = User.objects.create_user(username="ref-cdf-existente")
    AccesoCDF.objects.create(user=usuario, centro=centro)

    siguiente = GenerarUsuarioCDFView()
    siguiente.centro = centro
    assert siguiente.get_initial() == {}
