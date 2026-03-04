"""Tests de caracterización más integrados para ``ComedorService``."""

import json
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.utils import timezone

from acompanamientos.models.hitos import Hitos
from admisiones.models.admisiones import Admision
from ciudadanos.models import Ciudadano
from comedores.models import AuditComedorPrograma, Comedor, Nomina, Observacion
from comedores.services import comedor_service as module
from core.constants import UserGroups
from core.models import Provincia, Sexo
from duplas.models import Dupla
from rendicioncuentasmensual.models import RendicionCuentaMensual

pytestmark = pytest.mark.django_db


def _create_user(username):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )


def _create_dupla(nombre, *, abogado, tecnico=None, coordinador=None):
    dupla = Dupla.objects.create(
        nombre=nombre,
        estado="Activo",
        abogado=abogado,
        coordinador=coordinador,
    )
    if tecnico is not None:
        dupla.tecnico.add(tecnico)
    return dupla


def _create_comedor(nombre, provincia, dupla=None):
    return Comedor.objects.create(
        nombre=nombre,
        provincia=provincia,
        dupla=dupla,
    )


def _ensure_group(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    return group


def test_get_filtered_comedores_coordinador_filtra_por_duplas_asignadas_reales():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    abogado = _create_user("abogado_coord")
    tecnico = _create_user("tecnico_coord")
    coordinador = _create_user("coord_gestion")
    _ensure_group(coordinador, UserGroups.COORDINADOR_GESTION)

    dupla_visible = _create_dupla("Dupla visible", abogado=abogado, tecnico=tecnico)
    dupla_oculta = _create_dupla("Dupla oculta", abogado=abogado)

    coordinador.profile.es_coordinador = True
    coordinador.profile.save(update_fields=["es_coordinador"])
    coordinador.profile.duplas_asignadas.add(dupla_visible)

    comedor_visible = _create_comedor("Comedor Visible", provincia, dupla_visible)
    _create_comedor("Comedor Oculto", provincia, dupla_oculta)
    _create_comedor("Comedor Sin Dupla", provincia, None)

    rows = list(module.ComedorService.get_filtered_comedores({}, user=coordinador))

    assert [row["id"] for row in rows] == [comedor_visible.id]
    assert rows[0]["dupla__nombre"] == "Dupla visible"
    assert rows[0]["estado_general"] == Comedor.ESTADO_GENERAL_DEFAULT


def test_get_filtered_comedores_coordinador_general_ve_todos_y_filtra_real():
    provincia = Provincia.objects.create(nombre="Buenos Aires CG")
    abogado = _create_user("abogado_cg")
    tecnico = _create_user("tecnico_cg")
    coordinador_general = _create_user("coord_general")
    _ensure_group(coordinador_general, UserGroups.COORDINADOR_GENERAL)

    dupla = _create_dupla("Dupla CG", abogado=abogado, tecnico=tecnico)
    _create_comedor("Comedor Uno CG", provincia, dupla)
    comedor_match = _create_comedor("Comedor Dos CG", provincia, None)

    filters = json.dumps(
        {
            "logic": "AND",
            "items": [{"field": "nombre", "op": "contains", "value": "Dos"}],
        }
    )
    rows = list(
        module.ComedorService.get_filtered_comedores(
            {"filters": filters},
            user=coordinador_general,
        )
    )

    assert [row["id"] for row in rows] == [comedor_match.id]
    assert rows[0]["nombre"] == "Comedor Dos CG"


def test_get_filtered_comedores_tecnico_filtra_por_dupla_real():
    provincia = Provincia.objects.create(nombre="Santa Fe")
    tecnico = _create_user("tecnico_dupla")
    tecnico_otro = _create_user("tecnico_otro")
    abogado = _create_user("abogado_dupla")
    _ensure_group(tecnico, UserGroups.TECNICO_COMEDOR)

    dupla_tecnico = _create_dupla("Dupla Técnica", abogado=abogado, tecnico=tecnico)
    dupla_ajena = _create_dupla("Dupla Ajena", abogado=abogado, tecnico=tecnico_otro)

    comedor_propio = _create_comedor("Comedor Propio", provincia, dupla_tecnico)
    _create_comedor("Comedor Ajeno", provincia, dupla_ajena)
    _create_comedor("Comedor Libre", provincia, None)

    rows = list(module.ComedorService.get_filtered_comedores({}, user=tecnico))

    assert [row["id"] for row in rows] == [comedor_propio.id]
    assert rows[0]["dupla__nombre"] == "Dupla Técnica"
    assert rows[0]["nombre"] == "Comedor Propio"


def test_get_filtered_comedores_abogado_filtra_por_dupla_real():
    provincia = Provincia.objects.create(nombre="Mendoza")
    abogado = _create_user("abogado_dupla_real")
    abogado_otro = _create_user("abogado_otro")
    tecnico = _create_user("tecnico_dupla_real")
    _ensure_group(abogado, UserGroups.ABOGADO_DUPLA)

    dupla_abogado = _create_dupla("Dupla Abogado", abogado=abogado, tecnico=tecnico)
    dupla_ajena = _create_dupla("Dupla Ajena", abogado=abogado_otro, tecnico=tecnico)

    comedor_propio = _create_comedor("Comedor Abogado", provincia, dupla_abogado)
    _create_comedor("Comedor Otro Abogado", provincia, dupla_ajena)

    rows = list(module.ComedorService.get_filtered_comedores({}, user=abogado))

    assert [row["id"] for row in rows] == [comedor_propio.id]
    assert rows[0]["dupla__nombre"] == "Dupla Abogado"


def test_get_filtered_comedores_coordinador_sin_duplas_reales_devuelve_vacio():
    provincia = Provincia.objects.create(nombre="La Pampa")
    coordinador = _create_user("coord_sin_duplas")
    _ensure_group(coordinador, UserGroups.COORDINADOR_GESTION)
    coordinador.profile.es_coordinador = True
    coordinador.profile.save(update_fields=["es_coordinador"])

    _create_comedor("Comedor Visible?", provincia, None)

    rows = list(module.ComedorService.get_filtered_comedores({}, user=coordinador))

    assert rows == []


def test_get_filtered_comedores_aplica_filtro_avanzado_real_sobre_scope():
    provincia = Provincia.objects.create(nombre="Neuquen")
    abogado = _create_user("abogado_filter")
    tecnico = _create_user("tecnico_filter")
    coordinador = _create_user("coord_filter")
    _ensure_group(coordinador, UserGroups.COORDINADOR_GESTION)
    coordinador.profile.es_coordinador = True
    coordinador.profile.save(update_fields=["es_coordinador"])

    dupla = _create_dupla("Dupla Filtro", abogado=abogado, tecnico=tecnico)
    coordinador.profile.duplas_asignadas.add(dupla)

    comedor_match = _create_comedor("Comedor Alpha", provincia, dupla)
    _create_comedor("Comedor Beta", provincia, dupla)

    filters = json.dumps(
        {
            "logic": "AND",
            "items": [
                {
                    "field": "nombre",
                    "op": "contains",
                    "value": "Alpha",
                }
            ],
        }
    )
    rows = list(
        module.ComedorService.get_filtered_comedores(
            {"filters": filters}, user=coordinador
        )
    )

    assert [row["id"] for row in rows] == [comedor_match.id]
    assert rows[0]["nombre"] == "Comedor Alpha"


def test_get_comedor_detail_object_prefetchea_relaciones_y_to_attrs():
    provincia = Provincia.objects.create(nombre="Cordoba")
    comedor = Comedor.objects.create(nombre="Comedor Detail", provincia=provincia)
    observacion = Observacion.objects.create(
        comedor=comedor,
        observacion="Observación de prueba",
    )
    rendicion = RendicionCuentaMensual.objects.create(comedor=comedor, mes=1, anio=2026)
    cambio_programa = AuditComedorPrograma.objects.create(comedor=comedor)

    obj = module.ComedorService.get_comedor_detail_object(comedor.id)

    assert obj.id == comedor.id
    assert hasattr(obj, "imagenes_optimized")
    assert hasattr(obj, "relevamientos_optimized")
    assert hasattr(obj, "observaciones_optimized")
    assert hasattr(obj, "clasificaciones_optimized")
    assert hasattr(obj, "rendiciones_optimized")
    assert hasattr(obj, "programa_changes_optimized")

    assert isinstance(obj.imagenes_optimized, list)
    assert isinstance(obj.relevamientos_optimized, list)
    assert isinstance(obj.clasificaciones_optimized, list)

    assert [x.id for x in obj.observaciones_optimized] == [observacion.id]
    assert [x.id for x in obj.rendiciones_optimized] == [rendicion.id]
    assert [x.id for x in obj.programa_changes_optimized] == [cambio_programa.id]


def test_get_comedor_detail_object_limita_y_ordena_observaciones_prefetch():
    provincia = Provincia.objects.create(nombre="Chaco")
    comedor = Comedor.objects.create(nombre="Comedor Obs", provincia=provincia)
    now = timezone.now()
    obs_ids = []
    for idx in range(4):
        obs = Observacion.objects.create(
            comedor=comedor,
            observacion=f"Obs {idx}",
            fecha_visita=now - timedelta(days=idx),
        )
        obs_ids.append(obs.id)

    obj = module.ComedorService.get_comedor_detail_object(comedor.id)

    # Debe traer máximo 3 y ordenado por fecha_visita desc
    assert len(obj.observaciones_optimized) == 3
    assert [o.id for o in obj.observaciones_optimized] == obs_ids[:3]


def test_get_nomina_detail_con_db_real_calcula_resumen_y_rangos():
    provincia = Provincia.objects.create(nombre="Entre Rios")
    comedor = Comedor.objects.create(nombre="Comedor Nomina", provincia=provincia)
    sexo_m = Sexo.objects.create(sexo="Masculino")
    sexo_f = Sexo.objects.create(sexo="Femenino")
    sexo_x = Sexo.objects.create(sexo="X")

    hoy = timezone.now().date()

    def _ciudadano(doc, edad_anios, sexo):
        return Ciudadano.objects.create(
            apellido=f"Apellido{doc}",
            nombre=f"Nombre{doc}",
            documento=doc,
            fecha_nacimiento=date(hoy.year - edad_anios, hoy.month, max(1, hoy.day)),
            sexo=sexo,
        )

    # 5 activos en distintos rangos + 1 pendiente
    c_nino = _ciudadano(1001, 10, sexo_m)
    c_ado = _ciudadano(1002, 16, sexo_f)
    c_adulto = _ciudadano(1003, 30, sexo_x)
    c_adulto_mayor = _ciudadano(1004, 55, sexo_f)
    c_mayor_avanzado = _ciudadano(1005, 70, sexo_m)
    c_pendiente = _ciudadano(1006, 40, sexo_m)

    for ciudadano, estado in [
        (c_nino, Nomina.ESTADO_ACTIVO),
        (c_ado, Nomina.ESTADO_ACTIVO),
        (c_adulto, Nomina.ESTADO_ACTIVO),
        (c_adulto_mayor, Nomina.ESTADO_ACTIVO),
        (c_mayor_avanzado, Nomina.ESTADO_ACTIVO),
        (c_pendiente, Nomina.ESTADO_PENDIENTE),
    ]:
        Nomina.objects.create(comedor=comedor, ciudadano=ciudadano, estado=estado)

    page_obj, cant_m, cant_f, cant_x, espera, total, rangos = (
        module.ComedorService.get_nomina_detail(
            comedor_pk=comedor.pk,
            page=1,
            per_page=10,
        )
    )

    assert page_obj.paginator.count == 6
    assert (cant_m, cant_f, cant_x, espera, total) == (3, 2, 1, 1, 6)
    assert rangos["total_activos"] == 5
    assert rangos["ninos"] == 1
    assert rangos["adolescentes"] == 1
    assert rangos["adultos"] == 1
    assert rangos["adultos_mayores"] == 1
    assert rangos["adulto_mayor_avanzado"] == 1
    # 1/5 -> 20% cada bucket activo
    assert rangos["pct_ninos"] == 20
    assert rangos["pct_adolescentes"] == 20
    assert rangos["pct_adultos"] == 20
    assert rangos["pct_adultos_mayores"] == 20
    assert rangos["pct_adulto_mayor_avanzado"] == 20


def test_get_nomina_detail_con_db_real_sin_activos_no_divide_por_cero():
    provincia = Provincia.objects.create(nombre="Jujuy")
    comedor = Comedor.objects.create(nombre="Comedor Sin Activos", provincia=provincia)
    sexo_m = Sexo.objects.create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Ana",
        documento=2001,
        fecha_nacimiento=date(1990, 1, 1),
        sexo=sexo_m,
    )
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano, estado=Nomina.ESTADO_PENDIENTE
    )

    _page_obj, _m, _f, _x, espera, total, rangos = (
        module.ComedorService.get_nomina_detail(
            comedor_pk=comedor.pk,
            page=1,
            per_page=10,
        )
    )

    assert espera == 1
    assert total == 1
    assert rangos["total_activos"] == 0
    assert rangos["pct_ninos"] == 0
    assert rangos["pct_adolescentes"] == 0
    assert rangos["pct_adultos"] == 0
    assert rangos["pct_adultos_mayores"] == 0
    assert rangos["pct_adulto_mayor_avanzado"] == 0


def test_crear_admision_desde_comedor_crea_admision_y_hito_reales(mocker):
    provincia = Provincia.objects.create(nombre="Rio Negro")
    comedor = Comedor.objects.create(nombre="Comedor Alta Adm", provincia=provincia)
    request = RequestFactory().post("/comedores/1/", {"admision": "incorporacion"})

    success_msg = mocker.patch("comedores.services.comedor_service.messages.success")
    info_msg = mocker.patch("comedores.services.comedor_service.messages.info")
    warn_msg = mocker.patch("comedores.services.comedor_service.messages.warning")
    err_msg = mocker.patch("comedores.services.comedor_service.messages.error")

    out = module.ComedorService.crear_admision_desde_comedor(request, comedor)

    assert out.status_code == 302
    adm = Admision.objects.get(comedor=comedor)
    assert adm.tipo == "incorporacion"
    assert Hitos.objects.filter(comedor=comedor).exists() is True
    assert success_msg.call_count == 2
    info_msg.assert_not_called()
    warn_msg.assert_not_called()
    err_msg.assert_not_called()


def test_crear_admision_desde_comedor_bloquea_incorporacion_duplicada_activa_real(
    mocker,
):
    provincia = Provincia.objects.create(nombre="Formosa")
    comedor = Comedor.objects.create(nombre="Comedor Duplicado", provincia=provincia)
    Admision.objects.create(comedor=comedor, tipo="incorporacion", activa=True)
    request = RequestFactory().post("/comedores/1/", {"admision": "incorporacion"})

    warn_msg = mocker.patch("comedores.services.comedor_service.messages.warning")
    mocker.patch("comedores.services.comedor_service.messages.success")
    mocker.patch("comedores.services.comedor_service.messages.info")
    mocker.patch("comedores.services.comedor_service.messages.error")

    out = module.ComedorService.crear_admision_desde_comedor(request, comedor)

    assert out.status_code == 302
    assert Admision.objects.filter(comedor=comedor, tipo="incorporacion").count() == 1
    warn_msg.assert_called_once()


def test_crear_admision_desde_comedor_bloquea_renovacion_sin_incorporacion_real(mocker):
    provincia = Provincia.objects.create(nombre="San Luis")
    comedor = Comedor.objects.create(nombre="Comedor Renov", provincia=provincia)
    request = RequestFactory().post("/comedores/1/", {"admision": "renovacion"})

    err_msg = mocker.patch("comedores.services.comedor_service.messages.error")
    mocker.patch("comedores.services.comedor_service.messages.warning")
    mocker.patch("comedores.services.comedor_service.messages.success")
    mocker.patch("comedores.services.comedor_service.messages.info")

    out = module.ComedorService.crear_admision_desde_comedor(request, comedor)

    assert out.status_code == 302
    assert Admision.objects.filter(comedor=comedor).count() == 0
    err_msg.assert_called_once()
