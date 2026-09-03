from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.utils import timezone
from django.urls import reverse

from core.models import Municipio, Provincia
from pas.forms import PasCambioEstadoForm, PasPersonaCreateForm
from pas.models import (
    PasAviso,
    PasDeclaracionJurada,
    PasEstado,
    PasHistorialEstado,
    PasPersona,
)
from pas.services.persona_service import (
    cambiar_estado,
    get_personas_filtradas,
    registrar_persona,
)
from pas.services.formacion_service import (
    calcular_periodo_formacion,
    obtener_formacion_persona,
    resumir_formacion,
)


@pytest.fixture
def ubicacion():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    return provincia, municipio


@pytest.fixture
def catalogo_pas():
    activo = PasEstado.objects.create(nombre="Activo")
    suspendido = PasEstado.objects.create(nombre="Suspendido")
    aviso_activo = PasAviso.objects.create(codigo=1, descripcion="100%")
    aviso_activo.estados.add(activo)
    aviso_suspendido = PasAviso.objects.create(
        codigo=13,
        descripcion="SUSPENSION POR INCUMPLIMIENTO",
    )
    aviso_suspendido.estados.add(suspendido)
    return {
        "activo": activo,
        "suspendido": suspendido,
        "aviso_activo": aviso_activo,
        "aviso_suspendido": aviso_suspendido,
    }


@pytest.fixture
def titular_pas(ubicacion, catalogo_pas):
    provincia, municipio = ubicacion
    form = PasPersonaCreateForm(
        data={
            "id_persona": "1234",
            "apellidos": "Garcia",
            "nombres": "Maria Cristina",
            "dni": "30111222",
            "cuit": "27301112220",
            "provincia": str(provincia.id),
            "municipio": str(municipio.id),
            "estado": str(catalogo_pas["activo"].id),
            "avisos": [str(catalogo_pas["aviso_activo"].id)],
        }
    )
    assert form.is_valid(), form.errors
    return registrar_persona(form)


@pytest.mark.django_db
def test_registrar_persona_crea_estado_actual_e_historial(ubicacion, catalogo_pas):
    provincia, municipio = ubicacion
    form = PasPersonaCreateForm(
        data={
            "id_persona": "123",
            "apellidos": "Perez",
            "nombres": "Ana",
            "dni": "30111222",
            "cuit": "27301112220",
            "provincia": str(provincia.id),
            "municipio": str(municipio.id),
            "estado": str(catalogo_pas["activo"].id),
            "avisos": [str(catalogo_pas["aviso_activo"].id)],
        }
    )

    assert form.is_valid(), form.errors

    persona = registrar_persona(form)

    assert persona.estado == catalogo_pas["activo"]
    assert list(persona.avisos.all()) == [catalogo_pas["aviso_activo"]]
    historial = PasHistorialEstado.objects.get(persona=persona)
    assert historial.estado_anterior is None
    assert historial.estado_nuevo == catalogo_pas["activo"]
    assert list(historial.avisos_nuevos.all()) == [catalogo_pas["aviso_activo"]]
    assert persona.invitacion_ddjj_vigente is not None


@pytest.mark.django_db
def test_cambiar_estado_actualiza_persona_y_guarda_estado_anterior(
    ubicacion,
    catalogo_pas,
):
    provincia, municipio = ubicacion
    form = PasPersonaCreateForm(
        data={
            "id_persona": "456",
            "apellidos": "Gomez",
            "nombres": "Luis",
            "dni": "32111222",
            "cuit": "",
            "provincia": str(provincia.id),
            "municipio": str(municipio.id),
            "estado": str(catalogo_pas["activo"].id),
            "avisos": [str(catalogo_pas["aviso_activo"].id)],
        }
    )
    assert form.is_valid(), form.errors
    persona = registrar_persona(form)

    cambio_form = PasCambioEstadoForm(
        data={
            "estado": str(catalogo_pas["suspendido"].id),
            "avisos": [str(catalogo_pas["aviso_suspendido"].id)],
        }
    )
    assert cambio_form.is_valid(), cambio_form.errors

    cambiar_estado(persona, cambio_form)
    persona.refresh_from_db()

    assert persona.estado == catalogo_pas["suspendido"]
    assert list(persona.avisos.all()) == [catalogo_pas["aviso_suspendido"]]
    historial = persona.historial_estados.order_by("-fecha_cambio").first()
    assert historial.estado_anterior == catalogo_pas["activo"]
    assert historial.estado_nuevo == catalogo_pas["suspendido"]
    assert list(historial.avisos_anteriores.all()) == [catalogo_pas["aviso_activo"]]
    assert list(historial.avisos_nuevos.all()) == [catalogo_pas["aviso_suspendido"]]


@pytest.mark.django_db
def test_cambio_estado_rechaza_aviso_de_otro_estado(catalogo_pas):
    form = PasCambioEstadoForm(
        data={
            "estado": str(catalogo_pas["suspendido"].id),
            "avisos": [str(catalogo_pas["aviso_activo"].id)],
        }
    )

    assert not form.is_valid()
    assert "avisos" in form.errors


@pytest.mark.django_db
def test_buscador_pas_filtra_por_nombre_y_estado(ubicacion, catalogo_pas):
    provincia, municipio = ubicacion
    for id_persona, apellidos, nombres, dni, estado, aviso in (
        (
            101,
            "Garcia",
            "Maria Cristina",
            30111222,
            catalogo_pas["activo"],
            catalogo_pas["aviso_activo"],
        ),
        (
            102,
            "Fernandez",
            "Jorge Luis",
            32111222,
            catalogo_pas["suspendido"],
            catalogo_pas["aviso_suspendido"],
        ),
    ):
        form = PasPersonaCreateForm(
            data={
                "id_persona": str(id_persona),
                "apellidos": apellidos,
                "nombres": nombres,
                "dni": str(dni),
                "cuit": f"20{dni}1",
                "provincia": str(provincia.id),
                "municipio": str(municipio.id),
                "estado": str(estado.id),
                "avisos": [str(aviso.id)],
            }
        )
        assert form.is_valid(), form.errors
        registrar_persona(form)

    resultados = get_personas_filtradas(QueryDict("q=jorge&estado=Suspendido"))

    assert list(resultados.values_list("apellidos", flat=True)) == ["Fernandez"]


@pytest.mark.django_db
def test_buscador_pas_filtra_por_id_persona(ubicacion, catalogo_pas):
    provincia, municipio = ubicacion
    form = PasPersonaCreateForm(
        data={
            "id_persona": "9876",
            "apellidos": "Lopez",
            "nombres": "Ana",
            "dni": "30123456",
            "cuit": "27301234560",
            "provincia": str(provincia.id),
            "municipio": str(municipio.id),
            "estado": str(catalogo_pas["activo"].id),
            "avisos": [str(catalogo_pas["aviso_activo"].id)],
        }
    )
    assert form.is_valid(), form.errors
    registrar_persona(form)

    resultados = get_personas_filtradas(QueryDict("q=9876"))

    assert resultados.get().id_persona == 9876


@pytest.mark.django_db
def test_edicion_http_conserva_y_muestra_datos_de_contacto(client, titular_pas):
    titular_pas.domicilio = "Calle 10 123"
    titular_pas.correo_electronico = "titular@example.test"
    titular_pas.telefono_celular = "1122334455"
    titular_pas.save()
    usuario = get_user_model().objects.create_superuser(
        username="pas-edicion-contacto-test",
        email="edicion-contacto@example.test",
        password="test-pass",
    )
    client.force_login(usuario)
    url = reverse("pas_persona_editar", args=[titular_pas.pk])

    respuesta_get = client.get(url)

    assert respuesta_get.status_code == 200
    assert b"Calle 10 123" in respuesta_get.content
    assert b"titular@example.test" in respuesta_get.content
    assert b"1122334455" in respuesta_get.content

    respuesta_post = client.post(
        url,
        {
            "id_persona": titular_pas.id_persona,
            "apellidos": "Apellido actualizado",
            "nombres": titular_pas.nombres,
            "dni": titular_pas.dni,
            "cuit": titular_pas.cuit,
            "provincia": titular_pas.provincia_id,
            "municipio": titular_pas.municipio_id,
            "domicilio": titular_pas.domicilio,
            "correo_electronico": titular_pas.correo_electronico,
            "telefono_celular": titular_pas.telefono_celular,
        },
    )

    assert respuesta_post.status_code == 302
    titular_pas.refresh_from_db()
    assert titular_pas.apellidos == "Apellido actualizado"
    assert titular_pas.domicilio == "Calle 10 123"
    assert titular_pas.correo_electronico == "titular@example.test"
    assert titular_pas.telefono_celular == "1122334455"


@pytest.mark.django_db
def test_formacion_busca_titular_despues_de_los_primeros_cien(
    client, ubicacion, catalogo_pas
):
    provincia, municipio = ubicacion
    personas = [
        PasPersona(
            id_persona=20000 + indice,
            apellidos=f"Apellido {indice:03d}",
            nombres="Persona",
            dni=40000000 + indice,
            cuit=f"2040000{indice:04d}",
            provincia=provincia,
            municipio=municipio,
            estado=catalogo_pas["activo"],
        )
        for indice in range(105)
    ]
    personas.append(
        PasPersona(
            id_persona=29999,
            apellidos="ZZZ Busqueda",
            nombres="Objetivo",
            dni=49999999,
            cuit="20499999991",
            provincia=provincia,
            municipio=municipio,
            estado=catalogo_pas["activo"],
        )
    )
    PasPersona.objects.bulk_create(personas)
    usuario = get_user_model().objects.create_superuser(
        username="pas-formacion-padron-completo-test",
        email="formacion-padron@example.test",
        password="test-pass",
    )
    client.force_login(usuario)

    respuesta = client.get(reverse("pas_formacion"), {"q": "20499999991"})

    assert respuesta.status_code == 200
    assert b"ZZZ Busqueda" in respuesta.content


@pytest.mark.django_db
def test_formacion_scroll_infinito_entrega_paginas_sin_duplicados(
    client, ubicacion, catalogo_pas
):
    provincia, municipio = ubicacion
    PasPersona.objects.bulk_create(
        [
            PasPersona(
                id_persona=30000 + indice,
                apellidos=f"Scroll {indice:03d}",
                nombres="Persona",
                dni=50000000 + indice,
                cuit=f"2050000{indice:04d}",
                provincia=provincia,
                municipio=municipio,
                estado=catalogo_pas["activo"],
            )
            for indice in range(35)
        ]
    )
    usuario = get_user_model().objects.create_superuser(
        username="pas-formacion-scroll-test",
        email="formacion-scroll@example.test",
        password="test-pass",
    )
    client.force_login(usuario)

    primera = client.get(reverse("pas_formacion"), {"q": "Scroll"})
    segunda = client.get(
        reverse("pas_formacion_personas"),
        {"q": "Scroll", "page": 2},
    )

    assert primera.status_code == 200
    assert len(primera.context["personas"]) == 30
    assert primera.context["pagina_formacion"].has_next()
    assert segunda.status_code == 200
    payload = segunda.json()
    assert payload["has_next"] is False
    assert payload["html"].count("pas-formation-person-link") == 5


def test_formacion_pas_permanece_sin_datos_hasta_definir_una_fuente():
    assert obtener_formacion_persona(object()) == []


def test_resumir_formacion_asigna_cien_puntos_por_curso_completado():
    formaciones = [
        {"estado_codigo": "completada", "puntos": 100},
        {"estado_codigo": "inscripta", "puntos": 0},
    ]

    resumen = resumir_formacion(formaciones)

    assert resumen["puntos"] == 100
    assert resumen["cursos_completados"] == 1
    assert resumen["total_cursos"] == 2
    assert resumen["estado"] == "cumplido"


def test_periodo_formacion_avanza_y_reinicia_cada_noventa_dias():
    ultimo_dia_primer_periodo = calcular_periodo_formacion(date(2026, 3, 31))
    primer_dia_segundo_periodo = calcular_periodo_formacion(date(2026, 4, 1))
    periodo_vigente_referencia = calcular_periodo_formacion(date(2026, 7, 29))

    assert ultimo_dia_primer_periodo["dia_actual"] == 90
    assert primer_dia_segundo_periodo["dia_actual"] == 1
    assert primer_dia_segundo_periodo["inicio_actual"] == date(2026, 4, 1)
    assert primer_dia_segundo_periodo["fin_actual"] == date(2026, 6, 29)
    assert periodo_vigente_referencia["dia_actual"] == 30
    assert periodo_vigente_referencia["inicio_actual"] == date(2026, 6, 30)


@pytest.mark.django_db
def test_formacion_pas_muestra_semaforo_metricas_y_curso(client, titular_pas):
    usuario = get_user_model().objects.create_superuser(
        username="pas-formacion-test",
        email="pas-formacion@example.com",
        password="test-pass",
    )
    client.force_login(usuario)
    formacion = {
        "curso": "Herramientas digitales",
        "inicio": "2026-01-10",
        "fin": "2026-02-10",
        "estado": "Completada",
        "estado_codigo": "completada",
        "fuente": "Fuente futura",
        "progreso": 100,
        "puntos": 100,
        "certificado_url": None,
    }

    with (
        patch(
            "pas.services.formacion_service.obtener_puntos_por_dni",
            return_value={
                titular_pas.dni: {"puntos": 100, "total_cursos": 1},
            },
        ),
        patch("pas.views.obtener_formacion_persona", return_value=[formacion]),
    ):
        respuesta = client.get(reverse("pas_formacion"))

    assert respuesta.status_code == 200
    assert b"Sem" in respuesta.content
    assert b"Puntos acumulados" in respuesta.content
    assert b"D\xc3\xada del per\xc3\xadodo" in respuesta.content
    assert b"90 d\xc3\xadas corridos" in respuesta.content
    assert b"Herramientas digitales" in respuesta.content
    assert b"100 pts" in respuesta.content


@pytest.mark.django_db
def test_buscador_abre_panel_sobre_persona_seleccionada(client, titular_pas):
    usuario = get_user_model().objects.create_superuser(
        username="pas-panel-test",
        email="pas-panel@example.com",
        password="test-pass",
    )
    client.force_login(usuario)

    respuesta_buscador = client.get(reverse("pas_persona_listar"))
    url_panel = reverse("pas_panel_control_persona", args=[titular_pas.id])

    assert respuesta_buscador.status_code == 200
    assert url_panel.encode() in respuesta_buscador.content

    respuesta_panel = client.get(url_panel)

    assert respuesta_panel.status_code == 200
    assert respuesta_panel.context["persona"] == titular_pas
    assert b"Datos del titular" in respuesta_panel.content
    assert b"IdPersona" in respuesta_panel.content
    assert b"Integraci" in respuesta_panel.content
    assert b"$78.000" not in respuesta_panel.content
    assert b"0110099510008903894521" not in respuesta_panel.content
    assert b'id="capacitacion-panel"' in respuesta_panel.content
    enlace_externo = f'<a class="nav-link" href="{reverse("pas_formacion")}">'.encode()
    assert enlace_externo not in respuesta_panel.content


@pytest.mark.django_db
def test_panel_filtra_padron_por_cuit_y_estado_actual(client, titular_pas):
    usuario = get_user_model().objects.create_superuser(
        username="pas-panel-filtros-test",
        email="panel-filtros@example.com",
        password="test-pass",
    )
    client.force_login(usuario)
    url_panel = reverse("pas_panel_control_persona", args=[titular_pas.id])

    with patch(
        "pas.services.formacion_service.obtener_puntos_por_dni",
        return_value={titular_pas.dni: {"puntos": 0, "total_cursos": 0}},
    ):
        respuesta = client.get(
            url_panel,
            {"q": titular_pas.cuit, "estado_actual": titular_pas.estado_id},
        )

    assert respuesta.status_code == 200
    assert list(respuesta.context["personas_panel"]) == [titular_pas]
    assert respuesta.context["query"] == titular_pas.cuit
    assert respuesta.context["estado_actual"] == str(titular_pas.estado_id)
    assert b"Buscar por nombre, apellido o CUIT" in respuesta.content


@pytest.mark.django_db
def test_panel_y_formacion_conservan_la_persona_al_cambiar_de_area(client, titular_pas):
    usuario = get_user_model().objects.create_superuser(
        username="pas-navegacion-persona-test",
        email="navegacion-persona@example.com",
        password="test-pass",
    )
    client.force_login(usuario)
    url_panel = reverse("pas_panel_control_persona", args=[titular_pas.id])
    url_formacion = f'{reverse("pas_formacion")}?persona={titular_pas.id}'

    with patch(
        "pas.services.formacion_service.obtener_puntos_por_dni",
        return_value={titular_pas.dni: {"puntos": 0, "total_cursos": 0}},
    ):
        respuesta_panel = client.get(url_panel)
        respuesta_formacion = client.get(url_formacion)

    assert f'href="{url_formacion}"'.encode() in respuesta_panel.content
    assert respuesta_formacion.context["persona_seleccionada"] == titular_pas
    assert f'href="{url_panel}"'.encode() in respuesta_formacion.content


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "titulo"),
    [
        ("pas_mesa_ayuda", b"Mesa de Ayuda"),
        ("pas_liquidacion", b"Liquidaci\xc3\xb3n"),
    ],
)
def test_areas_pendientes_permanecen_visibles(client, url_name, titulo):
    usuario = get_user_model().objects.create_superuser(
        username=f"pas-{url_name}-test",
        email=f"{url_name}@example.test",
        password="test-pass",
    )
    client.force_login(usuario)

    respuesta = client.get(reverse(url_name))

    assert respuesta.status_code == 200
    assert len(respuesta.context["pas_areas"]) == 5
    assert titulo in respuesta.content
    assert b"Integraci\xc3\xb3n pendiente" in respuesta.content


@pytest.mark.django_db
def test_panel_muestra_solo_condiciones_y_colorea_aviso_por_estado(client, titular_pas):
    usuario = get_user_model().objects.create_superuser(
        username="pas-indicadores-test",
        email="indicadores@example.com",
        password="test-pass",
    )
    client.force_login(usuario)
    url_panel = reverse("pas_panel_control_persona", args=[titular_pas.id])

    with patch(
        "pas.services.formacion_service.obtener_puntos_por_dni",
        return_value={titular_pas.dni: {"puntos": 0, "total_cursos": 0}},
    ):
        pendiente = client.get(url_panel)

    item = pendiente.context["personas_panel"][0]
    assert item.mostrar_tag_ddjj
    assert not item.mostrar_tag_fch
    assert b"pas-mini-condition is-ddjj" in pendiente.content
    assert b"pas-mini-condition is-fch" not in pendiente.content
    assert b"pas-mini-flag-count" not in pendiente.content
    assert b"pas-aviso-card pas-status-activo" in pendiente.content

    titular_pas.estado = PasEstado.objects.get(nombre="Suspendido")
    titular_pas.save(update_fields=["estado"])
    PasDeclaracionJurada.objects.create(
        persona=titular_pas,
        invitacion=titular_pas.invitacion_ddjj_vigente,
        version=1,
        provincia=titular_pas.provincia,
        municipio=titular_pas.municipio,
        domicilio="Calle 1 100",
        correo_electronico="titular@example.test",
        telefono_celular="1122334455",
        datos_mi_argentina_confirmados=True,
        embarazada=False,
        hijos_menores_a_cargo=False,
        gastos_bajo_limite_smvm=True,
        no_accedio_mercado_cambios=True,
        acepto_declaracion=True,
        respuestas={},
        texto_legal="Declaración de prueba",
        archivo_pdf="pas/ddjj/prueba.pdf",
        finalizada=timezone.now(),
    )
    with patch(
        "pas.services.formacion_service.obtener_puntos_por_dni",
        return_value={titular_pas.dni: {"puntos": 100, "total_cursos": 1}},
    ):
        cumplido = client.get(url_panel)

    item = cumplido.context["personas_panel"][0]
    assert not item.mostrar_tag_ddjj
    assert not item.mostrar_tag_fch
    assert b"pas-mini-condition is-ddjj" not in cumplido.content
    assert b"pas-mini-condition is-fch" not in cumplido.content
    assert b"pas-aviso-card pas-status-suspendido" in cumplido.content
