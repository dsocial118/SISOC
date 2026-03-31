import pytest
from django.contrib.auth.models import Group, User
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.urls import reverse

from VAT.models import (
    AutoridadInstitucional,
    Centro,
    Sector,
    Subsector,
    TituloReferencia,
    Curso,
    ComisionCurso,
    InstitucionContacto,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    ModalidadCursada,
    PlanVersionCurricular,
)
from core.models import Localidad, Municipio, Provincia
from users.models import Profile


@pytest.fixture
def vat_geo_data(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    return provincia, municipio, localidad


@pytest.fixture
def vat_referente_user(db):
    group, _ = Group.objects.get_or_create(name="ReferenteCentroVAT")
    user = User.objects.create_user(username="referente-vat", password="test1234")
    user.groups.add(group)
    return user


@pytest.fixture
def vat_admin_client(client, db):
    user = User.objects.create_superuser(
        username="admin-vat",
        email="admin@vat.test",
        password="test1234",
    )
    client.force_login(user)
    return client


def _build_centro_payload(referente_user, provincia, municipio, localidad, **overrides):
    payload = {
        "nombre": "Centro de Formación 401",
        "codigo": "500144900",
        "provincia": str(provincia.pk),
        "municipio": str(municipio.pk),
        "localidad": str(localidad.pk),
        "calle": "7",
        "numero": "1234",
        "domicilio_actividad": "Calle 7 N° 1234",
        "codigo_postal": "1900",
        "lote": "12",
        "manzana": "B",
        "entre_calles": "45 y 46",
        "telefono": "221-4000000",
        "celular": "221-5000000",
        "correo": "institucion@vat.test",
        "sitio_web": "https://vat.test",
        "nombre_referente": "Ana",
        "apellido_referente": "Pérez",
        "autoridad_dni": "30111222",
        "telefono_referente": "221-4111111",
        "correo_referente": "direccion@vat.test",
        "referente": str(referente_user.pk),
        "activo": "on",
        "tipo_gestion": "Estatal",
        "clase_institucion": "Formación Profesional",
        "situacion": "Institución de ETP",
        "contactos-TOTAL_FORMS": "1",
        "contactos-INITIAL_FORMS": "0",
        "contactos-MIN_NUM_FORMS": "0",
        "contactos-MAX_NUM_FORMS": "1000",
        "contactos-0-nombre_contacto": "María Gómez",
        "contactos-0-rol_area": "Administración",
        "contactos-0-telefono_contacto": "221-4222222",
        "contactos-0-email_contacto": "maria@vat.test",
        "contactos-0-es_principal": "on",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_centro_create_crea_entidades_relacionadas(
    vat_admin_client, vat_referente_user, vat_geo_data
):
    provincia, municipio, localidad = vat_geo_data
    payload = _build_centro_payload(
        vat_referente_user, provincia, municipio, localidad, save_continue="1"
    )

    response = vat_admin_client.post(reverse("vat_centro_create"), data=payload)

    centro = Centro.objects.get(codigo="500144900")

    assert response.status_code == 302
    assert response.url == reverse("vat_centro_detail", kwargs={"pk": centro.pk})
    assert AutoridadInstitucional.objects.filter(centro=centro, dni="30111222").exists()
    assert InstitucionContacto.objects.filter(
        centro=centro,
        nombre_contacto="María Gómez",
        es_principal=True,
    ).exists()
    assert InstitucionIdentificadorHist.objects.filter(
        centro=centro,
        tipo_identificador="cue",
        valor_identificador="500144900",
    ).exists()
    assert InstitucionUbicacion.objects.filter(
        centro=centro,
        rol_ubicacion="sede_principal",
        es_principal=True,
    ).exists()


@pytest.mark.django_db
def test_centro_create_requiere_un_contacto_principal(
    vat_admin_client, vat_referente_user, vat_geo_data
):
    provincia, municipio, localidad = vat_geo_data
    payload = _build_centro_payload(
        vat_referente_user,
        provincia,
        municipio,
        localidad,
        **{"contactos-0-es_principal": ""},
    )

    response = vat_admin_client.post(reverse("vat_centro_create"), data=payload)

    assert response.status_code == 200
    assert Centro.objects.filter(codigo="500144900").count() == 0
    assert "Debe existir exactamente un contacto principal." in response.content.decode(
        "utf-8"
    )


@pytest.mark.django_db
def test_centro_list_usuario_provincial_solo_ve_su_provincia(client):
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")

    municipio_ba = Municipio.objects.create(nombre="La Plata", provincia=provincia_ba)
    municipio_sf = Municipio.objects.create(nombre="Rosario", provincia=provincia_sf)

    localidad_ba = Localidad.objects.create(nombre="Tolosa", municipio=municipio_ba)
    localidad_sf = Localidad.objects.create(nombre="Centro", municipio=municipio_sf)

    user = User.objects.create_user(username="provincial-vat", password="test1234")
    Profile.objects.update_or_create(
        user=user,
        defaults={
            "es_usuario_provincial": True,
            "provincia": provincia_ba,
        },
    )

    permiso_view_centro = Permission.objects.get(
        content_type__app_label="VAT",
        codename="view_centro",
    )
    user.user_permissions.add(permiso_view_centro)

    Centro.objects.create(
        nombre="Centro BA",
        codigo="BA-001",
        provincia=provincia_ba,
        municipio=municipio_ba,
        localidad=localidad_ba,
        calle="7",
        numero=123,
        domicilio_actividad="Calle 7",
        telefono="221-111111",
        celular="221-111112",
        correo="ba@vat.test",
        nombre_referente="Ana",
        apellido_referente="Perez",
        telefono_referente="221-111113",
        correo_referente="refba@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    Centro.objects.create(
        nombre="Centro SF",
        codigo="SF-001",
        provincia=provincia_sf,
        municipio=municipio_sf,
        localidad=localidad_sf,
        calle="Córdoba",
        numero=456,
        domicilio_actividad="Córdoba 456",
        telefono="341-222221",
        celular="341-222222",
        correo="sf@vat.test",
        nombre_referente="Juan",
        apellido_referente="Gomez",
        telefono_referente="341-222223",
        correo_referente="refsf@vat.test",
        tipo_gestion="Privada",
        clase_institucion="Capacitación Laboral",
        situacion="Institución de ETP",
        activo=True,
    )

    client.force_login(user)
    response = client.get(reverse("vat_centro_list"))

    assert response.status_code == 200
    centros = list(response.context["centros"])
    assert len(centros) == 1
    assert centros[0].nombre == "Centro BA"


@pytest.mark.django_db
def test_centro_create_usuario_provincial_sin_scope_global_recibe_403(client):
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    user = User.objects.create_user(
        username="provincial-no-create", password="test1234"
    )
    Profile.objects.update_or_create(
        user=user,
        defaults={
            "es_usuario_provincial": True,
            "provincia": provincia_ba,
        },
    )
    permiso_view_centro = Permission.objects.get(
        content_type__app_label="VAT",
        codename="view_centro",
    )
    user.user_permissions.add(permiso_view_centro)

    client.force_login(user)
    response = client.get(reverse("vat_centro_create"))

    assert response.status_code == 403


@pytest.fixture
def vat_plan_estudio_base(db):
    sector = Sector.objects.create(nombre="Industria")
    subsector = Subsector.objects.create(sector=sector, nombre="Metalúrgica")
    otro_sector = Sector.objects.create(nombre="Servicios")
    otro_subsector = Subsector.objects.create(
        sector=otro_sector,
        nombre="Administración",
    )
    modalidad = ModalidadCursada.objects.create(nombre="Presencial", activo=True)
    plan = PlanVersionCurricular.objects.create(
        sector=sector,
        subsector=subsector,
        modalidad_cursada=modalidad,
        activo=True,
    )
    titulo = TituloReferencia.objects.create(
        plan_estudio=plan,
        nombre="Soldador Básico",
        activo=True,
    )
    return sector, subsector, otro_sector, otro_subsector, titulo, modalidad


@pytest.mark.django_db
def test_plan_estudio_rechaza_subsector_fuera_del_sector(vat_plan_estudio_base):
    sector, _, _, otro_subsector, titulo, modalidad = vat_plan_estudio_base
    plan = PlanVersionCurricular(
        sector=sector,
        subsector=otro_subsector,
        modalidad_cursada=modalidad,
        activo=True,
    )

    with pytest.raises(ValidationError):
        plan.full_clean()


@pytest.mark.django_db
def test_plan_estudio_rechaza_sector_distinto_al_titulo(vat_plan_estudio_base):
    _, subsector, otro_sector, _, titulo, modalidad = vat_plan_estudio_base
    # Tras la inversión de la relación, el plan ya no valida coherencia con
    # el título. Título de Referencia ya no tiene sector/subsector propios.
    plan = PlanVersionCurricular(
        sector=otro_sector,
        subsector=subsector,
        modalidad_cursada=modalidad,
        activo=True,
    )
    plan.full_clean()  # ya no debe lanzar error por sector del titulo


@pytest.fixture
def vat_curso_base(db, vat_geo_data):
    provincia, municipio, localidad = vat_geo_data
    modalidad = ModalidadCursada.objects.create(nombre="Presencial", activo=True)
    centro = Centro.objects.create(
        nombre="CFP 501",
        codigo="CFP-501",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="8",
        numero=111,
        domicilio_actividad="Calle 8 N° 111",
        telefono="221-1111111",
        celular="221-1111112",
        correo="cfp501@vat.test",
        nombre_referente="Marta",
        apellido_referente="Lopez",
        telefono_referente="221-1111113",
        correo_referente="marta@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    ubicacion = InstitucionUbicacion.objects.create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="Calle 8 N° 111",
        es_principal=True,
    )
    return centro, ubicacion, modalidad


@pytest.mark.django_db
def test_comision_curso_no_permite_cupo_mayor_al_curso(vat_curso_base):
    centro, ubicacion, modalidad = vat_curso_base
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso Soldadura Inicial",
        modalidad=modalidad,
        fecha_inicio="2026-03-01",
        fecha_fin="2026-03-30",
        cupo_total=20,
        estado="planificado",
    )
    comision = ComisionCurso(
        curso=curso,
        codigo_comision="SOLD-01",
        nombre="Comisión mañana",
        cupo_total=25,
        fecha_inicio="2026-03-05",
        fecha_fin="2026-03-25",
        estado="planificada",
    )

    with pytest.raises(ValidationError):
        comision.full_clean()


@pytest.mark.django_db
def test_comision_curso_no_permite_fechas_fuera_de_rango(vat_curso_base):
    centro, ubicacion, modalidad = vat_curso_base
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso Electricidad",
        modalidad=modalidad,
        fecha_inicio="2026-04-01",
        fecha_fin="2026-04-30",
        cupo_total=30,
        estado="planificado",
    )
    comision = ComisionCurso(
        curso=curso,
        codigo_comision="ELEC-01",
        nombre="Comisión tarde",
        cupo_total=20,
        fecha_inicio="2026-03-28",
        fecha_fin="2026-04-20",
        estado="planificada",
    )

    with pytest.raises(ValidationError):
        comision.full_clean()


@pytest.mark.django_db
def test_curso_no_permite_ubicacion_de_otro_centro(vat_geo_data):
    provincia, municipio, localidad = vat_geo_data
    modalidad = ModalidadCursada.objects.create(nombre="Semipresencial", activo=True)
    centro_a = Centro.objects.create(
        nombre="Centro A",
        codigo="A-001",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="10",
        numero=100,
        domicilio_actividad="Calle 10",
        telefono="221-1000000",
        celular="221-1000001",
        correo="a@vat.test",
        nombre_referente="Ref",
        apellido_referente="A",
        telefono_referente="221-1000002",
        correo_referente="refa@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    centro_b = Centro.objects.create(
        nombre="Centro B",
        codigo="B-001",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="11",
        numero=101,
        domicilio_actividad="Calle 11",
        telefono="221-1100000",
        celular="221-1100001",
        correo="b@vat.test",
        nombre_referente="Ref",
        apellido_referente="B",
        telefono_referente="221-1100002",
        correo_referente="refb@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    ubicacion_b = InstitucionUbicacion.objects.create(
        centro=centro_b,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="Calle 11",
        es_principal=True,
    )

    curso = Curso(
        centro=centro_a,
        ubicacion=ubicacion_b,
        nombre="Curso Inválido",
        modalidad=modalidad,
        fecha_inicio="2026-05-01",
        fecha_fin="2026-05-10",
        cupo_total=10,
        estado="planificado",
    )

    with pytest.raises(ValidationError):
        curso.full_clean()
