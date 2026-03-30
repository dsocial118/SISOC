from decimal import Decimal
from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from VAT.api_web_views import VatWebInscripcionViewSet
from VAT.serializers import VatWebInscripcionCreateSerializer
from VAT.services.inscripcion_service import InscripcionService


def test_vat_web_inscripcion_create_serializer_resuelve_por_documento(mocker):
    ciudadano = SimpleNamespace(id=4, documento=30111222)
    programa = SimpleNamespace(id=2)
    comision = SimpleNamespace(id=9, oferta=SimpleNamespace(programa=programa))

    mocker.patch(
        "VAT.serializers.Ciudadano.objects.filter",
        return_value=SimpleNamespace(first=lambda: ciudadano),
    )
    mocker.patch(
        "VAT.serializers.Comision.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_k: SimpleNamespace(first=lambda: comision)
        ),
    )
    mocker.patch(
        "VAT.serializers.Inscripcion.objects.filter",
        return_value=SimpleNamespace(exists=lambda: False),
    )

    serializer = VatWebInscripcionCreateSerializer(
        data={"documento": "30111222", "comision_id": 9}
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["ciudadano"] is ciudadano
    assert serializer.validated_data["programa"] is programa


def test_vat_web_inscripcion_create_devuelve_400_si_falla_regla_negocio(mocker):
    factory = APIRequestFactory()
    request = factory.post(
        "/api/vat/web/inscripciones/",
        {"documento": "30111222", "comision_id": 9},
        format="json",
    )

    serializer_mock = mocker.Mock()
    serializer_mock.is_valid.return_value = True
    serializer_mock.save.side_effect = ValueError("No tiene voucher activo.")
    mocker.patch.object(VatWebInscripcionViewSet, "permission_classes", [])
    mocker.patch.object(
        VatWebInscripcionViewSet, "get_serializer", return_value=serializer_mock
    )

    view = VatWebInscripcionViewSet.as_view({"post": "create"})
    response = view(request)

    assert response.status_code == 400
    assert response.data == {"error": ["No tiene voucher activo."]}


def test_inscripcion_service_crear_inscripcion_debita_voucher(mocker):
    ciudadano = SimpleNamespace(id=3, __str__=lambda self: "Ciudadano Demo")
    programa = SimpleNamespace(id=7)
    oferta = SimpleNamespace(
        programa=programa,
        programa_id=7,
        usa_voucher=True,
        costo=Decimal("12500"),
    )
    comision = SimpleNamespace(id=8, oferta=oferta, __str__=lambda self: "COM-8")
    inscripcion = SimpleNamespace(id=21, comision_id=8, comision=comision)
    usuario = SimpleNamespace(is_authenticated=True)
    voucher = SimpleNamespace(cantidad_disponible=12500)

    create_mock = mocker.patch(
        "VAT.services.inscripcion_service.Inscripcion.objects.create",
        return_value=inscripcion,
    )
    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *_a, **_k: SimpleNamespace(first=lambda: voucher)
        ),
    )
    debitar_mock = mocker.patch(
        "VAT.services.inscripcion_service.VoucherService.debitar_voucher",
        return_value=(True, "ok"),
    )

    result = InscripcionService.crear_inscripcion(
        ciudadano=ciudadano,
        comision=comision,
        programa=programa,
        usuario=usuario,
    )

    assert result is inscripcion
    create_mock.assert_called_once()
    assert debitar_mock.call_args.kwargs["cantidad"] == 12500


# ============================================================================
# Tests: Inscripción única activa
# ============================================================================


def test_inscripcion_unica_activa_bloquea_segunda_inscripcion(mocker):
    """Si inscripcion_unica_activa está activo y hay inscripción activa, bloquea."""
    ciudadano = SimpleNamespace(id=3, __str__=lambda self: "Demo")
    programa = SimpleNamespace(id=7)
    parametria = SimpleNamespace(inscripcion_unica_activa=True)
    voucher = SimpleNamespace(parametria=parametria, cantidad_disponible=100)

    inscripcion_existente = SimpleNamespace(
        comision=SimpleNamespace(nombre="Electricidad I"),
        get_estado_display=lambda: "Inscripta",
    )

    oferta = SimpleNamespace(
        programa=programa,
        programa_id=7,
        usa_voucher=True,
        costo=Decimal("100"),
    )
    comision_nueva = SimpleNamespace(id=9, oferta=oferta, __str__=lambda self: "COM-9")

    # Mock de validar_inscripcion_unica: voucher con parametria.inscripcion_unica_activa=True
    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_k: SimpleNamespace(
                order_by=lambda *_a: SimpleNamespace(first=lambda: voucher)
            )
        ),
    )
    mocker.patch(
        "VAT.services.inscripcion_service.Inscripcion.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_k: SimpleNamespace(first=lambda: inscripcion_existente)
        ),
    )

    with pytest.raises(ValueError, match="Ya tenés una inscripción activa"):
        InscripcionService.crear_inscripcion(
            ciudadano=ciudadano,
            comision=comision_nueva,
            programa=programa,
            usuario=SimpleNamespace(is_authenticated=True),
        )


def test_inscripcion_unica_activa_permite_si_no_hay_activa(mocker):
    """Si inscripcion_unica_activa está activo pero no hay inscripción activa, permite."""
    ciudadano = SimpleNamespace(id=3, __str__=lambda self: "Demo")
    programa = SimpleNamespace(id=7)
    parametria = SimpleNamespace(inscripcion_unica_activa=True)
    voucher_param = SimpleNamespace(parametria=parametria, cantidad_disponible=100)

    oferta = SimpleNamespace(
        programa=programa,
        programa_id=7,
        usa_voucher=True,
        costo=Decimal("100"),
    )
    comision = SimpleNamespace(id=9, oferta=oferta, __str__=lambda self: "COM-9")
    inscripcion = SimpleNamespace(id=30, comision_id=9, comision=comision)
    usuario = SimpleNamespace(is_authenticated=True)
    voucher_debito = SimpleNamespace(cantidad_disponible=100)

    # validar_inscripcion_unica: voucher con parametria pero sin inscripción activa
    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_k: SimpleNamespace(
                order_by=lambda *_a: SimpleNamespace(first=lambda: voucher_param)
            )
        ),
    )
    mocker.patch(
        "VAT.services.inscripcion_service.Inscripcion.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_k: SimpleNamespace(first=lambda: None)
        ),
    )

    # crear_inscripcion flow
    mocker.patch(
        "VAT.services.inscripcion_service.Inscripcion.objects.create",
        return_value=inscripcion,
    )
    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *_a: SimpleNamespace(first=lambda: voucher_debito)
        ),
    )
    mocker.patch(
        "VAT.services.inscripcion_service.VoucherService.debitar_voucher",
        return_value=(True, "ok"),
    )

    result = InscripcionService.crear_inscripcion(
        ciudadano=ciudadano,
        comision=comision,
        programa=programa,
        usuario=usuario,
    )

    assert result is inscripcion


def test_inscripcion_unica_activa_desactivado_permite_multiples(mocker):
    """Si inscripcion_unica_activa=False, permite inscribirse aunque haya activa."""
    ciudadano = SimpleNamespace(id=3, __str__=lambda self: "Demo")
    programa = SimpleNamespace(id=7)
    parametria = SimpleNamespace(inscripcion_unica_activa=False)
    voucher_param = SimpleNamespace(parametria=parametria, cantidad_disponible=100)

    oferta = SimpleNamespace(
        programa=programa,
        programa_id=7,
        usa_voucher=True,
        costo=Decimal("100"),
    )
    comision = SimpleNamespace(id=9, oferta=oferta, __str__=lambda self: "COM-9")
    inscripcion = SimpleNamespace(id=31, comision_id=9, comision=comision)
    usuario = SimpleNamespace(is_authenticated=True)
    voucher_debito = SimpleNamespace(cantidad_disponible=100)

    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_k: SimpleNamespace(
                order_by=lambda *_a: SimpleNamespace(first=lambda: voucher_param)
            )
        ),
    )

    mocker.patch(
        "VAT.services.inscripcion_service.Inscripcion.objects.create",
        return_value=inscripcion,
    )
    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *_a: SimpleNamespace(first=lambda: voucher_debito)
        ),
    )
    mocker.patch(
        "VAT.services.inscripcion_service.VoucherService.debitar_voucher",
        return_value=(True, "ok"),
    )

    result = InscripcionService.crear_inscripcion(
        ciudadano=ciudadano,
        comision=comision,
        programa=programa,
        usuario=usuario,
    )

    assert result is inscripcion


def test_validar_inscripcion_unica_sin_voucher_permite(mocker):
    """Si no hay voucher activo con parametria, permite inscribirse."""
    ciudadano = SimpleNamespace(id=5)
    programa = SimpleNamespace(id=2)

    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_k: SimpleNamespace(
                order_by=lambda *_a: SimpleNamespace(first=lambda: None)
            )
        ),
    )

    puede, msg = InscripcionService.validar_inscripcion_unica(ciudadano, programa)
    assert puede is True
    assert msg == ""
