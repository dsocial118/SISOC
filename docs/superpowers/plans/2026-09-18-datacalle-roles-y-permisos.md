# DataCalle: roles y permisos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar los tres roles de DataCalle (Administrador Nacional > Coordinador Provincial > Relevador) con provincia única, acceso a la app para los tres, y la jerarquía aplicada en el servidor.

**Architecture:** `Profile.datacalle_rol` pasa a ser la única fuente de verdad del rol y gana dos valores. `Profile.es_relevador_calle` se conserva pero cambia de semántica: deja de significar "usuario sólo-app" y pasa a significar "accede a DataCalle". Todos los lectores dejan de mirar el flag para decidir qué puede hacer alguien y pasan por helpers de rol nuevos. Los permisos del backoffice siguen siendo grupos Django.

**Tech Stack:** Django 5.2, DRF, pytest + pytest-django, MySQL 8.4 (SQLite in-memory en tests), django-auditlog.

**Spec:** `docs/registro/decisiones/2026-09-18-datacalle-roles-y-permisos.md`

## Global Constraints

- Rama de trabajo: `fix/datacalle-qa-2026-09`. Todo va al mismo PR que el segundo bloque QA.
- Códigos de rol exactos: `"administrador"`, `"coordinador"`, `"entrevistador"`. Etiquetas exactas: `"Administrador Nacional"`, `"Coordinador Provincial"`, `"Relevador"`.
- Nombre exacto del grupo nuevo: `"Administrador DataCalle"`. El existente es `"Coordinador DataCalle"`.
- Tests: `docker compose exec -T django pytest <ruta> -v`. Formateo: `docker compose exec -T django black <archivos> -q`. Lint: `docker compose exec -T django pylint <app>/`.
- La lógica va en `<app>/services/` o en los servicios de `users/`; las views no llevan lógica (CLAUDE.md).
- Toda restricción se valida en servidor, nunca sólo ocultando UI (RN08).
- Cada commit termina con: `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`
- No se implementa reapertura de operativos (8.3 del documento funcional quedó "a definir").

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `users/models.py` | `DataCalleRol` con tres valores; constraint de provincia única | Modificar |
| `users/migrations/0053_datacalle_tres_roles.py` | Choices nuevos + migración de datos de coordinadores existentes | Crear |
| `users/migrations/0054_relevador_calle_provincia_unica.py` | Constraint `unique(profile)` con chequeo previo | Crear |
| `users/services_datacalle.py` | Helpers de rol y de provincia — única puerta de entrada al rol | Modificar |
| `users/bootstrap/groups_seed.py` | Grupo `Administrador DataCalle` | Modificar |
| `users/forms.py` | `is_staff` por rol; selector de rol acotado al actor; jerarquía RN02/RN03 | Modificar |
| `datacalle/api_permissions.py` | `TieneAccesoDataCalle` | Modificar |
| `datacalle/api_views.py` | `mis_relevamientos` jerárquico; guardia de cierre por rol | Modificar |
| `users/api_views.py` | Gate del login mobile por acceso, no por flag | Modificar |
| `datacalle/apps.py` | Registro de auditlog | Modificar |
| `tests/test_datacalle_roles.py` | Tests de los helpers y de la jerarquía | Crear |
| `tests/test_datacalle_api.py` | Tests de la API por rol | Modificar |
| `tests/test_datacalle_qa_usuarios.py` | Tests del alta de usuarios por rol | Modificar |

---

### Task 1: Los tres roles en el modelo, con migración de datos

**Files:**
- Modify: `users/models.py:98-106` (`class DataCalleRol`)
- Create: `users/migrations/0053_datacalle_tres_roles.py`
- Test: `tests/test_datacalle_roles.py`

**Interfaces:**
- Consumes: nada (primera tarea).
- Produces: `Profile.DataCalleRol.ADMINISTRADOR == "administrador"`, `.COORDINADOR == "coordinador"`, `.ENTREVISTADOR == "entrevistador"`.

- [ ] **Step 1: Write the failing test**

Crear `tests/test_datacalle_roles.py`:

```python
"""Tests de los tres roles de DataCalle (decisión 2026-09-18)."""

import pytest
from django.contrib.auth import get_user_model

from core.models import Provincia
from users.models import Profile


@pytest.fixture
def provincia(db):
    return Provincia.objects.create(nombre="Córdoba")


def test_existen_los_tres_roles_del_documento_funcional():
    codigos = [codigo for codigo, _ in Profile.DataCalleRol.choices]
    assert codigos == ["administrador", "coordinador", "entrevistador"]


def test_las_etiquetas_son_las_del_documento_funcional():
    etiquetas = dict(Profile.DataCalleRol.choices)
    assert etiquetas["administrador"] == "Administrador Nacional"
    assert etiquetas["coordinador"] == "Coordinador Provincial"
    assert etiquetas["entrevistador"] == "Relevador"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: FAIL — `codigos == ["entrevistador"]`, no los tres.

- [ ] **Step 3: Write minimal implementation**

En `users/models.py`, reemplazar la clase `DataCalleRol` completa:

```python
    class DataCalleRol(models.TextChoices):
        """Roles del relevamiento de situacion de calle (SISOC - Mobile DataCalle).

        Jerarquia decreciente: administrador > coordinador > entrevistador.
        Cada rol superior puede lo del inferior. Definidos en el documento
        funcional del area del 2026-09-18; ver
        docs/registro/decisiones/2026-09-18-datacalle-roles-y-permisos.md
        """

        ADMINISTRADOR = "administrador", "Administrador Nacional"
        COORDINADOR = "coordinador", "Coordinador Provincial"
        ENTREVISTADOR = "entrevistador", "Relevador"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Crear la migración de choices + datos**

Generar el esqueleto y después editarlo:

Run: `docker compose exec -T django python manage.py makemigrations users --name datacalle_tres_roles`

Abrir el archivo generado (`users/migrations/0053_datacalle_tres_roles.py`) y agregar la migración de datos **después** del `AlterField` que generó Django. El archivo queda así (conservar el `AlterField` tal como lo generó Django, sólo agregar el import, las dos funciones y el `RunPython`):

```python
from django.db import migrations, models


def asignar_rol_a_coordinadores_existentes(apps, schema_editor):
    """Los coordinadores que ya existen tienen el grupo pero no el rol.

    Sin esto, el dia del despliegue quedan fuera de la app y del gate nuevo.
    Coordinador si tiene alcance provincial; administrador si no tiene ninguno
    (que es como se venia representando al nacional).
    """
    Group = apps.get_model("auth", "Group")
    Profile = apps.get_model("users", "Profile")

    grupo = Group.objects.filter(name="Coordinador DataCalle").first()
    if grupo is None:
        return

    perfiles = Profile.objects.filter(user__groups=grupo).distinct()
    for perfil in perfiles:
        if perfil.datacalle_rol:
            continue
        tiene_alcance = perfil.territorial_scopes.filter(
            municipio__isnull=True
        ).exists()
        perfil.datacalle_rol = "coordinador" if tiene_alcance else "administrador"
        perfil.es_relevador_calle = True
        perfil.save(update_fields=["datacalle_rol", "es_relevador_calle"])


def revertir_rol_de_coordinadores(apps, schema_editor):
    """Reversa: limpia solo a los que esta migracion pudo haber tocado."""
    Group = apps.get_model("auth", "Group")
    Profile = apps.get_model("users", "Profile")

    grupo = Group.objects.filter(name="Coordinador DataCalle").first()
    if grupo is None:
        return

    Profile.objects.filter(
        user__groups=grupo,
        datacalle_rol__in=["coordinador", "administrador"],
    ).update(datacalle_rol="", es_relevador_calle=False)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0052_bootstrap_reportes_cdi_permission"),
    ]

    operations = [
        # <-- el AlterField que genero Django queda aca, sin tocar
        migrations.RunPython(
            asignar_rol_a_coordinadores_existentes,
            revertir_rol_de_coordinadores,
        ),
    ]
```

- [ ] **Step 6: Verificar que la migración corre y es reversible**

Run: `docker compose exec -T django python manage.py migrate users`
Expected: aplica `0053` sin error.

Run: `docker compose exec -T django python manage.py migrate users 0052`
Expected: revierte sin error.

Run: `docker compose exec -T django python manage.py migrate users`
Expected: vuelve a aplicar sin error.

- [ ] **Step 7: Verificar el efecto sobre los datos locales**

Run:

```bash
docker compose exec -T django python manage.py shell -c "
from users.models import Profile
print('coordinadores:', Profile.objects.filter(datacalle_rol='coordinador').count())
print('administradores:', Profile.objects.filter(datacalle_rol='administrador').count())
print('entrevistadores:', Profile.objects.filter(datacalle_rol='entrevistador').count())
"
```

Expected: al menos 1 coordinador (`coord.cordoba` del seed) y 1 administrador (`coord.nacional`), y los 3 entrevistadores intactos.

- [ ] **Step 8: Commit**

```bash
docker compose exec -T django black users/ tests/test_datacalle_roles.py -q
git add users/models.py users/migrations/0053_datacalle_tres_roles.py tests/test_datacalle_roles.py
git commit -m "$(cat <<'MSG'
feat(datacalle): los tres roles del documento funcional

Administrador Nacional > Coordinador Provincial > Relevador, jerarquicos y
decrecientes. `datacalle_rol` pasa a ser la unica fuente de verdad del rol.

La migracion de datos le asigna rol a los coordinadores que ya existen: sin
eso, el dia del despliegue quedan fuera de la app y del gate nuevo.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 2: Helpers de rol, y el equipo deja de mirar el flag

**Files:**
- Modify: `users/services_datacalle.py` (archivo completo)
- Test: `tests/test_datacalle_roles.py`

**Interfaces:**
- Consumes: `Profile.DataCalleRol` (Task 1).
- Produces:
  - `get_datacalle_rol(user) -> str` (`""` si no tiene)
  - `tiene_acceso_datacalle(user) -> bool` (los tres roles)
  - `es_administrador_datacalle(user) -> bool`
  - `es_coordinador_datacalle(user) -> bool` (coordinador **o** administrador)
  - `es_solo_app(user) -> bool` (sólo entrevistador)
  - `get_datacalle_provincia_ids(user) -> list[int] | None` (`None` = todo el país)

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_roles.py`:

```python
from users.models import RelevadorCalleProvincia
from users.services_datacalle import (
    es_administrador_datacalle,
    es_coordinador_datacalle,
    es_solo_app,
    get_datacalle_provincia_ids,
    get_datacalle_rol,
    get_relevador_calle_users_for_provincia,
    tiene_acceso_datacalle,
)


def _usuario(username, rol, provincia=None, staff=False):
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.is_staff = staff
    user.save()
    perfil = user.profile
    perfil.datacalle_rol = rol
    perfil.es_relevador_calle = bool(rol)
    if rol == "coordinador" and provincia is not None:
        perfil.es_usuario_provincial = True
    perfil.save()
    if provincia is not None:
        if rol == "entrevistador":
            RelevadorCalleProvincia.objects.create(profile=perfil, provincia=provincia)
        else:
            perfil.territorial_scopes.create(provincia=provincia)
    return user


@pytest.mark.django_db
def test_la_jerarquia_es_decreciente(provincia):
    admin = _usuario("admin_dc", "administrador", staff=True)
    coord = _usuario("coord_dc", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_dc", "entrevistador", provincia)

    # Los tres acceden a la app.
    assert [tiene_acceso_datacalle(u) for u in (admin, coord, relevador)] == [
        True,
        True,
        True,
    ]
    # Coordinador incluye al administrador: el superior puede lo del inferior.
    assert es_coordinador_datacalle(admin) is True
    assert es_coordinador_datacalle(coord) is True
    assert es_coordinador_datacalle(relevador) is False
    # Administrador es solo el administrador.
    assert es_administrador_datacalle(admin) is True
    assert es_administrador_datacalle(coord) is False
    # Solo-app es solo el relevador: es quien no entra a SISOC.
    assert [es_solo_app(u) for u in (admin, coord, relevador)] == [False, False, True]


@pytest.mark.django_db
def test_el_administrador_no_tiene_restriccion_territorial(provincia):
    admin = _usuario("admin_terr", "administrador", staff=True)
    coord = _usuario("coord_terr", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_terr", "entrevistador", provincia)

    assert get_datacalle_provincia_ids(admin) is None
    assert get_datacalle_provincia_ids(coord) == [provincia.id]
    assert get_datacalle_provincia_ids(relevador) == [provincia.id]


@pytest.mark.django_db
def test_un_usuario_sin_rol_no_accede(provincia):
    ajeno = get_user_model().objects.create_user(
        username="ajeno", email="ajeno@example.com", password="Sisoc12345!"
    )

    assert get_datacalle_rol(ajeno) == ""
    assert tiene_acceso_datacalle(ajeno) is False
    assert es_coordinador_datacalle(ajeno) is False
    assert get_datacalle_provincia_ids(ajeno) == []


@pytest.mark.django_db
def test_el_equipo_del_operativo_solo_ofrece_relevadores(provincia):
    """El coordinador tambien lleva el flag ahora: no puede colarse al equipo."""
    relevador = _usuario("relev_equipo", "entrevistador", provincia)
    _usuario("coord_equipo", "coordinador", provincia, staff=True)

    disponibles = get_relevador_calle_users_for_provincia(provincia.id)

    assert [u.username for u in disponibles] == [relevador.username]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: FAIL con `ImportError: cannot import name 'es_administrador_datacalle'`.

- [ ] **Step 3: Write minimal implementation**

En `users/services_datacalle.py`, reemplazar el docstring del módulo y agregar los helpers nuevos después de los imports:

```python
"""Servicios de los roles de DataCalle (SISOC - Mobile).

El rol vive en ``Profile.datacalle_rol`` y es la unica fuente de verdad:
administrador > coordinador > entrevistador, jerarquico y decreciente.

``Profile.es_relevador_calle`` se conserva por contrato con la app (D1.2 lo
expone en ``/api/users/me/``) pero **ya no decide nada**: significa "accede a
DataCalle" y lo tienen los tres roles. Quien necesite saber *que puede hacer*
un usuario, pregunta por el rol.
"""
```

Y agregar estas funciones (dejando las existentes en su lugar):

```python
def get_datacalle_rol(user) -> str:
    """Rol DataCalle del usuario, o ``""`` si no tiene ninguno."""
    if not user or not getattr(user, "is_authenticated", False):
        return ""
    profile = get_profile_or_none(user)
    return getattr(profile, "datacalle_rol", "") or ""


def tiene_acceso_datacalle(user) -> bool:
    """Si el usuario entra a la app. Los tres roles entran (matriz, punto 5)."""
    return get_datacalle_rol(user) in {
        "administrador",
        "coordinador",
        "entrevistador",
    }


def es_administrador_datacalle(user) -> bool:
    """Administrador Nacional: sin restriccion territorial."""
    return get_datacalle_rol(user) == "administrador"


def es_coordinador_datacalle(user) -> bool:
    """Gestiona operativos: coordinador provincial **o** administrador.

    La jerarquia es decreciente, asi que el superior incluye al inferior.
    """
    return get_datacalle_rol(user) in {"administrador", "coordinador"}


def es_solo_app(user) -> bool:
    """Relevador: no entra a SISOC (RN05)."""
    return get_datacalle_rol(user) == "entrevistador"


def get_datacalle_provincia_ids(user):
    """Provincias sobre las que opera, o ``None`` si son todas.

    ``None`` es "sin restriccion territorial" y solo lo devuelve el
    administrador; la lista vacia es "no puede operar en ninguna".
    """
    rol = get_datacalle_rol(user)
    if not rol:
        return []
    if rol == "administrador":
        return None
    if rol == "entrevistador":
        profile = get_profile_or_none(user)
        if not profile:
            return []
        return list(
            profile.relevador_calle_provincias.values_list("provincia_id", flat=True)
        )
    return get_full_province_scope_ids(user)
```

Reemplazar `es_coordinador_calle` por un alias, y arreglar los dos lectores que hoy miran el flag:

```python
def es_coordinador_calle(user) -> bool:
    """Alias historico de ``es_coordinador_datacalle``.

    Se conserva mientras queden llamadores; no agregar usos nuevos.
    """
    return es_coordinador_datacalle(user)
```

En `get_relevador_calle_users_for_provincia`, cambiar el filtro (el coordinador ahora también lleva el flag, así que sin esto se colaría al equipo):

```python
    return (
        User.objects.filter(
            is_active=True,
            profile__datacalle_rol="entrevistador",
            profile__relevador_calle_provincias__provincia_id=provincia_id,
        )
        .select_related("profile")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )
```

En `get_relevadores_administrables`, mismo criterio:

```python
    return User.objects.filter(
        profile__datacalle_rol="entrevistador",
        profile__relevador_calle_provincias__provincia_id__in=provincia_ids,
        is_staff=False,
        is_superuser=False,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Verificar que no rompe lo anterior**

Run: `docker compose exec -T django pytest tests/test_datacalle_qa_usuarios.py tests/test_datacalle_relevamientos.py -q`
Expected: PASS. Si falla algo de `get_relevadores_administrables`, es porque el fixture de test crea el entrevistador sin `datacalle_rol`: agregarle `perfil.datacalle_rol = "entrevistador"`.

- [ ] **Step 6: Commit**

```bash
docker compose exec -T django black users/ tests/test_datacalle_roles.py -q
git add users/services_datacalle.py tests/test_datacalle_roles.py tests/
git commit -m "$(cat <<'MSG'
feat(datacalle): helpers de rol como unica puerta de entrada

El flag `es_relevador_calle` deja de decidir que puede hacer un usuario y pasa
a significar solo "accede a DataCalle". Quien necesite saber que puede hacer,
pregunta por el rol.

Dos lectores se corrigen en la misma pasada: el equipo del operativo y los
relevadores administrables filtraban por el flag, y como ahora el coordinador
tambien lo lleva, se habrian colado en las dos listas.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 3: `is_staff` sale del rol, no del flag

**Files:**
- Modify: `users/forms.py:1265-1267` (`UserCreationForm._configure_created_user`)
- Modify: `users/forms.py:1527-1528` (`CustomUserChangeForm.save`)
- Test: `tests/test_datacalle_roles.py`

**Interfaces:**
- Consumes: `es_solo_app` (Task 2).
- Produces: nada nuevo; corrige comportamiento.

**Por qué es tarea propia:** hoy marcar `es_relevador_calle` fuerza `is_staff = False`. Con la semántica nueva, los tres roles llevan el flag, así que un coordinador creado desde el formulario quedaría **sin acceso al backoffice**. Es el bug más peligroso de la migración de semántica y merece su propio gate de revisión.

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_roles.py`:

```python
from users.forms import UserCreationForm


@pytest.mark.django_db
def test_el_coordinador_creado_conserva_el_acceso_al_backoffice(provincia):
    """El flag ya no degrada a no-staff: eso vale solo para el relevador."""
    from users.services_datacalle import es_solo_app

    coord = _usuario("coord_staff", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_staff", "entrevistador", provincia)

    assert es_solo_app(coord) is False
    assert es_solo_app(relevador) is True
    # El coordinador es de backoffice; el relevador no.
    assert coord.is_staff is True
    assert relevador.is_staff is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py::test_el_coordinador_creado_conserva_el_acceso_al_backoffice -v`
Expected: PASS (el helper ya existe de Task 2). **Este test es de regresión, no de implementación**: documenta la invariante. El cambio real de esta tarea es en el formulario y se verifica en el Step 5.

- [ ] **Step 3: Write minimal implementation**

En `users/forms.py`, dentro de `_configure_created_user`, reemplazar:

```python
        if self.cleaned_data.get("es_relevador_calle", False):
            user.is_staff = False
            return
```

por:

```python
        # Solo el relevador es usuario sin backoffice (RN05). El coordinador y
        # el administrador tambien llevan `es_relevador_calle` —les habilita la
        # app— pero entran a SISOC.
        if self.cleaned_data.get("datacalle_rol") == "entrevistador":
            user.is_staff = False
            return
```

Y dentro de `CustomUserChangeForm.save`, reemplazar:

```python
        elif self.cleaned_data.get("es_relevador_calle", False):
            user.is_staff = False
```

por:

```python
        elif self.cleaned_data.get("datacalle_rol") == "entrevistador":
            user.is_staff = False
```

- [ ] **Step 4: Verificar el alta real de un coordinador por formulario**

Run:

```bash
docker compose exec -T django pytest tests/test_datacalle_qa_usuarios.py -q
```

Expected: PASS.

- [ ] **Step 5: Verificar a mano que el alta no degrada al coordinador**

Run:

```bash
docker compose exec -T django python manage.py shell -c "
from users.forms import UserCreationForm
campos = UserCreationForm().fields
print('datacalle_rol en el form:', 'datacalle_rol' in campos)
print('opciones:', [c[0] for c in campos['datacalle_rol'].choices])
"
```

Expected: `True` y `['', 'administrador', 'coordinador', 'entrevistador']`.

- [ ] **Step 6: Commit**

```bash
docker compose exec -T django black users/forms.py tests/test_datacalle_roles.py -q
git add users/forms.py tests/test_datacalle_roles.py
git commit -m "$(cat <<'MSG'
fix(datacalle): is_staff sale del rol, no del flag

Marcar `es_relevador_calle` forzaba is_staff=False en los dos caminos de
guardado. Con la semantica nueva los tres roles llevan el flag, asi que un
coordinador creado desde el formulario quedaba sin acceso al backoffice.
Ahora solo degrada al rol entrevistador, que es el unico sin SISOC (RN05).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 4: Grupo "Administrador DataCalle" en la semilla

**Files:**
- Modify: `users/bootstrap/groups_seed.py:1124-1144` (después del bloque `Coordinador DataCalle`)
- Test: `tests/test_datacalle_roles.py`

**Interfaces:**
- Consumes: nada.
- Produces: grupo `"Administrador DataCalle"` disponible para `create_groups`.

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_roles.py`:

```python
def test_la_semilla_define_el_grupo_de_administrador():
    from users.bootstrap.groups_seed import BOOTSTRAP_GROUPS

    por_nombre = {seed.name: seed for seed in BOOTSTRAP_GROUPS}

    assert "Administrador DataCalle" in por_nombre
    admin = set(por_nombre["Administrador DataCalle"].permissions)
    coord = set(por_nombre["Coordinador DataCalle"].permissions)
    # La jerarquia es decreciente: el administrador puede todo lo del coordinador.
    assert coord <= admin
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py::test_la_semilla_define_el_grupo_de_administrador -v`
Expected: FAIL — `"Administrador DataCalle" not in por_nombre`.

- [ ] **Step 3: Write minimal implementation**

En `users/bootstrap/groups_seed.py`, inmediatamente después del bloque `BootstrapGroupSeed("Coordinador DataCalle", (...))`, agregar:

```python
    BootstrapGroupSeed(
        "Administrador DataCalle",
        (
            # Administrador Nacional: lo mismo que el coordinador provincial,
            # pero sin restriccion territorial. El alcance nacional no sale de
            # los permisos sino de no tener `territorial_scopes` (ver
            # docs/registro/decisiones/2026-09-18-datacalle-roles-y-permisos.md).
            "datacalle.view_relevamiento",
            "datacalle.add_relevamiento",
            "datacalle.change_relevamiento",
            "datacalle.delete_relevamiento",
            "datacalle.view_encuesta",
            "datacalle.add_encuesta",
            "datacalle.change_encuesta",
            "datacalle.delete_encuesta",
            # Da de alta coordinadores y relevadores de cualquier provincia.
            "auth.view_user",
            "auth.add_user",
            "auth.change_user",
        ),
    ),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: PASS

- [ ] **Step 5: Verificar que el comando de grupos lo crea**

Run: `docker compose exec -T django python manage.py create_groups`
Run: `docker compose exec -T django python manage.py shell -c "
from django.contrib.auth.models import Group
g = Group.objects.filter(name='Administrador DataCalle').first()
print('existe:', g is not None, '| permisos:', g.permissions.count() if g else 0)
"`
Expected: `existe: True | permisos: 11`

- [ ] **Step 6: Commit**

```bash
docker compose exec -T django black users/ tests/test_datacalle_roles.py -q
git add users/bootstrap/groups_seed.py tests/test_datacalle_roles.py
git commit -m "$(cat <<'MSG'
feat(datacalle): grupo Administrador DataCalle en la semilla

Mismos permisos que el coordinador provincial: el alcance nacional no sale de
los permisos sino de no tener alcance territorial configurado.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 5: Provincia única (RN01)

**Files:**
- Modify: `users/models.py:401-410` (`RelevadorCalleProvincia.Meta.constraints`)
- Create: `users/migrations/0054_relevador_calle_provincia_unica.py`
- Modify: `users/forms.py` (`_clean_relevador_calle_fields`)
- Test: `tests/test_datacalle_roles.py`

**Interfaces:**
- Consumes: `Profile.DataCalleRol` (Task 1).
- Produces: invariante "un relevador tiene exactamente una provincia".

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_roles.py`:

```python
from django.db import IntegrityError, transaction


@pytest.mark.django_db
def test_un_relevador_no_puede_tener_dos_provincias(provincia):
    """RN01: provincia unica, garantizada por la base y no solo por el form."""
    salta = Provincia.objects.create(nombre="Salta")
    relevador = _usuario("relev_unica", "entrevistador", provincia)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RelevadorCalleProvincia.objects.create(
                profile=relevador.profile, provincia=salta
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py::test_un_relevador_no_puede_tener_dos_provincias -v`
Expected: FAIL — `DID NOT RAISE IntegrityError`.

- [ ] **Step 3: Write minimal implementation**

En `users/models.py`, en `RelevadorCalleProvincia.Meta`, reemplazar el bloque `constraints`:

```python
        constraints = [
            # RN01: provincia unica por usuario. La constraint anterior
            # (profile, provincia) solo evitaba duplicados de la misma fila y
            # permitia N provincias distintas.
            models.UniqueConstraint(
                fields=["profile"],
                name="uniq_relevador_calle_una_provincia",
            ),
        ]
```

- [ ] **Step 4: Crear la migración con chequeo previo**

Run: `docker compose exec -T django python manage.py makemigrations users --name relevador_calle_provincia_unica`

Editar el archivo generado para anteponer el chequeo (dejar las operaciones que generó Django **después** del `RunPython`):

```python
from django.db import migrations, models


def verificar_provincia_unica(apps, schema_editor):
    """Falla temprano y con mensaje si hay datos que la constraint rechazaria.

    Sin esto, la constraint explota a mitad del deploy con un error de base
    ilegible. En local hay cero; en produccion hay que resolverlos a mano.
    """
    from django.db.models import Count

    RelevadorCalleProvincia = apps.get_model("users", "RelevadorCalleProvincia")
    conflictivos = (
        RelevadorCalleProvincia.objects.values("profile_id")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
    )
    ids = [fila["profile_id"] for fila in conflictivos]
    if ids:
        raise RuntimeError(
            "RN01 exige una sola provincia por relevador de DataCalle. "
            f"Estos profile_id tienen mas de una: {ids}. "
            "Resolverlos antes de aplicar esta migracion."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0053_datacalle_tres_roles"),
    ]

    operations = [
        migrations.RunPython(verificar_provincia_unica, migrations.RunPython.noop),
        # <-- RemoveConstraint / AddConstraint que genero Django quedan aca
    ]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: PASS

- [ ] **Step 6: Validar también en el formulario**

En `users/forms.py`, dentro de `_clean_relevador_calle_fields`, reemplazar el bloque final:

```python
        if not provincias:
            self.add_error(
                "provincias_datacalle",
                "Seleccione al menos una provincia para el relevador de DataCalle.",
            )
        return cleaned
```

por:

```python
        # RN01: exactamente una. El mensaje dice el porque, no solo el limite.
        if not provincias:
            self.add_error(
                "provincias_datacalle",
                "Seleccione la provincia del usuario de DataCalle.",
            )
        elif len(provincias) > 1:
            self.add_error(
                "provincias_datacalle",
                "Un usuario de DataCalle pertenece a una sola provincia.",
            )
        return cleaned
```

- [ ] **Step 7: Verificar el chequeo previo de la migración**

Run: `docker compose exec -T django python manage.py migrate users 0052`
Run: `docker compose exec -T django python manage.py migrate users`
Expected: aplica sin error (la base local tiene cero conflictos).

- [ ] **Step 8: Commit**

```bash
docker compose exec -T django black users/ tests/test_datacalle_roles.py -q
git add users/models.py users/migrations/0054_relevador_calle_provincia_unica.py users/forms.py tests/test_datacalle_roles.py
git commit -m "$(cat <<'MSG'
feat(datacalle): provincia unica por usuario (RN01)

La constraint anterior era (profile, provincia): evitaba duplicados de la
misma fila pero permitia N provincias distintas. Ahora es unique(profile).

La migracion chequea antes y falla con un mensaje que nombra los perfiles en
conflicto, en vez de explotar a mitad del deploy con un error de base.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 6: Quién entra a SISOC y quién a la app (RN05)

**Files:**
- Modify: `users/forms.py:28` (import) y `:251-255` (`confirm_login_allowed`)
- Modify: `users/api_views.py:36` (import) y `:100-104` (gate del login mobile)
- Test: `tests/test_datacalle_roles.py`

**Interfaces:**
- Consumes: `es_solo_app`, `tiene_acceso_datacalle` (Task 2).
- Produces: nada nuevo.

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_roles.py`:

```python
@pytest.mark.django_db
def test_solo_el_relevador_queda_afuera_del_backoffice(client, provincia):
    """RN05: el relevador no entra a SISOC; coordinador y admin si."""
    _usuario("coord_login", "coordinador", provincia, staff=True)
    _usuario("relev_login", "entrevistador", provincia)

    entra = client.post(
        "/login/",
        {"username": "coord_login", "password": "Sisoc12345!"},
        follow=True,
    )
    rebota = client.post(
        "/login/",
        {"username": "relev_login", "password": "Sisoc12345!"},
        follow=True,
    )

    assert entra.context["user"].is_authenticated is True
    assert rebota.context["user"].is_authenticated is False
    assert "SISOC - Mobile DataCalle" in rebota.content.decode()


@pytest.mark.django_db
def test_los_tres_roles_obtienen_token_de_la_app(provincia):
    """Matriz punto 5: los tres acceden a DataCalle."""
    from rest_framework.test import APIClient

    _usuario("admin_token", "administrador", staff=True)
    _usuario("coord_token", "coordinador", provincia, staff=True)
    _usuario("relev_token", "entrevistador", provincia)

    for username in ("admin_token", "coord_token", "relev_token"):
        respuesta = APIClient().post(
            "/api/users/login/",
            {"username": username, "password": "Sisoc12345!"},
            format="json",
        )
        assert respuesta.status_code == 200, username
        assert respuesta.data["token"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -k "backoffice or token" -v`
Expected: FAIL — el coordinador rebota del backoffice y el admin/coordinador no obtienen token.

- [ ] **Step 3: Write minimal implementation**

En `users/forms.py`, cambiar el import de la línea 28:

```python
from users.services_datacalle import es_solo_app
```

y dentro de `confirm_login_allowed` reemplazar:

```python
        if is_relevador_calle_user(user):
            raise forms.ValidationError(
                "Este usuario solo puede ingresar desde SISOC - Mobile DataCalle.",
                code="datacalle_only",
            )
```

por:

```python
        # RN05: solo el relevador queda afuera. El coordinador y el
        # administrador usan la app y tambien el backoffice.
        if es_solo_app(user):
            raise forms.ValidationError(
                "Este usuario solo puede ingresar desde SISOC - Mobile DataCalle.",
                code="datacalle_only",
            )
```

En `users/api_views.py`, cambiar el import de la línea 36:

```python
from users.services_datacalle import tiene_acceso_datacalle
```

y en el gate del login reemplazar `and not is_relevador_calle_user(user)` por:

```python
            and not tiene_acceso_datacalle(user)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: PASS

- [ ] **Step 5: Verificar que no se rompió el login de comedores**

Run: `docker compose exec -T django pytest tests/ -q -k "login or pwa"`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
docker compose exec -T django black users/ tests/test_datacalle_roles.py -q
git add users/forms.py users/api_views.py tests/test_datacalle_roles.py
git commit -m "$(cat <<'MSG'
feat(datacalle): el acceso sale del rol y no del flag (RN05)

Solo el relevador queda afuera del backoffice. El coordinador y el
administrador entran a SISOC y ademas obtienen token de la app, que es lo que
pide la matriz de permisos del documento funcional.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 7: La app sirve a los tres roles

**Files:**
- Modify: `datacalle/api_permissions.py` (archivo completo)
- Modify: `datacalle/api_views.py:35` (import), `:55-57` (`mis_relevamientos`), `:108` (guardia de cierre)
- Test: `tests/test_datacalle_api.py`

**Interfaces:**
- Consumes: `tiene_acceso_datacalle`, `es_coordinador_datacalle`, `get_datacalle_provincia_ids` (Task 2).
- Produces: `TieneAccesoDataCalle` (permiso DRF).

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_api.py`:

```python
def _con_rol(provincia, username, rol):
    """Usuario DataCalle con rol explicito, para los tests de jerarquia."""
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.profile.es_relevador_calle = True
    user.profile.datacalle_rol = rol
    if rol == "coordinador":
        user.profile.es_usuario_provincial = True
    user.profile.save()
    if rol == "entrevistador":
        RelevadorCalleProvincia.objects.create(profile=user.profile, provincia=provincia)
    elif rol == "coordinador":
        user.profile.territorial_scopes.create(provincia=provincia)
    return user


@pytest.mark.django_db
def test_el_coordinador_ve_los_operativos_de_su_provincia_sin_estar_en_el_equipo(
    provincia,
):
    entrevistador = _entrevistador(provincia, "entrev_jer")
    coordinador = _con_rol(provincia, "coord_jer", "coordinador")
    _relevamiento(provincia, equipo=[entrevistador], denominacion="De su provincia")

    respuesta = _cliente(coordinador).get("/api/datacalle/relevamientos/")

    assert respuesta.status_code == 200
    assert [r["denominacion"] for r in respuesta.data["results"]] == [
        "De su provincia"
    ]


@pytest.mark.django_db
def test_el_coordinador_no_ve_operativos_de_otra_provincia(provincia):
    salta = Provincia.objects.create(nombre="Salta")
    ajeno = _entrevistador(salta, "entrev_salta")
    coordinador = _con_rol(provincia, "coord_acotado", "coordinador")
    _relevamiento(salta, equipo=[ajeno], denominacion="De Salta")

    respuesta = _cliente(coordinador).get("/api/datacalle/relevamientos/")

    assert respuesta.data["results"] == []


@pytest.mark.django_db
def test_el_administrador_ve_todas_las_provincias(provincia):
    salta = Provincia.objects.create(nombre="Salta")
    _relevamiento(provincia, denominacion="De Cordoba")
    _relevamiento(salta, denominacion="De Salta")
    administrador = _con_rol(provincia, "admin_api", "administrador")

    respuesta = _cliente(administrador).get("/api/datacalle/relevamientos/")

    nombres = sorted(r["denominacion"] for r in respuesta.data["results"])
    assert nombres == ["De Cordoba", "De Salta"]


@pytest.mark.django_db
def test_el_coordinador_si_puede_cerrar_desde_la_app(provincia):
    """QA-0020 prohibe al relevador, no al coordinador."""
    coordinador = _con_rol(provincia, "coord_cierra", "coordinador")
    relevamiento = _relevamiento(provincia, denominacion="Para cerrar por app")

    respuesta = _cliente(coordinador).post(
        f"/api/datacalle/relevamientos/{relevamiento.id}/cerrar/", {}, format="json"
    )

    assert respuesta.status_code == 200
    relevamiento.refresh_from_db()
    assert relevamiento.estado == Relevamiento.Estado.FINALIZADO
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_api.py -k "jer or acotado or administrador_ve or coord_cierra or cerrar_desde_la_app" -v`
Expected: FAIL — el coordinador ve lista vacía (no está en `equipo`) y el cierre da 403.

- [ ] **Step 3: Write minimal implementation**

Reemplazar `datacalle/api_permissions.py` completo:

```python
from rest_framework.permissions import BasePermission

from users.services_datacalle import tiene_acceso_datacalle


class TieneAccesoDataCalle(BasePermission):
    """Los tres roles de DataCalle consumen la API de la app (D2.1).

    El relevador releva; el coordinador y el administrador ademas gestionan.
    Que puede hacer cada uno lo decide la vista, no este permiso.
    """

    message = "Este usuario no tiene habilitado DataCalle."

    def has_permission(self, request, view):
        return tiene_acceso_datacalle(request.user)


# Alias historico: se conserva mientras queden importadores.
EsRelevadorCalle = TieneAccesoDataCalle
```

En `datacalle/api_views.py`, cambiar el import de la línea 35:

```python
from users.services_datacalle import (
    es_coordinador_datacalle,
    get_datacalle_provincia_ids,
)
```

y el import del permiso:

```python
from datacalle.api_permissions import TieneAccesoDataCalle
```

Reemplazar `mis_relevamientos`:

```python
def mis_relevamientos(user):
    """Operativos que el usuario ve en la app, segun su rol (D2.2).

    La jerarquia es decreciente: el entrevistador ve los suyos, el coordinador
    todos los de su provincia —asi puede relevar sin estar en el equipo— y el
    administrador todos.
    """
    queryset = get_relevamientos_queryset()
    if not es_coordinador_datacalle(user):
        return queryset.filter(equipo=user).distinct()

    provincia_ids = get_datacalle_provincia_ids(user)
    if provincia_ids is None:
        return queryset.distinct()
    if not provincia_ids:
        return queryset.none()
    return queryset.filter(provincia_id__in=provincia_ids).distinct()
```

En las dos clases que lo declaran (`RelevamientoViewSet` y `EncuestaViewSet`), cambiar `permission_classes = [EsRelevadorCalle]` por `permission_classes = [TieneAccesoDataCalle]`.

En la acción `cerrar`, cambiar la guardia:

```python
        if not es_coordinador_datacalle(request.user):
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_api.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Verificar que el relevador sigue bloqueado**

Run: `docker compose exec -T django pytest tests/test_datacalle_api.py -k "qa_0020 or no_puedo_cargar" -v`
Expected: PASS — el entrevistador sigue recibiendo 403 al cerrar y 404 en operativos ajenos.

- [ ] **Step 6: Commit**

```bash
docker compose exec -T django black datacalle/ tests/test_datacalle_api.py -q
git add datacalle/api_permissions.py datacalle/api_views.py tests/test_datacalle_api.py
git commit -m "$(cat <<'MSG'
feat(datacalle): la app sirve a los tres roles, con alcance por rol

El entrevistador ve los operativos donde esta en el equipo; el coordinador
todos los de su provincia, asi puede relevar sin que lo agreguen; el
administrador todos. El cierre por API se habilita al coordinador y sigue
prohibido para el relevador (QA-0020).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 8: Jerarquía dura en el alta de usuarios (RN02, RN03)

**Files:**
- Modify: `users/forms.py` (`RelevadorCalleFormMixin._setup_relevador_calle_fields`, `_acotar_provincias_datacalle_al_actor`, `_clean_relevador_calle_fields`)
- Test: `tests/test_datacalle_qa_usuarios.py`

**Interfaces:**
- Consumes: `es_administrador_datacalle`, `get_datacalle_rol` (Task 2).
- Produces: nada nuevo.

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_qa_usuarios.py`:

```python
@pytest.mark.django_db
def test_rn02_el_coordinador_solo_puede_crear_relevadores(provincia):
    """RN02: crear coordinadores es exclusivo del Administrador Nacional."""
    from users.forms import UserCreationForm

    actor = _coordinador_datacalle(provincia, "coord_rn02")
    actor.profile.datacalle_rol = "coordinador"
    actor.profile.save()

    form = UserCreationForm(actor=actor)
    ofrecidos = [codigo for codigo, _ in form.fields["datacalle_rol"].choices if codigo]

    assert ofrecidos == ["entrevistador"]


@pytest.mark.django_db
def test_rn02_el_coordinador_no_puede_forzar_el_rol_por_post(provincia):
    """RN08: no alcanza con no mostrar la opcion; el servidor la rechaza."""
    from users.forms import UserCreationForm

    actor = _coordinador_datacalle(provincia, "coord_post")
    actor.profile.datacalle_rol = "coordinador"
    actor.profile.save()

    form = UserCreationForm(
        data={
            "username": "colado",
            "email": "colado@example.com",
            "password": "Sisoc12345!",
            "es_relevador_calle": True,
            "datacalle_rol": "coordinador",
            "provincias_datacalle": [provincia.id],
        },
        actor=actor,
    )

    assert form.is_valid() is False
    assert "datacalle_rol" in form.errors


@pytest.mark.django_db
def test_rn02_el_administrador_si_puede_crear_coordinadores(provincia):
    from users.forms import UserCreationForm

    actor = _coordinador_datacalle(provincia, "admin_rn02")
    actor.profile.datacalle_rol = "administrador"
    actor.profile.territorial_scopes.all().delete()
    actor.profile.save()

    form = UserCreationForm(actor=actor)
    ofrecidos = [codigo for codigo, _ in form.fields["datacalle_rol"].choices if codigo]

    assert ofrecidos == ["administrador", "coordinador", "entrevistador"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_qa_usuarios.py -k "rn02" -v`
Expected: FAIL — el coordinador ve los tres roles y el POST con `"coordinador"` pasa.

- [ ] **Step 3: Write minimal implementation**

En `users/forms.py`, dentro de `_setup_relevador_calle_fields`, reemplazar la construcción del campo `datacalle_rol` para que las opciones dependan del actor:

```python
        self.fields["datacalle_rol"] = forms.ChoiceField(
            choices=[("", "---------")] + self._roles_datacalle_para_el_actor(),
            required=False,
            widget=forms.Select(attrs={"class": "select2"}),
            label="Rol en DataCalle",
            help_text=(
                "Administrador Nacional (todo el pais), Coordinador Provincial "
                "(su provincia, entra al backoffice y a la app) o Relevador "
                "(solo la app). Crear coordinadores y elegir provincia es "
                "exclusivo del Administrador Nacional."
            ),
        )
```

Y agregar el método que decide las opciones, junto a los demás del mixin:

```python
    def _roles_datacalle_para_el_actor(self):
        """RN02: solo el Administrador Nacional crea roles superiores.

        Un coordinador da de alta relevadores de su provincia y nada mas.
        """
        actor = getattr(self, "actor", None)
        todos = list(Profile.DataCalleRol.choices)
        if actor is None or getattr(actor, "is_superuser", False):
            return todos
        if es_administrador_datacalle(actor):
            return todos
        return [
            (codigo, etiqueta)
            for codigo, etiqueta in todos
            if codigo == Profile.DataCalleRol.ENTREVISTADOR
        ]
```

En `_clean_relevador_calle_fields`, agregar la validación de servidor antes del `return cleaned` final:

```python
        # RN08: no alcanza con no ofrecer la opcion en el selector.
        rol = cleaned.get("datacalle_rol")
        permitidos = {codigo for codigo, _ in self._roles_datacalle_para_el_actor()}
        if rol and rol not in permitidos:
            self.add_error(
                "datacalle_rol",
                "No tenes permiso para asignar ese rol de DataCalle.",
            )
```

Agregar el import al principio de `users/forms.py`:

```python
from users.services_datacalle import es_administrador_datacalle, es_solo_app
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_qa_usuarios.py -v`
Expected: PASS

- [ ] **Step 5: Verificar que QA-0016 sigue andando**

Run: `docker compose exec -T django pytest tests/test_datacalle_qa_usuarios.py -k "qa_0016 or provincia" -v`
Expected: PASS — la provincia del coordinador se sigue heredando y quedando `disabled`.

- [ ] **Step 6: Commit**

```bash
docker compose exec -T django black users/forms.py tests/test_datacalle_qa_usuarios.py -q
git add users/forms.py tests/test_datacalle_qa_usuarios.py
git commit -m "$(cat <<'MSG'
feat(datacalle): solo el administrador crea roles superiores (RN02)

El coordinador provincial da de alta relevadores de su provincia y nada mas.
La restriccion no es solo de pantalla: el servidor rechaza el rol que llegue
por POST fuera del alcance del actor (RN08).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 9: Trazabilidad del operativo (8.6)

**Files:**
- Modify: `datacalle/apps.py`
- Test: `tests/test_datacalle_roles.py`

**Interfaces:**
- Consumes: nada.
- Produces: registros de auditoría de `Relevamiento` y `Encuesta`.

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datacalle_roles.py`:

```python
@pytest.mark.django_db
def test_las_modificaciones_del_operativo_quedan_registradas(provincia):
    """8.6: quien modifico que y cuando, mas alla de creado_por/cerrado_por."""
    import datetime

    from auditlog.models import LogEntry

    from datacalle.models import Relevamiento

    relevamiento = Relevamiento.objects.create(
        denominacion="Operativo auditado",
        provincia=provincia,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 20),
        fecha_fin=datetime.date(2026, 9, 21),
    )
    relevamiento.denominacion = "Operativo auditado y renombrado"
    relevamiento.save()

    entradas = LogEntry.objects.get_for_object(relevamiento)

    assert entradas.count() >= 2  # alta + modificacion
    assert "denominacion" in entradas.first().changes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py::test_las_modificaciones_del_operativo_quedan_registradas -v`
Expected: FAIL — `entradas.count() == 0`, el modelo no está registrado.

- [ ] **Step 3: Write minimal implementation**

En `datacalle/apps.py`, extender `ready`:

```python
    def ready(self):
        from auditlog.registry import (  # pylint: disable=import-outside-toplevel
            auditlog,
        )

        from datacalle.models import (  # pylint: disable=import-outside-toplevel
            Encuesta,
            Relevamiento,
        )
        from datacalle.sidebar_access import (  # pylint: disable=import-outside-toplevel
            registrar_acceso_sidebar,
        )

        # 8.6 del documento funcional: quien modifico el operativo y cuando.
        # `creado_por` y `cerrado_por` cubren las puntas; esto cubre el medio.
        auditlog.register(Relevamiento)
        auditlog.register(Encuesta)

        registrar_acceso_sidebar()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose exec -T django pytest tests/test_datacalle_roles.py -v`
Expected: PASS

- [ ] **Step 5: Verificar que no rompe la carga de casos por API**

Run: `docker compose exec -T django pytest tests/test_datacalle_api.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
docker compose exec -T django black datacalle/ tests/test_datacalle_roles.py -q
git add datacalle/apps.py tests/test_datacalle_roles.py
git commit -m "$(cat <<'MSG'
feat(datacalle): registrar en auditlog los cambios de operativos y casos

8.6 del documento funcional. `creado_por` y `cerrado_por` cubren las puntas
del ciclo; faltaba el medio: quien modifico que y cuando.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 10: Cierre — registro de cambios y verificación completa

**Files:**
- Modify: `docs/registro/decisiones/2026-09-18-datacalle-roles-y-permisos.md` (estado)
- Create: `docs/registro/cambios/2026-09-18-datacalle-roles-y-permisos.md`

- [ ] **Step 1: Correr la suite completa**

Run: `docker compose exec -T django pytest -n auto -q`
Expected: sólo las 2 fallas preexistentes del working tree Windows (`test_prod_infra_scripts`, `test_csv_export_architecture`). Cualquier otra falla se arregla antes de seguir.

- [ ] **Step 2: Lint**

Run: `docker compose exec -T django pylint datacalle/ users/services_datacalle.py`
Expected: 10.00/10

- [ ] **Step 3: Pasar la decisión a aceptada**

En `docs/registro/decisiones/2026-09-18-datacalle-roles-y-permisos.md`, cambiar el bloque `## Estado`:

```markdown
## Estado
- aceptada (implementada en `fix/datacalle-qa-2026-09`, 2026-09-18)
```

- [ ] **Step 4: Escribir el registro de cambios**

Crear `docs/registro/cambios/2026-09-18-datacalle-roles-y-permisos.md` con las secciones `## Alcance`, `## Comportamiento`, `## Decisiones` y `## Pendiente`, siguiendo el formato de `2026-09-17-datacalle-qa-segundo-bloque.md`. En `## Pendiente` dejar asentado: la reapertura de operativos (8.3) no se implementó, y la migración `0054` puede fallar en producción si hay relevadores con más de una provincia.

- [ ] **Step 5: Commit y push**

```bash
git add docs/registro/
git commit -m "$(cat <<'MSG'
docs(datacalle): registrar la implementacion de roles y permisos

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
git push origin fix/datacalle-qa-2026-09
```

- [ ] **Step 6: Avisar que el PR está listo para abrirse**

El PR cubre ahora el segundo bloque QA **más** los roles. No abrirlo sin confirmar con el usuario, que ya tiene el cuerpo redactado de la conversación anterior y hay que ampliarlo con los roles.

---

## Self-Review

**Cobertura del spec:**

| Decisión del spec | Tarea |
|---|---|
| D1 tres roles + migración de datos | 1 |
| D1 helpers de rol | 2 |
| D1 grupo `Administrador DataCalle` | 4 |
| D2 login backoffice y API | 6 |
| D2 permiso de la app + tareas jerárquicas + cierre | 7 |
| D3 provincia única (constraint + form) | 5 |
| D4 jerarquía dura en servidor | 8 |
| D5 trazabilidad | 9 |
| D6 fuera de alcance | documentado en Task 10 Step 4 |

**Descubierto al planificar, no estaba en el spec:** `is_staff` se fuerza desde el flag en dos lugares (Task 3) y los lectores del equipo y de administrables filtran por el flag (Task 2 Step 3). Sin esas dos, el coordinador quedaría sin backoffice y se colaría en las listas de relevadores.

**Consistencia de nombres verificada:** `tiene_acceso_datacalle`, `es_coordinador_datacalle`, `es_administrador_datacalle`, `es_solo_app`, `get_datacalle_rol`, `get_datacalle_provincia_ids` y `TieneAccesoDataCalle` se usan con la misma firma en las tareas 2, 3, 6, 7 y 8.
