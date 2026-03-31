from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Permission, User
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse

from centrodeinfancia.models import (
    CentroDeInfancia,
    CentroDeInfanciaHorarioFuncionamiento,
    FormularioCDI,
)
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


def _construir_payload_edicion_formulario(formulario, **overrides):
    payload = {
        "fecha_relevamiento": (
            formulario.fecha_relevamiento.isoformat()
            if formulario.fecha_relevamiento
            else ""
        ),
        "nombre_completo_respondente": formulario.nombre_completo_respondente or "",
        "rol_respondente": formulario.rol_respondente or "",
        "email_respondente": formulario.email_respondente or "",
        "nombre_cdi": formulario.nombre_cdi or "",
        "codigo_cdi": formulario.codigo_cdi or "",
        "distribucion_salas-TOTAL_FORMS": "6",
        "distribucion_salas-INITIAL_FORMS": "6",
        "distribucion_salas-MIN_NUM_FORMS": "0",
        "distribucion_salas-MAX_NUM_FORMS": "1000",
        "demanda_insatisfecha_por_grupo_etario-TOTAL_FORMS": "6",
        "demanda_insatisfecha_por_grupo_etario-INITIAL_FORMS": "6",
        "demanda_insatisfecha_por_grupo_etario-MIN_NUM_FORMS": "0",
        "demanda_insatisfecha_por_grupo_etario-MAX_NUM_FORMS": "1000",
        "frecuencia_articulacion-TOTAL_FORMS": "15",
        "frecuencia_articulacion-INITIAL_FORMS": "15",
        "frecuencia_articulacion-MIN_NUM_FORMS": "0",
        "frecuencia_articulacion-MAX_NUM_FORMS": "1000",
    }

    for index, row in enumerate(formulario.filas_distribucion_salas.order_by("id")):
        payload[f"distribucion_salas-{index}-id"] = str(row.id)
        payload[f"distribucion_salas-{index}-grupo_etario"] = row.grupo_etario
        payload[f"distribucion_salas-{index}-cantidad_salas"] = row.cantidad_salas or ""
        payload[f"distribucion_salas-{index}-superficie_exclusiva_m2"] = (
            row.superficie_exclusiva_m2 or ""
        )
        payload[f"distribucion_salas-{index}-cantidad_ninos"] = row.cantidad_ninos or ""
        payload[f"distribucion_salas-{index}-cantidad_personal_sala"] = (
            row.cantidad_personal_sala or ""
        )

    for index, row in enumerate(formulario.filas_demanda_insatisfecha.order_by("id")):
        payload[f"demanda_insatisfecha_por_grupo_etario-{index}-id"] = str(row.id)
        payload[f"demanda_insatisfecha_por_grupo_etario-{index}-grupo_etario"] = (
            row.grupo_etario
        )
        payload[
            f"demanda_insatisfecha_por_grupo_etario-{index}-cantidad_demanda_insatisfecha"
        ] = (row.cantidad_demanda_insatisfecha or "")

    for index, row in enumerate(formulario.filas_articulacion.order_by("id")):
        payload[f"frecuencia_articulacion-{index}-id"] = str(row.id)
        payload[f"frecuencia_articulacion-{index}-tipo_institucion"] = (
            row.tipo_institucion
        )
        payload[f"frecuencia_articulacion-{index}-frecuencia"] = row.frecuencia or ""

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
    assert (
        'name="demanda_insatisfecha_por_grupo_etario-0-cantidad_demanda_insatisfecha"'
        in content
    )
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
def test_formulario_cdi_crear_guarda_telefonos_flexibles_autocompletados(client):
    user = _crear_usuario("super-form-phone", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Telefonos Flex",
        telefono="12345678",
        telefono_referente="11-2233-4455",
    )

    response_get = client.get(
        reverse("centrodeinfancia_formulario_crear", kwargs={"pk": centro.pk})
    )

    assert response_get.status_code == 200
    assert response_get.context["form"]["telefono_cdi"].value() == "12345678"
    assert (
        response_get.context["form"]["telefono_referente_cdi"].value() == "11-2233-4455"
    )

    payload = _construir_payload_creacion_formulario(
        centro,
        telefono_cdi="12345678",
        telefono_referente_cdi="11-2233-4455",
        telefono_organizacion="22334455",
        telefono_referente_organizacion="54-11-99887766",
    )

    response_post = client.post(
        reverse("centrodeinfancia_formulario_crear", kwargs={"pk": centro.pk}),
        payload,
    )

    assert response_post.status_code == 302
    formulario = FormularioCDI.objects.get(centro=centro)
    assert formulario.telefono_cdi == "12345678"
    assert formulario.telefono_referente_cdi == "11-2233-4455"
    assert formulario.telefono_organizacion == "22334455"
    assert formulario.telefono_referente_organizacion == "54-11-99887766"


@pytest.mark.django_db
def test_formulario_cdi_editar_vacio_sin_cambios_guarda_correctamente(client):
    user = _crear_usuario("super-form-empty-edit", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Empty Edit")

    response_create = client.post(
        reverse("centrodeinfancia_formulario_crear", kwargs={"pk": centro.pk}),
        _construir_payload_creacion_formulario(centro),
    )

    assert response_create.status_code == 302
    formulario = FormularioCDI.objects.get(centro=centro)

    response_get = client.get(
        reverse(
            "centrodeinfancia_formulario_editar",
            kwargs={"pk": centro.pk, "form_pk": formulario.pk},
        )
    )

    assert response_get.status_code == 200
    content = response_get.content.decode("utf-8")
    assert content.count('name="distribucion_salas-0-id"') == 1
    assert content.count('name="demanda_insatisfecha_por_grupo_etario-0-id"') == 1
    assert content.count('name="frecuencia_articulacion-0-id"') == 1

    response_update = client.post(
        reverse(
            "centrodeinfancia_formulario_editar",
            kwargs={"pk": centro.pk, "form_pk": formulario.pk},
        ),
        _construir_payload_edicion_formulario(formulario),
    )

    assert response_update.status_code == 302
    formulario.refresh_from_db()
    assert formulario.pk is not None


@pytest.mark.django_db
def test_formulario_cdi_crear_autocompleta_campos_nuevos_desde_centro(client):
    user = _crear_usuario("super-form-autocomplete", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Autocomplete",
        organizacion="Asociacion Civil Horizonte",
        cuit_organizacion_gestiona="20445350304",
        ambito="rural",
        telefono="12345678",
        mail="cdi@example.com",
        dias_funcionamiento=["lunes", "martes"],
        meses_funcionamiento=["enero", "febrero"],
        tipo_jornada="simple_single_shift",
        oferta_servicios="multiedad",
        modalidad_gestion="gestion_tercer_sector",
    )
    CentroDeInfanciaHorarioFuncionamiento.objects.create(
        centro=centro,
        dia="lunes",
        hora_apertura="08:00",
        hora_cierre="12:00",
    )

    response = client.get(
        reverse("centrodeinfancia_formulario_crear", kwargs={"pk": centro.pk})
    )

    assert response.status_code == 200
    form = response.context["form"]
    assert form["ambito"].value() == "rural"
    assert form["nombre_organizacion_gestora"].value() == "Asociacion Civil Horizonte"
    assert form["cuit_organizacion_gestora"].value() == "20445350304"
    assert form["email_cdi"].value() == "cdi@example.com"
    assert form["tipo_jornada"].value() == "simple_single_shift"
    assert form["oferta_servicios"].value() == "multiedad"
    assert form["modalidad_gestion"].value() == "gestion_tercer_sector"
    assert form["horario_lunes_apertura"].value().strftime("%H:%M") == "08:00"
    assert form["horario_lunes_cierre"].value().strftime("%H:%M") == "12:00"


@pytest.mark.django_db
def test_detalle_cdi_muestra_nuevos_paneles_y_campos(client):
    user = _crear_usuario("super-cdi-detalle-campos", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Detalle",
        organizacion="Asociacion Civil Horizonte",
        cuit_organizacion_gestiona="20445350304",
        ambito="rural",
        mail="detalle@example.com",
        fecha_inicio=date(2024, 5, 20),
        codigo_postal=1234,
        latitud="-34.603700",
        longitud="-58.381600",
        meses_funcionamiento=["enero", "febrero"],
        dias_funcionamiento=["lunes", "martes"],
        tipo_jornada="simple_single_shift",
        oferta_servicios="multiedad",
        modalidad_gestion="gestion_tercer_sector",
    )
    CentroDeInfanciaHorarioFuncionamiento.objects.create(
        centro=centro,
        dia="lunes",
        hora_apertura="08:00",
        hora_cierre="12:00",
    )

    response = client.get(reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "accordion-header--informacion" in content
    assert "Informacion Basica" in content
    assert "accordion-header--funcionamiento" in content
    assert "Funcionamiento" in content
    assert "Asociacion Civil Horizonte" in content
    assert "20-44535030-4" in content
    assert "detalle@example.com" in content
    assert "20/05/2024" in content
    assert "1234" in content
    assert "Latitud:" in content
    assert "Longitud:" in content
    assert "Enero, Febrero" in content
    assert "Lunes, Martes" in content
    assert "Lunes: 08:00 a 12:00" in content
    assert "Multiedad" in content


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
