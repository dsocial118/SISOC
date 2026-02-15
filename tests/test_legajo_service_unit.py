from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from celiaquia.services import legajo_service as module

pytestmark = pytest.mark.django_db


def test_estado_helpers_and_recalc(mocker):
    module._estado_archivo_cargado_id.cache_clear()
    mocker.patch("celiaquia.services.legajo_service.EstadoLegajo.objects.only", return_value=SimpleNamespace(get=lambda **k: SimpleNamespace(id=7)))

    obj = SimpleNamespace(estado_id=None)
    fields = []
    module._set_estado_archivo_cargado(obj, fields)
    assert obj.estado_id == 7
    assert "estado" in fields

    obj2 = SimpleNamespace(archivo2=True, archivo3=False, archivos_ok=False)
    fields2 = []
    module._recalc_archivos_ok(obj2, fields2)
    assert obj2.archivos_ok is False


def test_subir_archivo_individual_and_errors(mocker):
    module._estado_archivo_cargado_id.cache_clear()
    mocker.patch("celiaquia.services.legajo_service._estado_archivo_cargado_id", return_value=1)

    leg = SimpleNamespace(pk=1, archivo1=None, archivo2=None, archivo3=None, estado_id=None, archivos_ok=False, save=mocker.Mock())
    with pytest.raises(ValidationError):
        module.LegajoService.subir_archivo_individual(leg, None)
    with pytest.raises(ValidationError):
        module.LegajoService.subir_archivo_individual(leg, object(), slot=4)

    out = module.LegajoService.subir_archivo_individual(leg, object(), slot=1)
    assert out is leg
    assert leg.save.called


def test_subir_archivos_iniciales_and_subsanacion(mocker):
    mocker.patch("celiaquia.services.legajo_service._estado_archivo_cargado_id", return_value=1)
    leg = SimpleNamespace(pk=1, archivo2=None, archivo3=None, estado_id=None, archivos_ok=False, save=mocker.Mock())

    with pytest.raises(ValidationError):
        module.LegajoService.subir_archivos_iniciales(leg, None, None, object())

    module.LegajoService.subir_archivos_iniciales(leg, None, object(), object())
    assert leg.save.called

    vt = SimpleNamespace()
    mocker.patch("celiaquia.services.legajo_service.ValidacionTecnica.objects.filter", return_value=SimpleNamespace(first=lambda: vt))
    mocker.patch("celiaquia.services.legajo_service.SubsanacionRespuesta.objects.create")

    leg2 = SimpleNamespace(pk=2, archivo1=None, archivo2=None, archivo3=None, estado_id=None, archivos_ok=False, save=mocker.Mock())
    with pytest.raises(ValidationError):
        module.LegajoService.actualizar_archivos_subsanacion(leg2)

    module.LegajoService.actualizar_archivos_subsanacion(leg2, archivo1=object(), usuario="u")
    assert leg2.save.called


def test_solicitar_subsanacion_all_loaded_and_faltantes(mocker):
    leg = SimpleNamespace(pk=1, revision_tecnico="APROBADO", save=mocker.Mock())
    mocker.patch("celiaquia.services.legajo_service.HistorialValidacionTecnica.objects.create")

    with pytest.raises(ValidationError):
        module.LegajoService.solicitar_subsanacion(leg, "", usuario="u")

    module.LegajoService.solicitar_subsanacion(leg, "motivo", usuario=SimpleNamespace(username="x"))
    assert leg.save.called

    qs = SimpleNamespace(filter=lambda **k: SimpleNamespace(exists=lambda: False))
    exp = SimpleNamespace(expediente_ciudadanos=qs)
    assert module.LegajoService.all_legajos_loaded(exp) is True

    # faltantes_archivos
    class Leg:
        def __init__(self):
            self.id = 9
            self.archivo2 = None
            self.archivo3 = None
            self.ciudadano = SimpleNamespace(id=1, documento="123", nombre="A", apellido="B")
            self.ciudadano_id = 1
            self.estado = SimpleNamespace(nombre="E")
            self.revision_tecnico = "R"
            self.archivos_ok = False

    class Qs:
        def select_related(self, *a, **k):
            return self

        def only(self, *a, **k):
            return self

        def filter(self, *a, **k):
            return self

        def values_list(self, *a, **k):
            return [1]

        def iterator(self):
            return iter([Leg()])

    exp2 = SimpleNamespace(id=1, expediente_ciudadanos=Qs())
    mocker.patch("celiaquia.services.legajo_service.FamiliaService.obtener_ids_responsables", return_value={1})
    mocker.patch.object(module.LegajoService, "get_archivos_requeridos_por_legajo", return_value={"archivo2": "A2", "archivo3": "A3"})
    out = module.LegajoService.faltantes_archivos(exp2, limit=1)
    assert len(out) == 1
    assert out[0]["es_responsable"] is True


def test_listar_legajos_and_subir_individual_branches(mocker):
    chain = SimpleNamespace(order_by=lambda *a, **k: "ordered")
    exp = SimpleNamespace(
        expediente_ciudadanos=SimpleNamespace(select_related=lambda *a, **k: chain)
    )
    assert module.LegajoService.listar_legajos(exp) == "ordered"

    mocker.patch("celiaquia.services.legajo_service._estado_archivo_cargado_id", return_value=1)
    leg = SimpleNamespace(
        pk=3,
        archivo1=object(),
        archivo2=None,
        archivo3=None,
        estado_id=None,
        archivos_ok=False,
        save=mocker.Mock(),
    )
    module.LegajoService.subir_archivo_individual(leg, object())
    assert leg.archivo2 is not None

    leg2 = SimpleNamespace(
        pk=4,
        archivo1=object(),
        archivo2=object(),
        archivo3=object(),
        estado_id=None,
        archivos_ok=True,
        save=mocker.Mock(),
    )
    with pytest.raises(ValidationError):
        module.LegajoService.subir_archivo_individual(leg2, object())


def test_es_responsable_and_archivos_requeridos_fallbacks(mocker):
    assert module.LegajoService._es_responsable(SimpleNamespace(id=5), {5}) is True
    assert module.LegajoService._es_responsable(SimpleNamespace(id=6), {5}) is False

    mocker.patch("celiaquia.services.legajo_service.FamiliaService.es_responsable", side_effect=RuntimeError("x"))
    assert module.LegajoService._es_responsable(SimpleNamespace(id=7), None) is False

    leg_resp = SimpleNamespace(pk=10, ciudadano=SimpleNamespace(id=1))
    out_resp = module.LegajoService.get_archivos_requeridos_por_legajo(leg_resp, {1})
    assert "ANSES" in out_resp["archivo3"]

    leg_minor = SimpleNamespace(
        pk=11,
        ciudadano=SimpleNamespace(id=2, documento="1", fecha_nacimiento=module.date(module.date.today().year - 10, 1, 1)),
    )
    out_minor = module.LegajoService.get_archivos_requeridos_por_legajo(leg_minor, {1})
    assert out_minor["archivo3"] == "Foto DNI"


def test_actualizar_subsanacion_warning_and_estado_cache_missing(mocker):
    class Missing(Exception):
        pass

    module._estado_archivo_cargado_id.cache_clear()
    mocker.patch("celiaquia.services.legajo_service.EstadoLegajo.DoesNotExist", Missing)
    mocker.patch(
        "celiaquia.services.legajo_service.EstadoLegajo.objects.only",
        return_value=SimpleNamespace(get=lambda **k: (_ for _ in ()).throw(Missing())),
    )
    assert module._estado_archivo_cargado_id() is None

    leg = SimpleNamespace(
        pk=12,
        archivo1=None,
        archivo2=None,
        archivo3=None,
        estado_id=None,
        archivos_ok=False,
        save=mocker.Mock(),
    )
    mocker.patch(
        "celiaquia.services.legajo_service.ValidacionTecnica.objects.filter",
        side_effect=Exception("db"),
    )
    module.LegajoService.actualizar_archivos_subsanacion(leg, archivo2=object(), usuario="x")
    assert leg.save.called
