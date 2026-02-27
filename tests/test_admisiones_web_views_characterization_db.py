"""Caracterización DB de ramas críticas en ``admisiones.views.web_views``."""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from admisiones.models.admisiones import Admision
from admisiones.views import web_views as module
from comedores.models import Comedor
from core.models import Provincia

pytestmark = pytest.mark.django_db


def _crear_superuser():
    return get_user_model().objects.create_superuser(
        username=f"admin_{get_user_model().objects.count()+1}",
        email=f"admin_{get_user_model().objects.count()+1}@example.com",
        password="testpass123",
    )


def _crear_admision_minima(**overrides):
    provincia = Provincia.objects.create(nombre=f"Prov {Provincia.objects.count()+1}")
    comedor = Comedor.objects.create(nombre="Comedor Admision", provincia=provincia)
    data = {
        "comedor": comedor,
        "activa": True,
        "estado_admision": "documentacion_en_proceso",
        "estado_legales": None,
    }
    data.update(overrides)
    return Admision.objects.create(**data)


def _build_view_for_request(request, admision):
    view = module.AdmisionDetailView()
    view.request = request
    view.kwargs = {"comedor_pk": admision.comedor_id, "pk": admision.pk}
    view.get_object = lambda *args, **kwargs: admision
    return view


def test_handle_forzar_cierre_post_persiste_inactivada_con_estado_legales(mocker):
    admision = _crear_admision_minima(estado_legales="A Rectificar")
    request = RequestFactory().post(
        f"/admisiones/{admision.pk}/",
        {"forzar_cierre": "1", "motivo_forzar_cierre": "Cierre manual QA"},
    )
    request.user = _crear_superuser()

    success_msg = mocker.patch("admisiones.views.web_views.messages.success")
    mocker.patch("admisiones.views.web_views.messages.error")
    view = _build_view_for_request(request, admision)
    redirect_response = object()
    view._safe_redirect_to_self = lambda _req: redirect_response

    out = view._handle_forzar_cierre_post(request)

    admision.refresh_from_db()
    assert out is redirect_response
    assert admision.activa is False
    assert admision.motivo_forzar_cierre == "Cierre manual QA"
    assert admision.estado_legales == "Inactivada"
    assert admision.estado_mostrar == "Inactivada"
    assert admision.fecha_estado_mostrar is not None
    success_msg.assert_called_once()


def test_handle_forzar_cierre_post_persiste_inactivada_en_estado_admision(mocker):
    admision = _crear_admision_minima(
        estado_legales=None,
        estado_admision="informe_tecnico_aprobado",
    )
    request = RequestFactory().post(
        f"/admisiones/{admision.pk}/",
        {"forzar_cierre": "1", "motivo_forzar_cierre": "Sin legales"},
    )
    request.user = _crear_superuser()

    mocker.patch("admisiones.views.web_views.messages.success")
    mocker.patch("admisiones.views.web_views.messages.error")
    view = _build_view_for_request(request, admision)
    redirect_response = object()
    view._safe_redirect_to_self = lambda _req: redirect_response

    out = view._handle_forzar_cierre_post(request)

    admision.refresh_from_db()
    assert out is redirect_response
    assert admision.activa is False
    assert admision.estado_legales is None
    assert admision.estado_admision == "inactivada"
    assert admision.estado_mostrar == "Inactivada"
    assert admision.fecha_estado_mostrar is not None


def test_handle_forzar_cierre_post_rechaza_sin_motivo_y_no_persiste(mocker):
    admision = _crear_admision_minima(estado_legales="A Rectificar")
    request = RequestFactory().post(
        f"/admisiones/{admision.pk}/",
        {"forzar_cierre": "1", "motivo_forzar_cierre": "   "},
    )
    request.user = _crear_superuser()

    error_msg = mocker.patch("admisiones.views.web_views.messages.error")
    mocker.patch("admisiones.views.web_views.messages.success")
    view = _build_view_for_request(request, admision)
    redirect_response = object()
    view._safe_redirect_to_self = lambda _req: redirect_response

    out = view._handle_forzar_cierre_post(request)

    admision.refresh_from_db()
    assert out is redirect_response
    assert admision.activa is True
    assert admision.motivo_forzar_cierre in (None, "")
    assert admision.estado_legales == "A Rectificar"
    error_msg.assert_called_once()
