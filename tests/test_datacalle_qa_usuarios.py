"""Revisión QA 2026-09-16 — ítems del módulo de usuarios."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from core.models import Provincia
from users.services import UsuariosService


@pytest.fixture
def provincia(db):
    return Provincia.objects.create(nombre="Córdoba")


def _coordinador_datacalle(provincia, username="coord_dc"):
    """Coordinador tal como lo crea un administrador: grupo + alcance."""
    from django.contrib.auth.models import Permission

    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    grupo, _ = Group.objects.get_or_create(name="Coordinador DataCalle")
    grupo.permissions.add(
        *Permission.objects.filter(
            content_type__app_label="datacalle",
            codename__in=["view_relevamiento", "change_relevamiento"],
        )
    )
    user.groups.add(grupo)
    user.profile.es_usuario_provincial = True
    # datacalle_rol es la unica fuente de verdad que miran los helpers de rol
    # (es_coordinador_calle es alias de es_coordinador_datacalle): sin esto el
    # fixture arma un coordinador que el modulo ya no reconoce como tal.
    user.profile.datacalle_rol = "coordinador"
    user.profile.save()
    user.profile.territorial_scopes.create(provincia=provincia)
    return user


def _entrevistador(provincia, username="entrev_dc"):
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.profile.es_relevador_calle = True
    user.profile.datacalle_rol = "entrevistador"
    user.profile.save()
    user.profile.relevador_calle_provincias.create(provincia=provincia)
    return user


def _visibles(actor, rf):
    request = rf.get("/usuarios/")
    request.user = actor
    return sorted(u.username for u in UsuariosService.get_usuarios_en_alcance(request))


@pytest.mark.django_db
def test_qa_0018_el_coordinador_ve_a_sus_entrevistadores(rf, provincia):
    """QA-0018: el usuario recién creado tiene que aparecer en el listado."""
    coordinador = _coordinador_datacalle(provincia)
    entrevistador = _entrevistador(provincia)

    visibles = _visibles(coordinador, rf)

    assert entrevistador.username in visibles
    assert coordinador.username in visibles


@pytest.mark.django_db
def test_qa_0018_no_ve_entrevistadores_de_otra_provincia(rf, provincia):
    """El alcance nuevo es aditivo pero sigue siendo provincial."""
    otra = Provincia.objects.create(nombre="Salta")
    coordinador = _coordinador_datacalle(provincia)
    ajeno = _entrevistador(otra, "entrev_ajeno")

    assert ajeno.username not in _visibles(coordinador, rf)


@pytest.mark.django_db
def test_qa_0018_no_ve_usuarios_sin_rol_datacalle(rf, provincia):
    """La regla no abre la puerta a todos los usuarios sin grupo."""
    coordinador = _coordinador_datacalle(provincia)
    comun = get_user_model().objects.create_user(
        username="usuario_comun", email="c@example.com", password="Sisoc12345!"
    )

    assert comun.username not in _visibles(coordinador, rf)


@pytest.mark.django_db
def test_el_alcance_de_los_demas_roles_no_cambia(rf, provincia):
    """Un actor sin permisos de DataCalle sigue con el deny-by-default."""
    otro = get_user_model().objects.create_user(
        username="otro_rol", email="o@example.com", password="Sisoc12345!"
    )
    _entrevistador(provincia, "entrev_invisible")

    assert _visibles(otro, rf) == ["otro_rol"]


@pytest.mark.django_db
def test_qa_0014_el_coordinador_ve_un_menu_acotado(client, provincia):
    """El menú muestra Situación de Calle y esconde el resto del backoffice."""
    coordinador = _coordinador_datacalle(provincia, "coord_menu")
    client.force_login(coordinador)

    respuesta = client.get("/inicio/")

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Situación de Calle" in html
    assert "Relevamientos DataCalle" in html
    # Módulos ajenos al operativo: no tienen por qué aparecerle.
    assert "Comunicados" not in html
    assert "Configuración de Comedores" not in html
    # Usuarios sí: el coordinador da de alta a sus entrevistadores (QA-0016).
    assert "usuarios" in html.lower()


@pytest.mark.django_db
def test_qa_0014_un_usuario_del_backoffice_conserva_su_menu(client, provincia):
    """La regla sólo aplica al coordinador puro de DataCalle."""
    from django.contrib.auth.models import Permission

    usuario = _coordinador_datacalle(provincia, "coord_mixto")
    # Además gestiona comedores: es un usuario del backoffice, no sólo DataCalle.
    usuario.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="comedores", codename="view_comedor"
        )
    )
    client.force_login(usuario)

    respuesta = client.get("/inicio/")

    assert respuesta.status_code == 200
    assert "Comunicados" in respuesta.content.decode()


def _dar_permisos_usuarios(user, codenames):
    """Permisos del backoffice de usuarios (app ``auth``)."""
    from django.contrib.auth.models import Permission

    user.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="auth", codename__in=codenames
        )
    )
    return user


@pytest.mark.django_db
def test_el_alcance_datacalle_no_alcanza_a_un_superusuario(rf, provincia):
    """Un superusuario marcado como relevador no queda administrable.

    El queryset de alcance gatea edición y baja, y el formulario de usuario
    permite fijar contraseña: sin esta exclusión, alcanzaría con tener el flag
    para poder tomarle la cuenta a un superusuario.
    """
    coordinador = _coordinador_datacalle(provincia)
    superusuario = get_user_model().objects.create_superuser(
        username="super_relevador", email="s@example.com", password="Sisoc12345!"
    )
    superusuario.profile.es_relevador_calle = True
    superusuario.profile.save()
    superusuario.profile.relevador_calle_provincias.create(provincia=provincia)

    assert superusuario.username not in _visibles(coordinador, rf)


@pytest.mark.django_db
def test_el_alcance_datacalle_no_alcanza_a_un_usuario_del_backoffice(rf, provincia):
    """Marcar el flag degrada a no-staff, así que un staff con el flag es anómalo.

    Puede pasar por carga directa o por un import: no puede volverse editable
    por un coordinador provincial sólo por estar marcado en su provincia.
    """
    coordinador = _coordinador_datacalle(provincia)
    del_backoffice = get_user_model().objects.create_user(
        username="staff_relevador",
        email="st@example.com",
        password="Sisoc12345!",
        is_staff=True,
    )
    del_backoffice.profile.es_relevador_calle = True
    del_backoffice.profile.save()
    del_backoffice.profile.relevador_calle_provincias.create(provincia=provincia)

    assert del_backoffice.username not in _visibles(coordinador, rf)


@pytest.mark.django_db
def test_no_se_puede_editar_por_url_a_un_objetivo_privilegiado(client, provincia):
    """La guarda anti-IDOR de UserUpdateView tiene que cerrarse, no sólo el listado."""
    coordinador = _dar_permisos_usuarios(
        _coordinador_datacalle(provincia, "coord_idor"),
        ["view_user", "change_user"],
    )
    superusuario = get_user_model().objects.create_superuser(
        username="super_idor", email="si@example.com", password="Sisoc12345!"
    )
    superusuario.profile.es_relevador_calle = True
    superusuario.profile.save()
    superusuario.profile.relevador_calle_provincias.create(provincia=provincia)
    client.force_login(coordinador)

    respuesta = client.get(f"/usuarios/editar/{superusuario.pk}/")

    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_el_entrevistador_legitimo_sigue_siendo_editable(client, provincia):
    """La corrección no puede romper QA-0018: el caso real tiene que seguir andando."""
    coordinador = _dar_permisos_usuarios(
        _coordinador_datacalle(provincia, "coord_ok"),
        ["view_user", "change_user"],
    )
    entrevistador = _entrevistador(provincia, "entrev_ok")
    client.force_login(coordinador)

    respuesta = client.get(f"/usuarios/editar/{entrevistador.pk}/")

    assert respuesta.status_code == 200


def _datos_edicion(user, **extra):
    """Payload mínimo del formulario de edición (ver test_users_auth_flows)."""
    datos = {
        "username": user.username,
        "tipo_usuario": "interno",
        "email": "",
        "password": "",
    }
    datos.update(extra)
    return datos


@pytest.mark.django_db
def test_el_coordinador_puede_habilitar_a_un_usuario_existente(provincia):
    """QA-0016 en el camino de edición, no sólo en el alta.

    Con el campo de provincias fijo al alcance del actor, el initial no puede
    salir del perfil: para un usuario que todavía no es relevador sería vacío,
    y clean exige al menos una provincia sobre un campo deshabilitado.
    """
    from users.forms import CustomUserChangeForm

    coordinador = _coordinador_datacalle(provincia, "coord_habilita")
    existente = get_user_model().objects.create_user(
        username="ya_existia", email="y@example.com", password="Sisoc12345!"
    )

    form = CustomUserChangeForm(
        instance=existente,
        actor=coordinador,
        data=_datos_edicion(
            existente,
            es_relevador_calle="on",
            datacalle_rol="entrevistador",
        ),
    )

    assert form.is_valid(), form.errors
    form.save()
    existente.profile.refresh_from_db()
    assert existente.profile.es_relevador_calle is True
    assert list(
        existente.profile.relevador_calle_provincias.values_list(
            "provincia__nombre", flat=True
        )
    ) == [provincia.nombre]


@pytest.mark.django_db
def test_editar_no_le_borra_la_provincia_al_relevador(provincia):
    """El campo fijo no puede convertirse en una baja silenciosa.

    Antes probaba que la edición no le borrara a un relevador una provincia
    fuera del alcance del actor, escenario que asumía que un relevador podía
    tener varias provincias a la vez. RN01 lo prohíbe (una sola por usuario),
    así que lo que queda por proteger es más chico pero sigue siendo real:
    que editar a un relevador de la propia provincia no le pierda esa única
    provincia en el camino.
    """
    from users.forms import CustomUserChangeForm

    coordinador = _coordinador_datacalle(provincia, "coord_preserva")
    entrevistador = _entrevistador(provincia, "entrev_preserva")

    form = CustomUserChangeForm(
        instance=entrevistador,
        actor=coordinador,
        data=_datos_edicion(
            entrevistador,
            first_name="Nombre Editado",
            es_relevador_calle="on",
            datacalle_rol="entrevistador",
        ),
    )

    assert form.is_valid(), form.errors
    form.save()
    entrevistador.profile.refresh_from_db()
    assert list(
        entrevistador.profile.relevador_calle_provincias.values_list(
            "provincia__nombre", flat=True
        )
    ) == [provincia.nombre]


@pytest.mark.django_db
def test_qa_0015_el_alta_explica_donde_se_define_cada_rol():
    """QA-0015: los tres roles no se eligen en el mismo lugar.

    El entrevistador sale del flag (usuario sólo de la app); el coordinador y
    el administrador salen del grupo y del alcance territorial. La pantalla
    tiene que decirlo, que era lo que QA no podía deducir.
    """
    from users.forms import UserCreationForm

    form = UserCreationForm()

    ayuda_flag = form.fields["es_relevador_calle"].help_text
    ayuda_rol = form.fields["datacalle_rol"].help_text

    assert "entrevistador" in ayuda_flag.lower()
    assert "Coordinador DataCalle" in ayuda_flag
    assert "coordinador" in ayuda_rol.lower()
    assert "administrador" in ayuda_rol.lower()
    # Los tres roles del documento funcional del 2026-09-18. La ayuda explica
    # dónde se define cada uno, que es lo que QA-0015 no podía deducir.
    assert [c[0] for c in form.fields["datacalle_rol"].choices] == [
        "",
        "administrador",
        "coordinador",
        "entrevistador",
    ]
