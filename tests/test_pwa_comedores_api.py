"""Tests for test pwa comedores api."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from admisiones.models.admisiones import Admision, InformeTecnico
from comedores.models import Comedor, ImagenComedor, Nomina, Programas
from core.models import Localidad, Municipio, Provincia
from organizaciones.models import Organizacion
from relevamientos.models import (
    Anexo,
    CantidadColaboradores,
    Colaboradores,
    Espacio,
    EspacioCocina,
    EspacioPrestacion,
    FrecuenciaLimpieza,
    FrecuenciaRecepcionRecursos,
    FuenteCompras,
    FuenteRecursos,
    FuncionamientoPrestacion,
    Relevamiento,
    TipoAgua,
    TipoDistanciaTransporte,
    TipoEspacio,
    TipoModalidadPrestacion,
    TipoRecurso,
    TipoTecnologia,
)
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from users.models import AccesoComedorPWA


@pytest.fixture
def comedores(db):
    provincia = Provincia.objects.create(nombre="Cordoba")
    comedor_1 = Comedor.objects.create(nombre="Comedor Uno", provincia=provincia)
    comedor_2 = Comedor.objects.create(nombre="Comedor Dos", provincia=provincia)
    return comedor_1, comedor_2


def _create_pwa_user(
    *,
    comedor,
    role,
    username,
    created_by=None,
    password="testpass123",
):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=role,
        creado_por=created_by,
        activo=True,
    )
    return user


def _token_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _grant_mobile_rendicion_permission(user):
    permission = Permission.objects.get(
        content_type__app_label="rendicioncuentasmensual",
        codename="manage_mobile_rendicion",
    )
    user.user_permissions.add(permission)


def _fake_value_for_field(field):
    if field.choices:
        return field.choices[0][0]
    if isinstance(field, models.EmailField):
        return "test@example.com"
    if isinstance(field, (models.CharField, models.TextField)):
        return "test"
    if isinstance(field, models.BooleanField):
        return False
    if isinstance(field, models.DecimalField):
        return 1
    if isinstance(field, models.FloatField):
        return 1.0
    if isinstance(field, models.DateTimeField):
        return date(2026, 1, 1)
    if isinstance(field, models.DateField):
        return date(2026, 1, 1)
    if isinstance(field, models.IntegerField):
        return 1
    return "test"


def _create_informe_tecnico(admision, **overrides):
    payload = {}
    for field in InformeTecnico._meta.fields:
        if field.primary_key or field.auto_created:
            continue
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            continue
        if field.has_default():
            continue
        if isinstance(field, models.ForeignKey):
            continue
        if field.null:
            continue
        payload[field.name] = _fake_value_for_field(field)

    payload.update(
        {
            "admision": admision,
            "tipo": "base",
            "estado": "Iniciado",
            "estado_formulario": "finalizado",
        }
    )
    payload.update(overrides)
    return InformeTecnico.objects.create(**payload)


@pytest.mark.django_db
def test_comedor_api_requires_authentication(comedores):
    comedor_1, _ = comedores
    client = APIClient()
    response = client.get(f"/api/comedores/{comedor_1.id}/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_comedor_api_accepts_non_pwa_token(comedores):
    comedor_1, _ = comedores
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="no_pwa",
        email="no_pwa@example.com",
        password="testpass123",
    )
    client = _token_client(user)
    response = client.get(f"/api/comedores/{comedor_1.id}/")
    assert response.status_code == 200
    assert response.data["id"] == comedor_1.id


@pytest.mark.django_db
def test_representante_scope_returns_404_for_unassigned_comedor(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_scope",
    )
    client = _token_client(representante)

    ok_response = client.get(f"/api/comedores/{comedor_1.id}/")
    forbidden_scope_response = client.get(f"/api/comedores/{comedor_2.id}/")

    assert ok_response.status_code == 200
    assert forbidden_scope_response.status_code == 404


@pytest.mark.django_db
def test_pwa_spaces_selector_list_returns_metadata_and_sorted_names():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    programa = Programas.objects.create(nombre="Alimentar Comunidad")
    organizacion = Organizacion.objects.create(nombre="Organización Central")
    comedor_b = Comedor.objects.create(
        nombre="Beta",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        organizacion=organizacion,
        programa=programa,
        codigo_de_proyecto="PROY-02",
    )
    comedor_a = Comedor.objects.create(
        nombre="Alpha",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        organizacion=organizacion,
        programa=programa,
        codigo_de_proyecto="PROY-01",
    )

    representante = _create_pwa_user(
        comedor=comedor_b,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_selector",
    )
    AccesoComedorPWA.objects.filter(user=representante, comedor=comedor_b).update(
        tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
        organizacion=organizacion,
    )
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=comedor_a,
        organizacion=organizacion,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
        activo=True,
    )
    client = _token_client(representante)

    response = client.get("/api/comedores/")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert [item["nombre"] for item in response.data["results"]] == ["Alpha", "Beta"]
    assert response.data["results"][0]["programa__nombre"] == "Alimentar Comunidad"
    assert response.data["results"][0]["organizacion__nombre"] == "Organización Central"
    assert response.data["results"][0]["codigo_de_proyecto"] == "PROY-01"
    assert response.data["results"][0]["provincia__nombre"] == "Buenos Aires"
    assert response.data["results"][0]["localidad__nombre"] == "Tolosa"
    assert (
        response.data["results"][0]["tipo_asociacion"]
        == AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
    )


@pytest.mark.django_db
def test_comedor_detail_includes_mobile_relevamiento_summary():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    programa = Programas.objects.create(nombre="Alimentar Comunidad")
    organizacion = Organizacion.objects.create(nombre="Organización Central")
    comedor = Comedor.objects.create(
        nombre="Espacio Relevado",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        organizacion=organizacion,
        programa=programa,
    )

    modalidad = TipoModalidadPrestacion.objects.create(nombre="Viandas")
    tipo_agua = TipoAgua.objects.create(nombre="Red")
    tipo_espacio = TipoEspacio.objects.create(nombre="Centro comunitario")
    frecuencia_limpieza = FrecuenciaLimpieza.objects.create(nombre="Diaria")
    cantidad_colaboradores = CantidadColaboradores.objects.create(nombre="5")
    distancia = TipoDistanciaTransporte.objects.create(nombre="1 cuadra")
    tecnologia = TipoTecnologia.objects.create(nombre="Celular")
    recurso = TipoRecurso.objects.create(nombre="Alimentos secos")
    frecuencia_recursos = FrecuenciaRecepcionRecursos.objects.create(nombre="Mensual")

    funcionamiento = FuncionamientoPrestacion.objects.create(
        modalidad_prestacion=modalidad
    )
    cocina = EspacioCocina.objects.create(
        almacenamiento_alimentos_secos=True,
        heladera=True,
        recipiente_residuos_reciclables=True,
        espacio_elaboracion_alimentos=True,
        abastecimiento_agua=tipo_agua,
        instalacion_electrica=True,
    )
    espacio_prestacion = EspacioPrestacion.objects.create(
        tiene_ventilacion=True,
        tiene_salida_emergencia=True,
        salida_emergencia_senializada=True,
        tiene_equipacion_incendio=True,
        tiene_botiquin=True,
        tiene_sanitarios=True,
        frecuencia_limpieza=frecuencia_limpieza,
    )
    espacio = Espacio.objects.create(
        tipo_espacio_fisico=tipo_espacio,
        cocina=cocina,
        prestacion=espacio_prestacion,
    )
    colaboradores = Colaboradores.objects.create(
        cantidad_colaboradores=cantidad_colaboradores,
        colaboradores_capacitados_alimentos=True,
        colaboradores_capacitados_salud_seguridad=True,
        colaboradores_recibieron_capacitacion_emergencias=True,
        colaboradores_recibieron_capacitacion_violencia=True,
    )
    recursos = FuenteRecursos.objects.create(
        recibe_donaciones_particulares=True,
        frecuencia_donaciones_particulares=frecuencia_recursos,
    )
    recursos.recursos_donaciones_particulares.add(recurso)
    compras = FuenteCompras.objects.create(supermercado=True, mayoristas=True)
    anexo = Anexo.objects.create(
        servicio_internet=True,
        tecnologia=tecnologia,
        zona_inundable=False,
        distancia_transporte=distancia,
        actividades_culturales=True,
        otras_actividades=True,
        cuales_otras_actividades="Murga",
    )
    Relevamiento.objects.create(
        comedor=comedor,
        estado="Finalizado",
        funcionamiento=funcionamiento,
        espacio=espacio,
        colaboradores=colaboradores,
        recursos=recursos,
        compras=compras,
        anexo=anexo,
    )

    representante = _create_pwa_user(
        comedor=comedor,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_detail_relevamiento",
    )
    client = _token_client(representante)

    response = client.get(f"/api/comedores/{comedor.id}/")

    assert response.status_code == 200
    assert response.data["relevamiento_actual_mobile"]["estado"] == "Finalizado"
    items = {
        item["pregunta"]: item["respuesta"]
        for item in response.data["relevamiento_actual_mobile"]["items"]
    }
    assert items["¿Qué tipo de servicio presta?"] == "Viandas"
    assert items["¿Cómo se abastece de agua?"] == "Red"
    assert items["¿En qué lugar realiza sus compras?"] == "Supermercado, Mayoristas"
    assert "Murga" in items["¿Qué tipo de actividades se realizan?"]


@pytest.mark.django_db
def test_representante_can_list_and_create_operadores(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_users",
    )
    operador_existente = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_existente",
        created_by=representante,
    )
    client = _token_client(representante)

    list_response = client.get(f"/api/comedores/{comedor_1.id}/usuarios/")
    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["id"] == operador_existente.id

    create_response = client.post(
        f"/api/comedores/{comedor_1.id}/usuarios/",
        {
            "username": "op_nuevo",
            "email": "op_nuevo@example.com",
            "password": "Secreta123!",
        },
        format="json",
    )
    assert create_response.status_code == 201
    assert create_response.data["username"] == "op_nuevo"
    assert create_response.data["rol"] == AccesoComedorPWA.ROL_OPERADOR


@pytest.mark.django_db
def test_operador_cannot_manage_users_endpoint(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_creador",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_solo",
        created_by=representante,
    )
    client = _token_client(operador)

    get_response = client.get(f"/api/comedores/{comedor_1.id}/usuarios/")
    post_response = client.post(
        f"/api/comedores/{comedor_1.id}/usuarios/",
        {"username": "otro", "email": "otro@example.com", "password": "Secreta123!"},
        format="json",
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403


@pytest.mark.django_db
def test_representante_can_deactivate_operador(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_deact",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_deact",
        created_by=representante,
    )
    client = _token_client(representante)

    response = client.patch(
        f"/api/comedores/{comedor_1.id}/usuarios/{operador.id}/desactivar/",
        {},
        format="json",
    )

    assert response.status_code == 200
    operador.refresh_from_db()
    acceso = AccesoComedorPWA.objects.get(user=operador, comedor=comedor_1)
    assert operador.is_active is False
    assert acceso.activo is False


@pytest.mark.django_db
def test_cualquier_representante_del_mismo_comedor_puede_desactivar(comedores):
    comedor_1, _ = comedores
    representante_1 = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_a",
    )
    representante_2 = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_b",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_multi_rep",
        created_by=representante_1,
    )
    client = _token_client(representante_2)

    response = client.patch(
        f"/api/comedores/{comedor_1.id}/usuarios/{operador.id}/desactivar/",
        {},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_nomina_scope_is_filtered_by_pwa_access(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_nomina",
    )
    client = _token_client(representante)

    admision_1 = Admision.objects.create(comedor=comedor_1)
    admision_2 = Admision.objects.create(comedor=comedor_2)
    nomina_asignada = Nomina.objects.create(admision=admision_1)
    nomina_fuera_scope = Nomina.objects.create(admision=admision_2)

    ok_response = client.patch(
        f"/api/comedores/nomina/{nomina_asignada.id}/",
        {"estado": "activo"},
        format="json",
    )
    forbidden_scope_response = client.patch(
        f"/api/comedores/nomina/{nomina_fuera_scope.id}/",
        {"estado": "activo"},
        format="json",
    )

    assert ok_response.status_code == 200
    assert forbidden_scope_response.status_code == 404


@pytest.mark.django_db
def test_rendiciones_list_and_detail_by_scope(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendiciones",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion_1 = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=1,
        anio=2026,
        observaciones="Rendición enero",
    )
    RendicionCuentaMensual.objects.create(
        comedor=comedor_2,
        mes=2,
        anio=2026,
        observaciones="Rendición fuera de scope",
    )

    list_response = client.get(f"/api/comedores/{comedor_1.id}/rendiciones/")
    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["id"] == rendicion_1.id

    detail_response = client.get(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion_1.id}/"
    )
    assert detail_response.status_code == 200
    assert detail_response.data["id"] == rendicion_1.id
    assert detail_response.data["estado"] == "elaboracion"

    forbidden_scope_response = client.get(
        f"/api/comedores/{comedor_2.id}/rendiciones/{rendicion_1.id}/"
    )
    assert forbidden_scope_response.status_code == 403


@pytest.mark.django_db
def test_crear_rendicion_mobile_con_datos_generales(comedores):
    comedor_1, _ = comedores
    comedor_1.codigo_de_proyecto = "PROY-REND-01"
    comedor_1.save(update_fields=["codigo_de_proyecto"])
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_crea_rendicion",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/",
        {
            "convenio": "CONV-2026-01",
            "numero_rendicion": 1,
            "periodo_inicio": "2026-01-01",
            "periodo_fin": "2026-01-31",
            "observaciones": "Primera presentación",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["convenio"] == "CONV-2026-01"
    assert response.data["numero_rendicion"] == 1
    assert response.data["estado"] == "elaboracion"
    assert response.data["periodo_inicio"] == "2026-01-01"
    assert response.data["periodo_fin"] == "2026-01-31"
    rendicion = RendicionCuentaMensual.objects.get(
        numero_rendicion=1, comedor=comedor_1
    )
    assert rendicion.usuario_creador == representante
    assert rendicion.usuario_ultima_modificacion == representante


@pytest.mark.django_db
def test_crear_rendicion_mobile_rechaza_numero_repetido_y_periodo_solapado(comedores):
    comedor_1, comedor_2 = comedores
    comedor_1.codigo_de_proyecto = "PROY-REND-02"
    comedor_1.save(update_fields=["codigo_de_proyecto"])
    comedor_2.codigo_de_proyecto = "PROY-REND-02"
    comedor_2.save(update_fields=["codigo_de_proyecto"])
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_valida_rendicion",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    RendicionCuentaMensual.objects.create(
        comedor=comedor_2,
        mes=1,
        anio=2026,
        convenio="CONV-2026-02",
        numero_rendicion=2,
        periodo_inicio=date(2026, 1, 1),
        periodo_fin=date(2026, 1, 31),
    )

    duplicate_number_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/",
        {
            "convenio": "CONV-2026-02",
            "numero_rendicion": 2,
            "periodo_inicio": "2026-02-01",
            "periodo_fin": "2026-02-28",
        },
        format="json",
    )
    assert duplicate_number_response.status_code == 400
    assert "numero_rendicion" in str(duplicate_number_response.data["detail"])

    overlap_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/",
        {
            "convenio": "CONV-2026-02",
            "numero_rendicion": 3,
            "periodo_inicio": "2026-01-15",
            "periodo_fin": "2026-02-15",
        },
        format="json",
    )
    assert overlap_response.status_code == 400
    assert "periodo" in str(overlap_response.data["detail"])


@pytest.mark.django_db
def test_rendiciones_mobile_scope_por_organizacion_y_proyecto():
    provincia = Provincia.objects.create(nombre="Santa Fe")
    organizacion_a = Organizacion.objects.create(nombre="Organización A")
    organizacion_b = Organizacion.objects.create(nombre="Organización B")
    comedor_a_1 = Comedor.objects.create(
        nombre="Espacio A1",
        provincia=provincia,
        organizacion=organizacion_a,
        codigo_de_proyecto="PROY-COMPARTIDO",
    )
    comedor_a_2 = Comedor.objects.create(
        nombre="Espacio A2",
        provincia=provincia,
        organizacion=organizacion_a,
        codigo_de_proyecto="PROY-COMPARTIDO",
    )
    comedor_b_1 = Comedor.objects.create(
        nombre="Espacio B1",
        provincia=provincia,
        organizacion=organizacion_b,
        codigo_de_proyecto="PROY-COMPARTIDO",
    )

    representante = _create_pwa_user(
        comedor=comedor_a_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_scope_org_project",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion_misma_organizacion = RendicionCuentaMensual.objects.create(
        comedor=comedor_a_2,
        mes=3,
        anio=2026,
        convenio="CONV-A",
        numero_rendicion=1,
        periodo_inicio=date(2026, 3, 1),
        periodo_fin=date(2026, 3, 31),
    )
    RendicionCuentaMensual.objects.create(
        comedor=comedor_b_1,
        mes=3,
        anio=2026,
        convenio="CONV-B",
        numero_rendicion=9,
        periodo_inicio=date(2026, 3, 1),
        periodo_fin=date(2026, 3, 31),
    )

    response = client.get(f"/api/comedores/{comedor_a_1.id}/rendiciones/")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == rendicion_misma_organizacion.id


@pytest.mark.django_db
def test_crear_rendicion_mobile_permite_mismo_proyecto_en_otra_organizacion():
    provincia = Provincia.objects.create(nombre="Entre Ríos")
    organizacion_a = Organizacion.objects.create(nombre="Organización Rendición A")
    organizacion_b = Organizacion.objects.create(nombre="Organización Rendición B")
    comedor_a = Comedor.objects.create(
        nombre="Espacio Rendición A",
        provincia=provincia,
        organizacion=organizacion_a,
        codigo_de_proyecto="PROY-ORG-01",
    )
    comedor_b = Comedor.objects.create(
        nombre="Espacio Rendición B",
        provincia=provincia,
        organizacion=organizacion_b,
        codigo_de_proyecto="PROY-ORG-01",
    )

    representante = _create_pwa_user(
        comedor=comedor_a,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_otro_org",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    RendicionCuentaMensual.objects.create(
        comedor=comedor_b,
        mes=4,
        anio=2026,
        convenio="CONV-ORG-01",
        numero_rendicion=7,
        periodo_inicio=date(2026, 4, 1),
        periodo_fin=date(2026, 4, 30),
    )

    response = client.post(
        f"/api/comedores/{comedor_a.id}/rendiciones/",
        {
            "convenio": "CONV-ORG-01",
            "numero_rendicion": 7,
            "periodo_inicio": "2026-04-01",
            "periodo_fin": "2026-04-30",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["convenio"] == "CONV-ORG-01"
    assert response.data["numero_rendicion"] == 7


@pytest.mark.django_db
def test_adjuntar_y_presentar_rendicion(comedores, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_adjuntar_rendicion",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=3,
        anio=2026,
    )

    present_without_docs_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/presentar/",
        {},
        format="json",
    )
    assert present_without_docs_response.status_code == 400

    categorias_obligatorias = [
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_II,
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_III,
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_V,
        DocumentacionAdjunta.CATEGORIA_EXTRACTO_BANCARIO,
        DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
    ]
    for categoria in categorias_obligatorias:
        archivo = SimpleUploadedFile(
            f"{categoria}.pdf",
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )
        upload_response = client.post(
            f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/documentacion/",
            {"archivo": archivo, "categoria": categoria},
            format="multipart",
        )
        assert upload_response.status_code == 201

    detail_response = client.get(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/",
    )
    assert detail_response.status_code == 200
    assert len(detail_response.data["documentacion"]) == 9
    categoria_extra = next(
        item
        for item in detail_response.data["documentacion"]
        if item["codigo"] == DocumentacionAdjunta.CATEGORIA_OTROS
    )
    assert categoria_extra["label"] == "Documentación Extra"

    present_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/presentar/",
        {},
        format="json",
    )
    assert present_response.status_code == 200
    rendicion.refresh_from_db()
    assert rendicion.documento_adjunto is True
    assert rendicion.estado == RendicionCuentaMensual.ESTADO_REVISION


@pytest.mark.django_db
def test_detalle_rendicion_mobile_expone_estado_y_observaciones_por_archivo(
    comedores, settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_detalle_estado_rendicion",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=4,
        anio=2026,
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
    )
    DocumentacionAdjunta.objects.create(
        nombre="formulario-ii.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_FORMULARIO_II,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "formulario-ii.pdf",
            b"%PDF-1.4 validado",
            content_type="application/pdf",
        ),
    )
    DocumentacionAdjunta.objects.create(
        nombre="comprobante.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Volver a subir el comprobante completo",
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante.pdf",
            b"%PDF-1.4 subsanar",
            content_type="application/pdf",
        ),
    )

    response = client.get(f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/")

    assert response.status_code == 200
    formulario = next(
        item
        for categoria in response.data["documentacion"]
        for item in categoria["archivos"]
        if item["nombre"] == "formulario-ii.pdf"
    )
    comprobante = next(
        item
        for categoria in response.data["documentacion"]
        for item in categoria["archivos"]
        if item["nombre"] == "comprobante.pdf"
    )
    assert formulario["estado"] == DocumentacionAdjunta.ESTADO_VALIDADO
    assert formulario["estado_label"] == "Validado"
    assert formulario["observaciones"] is None
    assert comprobante["estado"] == DocumentacionAdjunta.ESTADO_SUBSANAR
    assert comprobante["estado_label"] == "A Subsanar"
    assert comprobante["observaciones"] == "Volver a subir el comprobante completo"


@pytest.mark.django_db
def test_eliminar_rendicion_mobile_en_elaboracion(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_elimina_rendicion",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=5,
        anio=2026,
        estado=RendicionCuentaMensual.ESTADO_ELABORACION,
    )

    response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/eliminar/",
        {},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["detail"] == "Rendición eliminada."
    rendicion.refresh_from_db()
    assert rendicion.deleted_at is not None


@pytest.mark.django_db
def test_eliminar_rendicion_mobile_rechaza_revision(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_no_elimina_presentada",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=6,
        anio=2026,
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )

    response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/eliminar/",
        {},
        format="json",
    )

    assert response.status_code == 400
    assert "solo puede modificarse en elabor" in str(response.data["detail"])


@pytest.mark.django_db
def test_rendicion_en_subsanar_no_permite_borrar_documentacion_manualmente(
    comedores, settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_subsanar_bloqueada",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=6,
        anio=2026,
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
    )
    documento = DocumentacionAdjunta.objects.create(
        nombre="comprobante.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante.pdf",
            b"%PDF-1.4 original",
            content_type="application/pdf",
        ),
    )

    delete_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/documentacion/{documento.id}/eliminar/",
        {},
        format="json",
    )

    assert delete_response.status_code == 400
    assert "solo puede modificarse en elabor" in str(delete_response.data["detail"])


@pytest.mark.django_db
def test_rendicion_en_subsanar_permite_agregar_historial_para_comprobantes(
    comedores, settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_subsanar_comprobantes",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _token_client(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=6,
        anio=2026,
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
    )
    for categoria in (
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_II,
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_III,
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_V,
        DocumentacionAdjunta.CATEGORIA_EXTRACTO_BANCARIO,
    ):
        DocumentacionAdjunta.objects.create(
            nombre=f"{categoria}.pdf",
            categoria=categoria,
            estado=DocumentacionAdjunta.ESTADO_VALIDADO,
            rendicion_cuenta_mensual=rendicion,
            archivo=SimpleUploadedFile(
                f"{categoria}.pdf",
                b"%PDF-1.4 vigente",
                content_type="application/pdf",
            ),
        )
    observado = DocumentacionAdjunta.objects.create(
        nombre="comprobante-observado.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Subir una versión legible",
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante-observado.pdf",
            b"%PDF-1.4 original",
            content_type="application/pdf",
        ),
    )

    response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/documentacion/",
        {
            "archivo": SimpleUploadedFile(
                "comprobante-nuevo.pdf",
                b"%PDF-1.4 nuevo",
                content_type="application/pdf",
            ),
            "categoria": DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
            "documento_subsanado_id": str(observado.id),
        },
        format="multipart",
    )

    assert response.status_code == 201
    comprobantes = next(
        item
        for item in response.data["documentacion"]
        if item["codigo"] == DocumentacionAdjunta.CATEGORIA_COMPROBANTES
    )
    assert len(comprobantes["archivos"]) == 1
    nuevo_payload = comprobantes["archivos"][0]
    assert nuevo_payload["estado"] == DocumentacionAdjunta.ESTADO_PRESENTADO
    assert nuevo_payload["estado_visual"] == DocumentacionAdjunta.ESTADO_PRESENTADO
    assert nuevo_payload["estado_label_visual"] == "Presentado"
    assert nuevo_payload["documento_subsanado"] == observado.id
    assert len(nuevo_payload["subsanaciones"]) == 1
    observado_payload = nuevo_payload["subsanaciones"][0]
    assert observado_payload["id"] == observado.id
    assert observado_payload["estado"] == DocumentacionAdjunta.ESTADO_SUBSANAR
    assert observado_payload["estado_visual"] == "subsanado"
    assert observado_payload["estado_label_visual"] == "Subsanado"
    assert observado_payload["observaciones"] == "Subir una versión legible"
