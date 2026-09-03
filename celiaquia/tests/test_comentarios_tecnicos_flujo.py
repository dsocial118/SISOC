"""Flujo de comentarios técnicos: endpoints y publicación en Subsanar/Rechazar.

Cubre las fases 3 y 4 del issue #2318: el alta estructurada por endpoint, la
previsualización del motivo, y cómo Subsanar/Rechazar arman el motivo en backend
y publican a la Provincia las observaciones con ``Sí``.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from users.models import Profile, ProfileTerritorialScope
from celiaquia.models import (
    AsignacionTecnico,
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    HistorialComentarios,
    HistorialValidacionTecnica,
    RevisionTecnico,
    Subsanacion,
    TipoSubsanacion,
)
from celiaquia.services.comentarios_tecnicos_service import ComentariosTecnicosService

pytestmark = pytest.mark.django_db

CODIGO_RENAPER = "RENAPER_FECHA_NACIMIENTO"
CODIGO_DIAG = "DIAG_DOC_ILEGIBLE"


def _grant(user, codename, model=User, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


@pytest.fixture(name="coordinador")
def fixture_coordinador():
    user = User.objects.create_user(username="coord-ct", password="pass")
    _grant(user, "view_expediente", model=Expediente)
    _grant(user, "role_coordinadorceliaquia", name="Coordinador Celiaquia")
    return user


@pytest.fixture(name="provincia_obj")
def fixture_provincia():
    return Provincia.objects.create(nombre="Prov CT")


@pytest.fixture(name="provincial")
def fixture_provincial(provincia_obj):
    user = User.objects.create_user(username="prov-ct", password="pass")
    _grant(user, "view_expediente", model=Expediente)
    _grant(user, "role_provinciaceliaquia", name="Provincia Celiaquia")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia_obj)
    return user


@pytest.fixture(name="legajo")
def fixture_legajo(coordinador, provincia_obj):
    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    expediente = Expediente.objects.create(
        usuario_provincia=coordinador, estado=estado_exp
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Flujo",
        nombre="Comentario",
        documento="77000111",
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia_obj,
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.PENDIENTE,
    )


def _url_crear(legajo):
    return reverse("legajo_comentario_create", args=[legajo.expediente_id, legajo.pk])


def _url_listar(legajo):
    return reverse("legajo_comentarios_list", args=[legajo.expediente_id, legajo.pk])


def _url_preview(legajo):
    return reverse("legajo_motivo_preview", args=[legajo.expediente_id, legajo.pk])


def _url_revisar(legajo):
    return reverse("legajo_revisar", args=[legajo.expediente_id, legajo.pk])


def _sembrar(legajo, usuario, con_si=True, con_no=True):
    if con_si:
        ComentariosTecnicosService.registrar(
            legajo,
            tipo_documento="RENAPER",
            tiene_observaciones=True,
            observacion_codigo=CODIGO_RENAPER,
            usuario=usuario,
        )
        ComentariosTecnicosService.registrar(
            legajo,
            tipo_documento="CONDICION_DIAGNOSTICA",
            tiene_observaciones=True,
            observacion_codigo=CODIGO_DIAG,
            usuario=usuario,
        )
    if con_no:
        ComentariosTecnicosService.registrar(
            legajo,
            tipo_documento="ANSES",
            tiene_observaciones=False,
            usuario=usuario,
        )


# --- Fase 3: endpoints ----------------------------------------------------


def test_alta_estructurada_por_endpoint(client, coordinador, legajo):
    client.force_login(coordinador)

    response = client.post(
        _url_crear(legajo),
        data={
            "tipo_documento": "RENAPER",
            "tiene_observaciones": "si",
            "observacion_codigo": CODIGO_RENAPER,
        },
    )

    assert response.status_code == 200
    payload = response.json()["comentario"]
    assert payload["es_comentario_tecnico"] is True
    assert payload["tipo_documento"] == "RENAPER"
    assert payload["tiene_observaciones"] is True
    assert payload["es_interno"] is True

    comentario = HistorialComentarios.objects.get(pk=payload["id"])
    assert comentario.tipo_comentario == HistorialComentarios.TIPO_COMENTARIO_TECNICO


def test_alta_estructurada_invalida_devuelve_400(client, coordinador, legajo):
    client.force_login(coordinador)

    response = client.post(
        _url_crear(legajo),
        data={
            "tipo_documento": "ANSES",
            "tiene_observaciones": "si",
            "observacion_codigo": CODIGO_RENAPER,  # código de otro tipo
        },
    )

    assert response.status_code == 400
    assert not ComentariosTecnicosService.historial(legajo).exists()


@pytest.mark.parametrize(
    "permission_code, asignar_tecnico",
    [
        ("role_tecnicoceliaquia", True),
        ("role_coordinadorceliaquia", False),
    ],
)
def test_usuario_territorial_con_rol_nacion_no_accede_a_endpoints_internos(
    client, provincial, legajo, permission_code, asignar_tecnico
):
    """El perfil territorial prevalece sobre roles acumulados de Nación."""
    _grant(provincial, permission_code)
    if asignar_tecnico:
        AsignacionTecnico.objects.create(
            expediente=legajo.expediente, tecnico=provincial
        )
    client.force_login(provincial)

    preview = client.get(_url_preview(legajo))
    crear = client.post(
        _url_crear(legajo),
        data={
            "tipo_documento": "RENAPER",
            "tiene_observaciones": "si",
            "observacion_codigo": CODIGO_RENAPER,
        },
    )

    assert preview.status_code == 403
    assert crear.status_code == 403
    assert not ComentariosTecnicosService.historial(legajo).exists()


def test_alta_libre_sigue_funcionando(client, coordinador, legajo):
    """El formato previo al issue #2318 no se rompe."""
    client.force_login(coordinador)

    response = client.post(
        _url_crear(legajo), data={"comentario": "Observación suelta", "es_interno": "1"}
    )

    assert response.status_code == 200
    comentario = HistorialComentarios.objects.get(
        pk=response.json()["comentario"]["id"]
    )
    assert comentario.tipo_comentario == HistorialComentarios.TIPO_OBSERVACION_GENERAL
    assert comentario.es_comentario_tecnico is False


def test_listado_nacion_ve_los_internos(client, coordinador, legajo):
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    comentarios = client.get(_url_listar(legajo)).json()["comentarios"]

    tecnicos = [c for c in comentarios if c["es_comentario_tecnico"]]
    assert len(tecnicos) == 3
    assert all(c["es_interno"] for c in tecnicos)


@pytest.mark.parametrize(
    "estado,visible",
    [
        # Antes de cualquier acción no hay nada publicado.
        (RevisionTecnico.PENDIENTE, False),
        (RevisionTecnico.SUBSANAR, True),
        # Tras responder, la provincia tiene que poder releer qué le pidieron.
        (RevisionTecnico.SUBSANADO, True),
        (RevisionTecnico.RECHAZADO, True),
        # El historial queda consultable aunque el legajo termine aprobado.
        (RevisionTecnico.APROBADO, True),
    ],
)
def test_panel_visible_para_provincia_segun_estado(
    client, coordinador, legajo, estado, visible
):
    legajo.revision_tecnico = estado
    legajo.save(update_fields=["revision_tecnico"])
    client.force_login(coordinador)

    response = client.get(reverse("expediente_detail", args=[legajo.expediente_id]))
    item = next(
        i for i in response.context["legajos_enriquecidos"] if i.pk == legajo.pk
    )

    assert item.comentarios_visibles_provincia is visible


def test_superusuario_no_figura_como_provincia(client, legajo):
    """Un superusuario tiene todos los permisos, incluido el rol provincial:
    el autor se etiqueta por alcance territorial, no por permiso."""
    admin = User.objects.create_superuser(username="admin-ct", password="pass")
    ComentariosTecnicosService.registrar(
        legajo,
        tipo_documento="RENAPER",
        tiene_observaciones=True,
        observacion_codigo=CODIGO_RENAPER,
        usuario=admin,
    )
    client.force_login(admin)

    comentarios = client.get(_url_listar(legajo)).json()["comentarios"]

    assert [c["es_provincia"] for c in comentarios] == [False]


def test_listado_provincia_no_ve_comentarios_sin_publicar(
    client, coordinador, provincial, legajo
):
    _sembrar(legajo, coordinador)
    client.force_login(provincial)

    assert client.get(_url_listar(legajo)).json()["comentarios"] == []


def test_listado_provincia_deduplica_las_observaciones_publicadas(
    client, coordinador, provincial, legajo
):
    _sembrar(legajo, coordinador, con_no=False)
    # Misma observación registrada dos veces: el historial la conserva, la
    # Provincia la ve una sola vez.
    ComentariosTecnicosService.registrar(
        legajo,
        tipo_documento="RENAPER",
        tiene_observaciones=True,
        observacion_codigo=CODIGO_RENAPER,
        usuario=coordinador,
    )
    ComentariosTecnicosService.publicar(legajo, usuario=coordinador)

    client.force_login(coordinador)
    assert len(client.get(_url_listar(legajo)).json()["comentarios"]) == 3

    client.force_login(provincial)
    assert len(client.get(_url_listar(legajo)).json()["comentarios"]) == 2


def test_preview_devuelve_las_lineas_concatenadas(client, coordinador, legajo):
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    payload = client.get(_url_preview(legajo)).json()

    assert payload["tiene_observaciones"] is True
    assert len(payload["lineas"]) == 2
    assert payload["lineas"][0].startswith("RENAPER: ")
    assert "Sin observaciones." not in payload["motivo"]


def test_preview_sin_observaciones(client, coordinador, legajo):
    _sembrar(legajo, coordinador, con_si=False)
    client.force_login(coordinador)

    payload = client.get(_url_preview(legajo)).json()

    assert payload["tiene_observaciones"] is False
    assert payload["motivo"] == ""


def test_preview_denegado_para_provincia(client, provincial, legajo):
    client.force_login(provincial)

    assert client.get(_url_preview(legajo)).status_code == 403


# --- Detalle del expediente: catálogo para el formulario ------------------


def test_detalle_embebe_el_catalogo_de_observaciones(client, coordinador, legajo):
    """El desplegable de observaciones se filtra en el cliente: el catálogo
    tiene que viajar embebido en la página."""
    client.force_login(coordinador)

    response = client.get(reverse("expediente_detail", args=[legajo.expediente_id]))
    html = response.content.decode()

    assert response.status_code == 200
    assert 'id="catalogo-comentarios-tecnicos"' in html
    catalogo = response.context["catalogo_comentarios_tecnicos"]
    assert set(catalogo) == {"RENAPER", "ANSES", "CONDICION_DIAGNOSTICA"}
    assert catalogo["RENAPER"][-1]["libre"] is True
    # Los tres tipos alimentan el primer desplegable del formulario.
    assert len(response.context["tipos_documento_comentario"]) == 3


# --- Fase 4: Subsanar y Rechazar -----------------------------------------


def test_subsanar_arma_el_motivo_y_publica(client, coordinador, legajo):
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    response = client.post(
        _url_revisar(legajo),
        data={"accion": "SUBSANAR", "texto_libre": "Se adjunta nota."},
    )

    assert response.status_code == 200
    assert response.json()["comentarios_publicados"] == 2

    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.SUBSANAR
    # Motivo armado en backend: las dos observaciones con Sí + el texto libre.
    assert legajo.subsanacion_motivo.startswith("RENAPER: ")
    assert "Condición diagnóstica: " in legajo.subsanacion_motivo
    assert legajo.subsanacion_motivo.endswith("Se adjunta nota.")
    assert "Sin observaciones." not in legajo.subsanacion_motivo

    # Los comentarios con Sí quedan publicados; el No sigue interno.
    tecnicos = ComentariosTecnicosService.historial(legajo)
    assert tecnicos.filter(tiene_observaciones=True, es_interno=False).count() == 2
    assert tecnicos.filter(tiene_observaciones=False, es_interno=True).count() == 1


def test_subsanar_deriva_las_observaciones_del_legajo(client, coordinador, legajo):
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    client.post(_url_revisar(legajo), data={"accion": "SUBSANAR"})

    subsanacion = Subsanacion.objects.get(legajo=legajo)
    tipos = sorted(o.tipo for o in subsanacion.observaciones.all())
    # RENAPER mapea a RENAPER; condición diagnóstica, a DOCUMENTACION.
    assert tipos == [TipoSubsanacion.DOCUMENTACION, TipoSubsanacion.RENAPER]
    assert legajo.subsanaciones.count() == 1


def test_subsanar_sin_observaciones_ni_texto_libre_falla(client, coordinador, legajo):
    _sembrar(legajo, coordinador, con_si=False)
    client.force_login(coordinador)

    response = client.post(_url_revisar(legajo), data={"accion": "SUBSANAR"})

    assert response.status_code == 400
    legajo.refresh_from_db()
    # El legajo queda intacto: no cambia de estado ni se crea la subsanación.
    assert legajo.revision_tecnico == RevisionTecnico.PENDIENTE
    assert not legajo.subsanaciones.exists()
    assert (
        ComentariosTecnicosService.historial(legajo).filter(es_interno=False).count()
        == 0
    )


def test_subsanar_sin_observaciones_acepta_solo_texto_libre(
    client, coordinador, legajo
):
    _sembrar(legajo, coordinador, con_si=False)
    client.force_login(coordinador)

    response = client.post(
        _url_revisar(legajo),
        data={"accion": "SUBSANAR", "texto_libre": "Motivo puntual."},
    )

    assert response.status_code == 200
    legajo.refresh_from_db()
    assert legajo.subsanacion_motivo == "Motivo puntual."


def test_subsanar_con_ui_previa_sigue_funcionando(client, coordinador, legajo):
    """Sin comentarios técnicos, el POST anterior (motivo + motivos) sigue vivo."""
    client.force_login(coordinador)

    response = client.post(
        _url_revisar(legajo),
        data={
            "accion": "SUBSANAR",
            "motivo": "Revisar documentación",
            "motivos": ["DOCUMENTACION"],
        },
    )

    assert response.status_code == 200
    legajo.refresh_from_db()
    assert legajo.subsanacion_motivo == "Revisar documentación"
    subsanacion = Subsanacion.objects.get(legajo=legajo)
    assert [o.tipo for o in subsanacion.observaciones.all()] == [
        TipoSubsanacion.DOCUMENTACION
    ]


def test_motivo_largo_no_se_trunca(client, coordinador, legajo):
    """La concatenación supera los 500 caracteres que truncaba el flujo previo."""
    for indice in range(4):
        ComentariosTecnicosService.registrar(
            legajo,
            tipo_documento="CONDICION_DIAGNOSTICA",
            tiene_observaciones=True,
            observacion_codigo="OTROS",
            observacion_libre=f"Observación {indice}: " + "x" * 200,
            usuario=coordinador,
        )
    client.force_login(coordinador)

    client.post(_url_revisar(legajo), data={"accion": "SUBSANAR"})

    legajo.refresh_from_db()
    assert len(legajo.subsanacion_motivo) > 500
    historial = HistorialValidacionTecnica.objects.get(legajo=legajo)
    assert len(historial.motivo) > 500


def test_rechazar_arma_el_motivo_y_publica(client, coordinador, legajo):
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    response = client.post(
        _url_revisar(legajo),
        data={"accion": "RECHAZAR", "texto_libre": "No cumple requisitos."},
    )

    assert response.status_code == 200
    assert response.json()["comentarios_publicados"] == 2

    legajo.refresh_from_db()
    assert legajo.revision_tecnico == "RECHAZADO"

    historial = HistorialValidacionTecnica.objects.get(legajo=legajo)
    assert historial.motivo.startswith("RENAPER: ")
    assert historial.motivo.endswith("No cumple requisitos.")


def test_rechazar_sin_observaciones_ni_texto_libre_falla(client, coordinador, legajo):
    client.force_login(coordinador)

    response = client.post(_url_revisar(legajo), data={"accion": "RECHAZAR"})

    assert response.status_code == 400
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.PENDIENTE


def test_aprobar_no_publica_comentarios(client, coordinador, legajo):
    """Validar no cambia: no exige comentarios ni los publica."""
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    response = client.post(_url_revisar(legajo), data={"accion": "APROBAR"})

    assert response.status_code == 200
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == "APROBADO"
    assert (
        ComentariosTecnicosService.historial(legajo).filter(es_interno=False).count()
        == 0
    )
