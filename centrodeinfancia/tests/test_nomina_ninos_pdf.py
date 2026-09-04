from datetime import date, datetime
from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.urls import reverse
from django.utils import timezone
from pypdf import PdfReader

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import AccesoCDI, CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.services_nomina_ninos_pdf import (
    CDIGroup,
    ExportData,
    NinoRow,
    NominaNinosPDFError,
    build_export_data,
    build_vector_pdf,
    rasterize_pdf,
)
from core.constants import UserGroups
from core.models import Municipio, Provincia
from users.models import Profile, ProfileTerritorialScope


def _create_egp(username, provincia, *, full_scope=True):
    user = User.objects.create_user(
        username=username,
        password="test1234",
        email=f"{username}@example.test",
    )
    group, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_EGP)
    user.groups.add(group)
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.cuil = "20-00000000-0"
    profile.save()
    municipio = None
    if not full_scope:
        municipio = Municipio.objects.create(
            nombre=f"Municipio {username}",
            provincia=provincia,
        )
    ProfileTerritorialScope.objects.create(
        profile=profile,
        provincia=provincia,
        municipio=municipio,
    )
    return user


def _create_child(documento, *, validated=True, birth_date=date(2024, 1, 15)):
    return Ciudadano.objects.create(
        apellido="Pérez",
        nombre=f"Niño {documento}",
        fecha_nacimiento=birth_date,
        documento=documento,
        estado_validacion_renaper=(
            Ciudadano.RENAPER_VALIDADO if validated else Ciudadano.RENAPER_NO_VALIDADO
        ),
    )


@pytest.mark.django_db
def test_descarga_exige_egp_con_scope_provincial_completo(client):
    provincia = Provincia.objects.create(nombre="Provincia Uno")
    user = User.objects.create_user(username="sin-rol", password="test1234")
    client.force_login(user)
    url = reverse("centrodeinfancia_nomina_ninos_pdf")

    assert client.get(url).status_code == 403

    partial_user = _create_egp("egp-parcial", provincia, full_scope=False)
    client.force_login(partial_user)

    assert client.get(url).status_code == 403


@pytest.mark.django_db
def test_superadmin_descarga_la_provincia_seleccionada(client):
    provincia = Provincia.objects.create(nombre="Provincia Seleccionada")
    superadmin = User.objects.create_superuser(
        username="superadmin-descarga",
        password="test1234",
        email="superadmin@example.test",
    )
    client.force_login(superadmin)

    with patch(
        "centrodeinfancia.views_export.generar_nomina_ninos_pdf",
        return_value=b"%PDF-1.4\nprueba",
    ) as generar_pdf:
        response = client.get(
            reverse("centrodeinfancia_nomina_ninos_pdf"),
            {"provincia": provincia.pk},
        )

    assert response.status_code == 200
    generar_pdf.assert_called_once_with(user=superadmin, provincia=provincia)
    assert (
        response["Content-Disposition"]
        == 'attachment; filename="nomina-ninos-provincia-seleccionada.pdf"'
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query",
    [
        {},
        {"provincia": "no-es-un-id"},
        {"provincia": "999999"},
    ],
)
def test_superadmin_debe_elegir_una_provincia_valida(client, query):
    superadmin = User.objects.create_superuser(
        username=f"superadmin-invalido-{query.get('provincia', 'vacio')}",
        password="test1234",
        email="superadmin@example.test",
    )
    client.force_login(superadmin)

    with patch("centrodeinfancia.views_export.generar_nomina_ninos_pdf") as generar_pdf:
        response = client.get(
            reverse("centrodeinfancia_nomina_ninos_pdf"),
            query,
        )

    assert response.status_code == 400
    assert "Seleccione una provincia válida." in response.content.decode()
    generar_pdf.assert_not_called()


@pytest.mark.django_db
def test_egp_no_puede_descargar_una_provincia_fuera_de_su_alcance(client):
    provincia_egp = Provincia.objects.create(nombre="Provincia EGP")
    provincia_inyectada = Provincia.objects.create(nombre="Provincia Inyectada")
    egp = _create_egp("egp-parametro-inyectado", provincia_egp)
    client.force_login(egp)

    with patch("centrodeinfancia.views_export.generar_nomina_ninos_pdf") as generar_pdf:
        response = client.get(
            reverse("centrodeinfancia_nomina_ninos_pdf"),
            {"provincia": provincia_inyectada.pk},
        )

    assert response.status_code == 403
    generar_pdf.assert_not_called()


@pytest.mark.django_db
def test_descarga_pdf_define_attachment_y_no_cache(client):
    provincia = Provincia.objects.create(nombre="Tierra de Prueba")
    user = _create_egp("egp-descarga", provincia)
    client.force_login(user)

    with patch(
        "centrodeinfancia.views_export.generar_nomina_ninos_pdf",
        return_value=b"%PDF-1.4\nprueba",
    ):
        response = client.get(
            reverse("centrodeinfancia_nomina_ninos_pdf"), {"provincia": provincia.pk}
        )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert (
        response["Content-Disposition"]
        == 'attachment; filename="nomina-ninos-tierra-de-prueba.pdf"'
    )
    assert response["Cache-Control"] == "private, no-store"
    assert response["Pragma"] == "no-cache"


@pytest.mark.django_db
def test_descarga_devuelve_error_controlado_sin_detalles(client):
    provincia = Provincia.objects.create(nombre="Provincia Error")
    user = _create_egp("egp-error", provincia)
    client.force_login(user)

    with patch(
        "centrodeinfancia.views_export.generar_nomina_ninos_pdf",
        side_effect=NominaNinosPDFError("detalle interno"),
    ):
        response = client.get(
            reverse("centrodeinfancia_nomina_ninos_pdf"), {"provincia": provincia.pk}
        )

    assert response.status_code == 503
    assert "detalle interno" not in response.content.decode()
    assert response["Content-Type"].startswith("text/plain")


@pytest.mark.django_db
def test_boton_descarga_solo_se_muestra_a_egp(client):
    provincia = Provincia.objects.create(nombre="Provincia Botón")
    egp = _create_egp("egp-boton", provincia)
    permission = Permission.objects.get(codename="view_centrodeinfancia")
    egp.user_permissions.add(permission)
    client.force_login(egp)

    response = client.get(reverse("centrodeinfancia"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Descargar nómina de niños" in content
    assert "poncho-btn poncho-btn--descarga" in content

    regular = User.objects.create_user(username="regular", password="test1234")
    regular.user_permissions.add(permission)
    client.force_login(regular)

    response = client.get(reverse("centrodeinfancia"))

    assert response.status_code == 200
    assert "Descargar nómina de niños" not in response.content.decode()


@pytest.mark.django_db
def test_superadmin_ve_modal_con_selector_provincial_obligatorio(client):
    provincia_b = Provincia.objects.create(nombre="Zeta")
    provincia_a = Provincia.objects.create(nombre="Alfa")
    superadmin = User.objects.create_superuser(
        username="superadmin-modal",
        password="test1234",
        email="superadmin@example.test",
    )
    client.force_login(superadmin)

    response = client.get(reverse("centrodeinfancia"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Descargar nómina de niños" in content
    assert "poncho-btn poncho-btn--descarga" in content
    assert 'data-bs-target="#nomina-ninos-provincia-modal"' in content
    assert 'id="nomina-ninos-provincia-modal"' in content
    assert 'name="provincia"' in content
    assert "required" in content
    assert list(response.context["nomina_ninos_provincias"]) == [
        provincia_a,
        provincia_b,
    ]


@pytest.mark.django_db
def test_export_data_filtra_deduplica_ordena_y_resuelve_validaciones():
    provincia = Provincia.objects.create(nombre="Provincia Datos")
    otra_provincia = Provincia.objects.create(nombre="Otra Provincia")
    user = _create_egp("egp-datos", provincia)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Central",
        codigo_cdi="CDI-001",
        provincia=provincia,
        nombre_referente="Ana",
        apellido_referente="Referente",
        email_referente="referente@example.test",
    )
    centro_ajeno = CentroDeInfancia.objects.create(
        nombre="CDI Ajeno",
        codigo_cdi="CDI-002",
        provincia=otra_provincia,
    )
    referente = User.objects.create_user(
        username="referente-cdi",
        email="referente@example.test",
    )
    referente_profile, _ = Profile.objects.get_or_create(user=referente)
    referente_profile.cuil = "27-00000000-1"
    referente_profile.save()
    AccesoCDI.objects.create(user=referente, centro=centro, activo=True)

    child_months = _create_child(40000001, validated=True, birth_date=date(2024, 1, 1))
    child_years = _create_child(40000002, validated=False, birth_date=date(2023, 1, 1))
    child_foreign = _create_child(40000003)
    adult = Ciudadano.objects.create(
        apellido="Adulto",
        nombre="Validado",
        fecha_nacimiento=date(1985, 1, 1),
        documento=30000001,
        estado_validacion_renaper=Ciudadano.RENAPER_VALIDADO,
    )
    assert adult.pk

    duplicate_old = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=child_months,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Álvarez",
        nombre="Luz",
        dni=40000001,
        fecha_nacimiento=date(2024, 1, 1),
        sexo=NominaCentroInfancia.SexoChoices.FEMENINO,
        edad_unidad="meses",
    )
    NominaCentroInfancia.objects.filter(pk=duplicate_old.pk).update(
        fecha=timezone.make_aware(datetime(2025, 1, 1, 10, 0))
    )
    duplicate_new = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=child_months,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Álvarez",
        nombre="Luz",
        dni=40000001,
        fecha_nacimiento=date(2024, 1, 1),
        sexo=NominaCentroInfancia.SexoChoices.FEMENINO,
        edad_unidad="meses",
        responsable_legal_1_apellido="Responsable",
        responsable_legal_1_nombre="Uno",
        responsable_legal_1_dni=30000001,
        responsable_legal_1_cuit="20-00000001-1",
        responsable_legal_1_fecha_nacimiento=date(1985, 1, 1),
    )
    NominaCentroInfancia.objects.filter(pk=duplicate_new.pk).update(
        fecha=timezone.make_aware(datetime(2026, 1, 1, 10, 0))
    )
    NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=child_years,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Zuluaga",
        nombre="Sol",
        edad_unidad="anios",
    )
    NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=_create_child(40000004),
        estado=NominaCentroInfancia.ESTADO_BAJA,
    )
    NominaCentroInfancia.objects.create(
        centro=centro_ajeno,
        ciudadano=child_foreign,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )

    data = build_export_data(
        user=user,
        provincia=provincia,
        generado_en=timezone.make_aware(datetime(2026, 8, 18, 12, 30)),
    )

    assert data.total_ninos == 2
    assert len(data.centros) == 1
    assert data.centros[0].referente_cuil == "27-00000000-1"
    assert [row.medida for row in data.centros[0].rows] == ["Meses", "Años"]
    assert data.centros[0].rows[0].adulto_apellido == "Responsable"
    assert data.centros[0].rows[0].adulto_renaper == "Sí"
    assert data.centros[0].rows[0].renaper_nino == "Sí"
    assert data.centros[0].rows[1].renaper_nino == "No"


@pytest.mark.django_db
def test_export_data_usa_provincia_del_centro_aunque_falte_domicilio_del_nino():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = _create_egp("egp-buenos-aires", provincia)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Buenos Aires",
        provincia=provincia,
    )
    con_provincia = _create_child(41000001)
    sin_provincia = _create_child(41000002)

    NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=con_provincia,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        provincia_domicilio=provincia,
    )
    NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=sin_provincia,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        provincia_domicilio=None,
    )

    data = build_export_data(user=user, provincia=provincia)

    assert data.total_ninos == 2
    assert {row.dni for row in data.centros[0].rows} == {"41000001", "41000002"}


@pytest.mark.django_db
def test_export_data_no_duplica_mismo_ciudadano_si_sus_fichas_difieren():
    provincia = Provincia.objects.create(nombre="Provincia Sin Duplicados")
    user = _create_egp("egp-sin-duplicados", provincia)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sin Duplicados",
        provincia=provincia,
    )
    child = _create_child(42000001, birth_date=date(2024, 1, 15))

    ficha_anterior = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=child,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Apellido anterior",
        nombre="Nombre anterior",
        dni=42000001,
        fecha_nacimiento=date(2024, 1, 15),
        sexo=NominaCentroInfancia.SexoChoices.MASCULINO,
    )
    NominaCentroInfancia.objects.filter(pk=ficha_anterior.pk).update(
        fecha=timezone.make_aware(datetime(2025, 1, 1, 10, 0))
    )
    ficha_reciente = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=child,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Apellido corregido",
        nombre="Nombre corregido",
        dni=42000001,
        fecha_nacimiento=date(2024, 1, 16),
        sexo=NominaCentroInfancia.SexoChoices.FEMENINO,
    )
    NominaCentroInfancia.objects.filter(pk=ficha_reciente.pk).update(
        fecha=timezone.make_aware(datetime(2026, 1, 1, 10, 0))
    )

    data = build_export_data(user=user, provincia=provincia)

    assert data.total_ninos == 1
    assert data.centros[0].rows[0].apellido == "Apellido corregido"


@pytest.mark.django_db
def test_export_data_no_duplica_mismo_dni_en_ciudadanos_distintos():
    provincia = Provincia.objects.create(nombre="Provincia DNI Único")
    user = _create_egp("egp-dni-unico", provincia)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI DNI Único",
        provincia=provincia,
    )
    child_anterior = Ciudadano.objects.create(
        apellido="Apellido ciudadano anterior",
        nombre="Nombre ciudadano anterior",
        fecha_nacimiento=date(2024, 1, 15),
        documento=43000001,
        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
    )
    child_reciente = Ciudadano.objects.create(
        apellido="Apellido ciudadano reciente",
        nombre="Nombre ciudadano reciente",
        fecha_nacimiento=date(2024, 1, 16),
        documento=43000001,
        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
    )

    ficha_anterior = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=child_anterior,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Apellido anterior",
        nombre="Nombre anterior",
        dni=43000001,
    )
    NominaCentroInfancia.objects.filter(pk=ficha_anterior.pk).update(
        fecha=timezone.make_aware(datetime(2025, 1, 1, 10, 0))
    )
    ficha_reciente = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=child_reciente,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Apellido corregido",
        nombre="Nombre corregido",
        dni=43000001,
    )
    NominaCentroInfancia.objects.filter(pk=ficha_reciente.pk).update(
        fecha=timezone.make_aware(datetime(2026, 1, 1, 10, 0))
    )

    data = build_export_data(user=user, provincia=provincia)

    assert data.total_ninos == 1
    assert data.centros[0].rows[0].apellido == "Apellido corregido"


@pytest.mark.django_db
def test_export_data_excluye_mayores_de_48_meses_aunque_sigan_activos():
    provincia = Provincia.objects.create(nombre="Provincia Límite Edad")
    user = _create_egp("egp-limite-edad", provincia)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Límite Edad",
        provincia=provincia,
    )
    fecha_exportacion = timezone.make_aware(datetime(2026, 8, 31, 12, 0))

    for documento, nacimiento in (
        (44000001, date(2022, 8, 31)),  # exactamente 48 meses
        (44000002, date(2022, 8, 30)),  # 48 meses y un día
    ):
        ciudadano = _create_child(documento, birth_date=nacimiento)
        NominaCentroInfancia.objects.create(
            centro=centro,
            ciudadano=ciudadano,
            estado=NominaCentroInfancia.ESTADO_ACTIVO,
            fecha_nacimiento=nacimiento,
            edad_unidad="anios",
        )

    data = build_export_data(
        user=user,
        provincia=provincia,
        generado_en=fecha_exportacion,
    )

    assert data.total_ninos == 1
    assert data.centros[0].rows[0].dni == "44000001"


@pytest.mark.django_db
def test_export_data_repara_mojibake_historico_sin_cambiar_fuente_del_snapshot():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = _create_egp("egp-encoding", provincia)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Encoding",
        provincia=provincia,
    )
    ciudadano = _create_child(45000001)
    ciudadano.apellido = "Apellido del ciudadano"
    ciudadano.nombre = "Nombre del ciudadano"
    ciudadano.save(update_fields=["apellido", "nombre"])
    NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Dell \u00c3\u201clio",
        nombre="Joaqu\u00c3\u00adn",
        fecha_nacimiento=date(2024, 1, 15),
        edad_unidad="anios",
    )

    data = build_export_data(user=user, provincia=provincia)

    assert data.centros[0].rows[0].apellido == "Dell Ólio"
    assert data.centros[0].rows[0].nombre == "Joaquín"


@pytest.mark.parametrize(
    ("raw_name", "expected_name"),
    [
        ("Dariel Lu\u00e3\u0081N", "Dariel Luán"),
        ("Lautaro Isa\u00e3\u00adAs", "Lautaro Isaías"),
        ("ÁNabelle", "Ánabelle"),
    ],
)
@pytest.mark.django_db
def test_export_data_repara_mojibake_capitalizado_del_snapshot(
    raw_name,
    expected_name,
):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = _create_egp("egp-encoding-capitalizado", provincia)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Encoding capitalizado",
        provincia=provincia,
    )
    ciudadano = _create_child(45000006)
    ciudadano.nombre = "Nombre del ciudadano"
    ciudadano.save(update_fields=["nombre"])
    NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Apellido",
        nombre=raw_name,
        fecha_nacimiento=date(2024, 1, 15),
        edad_unidad="anios",
    )

    data = build_export_data(user=user, provincia=provincia)

    assert data.centros[0].rows[0].nombre == expected_name


def _sample_export_data():
    row = NinoRow(
        centro_id=1,
        apellido="Apellido",
        nombre="Nombre",
        dni="40000000",
        fecha_nacimiento="01/01/2020",
        edad="6",
        medida="Años",
        sexo="Femenino",
        renaper_nino="Sí",
        adulto_apellido="Responsable",
        adulto_nombre="Adulto",
        adulto_cuit="20-00000000-0",
        adulto_fecha_nacimiento="01/01/1980",
        adulto_renaper="Sí",
        sort_key=(1, 6, "apellido", "nombre", "40000000", 1),
    )
    return ExportData(
        provincia="Provincia Visual",
        usuario="egp-visual",
        rol="SIMEPI - EGP",
        usuario_cuil="20-00000000-0",
        generado_en=timezone.make_aware(datetime(2026, 8, 18, 12, 30)),
        centros=(
            CDIGroup(
                centro_id=1,
                codigo="CDI-001",
                nombre="CDI Visual",
                referente="Persona Referente",
                referente_cuil="27-00000000-1",
                rows=(row,),
            ),
        ),
    )


def test_pdf_final_es_a4_apaisado_y_contiene_un_jpeg_por_pagina():
    final_pdf = rasterize_pdf(build_vector_pdf(_sample_export_data()))
    reader = PdfReader(BytesIO(final_pdf))

    assert len(reader.pages) == 2
    for page in reader.pages:
        assert float(page.mediabox.width) > float(page.mediabox.height)
        assert float(page.mediabox.width) == pytest.approx(841.89, abs=0.2)
        assert float(page.mediabox.height) == pytest.approx(595.28, abs=0.2)
        xobjects = page["/Resources"]["/XObject"].get_object()
        images = [
            obj.get_object()
            for obj in xobjects.values()
            if obj.get_object().get("/Subtype") == "/Image"
        ]
        assert len(images) == 1
        filters = images[0]["/Filter"]
        if not isinstance(filters, list):
            filters = [filters]
        assert "/DCTDecode" in filters
        assert not (page.extract_text() or "").strip()
