import json
from datetime import date, datetime, time, timezone as dt_timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core.models import MontoPrestacionPrograma, Programa
from historial.models import Historial
from historial.services import historial_service
from historial.services.historial_service import HistorialService


User = get_user_model()


@pytest.mark.django_db
class TestHistorialService:
    def test_registrar_historial_serializes_complex_payload(self, monkeypatch):
        user = User.objects.create_user(
            username="historial_user",
            password="testpass123",
            email="historial@example.com",
        )
        monkeypatch.setattr(historial_service, "get_current_user", lambda: user)

        programa = Programa.objects.create(nombre="Programa Test")
        prestacion = MontoPrestacionPrograma.objects.create(
            programa="Programa A",
            desayuno_valor=Decimal("10.50"),
            almuerzo_valor=Decimal("20.75"),
            merienda_valor=Decimal("5.25"),
            cena_valor=Decimal("15.00"),
            usuario_creador=user,
        )

        payload = {
            "decimal": Decimal("12.34"),
            "date": date(2025, 1, 2),
            "datetime": datetime(2025, 1, 3, 15, 45, tzinfo=dt_timezone.utc),
            "time": time(8, 15),
            "list": [Decimal("1.23"), date(2025, 1, 4)],
            "queryset": Programa.objects.filter(pk=programa.pk),
            "model": programa,
            "none": None,
        }

        HistorialService.registrar_historial(
            accion="Creación de prueba",
            instancia=prestacion,
            diferencias=payload,
        )

        historial = Historial.objects.get()
        diferencias = historial.diferencias

        assert diferencias["decimal"] == "12.34"
        assert diferencias["date"] == "2025-01-02"
        assert diferencias["datetime"] == "2025-01-03T15:45:00+00:00"
        assert diferencias["time"].startswith("08:15:00")
        assert diferencias["list"] == ["1.23", "2025-01-04"]
        assert diferencias["queryset"] == ["Programa Test"]
        assert diferencias["model"] == "Programa Test"
        assert diferencias["none"] is None

    def test_json_safe_handles_unserializable_objects(self):
        payload = {
            "decimal": Decimal("3.14"),
            "date": date(2024, 12, 31),
            "time": time(12, 30),
            "tuple": (Decimal("1.0"), date(2024, 1, 1)),
            "set": {Decimal("2.0"), Decimal("2.0")},
        }

        safe_payload = HistorialService._json_safe(payload)

        # Ensure it's valid JSON and values got stringified where needed
        json_string = json.dumps(safe_payload)
        assert "3.14" in json_string
        assert safe_payload["tuple"] == ["1.0", "2024-01-01"]
        assert sorted(safe_payload["set"]) == ["2.0"]
