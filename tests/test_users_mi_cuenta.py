"""Tests del flujo de confirmación de datos personales y de Mi cuenta."""

import pytest
from django.apps import apps as global_apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from users.forms import MiCuentaForm
from users.models import Profile

User = get_user_model()

CUIL_VALIDO = "20-12345678-6"
CUIL_INVALIDO = "20-12345678-9"


def _form_data(**overrides):
    data = {
        "first_name": "Ana",
        "last_name": "Pérez",
        "email": "ana@example.com",
        "dni": "12345678",
        "cuil": CUIL_VALIDO,
        "correo_institucional": "",
    }
    data.update(overrides)
    return data


def _crear_usuario(username, **profile_flags):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="Secreta123!",
    )
    if profile_flags:
        for field, value in profile_flags.items():
            setattr(user.profile, field, value)
        user.profile.save(update_fields=list(profile_flags))
    return user


# --- Formulario -------------------------------------------------------------


@pytest.mark.django_db
def test_form_no_expone_tipo_usuario_ni_rol():
    """UX/UI pidió sacarlos: son datos de administración."""

    user = _crear_usuario("ut0")

    form = MiCuentaForm(instance=user)

    assert "tipo_usuario" not in form.fields
    assert "rol" not in form.fields


@pytest.mark.django_db
@pytest.mark.parametrize(
    "campo",
    ["first_name", "last_name", "email", "dni", "cuil"],
)
def test_form_exige_todos_los_campos_menos_correo_institucional(campo):
    user = _crear_usuario(f"ut1_{campo}")

    form = MiCuentaForm(data=_form_data(**{campo: ""}), instance=user)

    assert form.is_valid() is False
    assert campo in form.errors


@pytest.mark.django_db
def test_form_acepta_correo_institucional_vacio():
    user = _crear_usuario("ut2")

    form = MiCuentaForm(data=_form_data(correo_institucional=""), instance=user)

    assert form.is_valid() is True, form.errors


@pytest.mark.django_db
def test_form_rechaza_cuil_con_digito_verificador_invalido():
    user = _crear_usuario("ut2d")

    form = MiCuentaForm(data=_form_data(cuil=CUIL_INVALIDO), instance=user)

    assert form.is_valid() is False
    assert "cuil" in form.errors


@pytest.mark.django_db
def test_form_guarda_user_y_profile_y_limpia_flag():
    user = _crear_usuario("ut3", needs_profile_confirmation=True)

    form = MiCuentaForm(
        data=_form_data(correo_institucional="ana@desarrollosocial.gob.ar"),
        instance=user,
    )
    assert form.is_valid() is True, form.errors
    form.save()

    user.refresh_from_db()
    assert user.first_name == "Ana"
    assert user.last_name == "Pérez"
    assert user.email == "ana@example.com"
    assert user.profile.dni == "12345678"
    assert user.profile.cuil == "20123456786"
    assert user.profile.correo_institucional == "ana@desarrollosocial.gob.ar"
    assert user.profile.declaracion_aceptada is False
    assert user.profile.needs_profile_confirmation is False
    assert user.profile.datos_confirmados_at is not None


@pytest.mark.django_db
def test_form_precarga_datos_del_perfil():
    """Todos los campos arrancan autocompletados con lo que ya hay en sistema."""

    user = _crear_usuario("ut4")
    user.first_name = "Ana"
    user.save(update_fields=["first_name"])
    user.profile.dni = "12345678"
    user.profile.cuil = "20123456786"
    user.profile.correo_institucional = "ana@desarrollosocial.gob.ar"
    user.profile.save(
        update_fields=[
            "dni",
            "cuil",
            "correo_institucional",
        ]
    )

    form = MiCuentaForm(instance=user)

    assert form.initial["first_name"] == "Ana"
    assert form.fields["dni"].initial == "12345678"
    assert form.fields["cuil"].initial == "20123456786"
    assert form.fields["correo_institucional"].initial == "ana@desarrollosocial.gob.ar"
    assert "declaracion_aceptada" not in form.fields


# --- Middleware -------------------------------------------------------------


@pytest.mark.django_db
def test_middleware_redirige_cuando_falta_confirmar(client):
    user = _crear_usuario("it1", needs_profile_confirmation=True)
    client.force_login(user)

    response = client.get("/")

    assert response.status_code in {302, 303}
    assert reverse("confirmar_datos_personales") in response.url


@pytest.mark.django_db
def test_middleware_no_redirige_luego_de_confirmar(client):
    user = _crear_usuario("it2", needs_profile_confirmation=True)
    client.force_login(user)

    response = client.post(
        reverse("confirmar_datos_personales"),
        data=_form_data(cuil=CUIL_VALIDO),
    )
    assert response.status_code in {302, 303}

    user.refresh_from_db()
    assert user.profile.needs_profile_confirmation is False

    response = client.get("/")
    assert reverse("confirmar_datos_personales") not in getattr(response, "url", "")


@pytest.mark.django_db
def test_middleware_no_molesta_a_usuarios_nuevos(client):
    user = _crear_usuario("nuevo")
    client.force_login(user)

    response = client.get("/")

    assert reverse("confirmar_datos_personales") not in getattr(response, "url", "")


@pytest.mark.django_db
def test_middleware_exime_la_propia_vista_de_confirmacion(client):
    user = _crear_usuario("it3", needs_profile_confirmation=True)
    client.force_login(user)

    response = client.get(reverse("confirmar_datos_personales"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_middleware_exime_api(client):
    user = _crear_usuario("it4", needs_profile_confirmation=True)
    client.force_login(user)

    response = client.get("/api/users/login/")

    assert response.status_code not in {302, 303}


@pytest.mark.django_db
def test_password_change_tiene_prioridad_sobre_confirmacion(client):
    user = _crear_usuario(
        "it5",
        must_change_password=True,
        needs_profile_confirmation=True,
    )
    client.force_login(user)

    response = client.get("/")

    assert response.status_code in {302, 303}
    assert reverse("password_change_required") in response.url


@pytest.mark.django_db
def test_confirmacion_no_bloquea_el_cambio_de_password_obligatorio(client):
    user = _crear_usuario(
        "it6",
        must_change_password=True,
        needs_profile_confirmation=True,
    )
    client.force_login(user)

    response = client.get(reverse("password_change_required"))

    assert response.status_code == 200


def test_middleware_registrado_despues_del_de_password():
    middlewares = list(settings.MIDDLEWARE)

    assert middlewares.index(
        "users.middleware.FirstLoginPasswordChangeMiddleware"
    ) < middlewares.index("users.middleware.ProfileConfirmationMiddleware")


# --- Vistas -----------------------------------------------------------------


@pytest.mark.django_db
def test_mi_cuenta_precarga_datos_actuales(client):
    user = _crear_usuario("vista1")
    user.first_name = "Ana"
    user.save(update_fields=["first_name"])
    user.profile.dni = "12345678"
    user.profile.save(update_fields=["dni"])
    client.force_login(user)

    response = client.get(reverse("mi_cuenta"))

    assert response.status_code == 200
    assert response.context["form"].initial["first_name"] == "Ana"
    assert response.context["form"].fields["dni"].initial == "12345678"


@pytest.mark.django_db
def test_mi_cuenta_guarda_cambios(client):
    user = _crear_usuario("vista2")
    client.force_login(user)

    response = client.post(reverse("mi_cuenta"), data=_form_data(cuil=CUIL_VALIDO))

    assert response.status_code in {302, 303}
    user.refresh_from_db()
    assert user.profile.dni == "12345678"


@pytest.mark.django_db
def test_mi_cuenta_requiere_login(client):
    response = client.get(reverse("mi_cuenta"))

    assert response.status_code in {302, 303}


@pytest.mark.django_db
def test_confirmacion_redirige_si_ya_fue_confirmada(client):
    user = _crear_usuario("vista3")
    client.force_login(user)

    response = client.get(reverse("confirmar_datos_personales"))

    assert response.status_code in {302, 303}


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["mi_cuenta", "confirmar_datos_personales"])
def test_boton_guardar_se_habilita_por_js_en_ambas_vistas(client, url_name):
    """El gate del botón es ayuda de UX; la validación real es del servidor."""

    # El middleware redirige /mi-cuenta/ mientras la confirmación esté pendiente.
    pendiente = url_name == "confirmar_datos_personales"
    user = _crear_usuario(f"js_{url_name}", needs_profile_confirmation=pendiente)
    client.force_login(user)

    html = client.get(reverse(url_name)).content.decode()

    assert "data-mi-cuenta-submit" in html
    assert "data-mi-cuenta-form" in html
    assert "checkValidity" in html


@pytest.mark.django_db
def test_confirmacion_no_muestra_declaracion(client):
    user = _crear_usuario("sin_declaracion", needs_profile_confirmation=True)
    client.force_login(user)

    response = client.get(reverse("confirmar_datos_personales"))
    html = response.content.decode()

    assert "declaracion_aceptada" not in html
    assert "Acepto que la información contenida" not in html
    assert "Estos datos se usan para identificación y auditoría interna." not in html

    response = client.post(
        reverse("confirmar_datos_personales"),
        data=_form_data(),
    )

    assert response.status_code in {302, 303}
    user.refresh_from_db()
    assert user.profile.needs_profile_confirmation is False


@pytest.mark.django_db
def test_mi_cuenta_no_muestra_declaracion(client):
    user = _crear_usuario("mi_cuenta_sin_declaracion")
    client.force_login(user)

    html = client.get(reverse("mi_cuenta")).content.decode()

    assert "declaracion_aceptada" not in html
    assert "Acepto que la información contenida" not in html
    assert "Estos datos se usan para identificación y auditoría interna." not in html


def test_sidebar_expone_mi_cuenta():
    template_source = (
        settings.BASE_DIR / "templates" / "includes" / "sidebar" / "opciones.html"
    ).read_text(encoding="utf-8")

    assert "{% url 'mi_cuenta' %}" in template_source
    assert "<p>Mi cuenta</p>" in template_source


# --- Data migration ---------------------------------------------------------


@pytest.mark.django_db
def test_data_migration_marca_perfiles_existentes_y_crea_faltantes():
    """La data migration no corre en tests (TEST MIGRATE=False): se invoca directo."""

    from importlib import import_module

    migracion = import_module("users.migrations.0044_profile_confirmacion_datos")

    activo = _crear_usuario("migracion_activo")
    inactivo = _crear_usuario("migracion_inactivo")
    inactivo.is_active = False
    inactivo.save(update_fields=["is_active"])

    sin_perfil = _crear_usuario("migracion_sin_perfil")
    sin_perfil.profile.delete()

    migracion.marcar_perfiles_existentes(global_apps, None)

    assert Profile.objects.get(user=activo).needs_profile_confirmation is True
    assert Profile.objects.get(user=inactivo).needs_profile_confirmation is False
    assert Profile.objects.get(user=sin_perfil).needs_profile_confirmation is True
