"""Tests de las correcciones de correctitud de datos del reporter-provincias.

Se usan RequestFactory + get_context_data (en lugar de client.get(reverse(...)))
para ejercitar la lógica del reporte sin cargar todo el ROOT_URLCONF.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.test import RequestFactory
from django.utils import timezone

from ciudadanos.models import Ciudadano, GrupoFamiliar
from users.models import Profile

from celiaquia.models import (
    EstadoCupo,
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    ProvinciaCupo,
    ResultadoSintys,
    RevisionTecnico,
)
from celiaquia.services.familia_service import FamiliaService
from celiaquia.views.reporter_provincias import ReporterProvinciasView
from celiaquia.views.validacion_renaper import ValidacionRenaperView
from core.models import Provincia


def _user(username, provincia=None, es_provincial=False):
    user = User.objects.create_user(username=username, password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia", codename="view_expediente"
    )
    user.user_permissions.add(permission)
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = es_provincial
    profile.provincia = provincia
    profile.save()
    return user


def _contexto(user, params=None):
    request = RequestFactory().get("/reporter-provincias/", params or {})
    request.user = user
    view = ReporterProvinciasView()
    view.setup(request)
    return view.get_context_data()


def _expediente(user, nombre_estado="CREADO"):
    estado = EstadoExpediente.objects.create(nombre=nombre_estado)
    return Expediente.objects.create(
        usuario_provincia=user, estado=estado, numero_expediente="EXP-FIX"
    )


def _legajo(expediente, estado_legajo, documento, provincia=None, **kwargs):
    ciudadano = Ciudadano.objects.create(
        apellido="Ape",
        nombre=f"N{documento}",
        documento=documento,
        provincia=provincia,
        fecha_nacimiento=kwargs.pop("fecha_nacimiento", date(1985, 1, 1)),
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        **kwargs,
    )


@pytest.mark.django_db
def test_fecha_hasta_incluye_el_ultimo_dia():
    """Fix #1/#2: filtrar Desde=Hasta=hoy debe incluir el legajo creado hoy."""
    user = _user("fix-fechas")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")
    exp = _expediente(user)
    _legajo(exp, estado_legajo, 50000001, revision_tecnico="APROBADO")

    hoy = timezone.localdate().isoformat()
    ctx = _contexto(user, {"fecha_desde": hoy, "fecha_hasta": hoy})

    assert ctx["total_casos"] == 1  # antes del fix esto daba 0


@pytest.mark.django_db
def test_expedientes_por_provincia_suma_igual_a_total():
    """Fix #4/#11: la suma de 'casos' por provincia coincide con total_casos."""
    user = _user("fix-agg")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")
    bsas = Provincia.objects.create(nombre="Buenos Aires")
    cba = Provincia.objects.create(nombre="Cordoba")
    exp = _expediente(user)
    _legajo(exp, estado_legajo, 50000101, provincia=bsas)
    _legajo(exp, estado_legajo, 50000102, provincia=bsas)
    _legajo(exp, estado_legajo, 50000103, provincia=cba)

    ctx = _contexto(user)

    filas = ctx["expedientes_por_provincia"]
    assert sum(f["casos"] for f in filas) == ctx["total_casos"] == 3
    assert round(sum(f["share"] for f in filas)) == 100


@pytest.mark.django_db
def test_clasificacion_doble_rol_por_vinculo_familiar():
    """Fix #8: un responsable que además es beneficiario en su familia es doble rol."""
    user = _user("fix-doblerol")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")
    exp = _expediente(user)
    legajo = _legajo(
        exp,
        estado_legajo,
        50000201,
        rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
        revision_tecnico="APROBADO",
    )
    otro_responsable = Ciudadano.objects.create(
        apellido="Cuidador", nombre="Ppal", documento=50000202
    )
    # El ciudadano del legajo figura como hijo (ciudadano_2) de otro cuidador.
    GrupoFamiliar.objects.create(
        ciudadano_1=otro_responsable,
        ciudadano_2=legajo.ciudadano,
        vinculo=GrupoFamiliar.RELACION_PADRE,
        cuidador_principal=True,
    )

    ctx = _contexto(user)
    counts = {i["code"]: i["count"] for i in ctx["clasificacion_aprobados"]["items"]}

    assert counts["doble_rol"] == 1
    assert counts["responsable"] == 0


@pytest.mark.django_db
def test_provincia_fuera_de_scope_no_se_refleja_en_alcance():
    """Fix #9: ?provincia= ajeno al scope no debe fijarse como provincia_actual."""
    propia = Provincia.objects.create(nombre="Propia")
    ajena = Provincia.objects.create(nombre="Ajena")
    user = _user("fix-scope", provincia=propia, es_provincial=True)

    ctx = _contexto(user, {"provincia": str(ajena.id)})

    assert ctx["provincia_actual"] is not None
    assert ctx["provincia_actual"].id == propia.id
    assert ctx["provincia_actual"].id != ajena.id


@pytest.mark.django_db
def test_metricas_support_dice_legajos_no_expedientes():
    """Fix #7: el support de las tarjetas de documentación habla de 'legajos'."""
    user = _user("fix-label")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")
    exp = _expediente(user)
    _legajo(exp, estado_legajo, 50000301)

    ctx = _contexto(user)
    supports = " ".join(m["support"] for m in ctx["metricas_principales"])

    assert "legajos con archivos" in supports
    assert "expedientes con archivos" not in supports


@pytest.mark.django_db
def test_paginacion_ordena_con_desempate_estable():
    """Fix #5: la paginación ordena por (-creado_en, -pk), no solo -creado_en."""
    user = _user("fix-pag")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")
    exp = _expediente(user)
    _legajo(exp, estado_legajo, 50000401)

    ctx = _contexto(user)
    order = ctx["page_obj"].paginator.object_list.query.order_by

    assert tuple(order) == ("-creado_en", "-pk")


@pytest.mark.django_db
def test_renaper_rechazado_degrada_y_libera_cupo():
    """Fix #3: estado 2 (Rechazado) degrada a RECHAZADO y libera el cupo ocupado."""
    admin = User.objects.create_superuser("renaper-admin", password="pass")
    provincia = Provincia.objects.create(nombre="Salta")
    ProvinciaCupo.objects.create(provincia=provincia, total_asignado=10, usados=1)
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")
    exp = _expediente(admin)
    legajo = _legajo(
        exp,
        estado_legajo,
        50000501,
        provincia=provincia,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
        revision_tecnico="APROBADO",
        resultado_sintys=ResultadoSintys.MATCH,
        estado_cupo=EstadoCupo.DENTRO,
        es_titular_activo=True,
    )

    request = RequestFactory().post(
        f"/celiaquia/expediente/{exp.pk}/renaper/{legajo.pk}/", {}
    )
    request.user = admin
    view = ValidacionRenaperView()
    view._guardar_validacion_estado(request, exp.pk, legajo.pk, "2")

    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.RECHAZADO
    assert legajo.estado_validacion_renaper == 2
    assert legajo.estado_cupo == EstadoCupo.NO_EVAL
    assert legajo.es_titular_activo is False
    provincia.cupo.refresh_from_db()
    assert provincia.cupo.usados == 0  # cupo liberado


@pytest.mark.django_db
def test_crear_relacion_familiar_refresca_archivos_ok():
    """Fix #6: crear una relación familiar recomputa archivos_ok cacheado."""
    user = _user("fix-archivos")
    estado_legajo = EstadoLegajo.objects.create(nombre="PENDIENTE")
    exp = _expediente(user)
    responsable = _legajo(
        exp,
        estado_legajo,
        50000601,
        rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
    )
    hijo = _legajo(exp, estado_legajo, 50000602)

    # El legajo (sin archivos) nunca tiene documentación completa; forzamos el
    # cache a un valor obsoleto (True) saltando save() con update().
    ExpedienteCiudadano.objects.filter(pk=responsable.pk).update(archivos_ok=True)

    FamiliaService.crear_relacion_responsable_hijo(
        responsable.ciudadano_id, hijo.ciudadano_id
    )

    responsable.refresh_from_db()
    assert responsable.archivos_ok is False  # recomputado al crear la relación
