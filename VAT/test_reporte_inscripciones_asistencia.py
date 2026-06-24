from datetime import date, time

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from VAT.models import (
    AsistenciaSesion,
    Centro,
    ComisionCurso,
    ComisionHorario,
    Curso,
    InstitucionUbicacion,
    Inscripcion,
    ModalidadCursada,
    SesionComision,
)
from VAT.services.reportes_inscripciones_asistencia import (
    ReporteFiltros,
    build_detalle_queryset,
    build_reporte_inscripciones_asistencia,
)
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Provincia, Sexo


def _grant_referente_role(user):
    permission, _ = Permission.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(Group),
        codename="role_centroreferentevat",
        defaults={"name": "ReferenteCentroVAT legacy"},
    )
    user.user_permissions.add(permission)


def _build_comision_curso(*, centro, localidad, modalidad, suffix, usa_voucher=False):
    ubicacion, _ = InstitucionUbicacion.objects.get_or_create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        defaults={
            "domicilio": f"Domicilio {suffix}",
            "es_principal": True,
        },
    )
    curso = Curso.objects.create(
        centro=centro,
        nombre=f"Curso {suffix}",
        modalidad=modalidad,
        usa_voucher=usa_voucher,
        costo_creditos=1 if usa_voucher else 0,
        estado="activo",
    )
    return ComisionCurso.objects.create(
        curso=curso,
        ubicacion=ubicacion,
        codigo_comision=f"COM-{suffix}",
        nombre=f"Comision {suffix}",
        cupo_total=20,
        fecha_inicio=date(2026, 4, 1),
        fecha_fin=date(2026, 4, 30),
        estado="activa",
    )


def _crear_asistencia(*, inscripcion, user, presente):
    dia, _ = Dia.objects.get_or_create(nombre="Lunes")
    horario = ComisionHorario.objects.create(
        comision_curso=inscripcion.comision_curso,
        dia_semana=dia,
        hora_desde=time(18, 0),
        hora_hasta=time(20, 0),
        aula_espacio="Aula 1",
        vigente=True,
    )
    sesion = SesionComision.objects.create(
        comision_curso=inscripcion.comision_curso,
        horario=horario,
        numero_sesion=1,
        fecha=date(2026, 4, 14),
        estado="realizada",
    )
    AsistenciaSesion.objects.create(
        sesion=sesion,
        inscripcion=inscripcion,
        presente=presente,
        registrado_por=user,
    )


@pytest.mark.django_db
def test_reporte_respeta_scope_referente():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    sexo = Sexo.objects.create(sexo="F")
    modalidad = ModalidadCursada.objects.create(nombre="Presencial", activo=True)

    referente = User.objects.create_user(username="rep-ref", password="test1234")
    _grant_referente_role(referente)

    centro_visible = Centro.objects.create(
        nombre="CFP Visible",
        codigo="CFP-VIS",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="7",
        numero=123,
        domicilio_actividad="Calle 7",
        telefono="221111",
        celular="221222",
        correo="visible@vat.test",
        nombre_referente="Ana",
        apellido_referente="Perez",
        telefono_referente="221333",
        correo_referente="ana@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
        referente=referente,
    )
    centro_oculto = Centro.objects.create(
        nombre="CFP Oculto",
        codigo="CFP-OCU",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="8",
        numero=124,
        domicilio_actividad="Calle 8",
        telefono="221444",
        celular="221555",
        correo="oculto@vat.test",
        nombre_referente="Beto",
        apellido_referente="Gomez",
        telefono_referente="221666",
        correo_referente="beto@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )

    comision_visible = _build_comision_curso(
        centro=centro_visible,
        localidad=localidad,
        modalidad=modalidad,
        suffix="VIS",
    )
    comision_oculta = _build_comision_curso(
        centro=centro_oculto,
        localidad=localidad,
        modalidad=modalidad,
        suffix="OCU",
    )

    ciudadana_visible = Ciudadano.objects.create(
        apellido="Visible",
        nombre="Ada",
        fecha_nacimiento=date(2000, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40111001,
        sexo=sexo,
    )
    ciudadano_oculto = Ciudadano.objects.create(
        apellido="Oculto",
        nombre="Bruno",
        fecha_nacimiento=date(2000, 1, 2),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40111002,
        sexo=sexo,
    )

    Inscripcion.objects.create(
        ciudadano=ciudadana_visible,
        comision_curso=comision_visible,
        estado="inscripta",
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano_oculto,
        comision_curso=comision_oculta,
        estado="inscripta",
    )

    resultado = build_reporte_inscripciones_asistencia(
        referente,
        ReporteFiltros(group_by="centro"),
    )

    assert resultado["resumen"]["inscripciones_total"] == 1
    assert len(resultado["rows"]) == 1
    assert resultado["rows"][0]["grupo"] == "CFP Visible"


@pytest.mark.django_db
def test_reporte_calcula_metricas_de_asistencia():
    provincia = Provincia.objects.create(nombre="Cordoba")
    municipio = Municipio.objects.create(nombre="Capital", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    sexo = Sexo.objects.create(sexo="M")
    modalidad = ModalidadCursada.objects.create(nombre="Virtual", activo=True)

    referente = User.objects.create_user(username="rep-metricas", password="test1234")
    _grant_referente_role(referente)

    centro = Centro.objects.create(
        nombre="CFP Metricas",
        codigo="CFP-MET",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="9",
        numero=200,
        domicilio_actividad="Calle 9",
        telefono="351111",
        celular="351222",
        correo="metricas@vat.test",
        nombre_referente="Lia",
        apellido_referente="Sosa",
        telefono_referente="351333",
        correo_referente="lia@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
        referente=referente,
    )

    comision = _build_comision_curso(
        centro=centro,
        localidad=localidad,
        modalidad=modalidad,
        suffix="MET",
    )

    ciudadano_1 = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        fecha_nacimiento=date(1999, 5, 20),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40111010,
        sexo=sexo,
    )
    ciudadano_2 = Ciudadano.objects.create(
        apellido="Diaz",
        nombre="Sol",
        fecha_nacimiento=date(1999, 6, 21),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40111011,
        sexo=sexo,
    )

    inscripcion_1 = Inscripcion.objects.create(
        ciudadano=ciudadano_1,
        comision_curso=comision,
        estado="inscripta",
    )
    inscripcion_2 = Inscripcion.objects.create(
        ciudadano=ciudadano_2,
        comision_curso=comision,
        estado="pre_inscripta",
    )

    _crear_asistencia(inscripcion=inscripcion_1, user=referente, presente=True)
    _crear_asistencia(inscripcion=inscripcion_2, user=referente, presente=False)

    resultado = build_reporte_inscripciones_asistencia(
        referente,
        ReporteFiltros(group_by="centro"),
    )
    resumen = resultado["resumen"]

    assert resumen["inscripciones_total"] == 2
    assert resumen["preinscriptos"] == 1
    assert resumen["inscriptos"] == 1
    assert resumen["presentes"] == 1
    assert resumen["ausentes"] == 1
    assert resumen["porcentaje_asistencia"] == 50.0


@pytest.mark.django_db
def test_reporte_incluye_sesiones_programadas_sin_asistencia():
    provincia = Provincia.objects.create(nombre="Santa Fe")
    municipio = Municipio.objects.create(nombre="Rosario", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    sexo = Sexo.objects.create(sexo="X")
    modalidad = ModalidadCursada.objects.create(nombre="Mixta", activo=True)

    referente = User.objects.create_user(username="rep-sesiones", password="test1234")
    _grant_referente_role(referente)

    centro = Centro.objects.create(
        nombre="CFP Sesiones",
        codigo="CFP-SES",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="10",
        numero=100,
        domicilio_actividad="Calle 10",
        telefono="341111",
        celular="341222",
        correo="sesiones@vat.test",
        nombre_referente="Pablo",
        apellido_referente="Ruiz",
        telefono_referente="341333",
        correo_referente="pablo@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
        referente=referente,
    )

    comision = _build_comision_curso(
        centro=centro,
        localidad=localidad,
        modalidad=modalidad,
        suffix="SES",
    )

    ciudadana = Ciudadano.objects.create(
        apellido="Mora",
        nombre="Ines",
        fecha_nacimiento=date(2001, 2, 2),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40111999,
        sexo=sexo,
    )
    inscripcion = Inscripcion.objects.create(
        ciudadano=ciudadana,
        comision_curso=comision,
        estado="inscripta",
    )

    dia, _ = Dia.objects.get_or_create(nombre="Martes")
    horario = ComisionHorario.objects.create(
        comision_curso=comision,
        dia_semana=dia,
        hora_desde=time(9, 0),
        hora_hasta=time(11, 0),
        aula_espacio="Aula 2",
        vigente=True,
    )
    SesionComision.objects.create(
        comision_curso=comision,
        horario=horario,
        numero_sesion=1,
        fecha=date(2026, 4, 10),
        estado="programada",
    )
    _crear_asistencia(inscripcion=inscripcion, user=referente, presente=True)

    resultado = build_reporte_inscripciones_asistencia(
        referente,
        ReporteFiltros(group_by="centro"),
    )
    resumen = resultado["resumen"]

    assert resumen["sesiones_programadas"] == 1
    assert resumen["sesiones_realizadas"] == 1


@pytest.mark.django_db
def test_reporte_filtra_por_usa_voucher():
    provincia = Provincia.objects.create(nombre="Mendoza")
    municipio = Municipio.objects.create(nombre="Guaymallen", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Norte", municipio=municipio)
    sexo = Sexo.objects.create(sexo="F")
    modalidad = ModalidadCursada.objects.create(nombre="Presencial", activo=True)

    referente = User.objects.create_user(username="rep-voucher", password="test1234")
    _grant_referente_role(referente)

    centro = Centro.objects.create(
        nombre="CFP Voucher",
        codigo="CFP-VOU",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="11",
        numero=88,
        domicilio_actividad="Calle 11",
        telefono="261111",
        celular="261222",
        correo="voucher@vat.test",
        nombre_referente="Nora",
        apellido_referente="Ibarra",
        telefono_referente="261333",
        correo_referente="nora@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
        referente=referente,
    )

    comision_voucher = _build_comision_curso(
        centro=centro,
        localidad=localidad,
        modalidad=modalidad,
        suffix="VOU",
        usa_voucher=True,
    )
    comision_libre = _build_comision_curso(
        centro=centro,
        localidad=localidad,
        modalidad=modalidad,
        suffix="LIB",
        usa_voucher=False,
    )

    ciudadano_a = Ciudadano.objects.create(
        apellido="A",
        nombre="Uno",
        fecha_nacimiento=date(2000, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40112001,
        sexo=sexo,
    )
    ciudadano_b = Ciudadano.objects.create(
        apellido="B",
        nombre="Dos",
        fecha_nacimiento=date(2000, 1, 2),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40112002,
        sexo=sexo,
    )

    Inscripcion.objects.create(
        ciudadano=ciudadano_a,
        comision_curso=comision_voucher,
        estado="inscripta",
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano_b,
        comision_curso=comision_libre,
        estado="inscripta",
    )

    resultado_true = build_reporte_inscripciones_asistencia(
        referente,
        ReporteFiltros(group_by="curso", usa_voucher="true"),
    )
    resultado_false = build_reporte_inscripciones_asistencia(
        referente,
        ReporteFiltros(group_by="curso", usa_voucher="false"),
    )

    assert resultado_true["resumen"]["inscripciones_total"] == 1
    assert resultado_false["resumen"]["inscripciones_total"] == 1


def _centro_basico(nombre, codigo, provincia, municipio, localidad, referente=None):
    return Centro.objects.create(
        nombre=nombre,
        codigo=codigo,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="1",
        numero=1,
        domicilio_actividad="Calle 1",
        telefono="2210000",
        celular="2210001",
        correo=f"{codigo}@vat.test",
        nombre_referente="Ref",
        apellido_referente="Erente",
        telefono_referente="2210002",
        correo_referente=f"ref-{codigo}@vat.test",
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
        referente=referente,
    )


@pytest.mark.django_db
def test_build_detalle_queryset_respeta_scope_y_pagina():
    provincia = Provincia.objects.create(nombre="Córdoba Det")
    municipio = Municipio.objects.create(nombre="Capital Det", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro Det", municipio=municipio)
    sexo = Sexo.objects.create(sexo="F")
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Det", activo=True)

    referente = User.objects.create_user(username="rep-det", password="test1234")
    _grant_referente_role(referente)

    centro_visible = _centro_basico(
        "CFP Det Visible", "CFP-DET-VIS", provincia, municipio, localidad, referente
    )
    centro_oculto = _centro_basico(
        "CFP Det Oculto", "CFP-DET-OCU", provincia, municipio, localidad
    )
    comision_visible = _build_comision_curso(
        centro=centro_visible, localidad=localidad, modalidad=modalidad, suffix="DETV"
    )
    comision_oculta = _build_comision_curso(
        centro=centro_oculto, localidad=localidad, modalidad=modalidad, suffix="DETO"
    )

    for i in range(3):
        ciudadano = Ciudadano.objects.create(
            apellido=f"Visible{i}",
            nombre="Det",
            fecha_nacimiento=date(2000, 1, 1),
            tipo_documento=Ciudadano.DOCUMENTO_DNI,
            documento=40222000 + i,
            sexo=sexo,
        )
        Inscripcion.objects.create(
            ciudadano=ciudadano, comision_curso=comision_visible, estado="inscripta"
        )

    ciudadano_oculto = Ciudadano.objects.create(
        apellido="Oculto",
        nombre="Det",
        fecha_nacimiento=date(2000, 1, 2),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40222999,
        sexo=sexo,
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano_oculto, comision_curso=comision_oculta, estado="inscripta"
    )

    qs = build_detalle_queryset(referente, ReporteFiltros())
    docs = [row["ciudadano__documento"] for row in qs]

    # Scope: el oculto no aparece; solo los 3 del centro del referente.
    assert 40222999 not in docs
    assert len(docs) == 3

    # Paginación por slicing (LIMIT/OFFSET): páginas disjuntas que cubren todo.
    page1_ids = {row["id"] for row in qs[:2]}
    page2_ids = {row["id"] for row in qs[2:4]}
    assert len(page1_ids) == 2
    assert len(page2_ids) == 1
    assert page1_ids.isdisjoint(page2_ids)
