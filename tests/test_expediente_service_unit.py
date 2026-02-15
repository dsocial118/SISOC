from types import SimpleNamespace

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


def test_create_expediente_and_provincia_guard(mocker):
    mocker.patch("celiaquia.services.expediente_service._estado_id", return_value=1)
    created = SimpleNamespace(pk=7)

    create_mock = mocker.Mock(return_value=created)
    expediente_stub = SimpleNamespace(provincia_id=True, objects=SimpleNamespace(create=create_mock))
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
        return_value={"validos": 2, "errores": 1, "excluidos_count": 3, "excluidos": ["x"]},
    )
    set_estado = mocker.patch("celiaquia.services.expediente_service._set_estado")

    out = module.ExpedienteService.procesar_expediente(exp, usuario="u")
    assert out == {"creados": 2, "errores": 1, "excluidos": 3, "excluidos_detalle": ["x"]}
    assert set_estado.call_count == 2


class _LegajosQS:
    def __init__(self, legs):
        self._legs = legs

    def all(self):
        return self._legs

    def count(self):
        return len(self._legs)


def test_confirmar_envio_paths(mocker):
    exp_bad = SimpleNamespace(estado=SimpleNamespace(nombre="CREADO"))
    with pytest.raises(ValidationError):
        module.ExpedienteService.confirmar_envio(exp_bad, usuario="u")

    legs = [
        SimpleNamespace(archivo2=None, archivo3=object(), archivos_ok=True, save=mocker.Mock()),
        SimpleNamespace(archivo2=object(), archivo3=object(), archivos_ok=False, save=mocker.Mock()),
    ]
    exp = SimpleNamespace(
        pk=9,
        estado=SimpleNamespace(nombre="EN_ESPERA"),
        expediente_ciudadanos=_LegajosQS(legs),
    )
    mocker.patch("celiaquia.services.expediente_service.LegajoService.all_legajos_loaded", return_value=False)
    with pytest.raises(ValidationError):
        module.ExpedienteService.confirmar_envio(exp, usuario="u")

    mocker.patch("celiaquia.services.expediente_service.LegajoService.all_legajos_loaded", return_value=True)
    set_estado = mocker.patch("celiaquia.services.expediente_service._set_estado")
    out = module.ExpedienteService.confirmar_envio(exp, usuario="u")
    assert out == {"validos": 2, "errores": 0}
    assert set_estado.called


def test_asignar_tecnico_with_id_and_user(mocker):
    exp = SimpleNamespace(pk=10)
    tecnico = SimpleNamespace(username="tec")
    mocker.patch("celiaquia.services.expediente_service.User.objects.get", return_value=tecnico)
    mocker.patch("celiaquia.models.AsignacionTecnico.objects.get_or_create", return_value=(SimpleNamespace(), True))
    set_estado = mocker.patch("celiaquia.services.expediente_service._set_estado")

    out = module.ExpedienteService.asignar_tecnico(exp, tecnico=1, usuario="u")
    assert out is exp
    assert set_estado.called
