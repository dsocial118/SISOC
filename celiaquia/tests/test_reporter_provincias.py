from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ciudadanos.models import Ciudadano, GrupoFamiliar
from core.models import Provincia
from users.models import Profile

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)


def _permiso(codename):
    """`view_reporte_provincias` es un permiso declarado en `Meta.permissions`;
    se siembra acá por si la base de tests no corrió el `post_migrate`."""
    try:
        return Permission.objects.get(
            content_type__app_label="celiaquia",
            codename=codename,
        )
    except Permission.DoesNotExist:
        content_type = ContentType.objects.get_or_create(
            app_label="celiaquia", model="expediente"
        )[0]
        return Permission.objects.create(
            content_type=content_type,
            codename=codename,
            name=codename,
        )


def _create_user_with_permission(username, provincia=None, es_provincial=False):
    user = User.objects.create_user(username=username, password="pass")
    user.user_permissions.add(_permiso("view_expediente"))
    user.user_permissions.add(_permiso("view_reporte_provincias"))
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = es_provincial
    profile.provincia = provincia
    profile.save()
    return user


@pytest.mark.django_db
def test_reporter_provincias_paginates_results_and_preserves_filters(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = _create_user_with_permission("reporter", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="CREADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")

    for index in range(13):
        expediente = Expediente.objects.create(
            usuario_provincia=user,
            estado=estado_expediente,
            numero_expediente=f"EXP-{index:03d}",
        )
        ciudadano = Ciudadano.objects.create(
            apellido=f"Apellido {index}",
            nombre=f"Nombre {index}",
            documento=20000000 + index,
        )
        ExpedienteCiudadano.objects.create(
            expediente=expediente,
            ciudadano=ciudadano,
            estado=estado_legajo,
            revision_tecnico="APROBADO",
        )

    client.force_login(user)
    response = client.get(
        reverse("reporter_provincias"),
        {
            "revision_tecnico": "APROBADO",
            "resultado_sintys": "",
            "documento_persona": "",
            "page": 2,
        },
    )

    assert response.status_code == 200
    assert response.context["page_obj"].number == 2
    assert response.context["page_obj"].paginator.count == 13
    assert len(response.context["ultimos_casos"]) == 1
    assert response.context["current_querystring"] == "revision_tecnico=APROBADO"
    assert response.context["detalle_desde"] == 13
    assert response.context["detalle_hasta"] == 13
    assert response.context["metricas_principales"][1]["value"] == "100,0%"


@pytest.mark.django_db
def test_reporter_provincias_clasifica_aprobados_por_rol(client):
    """El reporte clasifica los legajos APROBADOS por rol/edad en categorías
    mutuamente excluyentes cuyos subtotales suman el total de aprobados."""
    provincia = Provincia.objects.create(nombre="Mendoza Clasif")
    user = _create_user_with_permission("reporter-clasif", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="ARCHIVO_CARGADO_CLASIF")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
        numero_expediente="EXP-CLASIF-001",
    )

    casos = [
        # (documento, rol, fecha_nacimiento, revision_tecnico)
        (41000001, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(1990, 1, 1), "APROBADO"),
        (41000002, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(1985, 5, 5), "APROBADO"),
        (
            41000003,
            ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE,
            date(1980, 3, 3),
            "APROBADO",
        ),
        (41000004, ExpedienteCiudadano.ROLE_RESPONSABLE, date(1975, 7, 7), "APROBADO"),
        # Menor de edad: cae en "menor" aunque su rol sea beneficiario.
        (41000005, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(2015, 2, 2), "APROBADO"),
        # No aprobado: excluido del conteo.
        (
            41000006,
            ExpedienteCiudadano.ROLE_BENEFICIARIO,
            date(1992, 9, 9),
            "PENDIENTE",
        ),
    ]
    for documento, rol, fnac, revision in casos:
        ciudadano = Ciudadano.objects.create(
            apellido="Test",
            nombre=f"C{documento}",
            documento=documento,
            fecha_nacimiento=fnac,
            provincia=provincia,
        )
        ExpedienteCiudadano.objects.create(
            expediente=expediente,
            ciudadano=ciudadano,
            estado=estado_legajo,
            rol=rol,
            revision_tecnico=revision,
        )

    client.force_login(user)
    response = client.get(reverse("reporter_provincias"))

    assert response.status_code == 200
    clasificacion = response.context["clasificacion_aprobados"]
    counts = {item["code"]: item["count"] for item in clasificacion["items"]}

    assert counts == {
        "beneficiario": 2,
        "doble_rol": 1,
        "responsable": 1,
        "menor": 1,
    }
    assert clasificacion["total"] == 5  # los 5 aprobados, el PENDIENTE no cuenta
    assert sum(counts.values()) == clasificacion["total"]

    content = response.content.decode()
    assert "Clasificación por rol" in content
    assert "Beneficiario únicamente" in content


@pytest.mark.django_db
def test_reporter_provincias_renders_redesigned_sections(client):
    provincia = Provincia.objects.create(nombre="Jujuy")
    user = _create_user_with_permission("reporter-render", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="EN_PROCESO")
    estado_legajo = EstadoLegajo.objects.create(nombre="REVISION")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
        numero_expediente="EXP-RENDER-001",
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Ana",
        documento=30111222,
    )
    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )

    client.force_login(user)
    response = client.get(reverse("reporter_provincias"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Panorama general de legajos por provincia" in content
    assert "Detalle paginado" in content
    assert "reporterQuickSearch" in content
    assert "custom/js/reporter_provincias.js" in content


@pytest.mark.django_db
def test_reporter_provincias_cuenta_duplas_hijo_responsable(client):
    """Las duplas cuentan una unidad por hijo aprobado asociado a un responsable
    aprobado, sin duplicar el conteo de personas ni el total de legajos."""
    provincia = Provincia.objects.create(nombre="Salta Duplas")
    user = _create_user_with_permission("reporter-duplas", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="ARCHIVO_CARGADO_DUPLAS")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
        numero_expediente="EXP-DUPLAS-001",
    )

    def _crear(documento, rol, fnac, revision):
        ciudadano = Ciudadano.objects.create(
            apellido="Dupla",
            nombre=f"C{documento}",
            documento=documento,
            fecha_nacimiento=fnac,
            provincia=provincia,
        )
        ExpedienteCiudadano.objects.create(
            expediente=expediente,
            ciudadano=ciudadano,
            estado=estado_legajo,
            rol=rol,
            revision_tecnico=revision,
        )
        return ciudadano

    # Dupla completa: responsable aprobado + hijo menor aprobado.
    resp_ok = _crear(
        42000001, ExpedienteCiudadano.ROLE_RESPONSABLE, date(1980, 1, 1), "APROBADO"
    )
    hijo_ok = _crear(
        42000002, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(2015, 1, 1), "APROBADO"
    )
    # Responsable rechazado: la dupla no está conformada.
    resp_no = _crear(
        42000003, ExpedienteCiudadano.ROLE_RESPONSABLE, date(1979, 2, 2), "RECHAZADO"
    )
    hijo_sin_resp = _crear(
        42000004, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(2016, 3, 3), "APROBADO"
    )
    # Hijo con dos responsables aprobados: sigue siendo una sola dupla.
    resp_a = _crear(
        42000005, ExpedienteCiudadano.ROLE_RESPONSABLE, date(1978, 4, 4), "APROBADO"
    )
    resp_b = _crear(
        42000006, ExpedienteCiudadano.ROLE_RESPONSABLE, date(1977, 5, 5), "APROBADO"
    )
    hijo_dos = _crear(
        42000007, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(2017, 6, 6), "APROBADO"
    )
    # Beneficiario adulto suelto, sin vínculo familiar.
    _crear(
        42000008, ExpedienteCiudadano.ROLE_BENEFICIARIO, date(1990, 7, 7), "APROBADO"
    )

    for responsable, hijo in [
        (resp_ok, hijo_ok),
        (resp_no, hijo_sin_resp),
        (resp_a, hijo_dos),
        (resp_b, hijo_dos),
    ]:
        GrupoFamiliar.objects.create(
            ciudadano_1=responsable,
            ciudadano_2=hijo,
            vinculo=GrupoFamiliar.RELACION_PADRE,
            conviven=True,
            cuidador_principal=True,
        )

    client.force_login(user)
    response = client.get(reverse("reporter_provincias"))

    assert response.status_code == 200
    clasificacion = response.context["clasificacion_aprobados"]

    # hijo_ok y hijo_dos conforman dupla; hijo_sin_resp no (responsable rechazado).
    assert clasificacion["duplas"] == 2
    assert clasificacion["total"] == 7  # los 7 aprobados; el rechazado no cuenta
    assert clasificacion["personas_unicas"] == 7
    # Beneficiarios alcanzados: total menos los 3 responsables únicamente.
    assert clasificacion["beneficiarios"] == 4
    # Las duplas no se suman al total de legajos ni al de beneficiarios.
    assert clasificacion["duplas"] < clasificacion["total"]

    subtotales = {item["label"]: item["value"] for item in clasificacion["subtotales"]}
    assert subtotales["Duplas hijo-responsable"] == 2
    assert subtotales["Legajos aprobados"] == 7
    assert subtotales["Beneficiarios alcanzados"] == 4

    content = response.content.decode()
    assert "Duplas hijo-responsable" in content
    assert "Personas únicas" in content


@pytest.mark.django_db
def test_reporter_provincias_marca_dupla_en_el_detalle(client):
    """El detalle paginado muestra el rol de cada legajo y marca como dupla sólo
    la fila del hijo aprobado con responsable aprobado."""
    provincia = Provincia.objects.create(nombre="Chaco Detalle")
    user = _create_user_with_permission("reporter-detalle-dupla", provincia=provincia)
    estado_expediente = EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="ARCHIVO_CARGADO_DETALLE")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
        numero_expediente="EXP-DUPLAS-002",
    )

    responsable = Ciudadano.objects.create(
        apellido="DetalleDupla",
        nombre="Responsable",
        documento=43000001,
        fecha_nacimiento=date(1980, 1, 1),
        provincia=provincia,
    )
    hijo = Ciudadano.objects.create(
        apellido="DetalleDupla",
        nombre="Hijo",
        documento=43000002,
        fecha_nacimiento=date(2015, 1, 1),
        provincia=provincia,
    )
    legajo_responsable = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=responsable,
        estado=estado_legajo,
        rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
        revision_tecnico="APROBADO",
    )
    legajo_hijo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=hijo,
        estado=estado_legajo,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
        revision_tecnico="APROBADO",
    )
    GrupoFamiliar.objects.create(
        ciudadano_1=responsable,
        ciudadano_2=hijo,
        vinculo=GrupoFamiliar.RELACION_PADRE,
        conviven=True,
        cuidador_principal=True,
    )

    client.force_login(user)
    response = client.get(reverse("reporter_provincias"))

    assert response.status_code == 200
    filas = {caso.pk: caso for caso in response.context["ultimos_casos"]}

    assert filas[legajo_hijo.pk].clasificacion_label == "Menor de edad"
    assert filas[legajo_hijo.pk].integra_dupla is True
    # El responsable integra la misma dupla pero no se marca: la unidad se cuenta
    # una sola vez, del lado del hijo.
    assert filas[legajo_responsable.pk].clasificacion_label == "Responsable"
    assert filas[legajo_responsable.pk].integra_dupla is False
