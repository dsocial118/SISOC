import pytest
from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.test import RequestFactory

from core.constants import UserGroups
from core.models import Provincia
from centrodeinfancia.access import (
    puede_generar_usuario_cdi,
    puede_ver_usuarios_cdi,
)
from centrodeinfancia.models import AccesoCDI, CentroDeInfancia
from centrodeinfancia.views import CentroDeInfanciaDetailView
from centrodeinfancia.views_usuario_cdi import GenerarUsuarioCDIView
from users.models import Profile
from users.services_generate_user import (
    DatosUsuarioDelegado,
    generar_usuario_delegado,
)

GRUPO = UserGroups.CDI_REFERENTE_CENTRO


@pytest.fixture(autouse=True)
def _grupo_cdi_referente(db):
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
    return lambda nuevo: AccesoCDI.objects.create(
        user=nuevo, centro=centro, creado_por=actor
    )


# --------------------------- Service ---------------------------------------


@pytest.mark.django_db
def test_service_crea_usuario_grupo_acceso_y_password(settings):
    settings.DOMINIO = "http://testserver"
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    centro = CentroDeInfancia.objects.create(nombre="CDI 1", provincia=provincia)
    actor = _provincial("prov-1", provincia)

    resultado = generar_usuario_delegado(
        actor=actor,
        datos=DatosUsuarioDelegado(
            first_name="Ana", last_name="Gomez", email="ana@example.com"
        ),
        grupo_nombre=GRUPO,
        vinculo_callback=_vinculo(centro, actor),
    )

    nuevo = resultado["user"]
    assert nuevo.groups.filter(name=GRUPO).exists()
    assert nuevo.is_staff is True
    assert AccesoCDI.objects.filter(user=nuevo, centro=centro, activo=True).exists()
    assert nuevo.profile.must_change_password is True
    assert nuevo.profile.temporary_password_plaintext == resultado["password"]
    assert resultado["email_enviado"] is True
    assert len(mail.outbox) == 1
    assert "ana@example.com" in mail.outbox[0].to


@pytest.mark.django_db
def test_service_rechaza_actor_sin_grupo_delegable():
    provincia = Provincia.objects.create(nombre="Cordoba")
    centro = CentroDeInfancia.objects.create(nombre="CDI 2", provincia=provincia)
    actor = _provincial("prov-2", provincia, con_grupo_delegable=False)

    with pytest.raises(ValidationError):
        generar_usuario_delegado(
            actor=actor,
            datos=DatosUsuarioDelegado(
                first_name="X", last_name="Y", email="x@example.com"
            ),
            grupo_nombre=GRUPO,
            vinculo_callback=_vinculo(centro, actor),
        )
    assert not User.objects.filter(email__iexact="x@example.com").exists()


@pytest.mark.django_db
def test_service_respeta_limite():
    provincia = Provincia.objects.create(nombre="Mendoza")
    centro = CentroDeInfancia.objects.create(nombre="CDI 3", provincia=provincia)
    actor = _provincial("prov-3", provincia)

    with pytest.raises(ValidationError):
        generar_usuario_delegado(
            actor=actor,
            datos=DatosUsuarioDelegado(
                first_name="X", last_name="Y", email="lim@example.com"
            ),
            grupo_nombre=GRUPO,
            vinculo_callback=_vinculo(centro, actor),
            limite_check=lambda: False,
        )


@pytest.mark.django_db
def test_service_permite_email_duplicado():
    provincia = Provincia.objects.create(nombre="Salta")
    centro = CentroDeInfancia.objects.create(nombre="CDI 4", provincia=provincia)
    actor = _provincial("prov-4", provincia)
    User.objects.create_user(username="existente", email="dup@example.com")

    resultado = generar_usuario_delegado(
        actor=actor,
        datos=DatosUsuarioDelegado(
            first_name="X",
            last_name="Y",
            email="dup@example.com",
        ),
        grupo_nombre=GRUPO,
        vinculo_callback=_vinculo(centro, actor),
    )

    assert resultado["user"].email == "dup@example.com"
    assert User.objects.filter(email__iexact="dup@example.com").count() == 2


# --------------------------- Acceso / botón --------------------------------


@pytest.mark.django_db
def test_puede_generar_solo_misma_provincia_y_grupo():
    prov_a = Provincia.objects.create(nombre="La Pampa")
    prov_b = Provincia.objects.create(nombre="Neuquen")
    centro_a = CentroDeInfancia.objects.create(nombre="CDI A", provincia=prov_a)

    actor_ok = _provincial("prov-ok", prov_a)
    actor_otra_prov = _provincial("prov-otra", prov_b)
    actor_sin_grupo = _provincial("prov-sg", prov_a, con_grupo_delegable=False)

    assert puede_generar_usuario_cdi(actor_ok, centro_a) is True
    assert puede_generar_usuario_cdi(actor_otra_prov, centro_a) is False
    assert puede_generar_usuario_cdi(actor_sin_grupo, centro_a) is False


@pytest.mark.django_db
def test_puede_generar_falso_si_cupo_lleno():
    provincia = Provincia.objects.create(nombre="Chaco")
    centro = CentroDeInfancia.objects.create(nombre="CDI Cupo", provincia=provincia)
    actor = _provincial("prov-cupo", provincia)

    for i in range(AccesoCDI.LIMITE_USUARIOS_POR_CENTRO):
        usuario = User.objects.create_user(username=f"ref-{i}")
        AccesoCDI.objects.create(user=usuario, centro=centro, creado_por=actor)

    assert puede_generar_usuario_cdi(actor, centro) is False


# --------------------------- Vista -----------------------------------------


def _post_request(path, data, user):
    request = RequestFactory().post(path, data=data)
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    # En request real lo setea el middleware de CSP; aquí se llama la vista directa.
    request.csp_nonce = "test-nonce"
    return request


@pytest.mark.django_db
def test_vista_genera_usuario_y_muestra_credenciales(settings):
    settings.DOMINIO = "http://testserver"
    provincia = Provincia.objects.create(nombre="San Juan")
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Vista",
        provincia=provincia,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="lia@example.com",
    )
    actor = _provincial("prov-vista", provincia)

    request = _post_request(
        f"/centrodeinfancia/{centro.pk}/generar-usuario/",
        {"first_name": "Lia", "last_name": "Paz", "email": "lia@example.com"},
        actor,
    )
    response = GenerarUsuarioCDIView.as_view()(request, pk=centro.pk)

    assert response.status_code == 200
    nuevo = User.objects.get(email__iexact="lia@example.com")
    assert nuevo.groups.filter(name=GRUPO).exists()
    assert AccesoCDI.objects.filter(user=nuevo, centro=centro).exists()
    assert response.template_name == "centrodeinfancia/usuario_cdi_generado.html"
    assert response.context_data["usuario"].pk == nuevo.pk
    assert (
        response.context_data["password"] == nuevo.profile.temporary_password_plaintext
    )


@pytest.mark.django_db
def test_vista_prohibida_para_otra_provincia():
    prov_a = Provincia.objects.create(nombre="Jujuy")
    prov_b = Provincia.objects.create(nombre="Misiones")
    centro = CentroDeInfancia.objects.create(nombre="CDI Juj", provincia=prov_a)
    actor = _provincial("prov-no", prov_b)

    request = _post_request(
        f"/centrodeinfancia/{centro.pk}/generar-usuario/",
        {"first_name": "A", "last_name": "B", "email": "ab@example.com"},
        actor,
    )
    with pytest.raises(PermissionDenied):
        GenerarUsuarioCDIView.as_view()(request, pk=centro.pk)
    assert not User.objects.filter(email__iexact="ab@example.com").exists()


# --------------------------- Scope referente -------------------------------


def _referente(username, centro):
    user = User.objects.create_user(username=username, password="test1234")
    Profile.objects.get_or_create(user=user)
    AccesoCDI.objects.create(user=user, centro=centro)
    return user


@pytest.mark.django_db
def test_puede_ver_usuarios_cdi_solo_referente_o_superadmin():
    provincia = Provincia.objects.create(nombre="Rio Negro")
    centro = CentroDeInfancia.objects.create(nombre="CDI Ver", provincia=provincia)
    otro_centro = CentroDeInfancia.objects.create(
        nombre="CDI Otro", provincia=provincia
    )

    referente = _referente("ref-ver", centro)
    referente_otro = _referente("ref-otro", otro_centro)
    provincial = _provincial("prov-ver", provincia)
    superadmin = User.objects.create_superuser(
        username="su-ver", email="su@example.com", password="test1234"
    )

    assert puede_ver_usuarios_cdi(referente, centro) is True
    assert puede_ver_usuarios_cdi(superadmin, centro) is True
    assert puede_ver_usuarios_cdi(provincial, centro) is False
    assert puede_ver_usuarios_cdi(referente_otro, centro) is False


@pytest.mark.django_db
def test_puede_ver_usuarios_cdi_falso_si_acceso_inactivo():
    provincia = Provincia.objects.create(nombre="Santa Cruz")
    centro = CentroDeInfancia.objects.create(nombre="CDI Baja", provincia=provincia)
    user = User.objects.create_user(username="ref-baja")
    Profile.objects.get_or_create(user=user)
    AccesoCDI.objects.create(user=user, centro=centro, activo=False)

    assert puede_ver_usuarios_cdi(user, centro) is False


@pytest.mark.django_db
def test_referente_solo_ve_su_centro():
    provincia = Provincia.objects.create(nombre="Entre Rios")
    centro_propio = CentroDeInfancia.objects.create(
        nombre="Propio", provincia=provincia
    )
    centro_ajeno = CentroDeInfancia.objects.create(nombre="Ajeno", provincia=provincia)
    referente = _referente("ref-1", centro_propio)

    request = RequestFactory().get("/")
    request.user = referente

    view_ok = CentroDeInfanciaDetailView()
    view_ok.setup(request, pk=centro_propio.pk)
    assert view_ok.get_object().pk == centro_propio.pk

    view_bad = CentroDeInfanciaDetailView()
    view_bad.setup(request, pk=centro_ajeno.pk)
    with pytest.raises(Http404):
        view_bad.get_object()


@pytest.mark.django_db
def test_detail_referente_solo_lista_su_propia_credencial():
    provincia = Provincia.objects.create(nombre="Tucuman")
    centro = CentroDeInfancia.objects.create(nombre="CDI Cred", provincia=provincia)
    referente = _referente("ref-propio", centro)
    otro_referente = _referente("ref-ajeno", centro)
    referente.profile.temporary_password_plaintext = "propia-temporal"
    referente.profile.save(update_fields=["temporary_password_plaintext"])
    otro_referente.profile.temporary_password_plaintext = "ajena-temporal"
    otro_referente.profile.save(update_fields=["temporary_password_plaintext"])

    request = RequestFactory().get("/")
    request.user = referente
    view = CentroDeInfanciaDetailView()
    view.setup(request, pk=centro.pk)
    view.object = centro

    usuarios_cdi = list(view.get_context_data(object=centro)["usuarios_cdi"])

    assert [acceso.user_id for acceso in usuarios_cdi] == [referente.id]


@pytest.mark.django_db
def test_detail_superuser_lista_todas_las_credenciales_del_centro():
    provincia = Provincia.objects.create(nombre="San Luis")
    centro = CentroDeInfancia.objects.create(nombre="CDI Admin", provincia=provincia)
    referente = _referente("ref-admin-1", centro)
    otro_referente = _referente("ref-admin-2", centro)
    superadmin = User.objects.create_superuser(
        username="su-cdi", email="su-cdi@example.com", password="test1234"
    )

    request = RequestFactory().get("/")
    request.user = superadmin
    view = CentroDeInfanciaDetailView()
    view.setup(request, pk=centro.pk)
    view.object = centro

    usuarios_cdi = list(view.get_context_data(object=centro)["usuarios_cdi"])

    assert {acceso.user_id for acceso in usuarios_cdi} == {
        referente.id,
        otro_referente.id,
    }


@pytest.mark.django_db
def test_provincial_no_se_ve_afectado_por_scope_referente():
    provincia = Provincia.objects.create(nombre="Formosa")
    centro = CentroDeInfancia.objects.create(nombre="CDI Prov", provincia=provincia)
    provincial = _provincial("prov-scope", provincia)

    request = RequestFactory().get("/")
    request.user = provincial
    view = CentroDeInfanciaDetailView()
    view.setup(request, pk=centro.pk)
    assert view.get_object().pk == centro.pk


# --------------------------- Precarga --------------------------------------


@pytest.mark.django_db
def test_initial_precarga_solo_el_primer_usuario():
    provincia = Provincia.objects.create(nombre="Catamarca")
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Pre",
        provincia=provincia,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="lia@example.com",
    )

    primero = GenerarUsuarioCDIView()
    primero.centro = centro
    assert primero.get_initial() == {
        "first_name": "Lia",
        "last_name": "Paz",
        "email": "lia@example.com",
    }

    usuario = User.objects.create_user(username="ref-existente")
    AccesoCDI.objects.create(user=usuario, centro=centro)

    siguiente = GenerarUsuarioCDIView()
    siguiente.centro = centro
    assert siguiente.get_initial() == {}
