from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from pypdf import PdfReader

from core.models import Municipio, Provincia
from pas.forms import PasDeclaracionJuradaForm
from pas.models import PasDeclaracionJurada, PasEstado, PasPersona
from pas.services.ddjj_service import crear_invitacion, presentar_ddjj


@pytest.fixture
def persona_ddjj():
    provincia = Provincia.objects.create(nombre="Provincia inicial")
    municipio = Municipio.objects.create(
        nombre="Municipio inicial", provincia=provincia
    )
    estado = PasEstado.objects.create(nombre="Activo DDJJ")
    return PasPersona.objects.create(
        id_persona=9081,
        apellidos="Ejemplo",
        nombres="Persona",
        dni=30999888,
        provincia=provincia,
        municipio=municipio,
        estado=estado,
    )


def datos_formulario(provincia, municipio, **cambios):
    datos = {
        "datos_mi_argentina_confirmados": "si",
        "provincia": str(provincia.pk),
        "municipio": str(municipio.pk),
        "domicilio": "Calle 123",
        "correo_electronico": "persona@example.test",
        "telefono_celular": "1100000000",
        "embarazada": "no",
        "controles_embarazo_cumplidos": "",
        "hijos_menores_a_cargo": "no",
        "vacunacion_cumplida": "",
        "regularidad_escolar_acreditada": "",
        "gastos_bajo_limite_smvm": "si",
        "no_accedio_mercado_cambios": "si",
        "acepto_declaracion": "on",
        "firma_nombre_completo": "Persona Ejemplo",
    }
    datos.update(cambios)
    return datos


@pytest.mark.django_db
def test_presentacion_crea_pdf_inmutable_e_impacta_datos_actuales(
    persona_ddjj, tmp_path
):
    nueva_provincia = Provincia.objects.create(nombre="Provincia nueva")
    nuevo_municipio = Municipio.objects.create(
        nombre="Municipio nuevo", provincia=nueva_provincia
    )
    invitacion = crear_invitacion(persona_ddjj)
    form = PasDeclaracionJuradaForm(
        datos_formulario(
            nueva_provincia,
            nuevo_municipio,
            datos_mi_argentina_confirmados="no",
        ),
        persona=persona_ddjj,
    )
    assert form.is_valid(), form.errors

    with override_settings(MEDIA_ROOT=tmp_path):
        declaracion = presentar_ddjj(invitacion, form)
        assert declaracion.archivo_pdf.read().startswith(b"%PDF")

    persona_ddjj.refresh_from_db()
    invitacion.refresh_from_db()
    assert declaracion.version == 1
    assert declaracion.finalizada
    assert invitacion.utilizada
    assert persona_ddjj.provincia == nueva_provincia
    assert persona_ddjj.municipio == nuevo_municipio
    assert persona_ddjj.domicilio == "Calle 123"
    declaracion.domicilio = "No debe cambiar"
    with pytest.raises(ValidationError):
        declaracion.save()
    with pytest.raises(ValidationError):
        declaracion.delete()


@pytest.mark.django_db
def test_presentacion_conserva_literalmente_el_marcado_en_el_pdf(
    persona_ddjj, tmp_path
):
    invitacion = crear_invitacion(persona_ddjj)
    domicilio = "Calle <br/> 123 & 456"
    form = PasDeclaracionJuradaForm(
        datos_formulario(
            persona_ddjj.provincia,
            persona_ddjj.municipio,
            domicilio=domicilio,
        ),
        persona=persona_ddjj,
    )
    assert form.is_valid(), form.errors

    with override_settings(MEDIA_ROOT=tmp_path):
        declaracion = presentar_ddjj(invitacion, form)
        texto_pdf = PdfReader(declaracion.archivo_pdf).pages[0].extract_text()

    assert domicilio in texto_pdf


@pytest.mark.django_db
def test_nueva_presentacion_conserva_anterior_y_pasa_a_ser_vigente(
    persona_ddjj, tmp_path
):
    with override_settings(MEDIA_ROOT=tmp_path):
        for numero in (1, 2):
            invitacion = crear_invitacion(persona_ddjj)
            form = PasDeclaracionJuradaForm(
                datos_formulario(
                    persona_ddjj.provincia,
                    persona_ddjj.municipio,
                    domicilio=f"Calle {numero}",
                ),
                persona=persona_ddjj,
            )
            assert form.is_valid(), form.errors
            presentar_ddjj(invitacion, form)

    versiones = list(
        persona_ddjj.declaraciones_juradas.values_list("version", flat=True)
    )
    assert versiones == [2, 1]
    assert persona_ddjj.declaracion_jurada_vigente.version == 2
    assert PasDeclaracionJurada.objects.count() == 2


@pytest.mark.django_db
def test_enlace_publico_es_de_un_solo_uso(client, persona_ddjj, tmp_path):
    invitacion = crear_invitacion(persona_ddjj)
    url = reverse("pas_ddjj_formulario", args=[invitacion.token])

    assert client.get(url).status_code == 200
    with override_settings(MEDIA_ROOT=tmp_path):
        respuesta = client.post(
            url,
            datos_formulario(persona_ddjj.provincia, persona_ddjj.municipio),
        )

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("pas_ddjj_confirmacion")
    assert client.get(url).status_code == 410


@pytest.mark.django_db
def test_confirmacion_es_generica_y_no_redirige(client, persona_ddjj, tmp_path):
    invitacion = crear_invitacion(persona_ddjj)
    form = PasDeclaracionJuradaForm(
        datos_formulario(persona_ddjj.provincia, persona_ddjj.municipio),
        persona=persona_ddjj,
    )
    assert form.is_valid(), form.errors
    with override_settings(MEDIA_ROOT=tmp_path):
        declaracion = presentar_ddjj(invitacion, form)

    respuesta = client.get(reverse("pas_ddjj_confirmacion"))

    assert respuesta.status_code == 200
    assert b">OK</button>" in respuesta.content
    assert b"ddjj-countdown" not in respuesta.content
    assert b"pas_ddjj_confirmacion.js" not in respuesta.content
    assert b"panel-control" not in respuesta.content
    assert str(declaracion.pk).encode() not in respuesta.request["PATH_INFO"].encode()


@pytest.mark.django_db
def test_descarga_requiere_autenticacion_y_permiso(client, persona_ddjj, tmp_path):
    invitacion = crear_invitacion(persona_ddjj)
    form = PasDeclaracionJuradaForm(
        datos_formulario(persona_ddjj.provincia, persona_ddjj.municipio),
        persona=persona_ddjj,
    )
    assert form.is_valid()
    with override_settings(MEDIA_ROOT=tmp_path):
        declaracion = presentar_ddjj(invitacion, form)
        url = reverse("pas_ddjj_descargar", args=[declaracion.pk])
        respuesta_anonima = client.get(url)
        assert respuesta_anonima.status_code in (302, 403)

        usuario = get_user_model().objects.create_superuser(
            username="ddjj-admin",
            email="ddjj-admin@example.test",
            password="test-pass",
        )
        client.force_login(usuario)
        respuesta = client.get(url)
        assert respuesta.status_code == 200
        assert respuesta["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_pdf_ddjj_no_se_sirve_por_media_directo(client):
    respuesta = client.get("/media/pas/ddjj/30111222/2026/archivo.pdf")

    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_confirmar_datos_conserva_valores_pas_existentes_y_completa_faltantes(
    persona_ddjj,
):
    otra_provincia = Provincia.objects.create(nombre="Provincia manipulada")
    otro_municipio = Municipio.objects.create(
        nombre="Municipio manipulado", provincia=otra_provincia
    )
    form = PasDeclaracionJuradaForm(
        datos_formulario(otra_provincia, otro_municipio),
        persona=persona_ddjj,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["provincia"] == persona_ddjj.provincia
    assert form.cleaned_data["municipio"] == persona_ddjj.municipio
    assert form.cleaned_data["domicilio"] == "Calle 123"


@pytest.mark.django_db
def test_rechazar_datos_exige_todos_los_campos_editables(persona_ddjj):
    form = PasDeclaracionJuradaForm(
        datos_formulario(
            persona_ddjj.provincia,
            persona_ddjj.municipio,
            datos_mi_argentina_confirmados="no",
            domicilio="",
            correo_electronico="",
        ),
        persona=persona_ddjj,
    )

    assert not form.is_valid()
    assert "domicilio" in form.errors
    assert "correo_electronico" in form.errors


@pytest.mark.django_db
def test_respuestas_dependientes_ocultas_se_descartan(persona_ddjj):
    form = PasDeclaracionJuradaForm(
        datos_formulario(
            persona_ddjj.provincia,
            persona_ddjj.municipio,
            embarazada="no",
            controles_embarazo_cumplidos="si",
            hijos_menores_a_cargo="no",
            vacunacion_cumplida="si",
            regularidad_escolar_acreditada="si",
        ),
        persona=persona_ddjj,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["controles_embarazo_cumplidos"] == ""
    assert form.cleaned_data["vacunacion_cumplida"] == ""
    assert form.cleaned_data["regularidad_escolar_acreditada"] == ""


@pytest.mark.django_db
def test_formulario_muestra_foto_de_datos_pas(client, persona_ddjj):
    persona_ddjj.domicilio = "Domicilio visible 123"
    persona_ddjj.correo_electronico = "visible@example.test"
    persona_ddjj.telefono_celular = "11 4444 5555"
    persona_ddjj.save()
    invitacion = crear_invitacion(persona_ddjj)

    respuesta = client.get(reverse("pas_ddjj_formulario", args=[invitacion.token]))

    assert respuesta.status_code == 200
    assert b"Domicilio visible 123" in respuesta.content
    assert b"visible@example.test" in respuesta.content
    assert b"11 4444 5555" in respuesta.content
    assert b"data-data-step" in respuesta.content


@pytest.mark.django_db
def test_endpoint_publico_filtra_municipios_por_provincia(client, persona_ddjj):
    otra_provincia = Provincia.objects.create(nombre="Otra provincia")
    incluido = Municipio.objects.create(
        nombre="Municipio incluido", provincia=otra_provincia
    )
    Municipio.objects.create(
        nombre="Municipio excluido", provincia=persona_ddjj.provincia
    )
    invitacion = crear_invitacion(persona_ddjj)

    respuesta = client.get(
        reverse("pas_ddjj_municipios", args=[invitacion.token]),
        {"provincia_id": otra_provincia.pk},
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == [{"id": incluido.pk, "nombre": "Municipio incluido"}]


@pytest.mark.django_db
@override_settings(DOMINIO="https://qa.sisoc.example")
def test_invitacion_construye_url_segun_el_ambiente(persona_ddjj):
    invitacion = crear_invitacion(persona_ddjj)

    assert persona_ddjj.invitacion_ddjj_vigente == invitacion
    assert invitacion.get_formulario_url() == (
        f"https://qa.sisoc.example/pas/ddjj/formulario/{invitacion.token}"
    )
    assert invitacion.get_formulario_url("http://localhost:8002/") == (
        f"http://localhost:8002/pas/ddjj/formulario/{invitacion.token}"
    )


def test_resumen_final_incluye_todas_las_respuestas_si_no():
    javascript = (Path(settings.BASE_DIR) / "static/custom/js/pas_ddjj.js").read_text(
        encoding="utf-8"
    )

    for campo in (
        "embarazada",
        "controles_embarazo_cumplidos",
        "hijos_menores_a_cargo",
        "vacunacion_cumplida",
        "regularidad_escolar_acreditada",
        "gastos_bajo_limite_smvm",
        "no_accedio_mercado_cambios",
    ):
        assert f'["{campo}",' in javascript
    assert 'selected.closest("label")' in javascript


@pytest.mark.django_db
def test_formulario_versiona_javascript_del_resumen(client, persona_ddjj):
    invitacion = crear_invitacion(persona_ddjj)

    respuesta = client.get(reverse("pas_ddjj_formulario", args=[invitacion.token]))

    assert respuesta.status_code == 200
    assert b"pas_ddjj.js?v=20260831" in respuesta.content
    assert b"pas_ddjj.css?v=20260831" in respuesta.content


def test_resumen_final_no_tiene_altura_fija():
    css = (Path(settings.BASE_DIR) / "static/custom/css/pas_ddjj.css").read_text(
        encoding="utf-8"
    )

    regla = css.split(".pas-ddjj-summary {", 1)[1].split("}", 1)[0]
    assert "height: auto" in regla
    assert "height: 225px" not in regla
