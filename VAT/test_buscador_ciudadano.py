from datetime import date, time
from io import BytesIO

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse
from openpyxl import load_workbook

from VAT.models import (
    AsistenciaSesion,
    Centro,
    Comision,
    ComisionCurso,
    ComisionHorario,
    Curso,
    Inscripcion,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    ModalidadCursada,
    OfertaInstitucional,
    PlanVersionCurricular,
    Sector,
    SesionComision,
    TituloReferencia,
)
from VAT.services.buscador_ciudadano_service import (
    build_resumen,
    build_trayectoria_queryset,
    buscar_ciudadanos,
    contar_inscripciones_visibles,
    export_trayectoria_to_csv,
    export_trayectoria_to_excel,
)
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Programa, Provincia, Sexo


def _grant_referente_role(user):
    permission, _ = Permission.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(Group),
        codename="role_centroreferentevat",
        defaults={"name": "ReferenteCentroVAT legacy"},
    )
    user.user_permissions.add(permission)


def _grant_model_permission(user, model, codename):
    permission = Permission.objects.get(
        content_type=ContentType.objects.get_for_model(model),
        codename=codename,
    )
    user.user_permissions.add(permission)


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


def _build_comision_curso(*, centro, localidad, modalidad, suffix):
    ubicacion, _ = InstitucionUbicacion.objects.get_or_create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        defaults={"domicilio": f"Domicilio {suffix}", "es_principal": True},
    )
    curso = Curso.objects.create(
        centro=centro,
        nombre=f"Curso {suffix}",
        modalidad=modalidad,
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


def _build_comision_oferta(*, centro, provincia, localidad, suffix):
    sector = Sector.objects.create(nombre=f"Sector {suffix}")
    modalidad = ModalidadCursada.objects.create(
        nombre=f"Modalidad {suffix}", activo=True
    )
    plan = PlanVersionCurricular.objects.create(
        nombre=f"Plan {suffix}",
        provincia=provincia,
        sector=sector,
        modalidad_cursada=modalidad,
    )
    programa = Programa.objects.create(nombre=f"Programa {suffix}")
    oferta = OfertaInstitucional.objects.create(
        centro=centro,
        plan_curricular=plan,
        programa=programa,
        nombre_local=f"Oferta {suffix}",
        ciclo_lectivo=2026,
        estado="publicada",
    )
    ubicacion, _ = InstitucionUbicacion.objects.get_or_create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="anexo",
        defaults={"domicilio": f"Domicilio oferta {suffix}", "es_principal": False},
    )
    return Comision.objects.create(
        oferta=oferta,
        ubicacion=ubicacion,
        codigo_comision=f"OFE-{suffix}",
        nombre=f"Comision oferta {suffix}",
        fecha_inicio=date(2026, 5, 1),
        fecha_fin=date(2026, 6, 1),
        cupo=15,
        estado="activa",
    )


def _crear_asistencia(*, inscripcion, comision_curso, user, presente):
    dia, _ = Dia.objects.get_or_create(nombre="Lunes")
    horario = ComisionHorario.objects.create(
        comision_curso=comision_curso,
        dia_semana=dia,
        hora_desde=time(18, 0),
        hora_hasta=time(20, 0),
        aula_espacio="Aula 1",
        vigente=True,
    )
    sesion = SesionComision.objects.create(
        comision_curso=comision_curso,
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


def _geo():
    provincia = Provincia.objects.create(nombre="Jujuy")
    municipio = Municipio.objects.create(nombre="San Salvador", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    return provincia, municipio, localidad


def _ciudadano(**overrides):
    sexo, _ = Sexo.objects.get_or_create(sexo="X")
    defaults = {
        "apellido": "Perez",
        "nombre": "Maria",
        "fecha_nacimiento": date(2000, 1, 1),
        "tipo_documento": Ciudadano.DOCUMENTO_DNI,
        "documento": 30123456,
        "sexo": sexo,
    }
    defaults.update(overrides)
    return Ciudadano.objects.create(**defaults)


@pytest.mark.django_db
def test_normaliza_cuil_y_dni():
    admin = User.objects.create_superuser(username="buscar-normaliza")
    ciudadano = _ciudadano(documento=30123456, cuil_cuit="20-30123456-5")

    for query in ("30123456", "20-30123456-5", "20301234565", "30.123.456"):
        resultado = list(buscar_ciudadanos(admin, query))
        assert resultado == [ciudadano], f"query={query!r} no encontró al ciudadano"


@pytest.mark.django_db
def test_ciudadano_inexistente_devuelve_estado_vacio():
    admin = User.objects.create_superuser(username="buscar-inexistente")
    assert list(buscar_ciudadanos(admin, "99999999")) == []
    assert list(buscar_ciudadanos(admin, "abc")) == []


@pytest.mark.django_db
def test_incluye_ambas_rutas_de_inscripcion():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Rutas", activo=True)
    admin = User.objects.create_superuser(
        username="sse-rutas", email="sse@vat.test", password="test1234"
    )
    centro = _centro_basico("CFP Rutas", "CFP-RUT", provincia, municipio, localidad)

    comision_curso = _build_comision_curso(
        centro=centro, localidad=localidad, modalidad=modalidad, suffix="RUTA-A"
    )
    comision_oferta = _build_comision_oferta(
        centro=centro, provincia=provincia, localidad=localidad, suffix="RUTA-B"
    )

    ciudadano = _ciudadano(documento=30200001)
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_curso, estado="inscripta"
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision=comision_oferta, estado="completada"
    )

    filas = list(build_trayectoria_queryset(admin, ciudadano))
    assert len(filas) == 2
    for fila in filas:
        assert fila.centro_nombre_ref == "CFP Rutas"
        assert fila.unidad_formativa_nombre != "Sin curso/oferta"
        assert fila.comision_codigo_ref in {"COM-RUTA-A", "OFE-RUTA-B"}


@pytest.mark.django_db
def test_excluye_soft_deleted():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Baja", activo=True)
    admin = User.objects.create_superuser(
        username="sse-baja", email="sse-baja@vat.test", password="test1234"
    )
    centro = _centro_basico("CFP Baja", "CFP-BAJ", provincia, municipio, localidad)
    comision = _build_comision_curso(
        centro=centro, localidad=localidad, modalidad=modalidad, suffix="BAJA"
    )
    ciudadano = _ciudadano(documento=30200002)

    activa = Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision, estado="inscripta"
    )
    de_baja = Inscripcion.objects.create(
        ciudadano=ciudadano,
        comision_curso=_build_comision_curso(
            centro=centro, localidad=localidad, modalidad=modalidad, suffix="BAJA2"
        ),
        estado="inscripta",
    )
    de_baja.delete()

    comision_de_baja = _build_comision_curso(
        centro=centro,
        localidad=localidad,
        modalidad=modalidad,
        suffix="COMBAJA",
    )
    inscripcion_con_padre_de_baja = Inscripcion.objects.create(
        ciudadano=ciudadano,
        comision_curso=comision_de_baja,
        estado="inscripta",
    )
    comision_de_baja.delete(cascade=False)

    assert Inscripcion.objects.filter(pk=inscripcion_con_padre_de_baja.pk).exists()

    filas = list(build_trayectoria_queryset(admin, ciudadano))
    assert [fila.id for fila in filas] == [activa.id]


@pytest.mark.django_db
def test_no_duplica_por_cue_multiple():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial CUE", activo=True)
    admin = User.objects.create_superuser(
        username="sse-cue", email="sse-cue@vat.test", password="test1234"
    )
    centro = _centro_basico("CFP CUE", "CFP-CUE", provincia, municipio, localidad)
    InstitucionIdentificadorHist.objects.create(
        centro=centro,
        tipo_identificador="cue",
        valor_identificador="1000001-00",
        es_actual=True,
    )
    InstitucionIdentificadorHist.objects.create(
        centro=centro,
        tipo_identificador="cue",
        valor_identificador="1000001-01",
        es_actual=True,
    )
    comision = _build_comision_curso(
        centro=centro, localidad=localidad, modalidad=modalidad, suffix="CUE"
    )
    ciudadano = _ciudadano(documento=30200003)
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision, estado="inscripta"
    )

    filas = list(build_trayectoria_queryset(admin, ciudadano))
    assert len(filas) == 1
    assert filas[0].cue_ref in {"1000001-00", "1000001-01"}


@pytest.mark.django_db
def test_scope_referente_no_ve_otros_centros():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Scope", activo=True)
    referente = User.objects.create_user(username="ref-scope", password="test1234")
    _grant_referente_role(referente)

    centro_visible = _centro_basico(
        "CFP Visible Busc", "CFP-VISB", provincia, municipio, localidad, referente
    )
    centro_oculto = _centro_basico(
        "CFP Oculto Busc", "CFP-OCUB", provincia, municipio, localidad
    )
    comision_visible = _build_comision_curso(
        centro=centro_visible, localidad=localidad, modalidad=modalidad, suffix="VISB"
    )
    comision_oculta = _build_comision_curso(
        centro=centro_oculto, localidad=localidad, modalidad=modalidad, suffix="OCUB"
    )

    ciudadano = _ciudadano(documento=30200004)
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_visible, estado="inscripta"
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_oculta, estado="inscripta"
    )

    filas = list(build_trayectoria_queryset(referente, ciudadano))
    assert len(filas) == 1
    assert filas[0].centro_nombre_ref == "CFP Visible Busc"


@pytest.mark.django_db
def test_scope_sse_ve_todo():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial SSE", activo=True)
    admin = User.objects.create_superuser(
        username="sse-todo", email="sse-todo@vat.test", password="test1234"
    )
    centro_a = _centro_basico("CFP A Busc", "CFP-AB", provincia, municipio, localidad)
    centro_b = _centro_basico("CFP B Busc", "CFP-BB", provincia, municipio, localidad)
    comision_a = _build_comision_curso(
        centro=centro_a, localidad=localidad, modalidad=modalidad, suffix="AB"
    )
    comision_b = _build_comision_curso(
        centro=centro_b, localidad=localidad, modalidad=modalidad, suffix="BB"
    )

    ciudadano = _ciudadano(documento=30200005)
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_a, estado="inscripta"
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_b, estado="completada"
    )

    filas = list(build_trayectoria_queryset(admin, ciudadano))
    assert len(filas) == 2


@pytest.mark.django_db
def test_resumen_cuenta_estados_y_resultados():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(
        nombre="Presencial Resumen", activo=True
    )
    admin = User.objects.create_superuser(
        username="sse-resumen", email="sse-res@vat.test", password="test1234"
    )
    centro = _centro_basico("CFP Resumen", "CFP-RES", provincia, municipio, localidad)
    ciudadano = _ciudadano(documento=30200006)

    estados_y_resultados = [
        ("inscripta", None),
        ("completada", Inscripcion.RESULTADO_APROBADO),
        ("completada", Inscripcion.RESULTADO_DESAPROBADO),
        ("abandonada", None),
        ("rechazada", None),
    ]
    for index, (estado, resultado) in enumerate(estados_y_resultados):
        comision = _build_comision_curso(
            centro=centro,
            localidad=localidad,
            modalidad=modalidad,
            suffix=f"RES{index}",
        )
        Inscripcion.objects.create(
            ciudadano=ciudadano,
            comision_curso=comision,
            estado=estado,
            resultado_final=resultado,
        )

    filas = list(build_trayectoria_queryset(admin, ciudadano))
    resumen = build_resumen(filas)

    assert resumen["total"] == 5
    assert resumen["en_curso"] == 1
    assert resumen["completadas"] == 2
    assert resumen["abandonadas"] == 1
    assert resumen["rechazadas"] == 1
    assert resumen["aprobadas"] == 1
    assert resumen["desaprobadas"] == 1
    assert resumen["sin_calificar"] == 3


@pytest.mark.django_db
def test_asistencia_sin_registros_no_es_cero():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Asist", activo=True)
    admin = User.objects.create_superuser(
        username="sse-asist", email="sse-asist@vat.test", password="test1234"
    )
    centro = _centro_basico("CFP Asist", "CFP-ASI", provincia, municipio, localidad)
    comision_con = _build_comision_curso(
        centro=centro, localidad=localidad, modalidad=modalidad, suffix="ASICON"
    )
    comision_sin = _build_comision_curso(
        centro=centro, localidad=localidad, modalidad=modalidad, suffix="ASISIN"
    )
    ciudadano = _ciudadano(documento=30200007)

    con_registros = Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_con, estado="inscripta"
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_sin, estado="inscripta"
    )
    _crear_asistencia(
        inscripcion=con_registros,
        comision_curso=comision_con,
        user=admin,
        presente=True,
    )

    filas = {
        fila.comision_codigo_ref: fila
        for fila in build_trayectoria_queryset(admin, ciudadano)
    }
    assert filas["COM-ASICON"].presentes_ref == 1
    assert filas["COM-ASICON"].ausentes_ref == 0
    assert filas["COM-ASISIN"].presentes_ref == 0
    assert filas["COM-ASISIN"].ausentes_ref == 0


@pytest.mark.django_db
def test_export_csv_respeta_scope():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Export", activo=True)
    referente = User.objects.create_user(username="ref-export", password="test1234")
    _grant_referente_role(referente)

    centro_visible = _centro_basico(
        "CFP Export Visible", "CFP-EXV", provincia, municipio, localidad, referente
    )
    centro_oculto = _centro_basico(
        "CFP Export Oculto", "CFP-EXO", provincia, municipio, localidad
    )
    comision_visible = _build_comision_curso(
        centro=centro_visible, localidad=localidad, modalidad=modalidad, suffix="EXV"
    )
    comision_oculta = _build_comision_curso(
        centro=centro_oculto, localidad=localidad, modalidad=modalidad, suffix="EXO"
    )

    ciudadano = _ciudadano(documento=30200008)
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_visible, estado="inscripta"
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision_oculta, estado="inscripta"
    )

    respuesta = export_trayectoria_to_csv(referente, ciudadano)
    contenido = respuesta.content.decode("utf-8-sig")

    assert "CFP Export Visible" in contenido
    assert "CFP Export Oculto" not in contenido


@pytest.mark.django_db
def test_ruta_requiere_permiso():
    user = User.objects.create_user(username="sin-permiso-busc", password="test1234")
    client = Client()
    client.force_login(user)

    response = client.get(reverse("vat_buscador_ciudadano"))
    assert response.status_code == 403
    response = client.post(reverse("vat_buscador_ciudadano"), {"q": "30123456"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_ruta_accesible_con_permiso():
    user = User.objects.create_superuser(
        username="con-permiso-busc", email="con-permiso@vat.test", password="test1234"
    )
    client = Client()
    client.force_login(user)

    response = client.get(reverse("vat_buscador_ciudadano"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_permiso_ciudadanos_habilita_busqueda_sin_inscripciones():
    user = User.objects.create_user(username="busqueda-global")
    _grant_model_permission(user, Ciudadano, "view_ciudadano")
    ciudadano = _ciudadano(documento=30200009)

    assert list(buscar_ciudadanos(user, "30200009")) == [ciudadano]


@pytest.mark.django_db
def test_busqueda_vat_no_revela_ciudadano_fuera_de_scope():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Lookup", activo=True)
    referente = User.objects.create_user(username="ref-lookup")
    _grant_referente_role(referente)

    centro_visible = _centro_basico(
        "CFP Lookup Visible",
        "CFP-LKV",
        provincia,
        municipio,
        localidad,
        referente,
    )
    centro_oculto = _centro_basico(
        "CFP Lookup Oculto", "CFP-LKO", provincia, municipio, localidad
    )
    visible = _ciudadano(documento=30200010)
    oculto = _ciudadano(documento=30200011, nombre="PersonaFueraDeScope")
    Inscripcion.objects.create(
        ciudadano=visible,
        comision_curso=_build_comision_curso(
            centro=centro_visible,
            localidad=localidad,
            modalidad=modalidad,
            suffix="LKV",
        ),
        estado="inscripta",
    )
    Inscripcion.objects.create(
        ciudadano=oculto,
        comision_curso=_build_comision_curso(
            centro=centro_oculto,
            localidad=localidad,
            modalidad=modalidad,
            suffix="LKO",
        ),
        estado="inscripta",
    )

    assert list(buscar_ciudadanos(referente, "30200010")) == [visible]
    assert list(buscar_ciudadanos(referente, "30200011")) == []


@pytest.mark.django_db
def test_multiples_titulos_no_duplican_inscripcion():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(
        nombre="Presencial Títulos", activo=True
    )
    sector = Sector.objects.create(nombre="Sector Títulos")
    plan = PlanVersionCurricular.objects.create(
        nombre="Plan Títulos",
        provincia=provincia,
        sector=sector,
        modalidad_cursada=modalidad,
    )
    titulo_elegido = TituloReferencia.objects.create(
        nombre="Título B", plan_estudio=plan
    )
    TituloReferencia.objects.create(nombre="Título A", plan_estudio=plan)
    admin = User.objects.create_superuser(username="sse-titulos")
    centro = _centro_basico("CFP Títulos", "CFP-TIT", provincia, municipio, localidad)
    comision = _build_comision_curso(
        centro=centro, localidad=localidad, modalidad=modalidad, suffix="TIT"
    )
    comision.curso.plan_estudio = plan
    comision.curso.save(update_fields=["plan_estudio"])
    ciudadano = _ciudadano(documento=30200012)
    inscripcion = Inscripcion.objects.create(
        ciudadano=ciudadano, comision_curso=comision, estado="inscripta"
    )

    filas = list(build_trayectoria_queryset(admin, ciudadano))

    assert [fila.pk for fila in filas] == [inscripcion.pk]
    assert filas[0].titulo_id_ref == titulo_elegido.pk


@pytest.mark.django_db
def test_conteo_de_candidatos_se_resuelve_en_una_query(django_assert_num_queries):
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial Conteo", activo=True)
    admin = User.objects.create_superuser(username="sse-conteo")
    centro = _centro_basico("CFP Conteo", "CFP-CNT", provincia, municipio, localidad)
    ciudadanos = [
        _ciudadano(documento=30200013),
        _ciudadano(
            documento=30200013,
            tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE,
            nombre="Otro candidato",
        ),
    ]
    for index, ciudadano in enumerate(ciudadanos):
        Inscripcion.objects.create(
            ciudadano=ciudadano,
            comision_curso=_build_comision_curso(
                centro=centro,
                localidad=localidad,
                modalidad=modalidad,
                suffix=f"CNT{index}",
            ),
            estado="inscripta",
        )

    with django_assert_num_queries(1):
        totales = contar_inscripciones_visibles(admin, ciudadanos)

    assert totales == {ciudadano.pk: 1 for ciudadano in ciudadanos}

    client = Client()
    client.force_login(admin)
    url = reverse("vat_buscador_ciudadano")
    candidatos_response = client.post(url, {"q": 30200013})
    assert candidatos_response.context["estado"] == "candidatos"

    seleccionado_response = client.post(
        url,
        {"q": 30200013, "ciudadano_id": ciudadanos[1].pk},
    )
    assert seleccionado_response.context["estado"] == "resultado"
    assert seleccionado_response.context["ciudadano"] == ciudadanos[1]


@pytest.mark.django_db
def test_exports_neutralizan_formulas_en_csv_y_xlsx():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(
        nombre="Presencial Export Seguro", activo=True
    )
    admin = User.objects.create_superuser(username="sse-export-seguro")
    centro = _centro_basico("=2+2", "CFP-SEG", provincia, municipio, localidad)
    ciudadano = _ciudadano(documento=30200014)
    Inscripcion.objects.create(
        ciudadano=ciudadano,
        comision_curso=_build_comision_curso(
            centro=centro,
            localidad=localidad,
            modalidad=modalidad,
            suffix="SEG",
        ),
        estado="inscripta",
    )

    csv_response = export_trayectoria_to_csv(admin, ciudadano)
    assert "'=2+2" in csv_response.content.decode("utf-8-sig")

    xlsx_response = export_trayectoria_to_excel(admin, ciudadano)
    workbook = load_workbook(BytesIO(xlsx_response.content), data_only=False)
    centro_cell = workbook["Trayectoria INET"]["E2"]
    assert centro_cell.value == "'=2+2"
    assert centro_cell.data_type == "s"


@pytest.mark.django_db
def test_busqueda_y_export_se_procesan_solo_por_post():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial POST", activo=True)
    admin = User.objects.create_superuser(username="sse-post")
    centro = _centro_basico("CFP POST", "CFP-PST", provincia, municipio, localidad)
    ciudadano = _ciudadano(documento=30200015)
    Inscripcion.objects.create(
        ciudadano=ciudadano,
        comision_curso=_build_comision_curso(
            centro=centro,
            localidad=localidad,
            modalidad=modalidad,
            suffix="PST",
        ),
        estado="inscripta",
    )
    client = Client()
    client.force_login(admin)
    url = reverse("vat_buscador_ciudadano")

    get_response = client.get(url, {"q": ciudadano.documento})
    assert get_response.context["estado"] == "inicial"

    post_response = client.post(url, {"q": ciudadano.documento})
    assert post_response.context["estado"] == "resultado"
    assert post_response.context["ciudadano"] == ciudadano
    assert post_response.request["QUERY_STRING"] == ""
    assert post_response["Cache-Control"] == "no-store, private"

    export_response = client.post(
        url,
        {
            "q": ciudadano.documento,
            "ciudadano_id": ciudadano.pk,
            "export": "csv",
        },
    )
    assert export_response.status_code == 200
    assert export_response["Content-Type"].startswith("text/csv")
    assert export_response.request["QUERY_STRING"] == ""
    assert export_response["Cache-Control"] == "no-store, private"


@pytest.mark.django_db
def test_vista_no_expone_datos_de_ciudadano_fuera_de_scope():
    provincia, municipio, localidad = _geo()
    modalidad = ModalidadCursada.objects.create(nombre="Presencial PII", activo=True)
    referente = User.objects.create_user(username="ref-pii")
    _grant_referente_role(referente)
    _grant_model_permission(referente, Inscripcion, "view_inscripcion")
    centro_oculto = _centro_basico(
        "CFP PII Oculto", "CFP-PII", provincia, municipio, localidad
    )
    ciudadano = _ciudadano(
        documento=30200016,
        nombre="NombrePrivadoFueraDeScope",
        email="privado@example.test",
    )
    Inscripcion.objects.create(
        ciudadano=ciudadano,
        comision_curso=_build_comision_curso(
            centro=centro_oculto,
            localidad=localidad,
            modalidad=modalidad,
            suffix="PII",
        ),
        estado="inscripta",
    )
    client = Client()
    client.force_login(referente)

    response = client.post(
        reverse("vat_buscador_ciudadano"), {"q": ciudadano.documento}
    )
    contenido = response.content.decode()

    assert response.context["estado"] == "no_encontrado"
    assert "NombrePrivadoFueraDeScope" not in contenido
    assert "privado@example.test" not in contenido
