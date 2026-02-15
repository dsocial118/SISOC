"""Tests for test admisiones web views unit."""

from types import SimpleNamespace

from admisiones.views import web_views as module


def _user(superuser=False):
    return SimpleNamespace(is_authenticated=True, is_superuser=superuser)


class _Req(SimpleNamespace):
    pass


def test_actualizar_estado_archivo_success_and_error(mocker):
    req = _Req(user=_user(), method="GET")

    mocker.patch("admisiones.views.web_views.AdmisionService.actualizar_estado_ajax", return_value={
        "success": True,
        "nuevo_estado": "Aceptado",
        "grupo_usuario": "g",
        "mostrar_select": True,
        "opciones": ["a"],
    })
    resp = module.actualizar_estado_archivo(req)
    assert resp.status_code == 200

    mocker.patch("admisiones.views.web_views.AdmisionService.actualizar_estado_ajax", return_value={"success": False, "error": "bad"})
    resp2 = module.actualizar_estado_archivo(req)
    assert resp2.status_code == 400


def test_actualizar_numero_gde_and_convenio_numero(mocker):
    req = _Req(user=_user(), method="POST")

    mocker.patch("admisiones.views.web_views.AdmisionService.actualizar_numero_gde_ajax", return_value={"success": True, "numero_gde": "1", "valor_anterior": "0"})
    assert module.actualizar_numero_gde_archivo(req).status_code == 200

    mocker.patch("admisiones.views.web_views.AdmisionService.actualizar_numero_gde_ajax", return_value={"success": False, "error": "e"})
    assert module.actualizar_numero_gde_archivo(req).status_code == 400

    mocker.patch("admisiones.views.web_views.AdmisionService.actualizar_convenio_numero_ajax", return_value={"success": True, "convenio_numero": "12", "valor_anterior": None})
    assert module.actualizar_convenio_numero(req).status_code == 200

    mocker.patch("admisiones.views.web_views.AdmisionService.actualizar_convenio_numero_ajax", return_value={"success": False, "error": "e"})
    assert module.actualizar_convenio_numero(req).status_code == 400


def test_crear_documento_personalizado_paths(mocker):
    req = _Req(FILES={"archivo": object()}, POST={"nombre": "Doc"}, user=_user(), method="POST")

    archivo = SimpleNamespace(admision=SimpleNamespace())
    mocker.patch("admisiones.views.web_views.AdmisionService.crear_documento_personalizado", return_value=(archivo, None))
    mocker.patch("admisiones.views.web_views.AdmisionService.serialize_documento_personalizado", return_value={"id": 1})
    mocker.patch("admisiones.views.web_views.render_to_string", return_value="<tr></tr>")
    assert module.crear_documento_personalizado(req, 1).status_code == 201

    mocker.patch("admisiones.views.web_views.AdmisionService.crear_documento_personalizado", return_value=(None, "sin permiso"))
    assert module.crear_documento_personalizado(req, 1).status_code == 403

    mocker.patch("admisiones.views.web_views.AdmisionService.crear_documento_personalizado", return_value=(None, "otro"))
    assert module.crear_documento_personalizado(req, 1).status_code == 400


def test_eliminar_archivo_admision_method_and_permission_paths(mocker):
    req_bad = _Req(method="GET", user=_user())
    assert module.eliminar_archivo_admision(req_bad, 1, 2).status_code == 405

    admision = SimpleNamespace(comedor=None)
    req = _Req(method="DELETE", user=_user(False), GET={})
    mocker.patch("admisiones.views.web_views.get_object_or_404", return_value=admision)

    resp = module.eliminar_archivo_admision(req, 1, 2)
    assert resp.status_code == 403


def test_eliminar_archivo_admision_estado_no_permitido_and_success(mocker):
    comedor = SimpleNamespace()
    admision = SimpleNamespace(comedor=comedor)
    req = _Req(method="DELETE", user=_user(False), GET={"archivo_id": "5"})

    mocker.patch("admisiones.views.web_views.get_object_or_404", side_effect=[admision, SimpleNamespace()])
    mocker.patch("admisiones.views.web_views.AdmisionService._verificar_permiso_dupla", return_value=True)

    archivo_qs = mocker.Mock()
    archivo_qs.first.side_effect = [None, SimpleNamespace(estado="Aceptado", documentacion=SimpleNamespace(nombre="D"), nombre_personalizado=None)]
    mocker.patch("admisiones.views.web_views.ArchivoAdmision.objects.filter", return_value=archivo_qs)

    resp = module.eliminar_archivo_admision(req, 1, 2)
    assert resp.status_code == 400

    mocker.patch("admisiones.views.web_views.get_object_or_404", return_value=admision)

    archivo_ok = SimpleNamespace(
        estado="pendiente",
        documentacion=SimpleNamespace(nombre="Doc", id=9),
        nombre_personalizado=None,
        admision=admision,
    )
    archivo_qs2 = mocker.Mock()
    archivo_qs2.first.side_effect = [archivo_ok]
    mocker.patch("admisiones.views.web_views.ArchivoAdmision.objects.filter", return_value=archivo_qs2)
    mocker.patch("admisiones.views.web_views.AdmisionService._serialize_documentacion", return_value={"row_id": "9"})
    mocker.patch("admisiones.views.web_views.AdmisionService.delete_admision_file")
    mocker.patch("admisiones.views.web_views.render_to_string", return_value="<tr></tr>")

    resp2 = module.eliminar_archivo_admision(req, 1, 2)
    assert resp2.status_code == 200


def test_subir_archivo_admision_paths(mocker):
    req_no = _Req(FILES={}, user=_user(), method="POST")
    assert module.subir_archivo_admision(req_no, 1, 2).status_code == 400

    req = _Req(FILES={"archivo": object()}, user=_user(), method="POST")
    mocker.patch("admisiones.views.web_views.AdmisionService.handle_file_upload", return_value=(None, False))
    assert module.subir_archivo_admision(req, 1, 2).status_code == 400

    archivo = SimpleNamespace(documentacion=SimpleNamespace(id=1), admision=SimpleNamespace(), id=3)
    mocker.patch("admisiones.views.web_views.AdmisionService.handle_file_upload", return_value=(archivo, True))
    mocker.patch("admisiones.views.web_views.AdmisionService._serialize_documentacion", return_value={"row_id": "r", "estado": "Pendiente", "estado_valor": "pendiente"})
    mocker.patch("admisiones.views.web_views.render_to_string", return_value="<tr></tr>")
    assert module.subir_archivo_admision(req, 1, 2).status_code == 200
