from types import SimpleNamespace

import pytest

from celiaquia.services import comentarios_service as module

pytestmark = pytest.mark.django_db


def test_agregar_comentario_and_specialized_wrappers(mocker):
    created = object()
    create_mock = mocker.patch(
        "celiaquia.services.comentarios_service.HistorialComentarios.objects.create",
        return_value=created,
    )

    leg = SimpleNamespace(
        revision_tecnico="REV",
        estado_validacion_renaper="OK",
        resultado_sintys="CRUCE_OK",
    )

    out = module.ComentariosService.agregar_comentario(
        legajo=leg,
        tipo_comentario="T",
        comentario="hola",
        usuario="u",
        archivo_adjunto="a.pdf",
    )
    assert out is created
    assert create_mock.call_args.kwargs["estado_relacionado"] == "REV"

    spy = mocker.patch(
        "celiaquia.services.comentarios_service.ComentariosService.agregar_comentario",
        return_value=created,
    )
    module.ComentariosService.agregar_validacion_tecnica(leg, "v", usuario="u")
    module.ComentariosService.agregar_subsanacion_motivo(leg, "m", usuario="u")
    module.ComentariosService.agregar_subsanacion_respuesta(leg, "r", usuario="u")
    module.ComentariosService.agregar_validacion_renaper(leg, "ren", usuario="u")
    module.ComentariosService.agregar_cruce_sintys(leg, "obs", usuario="u")
    module.ComentariosService.agregar_observacion_pago(leg, "p", usuario="u")
    assert spy.call_count == 6


def test_obtener_historial_y_por_tipo():
    historial = [1, 2]

    class H:
        def __init__(self):
            self.kw = None

        def select_related(self, *_a):
            return self

        def all(self):
            return historial

        def filter(self, **kwargs):
            self.kw = kwargs
            return self

    h = H()
    leg = SimpleNamespace(historial_comentarios=h)

    assert module.ComentariosService.obtener_historial_legajo(leg) == historial
    out = module.ComentariosService.obtener_comentarios_por_tipo(leg, "ABC")
    assert out is h
    assert h.kw == {"tipo_comentario": "ABC"}


def test_migrar_comentarios_existentes(mocker):
    class _Q:
        def __init__(self, **_kwargs):
            pass

        def __or__(self, _other):
            return self

        def __and__(self, _other):
            return self

    module.models = SimpleNamespace(Q=_Q)

    leg1 = SimpleNamespace(
        subsanacion_motivo="mot",
        subsanacion_usuario="u",
        subsanacion_renaper_comentario="ren",
        observacion_cruce="obs",
    )
    leg2 = SimpleNamespace(
        subsanacion_motivo="",
        subsanacion_usuario=None,
        subsanacion_renaper_comentario="",
        observacion_cruce="",
    )

    class _QS:
        def exclude(self, *_a, **_k):
            return [leg1, leg2]

    mocker.patch(
        "celiaquia.services.comentarios_service.ExpedienteCiudadano.objects.filter",
        return_value=_QS(),
    )
    s1 = mocker.patch(
        "celiaquia.services.comentarios_service.ComentariosService.agregar_subsanacion_motivo"
    )
    s2 = mocker.patch(
        "celiaquia.services.comentarios_service.ComentariosService.agregar_validacion_renaper"
    )
    s3 = mocker.patch(
        "celiaquia.services.comentarios_service.ComentariosService.agregar_cruce_sintys"
    )

    assert module.ComentariosService.migrar_comentarios_existentes() == 3
    assert s1.called and s2.called and s3.called
