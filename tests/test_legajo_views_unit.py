"""Tests for test legajo views unit."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from celiaquia.views import legajo as module

pytestmark = pytest.mark.django_db


def _user(auth=True, superuser=False, groups=None):
    groups = set(groups or [])
    return SimpleNamespace(
        id=1,
        is_authenticated=auth,
        is_superuser=superuser,
        groups=SimpleNamespace(
            filter=lambda **k: SimpleNamespace(exists=lambda: k.get("name") in groups)
        ),
    )


def _call_post_unwrapped(view, request, *args, **kwargs):
    return view.__class__.post.__wrapped__(view, request, *args, **kwargs)


def test_in_group():
    assert module._in_group(_user(groups={"A"}), "A") is True
    assert module._in_group(_user(groups={"A"}), "B") is False


def test_archivo_upload_dispatch_and_post_paths(mocker):
    rf = RequestFactory()
    leg = SimpleNamespace(
        pk=2,
        expediente=SimpleNamespace(pk=3),
        archivo2=None,
        archivo3=None,
        revision_tecnico="OTRO",
    )

    req = rf.get("/")
    req.user = _user()
    mocker.patch("celiaquia.views.legajo.get_object_or_404", return_value=leg)
    mocker.patch(
        "celiaquia.views.legajo.can_edit_legajo_files", side_effect=PermissionDenied("x")
    )
    resp = module.LegajoArchivoUploadView().dispatch(req, pk=2, expediente_id=3)
    assert resp.status_code == 403

    view = module.LegajoArchivoUploadView()
    view.exp_ciud = leg

    bad_file = SimpleUploadedFile("a.txt", b"x")
    req_bad = rf.post("/", {"slot": "abc", "archivo": bad_file})
    req_bad.user = _user()
    resp_bad = _call_post_unwrapped(view, req_bad)
    assert resp_bad.status_code == 400

    ok_file = SimpleUploadedFile("a.txt", b"x")
    req_ok = rf.post("/", {"slot": "1", "archivo": ok_file})
    req_ok.user = _user()
    mocker.patch("celiaquia.views.legajo.LegajoService.subir_archivo_individual")
    resp_ok = _call_post_unwrapped(view, req_ok)
    assert resp_ok.status_code == 200

    req_missing = rf.post("/", {"archivo2": SimpleUploadedFile("2.txt", b"2")})
    req_missing.user = _user()
    resp_missing = _call_post_unwrapped(view, req_missing)
    assert resp_missing.status_code == 400


def test_archivo_upload_double_and_subsanacion_paths(mocker):
    rf = RequestFactory()
    leg = SimpleNamespace(
        pk=4,
        expediente=SimpleNamespace(pk=3),
        archivo2=object(),
        archivo3=object(),
        revision_tecnico=module.RevisionTecnico.SUBSANAR,
    )
    view = module.LegajoArchivoUploadView()
    view.exp_ciud = leg

    req = rf.post(
        "/",
        {
            "archivo2": SimpleUploadedFile("2.txt", b"2"),
            "archivo3": SimpleUploadedFile("3.txt", b"3"),
        },
    )
    req.user = _user()

    upd = mocker.patch("celiaquia.views.legajo.LegajoService.actualizar_archivos_subsanacion")
    resp = _call_post_unwrapped(view, req)
    assert resp.status_code == 200
    assert upd.called

    mocker.patch(
        "celiaquia.views.legajo.LegajoService.actualizar_archivos_subsanacion",
        side_effect=ValidationError("no"),
    )
    resp_val = _call_post_unwrapped(view, req)
    assert resp_val.status_code == 400


def test_rechazar_view_paths(mocker):
    rf = RequestFactory()
    req = rf.post("/")
    req.user = _user()
    leg = SimpleNamespace(pk=9, expediente=SimpleNamespace(), save=mocker.Mock(), revision_tecnico=None)

    view = module.LegajoRechazarView()
    mocker.patch("celiaquia.views.legajo.get_object_or_404", return_value=leg)
    mocker.patch("celiaquia.views.legajo.can_review_legajo")
    mocker.patch("celiaquia.views.legajo.CupoService.liberar_slot")
    resp = _call_post_unwrapped(view, req, pk=9, expediente_id=1)
    assert resp.status_code == 200

    mocker.patch(
        "celiaquia.views.legajo.CupoService.liberar_slot",
        side_effect=module.CupoNoConfigurado("x"),
    )
    resp2 = _call_post_unwrapped(view, req, pk=9, expediente_id=1)
    assert resp2.status_code == 200


def test_suspender_view_permission_and_success(mocker):
    rf = RequestFactory()
    view = module.LegajoSuspenderView()

    req_anon = rf.post("/")
    req_anon.user = _user(auth=False)
    with pytest.raises(PermissionDenied):
        _call_post_unwrapped(view, req_anon, pk=1, expediente_id=1)

    req = rf.post("/")
    req.user = _user(groups={"TecnicoCeliaquia"})
    leg = SimpleNamespace(
        pk=2,
        expediente=SimpleNamespace(
            asignaciones_tecnicos=SimpleNamespace(
                filter=lambda **k: SimpleNamespace(exists=lambda: True)
            )
        ),
        es_titular_activo=True,
        save=mocker.Mock(),
    )
    mocker.patch("celiaquia.views.legajo.get_object_or_404", return_value=leg)
    mocker.patch("celiaquia.views.legajo.CupoService.suspender_slot")

    resp = _call_post_unwrapped(view, req, pk=2, expediente_id=1)
    assert resp.status_code == 200


def test_baja_subsanar_y_eliminar_views(mocker):
    rf = RequestFactory()

    # Baja
    req_baja = rf.post("/")
    req_baja.user = _user(groups={"CoordinadorCeliaquia"})
    leg = SimpleNamespace(pk=3, expediente=SimpleNamespace(), save=mocker.Mock(), revision_tecnico=None, es_titular_activo=True)
    mocker.patch("celiaquia.views.legajo.get_object_or_404", return_value=leg)
    mocker.patch("celiaquia.views.legajo.CupoService.liberar_slot")
    resp_baja = _call_post_unwrapped(module.LegajoBajaView(), req_baja, pk=3, expediente_id=1)
    assert resp_baja.status_code == 200

    # Subsanar
    req_sub = rf.post("/", {"comentario": "faltan docs"})
    req_sub.user = _user(groups={"CoordinadorCeliaquia"})
    leg_sub = SimpleNamespace(
        pk=7,
        expediente=SimpleNamespace(asignaciones_tecnicos=SimpleNamespace(filter=lambda **k: SimpleNamespace(exists=lambda: True))),
        save=mocker.Mock(),
        revision_tecnico=None,
        comentario_subsanacion="",
    )
    mocker.patch("celiaquia.views.legajo.get_object_or_404", return_value=leg_sub)
    mocker.patch("celiaquia.views.legajo.EstadoLegajo.objects.get_or_create", return_value=(SimpleNamespace(), True))
    resp_sub = _call_post_unwrapped(module.LegajoSubsanarView(), req_sub, pk=1, legajo_id=7)
    assert resp_sub.status_code == 200

    # Eliminar
    req_del = rf.post("/")
    req_del.user = _user(groups={"CoordinadorCeliaquia"})
    leg_del = SimpleNamespace(pk=10, delete=mocker.Mock())
    mocker.patch("celiaquia.views.legajo.get_object_or_404", return_value=leg_del)
    mocker.patch("django.db.transaction.atomic", return_value=nullcontext())
    mocker.patch("celiaquia.views.legajo.CupoService.liberar_slot")
    mocker.patch("celiaquia.models.CupoMovimiento.objects.filter", return_value=SimpleNamespace(delete=mocker.Mock()))
    mocker.patch("celiaquia.models.PagoNomina.objects.filter", return_value=SimpleNamespace(delete=mocker.Mock()))

    resp_del = _call_post_unwrapped(module.LegajoEliminarView(), req_del, pk=1, legajo_id=10)
    assert resp_del.status_code == 200
