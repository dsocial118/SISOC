"""Tests for test expediente service unit."""

from types import SimpleNamespace
import json

import pytest
from django.core.exceptions import ValidationError

from celiaquia.services import expediente_service as module

pytestmark = pytest.mark.django_db


def test_estado_helpers(mocker):
    module._estado_id.cache_clear()
    mocker.patch(
        "celiaquia.services.expediente_service.EstadoExpediente.objects.get_or_create",
        return_value=(SimpleNamespace(pk=9), True),
    )
    assert module._estado_id("CREADO") == 9

    exp = SimpleNamespace(save=mocker.Mock(), estado_id=None, usuario_modificador=None)
    mocker.patch("celiaquia.services.expediente_service._estado_id", return_value=3)
    module._set_estado(exp, "X")
    exp.save.assert_called_with(update_fields=["estado"])

    exp2 = SimpleNamespace(save=mocker.Mock(), estado_id=None, usuario_modificador=None)
    module._set_estado(exp2, "X", usuario="u")
    exp2.save.assert_called_with(update_fields=["estado", "usuario_modificador"])


def test_set_estado_observaciones_actualiza_solo_ultimo_historial(mocker):
    historial_actual = SimpleNamespace(observaciones="", save=mocker.Mock())

    class HistorialQS:
        def order_by(self, *args):
            assert args == ("-fecha",)
            return self

        def first(self):
            return historial_actual

    filter_mock = mocker.patch(
        "celiaquia.services.expediente_service.ExpedienteEstadoHistorial.objects.filter",
        return_value=HistorialQS(),
    )
    mocker.patch("celiaquia.services.expediente_service._estado_id", return_value=3)

    expediente = SimpleNamespace(
        pk=8,
        estado_id=None,
        usuario_modificador=None,
        save=mocker.Mock(),
    )
    observaciones = '{"resumen": "Importacion procesada."}'

    module._set_estado(
        expediente, "EN_ESPERA", usuario="u", observaciones=observaciones
    )

    filter_mock.assert_called_once_with(expediente=expediente, estado_nuevo_id=3)
    assert historial_actual.observaciones == observaciones
    historial_actual.save.assert_called_once_with(update_fields=["observaciones"])


def test_build_observaciones_importacion_resume_excluidos():
    out = json.loads(
        module._build_observaciones_importacion(
            {
                "validos": 0,
                "errores": 1,
                "excluidos": [
                    {
                        "documento": "123",
                        "apellido": "Perez",
                        "nombre": "Ana",
                        "estado_programa": "ACEPTADO",
                        "expediente_origen_id": 77,
                    }
                ],
            }
        )
    )
    assert "Se crearon 0 legajos" in out["resumen"]
    assert "Errores detectados: 1." in out["resumen"]
    assert "No se crearon 1 legajos" in out["excluidos"]
    assert "Documento 123" in out["excluidos"]
    assert "Exp #77" in out["excluidos"]
    assert out["excluidos_detalle"][0]["documento"] == "123"
    assert out["tiene_errores"] is True
    assert out["creados_total"] == 0
    assert out["errores_actuales"] == 1


def test_build_observaciones_importacion_sin_errores_deja_resumen_en_success():
    out = json.loads(
        module._build_observaciones_importacion(
            {
                "validos": 2,
                "errores": 0,
                "excluidos": [],
            }
        )
    )
    assert "Se crearon 2 legajos" in out["resumen"]
    assert out["excluidos"] == ""
    assert out["tiene_errores"] is False
    assert out["creados_total"] == 2
    assert out["errores_actuales"] == 0


def test_create_expediente_and_provincia_guard(mocker):
    mocker.patch("celiaquia.services.expediente_service._estado_id", return_value=1)
    created = SimpleNamespace(pk=7)

    create_mock = mocker.Mock(return_value=created)
    expediente_stub = SimpleNamespace(
        provincia_id=True, objects=SimpleNamespace(create=create_mock)
    )
    mocker.patch("celiaquia.services.expediente_service.Expediente", expediente_stub)

    user = SimpleNamespace(username="usr", profile=SimpleNamespace(provincia_id=12))
    out = module.ExpedienteService.create_expediente(
        user,
        {"numero_expediente": "N-1", "observaciones": "obs"},
        excel_masivo="f.xlsx",
    )
    assert out is created
    assert create_mock.call_args.kwargs["provincia_id"] == 12


def test_procesar_expediente_validations_and_success(mocker):
    with pytest.raises(ValidationError):
        module.ExpedienteService.procesar_expediente(
            SimpleNamespace(excel_masivo=None), usuario="u"
        )

    exp = SimpleNamespace(pk=8, excel_masivo="file")
    mocker.patch(
        "celiaquia.services.expediente_service.ImportacionService.importar_legajos_desde_excel",
        return_value={
            "validos": 2,
            "errores": 1,
            "excluidos_count": 3,
            "excluidos": ["x"],
        },
    )
    set_estado = mocker.patch("celiaquia.services.expediente_service._set_estado")

    out = module.ExpedienteService.procesar_expediente(exp, usuario="u")
    assert out == {
        "creados": 2,
        "errores": 1,
        "excluidos": 3,
        "excluidos_detalle": ["x"],
    }
    assert set_estado.call_count == 2
    assert set_estado.call_args_list[1].kwargs["observaciones"]


class _LegajosQS:
    def __init__(self, legs):
        self._legs = legs

    def all(self):
        return self._legs

    def count(self):
        return len(self._legs)

    def select_related(self, *args, **kwargs):
        return self

    def values_list(self, *args, **kwargs):
        return [leg.ciudadano_id for leg in self._legs]

    def filter(self, **kwargs):
        if kwargs == {"archivos_ok": False}:
            return SimpleNamespace(
                exists=lambda: any(not leg.archivos_ok for leg in self._legs)
            )
        raise AssertionError(f"Filtro no esperado: {kwargs}")

    def iterator(self):
        return iter(self._legs)


def test_confirmar_envio_paths(mocker):
    exp_bad = SimpleNamespace(estado=SimpleNamespace(nombre="CREADO"))
    with pytest.raises(ValidationError):
        module.ExpedienteService.confirmar_envio(exp_bad, usuario="u")

    legs = [
        SimpleNamespace(
            archivo2=None, archivo3=object(), archivos_ok=True, save=mocker.Mock()
        ),
        SimpleNamespace(
            archivo2=object(), archivo3=object(), archivos_ok=False, save=mocker.Mock()
        ),
    ]
    exp = SimpleNamespace(
        pk=9,
        estado=SimpleNamespace(nombre="EN_ESPERA"),
        expediente_ciudadanos=_LegajosQS(legs),
    )
    mocker.patch(
        "celiaquia.services.expediente_service.LegajoService.all_legajos_loaded",
        return_value=False,
    )
    with pytest.raises(ValidationError):
        module.ExpedienteService.confirmar_envio(exp, usuario="u")

    mocker.patch(
        "celiaquia.services.expediente_service.LegajoService.all_legajos_loaded",
        return_value=True,
    )
    set_estado = mocker.patch("celiaquia.services.expediente_service._set_estado")
    out = module.ExpedienteService.confirmar_envio(exp, usuario="u")
    assert out == {"validos": 2, "errores": 0}
    assert set_estado.called


def test_confirmar_envio_rechaza_doble_rol_sin_archivo1(mocker):
    leg = SimpleNamespace(
        pk=12,
        rol="beneficiario_y_responsable",
        archivo1=None,
        archivo2=object(),
        archivo3=object(),
        archivos_ok=False,
        ciudadano=SimpleNamespace(id=4, documento="400", fecha_nacimiento=None),
        ciudadano_id=4,
        save=mocker.Mock(),
    )
    exp = SimpleNamespace(
        pk=13,
        estado=SimpleNamespace(nombre="EN_ESPERA"),
        expediente_ciudadanos=_LegajosQS([leg]),
    )
    mocker.patch(
        "celiaquia.services.legajo_service.FamiliaService.obtener_ids_responsables",
        return_value={4},
    )

    with pytest.raises(ValidationError):
        module.ExpedienteService.confirmar_envio(exp, usuario="u")

    assert leg.archivos_ok is False


def test_asignar_tecnico_with_id_and_user(mocker):
    exp = SimpleNamespace(pk=10)
    tecnico = SimpleNamespace(username="tec")
    mocker.patch(
        "celiaquia.services.expediente_service.User.objects.get", return_value=tecnico
    )
    mocker.patch(
        "celiaquia.models.AsignacionTecnico.objects.get_or_create",
        return_value=(SimpleNamespace(), True),
    )
    set_estado = mocker.patch("celiaquia.services.expediente_service._set_estado")

    out = module.ExpedienteService.asignar_tecnico(exp, tecnico=1, usuario="u")
    assert out is exp
    assert set_estado.called
