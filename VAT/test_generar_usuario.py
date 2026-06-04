import pytest
from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from VAT.models import Centro
from VAT.services.access_scope import (
    GRUPO_REFERENTE_CENTRO_VAT,
    puede_generar_usuario_centro_vat,
    puede_ver_usuarios_centro_vat,
    usuarios_centro_vat_restantes,
)
from VAT.views.generar_usuario import GenerarUsuarioCentroVATView
from users.models import Profile
from users.services_generate_user import (
    DatosUsuarioDelegado,
    generar_usuario_delegado,
)

CENTRO_DEFAULTS = {
    "telefono": "11-1111",
    "celular": "11-2222",
    "correo": "centro@example.com",
    "domicilio_actividad": "Av. Siempre Viva 123",
    "nombre_referente": "Lia",
    "apellido_referente": "Paz",
    "telefono_referente": "11-3333",
    "correo_referente": "lia@example.com",
}


@pytest.fixture(autouse=True)
def _grupo_cfp(db):
    """Las data migrations no corren en tests (TEST MIGRATE=False)."""
    Group.objects.get_or_create(name=GRUPO_REFERENTE_CENTRO_VAT)


def _superuser_con_delegacion(username):
    user = User.objects.create_superuser(
        username=username, email=f"{username}@example.com", password="test1234"
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    grupo = Group.objects.get(name=GRUPO_REFERENTE_CENTRO_VAT)
    profile.grupos_asignables.add(grupo)
    return user


def _crear_centro(codigo, **extra):
    return Centro.objects.create(
        nombre=f"Centro {codigo}",
        codigo=codigo,
        **{**CENTRO_DEFAULTS, **extra},
    )


def _post_request(path, data, user):
    request = RequestFactory().post(path, data=data)
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    request.csp_nonce = "test-nonce"
    return request


# --------------------------- Acceso ----------------------------------------


@pytest.mark.django_db
def test_puede_generar_requiere_capacidad_y_delegacion():
    centro = _crear_centro("C-1")
    actor_ok = _superuser_con_delegacion("su-ok")
    assert puede_generar_usuario_centro_vat(actor_ok, centro) is True

    # Usuario regular sin permisos VAT: no puede editar el centro, no genera.
    usuario_regular = User.objects.create_user(
        username="user-no-vat", email="nov@example.com", password="test1234"
    )
    Profile.objects.get_or_create(user=usuario_regular)
    assert puede_generar_usuario_centro_vat(usuario_regular, centro) is False


@pytest.mark.django_db
def test_puede_generar_falso_si_cupo_lleno():
    centro = _crear_centro("C-2")
    actor = _superuser_con_delegacion("su-cupo")

    for i in range(10):
        u = User.objects.create_user(username=f"ref-{i}", email=f"r{i}@example.com")
        Profile.objects.get_or_create(user=u)
        centro.referentes.add(u)

    assert usuarios_centro_vat_restantes(centro) == 0
    assert puede_generar_usuario_centro_vat(actor, centro) is False


@pytest.mark.django_db
def test_puede_ver_usuarios_solo_referente_o_sse():
    centro = _crear_centro("C-3")
    sse = _superuser_con_delegacion("su-ver")
    referente = User.objects.create_user(
        username="ref-ver", email="rv@example.com", password="test1234"
    )
    Profile.objects.get_or_create(user=referente)
    centro.referentes.add(referente)

    otro = User.objects.create_user(username="otro", email="otro@example.com")
    Profile.objects.get_or_create(user=otro)

    assert puede_ver_usuarios_centro_vat(sse, centro) is True
    assert puede_ver_usuarios_centro_vat(referente, centro) is True
    assert puede_ver_usuarios_centro_vat(otro, centro) is False


# --------------------------- Service ---------------------------------------


@pytest.mark.django_db
def test_service_crea_usuario_y_lo_vincula_al_centro(settings):
    settings.DOMINIO = "http://testserver"
    centro = _crear_centro("C-4")
    actor = _superuser_con_delegacion("su-srv")

    resultado = generar_usuario_delegado(
        actor=actor,
        datos=DatosUsuarioDelegado(
            first_name="Ana", last_name="Gomez", email="ana@example.com"
        ),
        grupo_nombre=GRUPO_REFERENTE_CENTRO_VAT,
        vinculo_callback=lambda nuevo: centro.referentes.add(nuevo),
    )

    nuevo = resultado["user"]
    assert nuevo.groups.filter(name=GRUPO_REFERENTE_CENTRO_VAT).exists()
    assert centro.referentes.filter(pk=nuevo.pk).exists()
    assert nuevo.profile.temporary_password_plaintext == resultado["password"]
    assert resultado["email_enviado"] is True
    assert len(mail.outbox) == 1


# --------------------------- Vista -----------------------------------------


@pytest.mark.django_db
def test_vista_genera_usuario_y_muestra_credenciales(settings):
    settings.DOMINIO = "http://testserver"
    centro = _crear_centro("C-5")
    actor = _superuser_con_delegacion("su-view")

    request = _post_request(
        f"/vat/centros/{centro.pk}/generar-usuario/",
        {"first_name": "Lia", "last_name": "Paz", "email": "lia2@example.com"},
        actor,
    )
    response = GenerarUsuarioCentroVATView.as_view()(request, pk=centro.pk)

    assert response.status_code == 200
    assert response.template_name == "vat/centros/usuario_generado.html"
    nuevo = User.objects.get(email__iexact="lia2@example.com")
    assert centro.referentes.filter(pk=nuevo.pk).exists()
    assert (
        response.context_data["password"] == nuevo.profile.temporary_password_plaintext
    )


@pytest.mark.django_db
def test_vista_prohibida_si_actor_no_puede_editar():
    centro = _crear_centro("C-6")
    usuario_regular = User.objects.create_user(
        username="user-bloq", email="b@example.com", password="test1234"
    )
    Profile.objects.get_or_create(user=usuario_regular)

    request = _post_request(
        f"/vat/centros/{centro.pk}/generar-usuario/",
        {"first_name": "X", "last_name": "Y", "email": "xy@example.com"},
        usuario_regular,
    )
    with pytest.raises(PermissionDenied):
        GenerarUsuarioCentroVATView.as_view()(request, pk=centro.pk)
    assert not User.objects.filter(email__iexact="xy@example.com").exists()


# --------------------------- Precarga --------------------------------------


@pytest.mark.django_db
def test_initial_precarga_solo_el_primer_usuario():
    centro = _crear_centro("C-7")

    primero = GenerarUsuarioCentroVATView()
    primero.centro = centro
    assert primero.get_initial() == {
        "first_name": "Lia",
        "last_name": "Paz",
        "email": "lia@example.com",
    }

    user = User.objects.create_user(username="ya-existe", email="ya@example.com")
    Profile.objects.get_or_create(user=user)
    centro.referentes.add(user)

    siguiente = GenerarUsuarioCentroVATView()
    siguiente.centro = centro
    assert siguiente.get_initial() == {}
