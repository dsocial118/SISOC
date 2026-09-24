"""Documentación complementaria de Nación al solicitar una subsanación (issue #2523).

Nación puede adjuntar archivos junto con el pedido de subsanación. Son opcionales,
cuelgan de la solicitud entera (no de una observación puntual) y la Provincia los
ve, pero **no cuentan como respuesta suya**: esa distinción es la que cubre la
mayor parte de este archivo.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    OrigenArchivoSubsanacion,
    RevisionTecnico,
    Subsanacion,
    SubsanacionArchivo,
)
from celiaquia.services.comentarios_tecnicos_service import ComentariosTecnicosService
from celiaquia.services.subsanacion_service import SubsanacionService
from celiaquia.validators import (
    COMPLEMENTARIA_ACCEPT_ATTR,
    COMPLEMENTARIA_MAX_ARCHIVOS,
    COMPLEMENTARIA_MAX_SIZE_MB,
)

pytestmark = pytest.mark.django_db

CODIGO_ANSES = "ANSES_CODEM_VENCIDO"


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
    user = User.objects.create_user(username="coord-dc", password="pass")
    _grant(user, "view_expediente", model=Expediente)
    _grant(user, "role_coordinadorceliaquia", name="Coordinador Celiaquia")
    return user


@pytest.fixture(name="legajo")
def fixture_legajo(coordinador):
    provincia = Provincia.objects.create(nombre="Prov DC")
    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO_DC")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE_DC")
    expediente = Expediente.objects.create(
        usuario_provincia=coordinador, estado=estado_exp
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Complementaria",
        nombre="Doc",
        documento="77000222",
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.PENDIENTE,
    )
    ComentariosTecnicosService.registrar(
        legajo,
        tipo_documento="ANSES",
        tiene_observaciones=True,
        observacion_codigo=CODIGO_ANSES,
        usuario=coordinador,
    )
    return legajo


def _url_revisar(legajo):
    return reverse("legajo_revisar", args=[legajo.expediente_id, legajo.pk])


def _pdf(nombre="constancia.pdf", contenido=b"%PDF-1.4 fake"):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


def _subsanar(client, legajo, archivos=None, **extra):
    data = {"accion": "SUBSANAR"}
    data.update(extra)
    if archivos is not None:
        data["documentacion_complementaria"] = archivos
    return client.post(_url_revisar(legajo), data=data)


# --- Alta ------------------------------------------------------------------


def test_subsanar_guarda_la_documentacion_con_origen_nacion(
    client, coordinador, legajo
):
    client.force_login(coordinador)

    response = _subsanar(client, legajo, archivos=[_pdf("a.pdf"), _pdf("b.pdf")])

    assert response.status_code == 200
    assert response.json()["documentacion_complementaria"] == 2

    subsanacion = Subsanacion.objects.get(legajo=legajo)
    archivos = subsanacion.archivos.all()
    assert archivos.count() == 2
    for archivo in archivos:
        assert archivo.origen == OrigenArchivoSubsanacion.NACION
        assert archivo.usuario == coordinador
        # No cuelga de una observación puntual: acompaña al pedido entero.
        assert archivo.observacion is None


def test_subsanar_sin_documentacion_no_se_bloquea(client, coordinador, legajo):
    """La carga es opcional y su ausencia no puede frenar la acción."""
    client.force_login(coordinador)

    response = _subsanar(client, legajo)

    assert response.status_code == 200
    assert response.json()["documentacion_complementaria"] == 0
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.SUBSANAR


# --- La distinción con la respuesta de la Provincia -------------------------


def test_la_documentacion_de_nacion_no_cuenta_como_respuesta(
    client, coordinador, legajo
):
    """El caso que motiva el campo `origen`.

    `tiene_evidencia` habilita el botón con el que la Provincia confirma la
    subsanación. Si contara los archivos de Nación, pedir subsanación con
    documentación adjunta la daría por respondida sin que la Provincia suba
    nada.
    """
    client.force_login(coordinador)

    _subsanar(client, legajo, archivos=[_pdf()])

    legajo.refresh_from_db()
    assert SubsanacionService.tiene_evidencia(legajo) is False
    sin_evidencia = SubsanacionService.legajos_sin_evidencia(legajo.expediente)
    assert [item.pk for item in sin_evidencia] == [legajo.pk]


def test_la_respuesta_de_la_provincia_si_cuenta_como_evidencia(
    client, coordinador, legajo
):
    client.force_login(coordinador)
    _subsanar(client, legajo, archivos=[_pdf()])
    legajo.refresh_from_db()

    SubsanacionService.responder(
        legajo=legajo, archivos=[_pdf("corregido.pdf")], usuario=coordinador
    )

    assert SubsanacionService.tiene_evidencia(legajo) is True
    subsanacion = SubsanacionService.subsanacion_activa(legajo)
    assert len(subsanacion.archivos_de_nacion) == 1
    assert len(subsanacion.archivos_de_provincia) == 1


def test_responder_marca_el_origen_provincia(client, coordinador, legajo):
    client.force_login(coordinador)
    _subsanar(client, legajo)
    legajo.refresh_from_db()

    SubsanacionService.responder(
        legajo=legajo, archivos=[_pdf("corregido.pdf")], usuario=coordinador
    )

    archivo = SubsanacionArchivo.objects.get()
    assert archivo.origen == OrigenArchivoSubsanacion.PROVINCIA


def test_nombre_archivo_no_expone_la_carpeta_de_upload(client, coordinador, legajo):
    """La UI muestra el nombre suelto, no la ruta de `upload_to`."""
    client.force_login(coordinador)
    _subsanar(client, legajo, archivos=[_pdf("constancia-codem.pdf")])

    archivo = SubsanacionArchivo.objects.get()
    assert archivo.archivo.name.startswith("legajos/subsanaciones/")
    assert "/" not in archivo.nombre_archivo
    assert archivo.nombre_archivo.endswith(".pdf")
    assert archivo.nombre_archivo.startswith("constancia-codem")


def test_el_modal_recibe_los_limites_del_backend(client, coordinador, legajo):
    """Los límites se declaran una sola vez, en `celiaquia/validators.py`.

    El modal los usa para el `accept`, para el texto de ayuda y para la
    validación en el cliente, así que tienen que viajar en el contexto en lugar
    de estar escritos a mano en el template.
    """
    client.force_login(coordinador)

    response = client.get(reverse("expediente_detail", args=[legajo.expediente_id]))
    html = response.content.decode()

    assert response.status_code == 200
    assert response.context["complementaria_accept"] == COMPLEMENTARIA_ACCEPT_ATTR
    assert (
        response.context["complementaria_max_archivos"] == COMPLEMENTARIA_MAX_ARCHIVOS
    )
    assert response.context["complementaria_max_mb"] == COMPLEMENTARIA_MAX_SIZE_MB
    assert f'data-max-archivos="{COMPLEMENTARIA_MAX_ARCHIVOS}"' in html
    assert f'data-max-mb="{COMPLEMENTARIA_MAX_SIZE_MB}"' in html


# --- Validación ------------------------------------------------------------


@pytest.mark.parametrize(
    "archivos,fragmento",
    [
        (
            [SimpleUploadedFile("virus.exe", b"x", content_type="application/pdf")],
            "PDF",
        ),
        ([_pdf("grande.pdf", b"x" * (10 * 1024 * 1024 + 1))], "tamaño máximo"),
        ([_pdf(f"f{i}.pdf") for i in range(COMPLEMENTARIA_MAX_ARCHIVOS + 1)], "hasta"),
    ],
    ids=["extension-invalida", "supera-10mb", "demasiados-archivos"],
)
def test_documentacion_invalida_no_subsana(
    client, coordinador, legajo, archivos, fragmento
):
    """Un archivo inválido corta antes de tocar el estado del legajo.

    La validación corre antes de la transacción: el legajo no puede quedar en
    SUBSANAR con la documentación a medias.
    """
    client.force_login(coordinador)

    response = _subsanar(client, legajo, archivos=archivos)

    assert response.status_code == 400
    assert fragmento in response.json()["error"]

    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.PENDIENTE
    assert not Subsanacion.objects.filter(legajo=legajo).exists()
    assert not SubsanacionArchivo.objects.exists()


def test_el_servicio_ignora_los_slots_vacios(coordinador, legajo):
    """El input `multiple` puede mandar entradas vacías si no se eligió nada."""
    subsanacion = Subsanacion.objects.create(legajo=legajo)

    creados = SubsanacionService.adjuntar_documentacion_complementaria(
        subsanacion, [None, ""], usuario=coordinador
    )

    assert creados == []
    assert subsanacion.archivos.count() == 0


def test_el_servicio_valida_antes_de_escribir(coordinador, legajo):
    """Si un archivo del lote es inválido no se guarda ninguno."""
    subsanacion = Subsanacion.objects.create(legajo=legajo)

    with pytest.raises(ValidationError):
        SubsanacionService.adjuntar_documentacion_complementaria(
            subsanacion,
            [_pdf("ok.pdf"), SimpleUploadedFile("no.exe", b"x")],
            usuario=coordinador,
        )

    assert subsanacion.archivos.count() == 0
