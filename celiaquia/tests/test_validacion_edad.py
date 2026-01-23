"""
Tests para validaciones de edad en celiaquía.
Verifica que se bloqueen:
1. Responsables menores de 18 años
2. Beneficiarios menores sin responsable
"""
import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from celiaquia.services.validacion_edad_service import ValidacionEdadService


class TestValidacionEdadService:
    """Tests para el servicio de validación de edad."""

    def test_calcular_edad_valida(self):
        """Calcula correctamente la edad."""
        hoy = date.today()
        hace_20_anos = hoy.replace(year=hoy.year - 20)
        edad = ValidacionEdadService.calcular_edad(hace_20_anos)
        assert edad == 20

    def test_calcular_edad_menor_18(self):
        """Calcula correctamente edad menor a 18."""
        hoy = date.today()
        hace_15_anos = hoy.replace(year=hoy.year - 15)
        edad = ValidacionEdadService.calcular_edad(hace_15_anos)
        assert edad == 15

    def test_calcular_edad_none(self):
        """Retorna None si la fecha es None."""
        edad = ValidacionEdadService.calcular_edad(None)
        assert edad is None

    # REQUERIMIENTO 1: Responsable menor de 18 años
    def test_validar_responsable_mayor_edad_ok(self):
        """Responsable mayor de 18 años es válido."""
        hoy = date.today()
        hace_25_anos = hoy.replace(year=hoy.year - 25)
        result = ValidacionEdadService.validar_responsable_mayor_edad(hace_25_anos)
        assert result is True

    def test_validar_responsable_menor_edad_bloquea(self):
        """Responsable menor de 18 años es bloqueado."""
        hoy = date.today()
        hace_15_anos = hoy.replace(year=hoy.year - 15)
        
        with pytest.raises(ValidationError) as exc_info:
            ValidacionEdadService.validar_responsable_mayor_edad(hace_15_anos)
        
        assert "El responsable no puede ser menor de 18 años" in str(exc_info.value)

    def test_validar_responsable_exactamente_18_ok(self):
        """Responsable con exactamente 18 años es válido."""
        hoy = date.today()
        hace_18_anos = hoy.replace(year=hoy.year - 18)
        result = ValidacionEdadService.validar_responsable_mayor_edad(hace_18_anos)
        assert result is True

    def test_validar_responsable_none_ok(self):
        """Si no hay fecha de nacimiento, no se valida."""
        result = ValidacionEdadService.validar_responsable_mayor_edad(None)
        assert result is True

    # REQUERIMIENTO 2: Beneficiario menor sin responsable
    def test_validar_beneficiario_menor_con_responsable_ok(self):
        """Beneficiario menor con responsable es válido."""
        hoy = date.today()
        hace_10_anos = hoy.replace(year=hoy.year - 10)
        result = ValidacionEdadService.validar_beneficiario_menor_con_responsable(
            hace_10_anos, tiene_responsable=True
        )
        assert result is True

    def test_validar_beneficiario_menor_sin_responsable_bloquea(self):
        """Beneficiario menor sin responsable es bloqueado."""
        hoy = date.today()
        hace_10_anos = hoy.replace(year=hoy.year - 10)
        
        with pytest.raises(ValidationError) as exc_info:
            ValidacionEdadService.validar_beneficiario_menor_con_responsable(
                hace_10_anos, tiene_responsable=False
            )
        
        assert "El beneficiario menor de 18 años debe tener un responsable" in str(
            exc_info.value
        )

    def test_validar_beneficiario_mayor_sin_responsable_ok(self):
        """Beneficiario mayor sin responsable es válido."""
        hoy = date.today()
        hace_25_anos = hoy.replace(year=hoy.year - 25)
        result = ValidacionEdadService.validar_beneficiario_menor_con_responsable(
            hace_25_anos, tiene_responsable=False
        )
        assert result is True

    def test_validar_beneficiario_exactamente_18_sin_responsable_ok(self):
        """Beneficiario con exactamente 18 años sin responsable es válido."""
        hoy = date.today()
        hace_18_anos = hoy.replace(year=hoy.year - 18)
        result = ValidacionEdadService.validar_beneficiario_menor_con_responsable(
            hace_18_anos, tiene_responsable=False
        )
        assert result is True

    def test_validar_beneficiario_none_ok(self):
        """Si no hay fecha de nacimiento, no se valida."""
        result = ValidacionEdadService.validar_beneficiario_menor_con_responsable(
            None, tiene_responsable=False
        )
        assert result is True

    # Validación adicional: responsable no puede ser más joven que beneficiario
    def test_validar_relacion_responsable_beneficiario_ok(self):
        """Responsable mayor que beneficiario es válido."""
        hoy = date.today()
        responsable_fecha = hoy.replace(year=hoy.year - 40)
        beneficiario_fecha = hoy.replace(year=hoy.year - 10)
        
        result = ValidacionEdadService.validar_relacion_responsable_beneficiario(
            responsable_fecha, beneficiario_fecha
        )
        assert result is True

    def test_validar_relacion_responsable_mas_joven_bloquea(self):
        """Responsable más joven que beneficiario es bloqueado."""
        hoy = date.today()
        responsable_fecha = hoy.replace(year=hoy.year - 10)
        beneficiario_fecha = hoy.replace(year=hoy.year - 20)
        
        with pytest.raises(ValidationError) as exc_info:
            ValidacionEdadService.validar_relacion_responsable_beneficiario(
                responsable_fecha, beneficiario_fecha
            )
        
        assert "no puede ser más joven" in str(exc_info.value)

    def test_validar_relacion_misma_edad_ok(self):
        """Responsable y beneficiario con la misma edad es válido."""
        hoy = date.today()
        fecha = hoy.replace(year=hoy.year - 20)
        
        result = ValidacionEdadService.validar_relacion_responsable_beneficiario(
            fecha, fecha
        )
        assert result is True

    def test_validar_relacion_none_ok(self):
        """Si faltan fechas, no se valida."""
        hoy = date.today()
        fecha = hoy.replace(year=hoy.year - 20)
        
        result = ValidacionEdadService.validar_relacion_responsable_beneficiario(
            None, fecha
        )
        assert result is True
        
        result = ValidacionEdadService.validar_relacion_responsable_beneficiario(
            fecha, None
        )
        assert result is True
