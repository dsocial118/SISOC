from datetime import date, timedelta
from decimal import Decimal

import pytest
from django import forms
from django.contrib.auth.models import Permission, User
from django.test import Client
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import (
    NOMINA_VACUNAS,
    CentroDeInfancia,
    NominaCentroInfancia,
)
from centrodeinfancia.tests.test_destinatario_form import datos_validos
from core.models import Provincia
from users.models import Profile


def _fecha_menor_48_meses():
    return date.today() - timedelta(days=365 * 3)


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────


@pytest.fixture
def provincia():
    return Provincia.objects.create(nombre="Buenos Aires")


@pytest.fixture
def centro(provincia):
    return CentroDeInfancia.objects.create(nombre="CDI Girasoles", provincia=provincia)


@pytest.fixture
def ciudadano():
    return Ciudadano.objects.create(
        apellido="Ramirez",
        nombre="Sofia",
        fecha_nacimiento=_fecha_menor_48_meses(),
        documento=44555666,
    )


@pytest.fixture
def nomina(centro, ciudadano):
    return NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        dni=ciudadano.documento,
        apellido=ciudadano.apellido,
        nombre=ciudadano.nombre,
        fecha_nacimiento=ciudadano.fecha_nacimiento,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )


def _make_user(*codenames):
    user = User.objects.create_user(
        username=f"user_{'_'.join(codenames)}", password="test1234"
    )
    Profile.objects.get_or_create(user=user)
    for codename in codenames:
        try:
            user.user_permissions.add(Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    return user


@pytest.fixture
def usuario_view():
    return _make_user("view_nominacentroinfancia", "view_centrodeinfancia")


@pytest.fixture
def usuario_add():
    return _make_user("add_nominacentroinfancia", "view_centrodeinfancia")


@pytest.fixture
def usuario_change():
    return _make_user("change_nominacentroinfancia", "view_centrodeinfancia")


def _valid_post(centro, **overrides):
    """Payload completo del legajo (todos los campos obligatorios)."""

    defaults = {
        "apellido": "Ramirez",
        "nombre": "Sofia",
        "fecha_nacimiento": _fecha_menor_48_meses().isoformat(),
        "dni": "44555666",
    }
    defaults.update(overrides)
    return datos_validos(centro, **defaults)


def _post_completo(centro, **overrides):
    """Valores distintivos para cada campo editable que renderiza el legajo."""

    data = _valid_post(
        centro,
        sala="3_anios",
        piso_domicilio="2",
        convivientes="4",
        pueblo_originario_cual="Mapuche",
        responsable_legal_1_telefono="1122334455",
        responsable_legal_2_relacion="padre",
        responsable_legal_2_apellido="Ramirez",
        responsable_legal_2_nombre="Pablo",
        responsable_legal_2_fecha_nacimiento="1988-09-12",
        responsable_legal_2_tipo_documentacion="dni_permanente",
        responsable_legal_2_dni="30123457",
        responsable_legal_2_cuit="27-30123456-8",
        responsable_legal_2_pais_nacimiento="Argentina",
        responsable_legal_2_nacionalidad="Argentino",
        responsable_legal_2_sexo_registral="varon",
        responsable_legal_2_nivel_educativo="superior_completo",
        responsable_legal_2_consentimiento="si",
        responsable_legal_2_telefono="1122334456",
        grupo_pertenencia=["indigena", "asiatico"],
        lenguajes=["espanol_castellano", "lsa"],
        tiene_discapacidad="si",
        tipo_discapacidad=["motora", "visual"],
        posee_cud="true",
        numero_cud="123456",
        cobertura_salud="obra_social",
        controles_sanitarios_ultimo_anio="3",
        calendario_vacunacion_al_dia="true",
        peso="14.2",
        longitud_acostado="80.0",
        talla="95.0",
        perimetro_cefalico="48.0",
        lactancia="complementaria",
        alergias_alimentarias=["leche_vaca", "tacc"],
        anses_auh="si",
        anses_aue="no",
        anses_acsi="si",
        anses_acn="no",
        recibe_apoyo_desarrollo="si",
        observaciones="Seguimiento integral sin novedades.",
    )
    for index, (code, _label) in enumerate(NOMINA_VACUNAS, start=1):
        data[f"vacuna_{code}_dosis"] = f"{min(index, 3)}_dosis"
        year = 2024 + ((index - 1) // 12)
        month = ((index - 1) % 12) + 1
        data[f"vacuna_{code}_fecha"] = f"{year}-{month:02d}-10"
    data.update(overrides)
    return data


def _valor_comparable(field_name, field, value):
    """Normaliza únicamente diferencias de representación HTML/modelo."""

    if isinstance(value, (list, tuple)):
        return sorted(str(item) for item in value)
    if value in (None, ""):
        return ""
    if field_name.endswith("cuit") or field_name == "cuit_nino":
        return "".join(character for character in str(value) if character.isdigit())
    if isinstance(field, forms.DateField):
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
    if isinstance(field, forms.DecimalField):
        return Decimal(str(value))
    if isinstance(field, forms.IntegerField):
        return int(value)
    rendered = str(value)
    return rendered.lower() if rendered.lower() in {"true", "false"} else rendered


# ─────────────────────────────────────────────────────────
# Create view
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestNominaCentroInfanciaCreateView:

    def _url(self, centro):
        return reverse("centrodeinfancia_nomina_crear", kwargs={"pk": centro.pk})

    def test_requiere_autenticacion(self, centro):
        resp = Client().get(self._url(centro))
        assert resp.status_code in (302, 403)

    def test_get_sin_query_muestra_busqueda(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        resp = client.get(self._url(centro))
        assert resp.status_code == 200
        assert not resp.context.get("mostrar_formulario")

    def test_get_con_ciudadano_id_muestra_formulario(
        self, usuario_add, centro, ciudadano
    ):
        client = Client()
        client.force_login(usuario_add)
        url = self._url(centro) + f"?ciudadano_id={ciudadano.pk}"
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.context.get("mostrar_formulario")
        assert resp.context.get("selected_ciudadano") == ciudadano

    def test_get_query_sin_resultados_muestra_formulario(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        url = self._url(centro) + "?query=99999999"
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.context.get("no_resultados")
        assert resp.context.get("mostrar_formulario")

    def test_get_precarga_la_provincia_del_cdi_sin_geografia_dependiente(
        self, usuario_add, centro
    ):
        client = Client()
        client.force_login(usuario_add)
        url = self._url(centro) + "?query=99999999"

        response = client.get(url)

        form = response.context["form"]
        assert form["provincia_domicilio"].value() == centro.provincia_id
        assert form["departamento_domicilio"].value() is None
        assert form["municipio_domicilio"].value() is None
        assert form["localidad_domicilio"].value() is None

    def test_get_prioriza_la_provincia_del_cdi_sobre_la_del_ciudadano(
        self, usuario_add, centro, ciudadano
    ):
        provincia_ciudadano = Provincia.objects.create(nombre="Cordoba")
        ciudadano.provincia = provincia_ciudadano
        ciudadano.save(update_fields=["provincia"])
        client = Client()
        client.force_login(usuario_add)

        response = client.get(self._url(centro) + f"?ciudadano_id={ciudadano.pk}")

        assert (
            response.context["form"]["provincia_domicilio"].value()
            == centro.provincia_id
        )

    def test_get_sin_provincia_del_cdi_no_precarga_provincia(self, usuario_add):
        centro = CentroDeInfancia.objects.create(nombre="CDI Sin Provincia")
        client = Client()
        client.force_login(usuario_add)

        response = client.get(self._url(centro) + "?query=99999999")

        assert response.context["form"]["provincia_domicilio"].value() is None

    def test_get_usa_template_destinatario(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        url = self._url(centro) + "?query=99999999"
        resp = client.get(url)
        assert "centrodeinfancia/destinatario_form.html" in [
            t.name for t in resp.templates
        ]

    def test_post_crea_nomina_con_ciudadano_existente(
        self, usuario_add, centro, ciudadano
    ):
        client = Client()
        client.force_login(usuario_add)
        data = _valid_post(centro, ciudadano_id=ciudadano.pk)
        resp = client.post(self._url(centro), data)
        assert resp.status_code == 302
        assert NominaCentroInfancia.objects.filter(
            centro=centro, ciudadano=ciudadano
        ).exists()

    def test_post_crea_ciudadano_si_no_existe(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        data = _valid_post(centro, dni="55666777", apellido="Nuevo", nombre="Niño")
        assert not Ciudadano.objects.filter(documento="55666777").exists()
        resp = client.post(self._url(centro), data)
        assert resp.status_code == 302
        assert Ciudadano.objects.filter(documento="55666777").exists()

    def test_post_duplicado_no_crea_segunda_nomina(
        self, usuario_add, centro, ciudadano, nomina
    ):
        client = Client()
        client.force_login(usuario_add)
        data = _valid_post(centro, ciudadano_id=ciudadano.pk)
        resp = client.post(self._url(centro), data)
        assert resp.status_code == 302
        assert (
            NominaCentroInfancia.objects.filter(
                centro=centro, ciudadano=ciudadano, deleted_at__isnull=True
            ).count()
            == 1
        )

    def test_post_invalido_no_redirige(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        resp = client.post(self._url(centro), {"apellido": "Sin fecha"})
        assert resp.status_code == 200

    def test_contexto_incluye_centro(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        resp = client.get(self._url(centro))
        assert resp.context["centro"] == centro


# ─────────────────────────────────────────────────────────
# Edit view
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestNominaCentroInfanciaEditView:

    def _url(self, centro, nomina):
        return reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

    def test_requiere_autenticacion(self, centro, nomina):
        resp = Client().get(self._url(centro, nomina))
        assert resp.status_code in (302, 403)

    def test_get_renderiza_template_destinatario(self, usuario_change, centro, nomina):
        client = Client()
        client.force_login(usuario_change)
        resp = client.get(self._url(centro, nomina))
        assert resp.status_code == 200
        assert "centrodeinfancia/destinatario_form.html" in [
            t.name for t in resp.templates
        ]

    def test_contexto_es_edit(self, usuario_change, centro, nomina):
        client = Client()
        client.force_login(usuario_change)
        resp = client.get(self._url(centro, nomina))
        assert resp.status_code == 200
        assert resp.context["is_edit"] is True
        assert resp.context["centro"] == centro

    def test_get_edicion_precarga_todos_los_campos_visibles(
        self, usuario_change, centro, nomina
    ):
        client = Client()
        client.force_login(usuario_change)
        url = self._url(centro, nomina)
        data = _post_completo(centro)

        update_response = client.post(url, data)
        assert update_response.status_code == 302

        response = client.get(url)
        assert response.status_code == 200
        form = response.context["form"]
        html = response.content.decode("utf-8")

        assert set(data).issubset(form.fields)
        for field_name, expected in data.items():
            field = form.fields[field_name]
            assert _valor_comparable(
                field_name, field, form[field_name].value()
            ) == _valor_comparable(field_name, field, expected), field_name
            assert f'name="{field_name}"' in html, field_name

    def test_post_invalido_conserva_todos_los_campos_visibles_y_no_guarda(
        self, usuario_change, centro, nomina
    ):
        client = Client()
        client.force_login(usuario_change)
        url = self._url(centro, nomina)
        nombre_original = nomina.nombre
        data = _post_completo(
            centro,
            nombre="Nombre Nuevo",
            fecha_registro="2026-99-99",
        )

        response = client.post(url, data)

        assert response.status_code == 200
        form = response.context["form"]
        html = response.content.decode("utf-8")
        assert form.is_bound
        assert "fecha_registro" in form.errors
        assert set(data).issubset(form.fields)
        for field_name, expected in data.items():
            field = form.fields[field_name]
            assert _valor_comparable(
                field_name, field, form[field_name].value()
            ) == _valor_comparable(field_name, field, expected), field_name
            assert f'name="{field_name}"' in html, field_name

        nomina.refresh_from_db()
        assert nomina.nombre == nombre_original

    def test_post_actualiza_campos(self, usuario_change, centro, nomina):
        client = Client()
        client.force_login(usuario_change)
        data = _valid_post(
            centro,
            apellido="Ramirez-Editado",
            nombre="Sofia",
            estado=NominaCentroInfancia.ESTADO_BAJA,
        )
        resp = client.post(self._url(centro, nomina), data)
        assert resp.status_code == 302
        nomina.refresh_from_db()
        assert nomina.apellido == "Ramirez-Editado"
        assert nomina.estado == NominaCentroInfancia.ESTADO_BAJA

    def test_post_redirige_a_nomina(self, usuario_change, centro, nomina):
        client = Client()
        client.force_login(usuario_change)
        resp = client.post(self._url(centro, nomina), _valid_post(centro))
        expected = reverse("centrodeinfancia_nomina_ver", kwargs={"pk": centro.pk})
        assert resp.status_code == 302
        assert expected in resp.url

    def test_scope_nomina_de_otro_centro_da_404(
        self, usuario_change, centro, ciudadano
    ):
        otro_centro = CentroDeInfancia.objects.create(
            nombre="CDI Otro", provincia=centro.provincia
        )
        nomina_otro = NominaCentroInfancia.objects.create(
            centro=otro_centro,
            ciudadano=ciudadano,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento=ciudadano.fecha_nacimiento,
        )
        client = Client()
        client.force_login(usuario_change)
        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina_otro.pk},
        )
        assert client.get(url).status_code in (404, 403)


# ─────────────────────────────────────────────────────────
# Detail view
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestNominaCentroInfanciaDestinatarioDetailView:

    def _url(self, centro, nomina):
        return reverse(
            "centrodeinfancia_nomina_destinatario_ver",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

    def test_requiere_autenticacion(self, centro, nomina):
        resp = Client().get(self._url(centro, nomina))
        assert resp.status_code in (302, 403)

    def test_get_devuelve_200(self, usuario_view, centro, nomina):
        client = Client()
        client.force_login(usuario_view)
        resp = client.get(self._url(centro, nomina))
        assert resp.status_code == 200

    def test_usa_template_destinatario_detail(self, usuario_view, centro, nomina):
        client = Client()
        client.force_login(usuario_view)
        resp = client.get(self._url(centro, nomina))
        assert "centrodeinfancia/destinatario_detail.html" in [
            t.name for t in resp.templates
        ]

    def test_contexto_contiene_nomina_y_centro(self, usuario_view, centro, nomina):
        client = Client()
        client.force_login(usuario_view)
        resp = client.get(self._url(centro, nomina))
        assert resp.context["nomina"] == nomina
        assert resp.context["centro"] == centro
        assert "puede_editar" in resp.context

    def test_scope_nomina_de_otro_centro_da_404(self, usuario_view, centro, ciudadano):
        otro_centro = CentroDeInfancia.objects.create(
            nombre="CDI Otro", provincia=centro.provincia
        )
        nomina_otro = NominaCentroInfancia.objects.create(
            centro=otro_centro,
            ciudadano=ciudadano,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento=ciudadano.fecha_nacimiento,
        )
        client = Client()
        client.force_login(usuario_view)
        url = reverse(
            "centrodeinfancia_nomina_destinatario_ver",
            kwargs={"pk": centro.pk, "nomina_id": nomina_otro.pk},
        )
        assert client.get(url).status_code in (404, 403)
