from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Permission, User
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse

from centrodeinfancia.models import CentroDeInfancia, FormularioCDI
from centrodeinfancia.views_formulario_cdi import (
    FormularioCDIDetailView,
    FormularioCDIListView,
)
from core.models import Provincia
from users.models import Profile


def _build_view(view_cls, request, **kwargs):
    view = view_cls()
    view.setup(request, **kwargs)
    return view


def _crear_usuario(username, provincia=None, superuser=False):
    if superuser:
        user = User.objects.create_superuser(
            username=username,
            email=f"{username}@example.com",
            password="test1234",
        )
    else:
        user = User.objects.create_user(username=username, password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia
    profile.save()
    return user


def _construir_payload_creacion_formulario(centro, **overrides):
    payload = {
        "fecha_relevamiento": "2026-03-13",
        "nombre_completo_respondente": "Ana Perez",
        "nombre_cdi": centro.nombre,
        "codigo_cdi": centro.codigo_cdi,
        "distribucion_salas-TOTAL_FORMS": "6",
        "distribucion_salas-INITIAL_FORMS": "0",
        "distribucion_salas-MIN_NUM_FORMS": "0",
        "distribucion_salas-MAX_NUM_FORMS": "1000",
        "demanda_insatisfecha_por_grupo_etario-TOTAL_FORMS": "6",
        "demanda_insatisfecha_por_grupo_etario-INITIAL_FORMS": "0",
        "demanda_insatisfecha_por_grupo_etario-MIN_NUM_FORMS": "0",
        "demanda_insatisfecha_por_grupo_etario-MAX_NUM_FORMS": "1000",
        "frecuencia_articulacion-TOTAL_FORMS": "15",
        "frecuencia_articulacion-INITIAL_FORMS": "0",
        "frecuencia_articulacion-MIN_NUM_FORMS": "0",
        "frecuencia_articulacion-MAX_NUM_FORMS": "1000",
    }

    for index, value in enumerate(
        [
            "lactantes",
            "deambuladores",
            "dos_anos",
            "tres_anos",
            "cuatro_anos",
            "multiedad",
        ]
    ):
        payload[f"distribucion_salas-{index}-grupo_etario"] = value

    for index, value in enumerate(
        ["lactantes", "deambuladores", "un_ano", "dos_anos", "tres_anos", "cuatro_anos"]
    ):
        payload[f"demanda_insatisfecha_por_grupo_etario-{index}-grupo_etario"] = value

    for index, value in enumerate(
        [
            "servicio_promocion_proteccion_local",
            "servicio_promocion_proteccion_zonal",
            "salud_caps_hospital_municipal",
            "salud_hospital_provincial",
            "educacion_jardin_maternal",
            "educacion_escuela_primaria",
            "desarrollo_social_municipal",
            "desarrollo_social_provincial",
            "justicia_juzgado",
            "cultura_juegotecas",
            "cultura_espacios_comunitarios",
            "cultura_iglesias",
            "seguridad_policia",
            "seguridad_social_anses",
            "identidad_renaper",
        ]
    ):
        payload[f"frecuencia_articulacion-{index}-tipo_institucion"] = value

    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_formulario_cdi_listado_no_permite_centro_fuera_de_provincia():
    provincia_a = Provincia.objects.create(nombre="Buenos Aires")
    provincia_b = Provincia.objects.create(nombre="Cordoba")
    user = _crear_usuario("user-form-prov", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(nombre="CDI B", provincia=provincia_b)

    request = RequestFactory().get(f"/centrodeinfancia/{centro_b.pk}/formularios/")
    request.user = user
    view = _build_view(FormularioCDIListView, request, pk=centro_b.pk)

    with pytest.raises(Http404):
        view.get_centro()


@pytest.mark.django_db
def test_formulario_cdi_detalle_respeta_scope_por_provincia():
    provincia_a = Provincia.objects.create(nombre="Mendoza")
    provincia_b = Provincia.objects.create(nombre="Salta")
    user = _crear_usuario("user-form-det", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(
        nombre="CDI Salta", provincia=provincia_b
    )
    formulario = FormularioCDI.objects.create(
        centro=centro_b, codigo_cdi=centro_b.codigo_cdi
    )

    request = RequestFactory().get(
        f"/centrodeinfancia/{centro_b.pk}/formularios/{formulario.pk}/"
    )
    request.user = user
    view = _build_view(
        FormularioCDIDetailView,
        request,
        pk=centro_b.pk,
        form_pk=formulario.pk,
    )

    with pytest.raises(Http404):
        view.get_object()


@pytest.mark.django_db
def test_detalle_cdi_muestra_solo_ultimos_tres_formularios(client):
    user = _crear_usuario("super-form-card", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Card")

    formularios = []
    base_date = date(2026, 3, 1)
    for offset in range(4):
        formularios.append(
            FormularioCDI.objects.create(
                centro=centro,
                codigo_cdi=centro.codigo_cdi,
                fecha_relevamiento=base_date + timedelta(days=offset),
                nombre_completo_respondente=f"Persona {offset}",
            )
        )

    response = client.get(reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert f">{formularios[3].id}<" in content
    assert f">{formularios[2].id}<" in content
    assert f">{formularios[1].id}<" in content
    assert f">{formularios[0].id}<" not in content
    assert 'accordion-header--formularios">Formularios</button>' in content


@pytest.mark.django_db
def test_detalle_cdi_no_expone_formularios_sin_permiso_especifico(client):
    user = _crear_usuario("user-form-card-hidden")
    user.user_permissions.add(Permission.objects.get(codename="view_centrodeinfancia"))
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Permisos")
    FormularioCDI.objects.create(
        centro=centro,
        codigo_cdi=centro.codigo_cdi,
        nombre_completo_respondente="Persona Reservada",
    )

    response = client.get(reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Formularios" not in content
    assert "Persona Reservada" not in content


@pytest.mark.django_db
def test_formulario_cdi_editar_preserva_snapshot_historico_del_centro(client):
    user = _crear_usuario("super-form-edit-snapshot", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(
        nombre="Centro Actual", calle="Calle Actual"
    )
    formulario = FormularioCDI.objects.create(
        centro=centro,
        codigo_cdi=centro.codigo_cdi,
        nombre_cdi="Centro Historico",
        calle_cdi="Calle Historica",
    )

    centro.nombre = "Centro Modificado"
    centro.calle = "Calle Modificada"
    centro.save()

    response = client.get(
        reverse(
            "centrodeinfancia_formulario_editar",
            kwargs={"pk": centro.pk, "form_pk": formulario.pk},
        )
    )

    assert response.status_code == 200
    assert response.context["form"]["nombre_cdi"].value() == "Centro Historico"
    assert response.context["form"]["calle_cdi"].value() == "Calle Historica"


@pytest.mark.django_db
def test_formulario_cdi_crear_renderiza_filas_editables_base(client):
    user = _crear_usuario("super-form-create", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Tablas")

    response = client.get(
        reverse("centrodeinfancia_formulario_crear", kwargs={"pk": centro.pk})
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'name="distribucion_salas-0-cantidad_salas"' in content
    assert 'name="demanda_insatisfecha_por_grupo_etario-0-cantidad_demanda_insatisfecha"' in content
    assert 'name="frecuencia_articulacion-0-frecuencia"' in content


@pytest.mark.django_db
def test_formulario_cdi_crear_guarda_y_limpia_campos_ocultos(client):
    user = _crear_usuario("super-form-save", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Guardado")

    payload = _construir_payload_creacion_formulario(
        centro,
        tiene_espacio_cocina="no",
        combustible_cocinar="gas_red",
        tiene_espacio_exterior="no",
        tiene_juegos_exteriores="si",
        prestaciones_alimentarias=["ninguna"],
        calidad_elaboracion_menu="sin_nutricionista_ultraprocesados",
    )

    response = client.post(
        reverse("centrodeinfancia_formulario_crear", kwargs={"pk": centro.pk}),
        payload,
    )

    assert response.status_code == 302
    formulario = FormularioCDI.objects.get(centro=centro)
    assert formulario.source_form_version == 1
    assert formulario.combustible_cocinar in ("", None)
    assert formulario.tiene_juegos_exteriores in ("", None)
    assert formulario.calidad_elaboracion_menu in ("", None)


@pytest.mark.django_db
def test_formulario_cdi_form_sections_agrupa_meses_y_dias_en_la_misma_fila(client):
    user = _crear_usuario("super-form-layout", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Layout")

    response = client.get(
        reverse("centrodeinfancia_formulario_crear", kwargs={"pk": centro.pk})
    )

    assert response.status_code == 200
    general_section = next(
        section
        for section in response.context["section_fields"]
        if section["title"] == "Caracterizacion general"
    )
    row_names = [[field["name"] for field in row] for row in general_section["rows"]]
    assert ["meses_funcionamiento", "dias_funcionamiento"] in row_names

