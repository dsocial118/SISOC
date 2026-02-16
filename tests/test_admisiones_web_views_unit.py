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


def test_tecnicos_list_view_queryset_and_context(mocker):
    """Technicians list view should delegate queryset and table context builders."""
    view = module.AdmisionesTecnicosListView()
    req = _Req(user=_user(), GET={})
    view.request = req

    qs = [SimpleNamespace()]
    mocker.patch("admisiones.views.web_views.AdmisionService.get_admisiones_tecnicos_queryset", return_value=qs)
    assert view.get_queryset() == qs

    mocker.patch("django.views.generic.list.MultipleObjectMixin.get_context_data", return_value={"admisiones": qs})
    mocker.patch("admisiones.views.web_views.AdmisionService.get_admisiones_tecnicos_table_data", return_value=[{"cells": []}])
    mocker.patch("admisiones.views.web_views.reverse", side_effect=lambda name: f"/{name}")
    mocker.patch("admisiones.views.web_views.get_tecnicos_filters_ui_config", return_value={})
    mocker.patch("admisiones.views.web_views.build_columns_context_for_custom_cells", return_value={"table_items": [1]})

    ctx = view.get_context_data()
    assert "table_items" in ctx


def test_tecnicos_create_view_post_branches(mocker):
    """Create view should create admision when tipo_convenio is present."""
    view = module.AdmisionesTecnicosCreateView()
    view.kwargs = {"pk": 99}

    req = _Req(POST={"tipo_convenio": "1"}, user=_user())
    adm = SimpleNamespace(pk=7)
    mocker.patch("admisiones.views.web_views.AdmisionService.create_admision", return_value=adm)
    mocker.patch("admisiones.views.web_views.redirect", return_value="redir")
    assert view.post(req) == "redir"

    req2 = _Req(POST={}, user=_user())
    mocker.patch("django.views.generic.edit.ProcessFormView.get", return_value="getresp")
    assert view.post(req2) == "getresp"


def test_tecnicos_update_view_post_docx_and_router_paths(mocker):
    """Update view should handle DOCX upload branch and standard POST router."""
    view = module.AdmisionesTecnicosUpdateView()
    adm = SimpleNamespace(pk=1, comedor=SimpleNamespace(), estado_admision="informe_tecnico_finalizado")
    view.get_object = lambda: adm

    # docx branch without file
    req_docx = _Req(POST={"subir_docx_final": "1"}, FILES={}, user=_user(), get_full_path=lambda: "/x")
    view.request = req_docx
    mocker.patch("admisiones.views.web_views.messages.error")
    mocker.patch("admisiones.views.web_views.safe_redirect", return_value="sr")
    mocker.patch("admisiones.views.web_views.reverse", return_value="/edit")
    assert view.post(req_docx) == "sr"

    # router branch
    req_router = _Req(POST={"btnX": "1"}, FILES={}, user=_user(), get_full_path=lambda: "/x")
    view.request = req_router
    mocker.patch("admisiones.views.web_views.AdmisionService.procesar_post_update", return_value=(True, "ok"))
    mocker.patch("admisiones.views.web_views.messages.success")
    mocker.patch("admisiones.views.web_views.safe_redirect", return_value="sr2")
    assert view.post(req_router) == "sr2"


def test_admision_detail_get_object_mismatch_raises(mocker):
    """Detail view should reject comedor/admision mismatch."""
    view = module.AdmisionDetailView()
    view.kwargs = {"comedor_pk": 2}
    mocker.patch("django.views.generic.detail.SingleObjectMixin.get_object", return_value=SimpleNamespace(comedor_id=1))

    import pytest

    with pytest.raises(module.Http404):
        view.get_object()


class _ListChain:
    def __init__(self, items):
        self._items = items

    def select_related(self, *args, **kwargs):
        return self

    def prefetch_related(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._items[0] if self._items else None

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]


def _groups_user(is_superuser=False, allowed=False):
    groups = SimpleNamespace(
        filter=lambda **kwargs: SimpleNamespace(exists=lambda: allowed)
    )
    return SimpleNamespace(is_superuser=is_superuser, groups=groups)


def test_admision_detail_get_context_data_builds_full_context(mocker):
    """Detail context should compose historial, acompanamiento and rendicion data."""
    view = module.AdmisionDetailView()
    tecnico = SimpleNamespace(get_full_name=lambda: "", username="tec")
    dupla = SimpleNamespace(tecnico=SimpleNamespace(all=lambda: [tecnico]), abogado="ab")
    comedor = SimpleNamespace(dupla=dupla)
    admision = SimpleNamespace(
        comedor=comedor,
        historial=_ListChain(
            [
                SimpleNamespace(
                    fecha=None,
                    usuario=SimpleNamespace(get_full_name=lambda: "", username="u1"),
                    campo="c",
                    valor_nuevo="n",
                    valor_anterior="a",
                )
            ]
        ),
        historial_estados=_ListChain(
            [
                SimpleNamespace(
                    fecha=None,
                    usuario=SimpleNamespace(get_full_name=lambda: "", username="u2"),
                    estado_anterior="pendiente",
                    estado_nuevo="aprobada",
                )
            ]
        ),
    )
    view.object = admision
    view.request = _Req(user=_user(), GET={})

    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )
    mocker.patch(
        "admisiones.views.web_views.AdmisionService.get_admision_update_context",
        return_value={"documentos": [1], "documentos_personalizados": [2], "informe_tecnico": "i", "pdf": "p"},
    )
    mocker.patch(
        "admisiones.views.web_views.AdmisionService._verificar_permiso_tecnico_dupla",
        return_value=True,
    )
    mocker.patch(
        "admisiones.views.web_views.InformeComplementario.objects.filter",
        return_value=_ListChain([SimpleNamespace()]),
    )
    mocker.patch(
        "admisiones.views.web_views.AcompanamientoService.obtener_datos_admision",
        return_value={"anexo": "x", "info_relevante": "info", "numero_if": "if", "numero_disposicion": "disp"},
    )
    mocker.patch(
        "admisiones.views.web_views.AcompanamientoService.obtener_prestaciones_detalladas",
        return_value={"prestaciones_por_dia": [1], "prestaciones_dias": [2], "dias_semana": [3]},
    )
    mocker.patch(
        "admisiones.views.web_views.ExpedientesPagosService.obtener_expedientes_pagos",
        return_value=["exp"],
    )
    mocker.patch(
        "admisiones.views.web_views.RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales",
        return_value=["rm"],
    )
    mocker.patch(
        "admisiones.views.web_views.RendicionCuentasFinal.objects.filter",
        return_value=_ListChain([SimpleNamespace()]),
    )
    mocker.patch(
        "admisiones.views.web_views.RendicionCuentasFinalService.get_documentos_rendicion_cuentas_final",
        return_value=["d"],
    )
    mocker.patch(
        "admisiones.views.web_views.HistorialService.get_historial_documentos_by_rendicion_cuentas_final",
        return_value=["h"],
    )
    mocker.patch("admisiones.templatetags.estado_filters.format_estado", side_effect=lambda x: f"fmt:{x}")

    ctx = view.get_context_data()
    assert ctx["dupla_abogado"] == "ab"
    assert ctx["documentos"] == [1]
    assert ctx["informes_complementarios"]
    assert ctx["acompanamiento_info"] == "info"
    assert ctx["expedientes_pagos"] == ["exp"]
    assert ctx["rendicion_final_documentos"] == ["d"]
    assert ctx["admision_historial_items"]
    assert ctx["historial_estados_items"]


def test_admision_detail_post_forzar_cierre_permission_and_validation(mocker):
    """Detail post should enforce permissions and require reason for forced close."""
    view = module.AdmisionDetailView()
    view.kwargs = {"comedor_pk": 2, "pk": 7}
    mocker.patch("admisiones.views.web_views.reverse", return_value="/detalle")
    mocker.patch("admisiones.views.web_views.safe_redirect", return_value="redir")
    err = mocker.patch("admisiones.views.web_views.messages.error")

    req_no_perm = _Req(
        POST={"forzar_cierre": "1"},
        FILES={},
        user=_groups_user(allowed=False),
        get_full_path=lambda: "/x",
    )
    assert view.post(req_no_perm) == "redir"
    assert err.called

    admision = SimpleNamespace(save=mocker.Mock())
    view.get_object = lambda: admision
    req_no_reason = _Req(
        POST={"forzar_cierre": "1", "motivo_forzar_cierre": "   "},
        FILES={},
        user=_groups_user(allowed=True),
        get_full_path=lambda: "/x",
    )
    assert view.post(req_no_reason) == "redir"


def test_admision_detail_post_forzar_cierre_success_branches(mocker):
    """Forced close should persist either legales or admision state path."""
    view = module.AdmisionDetailView()
    view.kwargs = {"comedor_pk": 2, "pk": 7}
    mocker.patch("admisiones.views.web_views.reverse", return_value="/detalle")
    mocker.patch("admisiones.views.web_views.safe_redirect", return_value="ok")
    mocker.patch("admisiones.views.web_views.messages.success")

    req = _Req(
        POST={"forzar_cierre": "1", "motivo_forzar_cierre": "motivo"},
        FILES={},
        user=_groups_user(allowed=True),
        get_full_path=lambda: "/x",
    )

    adm_legales = SimpleNamespace(
        activa=True,
        estado_legales="A validar",
        save=mocker.Mock(),
    )
    view.get_object = lambda: adm_legales
    assert view.post(req) == "ok"
    assert adm_legales.save.called

    adm_no_legales = SimpleNamespace(
        activa=True,
        estado_legales=None,
        save=mocker.Mock(),
    )
    view.get_object = lambda: adm_no_legales
    assert view.post(req) == "ok"
    assert adm_no_legales.save.called


def test_admision_detail_post_file_and_docx_paths(mocker):
    """Detail post should handle additional files and DOCX branch errors."""
    view = module.AdmisionDetailView()
    view.kwargs = {"comedor_pk": 2, "pk": 7}
    mocker.patch("admisiones.views.web_views.reverse", return_value="/detalle")
    mocker.patch("admisiones.views.web_views.safe_redirect", return_value="redir")
    mocker.patch("admisiones.views.web_views.messages.error")

    req_bad = _Req(
        POST={"nombre": "Doc"},
        FILES={},
        user=_groups_user(allowed=True),
        get_full_path=lambda: "/x",
    )
    assert view.post(req_bad).status_code == 400

    admision = SimpleNamespace(id=5, comedor=SimpleNamespace(), estado_admision="otro")
    view.get_object = lambda: admision
    req_upload = _Req(
        POST={"nombre": "Doc"},
        FILES={"archivo": object()},
        user=_groups_user(allowed=True),
        get_full_path=lambda: "/x",
    )
    mocker.patch(
        "admisiones.views.web_views.AdmisionService.crear_documento_personalizado",
        return_value=(SimpleNamespace(), None),
    )
    assert view.post(req_upload).status_code == 200

    req_docx_forbidden = _Req(
        POST={"subir_docx_final": "1"},
        FILES={"docx_final": object()},
        user=_user(False),
        get_full_path=lambda: "/x",
    )
    mocker.patch(
        "admisiones.views.web_views.AdmisionService._verificar_permiso_tecnico_dupla",
        return_value=False,
    )
    assert view.post(req_docx_forbidden).status_code == 403

    req_docx_invalid_state = _Req(
        POST={"subir_docx_final": "1"},
        FILES={"docx_final": object()},
        user=_user(True),
        get_full_path=lambda: "/x",
    )
    mocker.patch(
        "admisiones.views.web_views.InformeTecnico.objects.filter",
        return_value=_ListChain([SimpleNamespace(estado="Docx generado")]),
    )
    assert view.post(req_docx_invalid_state) == "redir"


def test_informe_tecnicos_create_dispatch_branches(mocker):
    view = module.InformeTecnicosCreateView()
    view.kwargs = {"pk": 10, "tipo": "base"}
    request = _Req(user=_user(), method="GET")

    mocker.patch(
        "admisiones.views.web_views.InformeService.get_admision_y_tipo_from_kwargs",
        return_value=(None, "base"),
    )

    import pytest

    with pytest.raises(module.Http404):
        view.dispatch(request)

    mocker.patch(
        "admisiones.views.web_views.InformeService.get_admision_y_tipo_from_kwargs",
        return_value=(SimpleNamespace(id=5), "otro"),
    )
    mocker.patch("admisiones.views.web_views.messages.error")
    mocker.patch("admisiones.views.web_views.reverse", return_value="/edit/5")
    resp = view.dispatch(request)
    assert resp.status_code == 302


def test_informe_tecnicos_create_get_form_kwargs_y_success_url(mocker):
    view = module.InformeTecnicosCreateView()
    view.admision_obj = SimpleNamespace(id=10)
    view.request = _Req(method="POST", POST={"action": "submit"})
    mocker.patch(
        "django.views.generic.edit.ModelFormMixin.get_form_kwargs",
        return_value={"base": True},
    )

    kwargs = view.get_form_kwargs()

    assert kwargs["admision"].id == 10
    assert kwargs["require_full"] is True

    view.object = SimpleNamespace(admision=SimpleNamespace(id=99))
    mocker.patch("admisiones.views.web_views.reverse", return_value="/ok")
    assert view.get_success_url() == "/ok"


def test_informe_tecnicos_create_form_invalid_agrega_error(mocker):
    view = module.InformeTecnicosCreateView()
    view.request = _Req(user=_user())
    form = SimpleNamespace(
        errors={"campo_x": ["error 1"]},
        fields={"campo_x": SimpleNamespace(label="Campo X")},
    )
    mocker.patch("admisiones.views.web_views.messages.error")
    super_invalid = mocker.patch(
        "django.views.generic.edit.ModelFormMixin.form_invalid",
        return_value="INVALID",
    )

    result = view.form_invalid(form)

    assert result == "INVALID"
    assert super_invalid.called


def test_informe_tecnicos_update_dispatch_and_form_kwargs(mocker):
    view = module.InformeTecnicosUpdateView()
    view.request = _Req(method="POST", POST={"action": "save"})
    admision = SimpleNamespace(id=22)
    view.get_object = lambda: SimpleNamespace(tipo="otro", admision=admision)

    mocker.patch("admisiones.views.web_views.messages.error")
    mocker.patch("admisiones.views.web_views.reverse", return_value="/edit")
    response = view.dispatch(view.request)
    assert response.status_code == 302

    view.object = SimpleNamespace(tipo="base", admision=admision)
    mocker.patch(
        "django.views.generic.edit.ModelFormMixin.get_form_kwargs",
        return_value={"seed": 1},
    )
    kwargs = view.get_form_kwargs()
    assert kwargs["admision"].id == 22
    assert kwargs["require_full"] is False


def test_informe_tecnico_detail_context_muestra_revision_tecnico(mocker):
    view = module.InformeTecnicoDetailView()
    view.request = _Req(
        user=SimpleNamespace(
            groups=SimpleNamespace(
                filter=lambda **kwargs: SimpleNamespace(exists=lambda: True)
            )
        )
    )
    view.object = SimpleNamespace(estado="Docx generado")
    view.kwargs = {"tipo": "base"}
    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )
    mocker.patch(
        "admisiones.views.web_views.InformeService.get_context_informe_detail",
        return_value={"k": "v"},
    )

    context = view.get_context_data()

    assert context["k"] == "v"
    assert context["mostrar_revision_tecnico"] is True


def test_admisiones_legales_ajax_devuelve_json(mocker):
    request = _Req(GET={"busqueda": "abc", "page": 1}, user=_user())

    mocker.patch(
        "core.decorators.group_required",
        return_value=lambda fn: fn,
    )
    mocker.patch(
        "admisiones.views.web_views.LegalesService.get_admisiones_legales_filtradas",
        return_value=[1, 2, 3],
    )
    mocker.patch(
        "django.template.loader.render_to_string",
        side_effect=["<tr></tr>", "<nav></nav>"],
    )

    response = module.admisiones_legales_ajax(request)

    assert response.status_code == 200


def test_admisiones_legales_list_view_queryset_y_contexto(mocker):
    view = module.AdmisionesLegalesListView()
    view.request = _Req(user=_user(), GET={})

    qs = [SimpleNamespace(id=1)]
    mocker.patch(
        "admisiones.views.web_views.LegalesService.get_admisiones_legales_filtradas",
        return_value=qs,
    )
    assert view.get_queryset() == qs

    mocker.patch(
        "django.views.generic.list.MultipleObjectMixin.get_context_data",
        return_value={"admisiones": qs},
    )
    mocker.patch(
        "admisiones.views.web_views.LegalesService.get_admisiones_legales_table_data",
        return_value=[{"id": 1}],
    )
    mocker.patch("admisiones.views.web_views.reverse", side_effect=lambda name: f"/{name}")
    mocker.patch("admisiones.views.web_views.get_legales_filters_ui_config", return_value={"k": "v"})
    mocker.patch(
        "admisiones.views.web_views.build_columns_context_for_custom_cells",
        return_value={"table_items": [1]},
    )

    ctx = view.get_context_data()
    assert ctx["filters_mode"] is True
    assert ctx["table_items"] == [1]


def test_admisiones_legales_detail_contexto_y_post(mocker):
    view = module.AdmisionesLegalesDetailView()
    obj = SimpleNamespace(pk=99)
    view.get_object = lambda: obj
    view.request = _Req(user=_user(), GET={})

    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )
    mocker.patch(
        "admisiones.views.web_views.LegalesService.get_legales_context",
        return_value={"ctx": 1},
    )
    mocker.patch.object(view, "get_form", return_value="FORM")
    mocker.patch("admisiones.views.web_views.LegalesNumIFForm", return_value="FORM_IF")

    context = view.get_context_data()
    assert context["ctx"] == 1
    assert context["form"] == "FORM"
    assert context["form_legales_num_if"] == "FORM_IF"

    mocker.patch(
        "admisiones.views.web_views.LegalesService.procesar_post_legales",
        return_value="OK_POST",
    )
    assert view.post(_Req(user=_user()), pk=99) == "OK_POST"


def test_informe_complementario_review_contexto_con_y_sin_informe(mocker):
    view = module.InformeTecnicoComplementarioReviewView()
    view.object = SimpleNamespace()

    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )

    filtro_mock = mocker.patch(
        "admisiones.models.admisiones.InformeComplementario.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    ctx = view.get_context_data()
    assert "informe_complementario" not in ctx
    assert filtro_mock.called

    informe = SimpleNamespace(id=3)
    mocker.patch(
        "admisiones.models.admisiones.InformeComplementario.objects.filter",
        return_value=SimpleNamespace(first=lambda: informe),
    )
    mocker.patch(
        "admisiones.models.admisiones.InformeComplementarioCampos.objects.filter",
        return_value=["campo"],
    )
    ctx2 = view.get_context_data()
    assert ctx2["informe_complementario"].id == 3
    assert ctx2["campos_modificados"] == ["campo"]


def test_informe_complementario_review_post_delega_servicio(mocker):
    view = module.InformeTecnicoComplementarioReviewView()
    view.get_object = lambda: SimpleNamespace(id=7)
    mocker.patch(
        "admisiones.views.web_views.LegalesService.revisar_informe_complementario",
        return_value="DONE",
    )

    result = view.post(_Req(user=_user()), pk=7)

    assert result == "DONE"


def test_informe_complementario_detail_contexto_y_post_success(mocker):
    view = module.InformeTecnicoComplementarioDetailView()
    admision = SimpleNamespace(id=12)
    informe_tecnico = SimpleNamespace(admision=admision)
    view.object = informe_tecnico
    view.kwargs = {"tipo": "base", "pk": 88}
    req = _Req(
        POST={"campo_estado": " valor "},
        user=_user(),
        get_full_path=lambda: "/x",
    )
    view.request = req
    view.get_object = lambda: informe_tecnico

    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )
    mocker.patch(
        "admisiones.views.web_views.InformeService.get_context_informe_detail",
        return_value={"base": True},
    )
    mocker.patch(
        "admisiones.models.admisiones.InformeComplementario.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    context = view.get_context_data()
    assert context["base"] is True

    informe_complementario = SimpleNamespace(estado=None, save=mocker.Mock())
    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_campos_complementarios",
        return_value=informe_complementario,
    )
    mocker.patch(
        "admisiones.services.legales_service.LegalesService.actualizar_estado_por_accion",
        return_value=None,
    )
    mocker.patch("admisiones.views.web_views.messages.success")
    mocker.patch("admisiones.views.web_views.reverse", return_value="/dest")

    response = view.post(req, pk=88)
    assert response.status_code == 302
    assert informe_complementario.estado == "enviado_validacion"
    assert informe_complementario.save.called
