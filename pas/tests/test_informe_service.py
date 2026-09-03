import csv
from datetime import date
from io import StringIO
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from core.models import Municipio, Provincia
from core.services.csv_export import CSV_CONTENT_TYPE, UTF8_BOM
from pas.forms import PasInformeGenerarForm
from pas.models import PasEstado, PasHistorialEstado, PasInforme, PasPersona
from pas.services.informe_service import csv_response_for_informe, preview_payload


@pytest.fixture
def catalogo_informe():
    provincia = Provincia.objects.create(nombre="Provincia informe")
    municipio = Municipio.objects.create(
        nombre="Municipio informe", provincia=provincia
    )
    estado = PasEstado.objects.create(nombre="Activo")
    return provincia, municipio, estado


def _crear_personas(catalogo, cantidad):
    provincia, municipio, estado = catalogo
    return [
        PasPersona.objects.create(
            id_persona=indice,
            apellidos=f"Apellido {indice:03d}",
            nombres=f"Nombre {indice:03d}",
            dni=30000000 + indice,
            cuit=f"2030000{indice:04d}",
            provincia=provincia,
            municipio=municipio,
            estado=estado,
        )
        for indice in range(1, cantidad + 1)
    ]


def _form_informe(data=None):
    form = PasInformeGenerarForm(data or {})
    assert form.is_valid(), form.errors
    return form


def _permission(app_label, codename):
    if (app_label, codename) == ("auth", "role_exportar_a_csv"):
        permission, _ = Permission.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Group),
            codename=codename,
            defaults={"name": "Exportar a csv"},
        )
        return permission
    return Permission.objects.get(
        content_type__app_label=app_label,
        codename=codename,
    )


def test_csv_informe_reutiliza_politica_central_con_bom():
    informe = SimpleNamespace(numero="PAS-INF-000001", resultado=[])

    response = csv_response_for_informe(informe)

    assert response["Content-Type"] == CSV_CONTENT_TYPE
    assert response["Content-Disposition"] == (
        'attachment; filename="pas-inf-000001.csv"'
    )
    assert response.content.decode("utf-8").startswith(UTF8_BOM)


def test_csv_informe_neutraliza_formulas_en_datos_importados():
    informe = SimpleNamespace(
        numero="PAS-INF-000001",
        resultado=[
            {
                "apellido": "=HIPERVINCULO()",
                "nombre": "+SUMA(1;1)",
                "cuit": "-1+2",
                "provincia": "@dato",
                "municipio": "Texto seguro",
            }
        ],
    )

    response = csv_response_for_informe(informe)
    rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig"))))
    exported = dict(zip(rows[0], rows[1]))

    assert exported["Apellido"] == "'=HIPERVINCULO()"
    assert exported["Nombre"] == "'+SUMA(1;1)"
    assert exported["CUIT"] == "'-1+2"
    assert exported["Provincia"] == "'@dato"
    assert exported["Municipio"] == "Texto seguro"


@pytest.mark.django_db
def test_preview_cuenta_todo_pero_serializa_solo_el_limite(
    catalogo_informe, monkeypatch
):
    _crear_personas(catalogo_informe, 55)
    serializadas = []

    def row_spy(persona):
        serializadas.append(persona.pk)
        return {"id_persona": persona.id_persona}

    monkeypatch.setattr("pas.services.informe_service._row_persona", row_spy)

    payload = preview_payload(_form_informe(), limit=10)

    assert payload["total"] == 55
    assert payload["total_personas"] == 55
    assert len(payload["rows"]) == 10
    assert len(serializadas) == 10


@pytest.mark.django_db
def test_preview_registros_mantiene_cantidad_de_queries_constante(
    catalogo_informe, django_assert_num_queries
):
    personas = _crear_personas(catalogo_informe, 4)
    estado = catalogo_informe[2]
    for persona in personas:
        PasHistorialEstado.objects.create(persona=persona, estado_nuevo=estado)

    with django_assert_num_queries(4):
        payload = preview_payload(_form_informe())

    assert len(payload["rows"]) == 4
    assert all(row["fecha_ultimo_cambio"] for row in payload["rows"])


@pytest.mark.django_db
def test_preview_cambios_mantiene_cantidad_de_queries_constante(
    catalogo_informe, django_assert_num_queries
):
    personas = _crear_personas(catalogo_informe, 4)
    estado = catalogo_informe[2]
    usuario = get_user_model().objects.create_user(username="operador-informe")
    for persona in personas:
        PasHistorialEstado.objects.create(
            persona=persona,
            estado_nuevo=estado,
            usuario=usuario,
        )

    with django_assert_num_queries(5):
        payload = preview_payload(
            _form_informe(
                {
                    "fecha_cambio_desde": date.today().isoformat(),
                }
            )
        )

    assert payload["modo"] == "cambios"
    assert len(payload["rows"]) == 4
    assert all(row["fecha_ultimo_cambio"] for row in payload["rows"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "method", "permission_codename"),
    [
        ("pas_informe_generar", "get", "add_pasinforme"),
        ("pas_informe_generar", "get", "view_paspersona"),
        ("pas_informe_previsualizar", "post", "add_pasinforme"),
        ("pas_informe_previsualizar", "post", "view_paspersona"),
    ],
)
def test_generacion_y_preview_requieren_lectura_y_generacion(
    client, url_name, method, permission_codename
):
    usuario = get_user_model().objects.create_user(
        username=f"solo-{url_name}-{permission_codename}"
    )
    usuario.user_permissions.add(_permission("pas", permission_codename))
    client.force_login(usuario)

    response = getattr(client, method)(reverse(url_name))

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "missing_permission",
    [
        ("pas", "view_paspersona"),
        ("pas", "view_pasinforme"),
        ("auth", "role_exportar_a_csv"),
    ],
)
def test_descarga_requiere_lectura_de_padron_informe_y_exportacion(
    client, missing_permission
):
    informe = PasInforme.objects.create()
    permisos = [
        ("pas", "view_paspersona"),
        ("pas", "view_pasinforme"),
        ("auth", "role_exportar_a_csv"),
    ]
    usuario = get_user_model().objects.create_user(
        username=f"sin-{missing_permission[1]}"
    )
    usuario.user_permissions.add(
        *[
            _permission(app_label, codename)
            for app_label, codename in permisos
            if (app_label, codename) != missing_permission
        ]
    )
    client.force_login(usuario)

    response = client.get(reverse("pas_informe_descargar", args=[informe.pk]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_descarga_acepta_todos_los_permisos_requeridos(client):
    informe = PasInforme.objects.create()
    usuario = get_user_model().objects.create_user(username="exportador-pas")
    usuario.user_permissions.add(
        _permission("pas", "view_paspersona"),
        _permission("pas", "view_pasinforme"),
        _permission("auth", "role_exportar_a_csv"),
    )
    client.force_login(usuario)

    response = client.get(reverse("pas_informe_descargar", args=[informe.pk]))

    assert response.status_code == 200
    assert response["Content-Type"] == CSV_CONTENT_TYPE


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "requires_pk", "missing_permission"),
    [
        ("pas_informe_listar", False, ("pas", "view_paspersona")),
        ("pas_informe_listar", False, ("pas", "view_pasinforme")),
        ("pas_informe_detalle", True, ("pas", "view_paspersona")),
        ("pas_informe_detalle", True, ("pas", "view_pasinforme")),
    ],
)
def test_listado_y_detalle_requieren_lectura_de_padron_e_informe(
    client, url_name, requires_pk, missing_permission
):
    informe = PasInforme.objects.create(
        resultado=[{"dni": "30000000", "cuit": "20300000001"}]
    )
    permisos = [("pas", "view_paspersona"), ("pas", "view_pasinforme")]
    usuario = get_user_model().objects.create_user(
        username=f"sin-{missing_permission[1]}-{url_name}"
    )
    usuario.user_permissions.add(
        *[
            _permission(app_label, codename)
            for app_label, codename in permisos
            if (app_label, codename) != missing_permission
        ]
    )
    client.force_login(usuario)

    args = [informe.pk] if requires_pk else []
    response = client.get(reverse(url_name, args=args))

    assert response.status_code == 403
