from importlib import import_module

import pytest
from django.contrib.auth.models import Group, Permission
from django.test import RequestFactory
from django.urls import reverse

from admisiones.forms.templates_informe_tecnico_forms import (
    PlantillaInformeTecnicoForm,
    PlantillaInformeTecnicoVersionForm,
)
from admisiones.models.admisiones import (
    Admision,
    IncidenciaTemplateInformeTecnico,
    IncidenciaTemplateInformeTecnicoCaso,
    PlantillaInformeTecnico,
    PlantillaInformeTecnicoPublicacion,
    TipoConvenio,
    VariableTemplateInformeTecnico,
)
from admisiones.services.templates_informe_tecnico_service import (
    PlantillaInformeTecnicoService,
)
from admisiones.views.templates_informe_tecnico import PlantillaInformeTecnicoListView


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(
        username="gestor-templates",
        password="secret",
    )


@pytest.fixture
def tipo_convenio():
    return TipoConvenio.objects.create(nombre="Organización Base")


def _datos_incorporacion(tipo_convenio, nombre="Incorporación Ex PNUD"):
    return {
        "nombre": nombre,
        "descripcion": "Template de prueba",
        "tipo_admision": "incorporacion",
        "tipo_convenio": tipo_convenio,
        "es_ex_pnud": "si",
        "estado_convenio_pnud": "vigente",
        "tipo_renovacion": None,
        "estado_financiamiento": None,
    }


@pytest.mark.django_db
def test_formulario_muestra_solo_los_tipos_de_convenio_permitidos():
    personeria_juridica = TipoConvenio.objects.create(nombre="Personería Jurídica")
    personeria_eclesiastica = TipoConvenio.objects.create(
        nombre="Personería Jurídica Eclesiástica"
    )
    asociacion_de_hecho = TipoConvenio.objects.create(nombre="Organización Base")
    TipoConvenio.objects.create(nombre="Sin uso")

    form = PlantillaInformeTecnicoForm()
    campo_tipo_convenio = form.fields["tipo_convenio"]
    etiquetas = dict(campo_tipo_convenio.choices)

    assert set(campo_tipo_convenio.queryset.values_list("pk", flat=True)) == {
        personeria_juridica.pk,
        personeria_eclesiastica.pk,
        asociacion_de_hecho.pk,
    }
    assert etiquetas[personeria_juridica.pk] == "Personería jurídica"
    assert etiquetas[personeria_eclesiastica.pk] == "Personería jurídica eclesiástica"
    assert etiquetas[asociacion_de_hecho.pk] == "Asociación de hecho"


@pytest.mark.django_db
def test_listado_filtra_la_combinacion_de_renovacion():
    convenio = TipoConvenio.objects.create(nombre="Personería Jurídica")
    coincidencia = PlantillaInformeTecnico.objects.create(
        nombre="Primera renovación finalizada",
        tipo_admision="renovacion",
        tipo_convenio=convenio,
        tipo_renovacion="primera",
        estado_financiamiento="finalizado",
    )
    PlantillaInformeTecnico.objects.create(
        nombre="Segunda renovación vigente",
        tipo_admision="renovacion",
        tipo_convenio=convenio,
        tipo_renovacion="segunda_o_posterior",
        estado_financiamiento="vigente",
    )

    request = RequestFactory().get(
        reverse("gestor_templates_listar"),
        {
            "estado": "activa",
            "tipo_admision": "renovacion",
            "tipo_convenio": convenio.pk,
            "tipo_renovacion": "primera",
            "estado_financiamiento": "finalizado",
        },
    )
    view = PlantillaInformeTecnicoListView()
    view.request = request

    assert list(view.get_queryset()) == [coincidencia]


@pytest.mark.django_db
def test_formulario_rechaza_tipo_de_convenio_fuera_del_catalogo_permitido():
    tipo_fuera_de_catalogo = TipoConvenio.objects.create(nombre="Sin uso")

    form = PlantillaInformeTecnicoForm(
        data={
            "nombre": "Template no permitido",
            "descripcion": "",
            "tipo_admision": "incorporacion",
            "tipo_convenio": tipo_fuera_de_catalogo.pk,
            "es_ex_pnud": "no",
            "estado_convenio_pnud": "",
            "tipo_renovacion": "",
            "estado_financiamiento": "",
        }
    )

    assert not form.is_valid()
    assert "tipo_convenio" in form.errors


def test_formulario_version_conserva_formato_docx_y_limpia_html_activo():
    form = PlantillaInformeTecnicoVersionForm(
        data={
            "contenido_html": (
                '<p style="text-align: justify; color: rgb(1, 2, 3)" '
                'onclick="alert(1)"><strong>Informe</strong> '
                "{{ informe.nombre_organizacion }}<script>alert(1)</script>"
                '<a href="javascript:alert(1)">Vínculo</a></p>'
                '<table><tbody><tr><td colspan="2">Dato</td></tr></tbody></table>'
                '<img src="https://ejemplo.test/imagen.png" />'
            ),
            "observaciones": "",
        }
    )

    assert form.is_valid()

    contenido = form.cleaned_data["contenido_html"]
    assert '<p style="text-align: justify; color: rgb(1, 2, 3)">' in contenido
    assert "<strong>Informe</strong>" in contenido
    assert "{{ informe.nombre_organizacion }}" in contenido
    assert (
        '<table><tbody><tr><td colspan="2">Dato</td></tr></tbody></table>' in contenido
    )
    assert "<a>Vínculo</a>" in contenido
    assert "onclick" not in contenido
    assert "javascript:" not in contenido
    assert "<script" not in contenido
    assert "<img" not in contenido


@pytest.mark.django_db
def test_crear_plantilla_genera_codigo_y_primera_version(usuario, tipo_convenio):
    plantilla, version = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )

    assert plantilla.codigo == f"IT-{plantilla.pk:06d}"
    assert version.numero == 1
    assert version.estado == "borrador"
    assert plantilla.clave_condiciones == (
        f"incorporacion|convenio:{tipo_convenio.pk}|ex_pnud:si|estado_pnud:vigente"
    )


@pytest.mark.django_db
def test_reutiliza_la_version_en_preparacion_en_lugar_de_duplicarla(
    usuario,
    tipo_convenio,
):
    plantilla, borrador = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )

    misma_version, mensaje = PlantillaInformeTecnicoService.crear_version_borrador(
        plantilla,
        usuario,
    )

    assert misma_version.pk == borrador.pk
    assert "ya existe una versión en preparación" in mensaje.lower()
    assert plantilla.versiones.filter(estado="borrador").count() == 1


@pytest.mark.django_db
def test_descartar_version_en_preparacion_elimina_solo_el_borrador(
    usuario,
    tipo_convenio,
):
    plantilla, borrador = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )

    exito, _ = PlantillaInformeTecnicoService.descartar_borrador(borrador, usuario)

    assert exito
    assert not plantilla.versiones.filter(pk=borrador.pk).exists()


@pytest.mark.django_db
def test_publicar_nueva_version_inactiva_la_anterior(usuario, tipo_convenio):
    plantilla, version_uno = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )
    PlantillaInformeTecnicoService.guardar_borrador(
        version_uno,
        {"contenido_html": "<p>Versión uno</p>", "observaciones": ""},
        usuario,
    )
    assert PlantillaInformeTecnicoService.publicar_version(version_uno, usuario)[0]

    version_dos, _ = PlantillaInformeTecnicoService.crear_version_borrador(
        plantilla,
        usuario,
        origen=version_uno,
    )
    PlantillaInformeTecnicoService.guardar_borrador(
        version_dos,
        {"contenido_html": "<p>Versión dos</p>", "observaciones": "actualizada"},
        usuario,
    )
    assert PlantillaInformeTecnicoService.publicar_version(version_dos, usuario)[0]

    version_uno.refresh_from_db()
    version_dos.refresh_from_db()
    publicacion = PlantillaInformeTecnicoPublicacion.objects.get(plantilla=plantilla)
    assert version_uno.estado == "inactiva"
    assert version_dos.estado == "publicada"
    assert publicacion.version_id == version_dos.pk


@pytest.mark.django_db
def test_no_publica_dos_plantillas_con_la_misma_combinacion(
    usuario,
    tipo_convenio,
):
    primera, primera_version = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio, nombre="Primera"),
        usuario,
    )
    segunda, segunda_version = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio, nombre="Segunda"),
        usuario,
    )
    for version in (primera_version, segunda_version):
        PlantillaInformeTecnicoService.guardar_borrador(
            version,
            {"contenido_html": "<p>Contenido</p>", "observaciones": ""},
            usuario,
        )

    assert PlantillaInformeTecnicoService.publicar_version(primera_version, usuario)[0]
    exito, mensaje = PlantillaInformeTecnicoService.publicar_version(
        segunda_version,
        usuario,
    )

    segunda_version.refresh_from_db()
    assert not exito
    assert primera.codigo in mensaje
    assert segunda_version.estado == "borrador"


@pytest.mark.django_db
def test_inactivar_plantilla_retira_la_publicacion(usuario, tipo_convenio):
    plantilla, version = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )
    PlantillaInformeTecnicoService.guardar_borrador(
        version,
        {"contenido_html": "<p>Contenido</p>", "observaciones": ""},
        usuario,
    )
    PlantillaInformeTecnicoService.publicar_version(version, usuario)

    assert PlantillaInformeTecnicoService.inactivar_plantilla(plantilla, usuario)[0]

    plantilla.refresh_from_db()
    version.refresh_from_db()
    assert plantilla.estado == "inactiva"
    assert version.estado == "inactiva"
    assert not PlantillaInformeTecnicoPublicacion.objects.filter(
        plantilla=plantilla
    ).exists()


@pytest.mark.django_db
def test_resuelve_la_version_publicada_desde_las_validaciones_de_admision(
    usuario,
    tipo_convenio,
):
    plantilla, version = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )
    PlantillaInformeTecnicoService.guardar_borrador(
        version,
        {
            "contenido_html": "<p>{{ informe.nombre_organizacion }}</p>",
            "observaciones": "",
        },
        usuario,
    )
    VariableTemplateInformeTecnico.objects.create(
        codigo="informe.nombre_organizacion",
        nombre="Nombre de la organización",
        categoria="Organización",
    )
    assert PlantillaInformeTecnicoService.publicar_version(version, usuario)[0]
    admision = Admision.objects.create(
        tipo="incorporacion",
        tipo_convenio=tipo_convenio,
        es_ex_pnud="si",
        estado_convenio_pnud="vigente",
    )

    publicacion, error = (
        PlantillaInformeTecnicoService.resolver_publicacion_para_admision(admision)
    )

    assert error is None
    assert publicacion.plantilla_id == plantilla.pk
    assert publicacion.version_id == version.pk


@pytest.mark.django_db
def test_catalogo_inicial_contiene_las_variables_de_los_templates_actuales():
    migracion = import_module(
        "admisiones.migrations.0073_variabletemplateinformetecnico"
    )
    catalogo = migracion.catalogo_inicial()

    assert len(catalogo) == 106
    assert (
        "informe.nombre_organizacion",
        "Nombre de la organización",
        "Organización",
    ) in catalogo
    assert ("texto_comidas.Desayunos", "Texto de desayunos", "Prestaciones") in catalogo

    migracion_compatibilidad = import_module(
        "admisiones.migrations.0074_variables_compatibilidad_templates_informe_tecnico"
    )
    assert len(migracion_compatibilidad.CATALOGO_COMPATIBILIDAD) == 21
    assert ("nombre_espacio", "Nombre del espacio") in (
        migracion_compatibilidad.CATALOGO_COMPATIBILIDAD
    )


@pytest.mark.django_db
def test_publica_una_variable_plana_compatible(usuario, tipo_convenio):
    plantilla, version = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )
    PlantillaInformeTecnicoService.guardar_borrador(
        version,
        {"contenido_html": "<p>{{ nombre_espacio }}</p>", "observaciones": ""},
        usuario,
    )
    VariableTemplateInformeTecnico.objects.create(
        codigo="nombre_espacio",
        nombre="Nombre del espacio",
        categoria="Compatibilidad con la versión inicial",
    )

    assert PlantillaInformeTecnicoService.publicar_version(version, usuario)[0]


@pytest.mark.django_db
def test_no_publica_una_variable_que_no_esta_activa(usuario, tipo_convenio):
    plantilla, version = PlantillaInformeTecnicoService.crear_plantilla(
        _datos_incorporacion(tipo_convenio),
        usuario,
    )
    PlantillaInformeTecnicoService.guardar_borrador(
        version,
        {
            "contenido_html": "<p>{{ informe.nombre_organizacion }}</p>",
            "observaciones": "",
        },
        usuario,
    )
    VariableTemplateInformeTecnico.objects.create(
        codigo="informe.nombre_organizacion",
        nombre="Nombre de la organización",
        categoria="Organización",
        activo=False,
    )

    exito, mensaje = PlantillaInformeTecnicoService.publicar_version(version, usuario)

    assert not exito
    assert "no están activas en el catálogo" in mensaje


@pytest.mark.django_db
def test_no_resuelve_si_falta_una_validacion_obligatoria(tipo_convenio):
    admision = Admision.objects.create(
        tipo="incorporacion",
        tipo_convenio=tipo_convenio,
        es_ex_pnud="si",
    )

    publicacion, error = (
        PlantillaInformeTecnicoService.resolver_publicacion_para_admision(admision)
    )

    assert publicacion is None
    assert "estado del convenio PNUD" in error


@pytest.mark.django_db
def test_reporte_faltante_agrupa_casos_y_reincide_al_resolver(
    usuario,
    tipo_convenio,
):
    primera_admision = Admision.objects.create(
        tipo="incorporacion",
        tipo_convenio=tipo_convenio,
        es_ex_pnud="si",
        estado_convenio_pnud="vigente",
    )
    segunda_admision = Admision.objects.create(
        tipo="incorporacion",
        tipo_convenio=tipo_convenio,
        es_ex_pnud="si",
        estado_convenio_pnud="vigente",
    )

    incidencia, mensaje = (
        PlantillaInformeTecnicoService.reportar_configuracion_faltante(
            primera_admision,
            None,
            usuario,
        )
    )
    misma_incidencia, segundo_mensaje = (
        PlantillaInformeTecnicoService.reportar_configuracion_faltante(
            segunda_admision,
            None,
            usuario,
        )
    )

    incidencia.refresh_from_db()
    assert "reportada" in mensaje
    assert "reportada" in segundo_mensaje
    assert misma_incidencia.pk == incidencia.pk
    assert incidencia.cantidad_casos == 2
    assert (
        IncidenciaTemplateInformeTecnicoCaso.objects.filter(
            incidencia=incidencia
        ).count()
        == 2
    )

    assert PlantillaInformeTecnicoService.gestionar_incidencia(
        incidencia,
        {
            "estado": "resuelta",
            "plantilla": None,
            "observaciones": "Configuración atendida.",
        },
        usuario,
    )[0]
    reincidencia, _ = PlantillaInformeTecnicoService.reportar_configuracion_faltante(
        primera_admision,
        None,
        usuario,
    )

    assert reincidencia.pk != incidencia.pk
    assert reincidencia.incidencia_anterior_id == incidencia.pk
    assert reincidencia.cantidad_casos == 1


@pytest.mark.django_db
def test_gestor_templates_exige_permiso_y_renderiza_el_listado(client, usuario):
    url = reverse("gestor_templates_listar")
    client.force_login(usuario)
    assert client.get(url).status_code == 403

    permiso = Permission.objects.get(
        content_type__app_label="admisiones",
        codename="gestionar_templates_informe_tecnico",
    )
    grupo_gestor, _ = Group.objects.get_or_create(name="Gestor de templates")
    grupo_gestor.permissions.add(permiso)
    usuario.groups.add(grupo_gestor)
    usuario = type(usuario).objects.get(pk=usuario.pk)
    client.force_login(usuario)

    response = client.get(url)
    assert response.status_code == 200
    contenido_listado = response.content.decode()
    assert "Gestor de templates" in contenido_listado
    assert "Variables documentales" in contenido_listado
    assert "Incidencias" in contenido_listado

    incidencias = client.get(reverse("gestor_templates_incidencias_listar"))
    assert incidencias.status_code == 200
    assert "Configuraciones faltantes" in incidencias.content.decode()

    variables = client.get(reverse("gestor_templates_variables_listar"))
    assert variables.status_code == 200
    assert "Variables documentales" in variables.content.decode()

    incidencia = IncidenciaTemplateInformeTecnico.objects.create(
        clave_condiciones="incorporacion|convenio:1|ex_pnud:no|estado_pnud:-",
        clave_abierta="incorporacion|convenio:1|ex_pnud:no|estado_pnud:-",
        condiciones={},
        creado_por=usuario,
        modificado_por=usuario,
    )
    detalle = client.get(
        reverse("gestor_templates_incidencia_detalle", args=[incidencia.pk])
    )
    assert detalle.status_code == 200
    assert incidencia.codigo in detalle.content.decode()
