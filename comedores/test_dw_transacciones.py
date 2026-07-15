"""
Tests para la integración de Transacciones DW en comedores.
"""

import pytest
from decimal import Decimal
from pathlib import Path

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from comedores.models import Comedor
from comedores.services.dw_transacciones_service import (
    DWTransaccionesService,
    DWTransaccion,
)


def test_templates_muestran_saldo_cereado():
    templates_dir = Path(__file__).parent / "templates" / "comedor"

    for template_name in (
        "comedor_transacciones_card.html",
        "comedor_transacciones_detail.html",
    ):
        contenido = (templates_dir / template_name).read_text(encoding="utf-8")
        assert "Saldo Cereado" in contenido
        assert "Saldo Remanente" not in contenido


class TestDWTransaccionDataclass(TestCase):
    """Tests para la dataclass DWTransaccion."""

    def test_dw_transaccion_periodo_display(self):
        """Verificar que periodo_display formatea correctamente YYYYMM."""
        # Arrange
        transaccion = DWTransaccion(
            comedor_id_sisoc=1,
            periodo="202603",
            cantidad_debitos=7,
            credito_total=Decimal("720000.00"),
            debito_total=Decimal("750000.00"),
            cereo=Decimal("30000.00"),
        )

        # Act
        resultado = transaccion.periodo_display()

        # Assert
        assert resultado == "2026-03"

    def test_dw_transaccion_transferido_display(self):
        """
        CP12: Verificar que los montos se visualicen correctamente.
        """
        # Arrange
        transaccion = DWTransaccion(
            comedor_id_sisoc=1,
            periodo="202603",
            cantidad_debitos=7,
            credito_total=Decimal("720000.00"),
            debito_total=Decimal("750000.00"),
            cereo=Decimal("30000.00"),
        )

        # Act
        resultado = transaccion.transferido_display()

        # Assert
        assert "$750.000" in resultado

    def test_dw_transaccion_gastado_display(self):
        """CP12: Verificar formato de montos gastado."""
        # Arrange
        transaccion = DWTransaccion(
            comedor_id_sisoc=1,
            periodo="202603",
            cantidad_debitos=7,
            credito_total=Decimal("720000.00"),
            debito_total=Decimal("750000.00"),
            cereo=Decimal("30000.00"),
        )

        # Act
        resultado = transaccion.gastado_display()

        # Assert
        assert "$720.000" in resultado

    def test_dw_transaccion_saldo_display(self):
        """CP12: Verificar formato de montos saldo remanente."""
        # Arrange
        transaccion = DWTransaccion(
            comedor_id_sisoc=1,
            periodo="202603",
            cantidad_debitos=7,
            credito_total=Decimal("720000.00"),
            debito_total=Decimal("750000.00"),
            cereo=Decimal("30000.00"),
        )

        # Act
        resultado = transaccion.saldo_display()

        # Assert
        assert "$30.000" in resultado

    def test_dw_transaccion_none_valores_display(self):
        """CP07: Verificar que se muestre 'Sin información' cuando no hay datos."""
        # Arrange
        transaccion = DWTransaccion(
            comedor_id_sisoc=1,
            periodo="202603",
            cantidad_debitos=7,
            credito_total=None,
            debito_total=None,
            cereo=None,
        )

        # Act
        gastado = transaccion.gastado_display()
        transferido = transaccion.transferido_display()
        saldo = transaccion.saldo_display()

        # Assert
        assert gastado == "Sin información"
        assert transferido == "Sin información"
        assert saldo == "Sin información"

    def test_dw_transaccion_creation(self):
        """Verificar que DWTransaccion se crea correctamente."""
        # Arrange & Act
        transaccion = DWTransaccion(
            comedor_id_sisoc=123,
            periodo="202512",
            cantidad_debitos=42,
            credito_total=Decimal("500000.50"),
            debito_total=Decimal("600000.75"),
            cereo=Decimal("100000.25"),
        )

        # Assert
        assert transaccion.comedor_id_sisoc == 123
        assert transaccion.periodo == "202512"
        assert transaccion.cantidad_debitos == 42
        assert transaccion.credito_total == Decimal("500000.50")
        assert transaccion.debito_total == Decimal("600000.75")
        assert transaccion.cereo == Decimal("100000.25")


class TestDWTransaccionesServiceStructure(TestCase):
    """Tests para verificar la estructura del servicio DW."""

    def test_servicio_tiene_metodos_requeridos(self):
        """Verificar que el servicio tiene los métodos requeridos."""
        # Assert
        assert hasattr(DWTransaccionesService, "obtener_resumen_ultimo_periodo")
        assert hasattr(DWTransaccionesService, "obtener_historico_completo")
        assert callable(DWTransaccionesService.obtener_resumen_ultimo_periodo)
        assert callable(DWTransaccionesService.obtener_historico_completo)

    def test_servicio_metodos_son_staticmethod(self):
        """Verificar que los métodos son estáticos."""
        # Assert
        assert isinstance(
            DWTransaccionesService.__dict__["obtener_resumen_ultimo_periodo"],
            staticmethod,
        )
        assert isinstance(
            DWTransaccionesService.__dict__["obtener_historico_completo"],
            staticmethod,
        )
