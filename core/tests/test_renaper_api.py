"""
Tests para el endpoint proxy de RENAPER (/api/renaper/).
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey


@pytest.fixture
def api_client():
    """Cliente API para tests."""
    return APIClient()


@pytest.fixture
def api_key():
    """Crea una APIKey para tests."""
    api_key_obj, key = APIKey.objects.create_key(name="test-renaper-key")
    return key


@pytest.mark.django_db
class TestRenaperConsultaEndpoint:
    """Tests para el endpoint /api/renaper/consultar/."""

    def test_consultar_sin_autenticacion(self, api_client):
        """Debe rechazar request sin APIKey (401 Unauthorized)."""
        response = api_client.post(
            "/api/renaper/consultar/",
            {"dni": "12345678", "sexo": "M"},
            format="json",
        )
        assert response.status_code == 401

    def test_consultar_con_apikey_valida(self, api_client, api_key):
        """Debe aceptar request con APIKey válida."""
        mock_response = {
            "success": True,
            "data": {
                "nombre": "Juan",
                "apellido": "Pérez",
                "dni": "12345678",
                "sexo": "M",
            },
        }

        with patch("core.api_views.APIClient.consultar_ciudadano") as mock_consulta:
            mock_consulta.return_value = mock_response

            response = api_client.post(
                "/api/renaper/consultar/",
                {"dni": "12345678", "sexo": "M"},
                format="json",
                HTTP_AUTHORIZATION=f"Api-Key {api_key}",
            )

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "data" in response.json()

    def test_consultar_input_invalido(self, api_client, api_key):
        """Debe validar input (sexo inválido)."""
        response = api_client.post(
            "/api/renaper/consultar/",
            {"dni": "12345678", "sexo": "INVALIDO"},
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {api_key}",
        )

        assert response.status_code == 400
        assert response.json()["success"] is False
        assert "error" in response.json()

    def test_consultar_dni_vacio(self, api_client, api_key):
        """Debe validar que DNI no sea vacío."""
        response = api_client.post(
            "/api/renaper/consultar/",
            {"dni": "", "sexo": "M"},
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {api_key}",
        )

        assert response.status_code == 400
        assert response.json()["success"] is False

    def test_consultar_error_renaper(self, api_client, api_key):
        """Debe devolver error si RENAPER falla."""
        mock_response = {
            "success": False,
            "error": "No se encontró coincidencia.",
        }

        with patch("core.api_views.APIClient.consultar_ciudadano") as mock_consulta:
            mock_consulta.return_value = mock_response

            response = api_client.post(
                "/api/renaper/consultar/",
                {"dni": "99999999", "sexo": "M"},
                format="json",
                HTTP_AUTHORIZATION=f"Api-Key {api_key}",
            )

        assert response.status_code == 200
        assert response.json()["success"] is False
        assert "error" in response.json()

    def test_consultar_excepcion_interna(self, api_client, api_key):
        """Debe manejar excepciones internas."""
        with patch("core.api_views.APIClient.consultar_ciudadano") as mock_consulta:
            mock_consulta.side_effect = Exception("Error de conexión")

            response = api_client.post(
                "/api/renaper/consultar/",
                {"dni": "12345678", "sexo": "M"},
                format="json",
                HTTP_AUTHORIZATION=f"Api-Key {api_key}",
            )

        assert response.status_code == 500
        assert response.json()["success"] is False

    def test_sexo_normalizado_a_mayuscula(self, api_client, api_key):
        """Debe normalizar sexo a mayúscula."""
        mock_response = {
            "success": True,
            "data": {"nombre": "Test"},
        }

        with patch("core.api_views.APIClient.consultar_ciudadano") as mock_consulta:
            mock_consulta.return_value = mock_response

            response = api_client.post(
                "/api/renaper/consultar/",
                {"dni": "12345678", "sexo": "m"},  # minúscula
                format="json",
                HTTP_AUTHORIZATION=f"Api-Key {api_key}",
            )

        assert response.status_code == 200
        # Verificar que fue llamado con sexo en mayúscula
        mock_consulta.assert_called_once_with("12345678", "M")
