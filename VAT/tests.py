import importlib
from datetime import date

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.urls import reverse

from VAT import serializers as vat_serializers
from VAT.forms import CursoForm
from VAT.models import (
    AutoridadInstitucional,
    Centro,
    Sector,
    Subsector,
    TituloReferencia,
    Curso,
    ComisionCurso,
    ComisionHorario,
    Inscripcion,
    InstitucionContacto,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    ModalidadCursada,
    PlanVersionCurricular,
    SesionComision,
    VoucherParametria,
)
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Provincia, Programa, Sexo
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
    _, _, otro_sector, otro_subsector, titulo, modalidad = vat_plan_estudio_base
    # Tras la inversión de la relación, el plan ya no valida coherencia con
    # el título. Título de Referencia ya no tiene sector/subsector propios.
    plan = PlanVersionCurricular(
        sector=otro_sector,
        subsector=otro_subsector,
        modalidad_cursada=modalidad,
        activo=True,
    )
    assert titulo.plan_estudio.sector_id != plan.sector_id
    plan.full_clean()  # ya no debe lanzar error por sector del titulo


@pytest.mark.django_db
def test_plan_estudio_backward_compat_devuelve_primer_titulo(vat_plan_estudio_base):
    _, _, _, _, titulo, _ = vat_plan_estudio_base

    assert titulo.plan_estudio.titulo_referencia == titulo
    assert titulo.plan_estudio.titulo_referencia_id == titulo.id


@pytest.mark.django_db
def test_titulo_referencia_serializer_expone_clasificacion_via_plan(
    vat_plan_estudio_base,
):
    sector, subsector, _, _, titulo, _ = vat_plan_estudio_base

    data = vat_serializers.TituloReferenciaSerializer(instance=titulo).data

    assert data["plan_estudio"] == titulo.plan_estudio_id
    assert data["sector"] == sector.id
    assert data["sector_nombre"] == sector.nombre
    assert data["subsector"] == subsector.id
    assert data["subsector_nombre"] == subsector.nombre


@pytest.mark.django_db
def test_plan_version_curricular_serializer_omite_campos_eliminados(
    vat_plan_estudio_base,
):
    _, _, _, _, titulo, _ = vat_plan_estudio_base

    data = vat_serializers.PlanVersionCurricularSerializer(
        instance=titulo.plan_estudio
    ).data

    assert data["titulo_referencia"] == titulo.id
    assert data["titulo_referencia_nombre"] == titulo.nombre
    assert "version" not in data
    assert "frecuencia" not in data


def test_migracion_0021_falla_si_un_titulo_tiene_multiples_planes():
    migration = importlib.import_module(
        "VAT.migrations.0021_invert_titulo_plan_relation"
    )

    with pytest.raises(RuntimeError, match="múltiples planes históricos"):
        migration._raise_if_ambiguous_title_plan_rows([(7, 2, "11,12")])


def test_migracion_0021_droppea_fk_antes_que_indices_de_titulo_referencia():
    migration = importlib.import_module(
        "VAT.migrations.0021_invert_titulo_plan_relation"
    )
    executed_sql = []

    class FakeCursor:
        def execute(self, sql, params=None):
            executed_sql.append((sql, params))
            if "CONSTRAINT_TYPE = 'FOREIGN KEY'" in sql:
                self._rows = [("vat_plan_titulo_fk",)]
                self._row = None
            elif "CONSTRAINT_TYPE = 'UNIQUE'" in sql:
                self._rows = [
                    ("VAT_planversioncurricula_titulo_referencia_id_mod_uniq",)
                ]
                self._row = None
            elif "FROM information_schema.STATISTICS" in sql:
                self._rows = []
                self._row = None
            elif "FROM information_schema.COLUMNS" in sql:
                self._rows = None
                self._row = (1,)
            else:
                self._rows = None
                self._row = None

        def fetchall(self):
            return self._rows

        def fetchone(self):
            return self._row

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    schema_editor = type(
        "FakeSchemaEditor",
        (),
        {"connection": FakeConnection()},
    )()

    migration._drop_titulo_referencia(None, schema_editor)

    drop_fk_index = next(
        i for i, (sql, _) in enumerate(executed_sql) if "DROP FOREIGN KEY" in sql
    )
    drop_unique_index = next(
        i for i, (sql, _) in enumerate(executed_sql) if "DROP INDEX" in sql
    )

    assert drop_fk_index < drop_unique_index


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
def test_comision_curso_permita_cupo_independiente_del_curso(vat_curso_base):
    centro, ubicacion, modalidad = vat_curso_base
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso Soldadura Inicial",
        modalidad=modalidad,
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

    comision.full_clean()


@pytest.mark.django_db
def test_comision_curso_permita_fechas_independientes_del_curso(vat_curso_base):
    centro, ubicacion, modalidad = vat_curso_base
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso Electricidad",
        modalidad=modalidad,
        estado="planificado",
    )
    comision = ComisionCurso(
        curso=curso,
        codigo_comision="ELEC-01",
        nombre="Comisión tarde",
        cupo_total=20,
        fecha_inicio=date(2026, 3, 28),
        fecha_fin=date(2026, 4, 20),
        estado="planificada",
    )

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
        estado="planificado",
    )

    with pytest.raises(ValidationError):
        curso.full_clean()


@pytest.mark.django_db
def test_curso_requiere_programa_si_usa_voucher(vat_curso_base):
    centro, ubicacion, modalidad = vat_curso_base
    curso = Curso(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso con voucher",
        modalidad=modalidad,
        estado="planificado",
        usa_voucher=True,
        programa=None,
    )

    with pytest.raises(ValidationError):
        curso.full_clean()


@pytest.mark.django_db
def test_curso_form_rechaza_vouchers_fuera_del_programa(vat_curso_base):
    centro, ubicacion, modalidad = vat_curso_base
    programa_curso = Programa.objects.create(nombre="Programa Curso")
    programa_otro = Programa.objects.create(nombre="Programa Otro")
    usuario = User.objects.create_user(username="voucher-curso", password="test1234")
    voucher_otro_programa = VoucherParametria.objects.create(
        nombre="Voucher Programa Otro",
        programa=programa_otro,
        cantidad_inicial=3,
        fecha_vencimiento=date(2026, 12, 31),
        creado_por=usuario,
        activa=True,
    )

    form = CursoForm(
        data={
            "programa": str(programa_curso.id),
            "ubicacion": str(ubicacion.id),
            "nombre": "Curso Test Voucher",
            "modalidad": str(modalidad.id),
            "estado": "planificado",
            "usa_voucher": "on",
            "voucher_parametrias": [str(voucher_otro_programa.id)],
            "costo_creditos": 1,
            "observaciones": "",
        },
        initial={"centro": centro},
    )

    assert not form.is_valid()
    assert "voucher_parametrias" in form.errors


@pytest.mark.django_db
def test_curso_form_plan_estudio_es_primer_campo():
    form = CursoForm()

    assert list(form.fields.keys())[0] == "plan_estudio"


@pytest.mark.django_db
def test_curso_form_guarda_plan_estudio(vat_curso_base, vat_plan_estudio_base):
    centro, ubicacion, modalidad = vat_curso_base
    _, _, _, _, titulo, _ = vat_plan_estudio_base

    form = CursoForm(
        data={
            "plan_estudio": str(titulo.plan_estudio_id),
            "programa": "",
            "ubicacion": str(ubicacion.id),
            "nombre": "Curso con plan",
            "modalidad": str(modalidad.id),
            "estado": "planificado",
            "costo_creditos": 1,
            "observaciones": "",
        },
        initial={"centro": centro},
    )

    assert form.is_valid(), form.errors

    curso = form.save(commit=False)
    curso.centro = centro
    curso.save()

    assert curso.plan_estudio_id == titulo.plan_estudio_id


@pytest.mark.django_db
def test_centro_detail_renderiza_marcadores_para_filtrar_comisiones_por_curso(
    client, vat_geo_data
):
    provincia, municipio, localidad = vat_geo_data
    modalidad = ModalidadCursada.objects.create(nombre="Virtual", activo=True)
    group, _ = Group.objects.get_or_create(name="ReferenteCentroVAT")
    user = User.objects.create_superuser(
        username="admin-vat-centro-detail",
        email="admin-centro-detail@vat.test",
        password="test1234",
    )
    user.groups.add(group)
    centro = Centro.objects.create(
        nombre="CFP 777",
        codigo="CFP-777",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="12",
        numero=345,
        domicilio_actividad="Calle 12 N° 345",
        telefono="221-7000001",
        celular="221-7000002",
        correo="cfp777@vat.test",
        nombre_referente="Laura",
        apellido_referente="Diaz",
        telefono_referente="221-7000003",
        correo_referente="laura@vat.test",
        referente=user,
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    ubicacion = InstitucionUbicacion.objects.create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="Calle 12 N° 345",
        es_principal=True,
    )
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso Filtrable",
        modalidad=modalidad,
        estado="planificado",
    )
    comision = ComisionCurso.objects.create(
        curso=curso,
        codigo_comision="FIL-01",
        nombre="Comisión Filtrable",
        cupo_total=30,
        fecha_inicio=date(2026, 4, 1),
        fecha_fin=date(2026, 4, 30),
        estado="planificada",
    )

    client.force_login(user)
    response = client.get(reverse("vat_centro_detail", kwargs={"pk": centro.pk}))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'id="tablaCursosCentro"' in content
    assert 'class="curso-row"' in content
    assert f'data-curso-id="{curso.id}"' in content
    assert 'id="tablaComisionesCursoCentro"' in content
    assert 'class="comision-curso-row"' in content
    assert reverse("vat_comision_curso_detail", kwargs={"pk": comision.pk}) in content
    assert 'title="Gestionar Comisión"' in content
    assert "setupCursoComisionFilter" in content


@pytest.mark.django_db
def test_comision_curso_detail_muestra_gestion_equivalente(client, vat_geo_data):
    provincia, municipio, localidad = vat_geo_data
    modalidad = ModalidadCursada.objects.create(nombre="Presencial", activo=True)
    programa = Programa.objects.create(nombre="Programa Curso VAT")
    group, _ = Group.objects.get_or_create(name="ReferenteCentroVAT")
    user = User.objects.create_superuser(
        username="admin-comision-curso-detail",
        email="admin-comision-curso-detail@vat.test",
        password="test1234",
    )
    user.groups.add(group)
    centro = Centro.objects.create(
        nombre="CFP 888",
        codigo="CFP-888",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="13",
        numero=456,
        domicilio_actividad="Calle 13 N° 456",
        telefono="221-8000001",
        celular="221-8000002",
        correo="cfp888@vat.test",
        nombre_referente="Ana",
        apellido_referente="Suarez",
        telefono_referente="221-8000003",
        correo_referente="ana@vat.test",
        referente=user,
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    ubicacion = InstitucionUbicacion.objects.create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="Calle 13 N° 456",
        es_principal=True,
    )
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso con detalle",
        modalidad=modalidad,
        programa=programa,
        estado="planificado",
    )
    comision = ComisionCurso.objects.create(
        curso=curso,
        codigo_comision="DET-01",
        nombre="Comisión Detalle",
        cupo_total=25,
        fecha_inicio=date(2026, 4, 1),
        fecha_fin=date(2026, 5, 1),
        estado="activa",
    )

    client.force_login(user)
    response = client.get(
        reverse("vat_comision_curso_detail", kwargs={"pk": comision.pk})
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Comisión de Curso" in content
    assert comision.nombre in content
    assert curso.nombre in content
    assert reverse("vat_comision_curso_update", kwargs={"pk": comision.pk}) in content
    assert reverse("vat_comision_curso_delete", kwargs={"pk": comision.pk}) in content
    assert reverse("vat_inscripcion_rapida_comision_curso") in content
    assert reverse("vat_comision_curso_horario_create") in content
    assert "Información" in content
    assert "Inscriptos" in content
    assert "Sesiones" in content
    assert "Horarios" in content


@pytest.mark.django_db
def test_comision_curso_horario_create_genera_sesiones(client, vat_geo_data):
    provincia, municipio, localidad = vat_geo_data
    modalidad = ModalidadCursada.objects.create(
        nombre="Presencial Horario", activo=True
    )
    group, _ = Group.objects.get_or_create(name="ReferenteCentroVAT")
    user = User.objects.create_superuser(
        username="admin-comision-curso-horario",
        email="admin-comision-curso-horario@vat.test",
        password="test1234",
    )
    user.groups.add(group)
    centro = Centro.objects.create(
        nombre="CFP Horarios",
        codigo="CFP-HOR",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="14",
        numero=100,
        domicilio_actividad="Calle 14 N° 100",
        telefono="221-1111111",
        celular="221-2222222",
        correo="cfphor@vat.test",
        nombre_referente="Ana",
        apellido_referente="Gomez",
        telefono_referente="221-3333333",
        correo_referente="ana-hor@vat.test",
        referente=user,
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    ubicacion = InstitucionUbicacion.objects.create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="Calle 14 N° 100",
        es_principal=True,
    )
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso con horarios",
        modalidad=modalidad,
        estado="planificado",
    )
    comision = ComisionCurso.objects.create(
        curso=curso,
        codigo_comision="HOR-01",
        nombre="Comisión Horario",
        cupo_total=20,
        fecha_inicio=date(2026, 4, 6),
        fecha_fin=date(2026, 4, 20),
        estado="activa",
    )
    dia = Dia.objects.create(nombre="Lunes")

    client.force_login(user)
    response = client.post(
        reverse("vat_comision_curso_horario_create"),
        data={
            "comision_curso": comision.pk,
            "dia_semana": dia.pk,
            "hora_desde": "09:00",
            "hora_hasta": "11:00",
            "aula_espacio": "Aula 1",
            "vigente": "on",
        },
    )

    horario = ComisionHorario.objects.get(comision_curso=comision)

    assert response.status_code == 302
    assert horario.dia_semana == dia
    assert (
        SesionComision.objects.filter(comision_curso=comision, horario=horario).count()
        == 3
    )


@pytest.mark.django_db
def test_inscripcion_rapida_comision_curso_crea_inscripcion(client, vat_geo_data):
    provincia, municipio, localidad = vat_geo_data
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Insc", activo=True)
    programa = Programa.objects.create(nombre="Programa Inscripción Curso")
    sexo = Sexo.objects.create(sexo="Femenino")
    group, _ = Group.objects.get_or_create(name="ReferenteCentroVAT")
    user = User.objects.create_superuser(
        username="admin-comision-curso-insc",
        email="admin-comision-curso-insc@vat.test",
        password="test1234",
    )
    user.groups.add(group)
    centro = Centro.objects.create(
        nombre="CFP Inscriptos",
        codigo="CFP-INSC",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="15",
        numero=100,
        domicilio_actividad="Calle 15 N° 100",
        telefono="221-1111112",
        celular="221-2222223",
        correo="cfpinsc@vat.test",
        nombre_referente="Ana",
        apellido_referente="Gomez",
        telefono_referente="221-3333334",
        correo_referente="ana-insc@vat.test",
        referente=user,
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    ubicacion = InstitucionUbicacion.objects.create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="Calle 15 N° 100",
        es_principal=True,
    )
    curso = Curso.objects.create(
        centro=centro,
        ubicacion=ubicacion,
        nombre="Curso con inscripción",
        modalidad=modalidad,
        programa=programa,
        estado="planificado",
    )
    comision = ComisionCurso.objects.create(
        curso=curso,
        codigo_comision="INSC-01",
        nombre="Comisión Inscriptos",
        cupo_total=20,
        fecha_inicio=date(2026, 4, 1),
        fecha_fin=date(2026, 4, 30),
        estado="activa",
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Lopez",
        nombre="Juana",
        fecha_nacimiento=date(2000, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=12345678,
        sexo=sexo,
    )

    client.force_login(user)
    response = client.post(
        reverse("vat_inscripcion_rapida_comision_curso"),
        data={
            "comision": comision.pk,
            "ciudadano_id": ciudadano.pk,
            "observaciones": "Alta rápida",
        },
    )

    payload = response.json()
    inscripcion = Inscripcion.objects.get(comision_curso=comision, ciudadano=ciudadano)

    assert response.status_code == 200
    assert payload["ok"] is True
    assert inscripcion.programa == programa
    assert inscripcion.estado == "inscripta"
