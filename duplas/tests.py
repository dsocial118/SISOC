"""Pruebas para la aplicación de filtros en el listado de duplas."""

import json

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from duplas.models import Dupla
from duplas.views import DuplaListView


class DuplaListViewFiltersTests(TestCase):
    """Valida que los filtros avanzados no dupliquen resultados."""

    def setUp(self) -> None:  # pylint: disable=invalid-name
        self.factory = RequestFactory()

    def test_filtering_by_tecnico_returns_distinct_duplas(self) -> None:
        """Aplica un filtro por técnicos y espera resultados únicos."""

        tecnico_a = User.objects.create_user(
            username="tecnica", first_name="Test", last_name="Uno"
        )
        tecnico_b = User.objects.create_user(
            username="tecnicob", first_name="Test", last_name="Dos"
        )
        abogado = User.objects.create_user(
            username="abogado", first_name="Law", last_name="Yer"
        )

        dupla = Dupla.objects.create(nombre="Equipo A", estado="Activo", abogado=abogado)
        dupla.tecnico.set([tecnico_a, tecnico_b])

        filters_payload = {
            "logic": "AND",
            "items": [
                {
                    "field": "tecnico",
                    "op": "contains",
                    "value": "Test",
                }
            ],
        }

        request = self.factory.get("/", {"filters": json.dumps(filters_payload)})
        view = DuplaListView()
        view.request = request

        queryset = view.get_queryset()

        self.assertEqual(list(queryset), [dupla])
